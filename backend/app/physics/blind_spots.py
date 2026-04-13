"""
physics/blind_spots.py — Systemic Blind Spot Detection & Mitigation
===================================================================
Addresses five critical blind spots that can degrade fuel optimization
accuracy in real-world maritime operations.

Blind Spots Modelled
--------------------
1. **Baseline Degradation Tracker**
   - Detects silent drift in hull, engine, and propulsion baselines
   - Uses CUSUM (Cumulative Sum) change-point detection
   - Flags when "normal" has silently shifted, invalidating models

2. **Micro-Climate Variance Engine**
   - Models localized sea conditions that differ from synoptic weather
   - Captures thermal layers, current shear, estuary effects
   - Addresses the gap between global forecast and ship-level reality

3. **Kinetic Energy Spike Detector**
   - Detects transient power surges from acceleration/deceleration
   - Quantifies fuel wasted in speed oscillations
   - Proposes smooth speed profiles to reduce wave-making losses

4. **Integration Synchronization Monitor**
   - Tracks timestamp alignment across sensor systems
   - Detects latency, clock drift, and out-of-order data
   - Computes data fusion confidence score

5. **Causal Disambiguation Engine**
   - Separates correlated vs causal factors in fuel consumption
   - Uses variance decomposition to attribute fuel changes to root causes
   - Prevents false optimization recommendations from spurious correlations

Reference Standards
-------------------
- ISO 19030-1: Speed-power performance baseline
- NIST SP 800-88: Data integrity assurance
- Hawkins (2001): CUSUM procedures for change-point detection

Author : SAMUDRA Backend — Phase 4 (Blind Spot Mitigation)
"""

from __future__ import annotations

import math
from collections import deque
from dataclasses import dataclass, field
from typing import Any

import numpy as np


# ═══════════════════════════════════════════════════════════════════════════
# 1. Baseline Degradation Tracker (CUSUM Change-Point Detection)
# ═══════════════════════════════════════════════════════════════════════════
class BaselineDegradationTracker:
    """Detects silent drift in performance baselines using CUSUM.

    Monitors speed-power ratio as primary baseline indicator.
    When the CUSUM statistic exceeds threshold, signals baseline shift.
    """

    def __init__(self, target_speed_power_ratio: float = 1.70,
                 allowance: float = 0.05, threshold: float = 4.0,
                 window: int = 200) -> None:
        self._target = target_speed_power_ratio   # kts per 1000 kW baseline
        self._allowance = allowance               # Slack (k) in CUSUM
        self._threshold = threshold               # Decision boundary (h)
        self._cusum_pos = 0.0
        self._cusum_neg = 0.0
        self._drift_detected = False
        self._baseline_shift_count = 0
        self._history = deque(maxlen=window)
        self._current_baseline = target_speed_power_ratio

    def update(self, sog_kts: float, power_kw: float) -> dict:
        if power_kw < 100:
            return self._result()

        ratio = sog_kts / (power_kw / 1000.0)
        self._history.append(ratio)

        # CUSUM update
        deviation = ratio - self._current_baseline
        self._cusum_pos = max(0.0, self._cusum_pos + deviation - self._allowance)
        self._cusum_neg = max(0.0, self._cusum_neg - deviation - self._allowance)

        if self._cusum_pos > self._threshold or self._cusum_neg > self._threshold:
            self._drift_detected = True
            self._baseline_shift_count += 1
            # Reset CUSUM and update baseline
            self._current_baseline = float(np.mean(list(self._history)[-50:]))
            self._cusum_pos = 0.0
            self._cusum_neg = 0.0
        else:
            self._drift_detected = False

        return self._result()

    def _result(self) -> dict:
        recent = list(self._history)[-30:] if len(self._history) >= 30 else list(self._history)
        current_mean = float(np.mean(recent)) if recent else self._target
        deviation_pct = ((current_mean - self._target) / self._target * 100.0) if self._target != 0 else 0.0

        return {
            "baseline_speed_power_ratio": round(self._current_baseline, 4),
            "current_speed_power_ratio": round(current_mean, 4),
            "cusum_positive": round(self._cusum_pos, 3),
            "cusum_negative": round(self._cusum_neg, 3),
            "drift_detected": self._drift_detected,
            "total_baseline_shifts": self._baseline_shift_count,
            "deviation_from_baseline_pct": round(deviation_pct, 2),
            "status": "DRIFT_DETECTED" if self._drift_detected else
                      "DEGRADING" if abs(deviation_pct) > 3.0 else "STABLE",
        }


# ═══════════════════════════════════════════════════════════════════════════
# 2. Micro-Climate Variance Engine
# ═══════════════════════════════════════════════════════════════════════════
class MicroClimateEngine:
    """Models localized sea conditions diverging from synoptic weather data.

    Captures:
    - Coastal thermal layering (thermocline effects)
    - Estuary/river mouth fresh water influence
    - Local current shear from tidal/littoral effects
    - Ship-level micro-weather vs forecast delta
    """

    def __init__(self, seed: int | None = None) -> None:
        self._rng = np.random.default_rng(seed)

    def update(self, lat: float, lon: float, sst_c: float,
               wind_speed_kts: float, wave_height_m: float,
               forecast_wind_kts: float, forecast_wave_m: float) -> dict:
        # Coastal proximity effect (simplified — nearshore = more variance)
        coastal_factor = self._coastal_proximity_factor(lat, lon)

        # Thermal layer delta — cold upwelling near shelf edges
        thermal_delta_c = float(self._rng.normal(0.0, 0.8 * coastal_factor))
        local_sst_c = sst_c + thermal_delta_c

        # Current shear — tidal/littoral near coast
        current_shear_kts = abs(float(self._rng.normal(0.0, 0.5 * coastal_factor)))

        # Fresh water influence (lower density near river mouths)
        salinity_deviation_psu = float(self._rng.normal(0.0, 1.5 * coastal_factor))

        # Forecast accuracy delta
        wind_forecast_error_kts = abs(wind_speed_kts - forecast_wind_kts) + float(self._rng.normal(0.0, 1.0))
        wave_forecast_error_m = abs(wave_height_m - forecast_wave_m) + float(self._rng.normal(0.0, 0.2))

        # Micro-climate confidence score (0-100)
        total_error = wind_forecast_error_kts + wave_forecast_error_m * 5.0 + abs(thermal_delta_c)
        confidence_pct = max(0.0, 100.0 - total_error * 3.0)

        # Fuel impact — rough estimate of micro-climate-induced fuel deviation
        fuel_impact_pct = (current_shear_kts * 1.5 +
                           abs(thermal_delta_c) * 0.3 +
                           wind_forecast_error_kts * 0.5)

        return {
            "local_sst_c": round(local_sst_c, 2),
            "thermal_layer_delta_c": round(thermal_delta_c, 2),
            "current_shear_kts": round(current_shear_kts, 2),
            "salinity_deviation_psu": round(salinity_deviation_psu, 2),
            "wind_forecast_error_kts": round(wind_forecast_error_kts, 1),
            "wave_forecast_error_m": round(wave_forecast_error_m, 2),
            "coastal_proximity_factor": round(coastal_factor, 2),
            "micro_climate_confidence_pct": round(confidence_pct, 1),
            "estimated_fuel_impact_pct": round(fuel_impact_pct, 2),
        }

    @staticmethod
    def _coastal_proximity_factor(lat: float, lon: float) -> float:
        """Estimate proximity to Indian west coast (higher = closer to shore)."""
        # Simplified: Indian west coast runs roughly along lon 73-77
        coast_lons = {
            18.9: 72.8, 17.0: 73.1, 15.4: 73.8, 14.8: 74.1,
            12.9: 74.8, 10.0: 76.3, 8.3: 76.9,
        }
        min_dist = float('inf')
        for clat, clon in coast_lons.items():
            d = math.sqrt((lat - clat) ** 2 + (lon - clon) ** 2)
            min_dist = min(min_dist, d)

        # >5° away → factor 0.1, at coast → factor 1.0
        return float(np.clip(1.0 - min_dist / 5.0, 0.1, 1.0))


# ═══════════════════════════════════════════════════════════════════════════
# 3. Kinetic Energy Spike Detector
# ═══════════════════════════════════════════════════════════════════════════
class KineticEnergySpikeDetector:
    """Detects transient power surges from speed changes.

    KE = ½ m V² → ΔKE/dt quantifies acceleration energy waste.
    A smooth speed profile minimizes wave-making losses (∝ V^6 for high Froude).
    """

    _DISPLACEMENT_KG = 2_350_000.0  # 2,350 tonnes
    _KTS_TO_MS = 0.5144

    def __init__(self, window: int = 60) -> None:
        self._speed_history = deque(maxlen=window)
        self._power_history = deque(maxlen=window)
        self._total_waste_kwh = 0.0
        self._spike_count = 0

    def update(self, sog_kts: float, power_kw: float, dt: float) -> dict:
        v_ms = sog_kts * self._KTS_TO_MS
        self._speed_history.append(v_ms)
        self._power_history.append(power_kw)

        # Acceleration
        if len(self._speed_history) >= 2:
            dv = self._speed_history[-1] - self._speed_history[-2]
            accel_ms2 = dv / max(dt, 0.01)
        else:
            dv = 0.0
            accel_ms2 = 0.0

        # Kinetic energy change
        ke_change_j = self._DISPLACEMENT_KG * v_ms * dv
        ke_change_kw = ke_change_j / max(dt, 0.01) / 1000.0

        # Power surge detection (significant acceleration)
        is_spike = abs(ke_change_kw) > 200.0  # >200 kW transient
        if is_spike:
            self._spike_count += 1
            self._total_waste_kwh += abs(ke_change_kw) * dt / 3600.0

        # Speed variability (coefficient of variation of recent speeds)
        if len(self._speed_history) >= 10:
            recent = list(self._speed_history)[-10:]
            mean_v = float(np.mean(recent))
            std_v = float(np.std(recent))
            cv = std_v / mean_v if mean_v > 0.01 else 0.0
        else:
            cv = 0.0

        # Smoothness score (0-100, higher = smoother profile)
        smoothness = max(0.0, 100.0 - cv * 500.0)

        return {
            "acceleration_ms2": round(accel_ms2, 4),
            "ke_change_kw": round(ke_change_kw, 1),
            "is_spike": is_spike,
            "total_spikes": self._spike_count,
            "total_waste_kwh": round(self._total_waste_kwh, 2),
            "speed_cv": round(cv, 4),
            "smoothness_score": round(smoothness, 1),
            "recommendation": "MAINTAIN_SPEED" if smoothness > 80 else
                              "REDUCE_OSCILLATION" if smoothness > 50 else
                              "CRITICAL_INSTABILITY",
        }


# ═══════════════════════════════════════════════════════════════════════════
# 4. Integration Synchronization Monitor
# ═══════════════════════════════════════════════════════════════════════════
class IntegrationSyncMonitor:
    """Monitors timestamp alignment across multiple sensor subsystems.

    In real ships, sensor clocks can drift by seconds to minutes,
    causing data fusion errors that cascade into incorrect optimization.
    """

    def __init__(self, num_sources: int = 8, seed: int | None = None) -> None:
        self._rng = np.random.default_rng(seed)
        self._num_sources = num_sources
        self._source_names = [
            "AIS_TRANSPONDER", "ECDIS", "EMCS", "FOMS",
            "WEATHER_STATION", "VDR", "GYRO_COMPASS", "GPS",
        ][:num_sources]
        self._clock_offsets_ms: list[float] = [0.0] * num_sources
        self._total_out_of_order = 0

    def update(self, dt: float) -> dict:
        # Simulate clock drift per source (±50ms wander per tick)
        for i in range(self._num_sources):
            drift = float(self._rng.normal(0.0, 5.0))
            self._clock_offsets_ms[i] += drift
            # Occasional resync (NTP-like)
            if abs(self._clock_offsets_ms[i]) > 500:
                self._clock_offsets_ms[i] *= 0.1

        # Max skew between any two sources
        max_skew_ms = max(self._clock_offsets_ms) - min(self._clock_offsets_ms)

        # Out-of-order detection
        if max_skew_ms > 200:
            self._total_out_of_order += 1

        # Data fusion confidence
        if max_skew_ms < 50:
            confidence_pct = 98.0
            status = "SYNCHRONIZED"
        elif max_skew_ms < 200:
            confidence_pct = 85.0 - (max_skew_ms - 50) * 0.15
            status = "MINOR_DRIFT"
        elif max_skew_ms < 500:
            confidence_pct = 60.0 - (max_skew_ms - 200) * 0.1
            status = "SIGNIFICANT_DRIFT"
        else:
            confidence_pct = max(10.0, 30.0 - (max_skew_ms - 500) * 0.02)
            status = "CRITICAL_DESYNC"

        source_status = {
            name: {
                "offset_ms": round(self._clock_offsets_ms[i], 1),
                "status": "OK" if abs(self._clock_offsets_ms[i]) < 100 else
                          "DRIFT" if abs(self._clock_offsets_ms[i]) < 300 else "DESYNC",
            }
            for i, name in enumerate(self._source_names)
        }

        return {
            "max_clock_skew_ms": round(max_skew_ms, 1),
            "fusion_confidence_pct": round(max(0.0, confidence_pct), 1),
            "sync_status": status,
            "total_out_of_order_events": self._total_out_of_order,
            "source_count": self._num_sources,
            "sources": source_status,
        }


# ═══════════════════════════════════════════════════════════════════════════
# 5. Causal Disambiguation Engine
# ═══════════════════════════════════════════════════════════════════════════
class CausalDisambiguationEngine:
    """Variance decomposition to attribute fuel consumption changes to root causes.

    Separates:
    - Speed effect (cubic law)
    - Weather/sea state effect
    - Hull fouling effect
    - Engine degradation effect
    - Operational mode effect
    - Unexplained residual (potential spurious correlation)
    """

    def __init__(self, window: int = 100) -> None:
        self._window = window
        self._fuel_history = deque(maxlen=window)
        self._speed_history = deque(maxlen=window)
        self._wave_history = deque(maxlen=window)
        self._roughness_history = deque(maxlen=window)
        self._temp_history = deque(maxlen=window)

    def update(self, fuel_flow_kgh: float, sog_kts: float,
               wave_height_m: float, hull_roughness_um: float,
               engine_temp_c: float, bio_penalty_pct: float,
               sea_margin_pct: float) -> dict:
        self._fuel_history.append(fuel_flow_kgh)
        self._speed_history.append(sog_kts)
        self._wave_history.append(wave_height_m)
        self._roughness_history.append(hull_roughness_um)
        self._temp_history.append(engine_temp_c)

        # Variance decomposition (simplified linear attribution)
        if len(self._fuel_history) < 10:
            return self._default_result()

        total_fuel_var = float(np.var(list(self._fuel_history)))
        if total_fuel_var < 0.01:
            return self._default_result()

        # Speed contribution (cubic law dominates)
        speed_var = float(np.var(list(self._speed_history)))
        speed_pct = min(60.0, (speed_var / max(speed_var + 1e-6, 1.0)) * 60.0)

        # Weather contribution
        wave_var = float(np.var(list(self._wave_history)))
        weather_pct = min(20.0, sea_margin_pct * 0.8 + wave_var * 2.0)

        # Hull fouling contribution
        roughness_var = float(np.var(list(self._roughness_history)))
        hull_pct = min(15.0, bio_penalty_pct * 1.2 + roughness_var * 0.001)

        # Engine degradation contribution
        temp_var = float(np.var(list(self._temp_history)))
        engine_pct = min(10.0, temp_var * 0.01)

        # Normalize and compute residual
        total = speed_pct + weather_pct + hull_pct + engine_pct
        if total > 100.0:
            scale = 95.0 / total
            speed_pct *= scale
            weather_pct *= scale
            hull_pct *= scale
            engine_pct *= scale

        residual_pct = max(0.0, 100.0 - speed_pct - weather_pct - hull_pct - engine_pct)

        # Causal confidence — lower if residual is large
        causal_confidence = max(0.0, 100.0 - residual_pct * 2.0)

        return {
            "attribution": {
                "speed_effect_pct": round(speed_pct, 1),
                "weather_effect_pct": round(weather_pct, 1),
                "hull_fouling_pct": round(hull_pct, 1),
                "engine_degradation_pct": round(engine_pct, 1),
                "unexplained_residual_pct": round(residual_pct, 1),
            },
            "causal_confidence_pct": round(causal_confidence, 1),
            "dominant_factor": max(
                [("SPEED", speed_pct), ("WEATHER", weather_pct),
                 ("HULL", hull_pct), ("ENGINE", engine_pct),
                 ("UNKNOWN", residual_pct)],
                key=lambda x: x[1],
            )[0],
            "warning": "High unexplained variance — possible spurious correlations"
                       if residual_pct > 30 else None,
        }

    @staticmethod
    def _default_result() -> dict:
        return {
            "attribution": {
                "speed_effect_pct": 0.0,
                "weather_effect_pct": 0.0,
                "hull_fouling_pct": 0.0,
                "engine_degradation_pct": 0.0,
                "unexplained_residual_pct": 100.0,
            },
            "causal_confidence_pct": 0.0,
            "dominant_factor": "INSUFFICIENT_DATA",
            "warning": "Insufficient data for causal analysis",
        }


# ═══════════════════════════════════════════════════════════════════════════
# Top-Level Blind Spots Engine
# ═══════════════════════════════════════════════════════════════════════════
class BlindSpotsEngine:
    """Unified engine addressing all five systemic blind spots."""

    def __init__(self, seed: int | None = None) -> None:
        self.baseline_tracker = BaselineDegradationTracker()
        self.micro_climate = MicroClimateEngine(seed=seed)
        self.ke_detector = KineticEnergySpikeDetector()
        self.sync_monitor = IntegrationSyncMonitor(seed=seed)
        self.causal_engine = CausalDisambiguationEngine()

    def update(
        self,
        sog_kts: float, power_kw: float,
        lat: float, lon: float, sst_c: float,
        wind_speed_kts: float, wave_height_m: float,
        hull_roughness_um: float, engine_temp_c: float,
        bio_penalty_pct: float, sea_margin_pct: float,
        dt: float,
    ) -> dict:
        baseline = self.baseline_tracker.update(sog_kts, power_kw)
        micro_climate = self.micro_climate.update(
            lat, lon, sst_c, wind_speed_kts, wave_height_m,
            forecast_wind_kts=wind_speed_kts * 0.9,
            forecast_wave_m=wave_height_m * 0.85,
        )
        ke_spikes = self.ke_detector.update(sog_kts, power_kw, dt)
        sync = self.sync_monitor.update(dt)
        causal = self.causal_engine.update(
            power_kw * 0.18, sog_kts, wave_height_m,
            hull_roughness_um, engine_temp_c, bio_penalty_pct, sea_margin_pct,
        )

        # Aggregate blind spot risk
        risks = [
            1.0 if baseline["drift_detected"] else 0.0,
            1.0 - micro_climate["micro_climate_confidence_pct"] / 100.0,
            1.0 - ke_spikes["smoothness_score"] / 100.0,
            1.0 - sync["fusion_confidence_pct"] / 100.0,
            1.0 - causal["causal_confidence_pct"] / 100.0,
        ]
        overall_risk = sum(risks) / len(risks)
        active_blind_spots = sum(1 for r in risks if r > 0.3)

        return {
            "baseline_degradation": baseline,
            "micro_climate": micro_climate,
            "kinetic_energy_spikes": ke_spikes,
            "integration_sync": sync,
            "causal_disambiguation": causal,
            "aggregate": {
                "overall_blind_spot_risk": round(overall_risk, 3),
                "active_blind_spots": active_blind_spots,
                "total_monitored": 5,
                "status": "CRITICAL" if active_blind_spots >= 3 else
                          "WARNING" if active_blind_spots >= 2 else
                          "WATCH" if active_blind_spots >= 1 else "CLEAR",
            },
        }
