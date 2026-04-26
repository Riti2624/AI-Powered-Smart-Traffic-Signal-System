from __future__ import annotations

import gymnasium as gym
import numpy as np
from gymnasium import spaces

from simulation.sumo_interface import SimulationConfig, SumoCorridorEnvironment


class CorridorSignalEnv(gym.Env):
    """Gymnasium wrapper for RL training on the corridor signal control problem."""

    metadata = {"render_modes": []}

    def __init__(self, intersections: int = 5, max_steps: int = 300) -> None:
        super().__init__()
        self.intersections = intersections
        self.max_steps = max_steps

        self.env = SumoCorridorEnvironment(
            SimulationConfig(intersection_ids=[f"J{i}" for i in range(1, intersections + 1)])
        )
        self.env.start()
        self.step_count = 0

        # For each intersection: 6 actions encoding (green_delta, switch_phase)
        self.action_space = spaces.MultiDiscrete([6] * intersections)
        # For each lane: queue, density, waiting. 4 lanes per intersection.
        self.observation_space = spaces.Box(
            low=0.0,
            high=200.0,
            shape=(intersections * 4 * 3,),
            dtype=np.float32,
        )

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.env.close()
        self.env = SumoCorridorEnvironment(
            SimulationConfig(intersection_ids=[f"J{i}" for i in range(1, self.intersections + 1)])
        )
        self.env.start()
        self.step_count = 0
        state = self.env.get_state()
        return self._flatten_state(state), {}

    def step(self, action):
        actions = []
        for idx, a in enumerate(action):
            delta, switch = self.decode_action(int(a))
            actions.append(
                {
                    "intersection_id": f"J{idx + 1}",
                    "green_delta_sec": delta,
                    "switch_phase": switch,
                }
            )

        from backend.schemas import SignalAction

        self.env.apply_signal_plan([SignalAction(**a) for a in actions])
        self.env.step()
        state = self.env.get_state()
        obs = self._flatten_state(state)

        total_wait = sum(l.waiting_time for i in state.intersections for l in i.lanes)
        total_queue = sum(l.queue_length for i in state.intersections for l in i.lanes)
        total_throughput = sum(i.throughput for i in state.intersections)

        reward = -(0.6 * total_wait + 0.3 * total_queue) + 0.4 * total_throughput
        self.step_count += 1
        terminated = self.step_count >= self.max_steps
        truncated = False
        info = {
            "total_wait": total_wait,
            "total_queue": total_queue,
            "throughput": total_throughput,
        }
        return obs, float(reward), terminated, truncated, info

    def close(self):
        self.env.close()

    @staticmethod
    def decode_action(action_id: int):
        # 0..5 -> (-4,False), (0,False), (+4,False), (-4,True), (0,True), (+4,True)
        table = {
            0: (-4, False),
            1: (0, False),
            2: (4, False),
            3: (-4, True),
            4: (0, True),
            5: (4, True),
        }
        return table[action_id]

    def _flatten_state(self, state):
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
