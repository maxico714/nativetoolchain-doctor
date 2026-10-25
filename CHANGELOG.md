# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-10-23

### Added

- JSON rule-pack engine with validation (`rules.py`)
- Read-only probes for VS, SDK, Python, Node, npm, node-gyp, environment (`probes.py`)
- Rule evaluation with severity mapping and fix-line generation (`engine.py`)
- Human, JSON, and redacted Markdown bundle reporters (`report.py`)
- CLI with `run`, `rules list`, `doctor`, `--json`, `--bundle`, `--dry-run`, `--rules` (`cli.py`)
- 11-rule pack v2026.10.1 covering VS/VC, SDK, Python, Node, npm, msvs_version, SDK env, INCLUDE/LIB, cl.exe
- Unit, integration, security, adversarial, and live test suites
- CI workflow for Python 3.10–3.12 on Windows
- Wheel packaging with rule data included

### Security

- Read-only by construction: no writes outside `--bundle`, no shell, no network, no registry writes
- Bundle redaction for username, user path segments, and secret-like values

[0.1.0]: https://github.com/<owner>/nativetoolchain-doctor/releases/tag/v0.1.0