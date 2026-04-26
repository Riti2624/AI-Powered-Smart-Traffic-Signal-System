from __future__ import annotations

import logging
from pathlib import Path
from typing import List

if not logging.getLogger().handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

import numpy as np

from backend.schemas import CorridorState, SignalAction


class RLSignalAgent:
    """Loads PPO policy when available; otherwise applies deterministic adaptive heuristic."""

    def __init__(self, model_path: str = "models/ppo_traffic.zip") -> None:
        self._logger = logging.getLogger(__name__)
        self.model_path = Path(model_path)
        self.available = False
        self._model = None
        self._logger.info("STARTUP LOGS: Module started")

        try:
            from stable_baselines3 import PPO  # type: ignore

            if self.model_path.exists():
                self._model = PPO.load(str(self.model_path))
                self.available = True
        except Exception:
            self.available = False

        self._logger.info("STARTUP LOGS: Model loaded = %s", "yes" if self.available else "no")
        self._logger.info("STARTUP LOGS: Connection status (SUMO / SERIAL) = SUMO:N/A SERIAL:N/A")

    def decide(self, state: CorridorState) -> List[SignalAction]:
        if self.available:
            return self._decide_from_model(state)
        self._logger.warning("FAIL SAFE: RL model not loaded. Falling back to rule-based logic.")
        return self._heuristic_decide(state)

    def _decide_from_model(self, state: CorridorState) -> List[SignalAction]:
        obs = self._flatten_state(state)
        self._logger.info("REAL-TIME LOGS: RL state vector = %s", obs.tolist())
        actions, _ = self._model.predict(obs, deterministic=True)
        decoded = [
            SignalAction(
                intersection_id=f"J{idx + 1}",
                green_delta_sec=self.decode_action(int(a))[0],
                switch_phase=self.decode_action(int(a))[1],
            )
            for idx, a in enumerate(actions)
        ]
        self._logger.info(
            "REAL-TIME LOGS: RL action chosen = %s",
            [
                {
                    "intersection": a.intersection_id,
                    "green_delta_sec": a.green_delta_sec,
                    "switch_phase": a.switch_phase,
                }
                for a in decoded
            ],
        )
        return decoded

    def _heuristic_decide(self, state: CorridorState) -> List[SignalAction]:
        obs = self._flatten_state(state)
        self._logger.info("REAL-TIME LOGS: RL state vector = %s", obs.tolist())
        actions: List[SignalAction] = []
        for inter in state.intersections:
            ns_queue = sum(l.queue_length for l in inter.lanes if "N_S" in l.lane_id or "S_N" in l.lane_id)
            ew_queue = sum(l.queue_length for l in inter.lanes if "E_W" in l.lane_id or "W_E" in l.lane_id)
            wait = sum(l.waiting_time for l in inter.lanes)

            if wait > 180 or abs(ns_queue - ew_queue) > 6:
                switch = True
            else:
                switch = False

            if max(ns_queue, ew_queue) > 14:
                delta = 4
            elif max(ns_queue, ew_queue) < 5:
                delta = -2
            else:
                delta = 0

            actions.append(
                SignalAction(
                    intersection_id=inter.intersection_id,
                    green_delta_sec=delta,
                    switch_phase=switch,
                )
            )
        self._logger.info(
            "REAL-TIME LOGS: RL action chosen = %s",
            [
                {
                    "intersection": a.intersection_id,
                    "green_delta_sec": a.green_delta_sec,
                    "switch_phase": a.switch_phase,
                }
                for a in actions
            ],
        )
        return actions

    @staticmethod
    def decode_action(action_id: int):
        table = {
            0: (-4, False),
            1: (0, False),
            2: (4, False),
            3: (-4, True),
            4: (0, True),
            5: (4, True),
        }
        return table[action_id]

    @staticmethod
    def _flatten_state(state: CorridorState) -> np.ndarray:
        vec = []
        for inter in state.intersections:
            lanes = inter.lanes[:4]
            if len(lanes) < 4:
                deficit = 4 - len(lanes)
                for _ in range(deficit):
                    vec.extend([0.0, 0.0, 0.0])
            for lane in lanes:
                vec.extend([lane.queue_length, lane.density * 100.0, lane.waiting_time])
        return np.asarray(vec, dtype=np.float32)
