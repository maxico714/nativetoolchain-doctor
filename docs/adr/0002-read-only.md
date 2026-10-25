# ADR-0002: Read-only by construction

- Status: accepted
- Date: 2026-10-23

## Context

The tool is intended for locked-down corporate machines and for support triage. Installation, repair, registry changes, or environment mutation would require privileges and would create a class of failure the tool cannot safely undo.

## Decision

- Normal runs do not write files.
- Probes only read environment variables, registry values, installation paths, and version output.
- Subprocesses use fixed argument lists with `shell=False` and timeouts.
- The only write path is `--bundle PATH`, explicitly requested by the user, and it writes redacted Markdown.

## Consequences

- No administrator requirement.
- The tool cannot repair a broken toolchain; it reports the state and prints commands for the user.
- Tests assert that a normal run creates no files and that no write APIs exist outside the bundle path.
- Bundle review remains the user's responsibility before sharing.
