# SAMUDRA — Frontend ↔ Backend Mapping Audit Report

**Date:** 2026-04-12  
**Scope:** Complete line-by-line audit of every frontend UI element against backend telemetry payload  
**Result:** ✅ ALL MAPPINGS VERIFIED — No broken bindings found

---

## 1. Backend Payload Structure (Verified Live)

The WebSocket at `ws://localhost:8000/ws/telemetry` (4 Hz) sends a `TelemetryFrame` with **10 top-level keys**:

| Key | Pydantic Model | Fields |
|-----|---------------|--------|
| `timestamp` | `float` | Unix epoch seconds |
| `engine` | `EngineFrame` | rpm, fuel_flow_kgh, temperature_c, power_kw, sfoc_gkwh |
| `navigation` | `NavigationFrame` | speed_knots, heading_deg, latitude, longitude |
| `environment` | `EnvironmentFrame` | wind_speed_kts, wind_direction_deg, sea_state, wave_height_m |
| `physics` | `PhysicsFrame` | admiralty_coefficient, thermal_efficiency, speed_ratio, cubic_law_power_kw, monsoon_resistance_pct, monsoon_active, pitch_deg, roll_deg, trim_fuel_penalty_pct |
| `ais` | `AISFrame` | nmea_sentence, mmsi, cog_deg, current_waypoint_index, distance_to_waypoint_nm |
| `ai_predictive_curve` | `AIPredictiveCurveFrame` | biological_roughness_coefficient, optimal_fuel_kgh, actual_fuel_kgh, penalty_pct, sea_surface_temp_c, hull_age_hours, curve[5] |
| `drl_optimization` | `DRLOptimizationFrame` | ghost_route_active, current_speed_kts, recommended_speed_kts, speed_reduction_kts, eta_current_s, eta_planned_s, arrival_delta_s, fuel_saving_kgh, total_fuel_saved_kg, mcr_load_pct, recommended_mcr_load_pct, in_mcr_band, ppo_reward |
| `cii_segregation` | `CIISegregationFrame` | mission_state, cii_attained_raw, cii_attained_corrected, cii_reference, cii_rating_raw, cii_rating_corrected, transit_co2_tonnes, loiter_co2_tonnes, transit_fuel_tonnes, loiter_fuel_tonnes, transit_distance_nm, loiter_events, transit_events, elapsed_hours |
| `ai_advisory_mode` | `bool` | AI PINN/DRL toggle |

## 2. Frontend TypeScript Interface Match

The `TelemetryFrame` interface (App.svelte lines 9–20) **exactly matches** every backend Pydantic model field name, type, and nesting structure. Verified field-by-field.

## 3. UI Element ↔ Backend Mapping (All Pages)

### Data Ticker (18 segments) ✅
SOG, FUEL, PWR, RPM, PPO, SFOC, TEMP, HDG, ETA-WP, CII, Fn, SEA-MRG, CO₂, ENDURE, RANGE, ADM-C, WIND, BIO — all correctly access `telemetry.*` and `derived.*`

### KPI Ribbon (14 cards + sparklines) ✅
SOG, RPM, FUEL, POWER, SFOC, η, TEMP, MCR, BIO, CII, Fn, WAVE, CO₂, ADM — each with 120-point sparkline buffer

### Voyage Progress Bar ✅
`ais.current_waypoint_index` / waypoint count → `voyPct()` function (line 561)

### Alert Banners (5 conditions) ✅
Monsoon (`physics.monsoon_active`), Ghost Route (`drl_optimization.ghost_route_active`), Trim penalty (`physics.trim_fuel_penalty_pct > 3`), CII D/E (`cii_segregation.cii_rating_corrected`), Biofouling (`ai_predictive_curve.penalty_pct > 8`)

### Override Bar ✅
MMSI (`ais.mmsi`), COG (`ais.cog_deg`), AI toggle sends `{command:'set_ai_mode',enabled:bool}` via WebSocket

### Gauge Strip (12 SVG gauges) ✅
MCR, THERMAL, CII, BIO-F, SPD-R, WIND, PPO-R, FUEL-E, PWR-M, SEA-ST, FROUDE, ENDURE — all computed from `telemetry.*` and `derived.*`

### Charts (5 Chart.js canvases) ✅
1. PINN Biofouling Curve — `ai_predictive_curve.curve[]`
2. Real-Time Telemetry — rolling SOG/Fuel/Power
3. Speed-Power Cubic — V³ law + operating point
4. Efficiency — Fuel Eff% + Thermal η%
5. Environmental — Wind/Wave/Sea State

### 3D Hull Digital Twin (Three.js) ✅
52×32 parametric hull, superstructure, nav lights, propeller animation (`engine.rpm`), bow wave/wake particles (`navigation.speed_knots`), sea surface, pitch/roll from `physics.pitch_deg`/`physics.roll_deg`

### AIS Tactical Map (Leaflet) ✅
10-waypoint Arabian Sea patrol route, ship icon at `navigation.latitude`/`.longitude`, heading rotation, track trail, range rings, ghost route overlay from `drl_optimization`

### Quad Row 1 ✅
- **CII Tactical Compliance** — 14 fields from `cii_segregation.*`
- **DRL PPO Optimizer** — 13 fields from `drl_optimization.*` + `derived.loadBalance`
- **Risk Assessment** — 6 categories computed in `derived.risk.*`
- **Fuel Economics** — 10 rows from `derived.*`

### Quad Row 2 ✅
- **Propulsion Analysis** — 9 rows from `physics.*` + `derived.*`
- **Emissions Tracker** — SOx/NOx/PM computed from fuel flow, CO₂ from `CARBON_FACTOR`
- **Environmental Chart** — Chart 5 + Beaufort tag
- **Performance Benchmark** — 9 rows comparing against `DESIGN_SPEED_KTS`/`DESIGN_POWER_KW`

### Data Cards (8 panels, 48 data rows) ✅
ENGINE, NAVIGATION, ENVIRONMENT, HYDRODYNAMICS, BIOFOULING, DRL DETAIL, VOYAGE ANALYTICS, MACHINERY HEALTH — all correctly mapped

### LSTM Anomaly Detector ✅
Synthetic MSE from RPM + temperature deviation, threshold comparison, sparkline, predictive days estimate

### Twin Engine Status ✅
PORT/STBD fault state computed from RPM/temp thresholds + MCR band, prop sync status

### Wind Compass (SVG) ✅
Heading line (`navigation.heading_deg`), wind arrow (`environment.wind_direction_deg`), Beaufort scale

### Stability Indicators ✅
Pitch, Roll, Trim Fuel Δ, Wave Height, Sea State, GM estimate, Structural Risk — all from `physics.*`, `environment.*`, `derived.risk.structural`

### Status Bar (11 items) ✅
WS state, FPS, Frames, Latency, AI mode, Mission state, Risk, Fuel, Endurance, CII, Version

### Alerts Sidebar ✅
Severity counts, alert list with `sevIcon()` (line 229), diagnostics panel

## 4. Bidirectional Communication ✅

| Direction | Mechanism | Data |
|-----------|-----------|------|
| Backend → Frontend | WebSocket frames at 4 Hz | Full `TelemetryFrame` JSON |
| Frontend → Backend | WebSocket command | `{command:'set_ai_mode', enabled: bool}` |
| Backend → Frontend | REST GET | `/health`, `/api/v1/telemetry/latest`, `/api/v1/telemetry/history?last=N`, `/api/v1/vessel/status` |

## 5. Null Safety ✅

Entire template wrapped in `{#if telemetry && derived}...{:else}Loading screen{/if}` — prevents any null access.

## 6. Static/Hardcoded Values (By Design, Not Bugs)

| Element | Value | Notes |
|---------|-------|-------|
| Draft | FWD 4.2m / AFT 5.1m | OPV design draft |
| GM computation | `1.2 - |roll|*0.02` | Simplified metacentric height |
| CPP pitch | 87.3° | Display placeholder |
| Prop sync | SYNCHRONIZED | Static display |
| ECA zone | OUTSIDE | Static for Arabian Sea patrol |
| SOLAS override | DISARMED | Safety default |
| Edge config | AES-256, Savitzky-Golay | Display constants |

## 7. Build Status

```
✓ built in 6.45s — 119 modules, 0 errors
  Only warnings: unused CSS selector ".ro-v small"
```

## 8. Live Verification

- Backend: ✅ Running on port 8000 (uptime 2+ hours)
- Frontend: ✅ Running on port 3000
- WebSocket: ✅ Frames received with all 10 top-level keys
- REST `/health`: ✅ `status: operational`, `history_depth: 300`
