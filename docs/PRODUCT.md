# PRODUCT — nativetoolchain-doctor

Status: v0.1 implemented and verified locally on 2026-10-23. Not published. The publish gates remain owner-controlled.

## Problem

Native npm packages fail on Windows with long `node-gyp` errors when Visual Studio Build Tools, the Windows SDK, Python, or node-gyp configuration are missing or mismatched. The information needed to diagnose the failure is spread across installer UI, `vswhere`, registry keys, environment variables, and package-manager configuration. The user needs one read-only command that turns that state into a short list of pass/warn/error results and an exact command to run next.

The research record that motivated the project is in [EVIDENCE.md](EVIDENCE.md). It is background evidence, not a claim that every historical signal was re-verified during this build.

## Target users

1. **JavaScript/TypeScript engineer on Windows** — a native dependency failed; they need a clear diagnosis and the exact `vcvarsall.bat` line without installing another global tool.
2. **Developer on a locked-down corporate machine** — they cannot change the toolchain freely; they need a redacted report for an IT ticket or a GitHub issue.
3. **Open-source maintainer** — they triage Windows build reports and want reporters to provide structured, comparable output.

## Jobs to be done

- "Tell me which part of the Windows native toolchain is missing or mismatched."
- "Give me the exact command to activate the toolchain I already have."
- "Give me a report I can share without exposing my username or secrets."

## Value proposition

An offline, read-only doctor for the Windows node-gyp toolchain that reports all relevant checks in one run, prints the exact toolchain activation command, and can produce a redacted support bundle.

## Non-goals

- Does not install Visual Studio, the Windows SDK, Python, Node.js, or npm packages.
- Does not invoke `cl.exe`, `node-gyp`, or a compiler.
- Does not modify the registry, `PATH`, `INCLUDE`, `LIB`, or npm configuration.
- Does not support macOS or Linux in v0.1.
- Does not monitor the machine continuously; it is a one-shot CLI.
- Does not guarantee that a detected toolchain can compile every project.

## v0.1 scope

### Implemented

- JSON rule-pack engine with validation and a versioned rule pack.
- Read-only probes for Visual Studio, `vcvarsall.bat`, the Windows SDK, Python, Node.js, npm, node-gyp configuration, SDK environment variables, `INCLUDE`/`LIB`, and `cl.exe`.
- Human, JSON, and redacted Markdown bundle reporters.
- Exact `vcvarsall.bat` fix lines.
- `doctor` self-check, rule inspection, and dry-run modes.
- Exit codes for pass, errors, warnings, unavailable environment, and bad rule packs.
- Windows-only packaging with no runtime dependencies outside the Python standard library.

### Deferred

- Additional Visual Studio instance selection and ARM64-specific checks.
- Rule-pack contribution tooling and schema documentation.
- Automated release publishing and registry distribution.
- Safe, print-only remediation suggestions beyond the current fix lines.

## Success criteria and evidence

| Criterion | Measure | Evidence |
|---|---|---|
| Static checks | Ruff check/format and mypy strict pass | [VERIFICATION.md](VERIFICATION.md) |
| Unit and integration behavior | Test suite green | [VERIFICATION.md](VERIFICATION.md) |
| Live host diagnosis | 11 rules pass on the build host and exit `0` | [VERIFICATION.md](VERIFICATION.md) |
| Redaction | Bundle contains no test username or secret-looking value | `tests/security/test_readonly.py` |
| Read-only behavior | A normal run creates no files; only `--bundle` writes | `tests/security/test_readonly.py` |
| Rule-pack failure | Invalid or non-UTF-8 pack returns exit `4` | `tests/unit/test_rules.py`, CLI tests |
| Clean environment | Fresh clone install and README quickstart | [VERIFICATION.md](VERIFICATION.md) |

## Honest comparison

- **Visual Studio Installer / Build Tools installer:** owns installation and repair. This tool owns diagnosis of an existing installation and deliberately does not compete with setup.
- **`vswhere.exe`:** accurately reports Visual Studio instances, but does not combine that with node-gyp, Python, SDK-version, environment-variable, or support-bundle checks.
- **`node-gyp` error output:** describes the failed build, but not the full machine state or the exact activation command.
- **Static documentation and forum answers:** cannot inspect the user's machine and can be out of date.

## Naming and license

- Name: `nativetoolchain-doctor`. It is descriptive and has no claimed affiliation with Microsoft, Node.js, or node-gyp.
- Registry and trademark availability are checked at the publish gates; the project is not published yet.
- License: MIT. Runtime code uses only the Python standard library. Development dependencies are recorded in [THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md).

## Risks

| Risk | Severity | Mitigation |
|---|---|---|
| Visual Studio or SDK changes break detection | High | Rules are data; probes have registry and environment fallbacks; live verification is repeatable. |
| `vswhere` misses a custom installation | Medium | Fall back to `VSINSTALLDIR`, VC tools paths, and the VS7 registry key; allow alternate rule packs. |
| A user expects the tool to install or repair software | Medium | README and output state diagnose-only; no install APIs exist. |
| A bundle leaks a username or secret | Medium | Redaction is tested; users are told to review bundles before sharing. |
| Windows-only maintenance burden | Medium | Small standard-library codebase; no runtime dependencies; CI matrix covers Python versions. |
| A custom rule pack causes a hidden probe dependency | Low | Rule validation restricts probes and expected types; missing environment probes no longer crash availability detection. |
