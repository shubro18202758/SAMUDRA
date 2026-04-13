"""
physics/eexi_compliance.py — EEXI & Enhanced CII Compliance Engine
==================================================================
Implements Energy Efficiency Existing Ship Index (EEXI) calculation and
enhanced CII monitoring per IMO MEPC.328(76) and MEPC.352(78).

EEXI Calculation
----------------
The EEXI quantifies the design energy efficiency of an existing ship:

    EEXI = (CF × SFC × P_ME × fw) / (fi × fc × Capacity × Vref)

Where:
- CF = CO₂ conversion factor for fuel type (3.114 for HFO)
- SFC = Specific Fuel Consumption (g/kWh)
- P_ME = Main engine power (kW) × reduction factor
- fw = Weather correction factor
- fi = Technical correction factor (ice class, etc.)
- fc = Cubic capacity correction (for chemical tankers)
- Capacity = DWT (or GT for passenger/ro-ro)
- Vref = Reference speed at design draft (kts → m/s)

OPV-Specific Implementation
----------------------------
Since naval vessels are typically exempt from MARPOL Annex VI, this module
implements EEXI as a VOLUNTARY compliance benchmark per the ICG's
environmental stewardship objectives, providing:
- Real-time EEXI calculation
- Required EEXI limit estimation (based on reference line)
- EEXI attainment status
- Technical measures for compliance (EPL, shaft generator, etc.)

Enhanced CII
------------
Extends existing CII module with:
- Annual CII trajectory tracking
- Required Annual Operational Carbon Intensity Indicator (CIIreq)
- Correction factors (voyage adjustments)
- Penalty-free CII optimization recommendations

Reference Standards
-------------------
- MEPC.328(76): EEXI regulations
- MEPC.352(78): CII regulations
- MEPC.1/Circ.896: EEXI calculation guidelines
- MEPC.364(79): Reference line parameters

Author : SAMUDRA Backend — Phase 4 (EEXI Compliance)
"""

from __future__ import annotations

import math
from collections import deque
from dataclasses import dataclass
from typing import Any

import numpy as np


# ═══════════════════════════════════════════════════════════════════════════
# Constants for ICG OPV (2,350 DWT-equivalent)
# ═══════════════════════════════════════════════════════════════════════════
_CF_HFO = 3.114          # CO₂ conversion factor for HFO (tCO₂/tFuel)
_CF_MDO = 3.206           # MDO
_CF_LNG = 2.750           # LNG
_SFC_DESIGN = 185.0       # Specific Fuel Consumption at MCR (g/kWh)
_MCR_KW = 8500.0          # Main engine MCR
_VREF_KTS = 14.5          # Reference speed at design draft
_DWT = 2350.0             # Deadweight tonnage (approximate for OPV)
_GT = 2200.0              # Gross tonnage
_DESIGN_DRAFT_M = 4.2     # Design draft
_KTS_TO_MS = 0.5144

# EEXI reference line parameters (naval vessel — using general cargo as proxy)
# EEXI_ref = a × DWT^(-c) → for general cargo: a=174.22, c=0.201
_EEXI_REF_A = 174.22
_EEXI_REF_C = 0.201

# Reduction factors (MEPC.364(79)) — Phase 1 (from 2023)
_EEXI_REDUCTION_FACTOR = 0.15  # 15% below reference line

# CII reference line: CIIref = a × DWT^(-c)
# For general cargo: a=4745, c=0.610
_CII_REF_A = 4745.0
_CII_REF_C = 0.610

# CII reduction factors (annual tightening)
_CII_REDUCTIONS = {
    2023: 0.05, 2024: 0.07, 2025: 0.09,
    2026: 0.11, 2027: 0.13, 2028: 0.15,
    2029: 0.17, 2030: 0.20,
}


# ═══════════════════════════════════════════════════════════════════════════
# EEXI Calculator
# ═══════════════════════════════════════════════════════════════════════════
class EEXICalculator:
    """Calculates attained EEXI and required EEXI for ICG OPV."""

    def __init__(self, epl_applied: bool = False,
                 shaft_generator_kw: float = 0.0) -> None:
        self._epl_applied = epl_applied        # Engine Power Limitation
        self._shaft_gen_kw = shaft_generator_kw
        self._epl_fraction = 0.75 if epl_applied else 1.0  # Limit to 75% MCR

    def calculate(self, current_sfc_gkwh: float | None = None,
                  weather_factor: float = 1.0) -> dict:
        sfc = current_sfc_gkwh or _SFC_DESIGN

        # Effective engine power after EPL
        p_me = _MCR_KW * self._epl_fraction

        # Shaft generator deduction
        p_ae = max(0.0, p_me * 0.025 - self._shaft_gen_kw)

        # Weather correction (fw typically 0.9-1.0)
        fw = max(0.5, min(1.0, weather_factor))

        # Reference speed adjusted for EPL (V^3 ∝ P → V ∝ P^(1/3))
        v_ref_kts = _VREF_KTS * (self._epl_fraction ** (1.0 / 3.0))
        v_ref_ms = v_ref_kts * _KTS_TO_MS

        # fi = 1.0 (no ice class), fc = 1.0 (not chemical tanker)
        fi = 1.0
        fc = 1.0

        # Attained EEXI (gCO₂ / (tonne × nautical mile))
        numerator = _CF_HFO * sfc * p_me * fw
        denominator = fi * fc * _DWT * v_ref_kts  # Using kts for maritime convention
        attained_eexi = numerator / max(denominator, 1.0)

        # Required EEXI (reference line × (1 - reduction))
        eexi_ref = _EEXI_REF_A * (_DWT ** (-_EEXI_REF_C))
        required_eexi = eexi_ref * (1.0 - _EEXI_REDUCTION_FACTOR)

        # Compliance status
        compliant = attained_eexi <= required_eexi
        margin_pct = ((required_eexi - attained_eexi) / required_eexi * 100.0) if required_eexi > 0 else 0.0

        # Technical measures available
        measures: list[dict] = []
        if not self._epl_applied and not compliant:
            potential = attained_eexi * 0.75 / max(attained_eexi, 1e-6) * 100.0
            measures.append({
                "measure": "Engine Power Limitation (EPL)",
                "reduction_pct": round(25.0, 1),
                "cost_estimate_usd": "50,000 - 100,000",
                "implementation_time": "1-2 weeks",
            })
        if self._shaft_gen_kw == 0:
            measures.append({
                "measure": "Shaft Generator Installation",
                "reduction_pct": round(5.0, 1),
                "cost_estimate_usd": "200,000 - 400,000",
                "implementation_time": "4-6 weeks (dry-dock)",
            })
        if not compliant:
            measures.append({
                "measure": "Energy Saving Device (ESD) — Propeller Boss Cap Fin",
                "reduction_pct": round(3.0, 1),
                "cost_estimate_usd": "30,000 - 60,000",
                "implementation_time": "1 week (dry-dock)",
            })
            measures.append({
                "measure": "Advanced Anti-Fouling Coating (FR Type)",
                "reduction_pct": round(4.0, 1),
                "cost_estimate_usd": "80,000 - 120,000",
                "implementation_time": "2 weeks (dry-dock)",
            })

        return {
            "attained_eexi": round(attained_eexi, 3),
            "required_eexi": round(required_eexi, 3),
            "eexi_reference_line": round(eexi_ref, 3),
            "reduction_factor_pct": round(_EEXI_REDUCTION_FACTOR * 100, 1),
            "compliant": compliant,
            "margin_pct": round(margin_pct, 2),
            "epl_applied": self._epl_applied,
            "epl_power_limit_kw": round(_MCR_KW * self._epl_fraction, 0),
            "shaft_generator_kw": self._shaft_gen_kw,
            "sfc_gkwh": round(sfc, 1),
            "reference_speed_kts": round(v_ref_kts, 2),
            "technical_measures": measures,
            "cf_fuel": _CF_HFO,
            "status": "COMPLIANT" if compliant else "NON_COMPLIANT",
        }


# ═══════════════════════════════════════════════════════════════════════════
# Enhanced CII Tracker (Annual Trajectory)
# ═══════════════════════════════════════════════════════════════════════════
class EnhancedCIITracker:
    """Tracks annual CII trajectory with voyage-level granularity.

    CII_attained = (total CO₂ emissions) / (capacity × distance sailed)
    Unit: gCO₂ / (tonne × nautical mile)
    """

    def __init__(self, year: int = 2025) -> None:
        self._year = year
        self._total_co2_tonnes = 0.0
        self._total_distance_nm = 0.0
        self._voyage_count = 0
        self._daily_cii: deque[float] = deque(maxlen=365)

    def update(self, fuel_consumed_kg: float, distance_nm: float,
               fuel_type: str = "HFO") -> dict:
        cf = {"HFO": _CF_HFO, "MDO": _CF_MDO, "LNG": _CF_LNG}.get(fuel_type, _CF_HFO)

        co2_tonnes = fuel_consumed_kg * cf / 1000.0
        self._total_co2_tonnes += co2_tonnes
        self._total_distance_nm += distance_nm

        if distance_nm > 0:
            daily_cii = (co2_tonnes * 1e6) / (_DWT * distance_nm)  # gCO₂/(t·nm)
            self._daily_cii.append(daily_cii)

        # Annual attained CII
        if self._total_distance_nm > 0 and _DWT > 0:
            attained_cii = (self._total_co2_tonnes * 1e6) / (_DWT * self._total_distance_nm)
        else:
            attained_cii = 0.0

        # Required CII
        cii_ref = _CII_REF_A * (_DWT ** (-_CII_REF_C))
        reduction = _CII_REDUCTIONS.get(self._year, 0.15)
        required_cii = cii_ref * (1.0 - reduction)

        # Rating bands (A through E)
        d1 = 0.82  # A-B boundary
        d2 = 0.93  # B-C boundary
        d3 = 1.08  # C-D boundary
        d4 = 1.28  # D-E boundary

        ratio = attained_cii / max(required_cii, 1e-6)
        if ratio <= d1:
            rating = "A"
        elif ratio <= d2:
            rating = "B"
        elif ratio <= d3:
            rating = "C"
        elif ratio <= d4:
            rating = "D"
        else:
            rating = "E"

        # Trajectory to year-end (projected)
        days_elapsed = len(self._daily_cii)
        if days_elapsed > 0:
            avg_daily_cii = float(np.mean(list(self._daily_cii)))
            projected_annual_cii = avg_daily_cii  # CII is already normalized
        else:
            projected_annual_cii = 0.0

        # Days remaining margin
        margin_pct = ((required_cii - attained_cii) / required_cii * 100.0) if required_cii > 0 else 0.0

        # Optimization potential
        recommendations: list[str] = []
        if rating in ("D", "E"):
            recommendations.append("URGENT: Reduce speed by 2-3 kts to improve CII rating")
            recommendations.append("Consider weather routing to reduce fuel consumption")
            recommendations.append("Schedule hull cleaning to reduce resistance")
        elif rating == "C":
            recommendations.append("Monitor closely — approaching D boundary")
            recommendations.append("Optimize trim to reduce fuel by 1-2%")
        elif rating in ("A", "B"):
            recommendations.append("Excellent operational efficiency — maintain current practices")

        return {
            "attained_cii": round(attained_cii, 3),
            "required_cii": round(required_cii, 3),
            "cii_reference": round(cii_ref, 3),
            "reduction_factor_pct": round(reduction * 100, 1),
            "rating": rating,
            "rating_ratio": round(ratio, 4),
            "rating_boundaries": {"A_B": d1, "B_C": d2, "C_D": d3, "D_E": d4},
            "total_co2_tonnes": round(self._total_co2_tonnes, 2),
            "total_distance_nm": round(self._total_distance_nm, 1),
            "margin_pct": round(margin_pct, 2),
            "projected_annual_cii": round(projected_annual_cii, 3),
            "days_tracked": days_elapsed,
            "year": self._year,
            "recommendations": recommendations,
            "status": "COMPLIANT" if rating in ("A", "B", "C") else "ACTION_REQUIRED",
        }


# ═══════════════════════════════════════════════════════════════════════════
# Emission Factors & IMO DCS Reporting
# ═══════════════════════════════════════════════════════════════════════════
class IMODCSReporter:
    """IMO Data Collection System (DCS) — annual fuel consumption reporting.

    MEPC.278(70): Ships ≥ 5000 GT must report annually.
    ICG OPVs participate voluntarily as environmental stewardship.
    """

    def __init__(self) -> None:
        self._fuel_records: deque[dict] = deque(maxlen=10000)
        self._total_hfo_tonnes = 0.0
        self._total_mdo_tonnes = 0.0
        self._total_hours_underway = 0.0
        self._total_distance_nm = 0.0

    def record_consumption(self, fuel_type: str, fuel_kg: float,
                           distance_nm: float, hours: float) -> None:
        self._fuel_records.append({
            "fuel_type": fuel_type,
            "fuel_kg": fuel_kg,
            "distance_nm": distance_nm,
            "hours": hours,
        })
        if fuel_type == "HFO":
            self._total_hfo_tonnes += fuel_kg / 1000.0
        else:
            self._total_mdo_tonnes += fuel_kg / 1000.0
        self._total_hours_underway += hours
        self._total_distance_nm += distance_nm

    def generate_report(self) -> dict:
        total_fuel = self._total_hfo_tonnes + self._total_mdo_tonnes
        total_co2 = (self._total_hfo_tonnes * _CF_HFO + self._total_mdo_tonnes * _CF_MDO)
        aer = (total_co2 * 1e6 / (_DWT * max(self._total_distance_nm, 1.0)))

        return {
            "imo_number": "ICG-OPV-2350",
            "vessel_type": "Offshore Patrol Vessel",
            "gt": _GT,
            "dwt": _DWT,
            "total_hfo_tonnes": round(self._total_hfo_tonnes, 2),
            "total_mdo_tonnes": round(self._total_mdo_tonnes, 2),
            "total_fuel_tonnes": round(total_fuel, 2),
            "total_co2_tonnes": round(total_co2, 2),
            "total_distance_nm": round(self._total_distance_nm, 1),
            "total_hours_underway": round(self._total_hours_underway, 1),
            "annual_efficiency_ratio": round(aer, 3),
            "records_count": len(self._fuel_records),
        }


# ═══════════════════════════════════════════════════════════════════════════
# Top-Level EEXI Compliance Engine
# ═══════════════════════════════════════════════════════════════════════════
class EEXIComplianceEngine:
    """Unified EEXI + Enhanced CII + DCS reporting engine."""

    def __init__(self, year: int = 2025, epl_applied: bool = False) -> None:
        self.eexi_calculator = EEXICalculator(epl_applied=epl_applied)
        self.cii_tracker = EnhancedCIITracker(year=year)
        self.dcs_reporter = IMODCSReporter()

    def update(self, fuel_consumed_kg: float, distance_nm: float,
               sfc_gkwh: float, weather_factor: float = 1.0,
               fuel_type: str = "HFO", dt_hours: float = 0.0) -> dict:
        eexi = self.eexi_calculator.calculate(sfc_gkwh, weather_factor)
        cii = self.cii_tracker.update(fuel_consumed_kg, distance_nm, fuel_type)
        self.dcs_reporter.record_consumption(fuel_type, fuel_consumed_kg, distance_nm, dt_hours)
        dcs = self.dcs_reporter.generate_report()

        return {
            "eexi": eexi,
            "cii_enhanced": cii,
            "dcs_report": dcs,
        }
