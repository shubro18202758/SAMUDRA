"""
physics/drl_optimizer.py — Deep Reinforcement Learning Voyage Optimiser
========================================================================
Mocks a Proximal Policy Optimization (PPO) agent that provides real-time
voyage re-optimisation to prevent the **Sail-Fast-Then-Wait (SFTW)**
phenomenon described in IMO MEPC.355(78).

SFTW Problem
-------------
Vessels sprint to a destination burning massive fuel (P ∝ V³), then idle
at anchor.  This wastes fuel *and* penalises the CII rating because
loitering time is included in the Attained CII formula:

    Attained CII = (ΣFC_j · C_Fj) / (C · D_t)

where FC = fuel consumption, C_F = CO₂ emission factor, C = capacity
(DWT), D_t = distance travelled.

AI Ghost Route
--------------
When the vessel is projected to arrive at the next waypoint ahead of
schedule, the agent computes an **optimal speed reduction** that:

1.  Achieves Just-In-Time (JIT) arrival — no idle time at waypoint.
2.  Drops engine load into the **peak thermal efficiency band**:
    70 %–85 % of Maximum Continuous Rating (MCR = 8,500 kW).
3.  Quantifies the fuel saved vs. the SFTW scenario.

PPO Reward Function (Conceptual)
---------------------------------
    R(s, a) = w₁ · (-fuel_consumed)          # minimise fuel
            + w₂ · (-|ETA - target_arrival|)  # minimise time deviation
            + w₃ · (-monsoon_resistance)       # avoid heavy weather penalty
            + w₄ · MCR_band_bonus              # reward 70–85 % MCR operation

The weights w₁…w₄ are fixed heuristics that simulate the output of a
trained PPO policy without requiring an actual neural network.

Author : SAMUDRA Backend — Phase 3 (Prompt 5)
"""

from __future__ import annotations

import math

import numpy as np

# =============================================================================
# Vessel Constants (mirrored to avoid circular imports)
# =============================================================================
_DESIGN_SPEED_KTS = 14.5
_DESIGN_SHAFT_POWER_KW = 8_500.0     # MCR — Maximum Continuous Rating
_LCV_HFO_MJ_PER_KG = 42.7

# Peak thermal-efficiency MCR band boundaries
MCR_BAND_LOW = 0.70   # 70 % MCR
MCR_BAND_HIGH = 0.85  # 85 % MCR
MCR_POWER_LOW = _DESIGN_SHAFT_POWER_KW * MCR_BAND_LOW     # 5,950 kW
MCR_POWER_HIGH = _DESIGN_SHAFT_POWER_KW * MCR_BAND_HIGH   # 7,225 kW

# Nominal planned-arrival buffer (seconds).  If ETA beats the planned
# arrival by more than this buffer, a Ghost Route is triggered.
JIT_TRIGGER_BUFFER_S = 120.0   # 2 minutes early → trigger

# PPO reward weights (conceptual — fixed heuristics)
_W_FUEL = 0.40
_W_TIME = 0.25
_W_WEATHER = 0.15
_W_MCR_BAND = 0.20


class DRLVoyageOptimizer:
    """Mocks a PPO-based DRL agent for real-time voyage speed optimisation.

    Lifecycle
    ---------
    1. Instantiated alongside ``HydrodynamicEngine``.
    2. ``evaluate()`` called every tick with current navigation scalars.
    3. Returns a dict ready for injection into the WebSocket payload
       under the key ``drl_optimization``.
    """

    def __init__(self, seed: int | None = None) -> None:
        self._rng = np.random.default_rng(seed)
        # Planned-arrival schedule: each waypoint assigned a nominal
        # transit time (seconds).  We keep a running schedule clock.
        self._schedule_clock: float = 0.0
        # Cumulative fuel saved (kg) by following Ghost Route advice
        self._total_fuel_saved_kg: float = 0.0
        # Last recommended speed (for smoothing)
        self._last_recommended_kts: float = _DESIGN_SPEED_KTS

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def evaluate(
        self,
        sog_kts: float,
        distance_to_wp_nm: float,
        power_actual_kw: float,
        fuel_flow_kgh: float,
        monsoon_resistance_pct: float,
        thermal_efficiency: float,
        dt: float,
    ) -> dict:
        """Evaluate the DRL policy and return a Ghost Route recommendation.

        Parameters
        ----------
        sog_kts : float
            Current Speed Over Ground (knots).
        distance_to_wp_nm : float
            Distance remaining to next waypoint (NM).
        power_actual_kw : float
            Current shaft power (kW).
        fuel_flow_kgh : float
            Current fuel flow (kg/h).
        monsoon_resistance_pct : float
            Current monsoon-added resistance (%).
        thermal_efficiency : float
            Current η_thermal.
        dt : float
            Tick interval (seconds).

        Returns
        -------
        dict
            Payload matching ``DRLOptimizationFrame``.
        """
        self._schedule_clock += dt

        # ---- 1. Compute ETA at current speed ----
        #   distance_nm / sog_kts gives hours → convert to seconds
        eta_s = (distance_to_wp_nm / max(sog_kts, 0.1)) * 3600.0

        # ---- 2. Planned arrival time ----
        #   Nominal transit assumes design speed (14.5 kn).
        #   Any delta indicates potential SFTW behaviour.
        planned_eta_s = (distance_to_wp_nm / _DESIGN_SPEED_KTS) * 3600.0

        # ---- 3. Detect early-arrival (SFTW trigger) ----
        arrival_delta_s = planned_eta_s - eta_s  # positive → arriving early
        ghost_route_active = arrival_delta_s > JIT_TRIGGER_BUFFER_S

        # ---- 4. Compute Ghost Route optimal speed ----
        if ghost_route_active and planned_eta_s > 0:
            # JIT speed = distance / planned_time
            jit_speed_kts = distance_to_wp_nm / (planned_eta_s / 3600.0)
            jit_speed_kts = max(jit_speed_kts, 4.0)

            # Clamp to keep engine in 70–85 % MCR band
            # Power at speed V: P = P_design · (V / V_design)³
            # V at power P: V = V_design · (P / P_design)^(1/3)
            v_at_mcr_low = _DESIGN_SPEED_KTS * (MCR_BAND_LOW ** (1.0 / 3.0))
            v_at_mcr_high = _DESIGN_SPEED_KTS * (MCR_BAND_HIGH ** (1.0 / 3.0))

            recommended_kts = float(np.clip(
                jit_speed_kts, v_at_mcr_low, v_at_mcr_high
            ))
            # Smooth the recommendation (EMA) to prevent oscillation
            recommended_kts = (
                0.15 * recommended_kts + 0.85 * self._last_recommended_kts
            )
            self._last_recommended_kts = recommended_kts
        else:
            recommended_kts = sog_kts
            self._last_recommended_kts = sog_kts

        # ---- 5. Compute fuel savings ----
        #   Fuel at current speed vs. fuel at recommended speed
        current_fuel_kgh = fuel_flow_kgh
        rec_power_kw = _DESIGN_SHAFT_POWER_KW * (
            (recommended_kts / _DESIGN_SPEED_KTS) ** 3
        )
        # Add monsoon resistance to recommended power too
        rec_power_kw *= (1.0 + monsoon_resistance_pct / 100.0)
        rec_fuel_kw = rec_power_kw / max(thermal_efficiency, 0.30)
        rec_fuel_kgh = rec_fuel_kw * 3600.0 / (_LCV_HFO_MJ_PER_KG * 1000.0)

        fuel_saving_kgh = max(0.0, current_fuel_kgh - rec_fuel_kgh)
        # Accumulate per-tick savings (kg)
        fuel_saving_tick_kg = fuel_saving_kgh * (dt / 3600.0)
        if ghost_route_active:
            self._total_fuel_saved_kg += fuel_saving_tick_kg

        # ---- 6. MCR load fraction ----
        mcr_load_pct = (power_actual_kw / _DESIGN_SHAFT_POWER_KW) * 100.0
        rec_mcr_load_pct = (rec_power_kw / _DESIGN_SHAFT_POWER_KW) * 100.0
        in_mcr_band = MCR_BAND_LOW * 100.0 <= rec_mcr_load_pct <= MCR_BAND_HIGH * 100.0

        # ---- 7. PPO reward function (conceptual evaluation) ----
        #     R(s,a) = w₁·(-fuel) + w₂·(-|ETA_delta|) + w₃·(-weather) + w₄·MCR_bonus
        reward_fuel = -fuel_flow_kgh / 1000.0                       # normalised
        reward_time = -(abs(arrival_delta_s) / 3600.0)               # hours off
        reward_weather = -(monsoon_resistance_pct / 100.0)           # [0, 0.6]
        reward_mcr = 1.0 if in_mcr_band else -0.5
        ppo_reward = (
            _W_FUEL * reward_fuel
            + _W_TIME * reward_time
            + _W_WEATHER * reward_weather
            + _W_MCR_BAND * reward_mcr
        )
        # Add small noise to simulate stochastic policy output
        ppo_reward += float(self._rng.normal(0.0, 0.02))

        # ---- 8. Build payload ----
        return {
            "ghost_route_active": ghost_route_active,
            "current_speed_kts": round(sog_kts, 2),
            "recommended_speed_kts": round(recommended_kts, 2),
            "speed_reduction_kts": round(max(0.0, sog_kts - recommended_kts), 2),
            "eta_current_s": round(eta_s, 1),
            "eta_planned_s": round(planned_eta_s, 1),
            "arrival_delta_s": round(arrival_delta_s, 1),
            "fuel_saving_kgh": round(fuel_saving_kgh, 2),
            "total_fuel_saved_kg": round(self._total_fuel_saved_kg, 3),
            "mcr_load_pct": round(mcr_load_pct, 1),
            "recommended_mcr_load_pct": round(rec_mcr_load_pct, 1),
            "in_mcr_band": in_mcr_band,
            "ppo_reward": round(ppo_reward, 4),
        }
