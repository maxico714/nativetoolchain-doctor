# VERIFICATION — nativetoolchain-doctor v0.1 (2026-10-23)

All commands executed on the build host (Windows 11, Python 3.12.10).

## L0 — Static checks

```powershell
ruff check src tests
# All checks passed!

ruff format --check src tests
# 17 files already formatted

mypy src
# Success: no issues found in 7 source files
```

## L1/L2 — Unit and integration tests

```powershell
python -m pytest -q --tb=short
# 84 passed in ~3s
```

Test breakdown:
- `tests/unit/test_rules.py` — 13 tests (rule loading, validation, errors)
- `tests/unit/test_engine.py` — 17 tests (evaluation, report, custom packs)
- `tests/unit/test_probes.py` — 28 tests (all probe behaviors)
- `tests/unit/test_report.py` — 3 tests (JSON/text/bundle rendering)
- `tests/integration/test_cli.py` — 11 tests (CLI commands, bundle, error codes)
- `tests/security/test_readonly.py` — 6 tests (no writes, redaction, no shell, no registry writes)
- `tests/adversarial/test_adversarial.py` — 5 tests (empty env, huge env, corrupt SDK, unversioned SDK dirs, Unicode paths)
- `tests/live/test_live.py` — 1 test (host live run, skipped in CI, run manually)

## L3 — Live host run

```powershell
nativetoolchain-doctor run --json
```

Result: exit code 0, 11 rules pass, fix line printed for `vcvarsall.bat`.

```powershell
nativetoolchain-doctor doctor
# nativetoolchain-doctor 0.1.0 (rules 2026.10.1)
# platform: win32
# python: C:\Users\rekha\AppData\Local\Programs\Python\Python312\python.exe
# vs: C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools
# sdk: C:\Program Files (x86)\Windows Kits\10
# doctor: ready
```

```powershell
nativetoolchain-doctor run --bundle bundle.md
# bundle: bundle.md (redacted, no username, no secrets)
```

## L4 — Clean environment (fresh clone)

```powershell
git clone <repo> nativetoolchain-doctor-clean
cd nativetoolchain-doctor-clean
python -m venv .venv
.venv\Scripts\python.exe -m pip install -e .
.venv\Scripts\nativetoolchain-doctor.exe run
```

Verified: install succeeds, command runs, output matches expectations.

Re-run 2026-10-25 from a fresh clone of the local repository (commit `97b5f1d`):

```text
git clone <local repo> ntd-clone
python -m venv --system-site-packages .venv
.venv/Scripts/python.exe -m pip install --no-build-isolation .
# install exit 0, console script created
.venv/Scripts/nativetoolchain-doctor.exe run --json
# exit 0, 11 rules, rule pack 2026.10.1
python -m pytest --tb=no -q
# exit 0, 84 tests collected
```

Note: a plain `python -m venv` on Python 3.12 has no setuptools, so `--no-build-isolation` fails until setuptools is present. Either allow build isolation (downloads setuptools) or use `--system-site-packages` as above.

## L5 — Adversarial & security

| Test | Result |
|---|---|
| Empty environment (no VS, no SDK) | Exit 3, no crash |
| Huge environment (5000 PATH entries) | Exit 3, < 5s, no crash |
| Corrupt SDK env (`WindowsSdkDir` missing) | Warns ENV001, exit 2 |
| Unversioned SDK `bin` dirs | SDK002 error, no crash |
| Unicode toolchain path (`工具链`) | Exit 0, all pass |
| Non-UTF-8 rule pack | RuleError raised, exit 4 |
| Empty rule pack | RuleError raised, exit 4 |
| Bundle redaction | Username and secret-like values redacted |
| Normal run writes nothing | No files created in CWD |
| No `shell=True` anywhere | Verified by source scan |
| No registry writes | Verified by source scan |

## Packaging

```powershell
python -m pip wheel . --no-deps -w dist
# Created nativetoolchain_doctor-0.1.0-py3-none-any.whl (14,562 bytes)
```

Wheel contents verified: package code, `rules/v1/rules.json`, entry point, metadata.

## Performance

| Metric | Measured |
|---|---|
| Full run (live) | ~1.2s |
| Memory (RSS) | ~18 MB |
| Startup (cold) | ~0.4s |

All within budget (< 5s, < 50 MB).