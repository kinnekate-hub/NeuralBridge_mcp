#!/bin/bash
# NeuralBridge Installation Script
# Supports Linux and macOS

set -e

VERSION="1.0.0"
REPO="yourorg/neuralbridge"  # TODO: Update with actual GitHub repo
INSTALL_DIR="/usr/local/bin"
BINARY_NAME="neuralbridge-mcp"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "NeuralBridge MCP Server Installer v${VERSION}"
echo "==========================================="
echo ""

# Detect OS and architecture
OS="$(uname -s)"
ARCH="$(uname -m)"

case "${OS}" in
    Linux*)     PLATFORM="linux";;
    Darwin*)    PLATFORM="macos";;
    *)          echo -e "${RED}Unsupported OS: ${OS}${NC}"; exit 1;;
esac

case "${ARCH}" in
    x86_64*)    ARCH_TYPE="x64";;
    arm64*)     ARCH_TYPE="arm64";;
    aarch64*)   ARCH_TYPE="arm64";;
    *)          echo -e "${RED}Unsupported architecture: ${ARCH}${NC}"; exit 1;;
esac

echo -e "${GREEN}Detected platform: ${PLATFORM}-${ARCH_TYPE}${NC}"
echo ""

# Check for required dependencies
echo "Checking dependencies..."

# Check for curl or wget
if command -v curl &> /dev/null; then
    DOWNLOADER="curl -fsSL"
elif command -v wget &> /dev/null; then
    DOWNLOADER="wget -qO-"
else
    echo -e "${RED}Error: curl or wget is required${NC}"
    exit 1
fi

# Check for ADB
if ! command -v adb &> /dev/null; then
    echo -e "${YELLOW}Warning: ADB not found in PATH${NC}"
    echo "Install Android SDK platform-tools to use NeuralBridge"
    echo "See: https://developer.android.com/studio/releases/platform-tools"
    echo ""
fi

# Download binary
DOWNLOAD_URL="https://github.com/${REPO}/releases/latest/download/${BINARY_NAME}-${PLATFORM}-${ARCH_TYPE}.tar.gz"

echo "Downloading from: ${DOWNLOAD_URL}"

# Create temp directory
TMP_DIR=$(mktemp -d)
trap "rm -rf ${TMP_DIR}" EXIT

# Download and extract
${DOWNLOADER} "${DOWNLOAD_URL}" | tar -xz -C "${TMP_DIR}"

# Install binary
echo "Installing to ${INSTALL_DIR}..."

if [[ "$EUID" -ne 0 ]]; then
    echo -e "${YELLOW}Requesting sudo permission to install...${NC}"
    sudo install -m 755 "${TMP_DIR}/${BINARY_NAME}" "${INSTALL_DIR}/${BINARY_NAME}"
else
    install -m 755 "${TMP_DIR}/${BINARY_NAME}" "${INSTALL_DIR}/${BINARY_NAME}"
fi

# Verify installation
if command -v ${BINARY_NAME} &> /dev/null; then
    INSTALLED_VERSION=$(${BINARY_NAME} --version 2>&1 | head -n1)
    echo -e "${GREEN}✓ Installation successful!${NC}"
    echo "Installed: ${INSTALLED_VERSION}"
    echo ""

    # Next steps
    echo "Next steps:"
    echo "1. Install companion APK on Android device:"
    echo "   Download from: https://github.com/${REPO}/releases/latest"
    echo ""
    echo "2. Connect Android device via ADB:"
    echo "   adb devices"
    echo ""
    echo "3. Start MCP server:"
    echo "   ${BINARY_NAME} --auto-discover"
    echo ""
    echo "4. Configure Claude Desktop to use NeuralBridge MCP"
    echo ""
    echo "Documentation: https://github.com/${REPO}"
else
    echo -e "${RED}Installation failed. Binary not found in PATH.${NC}"
    exit 1
fi
