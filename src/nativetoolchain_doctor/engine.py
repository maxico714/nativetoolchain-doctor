"""Evaluate rule packs against probe results."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .probes import PROBES, ProbeContext, ProbeResult
from .rules import Rule, RulePack


@dataclass(frozen=True)
class RuleResult:
    rule: Rule
    status: str
    detail: str
    value: str


@dataclass(frozen=True)
class Report:
    rule_pack: str
    results: tuple[RuleResult, ...]
    environment_unavailable: bool = False

    @property
    def summary(self) -> dict[str, int]:
        counts = {"pass": 0, "warn": 0, "error": 0, "info": 0}
        for result in self.results:
            counts[result.status] = counts.get(result.status, 0) + 1
        return counts

    def exit_code(self) -> int:
        if self.environment_unavailable:
            return 3
        counts = self.summary
        if counts["error"]:
            return 1
        if counts["warn"]:
            return 2
        return 0

    def fix_lines(self) -> tuple[str, ...]:
        lines: list[str] = []
        vcvars = next(
            (
                result.value
                for result in self.results
                if result.rule.probe == "vcvarsall_path" and result.status == "pass"
            ),
            "",
        )
        if vcvars:
            lines.append(f'set "VCVARS={vcvars}"')
            lines.append('cmd /k ""%VCVARS%" x64"')
        for result in self.results:
            if result.status in ("warn", "error") and result.rule.id == "GYP001":
                lines.append("npm config set msvs_version 2022")
            if result.status in ("warn", "error") and result.rule.id == "ENV001":
                lines.append('set "WindowsSdkDir=<detected SDK root>"')
        return tuple(dict.fromkeys(lines))


def _version_tuple(value: str) -> tuple[int, ...]:
    parts = [part for part in value.strip().split(".") if part.isdigit()]
    return tuple(int(part) for part in parts)


def _satisfies(rule: Rule, value: str) -> bool:
    expected: dict[str, Any] = rule.expected
    kind = expected["type"]
    if kind == "non_empty":
        return bool(value.strip())
    if kind == "version_ge":
        minimum = str(expected.get("minimum", ""))
        actual_tuple = _version_tuple(value)
        minimum_tuple = _version_tuple(minimum)
        return bool(actual_tuple) and actual_tuple >= minimum_tuple
    if kind == "path_exists":
        return bool(value.strip()) and Path(value).exists()
    if kind == "sdk_env_valid":
        return not value.strip() or Path(value).is_dir()
    if kind == "compile_env_valid":
        return value in ("unset", "ok")
    if kind == "msvs_compatible":
        if not value.strip():
            return True
        major = str(expected.get("vs_major", ""))
        accepted = {major, "17", "17.0"} if major == "2022" else {major}
        return value.strip() in accepted
    if kind == "optional":
        return True
    raise ValueError(f"unknown expected type: {kind}")


def evaluate_rule(rule: Rule, probe_result: ProbeResult) -> RuleResult:
    ok = _satisfies(rule, probe_result.value)
    if ok:
        status = "pass"
    elif rule.severity == "info":
        status = "info"
    else:
        status = rule.severity
    detail = probe_result.detail
    if not ok and not detail:
        detail = f"value {probe_result.value!r} did not satisfy {rule.expected!r}"
    return RuleResult(rule=rule, status=status, detail=detail, value=probe_result.value)


def build_report(pack: RulePack, context: ProbeContext) -> Report:
    probe_results: dict[str, ProbeResult] = {}
    for probe_name in dict.fromkeys(rule.probe for rule in pack.rules):
        probe_results[probe_name] = PROBES[probe_name](context)
    results = tuple(evaluate_rule(rule, probe_results[rule.probe]) for rule in pack.rules)
    vs_result = probe_results.get("vs_install_path")
    sdk_result = probe_results.get("sdk_install")
    unavailable = False
    if vs_result is not None and sdk_result is not None:
        unavailable = not vs_result.value and not sdk_result.value
    return Report(rule_pack=pack.version, results=results, environment_unavailable=unavailable)
