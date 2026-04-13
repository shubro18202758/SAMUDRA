"""
physics/hull_propulsion.py — Hull Improvement & Hybrid Propulsion Modelling
==========================================================================
Models anti-fouling coating performance, hull cleaning scheduling, and
hybrid-electric propulsion systems for Indian Coast Guard OPVs.

Hull Coatings & Maintenance
---------------------------
1. **Anti-Fouling Coating Model**
   - SPC (Self-Polishing Copolymer) erosion profile
   - Foul-Release (FR) silicone coating degradation
   - Hull roughness (AHR — Average Hull Roughness) tracking per ISO 19030
   - Coating lifespan projection with sea temperature dependency

2. **Hull Cleaning Scheduler**
   - ROI-based cleaning interval calculator
   - Diver vs robotic cleaning cost model
   - Fuel penalty breakeven analysis
   - Dry-dock scheduling recommendations

Hybrid Propulsion
-----------------
3. **Diesel-Electric Hybrid Model**
   - Combined Diesel-Electric and Diesel-Mechanical (CODLAG variant)
   - Battery State of Charge (SoC) tracking
   - Electric motor assist mode (harbor/patrol)
   - Regenerative braking during deceleration
   - Optimal power split based on operational mode

Reference Standards
-------------------
- ISO 19030: Hull and propeller performance monitoring
- MEPC.1/Circ.833: Guidance on hull fouling management
- IMO GHG Strategy 2023: Lifecycle CO₂ intensity targets
- Lloyd's Register: ShipRight hull performance monitoring

Author : SAMUDRA Backend — Phase 4 (Hull & Propulsion)
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import numpy as np


# ═══════════════════════════════════════════════════════════════════════════
# Anti-Fouling Coating Model
# ═══════════════════════════════════════════════════════════════════════════
@dataclass
class CoatingProfile:
    """Represents a hull coating system with degradation characteristics."""
    name: str
    initial_roughness_um: float   # µm AHR at application
    roughness_growth_um_month: float   # Monthly growth rate (clean tropical water)
    sst_factor: float             # Temperature sensitivity multiplier
    lifespan_months: int
    cost_per_m2_usd: float
    type: str                     # "SPC" or "FR"


# Standard ICG coating options
SPC_COATING = CoatingProfile(
    name="International Intersmooth 7460HS (SPC)",
    initial_roughness_um=75.0,
    roughness_growth_um_month=2.5,
    sst_factor=0.08,  # Extra µm per °C above 20°C per month
    lifespan_months=60,
    cost_per_m2_usd=28.0,
    type="SPC",
)

FR_COATING = CoatingProfile(
    name="Hempel Hempaguard X7 (Foul-Release)",
    initial_roughness_um=50.0,
    roughness_growth_um_month=1.2,
    sst_factor=0.04,
    lifespan_months=72,
    cost_per_m2_usd=55.0,
    type="FR",
)


class HullCoatingModel:
    """Tracks hull coating degradation and roughness buildup.

    Uses ISO 19030 methodology to relate AHR to added resistance (ΔR).
    Townsin (1981): ΔCf = 0.044 * [(AHR/10)^(1/3) - 10*(Re)^(-1/3)] + 0.000125
    Simplified: ΔR/R ≈ AHR_increase / 100 (% resistance increase per 100µm)
    """

    # Wetted surface area for OPV 2,350t (approx)
    _WETTED_AREA_M2 = 1450.0

    def __init__(self, coating: CoatingProfile | None = None,
                 seed: int | None = None) -> None:
        self._rng = np.random.default_rng(seed)
        self.coating = coating or SPC_COATING
        self._current_roughness_um = self.coating.initial_roughness_um
        self._age_months = 0.0
        self._last_cleaning_month = 0.0
        self._total_fuel_penalty_tonnes = 0.0

    def update(self, sst_c: float, sog_kts: float, fuel_flow_kgh: float,
               dt_hours: float) -> dict:
        dt_months = dt_hours / (30.0 * 24.0)
        self._age_months += dt_months

        # Temperature-modulated roughness growth
        temp_excess = max(0.0, sst_c - 20.0)
        growth_rate = (self.coating.roughness_growth_um_month +
                       self.coating.sst_factor * temp_excess)
        noise = float(self._rng.normal(0.0, growth_rate * 0.1))
        roughness_growth = max(0.0, (growth_rate + noise) * dt_months)
        self._current_roughness_um += roughness_growth

        # Added resistance fraction (Townsin-simplified)
        roughness_increase_um = self._current_roughness_um - self.coating.initial_roughness_um
        added_resistance_pct = roughness_increase_um / 100.0 * 0.5  # ~0.5% per 100µm

        # Fuel penalty estimation
        fuel_penalty_kgh = fuel_flow_kgh * (added_resistance_pct / 100.0)
        self._total_fuel_penalty_tonnes += fuel_penalty_kgh * dt_hours / 1e6

        # Speed loss at constant power
        speed_loss_pct = added_resistance_pct / 3.0  # ∝ V³ law inverse

        # Coating remaining life
        remaining_months = max(0.0, self.coating.lifespan_months - self._age_months)
        coating_health_pct = max(0.0, remaining_months / self.coating.lifespan_months * 100.0)

        # Cleaning recommendation
        months_since_cleaning = self._age_months - self._last_cleaning_month
        cleaning_recommended = (
            roughness_increase_um > 80.0 or
            added_resistance_pct > 2.5 or
            months_since_cleaning > 12
        )

        return {
            "coating_type": self.coating.type,
            "coating_name": self.coating.name,
            "current_roughness_um": round(self._current_roughness_um, 1),
            "roughness_increase_um": round(roughness_increase_um, 1),
            "added_resistance_pct": round(added_resistance_pct, 2),
            "fuel_penalty_kgh": round(fuel_penalty_kgh, 2),
            "speed_loss_pct": round(speed_loss_pct, 2),
            "coating_age_months": round(self._age_months, 1),
            "coating_health_pct": round(coating_health_pct, 1),
            "coating_remaining_months": round(remaining_months, 1),
            "cleaning_recommended": cleaning_recommended,
            "months_since_cleaning": round(months_since_cleaning, 1),
            "wetted_area_m2": self._WETTED_AREA_M2,
            "total_fuel_penalty_tonnes": round(self._total_fuel_penalty_tonnes, 4),
        }

    def perform_cleaning(self, method: str = "robotic") -> dict:
        """Hull cleaning restores roughness partially."""
        restoration = 0.70 if method == "diver" else 0.85 if method == "robotic" else 0.95
        old = self._current_roughness_um
        self._current_roughness_um = (
            self.coating.initial_roughness_um +
            (self._current_roughness_um - self.coating.initial_roughness_um) * (1.0 - restoration)
        )
        self._last_cleaning_month = self._age_months
        cost = {"diver": 8000, "robotic": 15000, "drydock": 180000}
        return {
            "method": method,
            "roughness_before_um": round(old, 1),
            "roughness_after_um": round(self._current_roughness_um, 1),
            "estimated_cost_usd": cost.get(method, 0),
        }


# ═══════════════════════════════════════════════════════════════════════════
# Hull Cleaning ROI Calculator
# ═══════════════════════════════════════════════════════════════════════════
class CleaningROICalculator:
    """Calculates whether hull cleaning pays off based on fuel savings vs cost."""

    FUEL_COST_USD_PER_TONNE = 600.0
    DAILY_FUEL_TONNES = 12.0  # Approximate for OPV at patrol speed

    @staticmethod
    def calculate_roi(added_resistance_pct: float,
                      cleaning_cost_usd: float) -> dict:
        daily_penalty_tonnes = CleaningROICalculator.DAILY_FUEL_TONNES * (added_resistance_pct / 100.0)
        daily_savings_usd = daily_penalty_tonnes * CleaningROICalculator.FUEL_COST_USD_PER_TONNE

        if daily_savings_usd > 0:
            breakeven_days = cleaning_cost_usd / daily_savings_usd
        else:
            breakeven_days = 9999.0

        annual_savings_usd = daily_savings_usd * 300  # ~300 sea days/year

        return {
            "daily_fuel_penalty_tonnes": round(daily_penalty_tonnes, 3),
            "daily_savings_usd": round(daily_savings_usd, 0),
            "breakeven_days": round(breakeven_days, 1),
            "annual_savings_usd": round(annual_savings_usd, 0),
            "roi_positive": breakeven_days < 180,
        }


# ═══════════════════════════════════════════════════════════════════════════
# Hybrid Propulsion — CODLAG (Combined Diesel-Electric and Gas)
# ═══════════════════════════════════════════════════════════════════════════
class HybridPropulsionSystem:
    """Diesel-Electric hybrid propulsion model for ICG OPV.

    Operational Modes:
    - DIESEL_MECHANICAL: Full diesel, direct drive (transit/sprint)
    - DIESEL_ELECTRIC: Generators → electric motor (patrol/loiter)
    - HYBRID: Diesel + electric motor assist (moderate load)
    - ELECTRIC_ONLY: Battery-powered silent running (harbor/covert)
    - REGENERATIVE: Deceleration energy recovery

    Battery: Lithium Iron Phosphate (LFP) 500 kWh pack
    Electric Motor: 800 kW permanent magnet synchronous
    """

    _BATTERY_CAPACITY_KWH = 500.0
    _MOTOR_RATED_KW = 800.0
    _CHARGE_EFFICIENCY = 0.92
    _DISCHARGE_EFFICIENCY = 0.94
    _REGEN_EFFICIENCY = 0.35
    _MIN_SOC = 0.15   # Don't discharge below 15%
    _MAX_SOC = 0.95   # Don't charge above 95%
    _DIESEL_EFF_BASE = 0.42  # Diesel thermal efficiency at optimal load
    _ELECTRIC_EFF = 0.92

    def __init__(self, seed: int | None = None) -> None:
        self._rng = np.random.default_rng(seed)
        self._soc = 0.80  # Start at 80% SoC
        self._mode = "DIESEL_MECHANICAL"
        self._total_electric_kwh = 0.0
        self._total_regen_kwh = 0.0

    def update(self, required_power_kw: float, sog_kts: float,
               mission_state: str, dt: float) -> dict:
        dt_hours = dt / 3600.0

        # Auto-select propulsion mode based on operational state
        if mission_state == "ANCHORED" or sog_kts < 2.0:
            mode = "ELECTRIC_ONLY" if self._soc > self._MIN_SOC + 0.1 else "DIESEL_ELECTRIC"
        elif mission_state in ("SAR_LOITER", "PATROL") and sog_kts < 8.0:
            mode = "DIESEL_ELECTRIC"
        elif mission_state == "TRANSIT" and required_power_kw > 6000:
            mode = "DIESEL_MECHANICAL"
        elif mission_state == "SPRINT_INT":
            mode = "HYBRID" if self._soc > 0.3 else "DIESEL_MECHANICAL"
        else:
            mode = "HYBRID" if self._soc > 0.25 else "DIESEL_MECHANICAL"

        self._mode = mode

        # Power split calculation
        diesel_power_kw = 0.0
        electric_power_kw = 0.0
        battery_power_kw = 0.0  # +charging, -discharging
        fuel_saving_pct = 0.0

        if mode == "DIESEL_MECHANICAL":
            diesel_power_kw = required_power_kw
        elif mode == "DIESEL_ELECTRIC":
            # Diesel runs at optimal load, excess charges battery
            optimal_diesel = required_power_kw * 0.8
            diesel_power_kw = optimal_diesel
            electric_power_kw = required_power_kw * 0.2
            if self._soc < self._MAX_SOC:
                charge_kw = min(200.0, (self._MAX_SOC - self._soc) * self._BATTERY_CAPACITY_KWH / dt_hours * 0.1)
                battery_power_kw = charge_kw
                self._soc = min(self._MAX_SOC,
                                self._soc + charge_kw * dt_hours * self._CHARGE_EFFICIENCY / self._BATTERY_CAPACITY_KWH)
            fuel_saving_pct = 15.0
        elif mode == "HYBRID":
            electric_share = min(0.3, self._soc - self._MIN_SOC)
            electric_power_kw = min(self._MOTOR_RATED_KW, required_power_kw * electric_share)
            diesel_power_kw = required_power_kw - electric_power_kw
            discharge_kwh = electric_power_kw * dt_hours / self._DISCHARGE_EFFICIENCY
            self._soc = max(self._MIN_SOC,
                            self._soc - discharge_kwh / self._BATTERY_CAPACITY_KWH)
            self._total_electric_kwh += electric_power_kw * dt_hours
            fuel_saving_pct = (electric_power_kw / required_power_kw * 100.0) if required_power_kw > 0 else 0
        elif mode == "ELECTRIC_ONLY":
            electric_power_kw = min(self._MOTOR_RATED_KW, required_power_kw)
            discharge_kwh = electric_power_kw * dt_hours / self._DISCHARGE_EFFICIENCY
            self._soc = max(self._MIN_SOC,
                            self._soc - discharge_kwh / self._BATTERY_CAPACITY_KWH)
            self._total_electric_kwh += electric_power_kw * dt_hours
            fuel_saving_pct = 100.0

        # Regenerative braking check (when decelerating)
        regen_kw = 0.0
        # Not directly tracked here; integrated via speed change in hydrodynamics

        # Battery state
        battery_kwh = self._soc * self._BATTERY_CAPACITY_KWH
        range_electric_h = 0.0
        if electric_power_kw > 10:
            range_electric_h = (battery_kwh * self._DISCHARGE_EFFICIENCY) / electric_power_kw

        # CO₂ reduction estimation
        diesel_co2_kgh = diesel_power_kw * 0.000650  # ~650 g/kWh for marine diesel
        full_diesel_co2_kgh = required_power_kw * 0.000650
        co2_reduction_pct = ((full_diesel_co2_kgh - diesel_co2_kgh) / full_diesel_co2_kgh * 100.0
                             if full_diesel_co2_kgh > 0 else 0.0)

        return {
            "propulsion_mode": mode,
            "diesel_power_kw": round(diesel_power_kw, 1),
            "electric_power_kw": round(electric_power_kw, 1),
            "total_power_kw": round(diesel_power_kw + electric_power_kw, 1),
            "battery_soc_pct": round(self._soc * 100.0, 1),
            "battery_kwh_remaining": round(battery_kwh, 1),
            "battery_capacity_kwh": self._BATTERY_CAPACITY_KWH,
            "electric_range_hours": round(range_electric_h, 1),
            "fuel_saving_pct": round(fuel_saving_pct, 1),
            "co2_reduction_pct": round(co2_reduction_pct, 1),
            "total_electric_kwh_used": round(self._total_electric_kwh, 1),
            "motor_rated_kw": self._MOTOR_RATED_KW,
            "motor_load_pct": round(electric_power_kw / self._MOTOR_RATED_KW * 100.0, 1),
        }


# ═══════════════════════════════════════════════════════════════════════════
# Top-Level Hull & Propulsion Engine
# ═══════════════════════════════════════════════════════════════════════════
class HullPropulsionEngine:
    """Unified hull coating management + hybrid propulsion system."""

    def __init__(self, seed: int | None = None) -> None:
        self.hull_coating = HullCoatingModel(coating=SPC_COATING, seed=seed)
        self.hybrid = HybridPropulsionSystem(seed=seed)
        self._roi_calc = CleaningROICalculator()

    def update(self, sst_c: float, sog_kts: float, fuel_flow_kgh: float,
               required_power_kw: float, mission_state: str, dt: float) -> dict:
        hull = self.hull_coating.update(sst_c, sog_kts, fuel_flow_kgh, dt / 3600.0)
        hybrid = self.hybrid.update(required_power_kw, sog_kts, mission_state, dt)

        # Cleaning ROI if cleaning is recommended
        cleaning_roi = {}
        if hull["cleaning_recommended"]:
            cleaning_roi = self._roi_calc.calculate_roi(
                hull["added_resistance_pct"],
                15000.0,  # Robotic cleaning default
            )

        return {
            "hull_coating": hull,
            "hybrid_propulsion": hybrid,
            "cleaning_roi": cleaning_roi,
        }
