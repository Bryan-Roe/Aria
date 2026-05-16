# Security Policy

Thank you for helping keep **Aria** and its users safe. This policy explains how to report vulnerabilities, what versions are supported, what’s in scope, and our coordinated disclosure process.

---

## Table of Contents

- [Supported Versions](#supported-versions)
- [How to Report a Vulnerability](#how-to-report-a-vulnerability)
- [What to Include in a Report](#what-to-include-in-a-report)
- [Coordinated Disclosure Process](#coordinated-disclosure-process)
- [Scope](#scope)
  - [In Scope](#in-scope)
  - [Out of Scope](#out-of-scope)
- [Testing Expectations](#testing-expectations)
- [Safe Harbor & Good-Faith Research](#safe-harbor--good-faith-research)
- [Remediation and Release Practices](#remediation-and-release-practices)
- [Policy Updates](#policy-updates)

---

## Supported Versions

Security fixes are provided only for versions listed below. If you’re running an unsupported release, please [upgrade](https://github.com/Bryan-Roe/Aria/releases) before reporting a vulnerability.

| Version         | Supported           | Notes                                        |
| --------------- | ------------------ | --------------------------------------------- |
| latest (`main`) | :white_check_mark: | Active development branch                     |
| 5.1.x           | :white_check_mark: | Current stable release                        |
| 5.0.x           | :x:                | End of life                                  |
| 4.0.x           | :white_check_mark: | Long-term support (critical fixes only)       |
| < 4.0           | :x:                | Unsupported — please upgrade                  |

Unsure which version you’re using? Review the [release notes](https://github.com/Bryan-Roe/Aria/releases).

---

## How to Report a Vulnerability

> **Please do NOT report security vulnerabilities through public GitHub issues, pull requests, or discussions. Disclosing security issues publicly before a fix is available can put users at risk.**

To report a potential security issue **privately and securely**:

1. **[Open a private report (recommended)](https://github.com/Bryan-Roe/Aria/security/advisories/new)**
2. **Contact via email:**  
   Message the maintainer using their public address from the [project maintainer’s GitHub profile](https://github.com/Bryan-Roe). Whenever possible, encrypt sensitive details.

Reports should be written in English when possible.

---

## What to Include in a Report

To help us confirm, triage, and fix the issue faster, please include:

- A clear description of the vulnerability and its potential impact.
- The version(s), environment, platform, or configuration involved.
- Steps to reproduce, proof-of-concept code, scripts, logs, or screenshots if possible.
- Any known workarounds or mitigations.
- Whether and where the issue has been disclosed elsewhere.
- CVE identifier (if one is already assigned).
- How you would like to be credited, if at all.

---

## Coordinated Disclosure Process

We strive to handle reports using a coordinated process and keep reporters informed.

| Stage                    | Target Response Time                                  |
| ------------------------ | ----------------------------------------------------- |
| Initial acknowledgment   | Within **3 business days**                            |
| Triage & assessment      | Within **7 business days**                            |
| Progress updates         | At least every **7 days** until resolution            |
| Fix/disclosure           | Typically within **90 days**, depending on severity   |

After triage, you’ll be notified if the report is accepted, declined, or needs more info. Accepted reports proceed to remediation and coordinated disclosure.

---

## Scope

### In Scope

Issues are generally in scope if they involve:

- Remote code execution, command injection, or unsafe deserialization
- Authentication/authorization bypass
- Sensitive data exposure (secrets, credentials, tokens, personal data)
- XSS, CSRF, SSRF, path traversal—in **first-party Aria code**
- Supply-chain or dependency risks from this repository’s configuration or integrations
- Insecure defaults, or exposed admin/debug features in authentic deployments

### Out of Scope

Out of scope, unless a **clear, material risk** exists:

- Vulnerabilities in third-party dependencies already tracked upstream ([check advisories](https://github.com/advisories))
- Issues requiring physical device access or a non-default insecure config
- Best-practice, compliance, or hardening items **without a demonstrated exploit path**
- Denial-of-service findings that only affect your own test environment or are impractical
- Missing HTTP security headers, banners, or version disclosures lacking an exploit chain
- Social engineering, phishing, or attacks requiring maintainer credential compromise outside this project

---

## Testing Expectations

- Test only on systems/data you own or are authorized to test.
- Avoid privacy violations, destructive actions, or disruptions.
- Do not access, modify, or retain others’ data.
- Do not use automated/high-volume scanning that could degrade service.
- Stop testing and report once you have enough info to demonstrate an issue.

---

## Safe Harbor & Good-Faith Research

We support good-faith security research. If you follow this policy:

- **Your findings are authorized** and welcomed by project maintainers.
- We’ll work with you to diagnose, remediate, and disclose issues cooperatively.
- We will not initiate or support legal action for research reported according to this policy.

**Note:** Safe harbor does not apply if research intentionally harms users, damages data, violates privacy, or disrupts service.

---

## Remediation and Release Practices

When a report is accepted, we may:

- Develop and validate a fix
- Prepare patched releases for all supported versions if feasible
- Publish a GitHub Security Advisory
- Request or reference a CVE
- Document mitigations for users unable to upgrade

---

## Policy Updates

This policy may evolve. Significant updates will be reflected in release notes, commit logs, or [this file](https://github.com/Bryan-Roe/Aria/blob/main/SECURITY.md). Always refer to the latest version here.


