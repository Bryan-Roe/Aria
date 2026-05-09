# Security Policy

Thank you for helping keep **Aria** and its users safe. This document describes
which versions of the project receive security updates, how to privately report
a vulnerability, and what to expect from the maintainers during the disclosure
process.

## Supported Versions

The table below lists the versions of Aria that are currently receiving
security updates. Older releases that are no longer supported will not receive
patches; please upgrade to a supported version before reporting an issue.

| Version         | Supported          | Notes                                   |
| --------------- | ------------------ | --------------------------------------- |
| latest (`main`) | :white_check_mark: | Active development branch               |
| 5.1.x           | :white_check_mark: | Current stable release                  |
| 5.0.x           | :x:                | End of life                             |
| 4.0.x           | :white_check_mark: | Long-term support (critical fixes only) |
| < 4.0           | :x:                | Unsupported – please upgrade            |

If you are unsure which version you are running, check the project release
notes or your installed package metadata.

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues,
discussions, or pull requests.** Public disclosure before a fix is available
puts users at risk.

Instead, please report vulnerabilities privately using one of the following
channels:

1. **GitHub Private Vulnerability Reporting** (preferred):
   Open a private report at
   [https://github.com/Bryan-Roe/Aria/security/advisories/new](https://github.com/Bryan-Roe/Aria/security/advisories/new).
2. **Email:** Contact the maintainer via the address listed on the
   [maintainer's GitHub profile](https://github.com/Bryan-Roe). If possible,
   encrypt sensitive details before sending.

### What to include

To help us triage and resolve the issue quickly, please include as much of the
following as you can:

- A clear description of the vulnerability and its potential impact.
- The affected version(s), platform, and configuration.
- Step-by-step instructions to reproduce the issue (proof-of-concept code,
  scripts, or screenshots are very helpful).
- Any known mitigations or workarounds.
- Whether the issue has been disclosed elsewhere, and any CVE identifier if
  one has already been assigned.
- How you would like to be credited (or whether you prefer to remain anonymous).

### What to expect

We aim to follow a coordinated disclosure process:

| Stage                          | Target Response Time                                                  |
| ------------------------------ | --------------------------------------------------------------------- |
| Initial acknowledgement        | Within **3 business days** of your report                             |
| Triage and severity assessment | Within **7 business days**                                            |
| Status updates                 | At least every **7 days** until resolution                            |
| Fix and disclosure             | Typically within **90 days**, depending on severity and complexity    |

After triage, we will let you know whether the report is accepted as a security
issue, declined (e.g., out of scope or not a vulnerability), or needs more
information. For accepted reports, we will work with you on a fix, prepare a
release, and coordinate public disclosure. With your permission, we will credit
you in the release notes and any associated security advisory.

## Scope

In-scope issues include, but are not limited to:

- Remote code execution, command injection, or unsafe deserialization.
- Authentication or authorization bypasses.
- Sensitive data exposure (secrets, credentials, personal data).
- Cross-site scripting (XSS), CSRF, SSRF, or path-traversal vulnerabilities in
  any first-party Aria component.
- Supply-chain or dependency issues unique to this repository's configuration.

The following are generally **out of scope**:

- Vulnerabilities in third-party dependencies that are already publicly tracked
  upstream (please report those to the upstream project; we will update once a
  fix is available).
- Issues that require physical access to a user's device or non-default,
  insecure configurations.
- Best-practice or hardening suggestions without a demonstrable security impact.
- Denial-of-service issues that require unrealistic resources or that only
  affect the reporter's own environment.

## Safe Harbor

We support good-faith security research. If you make a good-faith effort to
comply with this policy during your research, we will:

- Consider your research to be authorized.
- Work with you to understand and resolve the issue quickly.
- Not pursue or support legal action related to your research.

Please make every effort to avoid privacy violations, data destruction, and
service interruption while conducting research.

## Policy Updates

This policy may be updated from time to time. Material changes will be noted in
the project's release notes or commit history. The latest version of this
document is always available at
[`SECURITY.md`](https://github.com/Bryan-Roe/Aria/blob/main/SECURITY.md).
