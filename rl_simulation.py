"""Backward-compatible launcher for PPO training.

Use:
    python -m rl.train --timesteps 50000 --intersections 5 --output models/ppo_traffic.zip
"""

import subprocess
import sys
import os
import logging
from pathlib import Path


if __name__ == "__main__":
    expected_root = Path(__file__).resolve().parent
    if Path.cwd().resolve() != expected_root:
        os.chdir(expected_root)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    logging.getLogger(__name__).info("RUN RULE: running from %s", Path.cwd())

    cmd = [sys.executable, "-m", "rl.train", "--timesteps", "50000", "--intersections", "5"]
    raise SystemExit(subprocess.call(cmd))