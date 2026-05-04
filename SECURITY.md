# Security Policy

Thank you for taking the time to help keep Aria and its users safe.
This document explains which releases receive security fixes, how to report
a vulnerability responsibly, what you can expect after you report, and what
research activities we consider in scope.

---

## Supported Versions

The table below shows which versions currently receive security updates.

| Version          | Supported          | Notes                        |
| ---------------- | ------------------ | ---------------------------- |
| latest (`main`)  | :white_check_mark: | Active development branch    |
| 5.1.x            | :white_check_mark: | Current stable release       |
| 5.0.x            | :x:                | End of life — no updates     |
| 4.0.x            | :white_check_mark: | LTS — critical fixes only    |
| < 4.0            | :x:                | Unsupported — please upgrade |

---

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues,
discussions, or pull requests.**  Public disclosure before a fix is available
puts all users at risk.

### Preferred channel

Use **GitHub Private Vulnerability Reporting** to submit your report
confidentially:

<https://github.com/Bryan-Roe/Aria/security/advisories/new>

GitHub will notify the maintainers immediately, and your report stays private
until a fix is released.

### Email fallback

If you are unable to use the link above, you can contact the maintainer
directly through the contact information on their GitHub profile:

<https://github.com/Bryan-Roe>

Please encrypt sensitive details whenever possible.

---

### What to include

A thorough report helps us triage and fix issues faster.  Please provide as
many of the following as you can:

- **Description and impact** — What is the vulnerability and what can an
  attacker do with it?
- **Affected versions** — Which releases or commits are affected?
- **Reproduction steps** — A minimal, self-contained proof-of-concept
  (script, curl commands, screenshots, etc.).
- **Mitigations** — Any workarounds you have identified.
- **Prior disclosure / CVE** — Has the issue been reported elsewhere, or does
  it already have a CVE identifier?
- **Credit preference** — How would you like to be credited in the advisory
  (name, handle, "anonymous", etc.)?

---

### What to expect

| Milestone                         | Target                                   |
| --------------------------------- | ---------------------------------------- |
| Initial acknowledgement           | Within **3 business days**               |
| Triage and severity assessment    | Within **7 business days**               |
| Status updates                    | At least every **7 days** until resolved |
| Fix and coordinated disclosure    | Typically within **90 days**; may vary by severity |

If we need more information to reproduce the issue, we will reach out via the
private advisory thread.  We will notify you before any public disclosure.

---

## Scope

The following categories of vulnerabilities are **in scope**:

- Remote code execution (RCE)
- Authentication or authorization bypass
- Sensitive data exposure (credentials, PII, conversation history)
- Cross-site scripting (XSS), cross-site request forgery (CSRF), or
  server-side request forgery (SSRF)
- Path traversal / directory traversal
- Supply-chain issues in code **owned by this repository** (e.g., malicious
  logic introduced directly into this codebase)

## Out of scope

The following are **not** eligible for reports:

- Vulnerabilities in upstream dependencies that are already tracked in their
  own advisories (report those upstream; we will update our dependency when a
  fix is available)
- Issues that require physical access to the device running Aria
- General hardening suggestions without a demonstrable security impact
- Denial-of-service attacks that require an unrealistic volume of requests or
  special privileges not available to ordinary users
- Theoretical vulnerabilities without a working proof-of-concept

---

## Safe Harbor

We support responsible security research.  If you make a good-faith effort to
follow this policy, we will:

- Not pursue legal action against you related to your research.
- Work with you to understand and resolve the issue quickly.
- Credit you in the security advisory (unless you prefer to remain anonymous).

We ask that you:

- Give us a reasonable amount of time to respond and fix the issue before any
  public disclosure.
- Avoid accessing, modifying, or deleting data that does not belong to you.
- Limit your testing to your own accounts or systems you have permission to
  test.

---

## Policy Updates

This policy may be updated from time to time.  The latest version is always
available at:

<https://github.com/Bryan-Roe/Aria/blob/main/SECURITY.md>

