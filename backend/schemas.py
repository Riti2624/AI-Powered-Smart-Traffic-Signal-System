from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from typing import Dict, List


@dataclass
class LaneState:
    lane_id: str
    queue_length: float
    density: float
    waiting_time: float


@dataclass
class IntersectionState:
    intersection_id: str
    lanes: List[LaneState]
    throughput: float
    emergency_vehicle_count: int = 0
    emergency_lane_ids: List[str] = field(default_factory=list)


@dataclass
class CorridorState:
    timestamp: float
    step: int
    intersections: List[IntersectionState]


@dataclass
class SignalAction:
    intersection_id: str
    green_delta_sec: int
    switch_phase: bool


@dataclass
class DecisionSnapshot:
    timestamp: float
    step: int
    mode: str
    total_waiting_time: float
    baseline_waiting_time: float
    total_queue: float
    total_throughput: float
    actions: List[SignalAction]
    signal_states: Dict[str, str]
    state: CorridorState
