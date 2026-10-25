"""Command-line interface for nativetoolchain-doctor."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from . import __version__
from .engine import Report, build_report
from .probes import ProbeContext, probe_sdk_install, probe_vs_install_path
from .report import render_bundle, render_json, render_text
from .rules import RuleError, RulePack, load_rules


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="nativetoolchain-doctor",
        description="Offline, read-only Windows node-gyp / MSVC / SDK diagnostics.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument(
        "--rules",
        type=Path,
        default=None,
        help="use an alternate JSON rule pack (default: packaged v1 rules)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="run diagnostics")
    run.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    run.add_argument("--bundle", type=Path, default=None, help="write a redacted Markdown bundle")
    run.add_argument("--dry-run", action="store_true", help="list rules without probing")

    rules = sub.add_parser("rules", help="inspect the rule pack")
    rules_sub = rules.add_subparsers(dest="rules_command", required=True)
    rules_sub.add_parser("list", help="list rule ids, names and severity")

    sub.add_parser("doctor", help="self-check the doctor and its rule pack")
    return parser


def _list_rules(pack: RulePack) -> int:
    print(f"rule pack: {pack.version}")
    for rule in pack.rules:
        print(f"{rule.id:6} {rule.severity:5} {rule.name}")
    return 0


def _dry_run(pack: RulePack) -> int:
    print(f"rule pack: {pack.version} ({len(pack.rules)} rules)")
    for rule in pack.rules:
        print(f"{rule.id:6} {rule.severity:5} {rule.name} [probe: {rule.probe}]")
    return 0


def _bundle(report: Report, path: Path, context: ProbeContext) -> int:
    try:
        path.write_text(render_bundle(report, context.env), encoding="utf-8")
    except OSError as exc:
        print(f"error: cannot write bundle: {exc}", file=sys.stderr)
        return 3
    print(f"bundle: {path}", file=sys.stderr)
    return 0


def _doctor(pack: RulePack, context: ProbeContext) -> int:
    vs = probe_vs_install_path(context)
    sdk = probe_sdk_install(context)
    print(f"nativetoolchain-doctor {__version__} (rules {pack.version})")
    print(f"platform: {context.platform}")
    print(f"python: {sys.executable}")
    print(f"vs: {vs.value or 'not detected'}")
    print(f"sdk: {sdk.value or 'not detected'}")
    if not vs.value and not sdk.value:
        print("doctor: no Visual Studio or Windows SDK detected", file=sys.stderr)
        return 3
    print("doctor: ready")
    return 0


def main(argv: Sequence[str] | None = None, context: ProbeContext | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        pack = load_rules(args.rules)
    except RuleError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 4

    if args.command == "rules":
        return _list_rules(pack)
    if args.command == "doctor":
        return _doctor(pack, context or ProbeContext())
    if args.command == "run":
        if args.dry_run:
            return _dry_run(pack)
        ctx = context or ProbeContext()
        report = build_report(pack, ctx)
        if args.json:
            print(render_json(report))
        else:
            print(render_text(report))
        if args.bundle is not None:
            result = _bundle(report, args.bundle, ctx)
            if result != 0:
                return result
        return report.exit_code()
    parser.error(f"unknown command: {args.command}")
    return 2
