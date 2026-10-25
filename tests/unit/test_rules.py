from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from nativetoolchain_doctor.rules import RuleError, load_rules, load_rules_text

BASE = {
    "rule_pack": "test.1",
    "rules": [
        {
            "id": "R1",
            "name": "test rule",
            "probe": "vs_install_path",
            "expected": {"type": "non_empty"},
            "severity": "error",
            "fix_hint": "fix it",
        }
    ],
}


def _text(mutator=None) -> str:
    data = copy.deepcopy(BASE)
    if mutator is not None:
        mutator(data)
    return json.dumps(data)


def test_packaged_rule_pack_loads() -> None:
    pack = load_rules()
    assert pack.version == "2026.10.1"
    assert len(pack.rules) == 11
    assert {rule.id for rule in pack.rules} == {
        "VS001",
        "VS002",
        "SDK001",
        "SDK002",
        "PY001",
        "NODE001",
        "NPM001",
        "GYP001",
        "ENV001",
        "ENV002",
        "PATH001",
    }


def test_minimal_pack_loads() -> None:
    pack = load_rules_text(_text())
    assert pack.version == "test.1"
    assert pack.rules[0].id == "R1"


def test_invalid_json_rejected() -> None:
    with pytest.raises(RuleError, match="valid JSON"):
        load_rules_text("{")


def test_missing_version_rejected() -> None:
    with pytest.raises(RuleError, match="rule_pack"):
        load_rules_text(_text(lambda data: data.pop("rule_pack")))


def test_empty_rules_rejected() -> None:
    with pytest.raises(RuleError, match="non-empty rules"):
        load_rules_text(_text(lambda data: data.update(rules=[])))


def test_missing_field_rejected() -> None:
    with pytest.raises(RuleError, match="missing required field"):
        load_rules_text(_text(lambda data: data["rules"][0].pop("fix_hint")))


def test_duplicate_ids_rejected() -> None:
    def mutate(data) -> None:
        data["rules"].append(copy.deepcopy(data["rules"][0]))

    with pytest.raises(RuleError, match="unique"):
        load_rules_text(_text(mutate))


def test_unknown_probe_rejected() -> None:
    with pytest.raises(RuleError, match="unknown probe"):
        load_rules_text(_text(lambda data: data["rules"][0].update(probe="nope")))


def test_bad_severity_rejected() -> None:
    with pytest.raises(RuleError, match="severity"):
        load_rules_text(_text(lambda data: data["rules"][0].update(severity="fatal")))


def test_unknown_expected_type_rejected() -> None:
    with pytest.raises(RuleError, match="expected type"):
        load_rules_text(_text(lambda data: data["rules"][0]["expected"].update(type="magic")))


def test_version_ge_requires_minimum() -> None:
    with pytest.raises(RuleError, match="minimum"):
        load_rules_text(
            _text(lambda data: data["rules"][0]["expected"].update({"type": "version_ge"}))
        )


def test_msvs_requires_vs_major() -> None:
    with pytest.raises(RuleError, match="vs_major"):
        load_rules_text(
            _text(lambda data: data["rules"][0]["expected"].update({"type": "msvs_compatible"}))
        )


def test_non_utf8_file_is_clean_config_error(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    path.write_bytes(b"\xff\xfe\x00")
    with pytest.raises(RuleError, match="UTF-8"):
        load_rules(path)
