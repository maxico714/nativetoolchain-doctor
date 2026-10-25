"""Confirm the built wheel ships the rule pack and the CLI package."""

import glob
import sys
import zipfile


def main() -> int:
    wheels = glob.glob("dist/*.whl")
    if not wheels:
        print("no wheel found in dist/", file=sys.stderr)
        return 1
    wheel = wheels[0]
    with zipfile.ZipFile(wheel) as z:
        names = z.namelist()
    missing = [
        expected
        for expected in ("rules/v1/rules.json", "nativetoolchain_doctor/cli.py")
        if not any(expected in name for name in names)
    ]
    if missing:
        print(f"wheel {wheel} is missing: {', '.join(missing)}", file=sys.stderr)
        return 1
    print(f"Wheel OK: {wheel}")
    for name in sorted(names):
        print(f"  {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
