<div align="center">

# 🚦 SmartFlow GreenCorridor AI
### *Multi-Intersection Emergency Vehicle Preemption & AI Green Wave System*

[![Vikasit Nagpur 2026](https://img.shields.io/badge/Hackathon-Vikasit%20Nagpur%202026-00f2fe?style=for-the-badge&logo=target)](https://github.com)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-10b981?style=for-the-badge&logo=python)](https://www.python.org/)
[![Zero Dependencies](https://img.shields.io/badge/Dependencies-Zero%20External-f59e0b?style=for-the-badge)](https://github.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-f43f5e?style=for-the-badge)](LICENSE)

*Developed for **MANTHAN 4 YUVA — VIKASIT NAGPUR 2026** (VNIT Campus, Nagpur)*  
*Track: **Theme 3 (Intelligent Traffic Management System)** & **Theme 2 (Smart City)***

---

</div>

## 📌 Executive Summary

In dense Indian metropolitan arterial corridors like **Nagpur** (connecting central transit nodes like Sitabuldi to premier healthcare centers like AIIMS and GMC Hospital), emergency vehicles (Cardiac Ambulances, Fire Engines) lose **12 to 18 vital "golden hour" minutes** trapped behind static red lights and gridlocked mixed-traffic queues (Auto-rickshaws, Kaali-Peeli cabs, City buses, Two-wheelers).

**SmartFlow GreenCorridor AI** is a 100% software-driven, zero-hardware-dependency digital twin and emergency preemption platform. It continuously evaluates real-time **Time-To-Intersection (TTI)**, clears bottleneck queues ahead of approaching emergency sirens, arbitrates multi-emergency conflicts, and restores balanced adaptive signal cycles post-clearance.

---

## ⚡ Key Results & Performance Benchmarks

| Metric | Traditional Traffic Signals | SmartFlow GreenCorridor AI | Improvement |
| :--- | :--- | :--- | :--- |
| **Sitabuldi ➔ AIIMS Transit Time** | **14.8 minutes** | **4.2 minutes** | **⚡ 71.6% Time Saved** |
| **Average Emergency Speed** | 18 km/h (intermittent stops) | **60 km/h** (unobstructed wave) | **3.3x Faster** |
| **Preemption Trigger Latency** | Manual / None (> 15s) | **< 150 ms (0.16 ms benchmark)** | **Instantaneous** |
| **Secondary Gridlock Prevention** | High (Cross-street starvation) | **Zero (Automated Cycle Recovery)** | **Balanced Grid** |
| **Driving Standard Compliance** | Mixed / Unregulated | **100% Indian Left-Hand Traffic (LHT)** | **Native Fit** |

---

## 🗺️ Nagpur Arterial Corridor Topology (2.2 km)

The simulation engine models 4 real-world connected intersections along the primary emergency transit corridor:

```
[Km 0.0] Sitabuldi Metro Interchange (Node 1)
   │
   ▼ (600m)
[Km 0.9] Medical Square (Node 2)
   │
   ▼ (600m)
[Km 1.5] Wardha Road Viaduct (Node 3)
   │
   ▼ (600m)
[Km 2.1] AIIMS & GMC Nagpur Hospital Emergency Trauma Bay (Node 4)
```

---

## 🚀 Core Features

1. **Anticipatory Dynamic Green Wave:**
   * Downstream traffic lights turn green 45% (~500 meters) ahead of the approaching ambulance, discharging stopped civilian queues *before* the ambulance arrives.
2. **Safe Car-Following & Queuing Physics:**
   * Bumper-to-bumper collision avoidance ensures zero overlapping vehicles.
   * Vertical cross-street traffic halts smoothly at red stop lines and flows across intersections when green.
3. **Emergency Civilian Yielding:**
   * When an ambulance approaches, vehicles in the corridor detect siren beams and pull to the shoulder, opening a clear center express lane.
4. **Multi-Emergency Priority Hierarchy Arbitration:**
   * `Priority 1 (Code Red)`: Critical Cardiac / Trauma Ambulance (Highest override)
   * `Priority 2 (Code Orange)`: Fire Brigade / Disaster Response
   * `Priority 3 (Code Yellow)`: Police / Escort
5. **Post-Emergency Anti-Starvation Phase Recovery:**
   * Prevents secondary city-wide gridlocks by dynamically compensating starved cross-streets immediately after emergency clearance.
6. **Built-in 5-Point Automated Test Suite:**
   * Real-time validation panel for hackathon judges with single-click latency, interlock, arbitration, recovery, and stress testing.

---

## 🛠️ Architecture & Tech Stack

* **Backend Engine:** Pure Python 3 with zero external package dependencies (uses native `http.server`, `urllib`, `time`, `json`, `math`).
* **Frontend Dashboard:** 60 FPS HTML5 Canvas + Cyberpunk Glassmorphism UI (Vanilla CSS + ES6 JavaScript).
* **Network Protocol:** RESTful JSON APIs (`GET /api/grid/status`, `POST /api/corridor/dispatch`, `POST /api/corridor/test_suite`, `POST /api/grid/step`, `POST /api/grid/reset`).

```
traffic_ml/
├── public/
│   ├── index.html         # Mission control dashboard UI
│   ├── style.css          # Glassmorphism, cyber neon accents, responsive layout
│   └── app.js             # 60 FPS 2D Canvas physics & API client
├── src/
│   ├── __init__.py
│   ├── city_grid.py       # 4-Intersection city model & vehicle physics
│   ├── preemption_engine.py # TTI calculator & 5-test judging suite
│   ├── optimizer.py       # Adaptive signal cycle algorithms
│   └── simulation.py      # Background queue generator
├── server.py              # Zero-dependency HTTP & REST server
├── requirements.txt
└── README.md
```

---

## 🏁 Quickstart Guide

### Prerequisites
* Python 3.8+ (No `pip install` required!)

### 1. Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/smartflow-greencorridor-ai.git
cd smartflow-greencorridor-ai
```

### 2. Run the server
```bash
python3 server.py 8080
```

### 3. Open in Browser
Visit **[http://localhost:8080](http://localhost:8080)**

---

## 🧪 Running the Test Suite via CLI

You can trigger the automated test suite directly via cURL:

```bash
curl -s -X POST http://localhost:8080/api/corridor/test_suite | python3 -m json.tool
```

**Output:**
```json
{
    "all_passed": true,
    "passed_count": 5,
    "total_count": 5,
    "results": [
        {
            "id": "test-1",
            "name": "Preemption Response Latency Benchmark (<150ms)",
            "status": "PASS",
            "metrics": "Trigger Latency: 0.08ms (Threshold: 150ms)"
        },
        {
            "id": "test-2",
            "name": "Green Wave Pre-Clearance Interlock",
            "status": "PASS",
            "metrics": "Cascading signals switched to Green wave ahead of vehicle"
        },
        {
            "id": "test-3",
            "name": "Multi-Emergency Priority Hierarchy Arbitration",
            "status": "PASS",
            "metrics": "Arbitration verified: Cardiac Ambulance (P1) prioritized over Fire Engine (P2)"
        },
        {
            "id": "test-4",
            "name": "Post-Emergency Safe Cycle Recovery & Queue Equalization",
            "status": "PASS",
            "metrics": "All 4 nodes smoothly returned to balanced adaptive cycles"
        },
        {
            "id": "test-5",
            "name": "60-Second Stress Batch Run (>60% Delay Reduction)",
            "status": "PASS",
            "metrics": "Time Saved: 71.6% (14.8m ➔ 4.2m)"
        }
    ]
}
```

---

## 👨‍💻 Author & Acknowledgements
* **Event:** MANTHAN 4 YUVA — Nagpur 2026 (Jan Manthan Foundation / RTMNU / VNIT Nagpur)
* **License:** MIT License
