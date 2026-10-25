from __future__ import annotations

import subprocess
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path

from nativetoolchain_doctor.probes import SDK_KEY, ProbeContext


def completed(stdout: str = "", returncode: int = 0) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(
        args=["fake"], returncode=returncode, stdout=stdout, stderr=""
    )


def make_context(
    *,
    env: Mapping[str, str] | None = None,
    which: Mapping[str, str] | None = None,
    runner: Callable[[Sequence[str], float], subprocess.CompletedProcess[str]] | None = None,
    registry: Mapping[tuple[str, str], str] | None = None,
) -> ProbeContext:
    which_map = {key.lower(): value for key, value in (which or {}).items()}
    registry_map = dict(registry or {})

    def lookup(name: str) -> str | None:
        return which_map.get(Path(name).name.lower()) or which_map.get(name.lower())

    def read_registry(key: str, value: str) -> str | None:
        return registry_map.get((key, value))

    return ProbeContext(
        env=dict(env or {}),
        platform="win32",
        runner=runner or (lambda _argv, _timeout: completed()),
        which=lookup,
        registry=read_registry,
    )


def all_pass_context(tmp_path: Path, *, msvs: str = "undefined") -> ProbeContext:
    vs = tmp_path / "Users" / "alice" / "vs"
    vcvars = vs / "VC" / "Auxiliary" / "Build" / "vcvarsall.bat"
    vcvars.parent.mkdir(parents=True)
    vcvars.write_text("", encoding="utf-8")
    sdk = tmp_path / "sdk"
    sdk.mkdir()

    registry = {
        (SDK_KEY, "InstallationFolder"): str(sdk),
        (SDK_KEY, "ProductVersion"): "10.0.26100",
    }
    which = {
        "vswhere": str(tmp_path / "vswhere.exe"),
        "python": "python.exe",
        "node": "node.exe",
        "npm": "npm.cmd",
    }

    def runner(argv: Sequence[str], _timeout: float) -> subprocess.CompletedProcess[str]:
        executable = Path(str(argv[0])).name.lower()
        if executable.startswith("vswhere"):
            return completed(str(vs))
        if executable.startswith("python"):
            return completed("Python 3.12.10")
        if executable.startswith("node"):
            return completed("v24.18.0")
        if executable.startswith("npm"):
            if "--version" in argv:
                return completed("11.16.0")
            return completed(msvs)
        return completed("")

    return make_context(
        env={"USERNAME": "alice"},
        which=which,
        runner=runner,
        registry=registry,
    )


def no_environment_context(tmp_path: Path) -> ProbeContext:
    return make_context(
        env={},
        which={
            "python": "python.exe",
            "node": "node.exe",
            "npm": "npm.cmd",
        },
        runner=lambda argv, _timeout: completed(
            "Python 3.12.10" if Path(str(argv[0])).name.lower().startswith("python") else "v24.18.0"
        ),
        registry={},
    )
