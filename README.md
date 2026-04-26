# Reinforcement Learning Adaptive Traffic Control (5-Intersection Corridor)

Fully integrated hackathon system with one master loop:

SUMO TraCI -> State Generator -> RL Agent -> Signal Controller -> Hardware + Dashboard

## Hackathon Winning Project

This project is the hackathon-winning implementation for an AI-powered smart traffic signal system.

Team Lead:
- Ritika S

PPT and presentation contribution:
- Nithaester Ruby Joy S

## Project Structure

- `simulation/`: SUMO configuration and TraCI simulation adapter
- `rl/`: PPO training environment and inference agent
- `hardware/`: Arduino/ESP32 serial bridge + sample sketch
- `backend/`: integrated controller, telemetry, and REST API
- `dashboard/`: Streamlit real-time visualization
- `models/`: trained RL weights (`ppo_traffic.zip`)
- `main.py`: master controller (single integrated entry point)

## 1. Setup

1. Install Python 3.10+.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Optional (SUMO mode): install SUMO and set `SUMO_HOME` environment variable.
4. Optional (hardware mode): connect Arduino/ESP32 and note COM port.

## 2. SUMO Network Build (one time)

From `simulation/sumo/`:

```bash
generate_network.bat
```

This creates `corridor.net.xml` from `corridor.nod.xml` and `corridor.edg.xml`.

## 3. Train RL Model (PPO)

```bash
python -m rl.train --timesteps 50000 --intersections 5 --output models/ppo_traffic.zip
```

If model is missing, the system uses a deterministic adaptive heuristic fallback.

## 4. Run Integrated Controller

Basic run (headless SUMO only):

```bash
python main.py --interval 2 --serve-api
```

With hardware serial output:

```bash
python main.py --serial-port COM5 --interval 2 --serve-api
```

## 5. Launch Dashboard

In another terminal:

```bash
streamlit run dashboard/app.py
```

Dashboard shows:
- live waiting/queue/throughput
- RL action decisions per intersection
- per-intersection TraCI lane state and signal status
- before vs after RL comparison

## 6. Integration Notes

- `main.py` is the single orchestrator and keeps module communication unified.
- Loop timing is controlled by `--interval`.
- Fallbacks:
  - No SUMO/traci -> realistic mock corridor simulator
  - No serial hardware -> no-op hardware bridge

## 7. API Endpoints

When `--serve-api` is enabled:
- `GET /api/health`
- `GET /api/latest`

## 8. Demo Checklist

1. Start `main.py`.
2. Start Streamlit dashboard.
3. Show evolving queue and waiting metrics.
4. Show RL actions changing by intersection.
5. (Optional) show hardware LED ACK on serial monitor.
6. Compare `baseline_waiting_time` vs `total_waiting_time`.
