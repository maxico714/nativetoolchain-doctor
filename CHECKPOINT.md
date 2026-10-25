# CHECKPOINT — nativetoolchain-doctor v0.1 (2026-10-25)

## Status

**Locally verified and committed. No remote is configured; G2 and G3 have not been executed.**

The implementation, tests, docs and packaging exist and were re-verified on 2026-10-25. Earlier revisions of this checkpoint claimed "repo clean, ready for G2/G3"; that was inaccurate. On 2026-10-25 the repository had zero commits and 21 untracked entries, so it was neither clean nor push-ready. A local initial commit was made after re-verification, and the claims below now match observed command output.

## What was built

A read-only Windows CLI (`nativetoolchain-doctor`) that diagnoses the native toolchain needed by `node-gyp`:
- Visual Studio Build Tools (VC tools component) via `vswhere`, `VSINSTALLDIR`, VS7 registry
- `vcvarsall.bat` existence
- Windows SDK presence and version via registry and env fallback
- Python 3.8+, Node.js, npm availability
- node-gyp `msvs_version` config
- `WindowsSdkDir`, `INCLUDE`, `LIB` validation
- `cl.exe` PATH visibility (informational)

Outputs: human report, JSON (`--json`), redacted Markdown bundle (`--bundle`), exact `vcvarsall.bat` fix line.
Exit codes: 0 pass, 1 error, 2 warn, 3 env unavailable, 4 bad rule pack.
Rule pack: JSON (stdlib-only), 11 rules, versioned `2026.10.1`.

## Verification evidence (re-run 2026-10-25)

| Level | Command | Result |
|---|---|---|
| L0 | `python -m ruff check src tests` | `All checks passed!` |
| L0 | `python -m ruff format --check src tests` | `17 files already formatted` |
| L0 | `python -m mypy src` | `Success: no issues found in 7 source files` |
| L1/L2 | `python -m pytest --tb=no -q` | Exit 0; 83 tests collected (82 excluding `live`) |
| L3 | `python -m nativetoolchain_doctor run --json` | Exit 0; 11 rules evaluated on this host; rule pack `2026.10.1` |
| PKG | `python -m pip wheel . --no-deps -w dist` | Built `nativetoolchain_doctor-0.1.0-py3-none-any.whl`, 16,976 bytes, sha256 `ea3f5549…c74a` |
| L4 | fresh clone install and README quickstart | NOT yet re-run after the initial commit; run before requesting G2 |

The earlier 2026-10-23 table recorded a 14.5 KB wheel and did not note that the repository had no commits. Both are corrected above from commands run on 2026-10-25.

## Artifacts created

**Source:**
- `src/nativetoolchain_doctor/{cli.py,engine.py,probes.py,report.py,rules.py,__init__.py,__main__.py}`
- `src/nativetoolchain_doctor/rules/v1/rules.json` (11 rules)

**Tests (83):**
- `tests/unit/` — rules, engine, probes, report
- `tests/integration/` — CLI, bundle, doctor, custom packs
- `tests/security/` — read-only audit, redaction, no shell/network/registry writes
- `tests/adversarial/` — empty/corrupt/huge/Unicode env, bad packs
- `tests/live/` — host live run (manual)

**Docs:**
- `README.md` — install, quickstart, commands, exit codes, rule table, privacy, limitations
- `docs/PRODUCT.md` — problem, users, scope, success criteria, comparison, risks
- `docs/ARCHITECTURE.md` — C4, components, data model, interfaces, security model, testing, packaging
- `docs/ROADMAP.md` — v0.1 done, v0.5/v1.0 planned, maintenance
- `docs/EVIDENCE.md` — research record + live host verification table
- `docs/VERIFICATION.md` — commands and results for every gate
- `docs/adr/0001-json-rule-packs.md`, `0002-read-only.md`, `0003-exit-codes.md`
- `docs/MAINTAINING.md` — triage, release, local CI, limitations

**Packaging & governance:**
- `pyproject.toml` — stdlib runtime, dev deps pinned, pytest/ruff/mypy config
- `LICENSE` (MIT), `CHANGELOG.md`, `THIRD_PARTY_NOTICES.md`
- `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, `SUPPORT.md`, `GOVERNANCE.md`
- `.editorconfig`, `Makefile`
- `.github/workflows/ci.yml` (Windows matrix 3.10/3.11/3.12, pinned action SHAs)
- `.github/workflows/dependency-review.yml`
- `.github/ISSUE_TEMPLATE/{bug.yml,feature.yml}`, `PULL_REQUEST_TEMPLATE.md`
- `.github/dependabot.yml`, `CODEOWNERS` (placeholder)

**CI matrix:** Windows-latest, Python 3.10/3.11/3.12. Live test as manual `workflow_dispatch`.

## Gates

- **G1 (idea selected):** Done — CEO decision recorded in `work/CEO_DECISIONS.md`
- **G2 (public push):** NOT executed. After the 2026-10-25 local commit the tree is clean and checks are green, but no remote exists and pushing requires explicit owner approval.
- **G3 (registry publish):** NOT executed. Wheel builds locally; PyPI name availability is unchecked and publishing requires owner approval.

## Next steps (when API continues)

1. Push to remote (owner action at G2)
2. Configure GitHub repository settings (branch protection, Discussions, labels, `good first issue`)
3. Verify PyPI name availability
4. Publish via trusted publishing (OIDC) at G3
5. Post-publish: clean-clone verify from public URL

## Files not committed (gitignored)

- `.agent/` — agent state, progress, decisions
- `AGENTS.md` — master protocol (workspace-level, not project)
- `*.md.bundle` — generated bundles
- Build caches (`dist/`, `build/`, `*.egg-info/`, `__pycache__/`, `.pytest_cache/`, etc.)