from __future__ import annotations

import os
import random
import time
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

if not logging.getLogger().handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

from backend.schemas import CorridorState, IntersectionState, LaneState, SignalAction


@dataclass
class SimulationConfig:
    sumo_cfg: str = "simulation/sumo/corridor.sumocfg"
    intersection_ids: List[str] = None

    def __post_init__(self) -> None:
        if self.intersection_ids is None:
            self.intersection_ids = [f"J{i}" for i in range(1, 6)]


class SumoCorridorEnvironment:
    """Unified adapter: uses TraCI when available, otherwise a realistic stochastic corridor mock."""

    def __init__(self, config: SimulationConfig) -> None:
        self._logger = logging.getLogger(__name__)
        self.config = config
        self.step_count = 0
        self._rng = random.Random(42)
        self._traci = None
        self._mode = "mock"
        self._phase_index = {iid: 0 for iid in self.config.intersection_ids}
        self._green_duration = {iid: 20 for iid in self.config.intersection_ids}
        self._last_emergency_map: Dict[str, Dict[str, object]] = {}
        self._mock_state = self._init_mock_state()
        self._logger.info("STARTUP LOGS: Module started")
        self._logger.info("STARTUP LOGS: Model loaded = N/A (SUMO adapter)")
        self._logger.info("STARTUP LOGS: Connection status (SUMO / SERIAL) = SUMO:pending SERIAL:N/A")

    @property
    def mode(self) -> str:
        return self._mode

    def start(self) -> None:
        sumo_home = os.getenv("SUMO_HOME")
        cfg_path = Path(self.config.sumo_cfg)
        if not sumo_home or not cfg_path.exists():
            self._mode = "mock"
            self._logger.warning(
                "FAIL SAFE: SUMO not running/available. Switching to offline simulation mode. "
                "Connection status (SUMO / SERIAL) = SUMO:offline SERIAL:N/A"
            )
            return

        try:
            import traci  # type: ignore
            from sumolib import checkBinary  # type: ignore

            binary = checkBinary("sumo")
            traci.start([binary, "-c", str(cfg_path), "--start", "--quit-on-end"])
            self._traci = traci
            self._mode = "sumo"
            self._logger.info("STARTUP LOGS: Connection status (SUMO / SERIAL) = SUMO:connected SERIAL:N/A")
        except Exception:
            self._traci = None
            self._mode = "mock"
            self._logger.warning(
                "FAIL SAFE: SUMO startup failed. Switching to offline simulation mode. "
                "Connection status (SUMO / SERIAL) = SUMO:offline SERIAL:N/A"
            )

    def close(self) -> None:
        if self._traci is not None:
            try:
                self._traci.close()
            except Exception:
                pass

    def step(self) -> None:
        if self._mode == "sumo" and self._traci is not None:
            self._traci.simulationStep()
        else:
            self._mock_step()
        self.step_count += 1

    def get_state(self) -> CorridorState:
        if self._mode == "sumo" and self._traci is not None:
            intersections = self._collect_sumo_state()
        else:
            self._last_emergency_map = {}
            intersections = self._collect_mock_state()
        return CorridorState(timestamp=time.time(), step=self.step_count, intersections=intersections)

    def apply_signal_plan(self, actions: List[SignalAction]) -> None:
        for action in actions:
            iid = action.intersection_id
            self._green_duration[iid] = int(max(8, min(60, self._green_duration[iid] + action.green_delta_sec)))
            if action.switch_phase:
                self._phase_index[iid] = (self._phase_index[iid] + 1) % 2

            if self._mode == "sumo" and self._traci is not None:
                try:
                    if iid in self._traci.trafficlight.getIDList():
                        self._traci.trafficlight.setPhase(iid, self._phase_index[iid])
                        self._traci.trafficlight.setPhaseDuration(iid, self._green_duration[iid])
                except Exception:
                    continue

    def get_signal_states(self) -> Dict[str, str]:
        states: Dict[str, str] = {}
        for iid in self.config.intersection_ids:
            phase = self._phase_index.get(iid, 0)
            states[iid] = "G" if phase == 0 else "R"
        return states

    def get_emergency_map(self) -> Dict[str, Dict[str, object]]:
        return self._last_emergency_map

    def _init_mock_state(self) -> Dict[str, Dict[str, Dict[str, float]]]:
        state: Dict[str, Dict[str, Dict[str, float]]] = {}
        for iid in self.config.intersection_ids:
            state[iid] = {}
            for lane in ["N_S", "S_N", "E_W", "W_E"]:
                state[iid][lane] = {
                    "queue": self._rng.randint(3, 10),
                    "density": self._rng.uniform(0.2, 0.7),
                    "wait": self._rng.uniform(5, 25),
                }
        return state

    def _mock_step(self) -> None:
        for iid in self.config.intersection_ids:
            phase = self._phase_index[iid]
            is_ns_green = phase == 0
            for lane, lane_state in self._mock_state[iid].items():
                demand = self._rng.uniform(0.0, 2.5)
                discharge = self._rng.uniform(0.0, 3.5)

                if (is_ns_green and lane in {"N_S", "S_N"}) or (not is_ns_green and lane in {"E_W", "W_E"}):
                    lane_state["queue"] = max(0.0, lane_state["queue"] + demand - discharge)
                    lane_state["wait"] = max(0.0, lane_state["wait"] * 0.85 + lane_state["queue"] * 0.3)
                else:
                    lane_state["queue"] = max(0.0, lane_state["queue"] + demand * 1.2)
                    lane_state["wait"] = min(160.0, lane_state["wait"] + lane_state["queue"] * 0.45)

                lane_state["density"] = min(1.0, max(0.0, lane_state["queue"] / 20.0 + self._rng.uniform(0, 0.1)))

    def _collect_mock_state(self) -> List[IntersectionState]:
        intersections: List[IntersectionState] = []
        for iid in self.config.intersection_ids:
            lanes: List[LaneState] = []
            throughput = 0.0
            for lane, lane_state in self._mock_state[iid].items():
                lanes.append(
                    LaneState(
                        lane_id=f"{iid}_{lane}",
                        queue_length=round(float(lane_state["queue"]), 2),
                        density=round(float(lane_state["density"]), 3),
                        waiting_time=round(float(lane_state["wait"]), 2),
                    )
                )
                throughput += max(0.0, 12.0 - lane_state["queue"]) / 12.0

            intersections.append(
                IntersectionState(
                    intersection_id=iid,
                    lanes=lanes,
                    throughput=round(throughput, 3),
                )
            )
        return intersections

    def _collect_sumo_state(self) -> List[IntersectionState]:
        assert self._traci is not None
        intersections: List[IntersectionState] = []
        tls_ids = list(self._traci.trafficlight.getIDList())
        emergency_types = {"ambulance", "emergency", "police", "firebrigade", "rescue"}
        emergency_classes = {"emergency", "authority"}
        emergency_map: Dict[str, Dict[str, object]] = {}

        for iid in self.config.intersection_ids:
            if iid in tls_ids:
                controlled = self._traci.trafficlight.getControlledLanes(iid)
            else:
                controlled = []

            lanes: List[LaneState] = []
            throughput = 0.0
            emergency_lane_ids: List[str] = []
            emergency_count = 0
            emergency_target_phase = None
            for lane in sorted(set(controlled)):
                halting = float(self._traci.lane.getLastStepHaltingNumber(lane))
                veh_count = float(self._traci.lane.getLastStepVehicleNumber(lane))
                max_speed = max(0.1, float(self._traci.lane.getMaxSpeed(lane)))
                speed = float(self._traci.lane.getLastStepMeanSpeed(lane))
                wait = float(self._traci.lane.getWaitingTime(lane))
                veh_ids = list(self._traci.lane.getLastStepVehicleIDs(lane))

                density = min(1.0, veh_count / 20.0)
                throughput += speed / max_speed

                for veh_id in veh_ids:
                    try:
                        veh_type = str(self._traci.vehicle.getTypeID(veh_id)).lower()
                        veh_class = str(self._traci.vehicle.getVehicleClass(veh_id)).lower()
                    except Exception:
                        continue

                    if veh_type in emergency_types or veh_class in emergency_classes:
                        emergency_count += 1
                        if lane not in emergency_lane_ids:
                            emergency_lane_ids.append(lane)
                        if emergency_target_phase is None:
                            emergency_target_phase = 2 if ("n" in lane.lower() or "s" in lane.lower()) else 0

                lanes.append(
                    LaneState(
                        lane_id=lane,
                        queue_length=halting,
                        density=density,
                        waiting_time=wait,
                    )
                )

            if emergency_count:
                emergency_map[iid] = {
                    "count": emergency_count,
                    "lane_ids": emergency_lane_ids,
                    "target_phase": emergency_target_phase if emergency_target_phase is not None else 0,
                }

            intersections.append(
                IntersectionState(intersection_id=iid, lanes=lanes, throughput=throughput)
            )

        self._last_emergency_map = emergency_map
        return intersections
