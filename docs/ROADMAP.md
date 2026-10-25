# ROADMAP — nativetoolchain-doctor

Status: v0.1 implemented and locally verified on 2026-10-23. Later milestones are plans, not promises.

SemVer and Keep a Changelog are used from the first local release.

## v0.1 — Walking skeleton (complete locally)

- [x] JSON rule-pack loader and validator.
- [x] Read-only probes for Visual Studio, `vcvarsall.bat`, SDK, Python, Node.js, npm, `msvs_version`, SDK environment, `INCLUDE`/`LIB`, and `cl.exe`.
- [x] 11-rule pack with severity and fix hints.
- [x] Human, JSON, and redacted bundle reporters.
- [x] Exact `vcvarsall.bat` fix lines.
- [x] `doctor`, `rules list`, and `--dry-run`.
- [x] Unit, integration, security, adversarial, and live tests.
- [x] CI workflow for Python 3.10–3.12 on Windows.
- [x] Clean-clone verification of the README commands.

Exit criteria: all gates in [BUILD_CHECKLIST.md](../BUILD_CHECKLIST.md) that do not require the publish gates are green with evidence in [VERIFICATION.md](VERIFICATION.md).

## v0.5 — Core value hardening

- [ ] Support multiple Visual Studio instances and explicit instance selection.
- [ ] Add ARM64 Windows-specific checks where the host exposes reliable signals.
- [ ] Add a schema document and examples for community rule packs.
- [ ] Expand redaction tests with more path and secret patterns.
- [ ] Add a reproducible release workflow for signed artifacts and an SBOM.
- [ ] Publish the package and a public repository after the G2/G3 gates.

Exit criteria: the rule-pack workflow is documented and tested, and a release can be reproduced from a tag.

## v1.0 — Production-ready

- [ ] Package distribution through PyPI and a Windows package manager.
- [ ] Documented support policy and compatibility matrix.
- [ ] Performance and memory results recorded on the CI matrix.
- [ ] A triage-oriented integration example for maintainers.
- [ ] A stable JSON schema contract.

Exit criteria: clean-environment install, upgrade, and uninstall are verified; security and dependency scans are clean; release provenance is recorded.

## Post-1.0 (parked)

- macOS/Linux diagnostics as separate tools.
- Continuous monitoring or background agents.
- Compiler invocation or automatic repair.

These are outside the current scope and would require a new product decision.

## Maintenance

- A new Visual Studio or Windows SDK release normally changes rule data, not the engine.
- Rule-pack changes use the `YYYY.MM.N` version format.
- Security fixes and broken-detection fixes are released as patch versions.
- The project is maintained by the repository owner and contributors under [GOVERNANCE.md](../GOVERNANCE.md).
