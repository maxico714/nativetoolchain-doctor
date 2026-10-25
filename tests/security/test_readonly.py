from __future__ import annotations

from pathlib import Path

from nativetoolchain_doctor import cli
from nativetoolchain_doctor.engine import Report, RuleResult
from nativetoolchain_doctor.report import render_bundle
from nativetoolchain_doctor.rules import Rule
from tests.support import all_pass_context


def _report(detail: str, value: str = "") -> Report:
    rule = Rule(
        id="R1",
        name="test",
        probe="vs_install_path",
        expected={"type": "non_empty"},
        severity="error",
        fix_hint="fix",
    )
    return Report("test", (RuleResult(rule, "pass", detail, value),))


def test_render_bundle_redacts_secret_and_user() -> None:
    report = _report(r"detected C:\Users\alice\VS token=supersecret", r"C:\Users\alice\VS")
    text = render_bundle(report, {"USERNAME": "alice"})
    assert "alice" not in text.lower()
    assert "supersecret" not in text
    assert "<user>" in text
    assert "<redacted>" in text


def test_render_bundle_redacts_generic_user_path() -> None:
    report = _report(r"detected C:\Users\bob\VS")
    text = render_bundle(report, {})
    assert "bob" not in text
    assert r"C:\Users\<user>" in text


def test_run_without_bundle_does_not_write(tmp_path: Path, monkeypatch) -> None:
    working = tmp_path / "cwd"
    working.mkdir()
    monkeypatch.chdir(working)
    context = all_pass_context(tmp_path)
    assert cli.main(["run", "--json"], context=context) == 0
    assert list(working.iterdir()) == []


def test_only_bundle_uses_write_text() -> None:
    source = Path(cli.__file__).read_text(encoding="utf-8")
    assert source.count("write_text") == 1


def test_no_shell_true_or_network_imports() -> None:
    root = Path(cli.__file__).parent
    for name in ("cli.py", "probes.py", "report.py", "rules.py", "engine.py"):
        source = (root / name).read_text(encoding="utf-8")
        assert "shell=True" not in source
        assert "urllib.request" not in source
        assert "http.client" not in source
        assert "import socket" not in source


def test_no_registry_writes() -> None:
    source = (Path(cli.__file__).parent / "probes.py").read_text(encoding="utf-8")
    assert "SetValue" not in source
    assert "CreateKey" not in source
    assert "DeleteKey" not in source
