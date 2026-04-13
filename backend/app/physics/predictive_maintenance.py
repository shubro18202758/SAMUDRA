"""
physics/predictive_maintenance.py — AI-Driven Predictive Maintenance Engine
============================================================================
Implements mechanical component health monitoring, Remaining Useful Life (RUL)
estimation, and automated maintenance scheduling for Indian Coast Guard OPVs.

Architecture
------------
Component Health Models (exponential degradation + noise):
  1. Main Engine bearings (crankshaft main journal × 6)
  2. Turbocharger impeller (high-speed fatigue)
  3. Fuel injectors (12 cylinders — carbon fouling)
  4. Lube oil system (viscosity break-down, contamination)
  5. Coolant system (thermostat, pump cavitation risk)
  6. Exhaust valves (12 cylinders — carbon buildup, seat erosion)
  7. Governor actuator (fuel rack response degradation)

LSTM Anomaly Detection (simplified):
  - Sliding window of engine parameter residuals
  - Exponentially-weighted moving average (EWMA) z-score
  - Alerts when z-score exceeds threshold (simulates LSTM autoencoder)

Maintenance Scheduler:
  - Condition-Based Maintenance (CBM) per MIL-STD-3034
  - Risk-priority ordering, estimated downtime, spare parts flag

Reference Standards
-------------------
- MIL-STD-3034: Reliability-Centered Maintenance
- SOLAS Chapter II-1 Reg 26: Machinery maintenance
- IACS UR M78: Planned Maintenance Scheme
- ISO 17359: Condition monitoring diagnostics

Author : SAMUDRA Backend — Phase 4 (Predictive Maintenance)
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

import numpy as np


# ═══════════════════════════════════════════════════════════════════════════
# Component Health Model
# ═══════════════════════════════════════════════════════════════════════════
@dataclass
class ComponentState:
    name: str
    health_pct: float = 100.0         # 100=new, 0=failed
    rul_hours: float = 8000.0         # Remaining Useful Life
    degradation_rate: float = 0.001   # % per tick under normal load
    load_factor: float = 1.0          # Multiplied into degradation
    last_maintenance_h: float = 0.0
    maintenance_interval_h: float = 4000.0
    status: str = "HEALTHY"           # HEALTHY | WATCH | WARNING | CRITICAL | FAILED
    anomaly_score: float = 0.0


class ComponentHealthModel:
    """Generic exponential degradation model for a mechanical component."""

    def __init__(self, name: str, base_rate: float = 0.0008,
                 mtbf_hours: float = 8000.0, seed: int | None = None):
        self._rng = np.random.default_rng(seed)
        self.state = ComponentState(
            name=name,
            degradation_rate=base_rate,
            rul_hours=mtbf_hours,
            maintenance_interval_h=mtbf_hours * 0.5,
        )

    def update(self, load_pct: float, temperature_c: float,
               elapsed_hours: float, dt_hours: float) -> ComponentState:
        s = self.state

        # Load-dependent degradation (quadratic above 80%)
        load_factor = 1.0 + max(0.0, (load_pct - 80.0) * 0.05)
        # Temperature-dependent Arrhenius factor
        temp_factor = 1.0 + max(0.0, (temperature_c - 400.0) * 0.002)
        # Age factor — accelerates past 70% of MTBF
        age_ratio = max(0.0, 1.0 - s.health_pct / 100.0)
        age_factor = 1.0 + age_ratio * 2.0

        # Effective degradation per tick
        noise = float(self._rng.normal(0.0, s.degradation_rate * 0.3))
        effective_deg = s.degradation_rate * load_factor * temp_factor * age_factor * dt_hours + noise
        effective_deg = max(0.0, effective_deg)

        s.health_pct = max(0.0, s.health_pct - effective_deg)
        s.load_factor = load_factor

        # RUL estimation — linear projection
        if effective_deg > 1e-8:
            s.rul_hours = max(0.0, s.health_pct / (effective_deg / dt_hours))
        else:
            s.rul_hours = 99999.0

        # Status classification
        if s.health_pct > 80:
            s.status = "HEALTHY"
        elif s.health_pct > 60:
            s.status = "WATCH"
        elif s.health_pct > 35:
            s.status = "WARNING"
        elif s.health_pct > 0:
            s.status = "CRITICAL"
        else:
            s.status = "FAILED"

        return s

    def perform_maintenance(self, quality: float = 0.95) -> None:
        """Restore health — quality factor (0.5-1.0) determines restoration."""
        self.state.health_pct = min(100.0, self.state.health_pct + (100.0 - self.state.health_pct) * quality)
        self.state.status = "HEALTHY" if self.state.health_pct > 80 else "WATCH"


# ═══════════════════════════════════════════════════════════════════════════
# EWMA Anomaly Detector (simulates LSTM autoencoder behavior)
# ═══════════════════════════════════════════════════════════════════════════
class EWMAAnomalyDetector:
    """Exponentially Weighted Moving Average anomaly detector.
    Acts as a lightweight substitute for a trained LSTM autoencoder.
    """

    def __init__(self, span: int = 100, threshold: float = 2.5):
        self._span = span
        self._threshold = threshold
        self._alpha = 2.0 / (span + 1)
        self._ewma: float | None = None
        self._ewma_var: float | None = None

    def update(self, value: float) -> tuple[float, bool]:
        """Returns (z_score, is_anomaly)."""
        if self._ewma is None:
            self._ewma = value
            self._ewma_var = 0.0
            return (0.0, False)

        # Update EWMA and variance
        diff = value - self._ewma
        self._ewma = self._alpha * value + (1 - self._alpha) * self._ewma
        self._ewma_var = (1 - self._alpha) * (self._ewma_var + self._alpha * diff * diff)

        std = max(math.sqrt(self._ewma_var), 1e-6)
        z_score = abs(diff) / std
        return (round(z_score, 3), z_score > self._threshold)


# ═══════════════════════════════════════════════════════════════════════════
# Maintenance Scheduler
# ═══════════════════════════════════════════════════════════════════════════
@dataclass
class MaintenanceTask:
    component: str
    priority: str           # URGENT | HIGH | MEDIUM | LOW
    action: str
    estimated_hours: float
    spare_parts_needed: bool
    rul_remaining_h: float


class MaintenanceScheduler:
    """Condition-based maintenance scheduler per MIL-STD-3034."""

    @staticmethod
    def generate_schedule(components: list[ComponentHealthModel]) -> list[dict]:
        tasks: list[MaintenanceTask] = []
        for comp in components:
            s = comp.state
            if s.status in ("CRITICAL", "FAILED"):
                tasks.append(MaintenanceTask(
                    component=s.name, priority="URGENT",
                    action=f"Immediate replacement/overhaul of {s.name}",
                    estimated_hours=8.0, spare_parts_needed=True,
                    rul_remaining_h=s.rul_hours,
                ))
            elif s.status == "WARNING":
                tasks.append(MaintenanceTask(
                    component=s.name, priority="HIGH",
                    action=f"Schedule inspection and possible repair of {s.name}",
                    estimated_hours=4.0, spare_parts_needed=True,
                    rul_remaining_h=s.rul_hours,
                ))
            elif s.status == "WATCH":
                tasks.append(MaintenanceTask(
                    component=s.name, priority="MEDIUM",
                    action=f"Monitor {s.name} closely, plan next port maintenance",
                    estimated_hours=2.0, spare_parts_needed=False,
                    rul_remaining_h=s.rul_hours,
                ))

        # Sort by priority
        priority_order = {"URGENT": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        tasks.sort(key=lambda t: priority_order.get(t.priority, 4))

        return [
            {
                "component": t.component,
                "priority": t.priority,
                "action": t.action,
                "estimated_hours": t.estimated_hours,
                "spare_parts_needed": t.spare_parts_needed,
                "rul_remaining_h": round(t.rul_remaining_h, 1),
            }
            for t in tasks
        ]


# ═══════════════════════════════════════════════════════════════════════════
# Predictive Maintenance Engine (top-level orchestrator)
# ═══════════════════════════════════════════════════════════════════════════
class PredictiveMaintenanceEngine:
    """Orchestrates component health tracking, anomaly detection, and
    maintenance scheduling for all monitored mechanical subsystems.
    """

    def __init__(self, seed: int | None = None) -> None:
        base_seed = seed or 42
        self.components: dict[str, ComponentHealthModel] = {
            "main_bearings": ComponentHealthModel("Main Engine Bearings",
                                                   base_rate=0.0005, mtbf_hours=12000, seed=base_seed),
            "turbocharger": ComponentHealthModel("Turbocharger Impeller",
                                                  base_rate=0.0008, mtbf_hours=8000, seed=base_seed + 1),
            "fuel_injectors": ComponentHealthModel("Fuel Injectors (×12)",
                                                    base_rate=0.0010, mtbf_hours=6000, seed=base_seed + 2),
            "lube_oil": ComponentHealthModel("Lube Oil System",
                                              base_rate=0.0006, mtbf_hours=4000, seed=base_seed + 3),
            "coolant_system": ComponentHealthModel("Coolant / Thermostat",
                                                    base_rate=0.0004, mtbf_hours=10000, seed=base_seed + 4),
            "exhaust_valves": ComponentHealthModel("Exhaust Valves (×12)",
                                                    base_rate=0.0009, mtbf_hours=7000, seed=base_seed + 5),
            "governor": ComponentHealthModel("Governor Actuator",
                                              base_rate=0.0003, mtbf_hours=15000, seed=base_seed + 6),
        }

        self._anomaly_detectors: dict[str, EWMAAnomalyDetector] = {
            "rpm": EWMAAnomalyDetector(span=120, threshold=2.8),
            "power": EWMAAnomalyDetector(span=120, threshold=2.5),
            "temperature": EWMAAnomalyDetector(span=120, threshold=3.0),
            "fuel_flow": EWMAAnomalyDetector(span=120, threshold=2.5),
            "vibration": EWMAAnomalyDetector(span=80, threshold=2.2),
        }
        self._rng = np.random.default_rng(base_seed + 100)

    def update(self, rpm: float, power_kw: float, temperature_c: float,
               fuel_flow_kgh: float, mcr_load_pct: float,
               elapsed_hours: float, dt: float) -> dict:
        dt_hours = dt / 3600.0

        # Update all component health models
        component_states: dict[str, dict] = {}
        for key, comp in self.components.items():
            state = comp.update(mcr_load_pct, temperature_c, elapsed_hours, dt_hours)
            component_states[key] = {
                "name": state.name,
                "health_pct": round(state.health_pct, 2),
                "rul_hours": round(state.rul_hours, 1),
                "status": state.status,
                "load_factor": round(state.load_factor, 2),
            }

        # Anomaly detection on key parameters
        vibration_simulated = float(self._rng.exponential(0.3))
        anomalies: dict[str, dict] = {}
        anomaly_params = {
            "rpm": rpm,
            "power": power_kw,
            "temperature": temperature_c,
            "fuel_flow": fuel_flow_kgh,
            "vibration": vibration_simulated,
        }
        total_anomalies = 0
        for param, value in anomaly_params.items():
            z_score, is_anomaly = self._anomaly_detectors[param].update(value)
            anomalies[param] = {
                "z_score": z_score,
                "is_anomaly": is_anomaly,
                "value": round(value, 2),
            }
            if is_anomaly:
                total_anomalies += 1

        # Generate maintenance schedule
        schedule = MaintenanceScheduler.generate_schedule(list(self.components.values()))

        # Overall system health
        healths = [s["health_pct"] for s in component_states.values()]
        mean_health = sum(healths) / len(healths) if healths else 100.0
        min_health = min(healths) if healths else 100.0
        critical_count = sum(1 for s in component_states.values() if s["status"] in ("CRITICAL", "FAILED"))

        return {
            "components": component_states,
            "anomaly_detection": anomalies,
            "total_anomalies_active": total_anomalies,
            "maintenance_schedule": schedule,
            "system_health": {
                "mean_health_pct": round(mean_health, 1),
                "min_component_health_pct": round(min_health, 1),
                "critical_components": critical_count,
                "pending_tasks": len(schedule),
                "overall_status": "CRITICAL" if critical_count > 0 else
                                  "WARNING" if min_health < 50 else
                                  "WATCH" if min_health < 70 else "HEALTHY",
            },
        }
