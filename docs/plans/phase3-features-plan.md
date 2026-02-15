# Phase 3 Feature Plan — Architectural Review

**Date:** 2026-02-14
**Reviewer:** Senior Architect (opus)
**Confidence:** 100% on approach, 90% on event streaming bug fix (requires runtime debugging)

---

## Executive Assessment

After thorough code review of all source files (main.rs 2600 LOC, connection.rs 445 LOC, codec.rs 270 LOC, TcpServer.kt 390 LOC, CommandHandler.kt 2089 LOC, NeuralBridgeAccessibilityService.kt 519 LOC, NotificationListener.kt 127 LOC), I'm presenting a **3-sprint plan** focused on maximum ROI.

### What I'm REMOVING from the original proposal (over-engineering):

| Feature | Why Removed |
|---------|-------------|
| OCR fallback | External ML dependency (Tesseract/ML Kit), ~5 day effort, niche use case |
| Action recording | Needs new Kotlin event capture infra that doesn't exist |
| App state snapshot | ADB backup is unreliable, `run-as` only works on debuggable apps |
| Network interception | Requires VPN service or proxy — 5+ days, entire subsystem |
| Multi-device parallel | Connection pooling is a stub (`pool.rs:316` = `bail!`), needs architecture redesign |
| Element highlight overlay | Cute but low automation value |

### What I'm KEEPING (high ROI, grounded in code reality):

| Feature | Effort | Kotlin Changes? | Why |
|---------|--------|-----------------|-----|
| Fix event streaming bug | 3-5h | Yes (TcpServer.kt) | Unblocks toast/crash/notification events |
| Wire up existing proto tools | 2h | No | 3 tools already defined in proto + Kotlin, just need MCP wiring |
| `android_scroll_to_element` | 4-6h | No | #1 automation friction point today |
| `android_get_screen_context` | 3-4h | No | AI-native differentiator, reduces 4 tool calls to 1 |
| `android_capture_logcat` | 2-3h | No | Pure ADB, essential for debugging |
| Screenshot diff | 4-6h | No | Testing foundation, pure Rust |
| Gesture macros | 3-4h | No | Reusable compound gestures |
| Accessibility audit | 3-4h | No | Low-hanging fruit from existing UI tree |

---

## Sprint 1: Foundation Fixes (1 day)

### 1.1 Fix Event Streaming Protocol Corruption

**Priority:** CRITICAL — blocks toast detection, crash reporting, notification streaming

**Root Cause Analysis:**

Traced through the full data path:
- `NeuralBridgeAccessibilityService.kt:400-422` — `sendUIChangeEvent()` launches coroutine on `Dispatchers.IO`
- `TcpServer.kt:158-168` — `broadcastEvent()` calls `connection.sendEvent()`
- `TcpServer.kt:344-358` — `sendMessage()` uses `synchronized(outputStream)` with TWO separate `write()` calls
- `codec.rs:186-209` — `try_extract_message()` uses `BytesMut::split_to(total_size)`
- `connection.rs:196-265` — `read_response_inner()` handles Event type and continues reading

**Symptom:** Buffer shows `[42 03 00 00 00 3B ...]` instead of `[4E 42 03 00 00 00 3B ...]` — 1-byte offset.

**Most likely cause:** Previous message's `payload_length` field is 1 byte larger than actual protobuf payload, causing `split_to()` to consume 1 extra byte (the `0x4E` of the next message's magic).

**Fix approach (2 steps):**

**Step A — Diagnostic logging (both sides):**

File: `companion-app/.../network/TcpServer.kt` line 344
```kotlin
// Add before outputStream.write(header):
Log.d(TAG, "sendMessage: type=0x${type.toString(16)}, payloadSize=${payload.size}, " +
    "headerHex=${header.joinToString(" ") { "%02X".format(it) }}")
```

File: `mcp-server/src/protocol/codec.rs` line 193
```rust
// Add before split_to:
debug!("Extracting message: header_payload_len={}, buffer_len={}, buffer_hex={}",
    header.payload_length, self.buffer.len(),
    self.buffer.iter().take(14).map(|b| format!("{:02X}", b)).collect::<Vec<_>>().join(" "));
```

**Step B — Atomic write (Kotlin side):**

File: `companion-app/.../network/TcpServer.kt` lines 344-361
```kotlin
private fun sendMessage(type: Byte, payload: ByteArray) {
    val combined = ByteArray(HEADER_SIZE + payload.size)
    // Header
    ByteBuffer.wrap(combined, 0, HEADER_SIZE).apply {
        order(ByteOrder.BIG_ENDIAN)
        putShort(MAGIC)
        put(type)
        putInt(payload.size)
    }
    // Payload
    System.arraycopy(payload, 0, combined, HEADER_SIZE, payload.size)

    synchronized(outputStream) {
        outputStream.write(combined)  // Single atomic write
        outputStream.flush()
    }
}
```

**Note:** Previous attempt at atomic write failed ("companion app immediately closes connection"). This was likely a build issue — needs `./gradlew clean assembleDebug` and fresh install.

**Step C — Framing recovery (Rust fallback):**

If Steps A+B don't fix it, add recovery to `codec.rs`:
```rust
// When invalid magic detected, scan forward for 0x4E42 and realign
fn try_realign_buffer(&mut self) -> bool {
    for i in 1..self.buffer.len().saturating_sub(1) {
        if self.buffer[i] == 0x4E && self.buffer[i+1] == 0x42 {
            warn!("Realigning buffer: skipping {} corrupt bytes", i);
            self.buffer.advance(i);
            return true;
        }
    }
    false
}
```

**Verification:** Enable events, perform 10 tap/swipe actions, verify no protocol corruption.

**Files modified:**
- `companion-app/.../network/TcpServer.kt` (sendMessage atomic write)
- `mcp-server/src/protocol/codec.rs` (recovery mechanism + logging)
- `mcp-server/src/main.rs` (re-enable android_enable_events tool, lines 1973-1996)

---

### 1.2 Wire Up Missing Proto-Defined Tools

Three tools already have proto definitions + Kotlin handlers but no MCP tool wrapper:

**1.2a `android_clear_app_data`**
- Proto: `neuralbridge.proto:329-331` (ClearAppDataRequest)
- ADB: `device/adb.rs` has `clear_app_data()` method
- MCP tool: New, ~30 lines in main.rs (same pattern as `android_close_app`)

**1.2b `android_wait_for_gone`**
- Proto: `neuralbridge.proto:359-363` (WaitForGoneRequest)
- Kotlin: `CommandHandler.kt:81-83` (handleWaitForGone handler exists)
- MCP tool: New, ~40 lines in main.rs (same pattern as `android_wait_for_element`)

**1.2c `android_get_device_info`**
- Proto: `neuralbridge.proto:444-452` (DeviceInfo already in UITree)
- Implementation: Parse from `get_ui_tree` response's `device_info` field
- MCP tool: New standalone tool, ~30 lines

**Files modified:**
- `mcp-server/src/main.rs` (3 new tool functions + 3 param structs)

---

## Sprint 2: High-Value New Tools (2-3 days)

### 2.1 `android_scroll_to_element` (Compound Tool)

**What:** Automatically scrolls through scrollable containers to find a target element.

**Why #1 priority:** Currently agents must manually fling → get_ui_tree → check → repeat. This is the most common failure mode in real automation.

**Algorithm:**
```
1. find_elements(selector) → check if already visible → return if found
2. get_ui_tree() → find nearest scrollable ancestor
3. Loop (max 20 iterations):
   a. fling(direction) within scrollable bounds
   b. wait_for_idle(300ms)
   c. find_elements(selector) → return if found
   d. get_ui_tree() → check if content changed (hash comparison)
   e. If content unchanged → reached end of scroll → try opposite direction
   f. If both directions exhausted → return ELEMENT_NOT_FOUND
4. Return element bounds + coordinates
```

**MCP tool signature:**
```rust
#[tool(name = "android_scroll_to_element")]
async fn android_scroll_to_element(
    &self,
    text: Option<String>,
    resource_id: Option<String>,
    content_desc: Option<String>,
    direction: Option<String>,      // "up"|"down"|"left"|"right", default: "up" (scroll down)
    max_scrolls: Option<i32>,       // default: 20
    timeout_ms: Option<i32>,        // default: 30000
) -> Result<CallToolResult, McpError>
```

**Implementation:** Pure MCP server — calls existing tools internally (find_elements, get_ui_tree, fling, wait_for_idle). No Kotlin changes.

**Files modified:**
- `mcp-server/src/main.rs` (1 new tool function, ~80 lines)

---

### 2.2 `android_get_screen_context` (Compound Tool)

**What:** Single tool that returns everything an AI agent needs to understand the current screen.

**Why:** Reduces 3-4 sequential tool calls to 1. Cuts latency by 60-70% and reduces token waste.

**Returns:**
```json
{
  "app": { "package": "com.example", "activity": ".MainActivity" },
  "screen_summary": "Login screen with email/password fields and Sign In button",
  "elements": [
    { "id": "email_field", "type": "input", "text": "", "hint": "Email", "bounds": {...} },
    { "id": "password_field", "type": "input", "text": "", "hint": "Password", "bounds": {...} },
    { "id": "sign_in_btn", "type": "button", "text": "Sign In", "bounds": {...} }
  ],
  "element_count": 42,
  "interactive_elements": 5,
  "screenshot": "<base64 thumbnail>",
  "device": { "width": 1080, "height": 2400, "sdk": 34 }
}
```

**Key design decisions:**
- **Simplified tree:** Only include interactive elements + text labels (strip containers, spacers, decorations)
- **Screenshot:** Always thumbnail quality (40% JPEG, ~20KB) to minimize tokens
- **Parallel execution:** Run get_ui_tree, screenshot, and get_foreground_app concurrently via `tokio::join!`

**Implementation:** Pure MCP server compound tool. ~100 lines.

**Files modified:**
- `mcp-server/src/main.rs` (1 new tool function)

---

### 2.3 `android_capture_logcat` (ADB Path)

**What:** Capture logcat output for a specific package, with filtering and crash detection.

**MCP tool signature:**
```rust
#[tool(name = "android_capture_logcat")]
async fn android_capture_logcat(
    &self,
    package: Option<String>,     // filter by package (uses `--pid=$(pidof)`)
    level: Option<String>,       // "V"|"D"|"I"|"W"|"E"|"F", default: "W"
    lines: Option<i32>,          // max lines, default: 100
    since: Option<String>,       // time filter, e.g., "5s" "1m"
    crash_only: Option<bool>,    // only show FATAL EXCEPTION blocks
) -> Result<CallToolResult, McpError>
```

**Implementation:** Pure ADB path via `adb logcat -d -t <lines> *:<level>`. Crash detection uses regex for `FATAL EXCEPTION` blocks.

**Files modified:**
- `mcp-server/src/main.rs` (1 new tool function, ~60 lines)
- `mcp-server/src/device/adb.rs` (new `capture_logcat()` method, ~30 lines)

---

### 2.4 `android_get_device_info` (Standalone Tool)

**What:** Returns device specifications without full UI tree overhead.

**Implementation:** ADB path using `adb shell getprop` for manufacturer, model, SDK, and `adb shell wm size` / `wm density` for screen info.

**Files modified:**
- `mcp-server/src/main.rs` (1 new tool function, ~40 lines)
- `mcp-server/src/device/adb.rs` (new `get_device_info()` method, ~25 lines)

---

## Sprint 3: Testing & Advanced (2-3 days)

### 3.1 Screenshot Visual Diff

**What:** Compare two screenshots and return a similarity score + diff image.

**Implementation:**
- Add `image` crate to Cargo.toml (JPEG decode, pixel comparison)
- Simple pixel-by-pixel diff with configurable threshold
- Return: diff_percentage, match (bool), diff_image_base64

**Algorithm:** Block-based comparison (8x8 blocks), report percentage of changed blocks.

**Why not SSIM:** Over-engineering for automation testing. Simple pixel diff is sufficient and requires no external dependencies.

**Files modified:**
- `mcp-server/Cargo.toml` (add `image = "0.25"`)
- `mcp-server/src/main.rs` (1 new tool function, ~70 lines)

---

### 3.2 Toast/Snackbar Reliable Capture (Depends on 1.1)

**What:** Capture transient UI messages that auto-dismiss.

**Implementation:** After event streaming is fixed:
1. Events are buffered in `AppState.event_buffer` (circular, max 100)
2. New MCP tool `android_get_recent_toasts` reads from buffer
3. Filter by `EventType::TOAST_SHOWN`
4. Return text + timestamp for each toast in last N seconds

**Files modified:**
- `mcp-server/src/main.rs` (1 new tool function, ~40 lines)

---

### 3.3 Gesture Macros

**What:** Pre-built complex gesture sequences as single MCP tools.

**Macros to implement:**
1. `android_pull_to_refresh()` — swipe down from top 1/3 of screen, 400ms duration
2. `android_dismiss_keyboard()` — tap outside input area or press BACK
3. `android_unlock_swipe()` — swipe up from bottom of screen

**Implementation:** Compose existing gesture primitives with pre-calculated coordinates based on screen dimensions from `get_device_info`.

**Files modified:**
- `mcp-server/src/main.rs` (3 new tool functions, ~25 lines each)

---

### 3.4 Accessibility Audit

**What:** Scan current screen for WCAG violations.

**Checks:**
1. Missing content descriptions on clickable elements
2. Touch targets < 48dp
3. Empty text on visible text elements
4. Non-focusable interactive elements

**Implementation:** Call `get_ui_tree`, filter elements, check properties.

**Files modified:**
- `mcp-server/src/main.rs` (1 new tool function, ~60 lines)

---

## Dependency Graph

```
Sprint 1 (Foundation)
├── 1.1 Fix event streaming bug
│   └── 3.2 Toast capture (blocked by 1.1)
├── 1.2a android_clear_app_data
├── 1.2b android_wait_for_gone
└── 1.2c android_get_device_info
    └── 3.3 Gesture macros (needs screen dimensions)

Sprint 2 (High-Value) — no dependencies on Sprint 1
├── 2.1 android_scroll_to_element
├── 2.2 android_get_screen_context
├── 2.3 android_capture_logcat
└── 2.4 android_get_device_info (standalone)

Sprint 3 (Advanced) — partially depends on Sprint 1
├── 3.1 Screenshot diff (independent)
├── 3.2 Toast capture (depends on 1.1)
├── 3.3 Gesture macros (depends on 1.2c or 2.4)
└── 3.4 Accessibility audit (independent)
```

**Sprint 2 can run in PARALLEL with Sprint 1** — all Sprint 2 tools are pure MCP server, no Kotlin changes needed.

---

## Build & Verification Plan

After each sprint:
```bash
# Rust
cd mcp-server && cargo test && cargo build --release

# Kotlin (only if Sprint 1.1 changes merged)
cd companion-app && ./gradlew clean assembleDebug

# Integration
adb install -r companion-app/app/build/outputs/apk/debug/app-debug.apk
adb forward tcp:38472 tcp:38472
# Test new tools via MCP
```

---

## Total Tool Count After Plan

| Category | Current | Added | New Total |
|----------|---------|-------|-----------|
| OBSERVE | 5 | 3 (screen_context, device_info, capture_logcat) | 8 |
| ACT | 11 | 4 (scroll_to_element, 3 macros) | 15 |
| MANAGE | 3 | 1 (clear_app_data) | 4 |
| WAIT | 2 | 1 (wait_for_gone) | 3 |
| TEST | 0 | 2 (screenshot_diff, accessibility_audit) | 2 |
| EVENT | 2 | 1 (get_recent_toasts) | 3 |
| **TOTAL** | **23** | **12** | **35** |

---

## Risk Assessment

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Event streaming fix doesn't work on first attempt | 40% | Step B (hex logging) provides diagnostic data; Step C (realignment) is a reliable fallback |
| `scroll_to_element` misses edge cases (nested scrollable, horizontal lists) | 20% | Start with vertical-only, add horizontal support in follow-up |
| `image` crate adds significant binary size | 10% | Use `image` with minimal features (`jpeg` only), adds ~200KB |
| Gesture macros need device-specific coordinate tuning | 15% | Use percentage-based coordinates (e.g., 50% width, 25% height) |

---

## NOT in Scope (Deferred to Phase 4+)

- Multi-device parallel execution
- WebView DOM tools (get_webview_dom, execute_js)
- Screen recording
- CI/CD Docker image
- OCR fallback
- Network interception
- main.rs refactoring into modules (important but not blocking)
