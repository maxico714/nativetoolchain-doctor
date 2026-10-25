"""Load and validate the rules-as-data pack."""

from __future__ import annotations

import json
from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import Any

SEVERITIES = frozenset({"error", "warn", "info"})
EXPECTED_TYPES = frozenset(
    {
        "non_empty",
        "version_ge",
        "path_exists",
        "sdk_env_valid",
        "compile_env_valid",
        "msvs_compatible",
        "optional",
    }
)
KNOWN_PROBES = frozenset(
    {
        "vs_install_path",
        "vcvarsall_path",
        "sdk_install",
        "sdk_version",
        "python_version",
        "node_version",
        "npm_version",
        "msvs_version",
        "sdk_env",
        "compile_env",
        "cl_path",
    }
)


class RuleError(ValueError):
    """The rule pack is missing, unreadable, or invalid."""


@dataclass(frozen=True)
class Rule:
    id: str
    name: str
    probe: str
    expected: dict[str, Any]
    severity: str
    fix_hint: str


@dataclass(frozen=True)
class RulePack:
    version: str
    rules: tuple[Rule, ...]


def _require(raw: dict[str, Any], key: str) -> Any:
    if key not in raw:
        raise RuleError(f"rule is missing required field {key!r}")
    return raw[key]


def _parse_rule(raw: object, index: int) -> Rule:
    if not isinstance(raw, dict):
        raise RuleError(f"rule {index} must be an object")
    values: dict[str, Any] = raw
    rule_id = _require(values, "id")
    name = _require(values, "name")
    probe = _require(values, "probe")
    expected = _require(values, "expected")
    severity = _require(values, "severity")
    fix_hint = _require(values, "fix_hint")
    if not isinstance(rule_id, str) or not rule_id.strip():
        raise RuleError(f"rule {index} has an invalid id")
    if not isinstance(name, str) or not name.strip():
        raise RuleError(f"rule {rule_id!r} has an invalid name")
    if probe not in KNOWN_PROBES:
        raise RuleError(f"rule {rule_id!r} uses unknown probe {probe!r}")
    if severity not in SEVERITIES:
        raise RuleError(f"rule {rule_id!r} has invalid severity {severity!r}")
    if not isinstance(fix_hint, str):
        raise RuleError(f"rule {rule_id!r} has a non-string fix_hint")
    if not isinstance(expected, dict):
        raise RuleError(f"rule {rule_id!r} expected must be an object")
    expected_map: dict[str, Any] = expected
    expected_type = expected_map.get("type")
    if expected_type not in EXPECTED_TYPES:
        raise RuleError(f"rule {rule_id!r} has unknown expected type {expected_type!r}")
    if expected_type == "version_ge" and "minimum" not in expected_map:
        raise RuleError(f"rule {rule_id!r} version_ge needs a minimum")
    if expected_type == "msvs_compatible" and "vs_major" not in expected_map:
        raise RuleError(f"rule {rule_id!r} msvs_compatible needs vs_major")
    return Rule(
        id=rule_id,
        name=name,
        probe=probe,
        expected=expected_map,
        severity=severity,
        fix_hint=fix_hint,
    )


def load_rules_text(text: str) -> RulePack:
    """Parse a JSON rule pack from text, rejecting invalid schemas."""
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise RuleError(f"rule pack is not valid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise RuleError("rule pack must be a JSON object")
    version = data.get("rule_pack")
    if not isinstance(version, str) or not version.strip():
        raise RuleError("rule pack must have a non-empty rule_pack version")
    raw_rules = data.get("rules")
    if not isinstance(raw_rules, list) or not raw_rules:
        raise RuleError("rule pack must contain a non-empty rules list")
    rules = tuple(_parse_rule(item, index) for index, item in enumerate(raw_rules))
    ids = [rule.id for rule in rules]
    if len(ids) != len(set(ids)):
        raise RuleError("rule ids must be unique")
    return RulePack(version=version, rules=rules)


def load_rules(path: Path | None = None) -> RulePack:
    """Load the packaged rule pack, or a caller-supplied JSON file."""
    if path is None:
        resource = resources.files("nativetoolchain_doctor").joinpath("rules/v1/rules.json")
        try:
            text = resource.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            raise RuleError(f"packaged rule pack is unreadable: {exc}") from exc
        return load_rules_text(text)
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise RuleError(f"rule pack is not valid UTF-8: {path}") from exc
    except OSError as exc:
        raise RuleError(f"rule pack is unreadable: {path}: {exc}") from exc
    return load_rules_text(text)
