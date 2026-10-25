# ADR-0003: Exit codes and v0.1 checks

- Status: accepted
- Date: 2026-10-23

## Context

The CLI is used interactively and in CI or triage scripts. A single boolean is not enough: errors, warnings, unavailable environments, and configuration failures need distinct handling.

## Decision

Use these exit codes:

| Code | Meaning |
|---|---|
| `0` | All rules pass. |
| `1` | At least one error-severity rule failed. |
| `2` | Warnings only. |
| `3` | Neither Visual Studio nor a Windows SDK was detected. |
| `4` | Rule pack could not be read or validated. |

The v0.1 pack checks Visual Studio/VC tools, `vcvarsall.bat`, Windows SDK presence/version, Python, Node.js, npm, node-gyp `msvs_version`, SDK environment variables, `INCLUDE`/`LIB`, and `cl.exe` visibility.

## Consequences

- Optional configuration problems (`msvs_version` unset, `WindowsSdkDir` unset) are pass or warning states, not errors.
- A missing environment is distinct from a broken rule pack.
- Machine consumers should read the JSON `summary.exit_code` or the process exit code.
