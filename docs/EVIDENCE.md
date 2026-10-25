# EVIDENCE — research record and live verification

Status: research summary from 2026-10-12, plus live build-host verification on 2026-10-23. Historical demand claims are retained as context, not as re-verified statistics for launch copy.

## Research context

The project was selected from a private research ledger after comparing Windows native-build diagnostics with existing tools. The public summary is:

- Native npm modules commonly fail on Windows when the Visual Studio Build Tools, Windows SDK, Python, or node-gyp configuration are missing or mismatched.
- `vswhere.exe` reports Visual Studio instances but does not combine that result with Python, node-gyp, SDK-version, environment-variable, or support-bundle checks.
- The deprecated `windows-build-tools` package addressed installation, not diagnosis, and is not maintained as a diagnosis layer.
- Multiple existing tools and documentation sources cover parts of the setup problem; none of the sources checked in the original research owned a read-only, node-gyp-focused diagnostic report with a redacted bundle.

The original queries and source URLs remain in the private research ledger. Before using any historical count or popularity claim in launch material, re-run the query and record the date and URL.

## Live verification on the build host (2026-10-23)

These results were observed directly on the Windows 11 build host:

| Observation | Result |
|---|---|
| `vswhere` positive probe with the VC tools component | `C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools` |
| `vswhere` negative probe with a missing component | empty output |
| Visual Studio standard path | `C:\Program Files (x86)\Microsoft Visual Studio\Installer\vswhere.exe` |
| Windows SDK registry key | `HKLM\SOFTWARE\WOW6432Node\Microsoft\Microsoft SDKs\Windows\v10.0` |
| SDK installation folder | `C:\Program Files (x86)\Windows Kits\10\` |
| SDK product version | `10.0.26100` |
| Python | `3.12.10` |
| Node.js | `24.18.0` |
| npm | `11.16.0` |
| Live doctor result | 11 pass, 0 warn, 0 error, exit `0` |
| Exact activation path | `C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvarsall.bat` |

## Binding decisions

1. Diagnose existing state; never install or repair.
2. Use JSON rule packs rather than YAML to keep the runtime standard-library-only.
3. Keep normal runs read-only; `--bundle` is the only write path.
4. Validate rule packs before probing; invalid packs exit `4`.
5. Treat a missing Visual Studio and SDK together as an unavailable environment, not a crash.

## Known research limitations

- The original demand count and star counts were not re-queried during this build.
- No claim is made that the checked alternatives are exhaustive.
- The live verification is one Windows 11 host, not a cross-version matrix.
- CI and clean-clone verification are separate from the historical research record.
