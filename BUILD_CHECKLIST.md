# BUILD CHECKLIST — nativetoolchain-doctor

Status: SCAFFOLD. Work top-to-bottom; each gate shows REAL command output. Circuit breaker: 3 failures per gate → stop, re-research, log in STATE.md.

## Gate 0 — Spike (riskiest assumption FIRST)

- [ ] Run real `vswhere.exe` on this host: positive path (VC tools present) → installationPath; negative path (missing component) → empty. Log both outputs.
- [ ] Cross-check with registry (`HKLM\SOFTWARE\Microsoft\Microsoft SDKs\Windows\v10.0`) + env (`WindowsSdkDir`, `INCLUDE`, `LIB`). Log agreement/disagreement.
- [ ] **Expected:** at least one path (vswhere OR registry/env) correctly detects the host toolchain; if both fail → STOP, re-scope, log ADR.
- [ ] Record wall times vs performance budget.

## Gate 1 — L0 static (every commit)

- [ ] `ruff check .` + `ruff format --check .` clean.
- [ ] `mypy src/` clean.
- [ ] `pytest --collect-only -q` green.

## Gate 2 — L1 units (rule engine + probes)

- [ ] Rule engine: load YAML, evaluate expected vs probe result, severity mapping.
- [ ] Probe parsers: vswhere stdout, registry fixture, env fixture, subprocess version output.
- [ ] Rule-pack versioning: bad YAML → exit 4 (config).
- [ ] **Mutation sanity:** flip severity error→info for a failing rule → reporter MUST still exit 1; restore.

## Gate 3 — L2 integration (mock probes)

- [ ] Mock vswhere / registry / env fixtures → correct rule firing (pass/fail per id).
- [ ] Fallback path: vswhere returns empty → registry/env fallback correctly invoked.
- [ ] `--bundle` output: redacted (no username, no secret-looking env values).

## Gate 4 — L3 e2e (live)

- [ ] Live run on this host (known-good toolchain) → all rules pass; exact fix-line printed.
- [ ] Subprocess with stripped env (known-bad) → correct failures (SDK / vcvars / msvs_version).
- [ ] `--dry-run` lists rules without probing.

## Gate 5 — L5 adversarial

- [ ] vswhere missing entirely → fallback works or clean exit 3 (environment).
- [ ] Corrupted env vars → clean error, no crash.
- [ ] Non-admin user → works (read-only; no privilege escalation needed).
- [ ] Huge PATH → no unbounded memory.

## Gate 6 — Read-only & honesty audit (pre-M8)

- [ ] CI test: zero writes to system (no `open(..., 'w')` outside temp; no registry writes; no subprocess installs).
- [ ] README states diagnose-only; no install commands run; non-goals explicit.
- [ ] No TODO/FIXME in src/.
- [ ] Secrets scan clean.

## Gate 7 — L4 clean env

- [ ] Fresh clone → `pip install -e .` → live probes green on Windows CI runner.
- [ ] README quickstart verbatim-tested.

## Gate 8 — Packaging (G3-gated; do NOT run without operator approval)

- [ ] `python -m build` → wheel + sdist; `twine check` clean.
- [ ] Name free on PyPI confirmed live.
- [ ] Publish ONLY at G3 with trusted publishing (OIDC), after G2 checklist.

## Definition of done (v0.1)

Gates 0–5 + 7 + 6 (items 1–3) green with evidence in PROGRESS.md. Gate 8 prepared but not executed.
