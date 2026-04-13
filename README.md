<p align="center">
  <img src="https://img.shields.io/badge/INDIAN_COAST_GUARD-DISC_14-gold?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAxMDAgMTIwIj48cGF0aCBkPSJNNTAgMiBMOTIgMjUgTDkyIDcwIFE5MiAxMDAgNTAgMTE4IFE4IDEwMCA4IDcwIEw4IDI1IFoiIGZpbGw9Im5vbmUiIHN0cm9rZT0iI0ZGRDcwMCIgc3Ryb2tlLXdpZHRoPSIzIi8+PHBhdGggZD0iTTUwIDggTDg2IDI4IEw4NiA2OCBRODYgOTUgNTAgMTEyIFExNCA5NSAxNCA2OCBMMTQgMjggWiIgZmlsbD0icmdiYSgxMCwyMCw1MCwwLjg1KSIvPjxnIHN0cm9rZT0iI2ZmZiIgZmlsbD0ibm9uZSIgc3Ryb2tlLXdpZHRoPSIyIj48bGluZSB4MT0iNTAiIHkxPSIzNCIgeDI9IjUwIiB5Mj0iODUiLz48cGF0aCBkPSJNMzcgNDQgTDUwIDM0IEw2MyA0NCIvPjxjaXJjbGUgY3g9IjUwIiBjeT0iMzIiIHI9IjMiLz48cGF0aCBkPSJNMzIgNzggUTMyIDYwIDUwIDU4IFE2OCA2MCA2OCA3OCIvPjwvZz48L3N2Zz4=&labelColor=0a1428" height="42"/>
</p>

<h1 align="center">
  <br>
  <sub>🔱</sub>&ensp;PROJECT SAMUDRA&ensp;<sub>🔱</sub>
  <br>
  <sup><sub>Shipboard</sub> <sub>Autonomous</sub> <sub>Maritime</sub> <sub>Unified</sub> <sub>Digital</sub> <sub>Real-time</sub> <sub>Analytics</sub></sup>
</h1>

<p align="center">
  <a href="#-overview"><img src="https://img.shields.io/badge/Status-Prototype_v3.0-00ffcc?style=flat-square&labelColor=0a1428" alt="Status"/></a>
  <a href="#-tech-stack"><img src="https://img.shields.io/badge/Frontend-Svelte_5-FF3E00?style=flat-square&logo=svelte&logoColor=white&labelColor=0a1428" alt="Svelte"/></a>
  <a href="#-tech-stack"><img src="https://img.shields.io/badge/Backend-FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white&labelColor=0a1428" alt="FastAPI"/></a>
  <a href="#-tech-stack"><img src="https://img.shields.io/badge/3D_Engine-Three.js-000000?style=flat-square&logo=threedotjs&logoColor=white&labelColor=0a1428" alt="Three.js"/></a>
  <a href="#-tech-stack"><img src="https://img.shields.io/badge/Maps-Leaflet-199900?style=flat-square&logo=leaflet&logoColor=white&labelColor=0a1428" alt="Leaflet"/></a>
  <a href="#-tech-stack"><img src="https://img.shields.io/badge/Charts-Chart.js-FF6384?style=flat-square&logo=chartdotjs&logoColor=white&labelColor=0a1428" alt="Chart.js"/></a>
  <a href="#-docker"><img src="https://img.shields.io/badge/Deploy-Docker_Compose-2496ED?style=flat-square&logo=docker&logoColor=white&labelColor=0a1428" alt="Docker"/></a>
  <a href="#-websocket-protocol"><img src="https://img.shields.io/badge/Telemetry-4Hz_WebSocket-ffaa33?style=flat-square&labelColor=0a1428" alt="WebSocket"/></a>
  <a href="#-imo-compliance"><img src="https://img.shields.io/badge/IMO-MEPC.355(78)_Compliant-22ff88?style=flat-square&labelColor=0a1428" alt="IMO"/></a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Challenge-Problem_Statement_77-FFD700?style=for-the-badge&labelColor=0a1428" alt="PS77"/>
  <img src="https://img.shields.io/badge/DISC_14-Challenges_177--186-00c8ff?style=for-the-badge&labelColor=0a1428" alt="DISC14"/>
</p>

---

<div align="center">
  
> **"Reducing a fleet's average speed by just 10% yields a 27% fuel saving — the cubic law of propulsive power makes every knot count."**  
> — *Derived from the Admiralty Coefficient equation: Ac = Δ^(2/3) · V³ / P*

</div>

---
<img width="3199" height="1999" alt="Screenshot 2026-04-12 192747" src="https://github.com/user-attachments/assets/992bd93f-09c3-4ad4-a41b-62e4d70d0236" />

## 📋 Table of Contents

<details open>
<summary><b>Click to expand</b></summary>

- [🌊 Overview](#-overview)
- [🏗️ System Architecture](#️-system-architecture)
- [📁 Repository Structure](#-repository-structure)
- [🔬 Physics Engine — First Principles](#-physics-engine--first-principles)
  - [Admiralty Coefficient](#1-admiralty-coefficient)
  - [Cubic Law of Propulsive Power](#2-cubic-law-of-propulsive-power)
  - [Marine Diesel Thermal Efficiency](#3-marine-diesel-thermal-efficiency)
  - [Monsoon Sea-State Resistance Model](#4-monsoon-sea-state-resistance-model)
  - [Trim-Induced Fuel Penalty](#5-trim-induced-fuel-penalty)
- [🤖 AI/ML Modules](#-aiml-modules)
  - [PINN Biofouling Surrogate](#-pinn-biofouling-surrogate)
  - [DRL Voyage Optimizer (PPO)](#-drl-voyage-optimizer-ppo)
  - [CII Tactical Segregation (DBSCAN)](#-cii-tactical-segregation-dbscan)
  - [LSTM Anomaly Detection](#-lstm-anomaly-detection)
  - [Denoising Autoencoder Pipeline](#-denoising-autoencoder-pipeline)
- [� Phase 4 — Gap Analysis Modules](#-phase-4--gap-analysis-modules)
  - [Comprehensive Sensor Integration Hub](#1-comprehensive-sensor-integration-hub)
  - [Predictive Maintenance AI/ML](#2-predictive-maintenance-aiml)
  - [Hull Improvement & Hybrid Propulsion](#3-hull-improvement--hybrid-propulsion)
  - [Systemic Blind Spots Detection](#4-systemic-blind-spots-detection)
  - [Human-AI Collaboration](#5-human-ai-collaboration)
  - [EEXI Compliance Engine](#6-eexi-compliance-engine)
  - [Unified Data Architecture](#7-unified-data-architecture)
- [�🗺️ AIS & Navigation](#️-ais--navigation)
- [📊 Dashboard Pages](#-dashboard-pages)
  - [Bridge — Command Overview](#1-bridge--command-overview)
  - [Engine — Propulsion Analytics](#2-engine--propulsion-analytics)
  - [Route — Geospatial Intelligence](#3-route--geospatial-intelligence)
  - [Compliance — IMO Regulatory](#4-compliance--imo-regulatory)
  - [Settings — System Configuration](#5-settings--system-configuration)
- [⚙️ Tech Stack](#️-tech-stack)
- [📡 WebSocket Protocol](#-websocket-protocol)
- [🚢 Vessel Parameters](#-vessel-parameters)
- [🏛️ IMO Compliance Framework](#️-imo-compliance-framework)
- [📈 KPI Catalog (130+)](#-kpi-catalog-130)
- [🐳 Docker Deployment](#-docker-deployment)
- [💻 Local Development](#-local-development)
- [🧪 Testing Protocol — DISC 14](#-testing-protocol--disc-14)
- [🌍 Market & Use Cases](#-market--use-cases)
- [📚 References & Standards](#-references--standards)
- [🤝 Team](#-team)
- [📄 License](#-license)

</details>

---

## 🌊 Overview

**Project SAMUDRA** is an AI-powered maritime fuel intelligence platform built for the **Indian Coast Guard DISC 14 Challenge** (Problem Statement 77). It provides real-time fuel consumption monitoring, predictive analytics, and autonomous voyage optimization for a **2,350-tonne Offshore Patrol Vessel (OPV)** operating in the Arabian Sea.

The platform combines **first-principles naval hydrodynamics** with **cutting-edge AI/ML** — Physics-Informed Neural Networks (PINNs), Deep Reinforcement Learning (DRL/PPO), DBSCAN clustering, LSTM anomaly detection, and denoising autoencoders — to deliver actionable fuel savings while ensuring full compliance with IMO MARPOL Annex VI, MEPC.355(78), and the Carbon Intensity Indicator (CII) regulatory framework.

### 🎯 Core Capabilities

| Capability | Description | AI Method |
|:---|:---|:---|
| **Real-Time Fuel Monitoring** | 4 Hz telemetry stream with 60+ KPIs | WebSocket + Pydantic validation |
| **Cubic Law Power Prediction** | P ∝ V³ — every knot costs exponentially | First-principles physics |
| **Monsoon Resistance Modeling** | 30–60% added resistance in 3–5m waves | Stochastic state machine |
| **Hull Biofouling Prediction** | 7–20% fuel penalty from biological roughness | Physics-Informed Neural Network |
| **Ghost Route Optimization** | JIT arrival to prevent Sail-Fast-Then-Wait | PPO Deep Reinforcement Learning |
| **CII Tactical Segregation** | Separate transit vs. tactical loiter carbon | DBSCAN density clustering |
| **Engine Anomaly Detection** | MSE-based threshold breach on engine params | LSTM neural network |
| **Signal Denoising** | Savitzky-Golay adaptive noise filtering | Denoising Autoencoder |
| **AIS Position Tracking** | AIVDM Type 1 sentence encoding (ITU-R M.1371-5) | Waypoint interpolation |
| **3D Hull Visualization** | Real-time pitch/roll ship model | Three.js WebGL |
| **Geospatial Route Mapping** | 10-waypoint Arabian Sea patrol with live track | Leaflet + Haversine |
| **Sensor Integration Hub** | 5-sensor fusion (ECDIS, EMCS, FOMS, Weather, VDR) with UKC & XTE | Multi-source correlation |
| **Predictive Maintenance** | Component RUL forecasting with EWMA anomaly detection | MIL-STD-3034 scheduling |
| **Hull & Hybrid Propulsion** | ISO 19030 fouling + CODLAG hybrid drive with battery management | Coating + electric motor |
| **Systemic Blind Spots** | CUSUM drift, micro-climate, KE spike, causal disambiguation | Multi-physics ensemble |
| **Human-AI Collaboration** | Distribution-shift detection, SHAP explainability, SOLAS overrides | Trust-calibrated advisory |
| **EEXI Compliance Engine** | MEPC.328(76) EEXI + enhanced CII 2023-2030 + IMO DCS reporting | Regulatory calculator |
| **Unified Data Architecture** | Pub/sub data bus, NMEA parsing, sensor registry, data quality scoring | Event-driven pipeline |

### 💡 The Problem — Sail-Fast-Then-Wait (SFTW)

The vessel sprints to a destination at high speed, consuming fuel per the **P ∝ V³** cubic law, then sits idle at anchor. This pattern:

```
Speed +10% → Power +33.1% → Fuel +33.1%
Speed +20% → Power +72.8% → Fuel +72.8%
Speed +50% → Power +237.5% → Fuel +237.5%
```

SAMUDRA's DRL agent detects when the vessel is projected to arrive early and computes an **optimal speed reduction** that achieves **Just-In-Time (JIT)** arrival — zero idle time, maximum thermal efficiency, minimum carbon footprint.

---
<img width="3199" height="1580" alt="Screenshot 2026-04-12 192827" src="https://github.com/user-attachments/assets/b9415eca-d154-411a-8fab-a112d27da14c" />

## 🏗️ System Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                    ┌─────────────────────────┐                       │
│   SAMUDRA          │   Svelte 5 Frontend     │     Port 3000        │
│   Edge Node        │   ┌───────────────────┐ │                       │
│                    │   │ Three.js  (3D Hull)│ │   ◄── F1: Bridge     │
│                    │   │ Leaflet  (GeoMap)  │ │   ◄── F2: Engine     │
│                    │   │ Chart.js (Graphs)  │ │   ◄── F3: Route      │
│                    │   │ SVG Gauges + Sparks│ │   ◄── F4: Compliance │
│                    │   └───────────────────┘ │   ◄── F5: Settings   │
│                    └──────────┬──────────────┘                       │
│                               │  WebSocket 4Hz                       │
│                               │  ws://localhost:8000/ws/telemetry    │
│                    ┌──────────▼──────────────┐                       │
│                    │  FastAPI Backend         │     Port 8000        │
│                    │  ┌───────────────────┐  │                       │
│                    │  │ HydrodynamicEngine │  │  ◄── 20-Step Pipeline│
│                    │  │ BiofoulingSurrogate│  │  ◄── PINN            │
│                    │  │ DRLVoyageOptimizer │  │  ◄── PPO Agent       │
│                    │  │ CIISegregation     │  │  ◄── DBSCAN          │
│                    │  │ AISNavigator       │  │  ◄── NMEA 0183      │
│                    │  │─── Phase 4 ────────│  │                       │
│                    │  │ SensorIntegration  │  │  ◄── 5 Sensor Fusion │
│                    │  │ PredictiveMaint.   │  │  ◄── RUL + EWMA     │
│                    │  │ HullPropulsion     │  │  ◄── ISO 19030+CODLAG│
│                    │  │ BlindSpots         │  │  ◄── CUSUM + Causal  │
│                    │  │ HumanAI            │  │  ◄── SHAP + SOLAS   │
│                    │  │ EEXICompliance     │  │  ◄── MEPC.328(76)   │
│                    │  │ DataArchitecture   │  │  ◄── Pub/Sub Bus    │
│                    │  └───────────────────┘  │                       │
│                    │  Pydantic v2 Validation  │                       │
│                    └──────────────────────────┘                       │
│                                                                       │
│   REST Endpoints:                                                     │
│     GET /health                    ← System status + uptime           │
│     GET /api/v1/telemetry/latest   ← Last telemetry snapshot          │
│     GET /api/v1/telemetry/history  ← Ring buffer (300 frames)         │
│     GET /api/v1/vessel/status      ← Aggregated vessel summary        │
│     GET /api/v1/sensors/status     ← Sensor health & integration      │
│     GET /api/v1/maintenance/status ← Predictive maintenance schedule  │
│     GET /api/v1/hull/status        ← Hull coating & propulsion state  │
│     GET /api/v1/blindspots/status  ← Drift, spike, sync diagnostics  │
│     GET /api/v1/humanai/status     ← AI confidence & explainability   │
│     GET /api/v1/eexi/status        ← EEXI/CII/DCS compliance         │
│     GET /api/v1/databus/status     ← Data bus & quality metrics       │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 📁 Repository Structure

```
Project-SAMUDRA/
├── 📄 README.md                          # This file
├── 📄 docker-compose.yml                 # One-command deployment
├── 📄 start.ps1                          # Windows PowerShell launcher
├── 📄 start.sh                           # Linux/macOS bash launcher
├── 📄 .gitignore                         # node_modules, dist, __pycache__
│
├── 🔧 backend/                           # Python FastAPI Backend
│   ├── 📄 Dockerfile                     # Python 3.12-slim container
│   ├── 📄 requirements.txt              # 6 dependencies (FastAPI, NumPy, etc.)
│   └── 📂 app/
│       ├── 📄 __init__.py
│       ├── 📄 config.py                  # Pydantic Settings (ports, tick rate)
│       ├── 📄 main.py                    # FastAPI app + REST endpoints + ring buffer
│       ├── 📂 models/
│       │   ├── 📄 __init__.py            # Pydantic v2 TelemetryFrame (10 sub-models)
│       │   └──                           # EngineFrame, NavigationFrame, PhysicsFrame,
│       │                                 # EnvironmentFrame, AISFrame, CurvePoint,
│       │                                 # AIPredictiveCurve, DRLOptimization,
│       │                                 # CIISegregation, TelemetryFrame
│       ├── 📂 physics/
│       │   ├── 📄 __init__.py
│       │   ├── 📄 hydrodynamics.py       # Core 20-step physics engine (Admiralty Coeff,
│       │   │                             # Cubic Law, Monsoon FSM, thermal efficiency,
│       │   │                             # + Phase 4 gap module orchestration)
│       │   ├── 📄 biofouling.py          # PINN hull roughness surrogate
│       │   ├── 📄 drl_optimizer.py       # PPO voyage re-optimization agent
│       │   ├── 📄 cii_segregation.py     # DBSCAN transit/loiter classification
│       │   ├── 📄 ais_navigation.py      # AIS AIVDM encoding + waypoint navigation
│       │   ├── 📄 sensor_integration.py  # 5-sensor fusion (ECDIS, EMCS, FOMS, WX, VDR)
│       │   ├── 📄 predictive_maintenance.py # RUL forecasting + EWMA anomaly, MIL-STD-3034
│       │   ├── 📄 hull_propulsion.py     # ISO 19030 fouling + CODLAG hybrid propulsion
│       │   ├── 📄 blind_spots.py         # CUSUM drift, micro-climate, KE spike, causal
│       │   ├── 📄 human_ai.py            # Distribution-shift, SHAP, SOLAS, connectivity
│       │   ├── 📄 eexi_compliance.py     # MEPC.328(76) EEXI + CII 2023-2030 + IMO DCS
│       │   └── 📄 data_architecture.py   # Pub/sub bus, NMEA parser, quality scoring
│       └── 📂 ws/
│           ├── 📄 __init__.py
│           └── 📄 telemetry.py           # Bidirectional WebSocket handler (4Hz)
│
└── 🎨 frontend/                          # Svelte 5 + TypeScript Frontend
    ├── 📄 Dockerfile                     # Node 22-alpine container
    ├── 📄 package.json                   # Svelte 5, Three.js, Leaflet, Chart.js
    ├── 📄 vite.config.ts                 # Vite 6 dev server (port 3000)
    ├── 📄 svelte.config.js               # Svelte compiler config
    ├── 📄 tsconfig.json                  # TypeScript strict mode
    ├── 📄 index.html                     # SPA entry point
    └── 📂 src/
        ├── 📄 main.ts                    # Svelte mount point
        └── 📄 App.svelte                 # Monolithic SFC (~2200+ lines)
                                          # — Obsidian Neon design system
                                          # — 5-page SPA with F-key navigation
                                          # — 130+ real-time KPI widgets
                                          # — 7 Phase 4 gap module panels
                                          # — SVG gauges, sparklines, heatmaps
                                          # — Three.js 3D hull model
                                          # — Leaflet geospatial map
                                          # — Chart.js LSTM + DBSCAN charts
                                          # — EEXI compliance grid
                                          # — Indian Coast Guard SVG emblem
```

---
<img width="3125" height="1641" alt="Screenshot 2026-04-12 192846" src="https://github.com/user-attachments/assets/225eade1-fcf1-4685-8a33-2ee274533b80" />

## 🔬 Physics Engine — First Principles

The backend's `HydrodynamicEngine` class implements a **physically rigorous** simulation pipeline. Every telemetry frame passes through these equations in sequence:

### 1. Admiralty Coefficient

The Admiralty Coefficient is the cornerstone metric of naval architecture — a dimensionless quantity relating displacement, speed, and power:

$$A_c = \frac{\Delta^{2/3} \cdot V^3}{P}$$

| Symbol | Meaning | Value |
|:---:|:---|:---|
| $\Delta$ | Displacement | 2,350 tonnes |
| $V$ | Speed Over Ground | ~14.5 knots (design) |
| $P$ | Shaft Power | ~8,500 kW (design) |
| $A_c$ | Admiralty Coefficient | ≈ 532.8 (constant in calm sea) |

> **Diagnostic insight:** In calm water, $A_c$ should remain approximately constant. A dropping $A_c$ indicates hull fouling or mechanical degradation. A rising $A_c$ under constant speed implies the vessel is getting a favorable current assist.

### 2. Cubic Law of Propulsive Power

The most consequential equation in maritime fuel optimization:

$$P = P_{design} \cdot \left(\frac{V}{V_{design}}\right)^3$$

```
┌─────────────────────────────────────────────────────────────────┐
│  Speed Change vs. Power/Fuel Increase (Cubic Law)               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  V/V_d │ 0.80  │ 0.90  │ 1.00  │ 1.10  │ 1.20  │ 1.50  │     │
│  ──────┼───────┼───────┼───────┼───────┼───────┼───────┤     │
│  P/P_d │ 0.512 │ 0.729 │ 1.000 │ 1.331 │ 1.728 │ 3.375 │     │
│  ──────┼───────┼───────┼───────┼───────┼───────┼───────┤     │
│  Δ%    │ -48.8 │ -27.1 │  0.0  │ +33.1 │ +72.8 │+237.5 │     │
│                                                                  │
│  ████░░░░░░░░░░░  0.80x speed = 51.2% power (48.8% saving!)    │
│  ██████████░░░░░  0.90x speed = 72.9% power (27.1% saving!)    │
│  ██████████████░  1.00x speed = 100% power (baseline)          │
│  █████████████████████  1.10x speed = 133.1% power (+33.1%!)   │
│  ████████████████████████████  1.20x speed = 172.8% power      │
│  ███████████████████████████████████████████████  1.50x = 337%  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 3. Marine Diesel Thermal Efficiency

$$\eta_{thermal} \in [0.48, 0.52]$$

The thermal efficiency band for modern marine diesel engines (MAN B&W / Wärtsilä type):

$$\text{Fuel Power}_{kW} = \frac{P_{shaft}}{\eta}$$

$$\text{Fuel Flow}_{kg/h} = \frac{\text{Fuel Power} \times 3600}{LCV \times 1000}$$

$$\text{SFOC}_{g/kWh} = \frac{\text{Fuel Flow} \times 1000}{P_{shaft}}$$

Where $LCV_{HFO} = 42.7 \text{ MJ/kg}$ (Lower Calorific Value of Heavy Fuel Oil).

### 4. Monsoon Sea-State Resistance Model

The Arabian Sea experiences significant seasonal monsoons. When wave heights reach 3–5 metres, a multiplicative resistance factor of **30–60%** is applied:

$$P_{actual} = P_{calm} \cdot (1 + R_{monsoon})$$

| Sea Condition | Wave Height | $R_{monsoon}$ | Power Increase |
|:---|:---:|:---:|:---:|
| Calm | 0.3–1.0 m | 0% | Baseline |
| Moderate | 1.0–3.0 m | 0–15% | Minor |
| **Monsoon Burst** | **3.0–5.0 m** | **30–60%** | **Significant** |

The monsoon is modeled as a **finite state machine** with stochastic timing:
- **Calm spells**: 60–300 seconds
- **Monsoon bursts**: 30–120 seconds
- Wave height modulates within the storm via a bounded random walk

### 5. Trim-Induced Fuel Penalty

Non-optimal vessel trim (pitch angle) increases hull resistance:

$$
\text{Penalty (percent)} = \begin{cases} 0 & \lvert\theta_{pitch}\rvert \leq 0.5^{\circ} \\[6pt] \min\bigl(2.5 \cdot (\lvert\theta_{pitch}\rvert - 0.5),\; 5.0\bigr) & \lvert\theta_{pitch}\rvert \gt 0.5^{\circ} \end{cases}
$$

A 2° trim yields ~3.75% fuel penalty. A 3° trim hits the 5% ceiling.

---
<img width="3126" height="1386" alt="Screenshot 2026-04-12 192905" src="https://github.com/user-attachments/assets/e1fae1d8-08b5-48b6-b4ec-8b71524be4c4" />

## 🤖 AI/ML Modules

### 🧬 PINN Biofouling Surrogate

**File:** `backend/app/physics/biofouling.py`

Simulates a Physics-Informed Neural Network predicting hull biological roughness degradation in Indian Ocean waters (26–30°C):

```
                    Biological Roughness Coefficient (BRC) Growth
                    ─────────────────────────────────────────────

     BRC (%)│
     20 ────┤                                         ┌─────── BRC_MAX
            │                                    ╱────╱
     15 ────┤                              ╱────╱
            │                         ╱───╱
     10 ────┤                    ╱───╱
            │               ╱───╱
      7 ────┤──────────────╱ ◄─── BRC_MIN (clean hull)
            │
      0 ────┼──────┬───────┬───────┬───────┬───────┬──►  Time
            0     12h     24h     36h     48h     60h

    Temperature Modulation: +12% growth rate per °C above 26°C reference
    SST Range: 26–30°C (Indian Ocean operating envelope)
```

**Output per tick:**
- Biological Roughness Coefficient (BRC): 0.07 → 0.20
- 5-point predictive fuel curve (10–20 kn speed sweep)
- Optimal vs. actual fuel burn with penalty percentage
- Sea surface temperature correlation

### 🎯 DRL Voyage Optimizer (PPO)

**File:** `backend/app/physics/drl_optimizer.py`

Simulates a Proximal Policy Optimization agent that prevents the **Sail-Fast-Then-Wait (SFTW)** anti-pattern:

```
┌──────────────────────────────────────────────────────────────┐
│                 Ghost Route Decision Logic                     │
├──────────────────────────────────────────────────────────────┤
│                                                                │
│  IF ETA_current < ETA_planned - 120s (arriving >2min early)   │
│     THEN → Activate Ghost Route                                │
│     → Compute optimal speed reduction                          │
│     → Target: 70–85% MCR band (peak thermal efficiency)       │
│     → Achieve JIT (Just-In-Time) arrival                      │
│     → Report fuel saved (kg/h) vs SFTW scenario               │
│                                                                │
│  PPO Reward Function (Heuristic Weights):                     │
│    R(s,a) = 0.40 · (-fuel_consumed)                           │
│           + 0.25 · (-|ETA - target|)                          │
│           + 0.15 · (-monsoon_resistance)                       │
│           + 0.20 · MCR_band_bonus                              │
│                                                                │
│  MCR Optimal Band:                                             │
│    ░░░░░░░████████████████░░░░░░░░░░░░░░░░                   │
│    0%    70%           85%              100% MCR               │
│         ▲ Peak Efficiency Zone ▲                               │
│                                                                │
└──────────────────────────────────────────────────────────────┘
```

**Output per tick:**
- Ghost Route active/inactive status
- Current vs. recommended speed (knots)
- ETA current vs. planned (seconds)
- Fuel saving rate (kg/h) + cumulative total (kg)
- MCR load percentage + band compliance
- PPO reward signal

### 📊 CII Tactical Segregation (DBSCAN)

**File:** `backend/app/physics/cii_segregation.py`

Implements IMO MEPC.355(78) correction factors by classifying vessel operational modes using DBSCAN-inspired density clustering in the speed–power 2D space:

```
     Power (kW)
     8500 ┤
          │          ░░░░░░░░
     6000 ┤       ░░░░░░░░░░░░░
          │      ░░░TRANSIT░░░░░     ◄── SOG ≥ 4.0 kn
     4000 ┤       ░░░░░░░░░░░
          │        ░░░░░░░░░
     2000 ┤
          │  ▓▓▓▓▓▓▓
     1000 ┤  ▓LOITER▓              ◄── SOG < 4.0 kn, P > 5% MCR
          │  ▓▓▓▓▓▓▓
      425 ┤─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─   ◄── 5% MCR threshold
          │  ···IDLE···             ◄── SOG < 4.0 kn, P ≤ 5% MCR
        0 ┼───┬───┬───┬───┬───┬──► Speed (kn)
          0   2   4   8  12  16

    Classification Rules:
    ┌────────────┬──────────────┬──────────────────────────┐
    │ SOG ≥ 4 kn │ Any power    │ TRANSIT (normal steaming) │
    │ SOG < 4 kn │ P > 5% MCR   │ LOITER  (tactical ops)   │
    │ SOG < 4 kn │ P ≤ 5% MCR   │ IDLE    (excluded)       │
    └────────────┴──────────────┴──────────────────────────┘
```

**CII Rating Bands (A–E):**

| Rating | Status | Action |
|:---:|:---|:---|
| **A** | Significantly superior | — |
| **B** | Minor superior | — |
| **C** | Moderate | Monitor |
| **D** | Minor inferior | Corrective action plan |
| **E** | Inferior | **Mandatory corrective action** |

**Attained CII Formula:**

$$\text{CII}_{attained} = \frac{\sum FC_j \cdot C_{Fj}}{\text{Capacity} \cdot D_t}$$

Where $C_F = 3.114$ (HFO CO₂ emission factor), Capacity = 2,350 DWT, $D_t$ = distance in NM.

### 🧠 LSTM Anomaly Detection

**Frontend:** Chart 6 — LSTM 24-Hour Analysis (Engine page)

A Long Short-Term Memory network processes the 24-hour engine parameter history to detect anomalous patterns:

| Parameter | Description |
|:---|:---|
| **MSE Threshold** | Mean Squared Error baseline from training |
| **24-Hour Bins** | Hourly aggregation of engine telemetry |
| **Anomaly Flag** | Triggered when MSE > threshold for any bin |
| **Visualization** | Bar chart — amber (near-threshold) / cyan (normal) |

### 🔧 Denoising Autoencoder Pipeline

**Frontend:** Settings page — F1 Pipeline panel

Interactive noise filtering with two configurable parameters:

| Parameter | Range | Effect |
|:---|:---:|:---|
| **Imputation Sensitivity** | 0–100% | Dropout threshold for missing data interpolation |
| **Smoothing Factor** | 0–100% | Maps to Savitzky-Golay window: $k = \lfloor f/14.3 \rfloor$, $ord = 3$ |

Live MSE readout oscillates to show real-time reconstruction error.

---

## 🔩 Phase 4 — Gap Analysis Modules

Seven additional physics/intelligence modules were developed to close every gap identified in the **DISC 14 Problem Statement 77** analysis. Each module is a standalone Python class orchestrated by `hydrodynamics.py` as tick steps 14–20, feeding the unified telemetry frame at 4 Hz.

### 1. Comprehensive Sensor Integration Hub

**File:** `backend/app/physics/sensor_integration.py`

Fuses data from five independent sensor suites into correlated navigational and fuel intelligence:

| Sensor | Protocol | Key Outputs |
|:---|:---:|:---|
| **ECDIS** | IEC 61174 | Under-keel clearance (UKC), cross-track error (XTE), ENC chart corrections |
| **EMCS** | MAN CEAS | Per-cylinder exhaust temperature, ME load balance, turbocharger RPM |
| **FOMS** | ISO 8217 | Mass flow, density, viscosity, water content (%), fuel quality index |
| **Weather** | WMO SYNOP | Barometric trend, humidity, visibility, localized sea-state estimate |
| **VDR** | IEC 61996 | Voyage Data Recorder recording status, distress capsule integrity |

**Computed Correlations:**
- UKC ↔ draft ↔ displacement ↔ fuel-trim penalty
- XTE as percentage of safe corridor width
- Fuel quality index (0–100 composite)
- Overall sensor health (% of sensors responding with fresh data)

### 2. Predictive Maintenance AI/ML

**File:** `backend/app/physics/predictive_maintenance.py`

Implements MIL-STD-3034 reliability-centered maintenance with real-time anomaly detection:

```
Component Health Tiers:
  [███████████████████] 100% — HEALTHY       (RUL > 90 days)
  [██████████████░░░░░]  75% — WATCH         (RUL 30–90 days)
  [█████████░░░░░░░░░░]  50% — CAUTION       (RUL 7–30 days)
  [████░░░░░░░░░░░░░░░]  25% — CRITICAL      (RUL < 7 days)
```

- **EWMA Anomaly Detector**: Exponentially Weighted Moving Average with adaptive thresholds
- **ComponentHealthModel**: Tracks RUL (Remaining Useful Life) per component using Weibull degradation curves
- **MaintenanceScheduler**: Priority queue ordering by RUL urgency (nearest-deadline-first)

### 3. Hull Improvement & Hybrid Propulsion

**File:** `backend/app/physics/hull_propulsion.py`

| Sub-Module | Standard | Description |
|:---|:---:|:---|
| **HullCoatingModel** | ISO 19030 | Antifouling coating degradation + cleaning ROI (Hull Roughness Power penalty as ΔR/R) |
| **CleaningROICalculator** | — | Cost-benefit analysis: cleaning cost vs. cumulative fuel penalty savings |
| **HybridPropulsionSystem** | — | CODLAG (Combined Diesel and Gas) hybrid drive simulation |

**CODLAG Hybrid States:**
- `DIESEL_ONLY` — Full MCR from main engines
- `ELECTRIC_ONLY` — Battery-powered for harbor/quiet ops (SOC-limited)
- `HYBRID` — Combined diesel + electric motor assist
- `REGEN` — Regenerative braking mode, charging battery from shaft

**Battery Model:** 500 kWh Li-ion, SOC tracking (0–100%), 250 kW electric motor, charge/discharge cycling.

### 4. Systemic Blind Spots Detection

**File:** `backend/app/physics/blind_spots.py`

Detects degradation patterns and confounding factors that traditional monitoring misses:

| Detector | Method | Target |
|:---|:---:|:---|
| **BaselineDegradationTracker** | CUSUM (Cumulative Sum) | Slow sensor drift over hours/days |
| **MicroClimateEngine** | Zone classification | Localized SST/current micro-climates that bias fuel models |
| **KineticEnergySpikeDetector** | ΔKE threshold | Speed transients masked by averaging (course changes, acceleration) |
| **IntegrationSyncMonitor** | Clock-delta check | Sensor timestamp misalignment across data sources |
| **CausalDisambiguationEngine** | Multi-factor attribution | Disentangling weather vs. fouling vs. trim vs. current effects |

$$\text{CUSUM}_t = \max\bigl(0,\; \text{CUSUM}_{t-1} + (x_t - \mu_0) - k\bigr)$$

Where $\mu_0$ is the historical baseline, $k$ is the allowable slack, and an alarm fires when CUSUM exceeds threshold $h$.

### 5. Human-AI Collaboration

**File:** `backend/app/physics/human_ai.py`

Ensures AI recommendations remain trustworthy and actionable under operational conditions:

- **DistributionShiftDetector** — KS-inspired statistical test detecting when live sensor distributions deviate from training data → triggers model confidence degradation
- **ConnectivityManager** — Classifies comms channel (LOCAL/SATCOM/DEFERRED) and adjusts advisory verbosity; ensures AI continues functioning under challenged networking
- **ExplainabilityEngine** — SHAP-like additive feature attribution producing natural-language explanations ("Top factor: wave_height contributed +34% to fuel increase")
- **SafetyOverrideProtocol** — SOLAS Chapter V override tracking; logs all manual overrides with timestamps and justification for audit trail

**Trust Calibration:**
```
AI Confidence = f(shift_detected, connectivity, sensor_health)
  HIGH   → Full advisory mode (speed + route recommendations)
  MEDIUM → Cautionary advisory (flagged as lower-confidence)
  LOW    → Manual fallback (AI provides data display only)
```

### 6. EEXI Compliance Engine

**File:** `backend/app/physics/eexi_compliance.py`

Implements the full IMO EEXI regulatory calculation stack:

**EEXI Attained (MEPC.328(76)):**

$$\text{EEXI} = \frac{C_F \cdot \text{SFC} \cdot 0.75 \cdot \text{MCR}}{f_i \cdot \text{Capacity} \cdot V_{ref} \cdot f_w}$$

| Symbol | Description | Value |
|:---:|:---|:---|
| $C_F$ | CO₂ conversion factor (HFO) | 3.114 |
| SFC | Specific Fuel Consumption | ~190 g/kWh |
| MCR | Maximum Continuous Rating | 8,500 kW |
| $f_i$ | Technical correction factor | 1.0 |
| Capacity | DWT | 2,350 t |
| $V_{ref}$ | Reference speed | 14.5 kn |
| $f_w$ | Weather correction factor | 1.0 |

**Enhanced CII Tracker (2023–2030):**
- Annual reduction factors per MEPC.338(76) — reducing required CII by ~2% yearly
- Dynamic year-based thresholds for A–E ratings
- Separate tracking for transit vs. total operational CII

**IMO DCS Reporter (MEPC.278(70)):**
- Annual fuel consumption (tonnes)
- Total distance sailed (NM)
- Hours underway
- Structured JSON export for Flag State submission

### 7. Unified Data Architecture

**File:** `backend/app/physics/data_architecture.py`

Event-driven data management layer replacing ad-hoc data passing:

```
┌──────────────────────────────────────────────────────┐
│                  Unified Data Bus                      │
│  ┌────────┐  publish()  ┌─────────────────────┐      │
│  │ Sensor │────────────►│  Topic: engine.*     │      │
│  │ Feeds  │             │  Topic: nav.*        │      │
│  └────────┘             │  Topic: env.*        │      │
│                         │  Topic: physics.*    │      │
│  ┌────────┐  subscribe()│  Topic: compliance.* │      │
│  │ Physics│◄────────────┤                      │      │
│  │ Engine │             └─────────────────────┘      │
│  └────────┘                                           │
│                                                        │
│  ┌──────────────┐   ┌──────────────┐                  │
│  │SensorRegistry│   │DataQualityScr│                  │
│  │ • register() │   │ • freshness  │                  │
│  │ • heartbeat()│   │ • accuracy   │                  │
│  │ • status()   │   │ • consistency│                  │
│  └──────────────┘   │ • completness│                  │
│                      └──────────────┘                  │
│                                                        │
│  ┌──────────────┐                                     │
│  │ NMEA Parser  │ Parse $GPGGA/$WIMDA → typed dicts   │
│  └──────────────┘                                     │
└──────────────────────────────────────────────────────┘
```

**Data Quality Index (DQI):**
- **Freshness** — Lag since last sensor update (target < 500ms)
- **Accuracy** — Signal-to-noise ratio and calibration status
- **Consistency** — Cross-sensor agreement (e.g., ECDIS position vs. GPS)
- **Completeness** — % of expected fields populated per frame

---
<img width="3124" height="1274" alt="Screenshot 2026-04-12 192955" src="https://github.com/user-attachments/assets/075c1bd7-572e-4651-bbec-74b3238e9743" />

## 🗺️ AIS & Navigation

**File:** `backend/app/physics/ais_navigation.py`

### Arabian Sea Patrol Route — 10 Waypoints

```
                          ARABIAN SEA PATROL ROUTE
              ┌──────────────────────────────────────────┐
              │                                          │
        20°N ─┤                    ◉ WP0 Mumbai          │
              │                   ╱                      │
        18°N ─┤                  ╱                       │
              │                 ⬇ WP1 Off Ratnagiri      │
        16°N ─┤                ╱                         │
              │               ⬇ WP2 Off Goa              │
        14°N ─┤              ╱  WP3 Off Karwar           │
              │             ♦                             │
        12°N ─┤  WP8 ◉────────── WP4 Off Mangalore      │
              │  Mid Arabian │                            │
        10°N ─┤  Sea patrol  │  ◉ WP6 Lakshadweep       │
              │              │ ╱    (Kavaratti)           │
         8°N ─┤              ◉ WP7 Minicoy               │
              │                    ╱                      │
              └──────┬──────┬─────WP5──Off──Kochi────────┘
                    68°E   72°E   76°E
```

| Waypoint | Location | Coordinates |
|:---:|:---|:---:|
| WP 0 | Mumbai Anchorage | 18.922°N, 72.836°E |
| WP 1 | Off Ratnagiri | 16.980°N, 73.100°E |
| WP 2 | Off Goa (Mormugao) | 15.410°N, 73.780°E |
| WP 3 | Off Karwar | 14.800°N, 74.050°E |
| WP 4 | Off Mangalore | 12.870°N, 74.810°E |
| WP 5 | Off Kochi | 9.970°N, 76.260°E |
| WP 6 | Lakshadweep (Kavaratti) | 10.570°N, 72.640°E |
| WP 7 | Minicoy Island | 8.280°N, 73.040°E |
| WP 8 | Mid Arabian Sea Patrol | 12.500°N, 68.000°E |
| WP 9 | Return Leg, Off Goa | 15.700°N, 71.000°E |

**MMSI:** 419 001 234 (MID 419 = India)

### AIVDM Message Type 1 Encoding

Full 168-bit binary payload per ITU-R M.1371-5, six-bit ASCII armored into standard `!AIVDM` NMEA 0183 sentences.

```
!AIVDM,1,1,,A,<28 six-bit chars>,0*<checksum>
```

| Field | Bits | Description |
|:---|:---:|:---|
| Message Type | 0–5 | 1 (Position Report Class A) |
| MMSI | 8–37 | 419001234 |
| SOG | 50–59 | Speed Over Ground (1/10 kn) |
| Longitude | 61–88 | 1/10000 minutes, signed |
| Latitude | 89–115 | 1/10000 minutes, signed |
| COG | 116–127 | Course Over Ground (1/10°) |
| True Heading | 128–136 | Degrees |

---

## 📊 Dashboard Pages

The frontend is a 5-page Single Page Application with **F-key keyboard shortcuts** and an obsidian-neon design system.

### Page Navigation

| Key | Page | Icon | Description |
|:---:|:---|:---:|:---|
| **F1** | Bridge | ⚓ | Command overview — risk matrix, 3D hull, gauges |
| **F2** | Engine | ⚙️ | Propulsion analytics — LSTM, telemetry grid, MCR |
| **F3** | Route | 🗺️ | Geospatial intelligence — Leaflet map, AIS, waypoints |
| **F4** | Compliance | 📋 | IMO regulatory — CII, DBSCAN, segment table, IMO DCS |
| **F5** | Settings | 🔧 | System config — SOLAS override, autoencoder, network |

### 1. Bridge — Command Overview

The primary operational view displaying aggregated vessel intelligence:

- **6-Domain Risk Matrix** — Engine, Navigation, Environment, Compliance, Hull, Structural risk scores with color-coded severity (green/cyan/amber/red) and an overall composite index
- **Real-Time Gauges** — SVG arc gauges for RPM, Fuel Flow, Power, Speed, SFOC, Temperature, Thermal Efficiency with dynamic color gradients
- **3D Hull Model** — Three.js WebGL scene with ambient light simulating real-time pitch (trim) and roll angles from telemetry. Ship geometry rendered as a simplified hull box with bridge superstructure
- **Sparkline Arrays** — 120-sample rolling arrays for RPM, Fuel, Temperature, Speed with trend indicators (▲ UP / ▼ DOWN / ● FLAT)
- **AI Predictive Curve** — 5-point PINN biofouling fuel curve showing optimal vs. actual consumption across the 10–20 kn speed envelope
- **DRL Ghost Route Panel** — PPO optimizer status with current/recommended speed, fuel saving rate, cumulative savings, and MCR band compliance
- **System Alerts** — Deduplicated, severity-tagged alert feed (CRITICAL, WARNING, ADVISORY, INFO) with timestamps and occurrence counts
- **Sensor Integration Hub** — 5-sensor fusion status (ECDIS, EMCS, FOMS, Weather, VDR) with live status indicators, UKC, XTE, fuel quality index, and overall sensor health %
- **Data Architecture Panel** — Unified Data Bus health: DQI score bar, message rate, 4-dimension quality grid (freshness/accuracy/consistency/completeness), NMEA parse count, registered sensor count

### 2. Engine — Propulsion Analytics

Deep-dive into propulsion system monitoring:

- **Twin Engine Status** — Dual-engine KPI cards showing per-engine stats
- **LSTM 24hr Bar Chart** — Chart.js bar visualization of 24 hourly anomaly bins with a red dashed threshold line. Dynamic badge: `ANOMALY DETECTED` (red) / `STABLE` (green)
- **Live Telemetry 2×2 Grid** — E1 Lube Oil Pressure, E1 Coolant Temperature, E2 Lube Oil Pressure, E2 Exhaust C3 Temperature with conditional alert styling when values exceed thresholds
- **Propulsion Sync Hub** — MCR Load bar with 70–85% **green optimal zone overlay** and live pointer tracking. Supplementary readouts: CPP Pitch angle, Shaft RPM, Load Balance %, Propeller Coefficient Δ
- **Enhanced SOLAS Override** — Interactive toggle button (DISARMED ↔ ARMED) with track slider, armed/disarmed visual states, and system alert on activation
- **Predictive Maintenance Panel** — Component health tiers (HEALTHY/WATCH/CAUTION/CRITICAL) with RUL days per component, anomaly count, and next-maintenance indicator per MIL-STD-3034
- **Hull & Hybrid Propulsion Panel** — ISO 19030 coating age, ΔR/R fouling progress bar, CODLAG hybrid drive mode indicator, battery SOC gauge, electric motor power, and hybrid fuel saving %

### 3. Route — Geospatial Intelligence

Leaflet-powered maritime situational awareness:

- **Live Vessel Track** — Polyline trail plotting vessel position history on OpenStreetMap
- **Waypoint Markers** — All 10 Arabian Sea patrol waypoints with popup labels
- **Vessel Marker** — Real-time position with heading indicator
- **NMEA Display** — Raw `!AIVDM` sentence output
- **Navigation Metrics** — Current waypoint index, distance to next waypoint, COG, heading

### 4. Compliance — IMO Regulatory

Regulatory compliance monitoring and reporting:

- **CII Tactical Compliance Panel** — RAW vs. CORRECTED CII ratings with letter-grade badges (A–E), reference line comparison, scale bar visualization
- **CII 8-Item Metrics Grid** — Transit CO₂, Loiter CO₂, Transit Fuel, Loiter Fuel, Transit Distance, Loiter Events, Transit Events, Elapsed Hours
- **DBSCAN Emission Segregation** — Chart.js scatter plot showing Transit cluster (cyan) vs. Patrol/Loiter cluster (amber) in speed–fuel 2D space. Three KPI boxes: Total Fuel, DBSCAN Exempt Fuel, Attained Emission Ratio
- **Segment Classification Table** — 7-row operational timeline with color-coded mode badges (TRANSIT=cyan, SAR_LOITER=amber, ANCHORED=gray), fuel consumption per segment, and amber highlighting for segments >20 MT
- **IMO DCS Report Button** — One-click Data Collection System report generation with alert notification
- **DRL PPO Optimizer** — Full Ghost Route dashboard with speed reduction advice, MCR band status, and cumulative fuel savings
- **Systemic Blind Spots Panel** — CUSUM drift progress bar with alarm threshold, micro-climate zone classifier, KE spike detection flag, sensor sync status, and causal disambiguation (top confounding factor)
- **Human-AI Collaboration Panel** — AI confidence tier badge (HIGH/MEDIUM/LOW), connectivity type and bandwidth, SHAP top factor with contribution %, distribution shift alert, SOLAS override audit status, and natural-language advisory text
- **EEXI Compliance Engine** — 4-card grid: EEXI Attained, EEXI Required, Margin, CII Enhanced Rating. Detail rows for CF, SFC, MCR fraction, DWT, EPL, IMO DCS totals, and annual reduction schedule

### 5. Settings — System Configuration

Edge node configuration and diagnostics:

- **AI Advisory Mode Toggle** — Master on/off for all AI subsystems (PINN, DRL, CII). Sends `set_ai_mode` WebSocket command to backend
- **Enhanced SOLAS Override** — Interactive safety override with armed/disarmed states
- **Network Communication Tiers** — LOCAL (●ACTIVE), 4G/LTE (○STANDBY), ISRO S-BAND (●TRANSMITTING)
- **Denoising Autoencoder Panel** — F1 PIPELINE: AUTOENCODER NOISE FILTER with live MSE, Imputation Sensitivity slider, Smoothing Factor slider with dynamic Savitzky-Golay parameter computation
- **Edge Systems Configuration** — Readouts for CPU/GPU load, memory, storage, data rate

---

## ⚙️ Tech Stack

### Frontend

| Technology | Version | Purpose |
|:---|:---:|:---|
| **Svelte 5** | 5.x | Reactive UI framework with runes (`$state`, `$effect`, `$derived`) |
| **TypeScript** | ~5.7 | Type-safe development |
| **Vite** | 6.x | Build tool & dev server |
| **Three.js** | 0.183.x | WebGL 3D hull visualization |
| **Leaflet** | 1.9.x | Geospatial mapping (OpenStreetMap) |
| **Chart.js** | 4.5.x | LSTM bar chart + DBSCAN scatter plot |

### Backend

| Technology | Version | Purpose |
|:---|:---:|:---|
| **Python** | 3.12 | Runtime |
| **FastAPI** | 0.115.x | Async HTTP + WebSocket framework |
| **Uvicorn** | 0.34.x | ASGI server |
| **Pydantic v2** | 2.10.x | Schema validation (17 telemetry sub-models) |
| **NumPy** | 2.2.x | Physics computations & random walks |
| **WebSockets** | 14.1 | Bidirectional telemetry channel |

### Infrastructure

| Technology | Purpose |
|:---|:---|
| **Docker Compose** | One-command multi-container deployment |
| **Node 22 Alpine** | Lightweight frontend container |
| **Python 3.12 Slim** | Minimal backend container |

---

## 📡 WebSocket Protocol

### Connection

```
ws://localhost:8000/ws/telemetry
```

### Frame Rate

**4 Hz** (250ms interval) — configurable via `SAMUDRA_WS_TICK_RATE_MS` environment variable.

### Downstream — Telemetry Frame (Server → Client)

Every 250ms, the backend emits a JSON frame with 17 top-level sections:

```jsonc
{
  "timestamp": 1712937600.123,
  "engine": {
    "rpm": 120.3,
    "fuel_flow_kgh": 485.72,
    "temperature_c": 342.1,
    "power_kw": 8234.5,
    "sfoc_gkwh": 198.3
  },
  "navigation": {
    "speed_knots": 14.52,
    "heading_deg": 225.3,
    "latitude": 15.41,
    "longitude": 73.78
  },
  "environment": {
    "wind_speed_kts": 15.2,
    "wind_direction_deg": 210.4,
    "sea_state": 3,
    "wave_height_m": 1.25
  },
  "physics": {
    "admiralty_coefficient": 532.81,
    "thermal_efficiency": 0.5012,
    "speed_ratio": 1.0014,
    "cubic_law_power_kw": 8100.2,
    "monsoon_resistance_pct": 0.0,
    "monsoon_active": false,
    "pitch_deg": 0.32,
    "roll_deg": -1.24,
    "trim_fuel_penalty_pct": 0.0
  },
  "ais": {
    "nmea_sentence": "!AIVDM,1,1,,A,1P000Oh@IT1svTP2r:43grwb0Eq4,0*01",
    "mmsi": 419001234,
    "cog_deg": 225.3,
    "current_waypoint_index": 3,
    "distance_to_waypoint_nm": 42.7
  },
  "ai_predictive_curve": {
    "biological_roughness_coefficient": 0.089,
    "optimal_fuel_kgh": 462.15,
    "actual_fuel_kgh": 503.74,
    "penalty_pct": 9.0,
    "sea_surface_temp_c": 28.3,
    "hull_age_hours": 12.4,
    "curve": [/* 5 speed-fuel data points */]
  },
  "drl_optimization": {
    "ghost_route_active": true,
    "current_speed_kts": 15.8,
    "recommended_speed_kts": 13.2,
    "speed_reduction_kts": 2.6,
    "fuel_saving_kgh": 142.3,
    "total_fuel_saved_kg": 1247.8,
    "mcr_load_pct": 78.2,
    "in_mcr_band": true,
    "ppo_reward": 0.73
  },
  "cii_segregation": {
    "mission_state": "transit",
    "cii_attained_raw": 12.45,
    "cii_attained_corrected": 8.92,
    "cii_reference": 11.2,
    "cii_rating_raw": "C",
    "cii_rating_corrected": "B",
    "transit_co2_tonnes": 1.847,
    "loiter_co2_tonnes": 0.412
  },
  "sensor_integration": {
    "sensors": {
      "ECDIS": {"status": "OK", "ukc_m": 8.2, "xte_m": 12.5},
      "EMCS": {"status": "OK", "exhaust_temps_c": [320, 318, 325, 322]},
      "FOMS": {"status": "OK", "flow_kgh": 503.7, "quality_idx": 87},
      "WEATHER": {"status": "OK", "baro_trend": "falling", "humidity_pct": 78},
      "VDR": {"status": "RECORDING", "capsule_ok": true}
    },
    "health_pct": 100.0,
    "correlations": {"fuel_quality_index": 87, "xte_corridor_pct": 6.2}
  },
  "predictive_maintenance": {
    "components": {
      "main_engine": {"rul_days": 142, "health": "HEALTHY"},
      "turbocharger": {"rul_days": 67, "health": "WATCH"},
      "fuel_pump": {"rul_days": 201, "health": "HEALTHY"},
      "alternator": {"rul_days": 88, "health": "WATCH"},
      "cooling_system": {"rul_days": 23, "health": "CAUTION"}
    },
    "anomaly_count": 1,
    "next_maintenance": "cooling_system",
    "avg_rul_days": 104.2
  },
  "hull_propulsion": {
    "coating_age_months": 14.2,
    "delta_rr": 0.034,
    "cleaning_roi_positive": true,
    "hybrid_mode": "DIESEL_ONLY",
    "battery_soc_pct": 78.5,
    "electric_motor_kw": 0,
    "fuel_saving_hybrid_pct": 0
  },
  "blind_spots": {
    "cusum_drift": 0.23,
    "drift_alarm": false,
    "micro_climate_zone": "tropical_coastal",
    "ke_spike_detected": false,
    "sync_status": "OK",
    "causal_top_cause": "wave_height",
    "risk_level": "LOW"
  },
  "human_ai_collaboration": {
    "ai_confidence": "HIGH",
    "distribution_shift": false,
    "connectivity_type": "LOCAL",
    "bandwidth_mbps": 100,
    "shap_top_factor": "wave_height",
    "shap_top_contribution": 0.34,
    "solas_override_active": false,
    "nl_advisory": "Maintain current speed. Conditions nominal."
  },
  "eexi_compliance": {
    "eexi_attained": 28.4,
    "eexi_required": 32.1,
    "eexi_margin": 3.7,
    "eexi_compliant": true,
    "cf": 3.114,
    "sfc_gkwh": 190,
    "cii_enhanced_rating": "B",
    "cii_annual_reduction_pct": 2.0,
    "imo_dcs": {"fuel_tonnes": 1847.2, "distance_nm": 12450, "hours_underway": 1820}
  },
  "data_architecture": {
    "dqi_score": 0.91,
    "bus_message_rate_hz": 48,
    "quality_dimensions": {
      "freshness": 0.95, "accuracy": 0.89, "consistency": 0.92, "completeness": 0.88
    },
    "nmea_parse_count": 4200,
    "registered_sensors": 12
  },
  "ai_advisory_mode": true
}
```

### Upstream — Commands (Client → Server)

```jsonc
{ "command": "set_ai_mode", "enabled": true }  // Toggle AI advisory
```

---

## 🚢 Vessel Parameters

| Parameter | Value | Source |
|:---|:---:|:---|
| **Vessel Type** | Offshore Patrol Vessel (OPV) | Indian Coast Guard |
| **Displacement** | 2,350 tonnes | Design specification |
| **Design Speed** | 14.5 knots | Calm-sea nominal |
| **Design Power (MCR)** | 8,500 kW | Maximum Continuous Rating |
| **Fuel Type** | HFO (Heavy Fuel Oil) | Standard marine diesel |
| **LCV** | 42.7 MJ/kg | Lower Calorific Value |
| **CO₂ Factor** | 3.114 t-CO₂/t-fuel | IMO MEPC.364(79) |
| **Fuel Cost** | $520 USD/tonne | Market reference |
| **Fuel Capacity** | 350 tonnes | Operational endurance |
| **Thermal Efficiency** | 48–52% | Marine diesel band |
| **RPM/Speed** | ~8.3 RPM/knot | Fixed-pitch propeller |
| **Patrol Route** | 10 waypoints, Arabian Sea | Mumbai → Lakshadweep → return |
| **MMSI** | 419001234 | AIS identity (MID 419 = India) |

---

## 🏛️ IMO Compliance Framework

SAMUDRA implements compliance monitoring for the following international maritime regulations:

| Regulation | Body | Description | SAMUDRA Module |
|:---|:---:|:---|:---|
| **MARPOL Annex VI** | IMO | Prevention of air pollution from ships | CII engine |
| **MEPC.355(78)** | MEPC | CII correction factors for voyage adjustments | CII segregation |
| **MEPC.364(79)** | MEPC | CO₂ emission factors (C_F = 3.114 for HFO) | Physics engine |
| **MEPC.339(76)** | MEPC | CII reference lines and rating boundaries | CII A–E ratings |
| **MEPC.328(76)** | MEPC | EEXI calculation methodology | EEXI Compliance Engine |
| **MEPC.338(76)** | MEPC | CII annual reduction factors 2023–2030 | Enhanced CII Tracker |
| **MEPC.278(70)** | MEPC | IMO Data Collection System (DCS) reporting | IMO DCS Reporter |
| **IMO DCS** | IMO | Data Collection System for fuel consumption | DCS report button |
| **EEXI** | IMO | Energy Efficiency Existing Ship Index | EEXI Compliance Engine |
| **SOLAS Ch. V** | IMO | Safety of Life at Sea — override panel | SOLAS toggle + audit trail |
| **MIL-STD-3034** | DoD | Reliability-Centered Maintenance | Predictive Maintenance |
| **ISO 19030** | ISO | Hull & propeller performance monitoring | Hull Coating Model |
| **ISO 8217** | ISO | Marine fuel quality specifications | FOMS sensor integration |
| **IEC 61174** | IEC | ECDIS operational requirements | Sensor Integration Hub |
| **IEC 61996** | IEC | VDR performance standards | Sensor Integration Hub |
| **ITU-R M.1371-5** | ITU | AIS technical characteristics | AIVDM encoding |
| **NMEA 0183 v4.11** | NMEA | Marine electronic device interface | Sentence format + parser |
| **IEC 62287-1** | IEC | AIS Class A shipborne equipment | Message Type 1 |
| **Douglas Sea Scale** | WMO | Sea state 0–9 from wave height | Environment frame |

---

## 📈 KPI Catalog (130+)

<details>
<summary><b>Click to expand full KPI listing</b></summary>

### Engine Domain
| # | KPI | Unit | Source |
|:---:|:---|:---:|:---|
| 1 | Engine RPM | rpm | `engine.rpm` |
| 2 | Fuel Flow Rate | kg/h | `engine.fuel_flow_kgh` |
| 3 | Exhaust Gas Temperature | °C | `engine.temperature_c` |
| 4 | Shaft Power | kW | `engine.power_kw` |
| 5 | SFOC | g/kWh | `engine.sfoc_gkwh` |
| 6 | E1 Lube Oil Pressure | bar | Derived (4.8 ± sin) |
| 7 | E1 Coolant Temperature | °C | Derived (82 ± sin) |
| 8 | E2 Lube Oil Pressure | bar | Derived (4.6 ± sin) |
| 9 | E2 Exhaust C3 Temperature | °C | `engine.temperature_c` |
| 10 | LSTM Anomaly MSE | — | Frontend computed |
| 11 | LSTM Anomaly Status | flag | MSE vs threshold |

### Navigation Domain
| # | KPI | Unit | Source |
|:---:|:---|:---:|:---|
| 12 | Speed Over Ground (SOG) | kn | `navigation.speed_knots` |
| 13 | True Heading | ° | `navigation.heading_deg` |
| 14 | Latitude | °N | `navigation.latitude` |
| 15 | Longitude | °E | `navigation.longitude` |
| 16 | Course Over Ground (COG) | ° | `ais.cog_deg` |
| 17 | Current Waypoint Index | — | `ais.current_waypoint_index` |
| 18 | Distance to Waypoint | NM | `ais.distance_to_waypoint_nm` |
| 19 | MMSI | — | `ais.mmsi` |
| 20 | NMEA Sentence | text | `ais.nmea_sentence` |

### Physics & Derived Domain
| # | KPI | Unit | Source |
|:---:|:---|:---:|:---|
| 21 | Admiralty Coefficient | — | `physics.admiralty_coefficient` |
| 22 | Thermal Efficiency | % | `physics.thermal_efficiency` |
| 23 | Speed Ratio (V/V_d) | — | `physics.speed_ratio` |
| 24 | Cubic Law Power (calm) | kW | `physics.cubic_law_power_kw` |
| 25 | Monsoon Resistance | % | `physics.monsoon_resistance_pct` |
| 26 | Monsoon Active | flag | `physics.monsoon_active` |
| 27 | Pitch (Trim) Angle | ° | `physics.pitch_deg` |
| 28 | Roll Angle | ° | `physics.roll_deg` |
| 29 | Trim Fuel Penalty | % | `physics.trim_fuel_penalty_pct` |
| 30 | Froude Number | — | Derived: $V / \sqrt{gL}$ |
| 31 | Sea Margin | % | Derived: $(P_{act} - P_{calm}) / P_{calm}$ |
| 32 | Fuel Range | hours | Derived: capacity / flow |
| 33 | Endurance | days | Derived: range / 24 |
| 34 | Fuel Cost Rate | $/h | Derived: flow × $520/1000 |
| 35 | Carbon Emission Rate | kg-CO₂/h | Derived: flow × 3.114 |

### Environment Domain
| # | KPI | Unit | Source |
|:---:|:---|:---:|:---|
| 36 | Wind Speed | kn | `environment.wind_speed_kts` |
| 37 | Wind Direction | ° | `environment.wind_direction_deg` |
| 38 | Sea State | Douglas 0–9 | `environment.sea_state` |
| 39 | Wave Height | m | `environment.wave_height_m` |
| 40 | Beaufort Scale | 0–12 | Derived from wind speed |
| 41 | Sea Surface Temperature | °C | `ai_predictive_curve.sea_surface_temp_c` |

### AI Biofouling Domain
| # | KPI | Unit | Source |
|:---:|:---|:---:|:---|
| 42 | Biological Roughness Coefficient | — | `ai_predictive_curve.biological_roughness_coefficient` |
| 43 | Optimal Fuel (clean hull) | kg/h | `ai_predictive_curve.optimal_fuel_kgh` |
| 44 | Actual Fuel (fouled hull) | kg/h | `ai_predictive_curve.actual_fuel_kgh` |
| 45 | Biofouling Penalty | % | `ai_predictive_curve.penalty_pct` |
| 46 | Hull Age | hours | `ai_predictive_curve.hull_age_hours` |
| 47 | PINN Curve (5 pts) | array | `ai_predictive_curve.curve` |

### DRL Optimization Domain
| # | KPI | Unit | Source |
|:---:|:---|:---:|:---|
| 48 | Ghost Route Active | flag | `drl_optimization.ghost_route_active` |
| 49 | Current Speed | kn | `drl_optimization.current_speed_kts` |
| 50 | Recommended Speed | kn | `drl_optimization.recommended_speed_kts` |
| 51 | Speed Reduction | kn | `drl_optimization.speed_reduction_kts` |
| 52 | ETA Current | s | `drl_optimization.eta_current_s` |
| 53 | ETA Planned | s | `drl_optimization.eta_planned_s` |
| 54 | Fuel Saving Rate | kg/h | `drl_optimization.fuel_saving_kgh` |
| 55 | Total Fuel Saved | kg | `drl_optimization.total_fuel_saved_kg` |
| 56 | MCR Load | % | `drl_optimization.mcr_load_pct` |
| 57 | MCR Band Compliance | flag | `drl_optimization.in_mcr_band` |
| 58 | PPO Reward | — | `drl_optimization.ppo_reward` |

### CII Compliance Domain
| # | KPI | Unit | Source |
|:---:|:---|:---:|:---|
| 59 | Mission State | enum | `cii_segregation.mission_state` |
| 60 | CII Attained (Raw) | g-CO₂/t·NM | `cii_segregation.cii_attained_raw` |
| 61 | CII Attained (Corrected) | g-CO₂/t·NM | `cii_segregation.cii_attained_corrected` |
| 62 | CII Reference Line | g-CO₂/t·NM | `cii_segregation.cii_reference` |
| 63 | CII Rating (Raw) | A–E | `cii_segregation.cii_rating_raw` |
| 64 | CII Rating (Corrected) | A–E | `cii_segregation.cii_rating_corrected` |
| 65 | Transit CO₂ | tonnes | `cii_segregation.transit_co2_tonnes` |
| 66 | Loiter CO₂ | tonnes | `cii_segregation.loiter_co2_tonnes` |
| 67 | Transit Fuel | tonnes | `cii_segregation.transit_fuel_tonnes` |
| 68 | Loiter Fuel | tonnes | `cii_segregation.loiter_fuel_tonnes` |
| 69 | Transit Distance | NM | `cii_segregation.transit_distance_nm` |
| 70 | Loiter Events | count | `cii_segregation.loiter_events` |
| 71 | Transit Events | count | `cii_segregation.transit_events` |
| 72 | Elapsed Time | hours | `cii_segregation.elapsed_hours` |

### Risk Assessment Domain
| # | KPI | Unit | Source |
|:---:|:---|:---:|:---|
| 73 | Engine Risk Score | 0–100 | Composite (MCR + temp + RPM deviation) |
| 74 | Navigation Risk Score | 0–100 | Composite (sea state + monsoon + waves) |
| 75 | Environmental Risk Score | 0–100 | Composite (wind + sea state + monsoon) |
| 76 | Compliance Risk Score | 0–100 | Composite (CII rating + reference breach) |
| 77 | Hull Risk Score | 0–100 | Composite (biofouling penalty + BRC) |
| 78 | Structural Risk Score | 0–100 | Composite (pitch + roll) |
| 79 | Overall Risk Index | 0–100 | Average of all 6 domains |

### Sensor Integration Domain
| # | KPI | Unit | Source |
|:---:|:---|:---:|:---|
| 80 | Sensor Health | % | `sensor_integration.health_pct` |
| 81 | ECDIS UKC | m | `sensor_integration.sensors.ECDIS.ukc_m` |
| 82 | Cross-Track Error (XTE) | m | `sensor_integration.sensors.ECDIS.xte_m` |
| 83 | Fuel Quality Index | 0–100 | `sensor_integration.correlations.fuel_quality_index` |
| 84 | XTE Corridor % | % | `sensor_integration.correlations.xte_corridor_pct` |
| 85 | VDR Recording Status | flag | `sensor_integration.sensors.VDR.status` |

### Predictive Maintenance Domain
| # | KPI | Unit | Source |
|:---:|:---|:---:|:---|
| 86 | Average RUL | days | `predictive_maintenance.avg_rul_days` |
| 87 | Anomaly Count | count | `predictive_maintenance.anomaly_count` |
| 88 | Next Maintenance Component | name | `predictive_maintenance.next_maintenance` |
| 89 | Main Engine RUL | days | `predictive_maintenance.components.main_engine.rul_days` |
| 90 | Turbocharger RUL | days | `predictive_maintenance.components.turbocharger.rul_days` |
| 91 | Cooling System RUL | days | `predictive_maintenance.components.cooling_system.rul_days` |

### Hull & Hybrid Propulsion Domain
| # | KPI | Unit | Source |
|:---:|:---|:---:|:---|
| 92 | Coating Age | months | `hull_propulsion.coating_age_months` |
| 93 | Hull Fouling ΔR/R | ratio | `hull_propulsion.delta_rr` |
| 94 | Cleaning ROI Positive | flag | `hull_propulsion.cleaning_roi_positive` |
| 95 | Hybrid Drive Mode | enum | `hull_propulsion.hybrid_mode` |
| 96 | Battery SOC | % | `hull_propulsion.battery_soc_pct` |
| 97 | Electric Motor Power | kW | `hull_propulsion.electric_motor_kw` |
| 98 | Hybrid Fuel Saving | % | `hull_propulsion.fuel_saving_hybrid_pct` |

### Blind Spots Domain
| # | KPI | Unit | Source |
|:---:|:---|:---:|:---|
| 99 | CUSUM Drift | σ | `blind_spots.cusum_drift` |
| 100 | Drift Alarm | flag | `blind_spots.drift_alarm` |
| 101 | Micro-Climate Zone | enum | `blind_spots.micro_climate_zone` |
| 102 | KE Spike Detected | flag | `blind_spots.ke_spike_detected` |
| 103 | Sensor Sync Status | enum | `blind_spots.sync_status` |
| 104 | Causal Top Cause | name | `blind_spots.causal_top_cause` |
| 105 | Blind Spot Risk Level | LOW/MED/HI | `blind_spots.risk_level` |

### Human-AI Collaboration Domain
| # | KPI | Unit | Source |
|:---:|:---|:---:|:---|
| 106 | AI Confidence Tier | HIGH/MED/LOW | `human_ai_collaboration.ai_confidence` |
| 107 | Distribution Shift Detected | flag | `human_ai_collaboration.distribution_shift` |
| 108 | Connectivity Type | enum | `human_ai_collaboration.connectivity_type` |
| 109 | Bandwidth | Mbps | `human_ai_collaboration.bandwidth_mbps` |
| 110 | SHAP Top Factor | name | `human_ai_collaboration.shap_top_factor` |
| 111 | SHAP Top Contribution | ratio | `human_ai_collaboration.shap_top_contribution` |
| 112 | SOLAS Override Active | flag | `human_ai_collaboration.solas_override_active` |
| 113 | NL Advisory Text | text | `human_ai_collaboration.nl_advisory` |

### EEXI & Enhanced CII Domain
| # | KPI | Unit | Source |
|:---:|:---|:---:|:---|
| 114 | EEXI Attained | g-CO₂/t·NM | `eexi_compliance.eexi_attained` |
| 115 | EEXI Required | g-CO₂/t·NM | `eexi_compliance.eexi_required` |
| 116 | EEXI Margin | g-CO₂/t·NM | `eexi_compliance.eexi_margin` |
| 117 | EEXI Compliant | flag | `eexi_compliance.eexi_compliant` |
| 118 | CII Enhanced Rating | A–E | `eexi_compliance.cii_enhanced_rating` |
| 119 | CII Annual Reduction | %/yr | `eexi_compliance.cii_annual_reduction_pct` |
| 120 | IMO DCS Fuel Total | tonnes | `eexi_compliance.imo_dcs.fuel_tonnes` |
| 121 | IMO DCS Distance | NM | `eexi_compliance.imo_dcs.distance_nm` |
| 122 | IMO DCS Hours Underway | h | `eexi_compliance.imo_dcs.hours_underway` |

### Data Architecture Domain
| # | KPI | Unit | Source |
|:---:|:---|:---:|:---|
| 123 | Data Quality Index (DQI) | 0–1 | `data_architecture.dqi_score` |
| 124 | Bus Message Rate | Hz | `data_architecture.bus_message_rate_hz` |
| 125 | DQ Freshness | 0–1 | `data_architecture.quality_dimensions.freshness` |
| 126 | DQ Accuracy | 0–1 | `data_architecture.quality_dimensions.accuracy` |
| 127 | DQ Consistency | 0–1 | `data_architecture.quality_dimensions.consistency` |
| 128 | DQ Completeness | 0–1 | `data_architecture.quality_dimensions.completeness` |
| 129 | NMEA Parse Count | count | `data_architecture.nmea_parse_count` |
| 130 | Registered Sensors | count | `data_architecture.registered_sensors` |

</details>

---

## 🐳 Docker Deployment

### One-Command Launch

```bash
docker compose up --build
```

This starts both services:

| Service | Container | Port | Health Check |
|:---|:---|:---:|:---|
| **Backend** | `samudra-backend` | 8000 | `GET /health` every 10s |
| **Frontend** | `samudra-frontend` | 3000 | Depends on backend health |

### Resource Limits

```yaml
deploy:
  resources:
    limits:
      memory: 2G  # Backend (physics engine + NumPy)
```

### Environment Variables

| Variable | Default | Description |
|:---|:---:|:---|
| `SAMUDRA_FRONTEND_PORT` | 3000 | Frontend dev server port |
| `SAMUDRA_BACKEND_PORT` | 8000 | Backend API port |
| `SAMUDRA_WS_TICK_RATE_MS` | 250 | Telemetry frame interval (ms) |

---

## 💻 Local Development

### Prerequisites

- **Python** 3.12+
- **Node.js** 22+
- **npm** 10+

### Quick Start (PowerShell)

```powershell
# Clone the repository
git clone https://github.com/shubro18202758/SAMUDRA.git
cd SAMUDRA

# Option 1: Use the orchestrator script
.\start.ps1

# Option 2: Manual startup
# Terminal 1 — Backend
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# Terminal 2 — Frontend
cd frontend
npm install
npm run dev
```

### Quick Start (Bash)

```bash
# Clone and launch
git clone https://github.com/shubro18202758/SAMUDRA.git
cd SAMUDRA
chmod +x start.sh
./start.sh
```

### Access Points

| Service | URL |
|:---|:---|
| **Dashboard** | http://localhost:3000 |
| **API Health** | http://localhost:8000/health |
| **API Docs** | http://localhost:8000/docs |
| **Latest Telemetry** | http://localhost:8000/api/v1/telemetry/latest |
| **Telemetry History** | http://localhost:8000/api/v1/telemetry/history?last=60 |
| **Vessel Status** | http://localhost:8000/api/v1/vessel/status |
| **Sensor Integration** | http://localhost:8000/api/v1/sensors/status |
| **Predictive Maintenance** | http://localhost:8000/api/v1/maintenance/status |
| **Hull & Propulsion** | http://localhost:8000/api/v1/hull/status |
| **Blind Spots** | http://localhost:8000/api/v1/blindspots/status |
| **Human-AI Collab** | http://localhost:8000/api/v1/humanai/status |
| **EEXI Compliance** | http://localhost:8000/api/v1/eexi/status |
| **Data Bus Status** | http://localhost:8000/api/v1/databus/status |

### Build for Production

```bash
cd frontend
npx vite build
# Output → frontend/dist/ (0.93 kB HTML + 47.5 kB CSS + 1,040 kB JS)
```

---

## 🧪 Testing Protocol — DISC 14

Per the Indian Coast Guard challenge specification, the following testing sequence is mandated:

| # | Test Phase | Description | SAMUDRA Implementation |
|:---:|:---|:---|:---|
| 1 | **Baseline Sea Trial** | Disabled AI — pure physics-only operation | AI Advisory Mode toggle → OFF. DRL disabled, PINN reports 0% penalty, CII still tracks |
| 2 | **AI Optimised Sea Trial** | Full AI suite — compare against baseline | AI Advisory Mode → ON. Ghost Route active, biofouling tracked, full optimization |
| 3 | **Voyage & Adaptive Learning** | Long-duration voyage with evolving conditions | Monsoon FSM + BRC growth over time + DRL cumulative savings |
| 4 | **Safety & Compliance Test** | IMO regulation adherence under stress | CII A–E ratings, MEPC.355(78) correction factors, MARPOL Annex VI |
| 5 | **Fault Tolerance Test** | System degradation behavior | WebSocket reconnect, data buffering, graceful disconnect |
| 6 | **Crew Usability Trial** | Operator interface assessment | F-key navigation, alert system, risk matrix, intuitive gauges |
| 7 | **Safety Override Validation** | SOLAS override functionality | SOLAS toggle (DISARMED ↔ ARMED) with system alert |

### AI ON vs. AI OFF — Comparative Analysis

```
┌──────────────────────────────────────────────────────────────┐
│  Metric                     │  AI OFF (Baseline) │  AI ON    │
├─────────────────────────────┼────────────────────┼───────────┤
│  Biofouling Penalty         │  Not tracked       │  7–20%    │
│  Ghost Route Activation     │  Never             │  Automatic│
│  SFTW Prevention            │  None              │  JIT      │
│  MCR Band Targeting         │  Random            │  70–85%   │
│  CII Correction             │  Raw only          │  Corrected│
│  Fuel Saving Rate           │  0 kg/h            │  Variable │
│  DRL Recommended Speed      │  = Current speed   │  Optimized│
│  PPO Reward Signal          │  0                 │  Active   │
└──────────────────────────────────────────────────────────────┘
```

---

## 🌍 Market & Use Cases

### Target Sectors

| Sector | Fleet Size | Key Pain Point | SAMUDRA Value |
|:---|:---:|:---|:---|
| **Indian Coast Guard** | 200+ vessels | Fuel is #1 operational expense | Real-time optimization + compliance |
| **Indian Navy** | 150+ ships | Multi-mission fuel allocation | CII segregation for tactical ops |
| **Commercial Shipping** | 50,000+ global | IMO 2023 CII ratings | Automated A–E rating tracking |
| **Cruise Lines** | 300+ ships | Environmental pressure | Carbon footprint reduction |
| **Offshore Oil & Gas** | 10,000+ vessels | Remote high-cost operations | Predictive maintenance |
| **Fleet Operators** | Variable | Multi-vessel optimization | Centralized fuel analytics |
| **Regulatory Agencies** | — | Compliance enforcement | Transparent DCS reporting |

### Return on Investment

A typical OPV burning 11.6 tonnes/day of HFO at $520/tonne:

| Scenario | Daily Consumption | Daily Cost | Annual Cost |
|:---|:---:|:---:|:---:|
| **No Optimization** | 11.6 t/day | $6,032 | $2.2M |
| **10% Speed Reduction** | 8.4 t/day | $4,383 | $1.6M |
| **SAMUDRA (DRL + PINN)** | ~7.8 t/day | $4,056 | $1.48M |
| **Annual Savings** | — | — | **~$720K** |

> *Estimates based on cubic law reduction + biofouling awareness + SFTW prevention. Actual savings depend on operational profile.*

---

## 📚 References & Standards

### IMO Regulatory Documents

1. **MEPC.355(78)** — 2022 Guidelines on the CII and CII rating, including correction factors and voyage adjustments
2. **MEPC.364(79)** — CO₂ emission factors for marine fuels ($C_F = 3.114$ for HFO)
3. **MEPC.339(76)** — CII reference lines and rating boundaries (A–E)
4. **MARPOL Annex VI** — Regulations for the Prevention of Air Pollution from Ships
5. **IMO DCS** — Data Collection System for fuel oil consumption reporting

### Technical Standards

6. **ITU-R M.1371-5** — Technical characteristics for AIS using TDMA in VHF maritime mobile band
7. **NMEA 0183 v4.11** — Standard for Interfacing Marine Electronic Devices
8. **IEC 62287-1** — AIS Part 1: Class A shipborne equipment
9. **WMO Douglas Sea Scale** — Sea state description and wave height classification

### Naval Architecture

10. **Admiralty Coefficient Method** — Classical power prediction based on displacement and speed
11. **Holtrop-Mennen Method** — (Reference) Statistical resistance prediction for displacement vessels
12. **Froude Number Analysis** — Wave-making resistance regime identification: $Fr = V / \sqrt{gL}$

### AI/ML Methods

13. **Raissi et al. (2019)** — "Physics-Informed Neural Networks" — *Journal of Computational Physics*
14. **Schulman et al. (2017)** — "Proximal Policy Optimization Algorithms" — *arXiv:1707.06347*
15. **Ester et al. (1996)** — "A Density-Based Algorithm for Discovering Clusters (DBSCAN)" — *KDD-96*
16. **Hochreiter & Schmidhuber (1997)** — "Long Short-Term Memory" — *Neural Computation*
17. **Vincent et al. (2008)** — "Extracting and Composing Robust Features with Denoising Autoencoders" — *ICML*

---

## 🤝 Team

Built for **Indian Coast Guard DISC 14 Challenge — Problem Statement 77**

> *Fuel Consumption Optimization Using AI-Based Tools*

---

## 📄 License

This project is developed as a prototype for the DISC 14 Challenge. All rights reserved.

---

<div align="center">

```
    ███████╗ █████╗ ███╗   ███╗██╗   ██╗██████╗ ██████╗  █████╗
    ██╔════╝██╔══██╗████╗ ████║██║   ██║██╔══██╗██╔══██╗██╔══██╗
    ███████╗███████║██╔████╔██║██║   ██║██║  ██║██████╔╝███████║
    ╚════██║██╔══██║██║╚██╔╝██║██║   ██║██║  ██║██╔══██╗██╔══██║
    ███████║██║  ██║██║ ╚═╝ ██║╚██████╔╝██████╔╝██║  ██║██║  ██║
    ╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝
```

**Project SAMUDRA** — Shipboard Autonomous Maritime Unified Digital Real-time Analytics

*Every knot counts. Every tonne matters. $P \propto V^3$*

</div>
