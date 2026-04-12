"""
physics/hydrodynamics.py — First-Principles Maritime Hydrodynamic Simulator
=============================================================================
Implements the core naval architecture equations governing an Offshore Patrol
Vessel (OPV) at 2,350 tonnes displacement.

Reference Equations
-------------------
1. **Admiralty Coefficient**:
       Ac = Δ^(2/3) · V³ / P
   where Δ = displacement (tonnes), V = speed (knots), P = shaft power (kW).

2. **Cubic Law of Propulsive Power**:
       P ∝ V³
   A 10 % speed increase yields a (1.10)³ = 1.331 → 33.1 % power increase.

3. **Marine Diesel Thermal Efficiency**:
       η_thermal ∈ [0.48, 0.52]   (48–52 %)
   Fuel energy → shaft power conversion ≈ 43 %, with ~57 % lost to heat/friction.

4. **Monsoon Sea-State Resistance Modifier**:
   Wave heights 3–5 m impose a 30–60 % added resistance, modelled as a
   multiplicative surge on the propulsive power at constant speed.

Author : SAMUDRA Backend — Phase 2
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field

import numpy as np

from app.physics.ais_navigation import AISNavigator, MMSI
from app.physics.biofouling import BiofoulingSurrogate
from app.physics.drl_optimizer import DRLVoyageOptimizer
from app.physics.cii_segregation import CIISegregationEngine

# =============================================================================
# Vessel Constants — Indian Coast Guard OPV Class
# =============================================================================
DISPLACEMENT_TONNES = 2_350.0                # Δ (tonnes)
DISPLACEMENT_TWO_THIRDS = DISPLACEMENT_TONNES ** (2.0 / 3.0)  # Δ^(2/3)

# Nominal operating point (calm sea, design speed)
DESIGN_SPEED_KTS = 14.5                      # V_design (knots)
DESIGN_SHAFT_POWER_KW = 8_500.0              # P_design (kW)

# Admiralty Coefficient — derived once from the design operating point
#   Ac = Δ^(2/3) · V_design³ / P_design
ADMIRALTY_COEFFICIENT: float = (
    DISPLACEMENT_TWO_THIRDS * (DESIGN_SPEED_KTS ** 3) / DESIGN_SHAFT_POWER_KW
)

# Marine diesel thermal-efficiency band
THERMAL_EFFICIENCY_MIN = 0.48
THERMAL_EFFICIENCY_MAX = 0.52

# Lower Calorific Value (LCV) of Heavy Fuel Oil — MJ/kg
LCV_HFO_MJ_PER_KG = 42.7

# Monsoon sea-state resistance envelope
MONSOON_WAVE_MIN_M = 3.0
MONSOON_WAVE_MAX_M = 5.0
MONSOON_RESISTANCE_MIN = 0.30   # +30 % added resistance
MONSOON_RESISTANCE_MAX = 0.60   # +60 % added resistance

# RPM ↔ speed affine mapping (approximation for fixed-pitch propeller)
RPM_PER_KNOT = 8.3              # ~120 RPM at 14.5 kn → 8.3 RPM/kn


# =============================================================================
# Smoothed Random Walk — Gaussian-kernel approach
# =============================================================================
class SmoothedRandomWalk:
    """Produces a smooth, physically plausible wander around a mean value.

    Uses a first-order exponential moving average (EMA) on Gaussian increments,
    equivalent to a Gaussian-smoothed random walk.  The smoothing factor ``alpha``
    controls bandwidth (lower → smoother).  A mean-reversion spring constant
    prevents unbounded drift.
    """

    def __init__(
        self,
        mean: float,
        std: float,
        alpha: float = 0.04,
        reversion: float = 0.02,
    ) -> None:
        self._mean = mean
        self._std = std
        self._alpha = alpha          # EMA smoothing weight (0, 1]
        self._reversion = reversion  # mean-reversion spring constant
        self._value = mean

    def step(self, rng: np.random.Generator) -> float:
        """Advance one tick and return the new smoothed value."""
        noise = rng.normal(0.0, self._std)
        # Mean-reversion pull + Gaussian-smoothed innovation
        pull = self._reversion * (self._mean - self._value)
        self._value += self._alpha * (noise + pull)
        return self._value

    @property
    def value(self) -> float:
        return self._value


# =============================================================================
# Monsoon Event State Machine
# =============================================================================
@dataclass
class MonsoonState:
    """Random temporal trigger for heavy sea-state resistance events."""

    active: bool = False
    resistance_factor: float = 0.0      # multiplicative added resistance [0, 1)
    wave_height_m: float = 1.0          # current simulated wave height
    _next_toggle_s: float = 0.0         # absolute time of next state change
    _rng: np.random.Generator = field(default_factory=lambda: np.random.default_rng())

    def init(self, rng: np.random.Generator, t: float) -> None:
        self._rng = rng
        self._schedule_toggle(t)

    def _schedule_toggle(self, t: float) -> None:
        """Schedule the next activation / deactivation event."""
        if self.active:
            # Monsoon bursts last 30–120 s
            self._next_toggle_s = t + float(self._rng.uniform(30.0, 120.0))
        else:
            # Calm spells last 60–300 s
            self._next_toggle_s = t + float(self._rng.uniform(60.0, 300.0))

    def update(self, t: float) -> None:
        """Advance the state machine by one tick at clock *t* (seconds)."""
        if t < self._next_toggle_s:
            if self.active:
                # Slowly modulate within the storm
                self.wave_height_m += float(
                    self._rng.normal(0.0, 0.05)
                )
                self.wave_height_m = float(np.clip(
                    self.wave_height_m, MONSOON_WAVE_MIN_M, MONSOON_WAVE_MAX_M
                ))
                # Resistance scales linearly with wave height within envelope
                frac = (self.wave_height_m - MONSOON_WAVE_MIN_M) / (
                    MONSOON_WAVE_MAX_M - MONSOON_WAVE_MIN_M
                )
                self.resistance_factor = (
                    MONSOON_RESISTANCE_MIN
                    + frac * (MONSOON_RESISTANCE_MAX - MONSOON_RESISTANCE_MIN)
                )
            else:
                # Calm-sea baseline
                self.wave_height_m = max(
                    0.3, 1.0 + float(self._rng.normal(0.0, 0.15))
                )
                self.resistance_factor = 0.0
            return

        # Toggle state
        self.active = not self.active
        if self.active:
            self.wave_height_m = float(
                self._rng.uniform(MONSOON_WAVE_MIN_M, MONSOON_WAVE_MAX_M)
            )
            frac = (self.wave_height_m - MONSOON_WAVE_MIN_M) / (
                MONSOON_WAVE_MAX_M - MONSOON_WAVE_MIN_M
            )
            self.resistance_factor = (
                MONSOON_RESISTANCE_MIN
                + frac * (MONSOON_RESISTANCE_MAX - MONSOON_RESISTANCE_MIN)
            )
        else:
            self.wave_height_m = 1.0
            self.resistance_factor = 0.0
        self._schedule_toggle(t)


# =============================================================================
# Core Physics Engine
# =============================================================================
class HydrodynamicEngine:
    """Stateful telemetry generator grounded in first-principles naval physics.

    Each call to :meth:`tick` advances the simulation clock by ``dt`` seconds
    and returns a fully derived telemetry snapshot.

    Physical Pipeline (per tick)
    ----------------------------
    1.  SOG (Speed Over Ground) — Gaussian-smoothed random walk around 14.5 kn.
    2.  **Cubic Law**:  P_calm = P_design · (V / V_design)³
    3.  **Monsoon modifier**:  P_actual = P_calm · (1 + resistance_factor)
    4.  **Admiralty Coefficient**:  Ac = Δ^(2/3) · V³ / P_actual  (logged)
    5.  **Thermal efficiency loss**:
            Fuel power  = P_actual / η
            Fuel flow   = Fuel_power / LCV
            SFOC        = fuel_flow / P_actual  (g / kWh)
    6.  Engine RPM — affine mapping from speed + small random jitter.
    7.  Environmental overlay — wind, heading, position drift.
    """

    def __init__(self, seed: int | None = None) -> None:
        self._rng = np.random.default_rng(seed)
        self._clock: float = 0.0
        self._ai_enabled: bool = True   # Master AI Advisory toggle

        # --- Smoothed random walks ---
        self._sog_walk = SmoothedRandomWalk(
            mean=DESIGN_SPEED_KTS, std=1.2, alpha=0.05, reversion=0.015
        )
        self._wind_speed_walk = SmoothedRandomWalk(
            mean=15.0, std=3.0, alpha=0.03, reversion=0.02
        )
        self._wind_dir_walk = SmoothedRandomWalk(
            mean=210.0, std=15.0, alpha=0.02, reversion=0.01
        )
        # --- Thermal efficiency (drifts slowly within 48-52 % band) ---
        self._eta_walk = SmoothedRandomWalk(
            mean=0.50, std=0.01, alpha=0.01, reversion=0.05
        )

        # --- Vessel attitude: pitch (trim) and roll ---
        self._pitch_walk = SmoothedRandomWalk(
            mean=0.3, std=0.5, alpha=0.03, reversion=0.02
        )
        self._roll_walk = SmoothedRandomWalk(
            mean=0.0, std=2.0, alpha=0.04, reversion=0.03
        )

        # --- AIS waypoint navigation (replaces simple position drift) ---
        self._navigator = AISNavigator()

        # --- Monsoon state machine ---
        self._monsoon = MonsoonState()
        self._monsoon.init(self._rng, self._clock)

        # --- Biofouling PINN surrogate ---
        self._biofouling = BiofoulingSurrogate(seed=seed)

        # --- DRL Voyage Optimizer (PPO mock) ---
        self._drl = DRLVoyageOptimizer(seed=seed)

        # --- CII Tactical Segregation (MEPC.355(78)) ---
        self._cii = CIISegregationEngine(seed=seed)

    # --------------------------------------------------------------------- #
    # AI Advisory Mode Toggle
    # --------------------------------------------------------------------- #
    @property
    def ai_enabled(self) -> bool:
        return self._ai_enabled

    @ai_enabled.setter
    def ai_enabled(self, value: bool) -> None:
        self._ai_enabled = bool(value)

    # --------------------------------------------------------------------- #
    # Public API
    # --------------------------------------------------------------------- #
    def tick(self, dt: float) -> dict:
        """Advance simulation by *dt* seconds and return a telemetry dict."""
        self._clock += dt

        # ---- 1. Speed Over Ground (SOG) — smoothed random walk ----
        sog_kts = self._sog_walk.step(self._rng)
        sog_kts = float(np.clip(sog_kts, 4.0, 22.0))  # physical bounds

        # ---- 2. Cubic Law of Propulsive Power ----
        #   P_calm = P_design · (V / V_design)³
        #   A 10 % speed increase → (1.10)³ = 1.331 → 33.1 % power increase
        speed_ratio = sog_kts / DESIGN_SPEED_KTS
        power_calm_kw = DESIGN_SHAFT_POWER_KW * (speed_ratio ** 3)

        # ---- 3. Monsoon Sea-State Resistance Modifier ----
        #   P_actual = P_calm · (1 + resistance_factor)
        #   resistance_factor ∈ [0.30, 0.60] during monsoon (3-5 m waves)
        self._monsoon.update(self._clock)
        power_actual_kw = power_calm_kw * (1.0 + self._monsoon.resistance_factor)

        # ---- 4. Admiralty Coefficient (verification metric) ----
        #   Ac = Δ^(2/3) · V³ / P_actual
        admiralty_coeff = (
            DISPLACEMENT_TWO_THIRDS * (sog_kts ** 3) / max(power_actual_kw, 1.0)
        )

        # ---- 5. Thermal Efficiency → Fuel Flow → SFOC ----
        #   η_thermal ∈ [0.48, 0.52]
        #   Fuel power (kW) = P_shaft / η
        #   Fuel flow (kg/h) = Fuel_power (kW) · 3600 (s/h) / (LCV · 1000 (kJ/MJ))
        #   SFOC (g/kWh) = fuel_flow (kg/h) · 1000 / P_shaft (kW)
        eta = self._eta_walk.step(self._rng)
        eta = float(np.clip(eta, THERMAL_EFFICIENCY_MIN, THERMAL_EFFICIENCY_MAX))

        fuel_power_kw = power_actual_kw / eta
        fuel_flow_kgh = fuel_power_kw * 3600.0 / (LCV_HFO_MJ_PER_KG * 1000.0)
        sfoc_gkwh = (fuel_flow_kgh * 1000.0) / max(power_actual_kw, 1.0)

        # ---- 6. Engine RPM ----
        rpm_base = sog_kts * RPM_PER_KNOT
        rpm = rpm_base + float(self._rng.normal(0.0, 0.8))
        rpm = float(np.clip(rpm, 40.0, 200.0))

        # ---- 7. Temperature (correlated with power) ----
        temp_c = 280.0 + 8.0 * (power_actual_kw / DESIGN_SHAFT_POWER_KW) + float(
            self._rng.normal(0.0, 1.5)
        )

        # ---- 8. AIS Navigation — waypoint interpolation ----
        #   Position and heading derived from the AIS navigator, which
        #   interpolates along the 10-waypoint Arabian Sea patrol route
        #   using the SOG from step 1 as the propulsive input.
        nav = self._navigator.update(sog_kts, dt)

        # ---- 9. Environment ----
        wind_speed = max(0.0, self._wind_speed_walk.step(self._rng))
        wind_dir = self._wind_dir_walk.step(self._rng) % 360.0

        sea_state = self._sea_state_from_wave(self._monsoon.wave_height_m)

        # ---- 9b. Vessel Attitude — Pitch (trim) and Roll ----
        #   Pitch (trim angle): mean ~+0.3° stern-down, modulated by speed.
        #   Roll: base wander amplified by wave height during monsoon.
        pitch_base = self._pitch_walk.step(self._rng)
        pitch_deg = float(np.clip(
            pitch_base + 0.15 * (speed_ratio - 1.0), -3.0, 3.0
        ))
        roll_base = self._roll_walk.step(self._rng)
        roll_scale = 1.0 + self._monsoon.wave_height_m * 0.4
        roll_deg = float(np.clip(roll_base * roll_scale, -8.0, 8.0))

        # ---- 9c. Trim Fuel Penalty ----
        #   |pitch| > 0.5° triggers 3–5 % fuel penalty (non-optimal trim).
        trim_abs = abs(pitch_deg)
        trim_fuel_penalty_pct = (
            min((trim_abs - 0.5) * 2.5, 5.0) if trim_abs > 0.5 else 0.0
        )

        # ---- 10. Sea-Surface Temperature (Indian Ocean 26–30 °C) ----
        sst_c = 28.0 + float(self._rng.normal(0.0, 0.6))
        sst_c = float(np.clip(sst_c, 26.0, 30.0))

        # ---- 11. Biofouling PINN surrogate ----
        if self._ai_enabled:
            ai_curve = self._biofouling.update(
                sog_kts=sog_kts,
                power_actual_kw=power_actual_kw,
                fuel_flow_kgh=fuel_flow_kgh,
                thermal_efficiency=eta,
                sea_surface_temp_c=sst_c,
                dt=dt,
            )
        else:
            # Baseline Sea Trial — no AI biofouling correction,
            # report clean-hull with 0 % penalty
            optimal_fuel = fuel_flow_kgh  # actual = optimal (no penalty)
            speed_sweep = [10.0, 12.5, 15.0, 17.5, 20.0]
            ai_curve = {
                "biological_roughness_coefficient": 0.0,
                "optimal_fuel_kgh": round(optimal_fuel, 2),
                "actual_fuel_kgh": round(optimal_fuel, 2),
                "penalty_pct": 0.0,
                "sea_surface_temp_c": round(sst_c, 1),
                "hull_age_hours": 0.0,
                "curve": [
                    {
                        "speed_kts": v,
                        "optimal_fuel_kgh": round(
                            fuel_flow_kgh * (v / max(sog_kts, 0.1)) ** 3, 2
                        ),
                        "actual_fuel_kgh": round(
                            fuel_flow_kgh * (v / max(sog_kts, 0.1)) ** 3, 2
                        ),
                        "penalty_pct": 0.0,
                    }
                    for v in speed_sweep
                ],
            }

        # ---- 12. DRL Voyage Optimizer — Ghost Route / JIT arrival ----
        if self._ai_enabled:
            drl_out = self._drl.evaluate(
                sog_kts=sog_kts,
                distance_to_wp_nm=nav["distance_to_waypoint_nm"],
                power_actual_kw=power_actual_kw,
                fuel_flow_kgh=fuel_flow_kgh,
                monsoon_resistance_pct=self._monsoon.resistance_factor * 100.0,
                thermal_efficiency=eta,
                dt=dt,
            )
        else:
            # Baseline Sea Trial — DRL advisory disabled, no Ghost Route
            mcr_load = (power_actual_kw / DESIGN_SHAFT_POWER_KW) * 100.0
            drl_out = {
                "ghost_route_active": False,
                "current_speed_kts": round(sog_kts, 2),
                "recommended_speed_kts": round(sog_kts, 2),
                "speed_reduction_kts": 0.0,
                "eta_current_s": round(
                    (nav["distance_to_waypoint_nm"] / max(sog_kts, 0.1)) * 3600.0, 1
                ),
                "eta_planned_s": round(
                    (nav["distance_to_waypoint_nm"] / DESIGN_SPEED_KTS) * 3600.0, 1
                ),
                "arrival_delta_s": 0.0,
                "fuel_saving_kgh": 0.0,
                "total_fuel_saved_kg": 0.0,
                "mcr_load_pct": round(mcr_load, 1),
                "recommended_mcr_load_pct": round(mcr_load, 1),
                "in_mcr_band": False,
                "ppo_reward": 0.0,
            }

        # ---- 13. CII Tactical Segregation ----
        cii_out = self._cii.update(
            sog_kts=sog_kts,
            power_actual_kw=power_actual_kw,
            fuel_flow_kgh=fuel_flow_kgh,
            dt=dt,
        )

        # ---- Build payload ----
        return {
            "timestamp": time.time(),
            "engine": {
                "rpm": round(rpm, 1),
                "fuel_flow_kgh": round(fuel_flow_kgh, 2),
                "temperature_c": round(temp_c, 1),
                "power_kw": round(power_actual_kw, 1),
                "sfoc_gkwh": round(sfoc_gkwh, 2),
            },
            "navigation": {
                "speed_knots": round(sog_kts, 2),
                "heading_deg": nav["heading_deg"],
                "latitude": nav["latitude"],
                "longitude": nav["longitude"],
            },
            "environment": {
                "wind_speed_kts": round(wind_speed, 1),
                "wind_direction_deg": round(wind_dir % 360.0, 1),
                "sea_state": sea_state,
                "wave_height_m": round(self._monsoon.wave_height_m, 2),
            },
            "physics": {
                "admiralty_coefficient": round(admiralty_coeff, 2),
                "thermal_efficiency": round(eta, 4),
                "speed_ratio": round(speed_ratio, 4),
                "cubic_law_power_kw": round(power_calm_kw, 1),
                "monsoon_resistance_pct": round(
                    self._monsoon.resistance_factor * 100.0, 1
                ),
                "monsoon_active": self._monsoon.active,
                "pitch_deg": round(pitch_deg, 2),
                "roll_deg": round(roll_deg, 2),
                "trim_fuel_penalty_pct": round(trim_fuel_penalty_pct, 2),
            },
            "ais": {
                "nmea_sentence": nav["nmea_sentence"],
                "mmsi": MMSI,
                "cog_deg": nav["cog_deg"],
                "current_waypoint_index": nav["current_waypoint_index"],
                "distance_to_waypoint_nm": nav["distance_to_waypoint_nm"],
            },
            "ai_predictive_curve": ai_curve,
            "drl_optimization": drl_out,
            "cii_segregation": cii_out,
            "ai_advisory_mode": self._ai_enabled,
        }

    # --------------------------------------------------------------------- #
    # Helpers
    # --------------------------------------------------------------------- #
    @staticmethod
    def _sea_state_from_wave(wave_m: float) -> int:
        """Douglas Sea Scale (simplified): wave height → sea state 0-9."""
        thresholds = [0, 0.1, 0.5, 1.25, 2.5, 4.0, 6.0, 9.0, 14.0]
        for i, threshold in enumerate(thresholds):
            if wave_m < threshold:
                return max(0, i - 1)
        return 9
