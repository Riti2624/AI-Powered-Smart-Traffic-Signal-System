"""Compatibility entrypoint.

This project is now orchestrated by `main.py` (master controller) and
`dashboard/app.py` (Streamlit live UI).
"""

import subprocess
import sys
import os
import logging
from pathlib import Path


def main() -> int:
    expected_root = Path(__file__).resolve().parent
    if Path.cwd().resolve() != expected_root:
        os.chdir(expected_root)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    logging.getLogger(__name__).info("RUN RULE: running from %s", Path.cwd())

    cmd = [sys.executable, "-m", "streamlit", "run", "dashboard/app.py"]
    return subprocess.call(cmd)


if __name__ == "__main__":
    raise SystemExit(main())