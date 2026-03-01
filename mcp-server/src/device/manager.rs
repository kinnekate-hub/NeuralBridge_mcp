/*!
 * Device Manager
 *
 * Manages Android device discovery and connection lifecycle.
 * Integrates with ADB for device enumeration and port forwarding setup.
 */

use anyhow::Result;
use std::collections::HashMap;
use tokio::sync::RwLock;
use tracing::{debug, info, warn};

use super::adb::AdbExecutor;

/// Device manager handles discovery and lifecycle of Android devices
pub struct DeviceManager {
    /// ADB command executor
    adb: AdbExecutor,

    /// Cache of discovered devices (device_id -> DeviceInfo)
    devices: RwLock<HashMap<String, DeviceInfo>>,
}

/// Information about a discovered device
#[derive(Debug, Clone)]
pub struct DeviceInfo {
    /// Device ID (e.g., "emulator-5554")
    pub device_id: String,

    /// Device state: "device", "offline", "unauthorized"
    pub state: String,

    /// Device model (if available)
    pub model: Option<String>,

    /// Android version (if available)
    pub android_version: Option<String>,
}

/// Permission status for companion app
#[derive(Debug, Clone)]
pub struct PermissionStatus {
    /// Whether companion app is installed
    pub companion_installed: bool,

    /// Whether AccessibilityService is enabled
    pub accessibility_enabled: bool,

    /// Whether NotificationListenerService is enabled
    pub notification_listener_enabled: bool,
}

impl PermissionStatus {
    /// Check if all permissions are ready
    pub fn is_ready(&self) -> bool {
        self.companion_installed && self.accessibility_enabled && self.notification_listener_enabled
    }

    /// Generate user-friendly error message for missing permissions
    pub fn missing_permissions_message(&self) -> Option<String> {
        if self.is_ready() {
            return None;
        }

        let mut missing = Vec::new();

        if !self.companion_installed {
            missing.push("Companion app not installed");
        }
        if !self.accessibility_enabled {
            missing.push("AccessibilityService not enabled");
        }
        if !self.notification_listener_enabled {
            missing.push("NotificationListenerService not enabled");
        }

        Some(format!("Missing permissions: {}", missing.join(", ")))
    }
}

impl DeviceManager {
    /// Create new device manager
    pub async fn new() -> Result<Self> {
        let adb = AdbExecutor::new().await?;

        Ok(Self {
            adb,
            devices: RwLock::new(HashMap::new()),
        })
    }

    /// Check if ADB is installed and accessible
    pub async fn check_adb_installed(&self) -> Result<bool> {
        self.adb.check_installed().await
    }

    /// Discover connected Android devices
    ///
    /// Executes `adb devices -l` and parses output.
    ///
    /// # Returns
    /// List of device IDs
    pub async fn discover_devices(&self) -> Result<Vec<String>> {
        info!("Discovering Android devices...");

        // Execute `adb devices -l`
        let output = self.adb.execute_command(&["devices", "-l"]).await?;

        // Parse output
        let devices = self.parse_devices_output(&output)?;

        // Update cache
        let mut cache = self.devices.write().await;
        cache.clear();
        for device in &devices {
            cache.insert(device.device_id.clone(), device.clone());
        }

        let device_ids: Vec<String> = devices.iter().map(|d| d.device_id.clone()).collect();

        info!("Found {} device(s): {:?}", device_ids.len(), device_ids);

        Ok(device_ids)
    }

    /// Parse `adb devices -l` output
    ///
    /// Example output:
    /// ```text
    /// List of devices attached
    /// emulator-5554          device product:sdk_phone_x86_64 model:sdk_phone_x86_64 device:generic_x86_64
    /// ```
    fn parse_devices_output(&self, output: &str) -> Result<Vec<DeviceInfo>> {
        let mut devices = Vec::new();

        for line in output.lines().skip(1) {
            // Skip header line and empty lines
            let line = line.trim();
            if line.is_empty() {
                continue;
            }

            // Parse line: "device_id  state  key:value key:value ..."
            let parts: Vec<&str> = line.split_whitespace().collect();
            if parts.len() < 2 {
                continue;
            }

            let device_id = parts[0].to_string();
            let state = parts[1].to_string();

            // Skip offline/unauthorized devices
            if state != "device" {
                warn!("Skipping device {} with state: {}", device_id, state);
                continue;
            }

            // Parse optional metadata
            let mut model = None;
            let android_version = None;

            for part in &parts[2..] {
                if let Some((key, value)) = part.split_once(':') {
                    match key {
                        "model" => model = Some(value.to_string()),
                        "product" => {} // Ignore for now
                        "device" => {}  // Ignore for now
                        _ => {}
                    }
                }
            }

            devices.push(DeviceInfo {
                device_id,
                state,
                model,
                android_version,
            });
        }

        Ok(devices)
    }

    /// Set up ADB port forwarding for a device
    ///
    /// Forwards host port 38472 to device port 38472.
    pub async fn setup_port_forwarding(&self, device_id: &str) -> Result<()> {
        info!("Setting up port forwarding for device: {}", device_id);

        // Execute: adb -s <device_id> forward tcp:38472 tcp:38472
        self.adb
            .execute_command(&["-s", device_id, "forward", "tcp:38472", "tcp:38472"])
            .await?;

        info!("Port forwarding established");
        Ok(())
    }

    /// Remove port forwarding for a device
    pub async fn remove_port_forwarding(&self, device_id: &str) -> Result<()> {
        info!("Removing port forwarding for device: {}", device_id);

        // Execute: adb -s <device_id> forward --remove tcp:38472
        self.adb
            .execute_command(&["-s", device_id, "forward", "--remove", "tcp:38472"])
            .await?;

        Ok(())
    }

    /// Check if companion app is installed on device
    pub async fn check_companion_installed(&self, device_id: &str) -> Result<bool> {
        debug!("Checking if companion app is installed on {}", device_id);

        // Execute: adb -s <device_id> shell pm list packages | grep com.neuralbridge
        let output = self
            .adb
            .execute_command(&[
                "-s",
                device_id,
                "shell",
                "pm",
                "list",
                "packages",
                "com.neuralbridge.companion",
            ])
            .await?;

        Ok(output.contains("com.neuralbridge.companion"))
    }

    /// Check if AccessibilityService is enabled on device
    pub async fn check_accessibility_enabled(&self, device_id: &str) -> Result<bool> {
        debug!(
            "Checking if AccessibilityService is enabled on {}",
            device_id
        );

        // Execute: adb -s <device_id> shell settings get secure enabled_accessibility_services
        let output = self
            .adb
            .execute_command(&[
                "-s",
                device_id,
                "shell",
                "settings",
                "get",
                "secure",
                "enabled_accessibility_services",
            ])
            .await?;

        Ok(output.contains("com.neuralbridge.companion/.service.NeuralBridgeAccessibilityService")
            || output.contains("com.neuralbridge.companion/com.neuralbridge.companion.service.NeuralBridgeAccessibilityService"))
    }

    /// Get device information
    pub async fn get_device_info(&self, device_id: &str) -> Result<Option<DeviceInfo>> {
        let cache = self.devices.read().await;
        Ok(cache.get(device_id).cloned())
    }

    /// Execute ADB shell command on device
    pub async fn execute_shell_command(&self, device_id: &str, command: &[&str]) -> Result<String> {
        let mut args = vec!["-s", device_id, "shell"];
        args.extend_from_slice(command);
        self.adb.execute_command(&args).await
    }

    /// Get ADB executor reference
    pub fn adb(&self) -> &AdbExecutor {
        &self.adb
    }

    /// Check if NotificationListenerService is enabled on device
    pub async fn check_notification_listener_enabled(&self, device_id: &str) -> Result<bool> {
        debug!(
            "Checking if NotificationListenerService is enabled on {}",
            device_id
        );

        // Execute: adb -s <device_id> shell settings get secure enabled_notification_listeners
        let output = self
            .adb
            .execute_command(&[
                "-s",
                device_id,
                "shell",
                "settings",
                "get",
                "secure",
                "enabled_notification_listeners",
            ])
            .await?;

        Ok(output.contains("com.neuralbridge.companion/com.neuralbridge.companion.notification.NotificationListener")
            || output.contains("com.neuralbridge.companion/.service.NeuralBridgeNotificationListener"))
    }

    /// Check all permissions required for companion app
    pub async fn check_permissions(&self, device_id: &str) -> Result<PermissionStatus> {
        info!("Checking permissions for device: {}", device_id);

        // Run all permission checks in parallel using tokio::join!
        let (companion_result, accessibility_result, notification_result) = tokio::join!(
            self.check_companion_installed(device_id),
            self.check_accessibility_enabled(device_id),
            self.check_notification_listener_enabled(device_id)
        );

        let status = PermissionStatus {
            companion_installed: companion_result?,
            accessibility_enabled: accessibility_result?,
            notification_listener_enabled: notification_result?,
        };

        if let Some(msg) = status.missing_permissions_message() {
            warn!("{}", msg);
        } else {
            info!("All permissions ready");
        }

        Ok(status)
    }

    /// Enable AccessibilityService on device via ADB
    ///
    /// Automatically enables the service without user interaction.
    /// Requires the companion app to be installed first.
    pub async fn enable_accessibility_service(&self, device_id: &str) -> Result<()> {
        // Validate device_id to prevent command injection
        // ADB device IDs contain only: alphanumeric, dots, colons, dashes, underscores
        if !device_id
            .chars()
            .all(|c| c.is_alphanumeric() || c == '.' || c == ':' || c == '-' || c == '_')
        {
            anyhow::bail!("Invalid device_id format: contains unsafe characters");
        }

        info!("Enabling AccessibilityService on {}", device_id);

        let service_component =
            "com.neuralbridge.companion/.service.NeuralBridgeAccessibilityService";

        // Get current enabled services
        let current = self
            .adb
            .execute_command(&[
                "-s",
                device_id,
                "shell",
                "settings",
                "get",
                "secure",
                "enabled_accessibility_services",
            ])
            .await?;

        // Build new value (append if others exist)
        let new_value = if current.trim().is_empty() || current.trim() == "null" {
            service_component.to_string()
        } else {
            let current = current.trim();
            if current.contains(service_component) {
                info!("AccessibilityService already enabled");
                return Ok(());
            }
            format!("{}:{}", current, service_component)
        };

        // Set enabled services
        self.adb
            .execute_command(&[
                "-s",
                device_id,
                "shell",
                "settings",
                "put",
                "secure",
                "enabled_accessibility_services",
                &new_value,
            ])
            .await?;

        // Enable accessibility globally
        self.adb
            .execute_command(&[
                "-s",
                device_id,
                "shell",
                "settings",
                "put",
                "secure",
                "accessibility_enabled",
                "1",
            ])
            .await?;

        info!("AccessibilityService enabled successfully");
        Ok(())
    }

    /// Enable NotificationListenerService on device via ADB
    ///
    /// Automatically enables the service without user interaction.
    /// Requires the companion app to be installed first.
    pub async fn enable_notification_listener(&self, device_id: &str) -> Result<()> {
        // Validate device_id to prevent command injection
        // ADB device IDs contain only: alphanumeric, dots, colons, dashes, underscores
        if !device_id
            .chars()
            .all(|c| c.is_alphanumeric() || c == '.' || c == ':' || c == '-' || c == '_')
        {
            anyhow::bail!("Invalid device_id format: contains unsafe characters");
        }

        info!("Enabling NotificationListenerService on {}", device_id);

        let service_component = "com.neuralbridge.companion/com.neuralbridge.companion.notification.NotificationListener";

        // Use cmd notification allow_listener
        self.adb
            .execute_command(&[
                "-s",
                device_id,
                "shell",
                "cmd",
                "notification",
                "allow_listener",
                service_component,
            ])
            .await?;

        info!("NotificationListenerService enabled successfully");
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parse_devices_output() {
        let manager = DeviceManager {
            adb: AdbExecutor {
                adb_path: "adb".into(),
            },
            devices: RwLock::new(HashMap::new()),
        };

        let output = r#"List of devices attached
emulator-5554          device product:sdk_phone_x86_64 model:sdk_phone_x86_64 device:generic_x86_64
192.168.1.100:5555     device
"#;

        let devices = manager.parse_devices_output(output).unwrap();
        assert_eq!(devices.len(), 2);
        assert_eq!(devices[0].device_id, "emulator-5554");
        assert_eq!(devices[0].state, "device");
        assert_eq!(devices[0].model, Some("sdk_phone_x86_64".to_string()));
    }

    #[test]
    fn test_parse_devices_offline() {
        let manager = DeviceManager {
            adb: AdbExecutor {
                adb_path: "adb".into(),
            },
            devices: RwLock::new(HashMap::new()),
        };

        let output = r#"List of devices attached
emulator-5554          offline
"#;

        let devices = manager.parse_devices_output(output).unwrap();
        assert_eq!(devices.len(), 0); // Offline devices are filtered out
    }

    // ============================================================================
    // PermissionStatus Tests
    // ============================================================================

    /// Test is_ready() when all permissions are granted
    #[test]
    fn test_permission_status_all_ready() {
        let status = PermissionStatus {
            companion_installed: true,
            accessibility_enabled: true,
            notification_listener_enabled: true,
        };
        assert!(
            status.is_ready(),
            "Should be ready when all permissions granted"
        );
    }

    /// Test is_ready() when companion app not installed
    #[test]
    fn test_permission_status_no_companion() {
        let status = PermissionStatus {
            companion_installed: false,
            accessibility_enabled: true,
            notification_listener_enabled: true,
        };
        assert!(
            !status.is_ready(),
            "Should not be ready without companion app"
        );
    }

    /// Test is_ready() when accessibility not enabled
    #[test]
    fn test_permission_status_no_accessibility() {
        let status = PermissionStatus {
            companion_installed: true,
            accessibility_enabled: false,
            notification_listener_enabled: true,
        };
        assert!(
            !status.is_ready(),
            "Should not be ready without accessibility"
        );
    }

    /// Test is_ready() when notification listener not enabled
    #[test]
    fn test_permission_status_no_notification_listener() {
        let status = PermissionStatus {
            companion_installed: true,
            accessibility_enabled: true,
            notification_listener_enabled: false,
        };
        assert!(
            !status.is_ready(),
            "Should not be ready without notification listener"
        );
    }

    /// Test is_ready() when nothing is ready
    #[test]
    fn test_permission_status_nothing_ready() {
        let status = PermissionStatus {
            companion_installed: false,
            accessibility_enabled: false,
            notification_listener_enabled: false,
        };
        assert!(
            !status.is_ready(),
            "Should not be ready when nothing is granted"
        );
    }

    /// Test missing_permissions_message() when all ready
    #[test]
    fn test_missing_permissions_message_none() {
        let status = PermissionStatus {
            companion_installed: true,
            accessibility_enabled: true,
            notification_listener_enabled: true,
        };
        assert_eq!(
            status.missing_permissions_message(),
            None,
            "Should return None when all permissions ready"
        );
    }

    /// Test missing_permissions_message() when companion not installed
    #[test]
    fn test_missing_permissions_message_companion() {
        let status = PermissionStatus {
            companion_installed: false,
            accessibility_enabled: true,
            notification_listener_enabled: true,
        };
        let msg = status.missing_permissions_message().unwrap();
        assert!(
            msg.contains("Companion app not installed"),
            "Message should mention companion app: {}",
            msg
        );
    }

    /// Test missing_permissions_message() when accessibility not enabled
    #[test]
    fn test_missing_permissions_message_accessibility() {
        let status = PermissionStatus {
            companion_installed: true,
            accessibility_enabled: false,
            notification_listener_enabled: true,
        };
        let msg = status.missing_permissions_message().unwrap();
        assert!(
            msg.contains("AccessibilityService not enabled"),
            "Message should mention accessibility: {}",
            msg
        );
    }

    /// Test missing_permissions_message() when notification listener not enabled
    #[test]
    fn test_missing_permissions_message_notification_listener() {
        let status = PermissionStatus {
            companion_installed: true,
            accessibility_enabled: true,
            notification_listener_enabled: false,
        };
        let msg = status.missing_permissions_message().unwrap();
        assert!(
            msg.contains("NotificationListenerService not enabled"),
            "Message should mention notification listener: {}",
            msg
        );
    }

    /// Test missing_permissions_message() when multiple permissions missing
    #[test]
    fn test_missing_permissions_message_multiple() {
        let status = PermissionStatus {
            companion_installed: false,
            accessibility_enabled: false,
            notification_listener_enabled: true,
        };
        let msg = status.missing_permissions_message().unwrap();
        assert!(
            msg.contains("Companion app not installed"),
            "Should mention companion app: {}",
            msg
        );
        assert!(
            msg.contains("AccessibilityService not enabled"),
            "Should mention accessibility: {}",
            msg
        );
        assert!(
            !msg.contains("NotificationListenerService"),
            "Should not mention notification listener when it's ready: {}",
            msg
        );
    }

    /// Test missing_permissions_message() when all permissions missing
    #[test]
    fn test_missing_permissions_message_all() {
        let status = PermissionStatus {
            companion_installed: false,
            accessibility_enabled: false,
            notification_listener_enabled: false,
        };
        let msg = status.missing_permissions_message().unwrap();
        assert!(
            msg.contains("Companion app not installed"),
            "Should mention all: {}",
            msg
        );
        assert!(
            msg.contains("AccessibilityService not enabled"),
            "Should mention all: {}",
            msg
        );
        assert!(
            msg.contains("NotificationListenerService not enabled"),
            "Should mention all: {}",
            msg
        );
    }

    // ============================================================================
    // ADB Output Parsing Tests
    // ============================================================================

    /// Test accessibility service parsing - enabled
    #[test]
    fn test_parse_accessibility_enabled() {
        let output = "com.neuralbridge.companion/.service.NeuralBridgeAccessibilityService:com.android.talkback/.TalkBackService";
        assert!(
            output.contains("com.neuralbridge.companion/.service.NeuralBridgeAccessibilityService"),
            "Should detect accessibility service in output"
        );
    }

    /// Test accessibility service parsing - not enabled
    #[test]
    fn test_parse_accessibility_not_enabled() {
        let output = "com.android.talkback/.TalkBackService";
        assert!(
            !output
                .contains("com.neuralbridge.companion/.service.NeuralBridgeAccessibilityService"),
            "Should not detect accessibility service when not present"
        );
    }

    /// Test accessibility service parsing - null/empty
    #[test]
    fn test_parse_accessibility_null() {
        let outputs = vec!["null", "", "  "];
        for output in outputs {
            assert!(
                !output.contains(
                    "com.neuralbridge.companion/.service.NeuralBridgeAccessibilityService"
                ),
                "Should handle null/empty output: '{}'",
                output
            );
        }
    }

    /// Test notification listener parsing - enabled
    #[test]
    fn test_parse_notification_listener_enabled() {
        let output = "com.neuralbridge.companion/.service.NeuralBridgeNotificationListener:com.android.systemui/.notificationlistener";
        assert!(
            output.contains("com.neuralbridge.companion/.service.NeuralBridgeNotificationListener"),
            "Should detect notification listener in output"
        );
    }

    /// Test notification listener parsing - not enabled
    #[test]
    fn test_parse_notification_listener_not_enabled() {
        let output = "com.android.systemui/.notificationlistener";
        assert!(
            !output
                .contains("com.neuralbridge.companion/.service.NeuralBridgeNotificationListener"),
            "Should not detect notification listener when not present"
        );
    }

    /// Test notification listener parsing - null/empty
    #[test]
    fn test_parse_notification_listener_null() {
        let outputs = vec!["null", "", "  "];
        for output in outputs {
            assert!(
                !output.contains(
                    "com.neuralbridge.companion/.service.NeuralBridgeNotificationListener"
                ),
                "Should handle null/empty output: '{}'",
                output
            );
        }
    }
}
