from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.live
@pytest.mark.skipif(sys.platform != "win32", reason="Windows toolchain only")
def test_host_live_run() -> None:
    root = Path(__file__).parents[2]
    env = dict(os.environ)
    env["PYTHONPATH"] = str(root / "src")
    proc = subprocess.run(
        [sys.executable, "-m", "nativetoolchain_doctor", "run", "--json"],
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["summary"]["pass"] == 11
    assert payload["summary"]["error"] == 0
