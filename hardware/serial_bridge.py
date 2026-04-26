from __future__ import annotations

import logging
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

if not logging.getLogger().handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

if __package__ is None or __package__ == "":
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from backend.schemas import CorridorState, SignalAction


class HardwareSignalBridge:
    """Serial bridge with reconnect and non-blocking writes for live LED control."""

    def __init__(self, serial_port: Optional[str] = None, baud_rate: int = 115200) -> None:
        self._logger = logging.getLogger(__name__)
        self.serial_port = serial_port
        self.baud_rate = baud_rate
        self.available = False
        self._serial = None
        self._serial_module = None
        self._last_connect_attempt = 0.0
        self._reconnect_interval_sec = 2.0

        self._logger.info("STARTUP LOGS: Module started")
        self._logger.info("STARTUP LOGS: Model loaded = N/A (serial bridge)")

        self._connect()
        self._logger.info(
            "STARTUP LOGS: Connection status (SUMO / SERIAL) = SUMO:N/A SERIAL:%s",
            "connected" if self.available else "offline",
        )

    def _connect(self) -> None:
        if not self.serial_port:
            self.available = False
            return

        self._last_connect_attempt = time.time()
        try:
            import serial  # type: ignore

            self._serial_module = serial
            self._serial = serial.Serial(
                self.serial_port,
                self.baud_rate,
                timeout=0,
                write_timeout=0,
            )
            self.available = True
            self._logger.info("Connection status (SUMO / SERIAL) = SUMO:N/A SERIAL:connected")
        except Exception as exc:
            self._serial = None
            self.available = False
            self._logger.warning("SERIAL connect failed on %s: %s", self.serial_port, exc)

    def _ensure_connection(self) -> None:
        if self.available and self._serial is not None:
            return

        if not self.serial_port:
            return

        if time.time() - self._last_connect_attempt >= self._reconnect_interval_sec:
            self._connect()

    @staticmethod
    def _serialize_signal_states(signal_states: Dict[str, str], actions: List[SignalAction]) -> str:
        ordered = [a.intersection_id for a in actions]
        if not ordered:
            ordered = sorted(signal_states.keys())

        priority_yellow = [iid for iid in ordered if signal_states.get(iid) == "Y"]
        priority_green = [iid for iid in ordered if signal_states.get(iid) == "G"]
        if priority_yellow:
            ordered = priority_yellow + [iid for iid in ordered if iid not in priority_yellow]
        elif priority_green:
            ordered = priority_green + [iid for iid in ordered if iid not in priority_green]

        parts: List[str] = []
        for iid in ordered:
            state = signal_states.get(iid, "R")
            led = state if state in {"G", "Y", "R"} else "R"
            parts.append(f"{iid}:{led}")
        return ",".join(parts)

    def send_actions(
        self,
        actions: List[SignalAction],
        state: CorridorState,
        signal_states: Optional[Dict[str, str]] = None,
    ) -> None:
        self._ensure_connection()

        fallback_signal_states = {
            a.intersection_id: ("G" if a.switch_phase else "R") for a in actions
        }
        resolved_signal_states = signal_states or fallback_signal_states

        payload = self._serialize_signal_states(resolved_signal_states, actions)
        self._logger.info("Hardware TX step=%s payload=%s", state.step, payload)

        if not self.available or self._serial is None:
            return

        try:
            self._serial.write((payload + "\n").encode("utf-8"))
            ack = b""
            if hasattr(self._serial, "in_waiting") and self._serial.in_waiting:
                ack = self._serial.readline().strip()
            if ack:
                self._logger.info("Hardware ACK: %s", ack.decode("utf-8", errors="ignore"))
        except Exception as exc:
            self.available = False
            self._logger.warning("SERIAL write failed, scheduling reconnect: %s", exc)

    def close(self) -> None:
        if self._serial is not None:
            try:
                self._serial.close()
            except Exception:
                pass
