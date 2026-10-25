# nativetoolchain-doctor

Offline, read-only Windows diagnostics for node-gyp, MSVC Build Tools, the Windows SDK, and the Python/npm pieces those builds depend on.

Native npm packages such as `bcrypt`, `sharp`, and `canvas` often fail on Windows with a long `node-gyp` error. The usual cause is a missing or mismatched Visual Studio Build Tools, Windows SDK, Python, or `msvs_version` setting. `nativetoolchain-doctor` reads the machine, explains what is missing or inconsistent, and prints the exact `vcvarsall.bat` command to use. It never installs anything and never changes system settings.

## What it checks

| Rule | Severity | Check |
|---|---|---|
| `VS001` | error | Visual Studio Build Tools with the VC tools component |
| `VS002` | error | `vcvarsall.bat` exists under the detected VC tools |
| `SDK001` | error | Windows 10/11 SDK is installed |
| `SDK002` | error | Windows SDK version is 10.0 or newer |
| `PY001` | error | Python 3.8+ is available for node-gyp |
| `NODE001` | error | Node.js is available |
| `NPM001` | error | npm is available |
| `GYP001` | warning | node-gyp `msvs_version` is compatible when set |
| `ENV001` | warning | `WindowsSdkDir` is valid when set |
| `ENV002` | warning | `INCLUDE`/`LIB` paths are valid when set |
| `PATH001` | info | whether `cl.exe` is already on `PATH` (expected: no) |

## Requirements

- Windows 10 or 11. Tested on Windows 11; Windows Server is not verified.
- Python 3.10 or newer.
- No administrator rights, network access, or paid service is required at runtime.
- Visual Studio Build Tools and the Windows SDK may be absent; the doctor reports that state instead of trying to install them.

## Install from a checkout

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install .
.venv\Scripts\nativetoolchain-doctor.exe run
```

For an editable development install:

```powershell
python -m pip install -e ".[dev]"
```

## Quickstart

```powershell
nativetoolchain-doctor run
```

Example output from a Windows 11 machine with a working Build Tools installation:

```text
nativetoolchain-doctor 0.1.0 (rules 2026.10.1)
platform: Windows-11-10.0.26200-SP0

[PASS ] VS001 Visual Studio Build Tools with VC tools
        vswhere: C:\Program Files (x86)\Microsoft Visual Studio\Installer\vswhere.exe
[PASS ] VS002 vcvarsall.bat available
        exact vcvarsall.bat found
[PASS ] SDK001 Windows 10/11 SDK installed
        registry: SOFTWARE\Microsoft\Microsoft SDKs\Windows\v10.0
[PASS ] SDK002 Windows SDK version 10.0 or newer
        registry ProductVersion
[PASS ] PY001 Python 3.8+ available for node-gyp
        Python 3.12.10
[PASS ] NODE001 Node.js available
        v24.18.0
[PASS ] NPM001 npm available
        11.16.0
[PASS ] GYP001 node-gyp MSVS version compatible
        msvs_version not set; node-gyp will auto-detect
[PASS ] ENV001 WindowsSdkDir is valid when set
        WindowsSdkDir not set; registry fallback is used
[PASS ] ENV002 INCLUDE/LIB paths are valid when set
        INCLUDE/LIB not set; vcvarsall must be called first
[PASS ] PATH001 cl.exe visibility (informational)
        cl.exe is not on PATH; run vcvarsall first (expected)

summary: 11 passed, 0 warnings, 0 errors, 0 info
exit: 0

exact fix line:
  set "VCVARS=C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvarsall.bat"
  cmd /k ""%VCVARS%" x64"
```

## Commands

```text
nativetoolchain-doctor run [--json] [--bundle PATH] [--dry-run]
nativetoolchain-doctor rules list
nativetoolchain-doctor doctor
nativetoolchain-doctor --rules PATH run
nativetoolchain-doctor --version
```

- `run` prints the human report and returns a meaningful exit code.
- `run --json` prints one JSON object for scripts and issue templates.
- `run --bundle PATH` writes a redacted Markdown support bundle. This is the only command that writes a file.
- `run --dry-run` lists the rules without running probes.
- `rules list` lists rule IDs, severities, and names.
- `doctor` checks that the tool can load its rules and find a Visual Studio or SDK installation.
- `--rules PATH` loads an alternate JSON rule pack. A custom pack can use any probe listed below; it cannot add shell commands or arbitrary code.

### Exit codes

| Code | Meaning |
|---|---|
| `0` | All checks passed. |
| `1` | One or more error-severity checks failed. |
| `2` | No errors; one or more warnings. |
| `3` | Neither Visual Studio nor a Windows SDK was detected, so the environment is unavailable. |
| `4` | The rule pack could not be read or validated. |

## Rule packs

The packaged rules live at `src/nativetoolchain_doctor/rules/v1/rules.json` and are included in the wheel. A rule has an `id`, `name`, `probe`, `expected`, `severity` (`error`, `warn`, or `info`), and `fix_hint`.

Available probes: `vs_install_path`, `vcvarsall_path`, `sdk_install`, `sdk_version`, `python_version`, `node_version`, `npm_version`, `msvs_version`, `sdk_env`, `compile_env`, and `cl_path`.

Available expected types: `non_empty`, `version_ge`, `path_exists`, `sdk_env_valid`, `compile_env_valid`, `msvs_compatible`, and `optional`.

## Privacy and safety

- No telemetry, analytics, network requests, or background services.
- Read-only by construction: no registry writes, no installs, no compiler invocation, and no changes to `PATH` or other environment variables.
- Subprocesses use fixed argument lists with `shell=False` and timeouts.
- Normal runs write no files. `--bundle` writes exactly the path you provide.
- Bundles redact the current username, `C:\Users\<name>` path segments, and values that look like tokens, passwords, or API keys. Review a bundle before sharing it.
- `--json` output is not redacted; use `--bundle` for support requests.

## Limitations

- Windows-only. It does not diagnose macOS or Linux builds.
- It detects Visual Studio through `vswhere`, `VSINSTALLDIR`, or the legacy VS7 registry key; unusual custom installations may need a manual rule pack.
- It does not compile a test program, so a detected toolchain can still be broken in ways outside these checks.
- `PATH001` is informational: `cl.exe` is normally absent until `vcvarsall.bat` is run.
- No automatic repairs. Fix hints are text only.
- The project is not published to PyPI yet. Build from a checkout until the publish gate is complete.

## Development

```powershell
python -m pip install -e ".[dev]"
ruff check src tests
ruff format --check src tests
mypy src
python -m pytest -m "not live"
python -m pytest -m live
python -m pip wheel . --no-deps -w dist
```

`pytest -m live` requires a real Windows toolchain. The default CI suite excludes that marker; a manual workflow job runs it on `windows-latest`.

## Documentation

- [docs/PRODUCT.md](docs/PRODUCT.md) — problem, users, scope, risks
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — components, interfaces, security model
- [docs/ROADMAP.md](docs/ROADMAP.md) — v0.1 status and later work
- [docs/VERIFICATION.md](docs/VERIFICATION.md) — commands and evidence from this build
- [docs/EVIDENCE.md](docs/EVIDENCE.md) — research record that motivated the project
- [docs/MAINTAINING.md](docs/MAINTAINING.md) — triage and release process

## License

MIT. See [LICENSE](LICENSE).
