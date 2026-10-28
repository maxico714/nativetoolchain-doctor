from __future__ import annotations

import json
from pathlib import Path

from nativetoolchain_doctor.engine import Report, RuleResult, build_report, evaluate_rule
from nativetoolchain_doctor.probes import SDK_KEY, ProbeResult
from nativetoolchain_doctor.rules import Rule, load_rules, load_rules_text
from tests.support import all_pass_context, completed, make_context, no_environment_context


def make_rule(
    *,
    rule_id: str = "R1",
    expected: dict[str, object] | None = None,
    severity: str = "error",
    probe: str = "vs_install_path",
) -> Rule:
    return Rule(
        id=rule_id,
        name="test rule",
        probe=probe,
        expected=expected or {"type": "non_empty"},
        severity=severity,
        fix_hint="fix it",
    )


def check(rule: Rule, value: str) -> str:
    return evaluate_rule(rule, ProbeResult(value, "detail")).status


def test_non_empty() -> None:
    rule = make_rule()
    assert check(rule, "x") == "pass"
    assert check(rule, "") == "error"


def test_version_ge() -> None:
    rule = make_rule(expected={"type": "version_ge", "minimum": "3.8"})
    assert check(rule, "3.12.10") == "pass"
    assert check(rule, "3.7.9") == "error"
    assert check(rule, "not-a-version") == "error"


def test_path_exists(tmp_path: Path) -> None:
    path = tmp_path / "vcvarsall.bat"
    path.write_text("", encoding="utf-8")
    rule = make_rule(expected={"type": "path_exists"})
    assert check(rule, str(path)) == "pass"
    assert check(rule, str(tmp_path / "missing")) == "error"


def test_sdk_env_valid(tmp_path: Path) -> None:
    rule = make_rule(expected={"type": "sdk_env_valid"}, severity="warn")
    assert check(rule, "") == "pass"
    assert check(rule, str(tmp_path)) == "pass"
    assert check(rule, str(tmp_path / "missing")) == "warn"


def test_compile_env_valid() -> None:
    rule = make_rule(expected={"type": "compile_env_valid"}, severity="warn")
    assert check(rule, "unset") == "pass"
    assert check(rule, "ok") == "pass"
    assert check(rule, "invalid") == "warn"


def test_msvs_compatible() -> None:
    rule = make_rule(expected={"type": "msvs_compatible", "vs_major": "2022"}, severity="warn")
    assert check(rule, "") == "pass"
    assert check(rule, "2022") == "pass"
    assert check(rule, "17.0") == "pass"
    assert check(rule, "2019") == "warn"
    assert check(rule, "unknown") == "warn"


def test_optional_always_passes() -> None:
    rule = make_rule(expected={"type": "optional"}, severity="info")
    assert check(rule, "") == "pass"
    assert check(rule, "anything") == "pass"


def test_info_failure_is_info() -> None:
    rule = make_rule(severity="info")
    assert check(rule, "") == "info"


def test_summary_and_exit_codes() -> None:
    rule = make_rule()
    results = (
        RuleResult(rule, "pass", "", "x"),
        RuleResult(rule, "warn", "", ""),
        RuleResult(rule, "error", "", ""),
        RuleResult(rule, "info", "", ""),
    )
    report = Report("test", results)
    assert report.summary == {"pass": 1, "warn": 1, "error": 1, "info": 1}
    assert report.exit_code() == 1


def test_warning_only_exit_code() -> None:
    rule = make_rule()
    report = Report("test", (RuleResult(rule, "pass", "", "x"), RuleResult(rule, "warn", "", "")))
    assert report.exit_code() == 2


def test_environment_unavailable_exit_code() -> None:
    rule = make_rule()
    report = Report("test", (RuleResult(rule, "error", "", ""),), environment_unavailable=True)
    assert report.exit_code() == 3


def test_fix_lines() -> None:
    vcvars = make_rule(rule_id="VS002", probe="vcvarsall_path", expected={"type": "path_exists"})
    msvs = make_rule(
        rule_id="GYP001",
        probe="msvs_version",
        expected={"type": "msvs_compatible", "vs_major": "2022"},
        severity="warn",
    )
    report = Report(
        "test",
        (
            RuleResult(vcvars, "pass", "", r"C:\VS\vcvarsall.bat"),
            RuleResult(msvs, "warn", "", "2019"),
        ),
    )
    lines = report.fix_lines()
    assert r'set "VCVARS=C:\VS\vcvarsall.bat"' in lines
    assert "npm config set msvs_version 2022" in lines


def test_build_report_all_pass(tmp_path: Path) -> None:
    report = build_report(load_rules(), all_pass_context(tmp_path))
    assert report.exit_code() == 0
    assert report.summary == {"pass": 11, "warn": 0, "error": 0, "info": 0}
    assert any("vcvarsall.bat" in line for line in report.fix_lines())


def test_build_report_custom_pack_without_environment_probes() -> None:
    pack = load_rules_text(
        json.dumps(
            {
                "rule_pack": "custom.1",
                "rules": [
                    {
                        "id": "PY001",
                        "name": "python",
                        "probe": "python_version",
                        "expected": {"type": "version_ge", "minimum": "3.8"},
                        "severity": "error",
                        "fix_hint": "install python",
                    }
                ],
            }
        )
    )
    context = make_context(
        which={"python": "python.exe"},
        runner=lambda _argv, _timeout: completed("Python 3.12.10"),
    )
    report = build_report(pack, context)
    assert report.environment_unavailable is False
    assert report.exit_code() == 0


def test_build_report_warning_only(tmp_path: Path) -> None:
    report = build_report(load_rules(), all_pass_context(tmp_path, msvs="2019"))
    assert report.exit_code() == 2
    assert report.summary["warn"] == 1


def test_build_report_missing_environment() -> None:
    report = build_report(load_rules(), no_environment_context(Path.cwd()))
    assert report.environment_unavailable is True
    assert report.exit_code() == 3


def test_build_report_missing_vs_with_sdk_fallback(tmp_path: Path) -> None:
    sdk = tmp_path / "sdk"
    sdk.mkdir()
    context = make_context(
        env={},
        which={"python": "python.exe", "node": "node.exe", "npm": "npm.cmd"},
        runner=lambda argv, _timeout: (
            completed("Python 3.12.10")
            if Path(str(argv[0])).name.lower().startswith("python")
            else completed("v24.18.0")
        ),
        registry={
            (SDK_KEY, "InstallationFolder"): str(sdk),
            (SDK_KEY, "ProductVersion"): "10.0.26100",
        },
    )
    report = build_report(load_rules(), context)
    assert report.environment_unavailable is False
    assert report.exit_code() == 1
    statuses = {result.rule.id: result.status for result in report.results}
    assert statuses["SDK001"] == "pass"
    assert statuses["VS001"] == "error"
