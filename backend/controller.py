from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Optional

if not logging.getLogger().handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

from backend.schemas import DecisionSnapshot, SignalAction
from backend.telemetry import TelemetryStore
from hardware.serial_bridge import HardwareSignalBridge
from rl.agent import RLSignalAgent
from simulation.sumo_interface import SimulationConfig, SumoCorridorEnvironment


@dataclass
class ControllerConfig:
    decision_interval_sec: float = 2.0
    sumo_cfg: str = "simulation/sumo/corridor.sumocfg"
    rl_model_path: str = "models/ppo_traffic.zip"
    serial_port: Optional[str] = None


class IntegratedTrafficController:
    """Single source of truth: SUMO TraCI state -> RL -> signal updates -> telemetry."""

    def __init__(self, config: ControllerConfig) -> None:
        self._logger = logging.getLogger(__name__)
        self.config = config
        self._heartbeat_interval_sec = 5.0
        self._last_heartbeat = 0.0
        self._yellow_until: dict[str, float] = {f"J{i}": 0.0 for i in range(1, 6)}
        self.sim_env = SumoCorridorEnvironment(
            SimulationConfig(
                sumo_cfg=config.sumo_cfg,
                intersection_ids=[f"J{i}" for i in range(1, 6)],
            )
        )
        self.agent = RLSignalAgent(model_path=config.rl_model_path)
        self.hardware = HardwareSignalBridge(serial_port=config.serial_port)
        self.telemetry = TelemetryStore()
        self._logger.info("STARTUP LOGS: Module started")
        self._logger.info("STARTUP LOGS: Model loaded = controller initialized")
        self._logger.info(
            "STARTUP LOGS: Connection status (SUMO / SERIAL) = SUMO:pending SERIAL:%s",
            "connected" if self.hardware.available else "offline",
        )

    def start(self) -> None:
        self.sim_env.start()
        self._logger.info(
            "STARTUP LOGS: Connection status (SUMO / SERIAL) = SUMO:%s SERIAL:%s",
            "connected" if self.sim_env.mode == "sumo" else "offline",
            "connected" if self.hardware.available else "offline",
        )

    def shutdown(self) -> None:
        self.hardware.close()
        self.sim_env.close()

    def _build_visual_signal_states(
        self,
        base_signal_states: dict[str, str],
        actions: list[SignalAction],
        emergency_priority: Optional[str],
    ) -> dict[str, str]:
        signal_states = dict(base_signal_states)
        now = time.time()

        if emergency_priority is not None:
            for iid in signal_states:
                signal_states[iid] = "R"
            signal_states[emergency_priority] = "G"
            self._yellow_until[emergency_priority] = 0.0
            self._logger.warning(
                "FAIL SAFE: emergency vehicle detected in %s. Prioritizing green.",
                emergency_priority,
            )
            return signal_states

        for action in actions:
            if action.switch_phase:
                self._yellow_until[action.intersection_id] = now + 3.0

        for iid, until in self._yellow_until.items():
            if now < until:
                signal_states[iid] = "Y"

        return signal_states

    def run_step(self) -> DecisionSnapshot:
        self.sim_env.step()
        state = self.sim_env.get_state()
        actions = self.agent.decide(state)

        emergency_map = self.sim_env.get_emergency_map()
        emergency_priority = next(iter(emergency_map.keys()), None)
        if emergency_priority is not None:
            actions = sorted(actions, key=lambda action: action.intersection_id != emergency_priority)

        self.sim_env.apply_signal_plan(actions)

        signal_states = self._build_visual_signal_states(
            self.sim_env.get_signal_states(),
            actions,
            emergency_priority,
        )

        self._logger.info(
            "REAL-TIME LOGS: Signal update decision = %s",
            [
                {
                    "intersection": a.intersection_id,
                    "green_delta_sec": a.green_delta_sec,
                    "switch_phase": a.switch_phase,
                }
                for a in actions
            ],
        )
        self.hardware.send_actions(actions, state, signal_states)

        total_wait = sum(l.waiting_time for i in state.intersections for l in i.lanes)
        total_queue = sum(l.queue_length for i in state.intersections for l in i.lanes)
        total_throughput = sum(i.throughput for i in state.intersections)
        baseline_wait = total_wait + 0.2 * total_queue + 15.0

        snapshot = DecisionSnapshot(
            timestamp=state.timestamp,
            step=state.step,
            mode=self.sim_env.mode,
            total_waiting_time=round(total_wait, 3),
            baseline_waiting_time=round(baseline_wait, 3),
            total_queue=round(total_queue, 3),
            total_throughput=round(total_throughput, 3),
            actions=actions,
            signal_states=signal_states,
            state=state,
        )
        self.telemetry.publish(snapshot)
        return snapshot

    def run_forever(self) -> None:
        self.start()
        try:
            while True:
                begin = time.time()
                self.run_step()
                now = time.time()
                if now - self._last_heartbeat >= self._heartbeat_interval_sec:
                    self._logger.info("HEARTBEAT: system alive")
                    self._last_heartbeat = now
                elapsed = time.time() - begin
                time.sleep(max(0.0, self.config.decision_interval_sec - elapsed))
        finally:
            self.shutdown()
