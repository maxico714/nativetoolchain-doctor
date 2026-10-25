# Pull Request Template

## Description

Briefly describe what this PR does.

## Type of Change

- [ ] Bug fix
- [ ] New probe
- [ ] New rule / rule pack change
- [ ] CLI enhancement
- [ ] Documentation
- [ ] Test improvement
- [ ] Refactor / internal
- [ ] CI / packaging

## Testing

- [ ] All existing tests pass (`pytest -m "not live"`)
- [ ] Added tests for new behavior
- [ ] Live test verified on Windows (`pytest -m live` or manual `nativetoolchain-doctor run`)
- [ ] Ruff check passes
- [ ] Ruff format check passes
- [ ] Mypy passes

## Checklist

- [ ] No `TODO`/`FIXME` in source
- [ ] Type hints added/updated
- [ ] Docs updated if user-facing change
- [ ] CHANGELOG.md updated (or will be in release)

## Screenshots / Output

If applicable, paste relevant command output or bundle excerpt.