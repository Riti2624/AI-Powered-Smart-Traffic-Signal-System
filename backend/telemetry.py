from __future__ import annotations

import csv
import json
import threading
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, Optional

from backend.schemas import DecisionSnapshot


class TelemetryStore:
    def __init__(self, state_file: str = "backend/runtime_state.json", history_file: str = "backend/history.csv") -> None:
        self.state_path = Path(state_file)
        self.history_path = Path(history_file)
        self._lock = threading.Lock()
        self._latest: Optional[Dict[str, Any]] = None

        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.history_path.exists():
            with self.history_path.open("w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(
                    [
                        "step",
                        "timestamp",
                        "mode",
                        "total_waiting_time",
                        "baseline_waiting_time",
                        "total_queue",
                        "total_throughput",
                        "rl_gain",
                    ]
                )

    def publish(self, snapshot: DecisionSnapshot) -> None:
        data = asdict(snapshot)
        with self._lock:
            self._latest = data
            self.state_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
            rl_gain = snapshot.baseline_waiting_time - snapshot.total_waiting_time
            with self.history_path.open("a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(
                    [
                        snapshot.step,
                        snapshot.timestamp,
                        snapshot.mode,
                        snapshot.total_waiting_time,
                        snapshot.baseline_waiting_time,
                        snapshot.total_queue,
                        snapshot.total_throughput,
                        rl_gain,
                    ]
                )

    def latest(self) -> Dict[str, Any]:
        with self._lock:
            if self._latest is not None:
                return self._latest
        if self.state_path.exists():
            return json.loads(self.state_path.read_text(encoding="utf-8"))
        return {}
