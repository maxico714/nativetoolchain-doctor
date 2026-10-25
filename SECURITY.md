# Security Policy

## Supported Versions

| Version | Supported |
|---|---|
| 0.1.x | Yes |

## Reporting a Vulnerability

**Do not open a public issue for security vulnerabilities.**

Report security issues privately via GitHub Security Advisories:

1. Go to the repository's **Security** tab
2. Click **Report a vulnerability**
3. Fill in the details and submit

We will acknowledge receipt within 72 hours and provide a status update within 7 days. If the vulnerability is confirmed, we will:

- Develop a fix
- Release a patch version
- Publish a GitHub Security Advisory with details

## Scope

This policy covers the `nativetoolchain-doctor` CLI tool and its packaged rule data. It does not cover:

- The host operating system or installed toolchains (Visual Studio, Windows SDK, Python, Node.js)
- Third-party packages used only in development (pytest, ruff, mypy)

## Security Model

- The tool is read-only by design (see [ADR-0002](../docs/adr/0002-read-only.md))
- No network requests, no telemetry, no background services
- Subprocesses use fixed argument lists with `shell=False` and timeouts
- The only write path is `--bundle <path>`, explicitly requested by the user
- Bundles redact usernames, user path segments, and secret-looking values
- Rule packs are validated before any probe runs; invalid packs exit `4` without probing

## Disclosure

Security fixes are released as patch versions. The vulnerability details are published in the corresponding GitHub Security Advisory after the fix is available.