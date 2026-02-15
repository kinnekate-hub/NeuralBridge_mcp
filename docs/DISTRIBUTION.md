# NeuralBridge Distribution Guide

Complete guide for packaging and distributing NeuralBridge to end users.

---

## 📦 What You're Distributing

NeuralBridge consists of two components:
1. **MCP Server** (Rust) - Runs on user's computer (Linux/macOS/Windows)
2. **Companion App** (APK) - Runs on Android device (API 24+)

---

## 🚀 Quick Start for Distributors

### Step 1: Build Release Artifacts

```bash
# Build MCP Server (all platforms)
cd mcp-server
cargo build --release

# Build Android APK
cd ../companion-app
./gradlew assembleRelease
./gradlew bundleRelease  # For Google Play Bundle (optional)
```

**Output:**
- MCP Server: `mcp-server/target/release/neuralbridge-mcp` (~2.8 MB)
- Android APK: `companion-app/app/build/outputs/apk/release/app-release-unsigned.apk` (~7.5 MB)

### Step 2: Sign Android APK (Required for Distribution)

```bash
# Generate keystore (one-time)
keytool -genkey -v -keystore neuralbridge.keystore \
  -alias neuralbridge -keyalg RSA -keysize 2048 -validity 10000

# Sign APK
jarsigner -verbose -sigalg SHA256withRSA -digestalg SHA-256 \
  -keystore neuralbridge.keystore \
  app/build/outputs/apk/release/app-release-unsigned.apk \
  neuralbridge

# Zipalign (optimize)
$ANDROID_HOME/build-tools/34.0.0/zipalign -v 4 \
  app-release-unsigned.apk \
  neuralbridge-companion.apk
```

---

## 📋 Distribution Channels

### Option 1: GitHub Releases (Recommended)

**Pros:** Free, version control, automatic updates, trusted source
**Cons:** Users must manually download

**Setup:**
1. Create release on GitHub
2. Upload platform-specific binaries
3. Include installation instructions

**Example Release Structure:**
```
neuralbridge-v1.0.0/
├── neuralbridge-mcp-linux-x64.tar.gz
├── neuralbridge-mcp-macos-arm64.tar.gz
├── neuralbridge-mcp-windows-x64.zip
├── neuralbridge-companion-v1.0.0.apk
├── INSTALL.md
└── CHANGELOG.md
```

**GitHub Actions Workflow** (auto-build on tag):
```yaml
name: Release
on:
  push:
    tags:
      - 'v*'
jobs:
  build:
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v3
      - uses: actions-rs/toolchain@v1
      - run: cargo build --release
      - uses: actions/upload-artifact@v3
        with:
          name: neuralbridge-mcp-${{ matrix.os }}
          path: target/release/neuralbridge-mcp*
```

### Option 2: Cargo Publish (Rust Developers)

**Pros:** Easy installation for Rust users (`cargo install`)
**Cons:** Requires Rust toolchain

```bash
# Publish to crates.io
cd mcp-server
cargo publish

# Users install with:
cargo install neuralbridge-mcp
```

### Option 3: F-Droid (Android APK)

**Pros:** Trusted by privacy-conscious users, auto-updates
**Cons:** Review process, build from source requirement

**Submission:**
1. Fork [fdroiddata](https://gitlab.com/fdroid/fdroiddata)
2. Add metadata file: `metadata/com.neuralbridge.companion.yml`
3. Submit merge request

**Important:** F-Droid builds from source. Ensure your build is reproducible.

### Option 4: Self-Hosted (Full Control)

**Pros:** Full control, custom analytics
**Cons:** Hosting costs, security responsibility

```bash
# Host on your server
scp neuralbridge-companion.apk user@server:/var/www/downloads/
scp neuralbridge-mcp user@server:/var/www/downloads/

# Generate SHA256 checksums
sha256sum neuralbridge-* > checksums.txt
```

---

## 📱 Android APK Distribution (CRITICAL)

### ⚠️ Google Play NOT Viable

**Reason:** AccessibilityService policy restrictions
**Quote from Play Policy:** "Apps must not use accessibility services for remote call audio recording."

While NeuralBridge doesn't do this, broad AccessibilityService permissions trigger manual review → rejection.

### ✅ Sideloading Instructions (Include in Docs)

**For Android 15+ Users:**
1. Download APK from GitHub releases
2. Install APK (Files app → Downloads → tap APK)
3. **Settings → Apps → Special app access → Install unknown apps**
4. Enable "Files" or your installer app
5. Complete installation
6. Open NeuralBridge
7. **Settings → Apps → NeuralBridge → Advanced**
8. Enable **"Allow restricted settings"** (required for AccessibilityService)
9. **Settings → Accessibility → NeuralBridge**
10. Enable the service

**Script for ADB Installation** (developers):
```bash
#!/bin/bash
# install-neuralbridge.sh

echo "Installing NeuralBridge Companion App..."
adb install -r neuralbridge-companion.apk

echo "Enabling AccessibilityService..."
adb shell settings put secure enabled_accessibility_services \
  com.dsapps.pocketledger/.NeuralBridgeAccessibilityService
adb shell settings put secure accessibility_enabled 1

echo "Setup complete! Launch the app to verify."
```

---

## 🔧 MCP Server Installation

### Linux/macOS (Recommended)

**Option A: Pre-built Binary**
```bash
# Download and extract
wget https://github.com/yourorg/neuralbridge/releases/latest/download/neuralbridge-mcp-linux-x64.tar.gz
tar -xzf neuralbridge-mcp-linux-x64.tar.gz

# Install to PATH
sudo mv neuralbridge-mcp /usr/local/bin/
sudo chmod +x /usr/local/bin/neuralbridge-mcp

# Verify
neuralbridge-mcp --version
```

**Option B: Build from Source**
```bash
git clone https://github.com/yourorg/neuralbridge.git
cd neuralbridge/mcp-server
cargo build --release
sudo cp target/release/neuralbridge-mcp /usr/local/bin/
```

### Windows

**Option A: Pre-built Binary**
```powershell
# Download neuralbridge-mcp-windows-x64.zip
# Extract to C:\Program Files\NeuralBridge\
# Add to PATH:
setx PATH "%PATH%;C:\Program Files\NeuralBridge"
```

**Option B: Chocolatey Package** (future)
```powershell
choco install neuralbridge-mcp
```

---

## 📚 Required User Documentation

### INSTALL.md (Include in Release)

```markdown
# Installation Guide

## Prerequisites
- Android device (API 24+, Android 7.0+)
- Computer with ADB installed
- USB cable or wireless ADB connection

## Step 1: Install MCP Server
[Platform-specific instructions]

## Step 2: Install Companion App
1. Download `neuralbridge-companion.apk`
2. Enable "Install from unknown sources"
3. Install APK
4. Enable AccessibilityService (Settings → Accessibility)

## Step 3: Connect Device
```bash
# USB connection
adb devices

# Or wireless (Android 11+)
adb pair <device-ip>:5555
adb connect <device-ip>:5555
```

## Step 4: Start MCP Server
```bash
# Auto-discover connected devices
neuralbridge-mcp --auto-discover

# Or specify device
neuralbridge-mcp --device emulator-5554
```

## Step 5: Test Connection
Use with Claude Desktop, Cursor, or any MCP client.
```

### TROUBLESHOOTING.md

```markdown
# Troubleshooting

## "Device not found"
- Run `adb devices` to verify connection
- Enable USB debugging (Settings → Developer Options)
- Authorize computer (tap "Allow" on device)

## "AccessibilityService not running"
- Settings → Accessibility → NeuralBridge → Enable
- Android 15+: Enable "Allow restricted settings" first

## "MediaProjection consent required"
- First screenshot request shows system dialog
- Tap "Start now" or "Allow"
- Android 14+: Permission resets after app restart
- Fallback: ADB screencap (slower but works)

## "Port 38472 already in use"
- Another instance is running
- Kill process: `pkill neuralbridge-mcp`
- Or change port in config
```

---

## 🔒 Security & Trust

### Code Signing (Recommended)

**MCP Server:**
```bash
# macOS: Sign with Developer ID
codesign --sign "Developer ID Application: Your Name" neuralbridge-mcp

# Windows: Sign with Authenticode
signtool sign /f cert.pfx /p password /t http://timestamp.digicert.com neuralbridge-mcp.exe
```

**Android APK:**
```bash
# Sign with same keystore for all releases
jarsigner -keystore neuralbridge.keystore app-release-unsigned.apk neuralbridge
```

### Checksums & Verification

```bash
# Generate SHA256 checksums
sha256sum neuralbridge-mcp-* neuralbridge-companion.apk > SHA256SUMS.txt

# Sign checksums
gpg --clearsign SHA256SUMS.txt

# Users verify:
sha256sum -c SHA256SUMS.txt
gpg --verify SHA256SUMS.txt.asc
```

---

## 📊 Analytics & Telemetry (Optional)

**Privacy-First Approach:**
- No telemetry by default
- Opt-in crash reporting (Sentry)
- Anonymous usage stats (session count, OS version, errors)

**Implementation:**
```rust
// mcp-server/src/telemetry.rs
pub struct Telemetry {
    enabled: bool,
    session_id: Uuid,
}

impl Telemetry {
    pub fn new() -> Self {
        // Read user preference from config
        let enabled = Config::get("telemetry_enabled").unwrap_or(false);
        Self { enabled, session_id: Uuid::new_v4() }
    }

    pub fn track_event(&self, event: &str) {
        if !self.enabled { return; }
        // Send to analytics endpoint
    }
}
```

---

## 🚢 Release Checklist

- [ ] Update version in `Cargo.toml` and `build.gradle`
- [ ] Update CHANGELOG.md
- [ ] Run full test suite (`cargo test`, `./gradlew test`)
- [ ] Build release artifacts (all platforms)
- [ ] Sign APK with release keystore
- [ ] Generate checksums (SHA256SUMS.txt)
- [ ] Create Git tag (`git tag -a v1.0.0 -m "Release v1.0.0"`)
- [ ] Push tag (`git push origin v1.0.0`)
- [ ] Create GitHub Release with artifacts
- [ ] Update documentation (README, INSTALL.md)
- [ ] Announce on social media / mailing list

---

## 🔄 Auto-Update Strategy (Future)

### MCP Server
- Check GitHub releases API for latest version
- Prompt user to download new version
- Or use platform package managers (Homebrew, Chocolatey)

### Companion App
- Built-in update checker (query GitHub API)
- Download APK → prompt user to install
- Or submit to F-Droid for automatic updates

**Example Update Check:**
```rust
// mcp-server/src/update_checker.rs
pub async fn check_for_updates() -> Result<Option<Version>> {
    let current = env!("CARGO_PKG_VERSION");
    let latest = reqwest::get("https://api.github.com/repos/yourorg/neuralbridge/releases/latest")
        .await?
        .json::<Release>()
        .await?
        .tag_name;

    if Version::parse(&latest)? > Version::parse(current)? {
        Ok(Some(Version::parse(&latest)?))
    } else {
        Ok(None)
    }
}
```

---

## 📞 Support & Community

**Setup:**
- GitHub Discussions for Q&A
- GitHub Issues for bug reports
- Discord/Slack for real-time support (optional)
- Email: support@neuralbridge.dev

**Documentation Sites:**
- docs.neuralbridge.dev (MkDocs or Docusaurus)
- Include: API reference, tutorials, examples, troubleshooting

---

## ⚖️ Licensing & Legal

**Recommended License:** MIT or Apache 2.0
**Reason:** Permissive, allows commercial use, widely adopted

**Include in All Releases:**
- LICENSE file
- NOTICE file (for Apache 2.0)
- CONTRIBUTING.md
- CODE_OF_CONDUCT.md

**APK Permissions Disclosure:**
```
Required Permissions:
- ACCESSIBILITY_SERVICE: UI automation (core functionality)
- INTERNET: TCP server for MCP communication
- FOREGROUND_SERVICE: Keep service alive
- NOTIFICATION_ACCESS: Read notifications (optional feature)

Optional Permissions:
- BIND_NOTIFICATION_LISTENER_SERVICE: Full notification content
```

---

## 📈 Success Metrics

Track (anonymously, opt-in):
- Downloads per release
- Active installations (ping every 7 days)
- Average session duration
- Most-used MCP tools
- Error rates by Android version
- Crash-free sessions percentage

**Privacy:** Use aggregate data only, no PII collection.

---

## Next Steps

1. ✅ Build release artifacts
2. ✅ Sign APK with release keystore
3. ✅ Create GitHub Release
4. ⏳ Write INSTALL.md and TROUBLESHOOTING.md
5. ⏳ Setup automated builds (GitHub Actions)
6. ⏳ Submit to F-Droid (optional)
7. ⏳ Create documentation site

**Questions?** Open an issue or contact the maintainers.
