from __future__ import annotations

import json
from pathlib import Path

from nativetoolchain_doctor.engine import build_report
from nativetoolchain_doctor.report import render_json, render_text, report_to_dict
from nativetoolchain_doctor.rules import load_rules
from tests.support import all_pass_context


def test_report_to_dict_shape(tmp_path: Path) -> None:
    report = build_report(load_rules(), all_pass_context(tmp_path))
    payload = report_to_dict(report)
    assert payload["tool"] == "nativetoolchain-doctor"
    assert payload["rule_pack"] == "2026.10.1"
    assert payload["summary"]["exit_code"] == 0
    assert len(payload["results"]) == 11
    assert payload["fix_lines"]


def test_render_json_round_trips(tmp_path: Path) -> None:
    report = build_report(load_rules(), all_pass_context(tmp_path))
    payload = json.loads(render_json(report))
    assert payload["summary"]["pass"] == 11


def test_render_text_has_summary_and_fix(tmp_path: Path) -> None:
    report = build_report(load_rules(), all_pass_context(tmp_path))
    text = render_text(report)
    assert "11 passed" in text
    assert "exact fix line" in text
    assert "vcvarsall.bat" in text
