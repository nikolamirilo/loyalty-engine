"""Run every regression script, each in its own process, and report the lot.

The scripts cannot share a process: each one swaps app.core.database.engine
for its own in-memory SQLite database when it is imported. So this finds
tests/regression/test_*.py, runs each as `python -m tests.regression.<name>`
from api/, and prints one line per script. A failing script's output is
printed under its line, since that is where it lists what went wrong.

Exits 1 if any script failed, so CI can use it as is.

Run: ./venv/bin/python -m tests.regression.run_all
"""

import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
API_DIR = HERE.parent.parent


def main() -> None:
    scripts = sorted(path.stem for path in HERE.glob("test_*.py"))
    # The scripts never send real mail or hit a real database, but an inherited
    # SENTRY_DSN would still report their deliberate failures to Sentry.
    env = {**os.environ, "SENTRY_DSN": ""}

    failed = []
    for name in scripts:
        started = time.monotonic()
        result = subprocess.run(
            [sys.executable, "-m", f"tests.regression.{name}"],
            cwd=API_DIR,
            env=env,
            capture_output=True,
            text=True,
        )
        seconds = time.monotonic() - started
        if result.returncode == 0:
            print(f"ok    {name}  ({seconds:.1f}s)", flush=True)
            continue
        failed.append(name)
        print(f"FAIL  {name}  ({seconds:.1f}s, exit {result.returncode})", flush=True)
        output = (result.stdout + result.stderr).rstrip()
        for line in output.splitlines():
            print(f"      {line}")
        print(flush=True)

    passed = len(scripts) - len(failed)
    if failed:
        print(f"{len(failed)} of {len(scripts)} regression scripts failed: {', '.join(failed)}")
        raise SystemExit(1)
    print(f"All {passed} regression scripts passed")


if __name__ == "__main__":
    main()
