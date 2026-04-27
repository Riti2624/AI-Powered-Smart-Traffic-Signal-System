
# 🚦 AI-Powered Adaptive Traffic Signal System
 Reinforcement Learning for Smart Chennai Traffic Control


---

## 🧠 Overview

This project presents a real-time adaptive traffic signal control system designed for urban environments like Chennai, where traffic is highly dynamic and dominated by mixed vehicle types.

Unlike traditional fixed-timing systems, our solution uses Reinforcement Learning (PPO) to dynamically adjust signal timings based on live traffic conditions.


---

## 🔁 System Pipeline

SUMO (TraCI) → State Generator → RL Agent → Signal Controller → Dashboard + Hardware

Traffic is simulated using Simulation of Urban MObility (SUMO)

Real-time lane data is extracted via TraCI

RL agent optimizes signal timings

Output is visualized and optionally sent to hardware



---

## 🏆 Hackathon Context

Built for TNSDC Naan Mudhalvan 2026 – Advanced AI/ML Hackathon (PS20)

Problem: Chennai Traffic Signal Timing

Goal: Reduce congestion and improve traffic flow using AI



---

## 👥 Team

Ritika S – Full Stack Developer, RL Integration

Nithaester Ruby Joy S – PPT & Presentation



---

## ⚙️ Key Features

🚦 Adaptive traffic signal control using RL

📊 Real-time dashboard visualization (Streamlit)

🔌 Arduino-based hardware signal simulation

🚑 Emergency vehicle priority handling

🔁 Fully integrated end-to-end pipeline

🧪 SUMO-based realistic traffic simulation



---

## 🧱 Project Architecture

<img src="https://github.com/user-attachments/assets/d6e99c4c-5cc4-4434-8883-3304aa464f71" width="100%" />


## 📁 Project Structure

simulation/   → SUMO config + TraCI adapter  
rl/           → PPO training + inference agent  
hardware/     → Arduino serial bridge + sketch  
backend/      → Controller, telemetry, API  
dashboard/    → Streamlit visualization  
models/       → Trained RL weights  
main.py       → Master orchestrator


---

## 🚀 Getting Started

1. Install Requirements
```bash
pip install -r requirements.txt
```


2. Setup SUMO (Optional but Recommended)

### Install SUMO
```bash
Set SUMO_HOME environment variable
```


---

### 🧠 Train RL Model
```bash
python -m rl.train --timesteps 50000 --intersections 5 --output models/ppo_traffic.zip
```


> If the model is missing, the system falls back to a rule-based heuristic controller.



---

## ▶️ Run System

Basic Run
```bash
python main.py --interval 2 --serve-api
```

With Hardware
```bash
python main.py --serial-port COM5 --interval 2 --serve-api
```

---

## 📊 Launch Dashboard

1. streamlit run dashboard/app.py

2. Dashboard Displays

3. Traffic queue & waiting time

4. RL decisions per intersection

5. Signal states (Green / Yellow / Red)

6. Throughput metrics

7. Baseline vs RL comparison



---

## 🔌 Hardware Integration

- Arduino / ESP32

- LEDs (Red, Yellow, Green)

- Serial communication from backend


Used to simulate real-world signal behavior.


---

## 🌐 API Endpoints

1. GET /api/health
 ```bash
Invoke-RestMethod http://127.0.0.1:8000/api/health 
```
<img width="745" height="152" alt="Screenshot 2026-04-27 173909" src="https://github.com/user-attachments/assets/f9827423-d100-4b7e-98a9-838e3ef5045c" />

3. GET /api/latest
```bash
Invoke-RestMethod http://127.0.0.1:8000/api/latest
```
<img width="1375" height="315" alt="Screenshot 2026-04-27 173846" src="https://github.com/user-attachments/assets/fd1d05c1-8a06-4bbf-a0c3-8c1b720e0efd" />

---

## 🧪 Simulation Behavior

1. TraCI extracts:

- vehicle count

- waiting time

- lane density


2. RL agent outputs:

- signal duration adjustments

- phase switching decisions



---

## 🧯 Fail-Safe Mechanism

1. No SUMO → fallback mock simulation

2. No RL model → heuristic controller

3. No hardware → safe no-op


✔ Ensures system always runs during demo


---

## 📸 Output Screens

**📊 Dashboard**

<img width="1909" height="882" alt="Screenshot 2026-04-27 174032" src="https://github.com/user-attachments/assets/9b1b626f-f616-4e12-be8a-40afb2efd7ee" />
<img width="1872" height="739" alt="Screenshot 2026-04-27 174047" src="https://github.com/user-attachments/assets/648730f3-6edf-4c37-b9a2-5a0c655e105b" />

**🖥️ Streamlit Running**
<img width="1919" height="975" alt="Screenshot 2026-04-27 173830" src="https://github.com/user-attachments/assets/952a1de7-8f21-4dcf-a1b7-f1ca8387b164" />


**🧠 RL Training**
<img width="1919" height="979" alt="Screenshot 2026-04-27 173819" src="https://github.com/user-attachments/assets/6055f516-df44-4c2d-ac91-b782767dd0f2" />
<img width="990" height="924" alt="Screenshot 2026-04-27 173921" src="https://github.com/user-attachments/assets/abb2a39c-36a0-4398-9611-0846fb1707db" />

---

## 📈 Results

⬇️ Reduced average waiting time

⬆️ Improved traffic throughput

🔄 Dynamic adaptation to traffic conditions

Metric	Baseline	RL Model	Improvement
Avg Waiting Time	~120s	~70s	↓ 40%
Throughput	Medium	High	↑ 30%
Signal Behavior	Static	Adaptive	Significant


---

## 🚀 Future Scope

Live CCTV integration with YOLO

Deployment on real intersections

Multi-agent RL for city-scale traffic

Integration with smart city IoT systems



---

## 🎥 Demo
```bash
https://youtu.be/i_daH_Y9Eho?si=9Ben6bIvkI94Wvpe
👉 
```

---

## 📌 Conclusion

This project demonstrates how Reinforcement Learning + Simulation + IoT can transform traditional traffic systems into adaptive, intelligent, and scalable smart city solutions.
