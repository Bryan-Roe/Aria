# Security Policy

Thank you for helping keep **Aria** and its users safe. This document explains which versions currently receive security updates, how to report a vulnerability privately, what is in scope for security reports, and what to expect during coordinated disclosure.

## Supported Versions

Security fixes are provided only for the versions listed below. If you are running an unsupported release, please upgrade to a supported version before reporting a vulnerability.

| Version | Supported | Notes |
| --------------- | ------------------ | --------------------------------------- |
| latest (`main`) | :white_check_mark: | Active development branch |
| 5.1.x | :white_check_mark: | Current stable release |
| 5.0.x | :x: | End of life |
| 4.0.x | :white_check_mark: | Long-term support (critical fixes only) |
| < 4.0 | :x: | Unsupported — please upgrade |

If you are unsure which version you are using, review the release notes or check your installed package metadata.

## Reporting a Vulnerability

**Do not report security vulnerabilities through public GitHub issues, discussions, pull requests, or other public channels.** Public disclosure before a fix is available can put users at risk.

Please use one of the private reporting options below:

1. **GitHub Private Vulnerability Reporting** (preferred)  
   Open a private report at [https://github.com/Bryan-Roe/Aria/security/advisories/new](https://github.com/Bryan-Roe/Aria/security/advisories/new)
2. **Email**  
   Contact the maintainer using the address listed on the [maintainer's GitHub profile](https://github.com/Bryan-Roe). If possible, encrypt sensitive details before sending them.

## What to Include

To help with triage and remediation, include as much of the following information as possible:

- A clear description of the issue and its potential impact
- The affected version, environment, platform, and configuration
- Reproduction steps, including proof-of-concept code, scripts, logs, or screenshots if available
- Any known mitigations or workarounds
- Whether the issue has been disclosed elsewhere
- Any assigned CVE identifier, if one already exists
- Whether and how you would like to be credited

## Coordinated Disclosure Process

We aim to handle reports using a coordinated disclosure process.

| Stage | Target Response Time |
| ------------------------------ | ------------------------------------------------------------------ |
| Initial acknowledgement | Within **3 business days** |
| Triage and severity assessment | Within **7 business days** |
| Status updates | At least every **7 days** until resolution |
| Fix and disclosure | Typically within **90 days**, depending on severity and complexity |

After triage, we will let you know whether the report is accepted as a security issue, declined, or requires more information. For accepted reports, we will work on remediation, prepare a release when appropriate, and coordinate public disclosure. With your permission, we may credit you in release notes or in a related security advisory.

## Scope

### In Scope

Examples of issues that are generally in scope include:

- Remote code execution, command injection, or unsafe deserialization
- Authentication or authorization bypass
- Sensitive data exposure, including secrets, credentials, tokens, or personal data
- Cross-site scripting (XSS), CSRF, SSRF, or path traversal in first-party Aria components
- Supply-chain or dependency issues that arise from this repository's configuration or integration
- Insecure defaults or exposed administrative/debug functionality that can be exploited in a real deployment

### Out of Scope

The following are generally out of scope unless they demonstrate clear, material security impact in this repository:

- Vulnerabilities in third-party dependencies that are already publicly tracked upstream
- Issues that require physical access to a device or rely on a non-default insecure configuration
- Best-practice, compliance, or hardening suggestions without a demonstrated exploit path or security impact
- Denial-of-service findings that require unrealistic resources or affect only the reporter's own environment
- Missing HTTP security headers, banner disclosure, or version disclosure without a meaningful exploit chain
- Social engineering, phishing, spam, or attacks requiring maintainer credential compromise outside this project

## Testing Expectations

Please keep testing limited to systems and data you own or are explicitly authorized to test. While researching:

- Avoid privacy violations, destructive actions, or service disruption
- Do not access, modify, or retain data that does not belong to you
- Do not use automated scanning or high-volume traffic in ways that could degrade service availability
- Stop testing and report the issue once you have gathered enough information to demonstrate impact safely

## Safe Harbor

We support good-faith security research. If you make a good-faith effort to follow this policy, we will:

- Consider your research to be authorized
- Work with you to understand and resolve the issue
- Not pursue or support legal action solely for research conducted in compliance with this policy

This safe harbor does not extend to activity that intentionally harms users, violates privacy, destroys data, or disrupts service availability.

## Remediation and Release Practices

When a report is accepted, maintainers may take one or more of the following actions:

- Develop and validate a fix
- Prepare patched releases for supported versions when feasible
- Publish a security advisory
- Request a CVE identifier or reference an existing one
- Document mitigations for users who cannot upgrade immediately

## Policy Updates

This policy may change over time. Material updates may be reflected in release notes, commit history, or repository documentation. The latest version is always available at [`SECURITY.md`](https://github.com/Bryan-Roe/Aria/blob/main/SECURITY.md).
