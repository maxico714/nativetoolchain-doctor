from __future__ import annotations

import subprocess
from pathlib import Path

from nativetoolchain_doctor.probes import (
    KITS_KEY,
    SDK_KEY,
    VS7_KEY,
    env_value,
    parse_version,
    probe_cl_path,
    probe_compile_env,
    probe_msvs_version,
    probe_node_version,
    probe_npm_version,
    probe_python_version,
    probe_sdk_env,
    probe_sdk_install,
    probe_sdk_version,
    probe_vcvarsall_path,
    probe_vs_install_path,
)
from tests.support import completed, make_context


def test_env_value_is_case_insensitive() -> None:
    assert env_value({"PROGRAMFILES(X86)": r"C:\PF"}, "ProgramFiles(x86)") == r"C:\PF"
    assert env_value({"programfiles": r"C:\P"}, "ProgramFiles") == r"C:\P"
    assert env_value({"other": "x"}, "ProgramFiles") is None


def test_parse_version() -> None:
    assert parse_version("v24.18.0") == "24.18.0"
    assert parse_version("Python 3.12.10") == "3.12.10"
    assert parse_version("10.0.26100.0") == "10.0.26100.0"
    assert parse_version("no version") == ""


def test_vswhere_via_path() -> None:
    context = make_context(
        which={"vswhere": r"C:\VS\vswhere.exe"},
        runner=lambda _argv, _timeout: completed(r"C:\VS\2022"),
    )
    result = probe_vs_install_path(context)
    assert result.value == r"C:\VS\2022"
    assert "vswhere:" in result.detail


def test_vswhere_standard_path_fallback(tmp_path: Path) -> None:
    installer = tmp_path / "Microsoft Visual Studio" / "Installer"
    installer.mkdir(parents=True)
    (installer / "vswhere.exe").write_text("", encoding="utf-8")
    context = make_context(
        env={"PROGRAMFILES(X86)": str(tmp_path)},
        runner=lambda _argv, _timeout: completed(r"C:\VS\2022"),
    )
    assert probe_vs_install_path(context).value == r"C:\VS\2022"


def test_vswhere_env_fallback() -> None:
    context = make_context(env={"VSINSTALLDIR": r"C:\VS"})
    result = probe_vs_install_path(context)
    assert result.value == r"C:\VS"
    assert "VSINSTALLDIR" in result.detail


def test_vswhere_registry_fallback() -> None:
    context = make_context(registry={(VS7_KEY, "17.0"): r"C:\VS"})
    result = probe_vs_install_path(context)
    assert result.value == r"C:\VS"
    assert "VS7" in result.detail


def test_vswhere_missing() -> None:
    result = probe_vs_install_path(make_context())
    assert result.value == ""
    assert "no VSINSTALLDIR" in result.detail


def test_vswhere_empty_output() -> None:
    context = make_context(
        which={"vswhere": "vswhere.exe"},
        runner=lambda _argv, _timeout: completed(""),
    )
    assert probe_vs_install_path(context).value == ""


def test_vswhere_timeout() -> None:
    def runner(_argv, timeout: float) -> subprocess.CompletedProcess[str]:
        raise subprocess.TimeoutExpired(cmd="vswhere", timeout=timeout)

    context = make_context(which={"vswhere": "vswhere.exe"}, runner=runner)
    result = probe_vs_install_path(context)
    assert result.value == ""
    assert "vswhere failed" in result.detail


def test_vcvarsall_present(tmp_path: Path) -> None:
    vcvars = tmp_path / "VC" / "Auxiliary" / "Build" / "vcvarsall.bat"
    vcvars.parent.mkdir(parents=True)
    vcvars.write_text("", encoding="utf-8")
    result = probe_vcvarsall_path(make_context(env={"VSINSTALLDIR": str(tmp_path)}))
    assert result.value == str(vcvars)


def test_vcvarsall_missing() -> None:
    result = probe_vcvarsall_path(make_context(env={"VSINSTALLDIR": r"C:\missing"}))
    assert result.value == ""


def test_sdk_install_from_registry(tmp_path: Path) -> None:
    context = make_context(registry={(SDK_KEY, "InstallationFolder"): str(tmp_path)})
    result = probe_sdk_install(context)
    assert result.value == str(tmp_path)
    assert "registry" in result.detail


def test_sdk_install_from_kits_registry(tmp_path: Path) -> None:
    context = make_context(registry={(KITS_KEY, "KitsRoot10"): str(tmp_path)})
    assert probe_sdk_install(context).value == str(tmp_path)


def test_sdk_install_from_env(tmp_path: Path) -> None:
    assert probe_sdk_install(make_context(env={"WindowsSdkDir": str(tmp_path)})).value == str(
        tmp_path
    )


def test_sdk_install_missing() -> None:
    result = probe_sdk_install(make_context())
    assert result.value == ""
    assert "not found" in result.detail


def test_sdk_version_from_registry() -> None:
    context = make_context(registry={(SDK_KEY, "ProductVersion"): "10.0.26100.0"})
    result = probe_sdk_version(context)
    assert result.value == "10.0.26100.0"


def test_sdk_version_from_bin(tmp_path: Path) -> None:
    sdk = tmp_path / "sdk"
    (sdk / "bin" / "10.0.19041.0").mkdir(parents=True)
    (sdk / "bin" / "10.0.26100.0").mkdir()
    context = make_context(registry={(SDK_KEY, "InstallationFolder"): str(sdk)})
    assert probe_sdk_version(context).value == "10.0.26100.0"


def test_sdk_version_without_bin(tmp_path: Path) -> None:
    context = make_context(registry={(SDK_KEY, "InstallationFolder"): str(tmp_path)})
    result = probe_sdk_version(context)
    assert result.value == ""
    assert "SDK bin" in result.detail


def test_python_node_and_npm_versions() -> None:
    outputs = {
        "python.exe": "Python 3.12.10",
        "node.exe": "v24.18.0",
        "npm.cmd": "11.16.0",
    }

    def runner(argv, _timeout: float) -> subprocess.CompletedProcess[str]:
        return completed(outputs.get(Path(str(argv[0])).name.lower(), ""))

    context = make_context(
        which={"python": "python.exe", "node": "node.exe", "npm": "npm.cmd"},
        runner=runner,
    )
    assert probe_python_version(context).value == "3.12.10"
    assert probe_node_version(context).value == "24.18.0"
    assert probe_npm_version(context).value == "11.16.0"


def test_version_missing_executable() -> None:
    result = probe_python_version(make_context())
    assert result.value == ""
    assert "not found" in result.detail


def test_version_nonzero_exit() -> None:
    context = make_context(
        which={"python": "python.exe"},
        runner=lambda _argv, _timeout: completed("", returncode=1),
    )
    result = probe_python_version(context)
    assert result.value == ""
    assert "exited 1" in result.detail


def test_version_timeout() -> None:
    def runner(_argv, timeout: float) -> subprocess.CompletedProcess[str]:
        raise subprocess.TimeoutExpired(cmd="python", timeout=timeout)

    context = make_context(which={"python": "python.exe"}, runner=runner)
    result = probe_python_version(context)
    assert result.value == ""
    assert "timed out" in result.detail


def test_msvs_unset_and_set() -> None:
    def unset(_argv, _timeout):
        return completed("undefined")

    def configured(_argv, _timeout):
        return completed("2022")

    assert probe_msvs_version(make_context(which={"npm": "npm.cmd"}, runner=unset)).value == ""
    assert (
        probe_msvs_version(make_context(which={"npm": "npm.cmd"}, runner=configured)).value
        == "2022"
    )


def test_msvs_without_npm() -> None:
    assert probe_msvs_version(make_context()).value == ""


def test_sdk_env_probe(tmp_path: Path) -> None:
    assert probe_sdk_env(make_context()).value == ""
    assert probe_sdk_env(make_context(env={"WindowsSdkDir": str(tmp_path)})).value == str(tmp_path)


def test_compile_env_probe(tmp_path: Path) -> None:
    assert probe_compile_env(make_context()).value == "unset"
    include = tmp_path / "include"
    lib = tmp_path / "lib"
    include.mkdir()
    lib.mkdir()
    context = make_context(env={"include": str(include), "LIB": str(lib)})
    assert probe_compile_env(context).value == "ok"
    broken = make_context(env={"INCLUDE": str(tmp_path / "missing")})
    assert probe_compile_env(broken).value == "invalid"


def test_cl_path_probe() -> None:
    assert probe_cl_path(make_context(which={"cl": r"C:\VC\cl.exe"})).value == r"C:\VC\cl.exe"
    assert probe_cl_path(make_context()).value == ""
