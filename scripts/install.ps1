# NeuralBridge Installation Script for Windows
# Run with: powershell -ExecutionPolicy Bypass -File install.ps1

param(
    [string]$InstallDir = "$env:ProgramFiles\NeuralBridge"
)

$ErrorActionPreference = "Stop"

$VERSION = "1.0.0"
$REPO = "yourorg/neuralbridge"  # TODO: Update with actual GitHub repo
$BINARY_NAME = "neuralbridge-mcp.exe"

Write-Host "NeuralBridge MCP Server Installer v$VERSION" -ForegroundColor Green
Write-Host "==========================================="
Write-Host ""

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "Warning: Not running as Administrator" -ForegroundColor Yellow
    Write-Host "Installation to Program Files requires admin rights" -ForegroundColor Yellow
    Write-Host "Re-run as Administrator or install to user directory" -ForegroundColor Yellow
    Write-Host ""

    $userChoice = Read-Host "Install to user directory instead? (y/n)"
    if ($userChoice -eq "y") {
        $InstallDir = "$env:LOCALAPPDATA\NeuralBridge"
    } else {
        Write-Host "Installation cancelled. Please re-run as Administrator." -ForegroundColor Red
        exit 1
    }
}

# Detect architecture
$arch = if ([Environment]::Is64BitOperatingSystem) { "x64" } else { "x86" }
Write-Host "Detected platform: windows-$arch" -ForegroundColor Green
Write-Host ""

# Download URL
$downloadUrl = "https://github.com/$REPO/releases/latest/download/$BINARY_NAME-windows-$arch.zip"

Write-Host "Downloading from: $downloadUrl"

# Create temp directory
$tempDir = [System.IO.Path]::GetTempPath() + [System.Guid]::NewGuid().ToString()
New-Item -ItemType Directory -Path $tempDir | Out-Null

try {
    # Download binary
    $zipPath = Join-Path $tempDir "neuralbridge.zip"
    Invoke-WebRequest -Uri $downloadUrl -OutFile $zipPath -UseBasicParsing

    # Extract
    Write-Host "Extracting..."
    Expand-Archive -Path $zipPath -DestinationPath $tempDir -Force

    # Create install directory
    if (-not (Test-Path $InstallDir)) {
        New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
    }

    # Copy binary
    Write-Host "Installing to $InstallDir..."
    Copy-Item -Path (Join-Path $tempDir $BINARY_NAME) -Destination (Join-Path $InstallDir $BINARY_NAME) -Force

    # Add to PATH if not already there
    $currentPath = [Environment]::GetEnvironmentVariable("Path", "User")
    if ($currentPath -notlike "*$InstallDir*") {
        Write-Host "Adding to PATH..."
        $newPath = "$currentPath;$InstallDir"
        [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
        $env:Path = "$env:Path;$InstallDir"  # Update current session
        Write-Host "PATH updated. You may need to restart your terminal." -ForegroundColor Yellow
    }

    # Verify installation
    $binaryPath = Join-Path $InstallDir $BINARY_NAME
    if (Test-Path $binaryPath) {
        Write-Host ""
        Write-Host "✓ Installation successful!" -ForegroundColor Green

        # Try to get version
        try {
            $version = & $binaryPath --version 2>&1 | Select-Object -First 1
            Write-Host "Installed: $version" -ForegroundColor Green
        } catch {
            Write-Host "Binary installed at: $binaryPath" -ForegroundColor Green
        }

        Write-Host ""
        Write-Host "Next steps:" -ForegroundColor Cyan
        Write-Host "1. Install companion APK on Android device:"
        Write-Host "   Download from: https://github.com/$REPO/releases/latest"
        Write-Host ""
        Write-Host "2. Connect Android device via ADB:"
        Write-Host "   adb devices"
        Write-Host ""
        Write-Host "3. Start MCP server:"
        Write-Host "   neuralbridge-mcp --auto-discover"
        Write-Host ""
        Write-Host "4. Configure Claude Desktop to use NeuralBridge MCP"
        Write-Host ""
        Write-Host "Documentation: https://github.com/$REPO"
        Write-Host ""

    } else {
        Write-Host "Installation failed. Binary not found." -ForegroundColor Red
        exit 1
    }

} finally {
    # Cleanup
    if (Test-Path $tempDir) {
        Remove-Item -Path $tempDir -Recurse -Force
    }
}
