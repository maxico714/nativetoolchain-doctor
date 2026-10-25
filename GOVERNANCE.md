# Governance

## Project Structure

`nativetoolchain-doctor` is a single-maintainer project with community contributions. The maintainer has final decision authority on:

- Scope and direction
- Accepting or rejecting pull requests
- Release timing and versioning
- Security handling

## Adding Maintainers

New maintainers may be added after sustained, high-quality contributions (code, reviews, docs, triage) over at least 3 months. The decision is made by the current maintainer.

## Decision Making

- Small changes (bug fixes, test improvements, doc updates): merged on maintainer approval
- Larger changes (new probes, rule pack changes, CLI changes): require discussion in an issue first
- Breaking changes: require a minor or major version bump per SemVer

## Releases

- Patch releases: bug fixes, security fixes
- Minor releases: new rules, new probes, backward-compatible features
- Major releases: breaking CLI changes, rule pack format changes

Releases are tagged and built via the CI workflow. Artifacts are signed (when G3 gate is passed).

## Code of Conduct

All participants are expected to follow the [Code of Conduct](CODE_OF_CONDUCT.md).

## License

The project is licensed under the MIT License. Contributions are accepted under the same license.