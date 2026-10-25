from __future__ import annotations

import json
from pathlib import Path

from nativetoolchain_doctor import cli
from nativetoolchain_doctor.probes import SDK_KEY
from tests.support import all_pass_context, completed, make_context, no_environment_context


def test_rules_list() -> None:
    assert cli.main(["rules", "list"]) == 0


def test_dry_run() -> None:
    assert cli.main(["run", "--dry-run"]) == 0


def test_doctor_ready(tmp_path: Path) -> None:
    assert cli.main(["doctor"], context=all_pass_context(tmp_path)) == 0


def test_doctor_unavailable() -> None:
    assert cli.main(["doctor"], context=make_context()) == 3


def test_run_all_pass(tmp_path: Path, capsys) -> None:
    assert cli.main(["run", "--json"], context=all_pass_context(tmp_path)) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["summary"]["exit_code"] == 0
    assert payload["summary"]["pass"] == 11
    assert payload["rule_pack"] == "2026.10.1"


def test_run_warning_exit(tmp_path: Path) -> None:
    assert cli.main(["run"], context=all_pass_context(tmp_path, msvs="2019")) == 2


def test_run_missing_environment_exit() -> None:
    assert cli.main(["run"], context=no_environment_context(Path.cwd())) == 3


def test_run_vs_missing_but_sdk_present_exit(tmp_path: Path) -> None:
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
            (SDK_KEY, "ProductVersion"): "10.0.26100.0",
        },
    )
    assert cli.main(["run"], context=context) == 1


def test_bundle_is_redacted(tmp_path: Path, capsys) -> None:
    bundle = tmp_path / "bundle.md"
    assert (
        cli.main(
            ["run", "--json", "--bundle", str(bundle)],
            context=all_pass_context(tmp_path),
        )
        == 0
    )
    text = bundle.read_text(encoding="utf-8")
    assert "alice" not in text.lower()
    assert "<user>" in text
    assert "token=" not in text
    assert "bundle:" in capsys.readouterr().err


def test_bundle_write_error_returns_3(tmp_path: Path) -> None:
    target = tmp_path / "directory"
    target.mkdir()
    assert (
        cli.main(
            ["run", "--json", "--bundle", str(target)],
            context=all_pass_context(tmp_path),
        )
        == 3
    )


def test_missing_rule_pack_returns_4(tmp_path: Path, capsys) -> None:
    missing = tmp_path / "missing.json"
    assert cli.main(["--rules", str(missing), "run", "--dry-run"]) == 4
    assert "error:" in capsys.readouterr().err
