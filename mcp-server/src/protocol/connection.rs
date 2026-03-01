/*!
 * Device Connection
 *
 * Manages TCP connection to the Android companion app.
 * Handles connection establishment, message sending/receiving, and reconnection logic.
 */

use anyhow::{bail, Context, Result};
use prost::Message;
use std::sync::Arc;
use std::time::Duration;
use tokio::io::{AsyncReadExt, AsyncWriteExt};
use tokio::net::TcpStream;
use tokio::sync::{mpsc, Mutex};
use tracing::{debug, info, warn};

use super::codec::{encode_message, MessageFramer, MessageType};
use super::pb::{Event, Request, Response};

/// TCP port where companion app listens
pub const COMPANION_PORT: u16 = 38472;

/// Connection timeout
const CONNECT_TIMEOUT: Duration = Duration::from_secs(5);

/// Read timeout
const READ_TIMEOUT: Duration = Duration::from_secs(10);

/// Retry configuration
const MAX_RETRIES: u32 = 5;
const INITIAL_BACKOFF_MS: u64 = 250; // Reduced from 500ms for faster initial retry
const MAX_BACKOFF_MS: u64 = 4000; // Reduced from 8000ms for faster reconnection

/// Device connection handle
#[derive(Clone)]
pub struct DeviceConnection {
    inner: Arc<Mutex<ConnectionInner>>,
}

struct ConnectionInner {
    stream: TcpStream,
    framer: MessageFramer,
    event_tx: Option<mpsc::Sender<Event>>, // Event channel sender (bounded)
    event_rx: Option<mpsc::Receiver<Event>>, // Event channel receiver (bounded, taken once)
}

impl DeviceConnection {
    /// Internal connection attempt (single try, no retries)
    async fn try_connect() -> Result<Self> {
        info!(
            "Connecting to companion app on localhost:{}",
            COMPANION_PORT
        );

        let stream = tokio::time::timeout(
            CONNECT_TIMEOUT,
            TcpStream::connect(("localhost", COMPANION_PORT)),
        )
        .await
        .context("Connection timeout")?
        .context("Failed to connect to companion app")?;

        // Set TCP_NODELAY for low latency
        stream
            .set_nodelay(true)
            .context("Failed to set TCP_NODELAY")?;

        info!("Connected to companion app");

        // Create bounded event channel (max 1000 events to prevent memory bloat)
        let (event_tx, event_rx) = mpsc::channel(1000);

        Ok(Self {
            inner: Arc::new(Mutex::new(ConnectionInner {
                stream,
                framer: MessageFramer::new(),
                event_tx: Some(event_tx),
                event_rx: Some(event_rx),
            })),
        })
    }

    /// Connect with automatic retry and exponential backoff
    ///
    /// Retries transient errors (Connection refused, timeout, reset) with exponential backoff:
    /// - 250ms → 500ms → 1s → 2s → 4s (capped at 4s)
    /// - Max 5 retries
    /// - Fails immediately on non-transient errors
    ///
    /// Requires ADB port forwarding to be set up first:
    /// `adb forward tcp:38472 tcp:38472`
    async fn connect_with_retry() -> Result<Self> {
        let mut last_error = None;

        for attempt in 0..=MAX_RETRIES {
            match Self::try_connect().await {
                Ok(conn) => {
                    if attempt > 0 {
                        info!("Connection established after {} retries", attempt);
                    }
                    return Ok(conn);
                }
                Err(e) => {
                    let error_msg = e.to_string().to_lowercase();

                    // Check if error is transient
                    let is_transient = error_msg.contains("connection refused")
                        || error_msg.contains("connection timeout")
                        || error_msg.contains("connection reset");

                    if !is_transient {
                        // Non-transient error - fail immediately
                        return Err(e).context("Connection failed with non-transient error");
                    }

                    last_error = Some(e);

                    if attempt < MAX_RETRIES {
                        // Calculate backoff delay (exponential with cap)
                        let backoff_ms =
                            std::cmp::min(INITIAL_BACKOFF_MS * 2_u64.pow(attempt), MAX_BACKOFF_MS);

                        warn!(
                            "Connection attempt {} failed (transient error), retrying in {}ms",
                            attempt + 1,
                            backoff_ms
                        );

                        tokio::time::sleep(Duration::from_millis(backoff_ms)).await;
                    }
                }
            }
        }

        // All retries exhausted
        Err(last_error.unwrap()).context(format!(
            "Failed to connect after {} attempts. Check that:\n  \
                 1. Companion app is running on device\n  \
                 2. ADB port forwarding is active: adb forward tcp:{} tcp:{}",
            MAX_RETRIES + 1,
            COMPANION_PORT,
            COMPANION_PORT
        ))
    }

    /// Establish connection to companion app
    ///
    /// Automatically retries transient errors with exponential backoff.
    /// Requires ADB port forwarding to be set up first:
    /// `adb forward tcp:38472 tcp:38472`
    pub async fn connect() -> Result<Self> {
        Self::connect_with_retry().await
    }

    /// Take the event receiver (can only be called once)
    pub async fn take_event_receiver(&self) -> Option<mpsc::Receiver<Event>> {
        let mut inner = self.inner.lock().await;
        inner.event_rx.take()
    }

    /// Send a request and wait for response
    pub async fn send_request(&self, request: Request) -> Result<Response> {
        let request_id = request.request_id.clone();
        debug!("Sending request: id={}", request_id);

        // Encode request
        let message_bytes = encode_message(MessageType::Request, &request)?;

        // Send to companion app
        let mut inner = self.inner.lock().await;
        inner
            .stream
            .write_all(&message_bytes)
            .await
            .context("Failed to send request")?;
        inner
            .stream
            .flush()
            .await
            .context("Failed to flush request")?;

        debug!("Request sent, waiting for response...");

        // Read response with timeout
        let response = tokio::time::timeout(READ_TIMEOUT, Self::read_response_inner(&mut inner))
            .await
            .context("Response timeout")??;

        // Validate request ID matches
        if response.request_id != request_id {
            warn!(
                "Response request_id mismatch: expected {}, got {}",
                request_id, response.request_id
            );
        }

        debug!("Received response: success={}", response.success);
        Ok(response)
    }

    /// Internal method to read response (requires lock held)
    async fn read_response_inner(inner: &mut ConnectionInner) -> Result<Response> {
        loop {
            // Try to extract message from buffer
            match inner.framer.try_extract_message() {
                Ok(Some((header, payload))) => {
                    // Handle different message types
                    match header.message_type {
                        MessageType::Response => {
                            // Decode response
                            let response = Response::decode(&payload[..])
                                .context("Failed to decode response")?;
                            return Ok(response);
                        }
                        MessageType::Event => {
                            // Decode and send event to channel
                            match Event::decode(&payload[..]) {
                                Ok(event) => {
                                    debug!(
                                        "Received event: type={:?}, id={}",
                                        event.event_type, event.event_id
                                    );
                                    // Send to event channel if available
                                    if let Some(ref tx) = inner.event_tx {
                                        if let Err(e) = tx.try_send(event) {
                                            warn!("Failed to send event to channel (buffer full?): {}", e);
                                        }
                                    } else {
                                        debug!("Event channel not available, event discarded");
                                    }
                                }
                                Err(e) => {
                                    warn!("Failed to decode event: {}", e);
                                }
                            }
                            // Continue reading for response
                            continue;
                        }
                        MessageType::Request => {
                            warn!("Received unexpected Request message from companion app");
                            continue;
                        }
                    }
                }
                Ok(None) => {
                    // Need more data - fall through to read
                }
                Err(e) => {
                    // Framing error - this is fatal
                    return Err(e);
                }
            }

            // Need more data
            let mut buf = vec![0u8; 4096];
            let n = inner
                .stream
                .read(&mut buf)
                .await
                .context("Failed to read from connection")?;

            if n == 0 {
                bail!("Connection closed by companion app");
            }

            // Log first 32 bytes as hex for debugging
            if n > 0 {
                let hex_preview: String = buf
                    .iter()
                    .take(std::cmp::min(32, n))
                    .map(|b| format!("{:02X}", b))
                    .collect::<Vec<String>>()
                    .join(" ");
                debug!(
                    "Read {} bytes from connection. First {} bytes: {}",
                    n,
                    std::cmp::min(32, n),
                    hex_preview
                );
            }

            inner.framer.add_data(&buf[..n]);
        }
    }

    /// Close the connection
    pub async fn close(&self) -> Result<()> {
        let mut inner = self.inner.lock().await;
        inner
            .stream
            .shutdown()
            .await
            .context("Failed to close connection")?;
        info!("Connection closed");
        Ok(())
    }

    /// Check if connection is still alive
    ///
    /// Uses both peek (read check) and write (write check) to detect dead connections.
    /// This is important because ADB port forwarding may not propagate TCP resets promptly.
    pub async fn is_alive(&self) -> bool {
        let mut inner = self.inner.lock().await;

        // First: try peek to check for EOF or error
        let mut peek_buf = [0u8; 1];
        match tokio::time::timeout(Duration::from_millis(50), inner.stream.peek(&mut peek_buf))
            .await
        {
            Ok(Ok(0)) => {
                debug!("Connection closed (EOF)");
                false
            }
            Ok(Ok(_)) => true, // Data available = definitely alive
            Ok(Err(_)) => {
                debug!("Connection health check failed (peek error)");
                false
            }
            Err(_) => {
                // Timeout on peek = no data waiting. Try a zero-byte write to verify
                // the socket is still writable (detects broken pipe through ADB forwarding)
                match tokio::time::timeout(Duration::from_millis(50), inner.stream.write_all(&[]))
                    .await
                {
                    Ok(Ok(())) => true, // Write succeeded = alive
                    Ok(Err(e)) => {
                        debug!("Connection health check failed (write error: {})", e);
                        false
                    }
                    Err(_) => {
                        debug!("Connection health check timed out on write");
                        false // If write times out, assume dead (conservative)
                    }
                }
            }
        }
    }
}

/// Connection pool for managing multiple device connections
#[allow(dead_code)]
#[derive(Default)]
pub struct ConnectionPool {
    // TODO Week 3: Implement connection pooling
}

impl ConnectionPool {
    #[allow(dead_code)]
    pub fn new() -> Self {
        Self::default()
    }

    #[allow(dead_code)]
    pub async fn get_connection(&self, _device_id: &str) -> Result<DeviceConnection> {
        bail!("Connection pooling not yet implemented")
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_connection_creation() {
        if std::env::var("CI").is_ok() {
            return;
        }

        let result = DeviceConnection::connect().await;
        if result.is_err() {
            eprintln!("Connection test skipped (companion app not running)");
        }
    }

    /// Test that exponential backoff timing matches expected values
    #[test]
    fn test_exponential_backoff_timing() {
        // Expected backoff sequence: 250ms → 500ms → 1s → 2s → 4s
        let expected = [250, 500, 1000, 2000, 4000];

        for (attempt, &expected_ms) in expected.iter().enumerate() {
            let backoff_ms = std::cmp::min(
                INITIAL_BACKOFF_MS * 2_u64.pow(attempt as u32),
                MAX_BACKOFF_MS,
            );
            assert_eq!(
                backoff_ms, expected_ms,
                "Backoff at attempt {} should be {}ms, got {}ms",
                attempt, expected_ms, backoff_ms
            );
        }
    }

    /// Test that backoff is capped at MAX_BACKOFF_MS
    #[test]
    fn test_exponential_backoff_cap() {
        // At attempt 10, backoff should still be capped at 4000ms
        let backoff_ms = std::cmp::min(INITIAL_BACKOFF_MS * 2_u64.pow(10), MAX_BACKOFF_MS);
        assert_eq!(backoff_ms, MAX_BACKOFF_MS);
    }

    /// Test transient error detection
    #[test]
    fn test_transient_error_detection() {
        let transient_errors = vec![
            "connection refused by peer",
            "Connection timeout after 5 seconds",
            "connection reset by peer",
            "ECONNREFUSED: Connection refused",
        ];

        for error_msg in transient_errors {
            let error_msg_lower = error_msg.to_lowercase();
            let is_transient = error_msg_lower.contains("connection refused")
                || error_msg_lower.contains("connection timeout")
                || error_msg_lower.contains("connection reset");

            assert!(
                is_transient,
                "Error '{}' should be classified as transient",
                error_msg
            );
        }
    }

    /// Test non-transient error detection
    #[test]
    fn test_non_transient_error_detection() {
        let non_transient_errors = vec![
            "permission denied",
            "host not found",
            "invalid address",
            "protocol error",
        ];

        for error_msg in non_transient_errors {
            let error_msg_lower = error_msg.to_lowercase();
            let is_transient = error_msg_lower.contains("connection refused")
                || error_msg_lower.contains("connection timeout")
                || error_msg_lower.contains("connection reset");

            assert!(
                !is_transient,
                "Error '{}' should NOT be classified as transient",
                error_msg
            );
        }
    }

    /// Test that MAX_RETRIES constant is correctly set
    #[test]
    fn test_max_retries_constant() {
        assert_eq!(MAX_RETRIES, 5, "MAX_RETRIES should be 5");
    }

    /// Test retry backoff calculation for all attempts
    #[test]
    fn test_retry_backoff_sequence() {
        let expected_sequence = vec![
            (0, 250),  // 250ms * 2^0 = 250ms
            (1, 500),  // 250ms * 2^1 = 500ms
            (2, 1000), // 250ms * 2^2 = 1000ms
            (3, 2000), // 250ms * 2^3 = 2000ms
            (4, 4000), // 250ms * 2^4 = 4000ms (capped)
            (5, 4000), // 250ms * 2^5 = 8000ms → capped at 4000ms
        ];

        for (attempt, expected_ms) in expected_sequence {
            let backoff_ms = std::cmp::min(INITIAL_BACKOFF_MS * 2_u64.pow(attempt), MAX_BACKOFF_MS);
            assert_eq!(
                backoff_ms, expected_ms,
                "Attempt {}: expected {}ms, got {}ms",
                attempt, expected_ms, backoff_ms
            );
        }
    }
}
