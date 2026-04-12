"""
physics/biofouling.py — Physics-Informed Neural Network (PINN) Surrogate
=========================================================================
Simulates a PINN predicting hull biofouling degradation on an Indian Coast
Guard OPV operating in the 26–30 °C waters of the Indian Ocean.

Science Background
-------------------
Biofouling (micro-slime → barnacles) roughens the hull, transitioning the
boundary layer from **laminar → turbulent**.  This increases frictional
resistance and therefore fuel consumption.

- **Clean hull**:  Optimal fuel burn follows pure Cubic-Law physics.
- **Fouled hull**:  A roughness penalty multiplier of 1.07 → 1.20
  (7 %–20 % excess fuel) is applied, growing over time.

The ``biological_roughness_coefficient`` (BRC) starts at its lower bound
(~0.07 = 7 %) at cold-start and drifts upward over the application's
runtime, simulating accelerated hull aging.  Sea-Surface Temperature (SST)
modulates the growth rate — hotter water accelerates biogenic accumulation.

Surrogate PINN Curve
---------------------
At every tick, the module evaluates a 5-point predictive fuel curve across
a 10–20 kn speed envelope.  Each point contains:

    speed_kts, optimal_fuel_kgh, actual_fuel_kgh, penalty_pct

The "optimal" value is computed from first-principles (Cubic Law +
thermal efficiency), while "actual" applies the BRC penalty with additive
Gaussian noise to emulate probabilistic neural-network inference jitter.

Author : SAMUDRA Backend — Phase 3 (Prompt 4)
"""

from __future__ import annotations

import math
import time

import numpy as np

# =============================================================================
# Vessel constants (shared with hydrodynamics.py — duplicated to keep module
# self-contained and avoid circular imports)
# =============================================================================
_DESIGN_SPEED_KTS = 14.5
_DESIGN_SHAFT_POWER_KW = 8_500.0
_LCV_HFO_MJ_PER_KG = 42.7        # Lower Calorific Value of HFO

# =============================================================================
# Biofouling parameters
# =============================================================================
BRC_MIN = 0.07          # 7 % penalty at clean hull
BRC_MAX = 0.20          # 20 % penalty at heavily fouled hull
BRC_GROWTH_RATE = 2.0e-5  # base growth per second (≈0.072/hour → ~7.2 %/h)

# Sea-Surface Temperature modulation — hotter water → faster fouling
SST_REFERENCE_C = 26.0   # baseline temperature
SST_SENSITIVITY = 0.12   # fractional growth boost per °C above reference

# Predictive speed sweep for the AI curve
CURVE_SPEED_MIN_KTS = 10.0
CURVE_SPEED_MAX_KTS = 20.0
CURVE_NUM_POINTS = 5


class BiofoulingSurrogate:
    """Deterministic surrogate that masquerades as a PINN predicting hull
    biofouling drag penalty and generating a live fuel-consumption curve.

    Lifecycle
    ---------
    1. Instantiated once alongside ``HydrodynamicEngine``.
    2. ``update()`` called every tick with current telemetry scalars.
    3. Returns a dict ready for injection into the WebSocket payload.
    """

    def __init__(self, seed: int | None = None) -> None:
        self._rng = np.random.default_rng(seed)
        self._brc: float = BRC_MIN          # biological roughness coefficient
        self._birth_time: float = time.monotonic()

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def update(
        self,
        sog_kts: float,
        power_actual_kw: float,
        fuel_flow_kgh: float,
        thermal_efficiency: float,
        sea_surface_temp_c: float,
        dt: float,
    ) -> dict:
        """Advance biofouling state and return the AI predictive payload.

        Parameters
        ----------
        sog_kts : float
            Current Speed Over Ground (knots).
        power_actual_kw : float
            Current shaft power after monsoon modifier (kW).
        fuel_flow_kgh : float
            Current actual fuel flow (kg/h).
        thermal_efficiency : float
            Current η_thermal [0.48–0.52].
        sea_surface_temp_c : float
            Simulated SST (°C) — drives fouling growth rate.
        dt : float
            Tick interval in seconds.

        Returns
        -------
        dict
            Payload with keys matching ``AIPredictiveCurveFrame``.
        """
        # ---- 1. Grow the Biological Roughness Coefficient ----
        self._grow_brc(sea_surface_temp_c, dt)

        # ---- 2. Compute instantaneous optimal vs actual fuel burn ----
        optimal_fuel_kgh = self._optimal_fuel_at_speed(
            sog_kts, thermal_efficiency
        )
        # The penalty with probabilistic jitter (Gaussian noise)
        noisy_brc = self._jittered_brc()
        actual_fuel_kgh = optimal_fuel_kgh * (1.0 + noisy_brc)
        penalty_pct = noisy_brc * 100.0

        # ---- 3. Generate the 5-point predictive fuel curve ----
        curve_points = self._generate_curve(thermal_efficiency)

        # ---- 4. Build payload ----
        return {
            "biological_roughness_coefficient": round(self._brc, 6),
            "optimal_fuel_kgh": round(optimal_fuel_kgh, 2),
            "actual_fuel_kgh": round(actual_fuel_kgh, 2),
            "penalty_pct": round(penalty_pct, 2),
            "sea_surface_temp_c": round(sea_surface_temp_c, 1),
            "hull_age_hours": round(
                (time.monotonic() - self._birth_time) / 3600.0, 3
            ),
            "curve": curve_points,
        }

    # ------------------------------------------------------------------ #
    # Internal: BRC growth model
    # ------------------------------------------------------------------ #
    def _grow_brc(self, sst_c: float, dt: float) -> None:
        """Increment the BRC based on elapsed time and SST."""
        # Temperature-dependent growth multiplier
        temp_boost = 1.0 + SST_SENSITIVITY * max(0.0, sst_c - SST_REFERENCE_C)
        # Small stochastic jitter on the growth itself (±15 %)
        growth_noise = 1.0 + float(self._rng.normal(0.0, 0.15))
        growth_noise = max(0.5, growth_noise)  # prevent negative growth

        increment = BRC_GROWTH_RATE * temp_boost * growth_noise * dt
        self._brc = min(self._brc + increment, BRC_MAX)

    # ------------------------------------------------------------------ #
    # Internal: Jittered BRC for probabilistic appearance
    # ------------------------------------------------------------------ #
    def _jittered_brc(self) -> float:
        """Return the BRC with additive Gaussian noise to simulate
        stochastic neural-network inference variance."""
        # Noise magnitude scales with the BRC itself (heteroscedastic)
        sigma = 0.004 + 0.02 * self._brc   # ~0.5–0.8 % std at typical BRC
        noise = float(self._rng.normal(0.0, sigma))
        return float(np.clip(self._brc + noise, BRC_MIN * 0.9, BRC_MAX * 1.05))

    # ------------------------------------------------------------------ #
    # Internal: First-principles optimal fuel burn
    # ------------------------------------------------------------------ #
    @staticmethod
    def _optimal_fuel_at_speed(
        speed_kts: float, thermal_efficiency: float
    ) -> float:
        """Compute the *clean-hull* fuel flow at a given speed using the
        Cubic Law and thermal-efficiency conversion.

            P_calm = P_design · (V / V_design)³
            fuel_flow = P_calm / η / (LCV · 1000) · 3600   [kg/h]
        """
        speed_ratio = max(speed_kts, 0.1) / _DESIGN_SPEED_KTS
        power_calm_kw = _DESIGN_SHAFT_POWER_KW * (speed_ratio ** 3)
        eta = max(thermal_efficiency, 0.30)
        fuel_power_kw = power_calm_kw / eta
        return fuel_power_kw * 3600.0 / (_LCV_HFO_MJ_PER_KG * 1000.0)

    # ------------------------------------------------------------------ #
    # Internal: 5-point predictive AI fuel curve
    # ------------------------------------------------------------------ #
    def _generate_curve(self, thermal_efficiency: float) -> list[dict]:
        """Produce 5 speed-vs-fuel data points spanning 10–20 kn.

        Each point contains:
          - speed_kts
          - optimal_fuel_kgh  (clean-hull, frictionless baseline)
          - actual_fuel_kgh   (biofouled, with noise)
          - penalty_pct       (delta between actual and optimal)
        """
        speeds = np.linspace(
            CURVE_SPEED_MIN_KTS, CURVE_SPEED_MAX_KTS, CURVE_NUM_POINTS
        )
        points: list[dict] = []

        for spd in speeds:
            opt = self._optimal_fuel_at_speed(float(spd), thermal_efficiency)
            noisy_brc = self._jittered_brc()
            act = opt * (1.0 + noisy_brc)
            pct = noisy_brc * 100.0

            points.append({
                "speed_kts": round(float(spd), 1),
                "optimal_fuel_kgh": round(opt, 2),
                "actual_fuel_kgh": round(act, 2),
                "penalty_pct": round(pct, 2),
            })

        return points
