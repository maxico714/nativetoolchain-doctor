# ADR-0001: JSON rule packs, not YAML

- Status: accepted
- Date: 2026-10-23

## Context

The product needs detection rules to be data so Visual Studio and Windows SDK changes can be patched without rewriting the engine. The original scaffold assumed YAML. The package promises no runtime dependencies outside the Python standard library. YAML support would add a parser dependency and a larger untrusted-input surface.

## Decision

Ship the v0.1 pack as JSON at `src/nativetoolchain_doctor/rules/v1/rules.json`. Validate it with the standard library and expose `--rules PATH` for an alternate pack.

## Consequences

- No YAML comments or anchors.
- Rule changes remain data-only.
- A YAML adapter can be added later as an optional extra without changing the engine contract.
- Invalid or non-UTF-8 packs fail cleanly with exit code `4` before any probe runs.
