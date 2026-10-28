"""Read-only probes for Windows native build toolchains."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path

Runner = Callable[[Sequence[str], float], subprocess.CompletedProcess[str]]
RegistryReader = Callable[[str, str], str | None]

SDK_KEY = r"SOFTWARE\Microsoft\Microsoft SDKs\Windows\v10.0"
KITS_KEY = r"SOFTWARE\Microsoft\Windows Kits\Installed Roots"
VS7_KEY = r"SOFTWARE\Microsoft\VisualStudio\SxS\VS7"
VSWHERE_COMPONENT = "Microsoft.VisualStudio.Component.VC.Tools.x86.x64"
_VERSION_RE = re.compile(r"(\d+(?:\.\d+)+)")


@dataclass(frozen=True)
class ProbeResult:
    value: str
    detail: str = ""


def parse_version(text: str) -> str:
    """Return the first dotted numeric version from *text*, or empty."""
    match = _VERSION_RE.search(text)
    return match.group(1) if match else ""


def env_value(env: Mapping[str, str], name: str) -> str | None:
    """Read an env var case-insensitively, including dict snapshots."""
    for candidate in (name, name.upper(), name.lower()):
        value = env.get(candidate)
        if value is not None:
            return value
    target = name.upper()
    for key, value in env.items():
        if key.upper() == target:
            return value
    return None


def _read_registry(key: str, value: str) -> str | None:
    if sys.platform != "win32":
        return None
    try:
        import winreg
    except ImportError:  # pragma: no cover - Windows always has winreg
        return None
    flags = (winreg.KEY_WOW64_64KEY, winreg.KEY_WOW64_32KEY)
    for view in flags:
        try:
            with winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE, key, 0, winreg.KEY_READ | view
            ) as handle:
                result, _ = winreg.QueryValueEx(handle, value)
        except OSError:
            continue
        if isinstance(result, str) and result.strip():
            return result.strip()
    return None


@dataclass
class ProbeContext:
    """Injection points keep probes testable without touching the host."""

    env: Mapping[str, str] = field(default_factory=lambda: dict(os.environ))
    platform: str = field(default_factory=lambda: sys.platform)
    runner: Runner | None = None
    which: Callable[[str], str | None] = shutil.which
    registry: RegistryReader | None = None

    def run(self, argv: Sequence[str], timeout: float = 10.0) -> subprocess.CompletedProcess[str]:
        if self.runner is not None:
            return self.runner(argv, timeout)
        return subprocess.run(
            list(argv),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )

    def find(self, name: str) -> str | None:
        return self.which(name)

    def registry_value(self, key: str, value: str) -> str | None:
        if self.registry is not None:
            return self.registry(key, value)
        return _read_registry(key, value)


def _run_version(ctx: ProbeContext, name: str, args: Sequence[str]) -> ProbeResult:
    executable = ctx.find(name)
    if not executable:
        return ProbeResult("", f"{name} not found on PATH")
    try:
        proc = ctx.run([executable, *args])
    except FileNotFoundError:
        return ProbeResult("", f"{name} not found on PATH")
    except subprocess.TimeoutExpired:
        return ProbeResult("", f"{name} timed out")
    except OSError as exc:
        return ProbeResult("", f"{name} failed: {exc}")
    stdout = (proc.stdout or "").strip()
    if proc.returncode != 0:
        return ProbeResult("", f"{name} exited {proc.returncode}")
    version = parse_version(stdout)
    return ProbeResult(version, stdout or f"{name} returned no version")


def probe_vs_install_path(ctx: ProbeContext) -> ProbeResult:
    vswhere = ctx.find("vswhere")
    if not vswhere:
        program_files = env_value(ctx.env, "ProgramFiles(x86)") or env_value(
            ctx.env, "ProgramFiles"
        )
        if program_files:
            candidate = (
                Path(program_files) / "Microsoft Visual Studio" / "Installer" / "vswhere.exe"
            )
            if candidate.is_file():
                vswhere = str(candidate)
    if vswhere:
        args = [
            vswhere,
            "-latest",
            "-products",
            "*",
            "-requires",
            VSWHERE_COMPONENT,
            "-property",
            "installationPath",
        ]
        try:
            proc = ctx.run(args)
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError) as exc:
            detail = f"vswhere failed: {exc}"
        else:
            for line in (proc.stdout or "").splitlines():
                if line.strip():
                    return ProbeResult(line.strip(), f"vswhere: {vswhere}")
            detail = "vswhere returned no VC-tools installation"
    else:
        detail = "vswhere not found"
    fallback = (env_value(ctx.env, "VSINSTALLDIR") or "").strip()
    if fallback:
        return ProbeResult(fallback, f"{detail}; using VSINSTALLDIR")
    for version in ("17.0", "16.0", "15.0"):
        registry_path = ctx.registry_value(VS7_KEY, version)
        if registry_path:
            return ProbeResult(registry_path, f"{detail}; using VS7 registry {version}")
    return ProbeResult("", f"{detail}; no VSINSTALLDIR or VS7 fallback")


def probe_vcvarsall_path(ctx: ProbeContext) -> ProbeResult:
    vs_path = probe_vs_install_path(ctx).value
    candidates: list[Path] = []
    if vs_path:
        candidates.append(Path(vs_path) / "VC" / "Auxiliary" / "Build" / "vcvarsall.bat")
    vc_dir = (env_value(ctx.env, "VCINSTALLDIR") or "").strip()
    if vc_dir:
        candidates.append(Path(vc_dir) / "Auxiliary" / "Build" / "vcvarsall.bat")
    for candidate in candidates:
        if candidate.is_file():
            return ProbeResult(str(candidate), "exact vcvarsall.bat found")
    return ProbeResult("", "vcvarsall.bat not found under the detected VC tools")


def probe_sdk_install(ctx: ProbeContext) -> ProbeResult:
    keys = (
        (SDK_KEY, "InstallationFolder"),
        (KITS_KEY, "KitsRoot10"),
    )
    for key, value in keys:
        found = ctx.registry_value(key, value)
        if found:
            return ProbeResult(found.rstrip("\\/"), f"registry: {key}")
    sdk_env = (env_value(ctx.env, "WindowsSdkDir") or "").strip()
    if sdk_env:
        return ProbeResult(sdk_env.rstrip("\\/"), "WindowsSdkDir")
    return ProbeResult("", "Windows SDK not found in registry or WindowsSdkDir")


def probe_sdk_version(ctx: ProbeContext) -> ProbeResult:
    found = ctx.registry_value(SDK_KEY, "ProductVersion")
    if found:
        return ProbeResult(parse_version(found), "registry ProductVersion")
    sdk_root = probe_sdk_install(ctx).value
    if not sdk_root:
        return ProbeResult("", "SDK root not detected")
    bin_dir = Path(sdk_root) / "bin"
    try:
        versions = [child.name for child in bin_dir.iterdir() if child.is_dir()]
    except OSError as exc:
        return ProbeResult("", f"SDK bin directory unreadable: {exc}")
    parsed = [(parse_version(name), name) for name in versions]
    usable = [(version, name) for version, name in parsed if version]
    if not usable:
        return ProbeResult("", "no versioned directories under the SDK bin folder")
    usable.sort(key=lambda item: tuple(int(part) for part in item[0].split(".")))
    version, name = usable[-1]
    return ProbeResult(version, f"SDK bin directory: {name}")


def probe_python_version(ctx: ProbeContext) -> ProbeResult:
    return _run_version(ctx, "python", ["--version"])


def probe_node_version(ctx: ProbeContext) -> ProbeResult:
    return _run_version(ctx, "node", ["--version"])


def probe_npm_version(ctx: ProbeContext) -> ProbeResult:
    return _run_version(ctx, "npm", ["--version"])


def probe_msvs_version(ctx: ProbeContext) -> ProbeResult:
    npm = ctx.find("npm")
    if not npm:
        return ProbeResult("", "npm not found; msvs_version cannot be read")
    try:
        proc = ctx.run([npm, "config", "get", "msvs_version"])
    except subprocess.TimeoutExpired:
        return ProbeResult("unknown", "npm config timed out; msvs_version could not be checked")
    except (FileNotFoundError, OSError) as exc:
        return ProbeResult("unknown", f"npm config failed: {exc}")
    value = (proc.stdout or "").strip()
    if value in ("", "undefined", "null"):
        return ProbeResult("", "msvs_version not set; node-gyp will auto-detect")
    return ProbeResult(value, "npm config msvs_version")


def probe_sdk_env(ctx: ProbeContext) -> ProbeResult:
    value = (env_value(ctx.env, "WindowsSdkDir") or "").strip()
    if not value:
        return ProbeResult("", "WindowsSdkDir not set; registry fallback is used")
    return ProbeResult(value, "WindowsSdkDir is set; validating the path")


def probe_compile_env(ctx: ProbeContext) -> ProbeResult:
    names = ("INCLUDE", "LIB")
    configured = {name: (env_value(ctx.env, name) or "").strip() for name in names}
    if not any(configured.values()):
        return ProbeResult("unset", "INCLUDE/LIB not set; vcvarsall must be called first")
    missing = 0
    for value in configured.values():
        for part in value.split(";"):
            if part.strip() and not Path(part.strip()).exists():
                missing += 1
    if missing:
        return ProbeResult("invalid", f"INCLUDE/LIB contains {missing} missing path(s)")
    return ProbeResult("ok", "INCLUDE/LIB paths exist")


def probe_cl_path(ctx: ProbeContext) -> ProbeResult:
    found = ctx.find("cl") or ctx.find("cl.exe")
    if found:
        return ProbeResult(found, "cl.exe is on PATH")
    return ProbeResult("", "cl.exe is not on PATH; run vcvarsall first (expected)")


PROBES: dict[str, Callable[[ProbeContext], ProbeResult]] = {
    "vs_install_path": probe_vs_install_path,
    "vcvarsall_path": probe_vcvarsall_path,
    "sdk_install": probe_sdk_install,
    "sdk_version": probe_sdk_version,
    "python_version": probe_python_version,
    "node_version": probe_node_version,
    "npm_version": probe_npm_version,
    "msvs_version": probe_msvs_version,
    "sdk_env": probe_sdk_env,
    "compile_env": probe_compile_env,
    "cl_path": probe_cl_path,
}
