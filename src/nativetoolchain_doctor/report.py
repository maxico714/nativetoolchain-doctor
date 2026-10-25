"""Human, JSON and redacted support-bundle reports."""

from __future__ import annotations

import json
import platform
import re
from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Any

from . import __version__
from .engine import Report
from .probes import env_value

_SECRET_RE = re.compile(r"(?i)\b(token|secret|password|api[_-]?key)\b\s*[=:]\s*\S+")
_USER_PATH_RE = re.compile(r"(?i)([A-Z]:\\Users\\)([^\\\s]+)")
_PATH_RULES = frozenset({"vs_install_path", "sdk_install", "vcvarsall_path", "cl_path"})


def redact_text(text: str, env: Mapping[str, str]) -> str:
    """Remove usernames and secret-looking assignments from support text."""
    username = (env_value(env, "USERNAME") or env_value(env, "USER") or "").strip()
    result = text
    if username:
        result = re.sub(re.escape(username), "<user>", result, flags=re.IGNORECASE)
    result = _USER_PATH_RE.sub(lambda match: f"{match.group(1)}<user>", result)
    result = _SECRET_RE.sub(lambda match: f"{match.group(1)}=<redacted>", result)
    return result


def report_to_dict(report: Report) -> dict[str, Any]:
    return {
        "tool": "nativetoolchain-doctor",
        "version": __version__,
        "rule_pack": report.rule_pack,
        "platform": platform.platform(),
        "results": [
            {
                "id": result.rule.id,
                "name": result.rule.name,
                "status": result.status,
                "severity": result.rule.severity,
                "detail": result.detail,
                "fix_hint": result.rule.fix_hint,
            }
            for result in report.results
        ],
        "summary": {**report.summary, "exit_code": report.exit_code()},
        "fix_lines": list(report.fix_lines()),
    }


def render_json(report: Report) -> str:
    return json.dumps(report_to_dict(report), indent=2)


def render_text(report: Report) -> str:
    lines = [
        f"nativetoolchain-doctor {__version__} (rules {report.rule_pack})",
        f"platform: {platform.platform()}",
        "",
    ]
    for result in report.results:
        lines.append(f"[{result.status.upper():5}] {result.rule.id} {result.rule.name}")
        if result.detail:
            lines.append(f"        {result.detail}")
    counts = report.summary
    lines.extend(
        [
            "",
            "summary: "
            f"{counts['pass']} passed, {counts['warn']} warnings, "
            f"{counts['error']} errors, {counts['info']} info",
            f"exit: {report.exit_code()}",
        ]
    )
    fixes = report.fix_lines()
    if fixes:
        lines.append("")
        lines.append("exact fix line:")
        lines.extend(f"  {line}" for line in fixes)
    return "\n".join(lines)


def render_bundle(report: Report, env: Mapping[str, str]) -> str:
    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    summary = report.summary
    lines = [
        "# nativetoolchain-doctor support bundle",
        "",
        f"- Generated: {stamp}",
        f"- Version: {__version__}",
        f"- Rule pack: {report.rule_pack}",
        f"- Platform: {redact_text(platform.platform(), env)}",
        f"- Summary: {summary['pass']} pass, {summary['warn']} warn, "
        f"{summary['error']} error, {summary['info']} info",
        f"- Exit code: {report.exit_code()}",
        "",
        "## Results",
        "",
        "| rule | status | detail |",
        "|---|---|---|",
    ]
    for result in report.results:
        detail = redact_text(result.detail, env)
        if result.rule.probe in _PATH_RULES and result.value:
            detail = f"{detail}; detected={redact_text(result.value, env)}"
        lines.append(f"| {result.rule.id} {result.rule.name} | {result.status} | {detail} |")
    fixes = report.fix_lines()
    if fixes:
        lines.extend(["", "## Fix lines", ""])
        lines.extend(f"```bat\n{redact_text(line, env)}\n```" for line in fixes)
    lines.extend(
        [
            "",
            "## Privacy",
            "",
            "This bundle contains rule results and detected toolchain roots only.",
            "Usernames, secret-looking values and full environment values are redacted.",
            "",
        ]
    )
    return "\n".join(lines)
