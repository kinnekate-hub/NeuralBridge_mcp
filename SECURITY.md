# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.x     | Yes       |

## Reporting a Vulnerability

If you discover a security vulnerability in NeuralBridge, please report it responsibly.

**Do not open a public issue.**

### How to Report

Use [GitHub's private vulnerability reporting](https://github.com/dondetir/neuralBridge/security/advisories/new) to submit your report.

### What to Include

- Description of the vulnerability
- Steps to reproduce
- Affected component (MCP server, companion app, protocol)
- Impact assessment (what an attacker could achieve)
- Any suggested fix, if you have one

### Response Timeline

- **Acknowledgment:** Within 48 hours
- **Initial assessment:** Within 7 days
- **Fix or mitigation:** Within 90 days (depending on severity)

We will coordinate disclosure with you. Credit will be given in the release notes unless you prefer to remain anonymous.

## Scope

### In Scope

- Remote code execution via MCP server or companion app
- Privilege escalation through the AccessibilityService
- Data exfiltration (UI tree data, screenshots, clipboard)
- Protocol vulnerabilities (protobuf parsing, TCP handling)
- Denial of service against the MCP server or companion app

### Out of Scope

- Attacks requiring physical access to the device
- Attacks requiring a rooted/jailbroken device
- Attacks requiring the user to install a malicious app alongside NeuralBridge
- Social engineering
- Vulnerabilities in dependencies (report these to the upstream project)

## Security Architecture

NeuralBridge communicates over localhost TCP (port 38472) between the MCP server and companion app. The MCP server connects to AI agents via stdio. No network-facing services are exposed by default.

The companion app uses Android's AccessibilityService API, which requires explicit user enablement in device Settings. MediaProjection (for screenshots) requires a separate user consent dialog.
