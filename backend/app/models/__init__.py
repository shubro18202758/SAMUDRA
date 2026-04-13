"""
models/telemetry.py — Strongly-Typed Telemetry Payload
======================================================
Pydantic v2 models that enforce schema validation on every frame emitted
over the WebSocket.  Serialised with ``model.model_dump(mode="json")``.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class EngineFrame(BaseModel):
    """Engine Monitoring and Control System (EMCS) data."""

    rpm: float = Field(..., ge=0, description="Engine revolutions per minute")
    fuel_flow_kgh: float = Field(
        ..., ge=0, description="Fuel flow rate in kg/h"
    )
    temperature_c: float = Field(..., description="Exhaust gas temperature °C")
    power_kw: float = Field(
        ..., ge=0, description="Shaft power delivered in kW"
    )
    sfoc_gkwh: float = Field(
        ..., ge=0, description="Specific Fuel Oil Consumption in g/kWh"
    )


class NavigationFrame(BaseModel):
    """Automatic Identification System (AIS) navigation data."""

    speed_knots: float = Field(
        ..., ge=0, le=30, description="Speed Over Ground in knots"
    )
    heading_deg: float = Field(
        ..., ge=0, lt=360, description="True heading in degrees"
    )
    latitude: float = Field(
        ..., ge=-90, le=90, description="WGS-84 latitude"
    )
    longitude: float = Field(
        ..., ge=-180, le=180, description="WGS-84 longitude"
    )


class EnvironmentFrame(BaseModel):
    """Meteorological / oceanographic overlay."""

    wind_speed_kts: float = Field(
        ..., ge=0, description="Wind speed in knots"
    )
    wind_direction_deg: float = Field(
        ..., ge=0, lt=360, description="Wind direction in degrees"
    )
    sea_state: int = Field(
        ..., ge=0, le=9, description="Douglas sea-state scale 0–9"
    )
    wave_height_m: float = Field(
        ..., ge=0, description="Significant wave height in metres"
    )


class PhysicsFrame(BaseModel):
    """Derived physical quantities for verification / diagnostics."""

    admiralty_coefficient: float = Field(
        ..., description="Ac = Δ^(2/3)·V³/P — should stay ~constant in calm sea"
    )
    thermal_efficiency: float = Field(
        ..., ge=0.0, le=1.0, description="Marine diesel η_thermal [0.48–0.52]"
    )
    speed_ratio: float = Field(
        ..., ge=0.0, description="V / V_design — cubic law input"
    )
    cubic_law_power_kw: float = Field(
        ..., ge=0.0, description="P_calm before monsoon modifier"
    )
    monsoon_resistance_pct: float = Field(
        ..., ge=0.0, description="Added resistance % from sea state"
    )
    monsoon_active: bool = Field(
        ..., description="Whether monsoon burst is active"
    )
    pitch_deg: float = Field(
        ..., description="Vessel trim angle in degrees (+ stern down)"
    )
    roll_deg: float = Field(
        ..., description="Vessel roll angle in degrees (+ starboard down)"
    )
    trim_fuel_penalty_pct: float = Field(
        ..., ge=0.0, le=5.0,
        description="Fuel penalty % from non-optimal trim",
    )


class AISFrame(BaseModel):
    """AIS / NMEA 0183 position report (Message Type 1)."""

    nmea_sentence: str = Field(
        ..., description="Raw !AIVDM sentence (ITU-R M.1371-5 Type 1)"
    )
    mmsi: int = Field(..., description="Maritime Mobile Service Identity")
    cog_deg: float = Field(
        ..., ge=0.0, lt=360.0, description="Course Over Ground in degrees"
    )
    current_waypoint_index: int = Field(
        ..., ge=0, description="Index of next target waypoint"
    )
    distance_to_waypoint_nm: float = Field(
        ..., ge=0.0, description="Distance to next waypoint in nautical miles"
    )


class CurvePoint(BaseModel):
    """Single data point on the PINN-predicted fuel curve."""

    speed_kts: float = Field(..., description="Speed in knots (10–20 kn)")
    optimal_fuel_kgh: float = Field(
        ..., ge=0.0, description="Clean-hull fuel burn at this speed (kg/h)"
    )
    actual_fuel_kgh: float = Field(
        ..., ge=0.0, description="Biofouled fuel burn at this speed (kg/h)"
    )
    penalty_pct: float = Field(
        ..., description="Biofouling penalty percentage"
    )


class AIPredictiveCurveFrame(BaseModel):
    """PINN surrogate output — biofouling drag and predictive fuel curve."""

    biological_roughness_coefficient: float = Field(
        ..., ge=0.0, description="BRC — hull roughness [0.07–0.20]"
    )
    optimal_fuel_kgh: float = Field(
        ..., ge=0.0, description="Clean-hull fuel burn at current speed (kg/h)"
    )
    actual_fuel_kgh: float = Field(
        ..., ge=0.0, description="Biofouled fuel burn at current speed (kg/h)"
    )
    penalty_pct: float = Field(
        ..., description="Current biofouling penalty %"
    )
    sea_surface_temp_c: float = Field(
        ..., description="Sea-surface temperature driving fouling growth (°C)"
    )
    hull_age_hours: float = Field(
        ..., ge=0.0, description="Simulated hull age since cold-start (hours)"
    )
    curve: list[CurvePoint] = Field(
        ..., min_length=5, max_length=5,
        description="5-point PINN fuel curve across 10–20 kn"
    )


class DRLOptimizationFrame(BaseModel):
    """DRL Voyage Optimiser — PPO agent Ghost Route output.

    Mocks a Proximal Policy Optimization (PPO) agent that computes
    Just-In-Time (JIT) arrival speed to prevent Sail-Fast-Then-Wait
    (SFTW) behaviour.  The recommended speed keeps the engine in the
    peak thermal efficiency band: 70 %–85 % of MCR (8,500 kW).

    PPO Reward:
        R(s,a) = w₁·(-fuel) + w₂·(-|ETA_δ|) + w₃·(-weather) + w₄·MCR_bonus
    """

    ghost_route_active: bool = Field(
        ..., description="True when vessel is projected to arrive early (SFTW detected)"
    )
    current_speed_kts: float = Field(
        ..., ge=0, description="Current Speed Over Ground (knots)"
    )
    recommended_speed_kts: float = Field(
        ..., ge=0, description="JIT optimal speed keeping 70–85 % MCR (knots)"
    )
    speed_reduction_kts: float = Field(
        ..., ge=0, description="Δ speed to shed for JIT arrival (knots)"
    )
    eta_current_s: float = Field(
        ..., ge=0, description="ETA at current speed (seconds)"
    )
    eta_planned_s: float = Field(
        ..., ge=0, description="Planned ETA at design speed (seconds)"
    )
    arrival_delta_s: float = Field(
        ..., description="Time early (+) or late (-) vs plan (seconds)"
    )
    fuel_saving_kgh: float = Field(
        ..., ge=0, description="Instantaneous fuel saving if Ghost Route adopted (kg/h)"
    )
    total_fuel_saved_kg: float = Field(
        ..., ge=0, description="Cumulative fuel saved by GR advice (kg)"
    )
    mcr_load_pct: float = Field(
        ..., ge=0, description="Current engine load as % of MCR"
    )
    recommended_mcr_load_pct: float = Field(
        ..., ge=0, description="Recommended engine load as % of MCR"
    )
    in_mcr_band: bool = Field(
        ..., description="True if recommended load is within 70–85 % MCR"
    )
    ppo_reward: float = Field(
        ..., description="PPO reward signal R(s,a) — higher is better"
    )


class CIISegregationFrame(BaseModel):
    """CII Tactical Segregation — MEPC.355(78) correction factors.

    Attained CII = (ΣFC_j · C_Fj) / (Capacity · D_t)

    where FC = fuel (tonnes), C_F = 3.114 (HFO), Capacity = DWT,
    D_t = distance (NM).  Mission state classified by DBSCAN-inspired
    speed–power clustering:
      - transit:          SOG ≥ 4.0 kn
      - tactical_loiter:  SOG < 4.0 kn AND power > 5 % MCR
      - idle:             SOG < 4.0 kn AND power ≤ 5 % MCR (excluded)
    """

    mission_state: str = Field(
        ..., description="Current state: transit | tactical_loiter | idle"
    )
    cii_attained_raw: float = Field(
        ..., ge=0, description="Attained CII — all fuel (g-CO₂/DWT·NM)"
    )
    cii_attained_corrected: float = Field(
        ..., ge=0, description="Attained CII — transit-only, MEPC.355(78) corrected"
    )
    cii_reference: float = Field(
        ..., ge=0, description="CII reference line (g-CO₂/DWT·NM)"
    )
    cii_rating_raw: str = Field(
        ..., description="IMO rating band A–E (raw)"
    )
    cii_rating_corrected: str = Field(
        ..., description="IMO rating band A–E (corrected)"
    )
    transit_co2_tonnes: float = Field(
        ..., ge=0, description="Cumulative transit CO₂ (tonnes)"
    )
    loiter_co2_tonnes: float = Field(
        ..., ge=0, description="Cumulative loiter CO₂ (tonnes)"
    )
    transit_fuel_tonnes: float = Field(
        ..., ge=0, description="Cumulative transit fuel (tonnes)"
    )
    loiter_fuel_tonnes: float = Field(
        ..., ge=0, description="Cumulative loiter fuel (tonnes)"
    )
    transit_distance_nm: float = Field(
        ..., ge=0, description="Cumulative transit distance (NM)"
    )
    loiter_events: int = Field(
        ..., ge=0, description="Number of ticks classified as tactical loiter"
    )
    transit_events: int = Field(
        ..., ge=0, description="Number of ticks classified as transit"
    )
    elapsed_hours: float = Field(
        ..., ge=0, description="Total simulation elapsed time (hours)"
    )


class TelemetryFrame(BaseModel):
    """Top-level frame broadcast over WS at 250 ms intervals."""

    timestamp: float = Field(..., description="Unix epoch seconds")
    engine: EngineFrame
    navigation: NavigationFrame
    environment: EnvironmentFrame
    physics: PhysicsFrame
    ais: AISFrame
    ai_predictive_curve: AIPredictiveCurveFrame
    drl_optimization: DRLOptimizationFrame
    cii_segregation: CIISegregationFrame
    ai_advisory_mode: bool = Field(
        True, description="True when AI PINN/DRL systems are active"
    )
    # ---- Phase 4: 7-Gap Overhaul Frames (passthrough dicts) ----
    sensor_integration: dict = Field(
        default_factory=dict, description="Sensor Integration Hub output"
    )
    predictive_maintenance: dict = Field(
        default_factory=dict, description="Predictive Maintenance Engine output"
    )
    hull_propulsion: dict = Field(
        default_factory=dict, description="Hull Improvement & Hybrid Propulsion output"
    )
    blind_spots: dict = Field(
        default_factory=dict, description="Systemic Blind Spot Detection output"
    )
    human_ai_collaboration: dict = Field(
        default_factory=dict, description="Human-AI Collaboration output"
    )
    eexi_compliance: dict = Field(
        default_factory=dict, description="EEXI & Enhanced CII Compliance output"
    )
    data_architecture: dict = Field(
        default_factory=dict, description="Data Architecture & Quality output"
    )
