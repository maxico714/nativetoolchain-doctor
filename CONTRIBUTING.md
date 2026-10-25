# Contributing

Thank you for considering a contribution to `nativetoolchain-doctor`!

## Quick start

```powershell
git clone https://github.com/<owner>/nativetoolchain-doctor
cd nativetoolchain-doctor
python -m venv .venv
.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

## Development workflow

1. Create a branch: `git checkout -b my-change`
2. Make your changes
3. Run the checks:
   ```powershell
   ruff check src tests
   ruff format --check src tests
   mypy src
   python -m pytest -m "not live"
   ```
4. Commit with a clear message (Conventional Commits preferred)
5. Push and open a pull request

## Code style

- Python 3.10+ syntax
- Ruff for formatting and linting (config in `pyproject.toml`)
- Type hints required; `mypy --strict` must pass
- No `TODO`/`FIXME` comments in source

## Tests

- Unit tests in `tests/unit/`
- Integration tests in `tests/integration/`
- Security tests in `tests/security/`
- Adversarial tests in `tests/adversarial/`
- Live tests in `tests/live/` (run manually: `pytest -m live`)

All new code must have tests. Mock external state (registry, env, subprocess) via `ProbeContext` injection.

## Rule packs

The packaged rule pack is at `src/nativetoolchain_doctor/rules/v1/rules.json`.

To propose a rule change:
1. Edit the JSON (or add a new pack under `rules/vN/`)
2. Ensure it passes validation: `python -c "from nativetoolchain_doctor.rules import load_rules; load_rules()"`
3. Run the full test suite

Alternate packs can be loaded at runtime with `--rules PATH`.

## Pull requests

- Keep changes small and focused
- Update docs if user-facing behavior changes
- CI must pass before merge

## Reporting issues

Use the GitHub issue templates for bugs and feature requests.