from __future__ import annotations

import time
from pathlib import Path

from nativetoolchain_doctor.engine import build_report
from nativetoolchain_doctor.probes import SDK_KEY
from nativetoolchain_doctor.rules import load_rules
from tests.support import all_pass_context, completed, make_context


def test_empty_environment_is_clean_exit_3() -> None:
    report = build_report(load_rules(), make_context())
    assert report.environment_unavailable is True
    assert report.exit_code() == 3


def test_huge_environment_does_not_hang(tmp_path: Path) -> None:
    huge = ";".join(str(tmp_path / f"entry-{index}") for index in range(5000))
    context = make_context(env={"INCLUDE": huge, "LIB": huge, "PATH": huge})
    started = time.monotonic()
    report = build_report(load_rules(), context)
    assert time.monotonic() - started < 5.0
    assert report.exit_code() in (1, 2, 3)


def test_corrupt_sdk_env_warns_instead_of_crashing(tmp_path: Path) -> None:
    context = all_pass_context(tmp_path)
    context.env = {**context.env, "WindowsSdkDir": str(tmp_path / "does-not-exist")}
    report = build_report(load_rules(), context)
    statuses = {result.rule.id: result.status for result in report.results}
    assert statuses["ENV001"] == "warn"
    assert report.exit_code() == 2


def test_sdk_bin_with_unversioned_directories(tmp_path: Path) -> None:
    sdk = tmp_path / "sdk"
    (sdk / "bin" / "not-a-version").mkdir(parents=True)
    context = make_context(registry={(SDK_KEY, "InstallationFolder"): str(sdk)})
    report = build_report(load_rules(), context)
    assert report.environment_unavailable is False
    statuses = {result.rule.id: result.status for result in report.results}
    assert statuses["SDK002"] == "error"


def test_unicode_toolchain_path_does_not_crash(tmp_path: Path) -> None:
    unicode_dir = tmp_path / "工具链"
    vcvars = unicode_dir / "VC" / "Auxiliary" / "Build" / "vcvarsall.bat"
    vcvars.parent.mkdir(parents=True)
    vcvars.write_text("", encoding="utf-8")
    sdk = unicode_dir / "sdk"
    (sdk / "bin" / "10.0.26100.0").mkdir(parents=True)
    outputs = {
        "python.exe": "Python 3.12.10",
        "node.exe": "v24.18.0",
        "npm.cmd": "11.16.0",
    }

    def runner(argv, _timeout: float):
        executable = Path(str(argv[0])).name.lower()
        if executable.startswith("npm"):
            return completed("11.16.0" if "--version" in argv else "undefined")
        return completed(outputs.get(executable, ""))

    context = make_context(
        env={"VSINSTALLDIR": str(unicode_dir)},
        which={"python": "python.exe", "node": "node.exe", "npm": "npm.cmd"},
        runner=runner,
        registry={(SDK_KEY, "InstallationFolder"): str(sdk)},
    )
    report = build_report(load_rules(), context)
    assert report.exit_code() == 0
