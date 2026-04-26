from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple
from urllib.error import URLError
from urllib.request import urlopen

import streamlit as st

API_URL = "http://127.0.0.1:8000/api/latest"
FALLBACK_STATE_PATH = Path("backend/runtime_state.json")
JUNCTIONS = ["J1", "J2", "J3", "J4", "J5"]
REFRESH_MS = 1000


st.set_page_config(page_title="Smart Traffic Control Dashboard", layout="wide")

st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(180deg, #07111f 0%, #0a1628 45%, #050b14 100%);
        color: #eef4ff;
    }
    .hero {
        padding: 1.1rem 1.2rem;
        border-radius: 20px;
        border: 1px solid rgba(255,255,255,0.08);
        background: linear-gradient(135deg, rgba(15,38,68,0.96), rgba(8,18,33,0.92));
        box-shadow: 0 18px 45px rgba(0,0,0,0.28);
        margin-bottom: 1rem;
    }
    .title-row {
        display: flex;
        align-items: center;
        gap: 0.8rem;
        justify-content: space-between;
        flex-wrap: wrap;
    }
    .title-row h1 {
        margin: 0;
        font-size: 2rem;
        color: #f5fbff;
    }
    .subtitle {
        margin-top: 0.25rem;
        color: rgba(231,240,255,0.78);
        font-size: 0.98rem;
    }
    .live-pill {
        display: inline-flex;
        align-items: center;
        gap: 0.45rem;
        padding: 0.5rem 0.8rem;
        border-radius: 999px;
        background: rgba(255, 37, 37, 0.15);
        border: 1px solid rgba(255, 84, 84, 0.65);
        color: #ffd5d5;
        font-weight: 700;
        white-space: nowrap;
    }
    .live-dot {
        width: 10px;
        height: 10px;
        border-radius: 999px;
        background: #ff3b30;
        box-shadow: 0 0 0 0 rgba(255, 59, 48, 0.85);
        animation: pulse 1.3s infinite;
    }
    @keyframes pulse {
        0% { box-shadow: 0 0 0 0 rgba(255, 59, 48, 0.9); }
        70% { box-shadow: 0 0 0 12px rgba(255, 59, 48, 0.0); }
        100% { box-shadow: 0 0 0 0 rgba(255, 59, 48, 0.0); }
    }
    .status-row {
        display: flex;
        gap: 0.6rem;
        flex-wrap: wrap;
        margin-top: 0.9rem;
    }
    .status-chip {
        padding: 0.35rem 0.7rem;
        border-radius: 999px;
        border: 1px solid rgba(255,255,255,0.08);
        background: rgba(255,255,255,0.05);
        color: #eef4ff;
        font-size: 0.9rem;
    }
    .card-grid {
        display: grid;
        grid-template-columns: repeat(5, minmax(0, 1fr));
        gap: 0.75rem;
    }
    @media (max-width: 1200px) {
        .card-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    }
    @media (max-width: 640px) {
        .card-grid { grid-template-columns: 1fr; }
    }
    .traffic-card {
        border-radius: 18px;
        padding: 0.95rem 1rem;
        border: 2px solid rgba(255,255,255,0.08);
        min-height: 150px;
        box-shadow: 0 12px 28px rgba(0,0,0,0.2);
        position: relative;
        overflow: hidden;
    }
    .traffic-card h3 {
        margin: 0 0 0.5rem 0;
        font-size: 1.25rem;
        color: #fff;
    }
    .traffic-label {
        color: rgba(255,255,255,0.9);
        font-weight: 700;
    }
    .traffic-value {
        color: rgba(255,255,255,0.96);
    }
    .badge {
        display: inline-block;
        margin-top: 0.5rem;
        padding: 0.25rem 0.6rem;
        border-radius: 999px;
        font-size: 0.85rem;
        font-weight: 700;
    }
    .badge-green { background: rgba(60, 179, 113, 0.22); color: #b8ffd0; }
    .badge-red { background: rgba(255, 59, 48, 0.22); color: #ffd0d0; }
    .badge-yellow { background: rgba(255, 176, 55, 0.22); color: #ffe2a4; }
    .emergency-panel {
        padding: 1rem 1.1rem;
        border-radius: 18px;
        background: linear-gradient(135deg, rgba(120, 0, 0, 0.98), rgba(48, 0, 0, 0.95));
        border: 2px solid #ff3b30;
        color: #fff;
        margin: 1rem 0;
        box-shadow: 0 0 0 0 rgba(255, 59, 48, 0.65);
        animation: emergencyPulse 1s infinite;
    }
    @keyframes emergencyPulse {
        0% { box-shadow: 0 0 0 0 rgba(255, 59, 48, 0.7); }
        70% { box-shadow: 0 0 0 16px rgba(255, 59, 48, 0.0); }
        100% { box-shadow: 0 0 0 0 rgba(255, 59, 48, 0.0); }
    }
    .emergency-card {
        border: 4px solid #ff1f1f !important;
        box-shadow: 0 0 0 4px rgba(255, 31, 31, 0.25), 0 12px 28px rgba(0,0,0,0.22);
    }
    .debug-note {
        color: rgba(255,255,255,0.7);
        font-size: 0.92rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)
def fetch_latest_data() -> Tuple[Dict[str, Any], str, str]:
    """Always fetch a fresh payload from the backend API."""
    try:
        with urlopen(API_URL, timeout=1.5) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return payload, "OK", datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    except Exception as exc:
        if FALLBACK_STATE_PATH.exists():
            try:
                payload = json.loads(FALLBACK_STATE_PATH.read_text(encoding="utf-8"))
                return payload, "ERROR", f"API error, showing fallback file: {exc}"
            except Exception:
                pass
        return {}, "ERROR", str(exc)


def normalize_signal(value: Any) -> str:
    text = str(value or "RED").strip().upper()
    if text in {"G", "GREEN"}:
        return "GREEN"
    if text in {"Y", "YELLOW"}:
        return "YELLOW"
    return "RED"


def normalize_intersections(data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    intersections: Dict[str, Dict[str, Any]] = {}
    raw_intersections = data.get("intersections")
    state_block = data.get("state", {}) if isinstance(data.get("state"), dict) else {}
    state_intersections = state_block.get("intersections", []) if isinstance(state_block.get("intersections"), list) else []

    signal_states = data.get("signal_states", {}) if isinstance(data.get("signal_states"), dict) else {}

    def upsert(intersection_id: str, source: Dict[str, Any]) -> None:
        lanes = source.get("lanes", []) if isinstance(source.get("lanes"), list) else []
        queue_length = source.get("queue_length")
        if queue_length is None and lanes:
            queue_length = sum(float(l.get("queue_length", 0.0)) for l in lanes if isinstance(l, dict))
        vehicle_count = source.get("vehicle_count")
        if vehicle_count is None and lanes:
            vehicle_count = sum(float(l.get("queue_length", 0.0)) for l in lanes if isinstance(l, dict))
        signal = source.get("signal") or source.get("signal_state") or signal_states.get(intersection_id)
        emergency_count = int(source.get("emergency_vehicle_count", 0) or 0)
        emergency_lanes = source.get("emergency_lane_ids", [])
        intersections[intersection_id] = {
            "signal": normalize_signal(signal),
            "vehicle_count": int(round(float(vehicle_count or 0))),
            "queue_length": int(round(float(queue_length or 0))),
            "emergency_vehicle_count": emergency_count,
            "emergency_lane_ids": emergency_lanes if isinstance(emergency_lanes, list) else [],
            "lanes": lanes,
        }

    if isinstance(raw_intersections, dict):
        for jid in JUNCTIONS:
            upsert(jid, dict(raw_intersections.get(jid, {})))
    elif isinstance(raw_intersections, list):
        for item in raw_intersections:
            if isinstance(item, dict):
                jid = str(item.get("intersection_id") or item.get("junction_id") or item.get("id") or "")
                if jid:
                    upsert(jid, item)

    # Fallback to the nested current snapshot format.
    if not intersections and state_intersections:
        for item in state_intersections:
            if isinstance(item, dict):
                jid = str(item.get("intersection_id") or item.get("junction_id") or item.get("id") or "")
                if jid:
                    upsert(jid, item)

    # Ensure all 5 cards exist.
    for jid in JUNCTIONS:
        intersections.setdefault(
            jid,
            {
                "signal": normalize_signal(signal_states.get(jid, "RED")),
                "vehicle_count": 0,
                "queue_length": 0,
                "emergency_vehicle_count": 0,
                "emergency_lane_ids": [],
                "lanes": [],
            },
        )

    return intersections


def render_emergency_panel(data: Dict[str, Any], intersections: Dict[str, Dict[str, Any]]) -> None:
    emergency_items: List[Tuple[str, Dict[str, Any]]] = [
        (jid, info)
        for jid, info in intersections.items()
        if int(info.get("emergency_vehicle_count", 0) or 0) > 0
    ]

    if not emergency_items:
        return

    jid, info = emergency_items[0]
    st.markdown(
        f"""
        <div class="emergency-panel">
            <h2 style="margin:0 0 0.3rem 0;">🚨 EMERGENCY VEHICLE DETECTED</h2>
            <div><b>Priority junction:</b> {jid}</div>
            <div><b>Emergency vehicle count:</b> {int(info.get('emergency_vehicle_count', 0))}</div>
            <div><b>Affected lanes:</b> {', '.join(info.get('emergency_lane_ids', [])) or 'N/A'}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_intersection_card(junction_id: str, data: Dict[str, Dict[str, Any]], emergency_junction: Optional[str]) -> None:
    info = data.get(junction_id, {})
    signal = normalize_signal(info.get("signal"))
    vehicle_count = int(info.get("vehicle_count", 0) or 0)
    queue_length = int(info.get("queue_length", 0) or 0)
    emergency_count = int(info.get("emergency_vehicle_count", 0) or 0)
    emergency = junction_id == emergency_junction and emergency_count > 0

    if signal == "GREEN":
        background = "linear-gradient(135deg, rgba(20,90,40,0.96), rgba(10,40,20,0.96))"
        chip_class = "badge-green"
    elif signal == "YELLOW":
        background = "linear-gradient(135deg, rgba(124,92,8,0.96), rgba(60,40,5,0.96))"
        chip_class = "badge-yellow"
    else:
        background = "linear-gradient(135deg, rgba(110,20,20,0.96), rgba(55,10,10,0.96))"
        chip_class = "badge-red"

    extra_class = " emergency-card" if emergency else ""
    st.markdown(
        f"""
        <div class="traffic-card{extra_class}" style="background:{background};">
            <h3>{junction_id}</h3>
            <div class="traffic-label">Signal</div>
            <div class="traffic-value">{signal}</div>
            <div style="height:0.5rem;"></div>
            <div class="traffic-label">Vehicles</div>
            <div class="traffic-value">{vehicle_count}</div>
            <div style="height:0.5rem;"></div>
            <div class="traffic-label">Queue Length</div>
            <div class="traffic-value">{queue_length}</div>
            <div style="height:0.75rem;"></div>
            <span class="badge {chip_class}">{signal}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


try:
    from streamlit_autorefresh import st_autorefresh  # type: ignore

    st_autorefresh(interval=REFRESH_MS, key="smart_traffic_live_refresh")
    refresh_mode = "autorefresh"
except Exception:
    refresh_mode = "rerun"

latest_data, api_status, status_detail = fetch_latest_data()
intersections = normalize_intersections(latest_data) if latest_data else {jid: {"signal": "RED", "vehicle_count": 0, "queue_length": 0, "emergency_vehicle_count": 0, "emergency_lane_ids": [], "lanes": []} for jid in JUNCTIONS}

emergency_junction: Optional[str] = None
for jid, info in intersections.items():
    if int(info.get("emergency_vehicle_count", 0) or 0) > 0:
        emergency_junction = jid
        break

st.markdown(
    f"""
    <div class="hero">
        <div class="title-row">
            <div>
                <h1>🚦 Smart Traffic Control System</h1>
                <div class="subtitle">Live RL + SUMO Traffic Simulation</div>
            </div>
            <div class="live-pill"><span class="live-dot"></span>LIVE (updates every 1 second)</div>
        </div>
        <div class="status-row">
            <span class="status-chip">API Status: {api_status}</span>
            <span class="status-chip">Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</span>
            <span class="status-chip">Refresh: {refresh_mode}</span>
            <span class="status-chip">Endpoint: /api/latest</span>
        </div>
        <div class="debug-note" style="margin-top:0.6rem;">{status_detail}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

render_emergency_panel(latest_data, intersections)

st.subheader("Intersection Status")
card_columns = st.columns(5)
for index, junction_id in enumerate(JUNCTIONS):
    with card_columns[index]:
        render_intersection_card(junction_id, intersections, emergency_junction)

st.subheader("Live Summary")
summary_columns = st.columns(4)
summary_columns[0].metric("Active Joints", len(JUNCTIONS))
summary_columns[1].metric("Emergency Count", sum(int(v.get("emergency_vehicle_count", 0) or 0) for v in intersections.values()))
summary_columns[2].metric("Total Vehicles", sum(int(v.get("vehicle_count", 0) or 0) for v in intersections.values()))
summary_columns[3].metric("Total Queue", sum(int(v.get("queue_length", 0) or 0) for v in intersections.values()))

st.subheader("Debug Data")
with st.expander("Debug Data", expanded=False):
    st.json(latest_data)

# Auto-refresh control.
if refresh_mode == "rerun":
    time.sleep(1)
    st.rerun()
