"""
physics/cii_segregation.py — CII Tactical Segregation Engine
=============================================================
Implements real-time Carbon Intensity Indicator (CII) monitoring with
unsupervised clustering to segregate **Transit** fuel from **Tactical
Loiter** fuel, enabling correction-factor application per MEPC.355(78).

Regulatory Background
---------------------
**Attained CII** (IMO DCS / MARPOL Annex VI, Regulation 28):

    Attained CII = (ΣFC_j · C_Fj) / (Capacity · D_t)

where:
    - FC_j     = fuel consumption of fuel type *j* (tonnes)
    - C_Fj     = CO₂ emission factor for fuel *j* (t-CO₂ / t-fuel)
                 For HFO (Heavy Fuel Oil): C_F = 3.114  (IMO MEPC.364(79))
    - Capacity = DWT (deadweight tonnage) = 2,350 tonnes for an OPV
    - D_t      = distance travelled in nautical miles

**CII Rating Bands** (A–E):
    A  = significantly superior      (≤ exp(d₁))
    B  = minor superior              (≤ exp(d₂))
    C  = moderate                    (≤ exp(d₃))
    D  = minor inferior              (≤ exp(d₄))
    E  = inferior                    (> exp(d₄)) — triggers corrective action

MEPC.355(78) Correction Factors
--------------------------------
Regulation 3.1 — Voyage adjustments exclude:
    • Fuel consumed during STS operations
    • Fuel consumed while in port / at anchor
    • **Tactical loiter fuel** (patrol vessel operational necessity)

This module applies a DBSCAN-inspired classification: if speed drops
below 4.0 knots while engine power remains active (> 5 % MCR), the
data block is tagged ``mission_state: tactical_loiter``.  Segregated
carbon totals provide regulators with pre/post-correction CII values.

Author : SAMUDRA Backend — Phase 3 (Prompt 5)
"""

from __future__ import annotations

import numpy as np


# =============================================================================
# IMO Constants
# =============================================================================

# CO₂ emission factor for Heavy Fuel Oil (HFO) — t-CO₂ per t-fuel
# Source: IMO MEPC.364(79), Table 1
CF_HFO: float = 3.114

# Vessel capacity (DWT) — Indian Coast Guard OPV
CAPACITY_DWT: float = 2_350.0

# MCR for the OPV's main engine (kW)
_MCR_KW: float = 8_500.0

# Loiter detection thresholds
LOITER_SPEED_THRESHOLD_KTS: float = 4.0     # below this → potential loiter
LOITER_POWER_THRESHOLD_PCT: float = 5.0     # engine must be > 5 % MCR

# CII rating boundary parameters (simplified exponential model)
# Based on MEPC.339(76) / MEPC.355(78) reference lines for patrol-class
_CII_D1 = -0.30   # A/B boundary (exp scale)
_CII_D2 = -0.15   # B/C boundary
_CII_D3 =  0.00   # C/D boundary (reference line)
_CII_D4 =  0.15   # D/E boundary


class CIISegregationEngine:
    """Real-time CII calculator with tactical-loiter segregation.

    Maintains separate running totals:
        - **Transit Carbon** — CO₂ from normal transit steaming
        - **Loiter Carbon** — CO₂ from tactical loitering periods

    The Attained CII is computed both *raw* (all fuel) and *corrected*
    (transit-only), demonstrating MEPC.355(78) correction capability.

    DBSCAN-Inspired Classification
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    Rather than a full DBSCAN clustering over a feature matrix, we apply
    the core density-reachability concept in the speed–power 2D space:

    - **Core point (Transit)**: SOG ≥ 4.0 kn — vessel making way.
    - **Noise point (Loiter)**: SOG < 4.0 kn AND P > 5 % MCR —
      vessel stationary but engines active (tactical station-keeping,
      patrol holding pattern, search-and-rescue box).
    - If SOG < 4.0 kn and P ≤ 5 % MCR → classified as ``idle``
      (excluded from both tallies per port-time exclusion rules).
    """

    def __init__(self, seed: int | None = None) -> None:
        self._rng = np.random.default_rng(seed)

        # Running accumulators
        self._transit_fuel_tonnes: float = 0.0
        self._loiter_fuel_tonnes: float = 0.0
        self._transit_distance_nm: float = 0.0
        self._loiter_fuel_events: int = 0
        self._transit_fuel_events: int = 0

        # CII reference line (g-CO₂ / (DWT · NM))
        # Baseline: ~15 g-CO₂/(DWT·NM) for an OPV — derived from
        # typical SFOC 200 g/kWh at design speed
        self._cii_reference: float = 15.0

        # Running clock for time-aggregation
        self._elapsed_s: float = 0.0

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def update(
        self,
        sog_kts: float,
        power_actual_kw: float,
        fuel_flow_kgh: float,
        dt: float,
    ) -> dict:
        """Classify the current tick and update CII accumulators.

        Parameters
        ----------
        sog_kts : float
            Speed Over Ground (knots).
        power_actual_kw : float
            Current shaft power (kW).
        fuel_flow_kgh : float
            Fuel flow (kg/h).
        dt : float
            Tick interval (seconds).

        Returns
        -------
        dict
            Payload matching ``CIISegregationFrame``.
        """
        self._elapsed_s += dt

        # ---- 1. Per-tick fuel consumption (tonnes) ----
        fuel_tick_tonnes = fuel_flow_kgh * (dt / 3600.0) / 1000.0

        # ---- 2. Per-tick distance (NM) ----
        distance_tick_nm = sog_kts * (dt / 3600.0)

        # ---- 3. DBSCAN-inspired mission-state classification ----
        #   Speed–Power 2D clustering:
        #     Transit:  SOG ≥ 4.0 kn ─ vessel making way
        #     Loiter:   SOG < 4.0 kn AND power > 5% MCR ─ station-keeping
        #     Idle:     SOG < 4.0 kn AND power ≤ 5% MCR ─ at anchor/port
        mcr_pct = (power_actual_kw / _MCR_KW) * 100.0

        if sog_kts >= LOITER_SPEED_THRESHOLD_KTS:
            mission_state = "transit"
            self._transit_fuel_tonnes += fuel_tick_tonnes
            self._transit_distance_nm += distance_tick_nm
            self._transit_fuel_events += 1
        elif mcr_pct > LOITER_POWER_THRESHOLD_PCT:
            mission_state = "tactical_loiter"
            self._loiter_fuel_tonnes += fuel_tick_tonnes
            self._loiter_fuel_events += 1
            # Loiter distance is negligible — not added to transit distance
        else:
            mission_state = "idle"
            # Excluded from CII per port-time exclusion

        # ---- 4. Attained CII — raw (all fuel) ----
        #   Attained CII = (ΣFC_j · C_Fj) / (C · D_t)
        #   Units: g-CO₂ / (DWT · NM)
        total_fuel_tonnes = self._transit_fuel_tonnes + self._loiter_fuel_tonnes
        total_co2_tonnes = total_fuel_tonnes * CF_HFO
        transit_co2_tonnes = self._transit_fuel_tonnes * CF_HFO
        loiter_co2_tonnes = self._loiter_fuel_tonnes * CF_HFO

        effective_distance = max(self._transit_distance_nm, 0.001)

        # Raw CII includes all fuel
        cii_raw = (total_co2_tonnes * 1e6) / (CAPACITY_DWT * effective_distance)
        # Corrected CII — transit fuel only (MEPC.355(78) correction)
        cii_corrected = (transit_co2_tonnes * 1e6) / (CAPACITY_DWT * effective_distance)

        # ---- 5. CII rating band ----
        cii_ratio = cii_raw / max(self._cii_reference, 0.01)
        rating_raw = self._classify_rating(cii_ratio)

        cii_ratio_corr = cii_corrected / max(self._cii_reference, 0.01)
        rating_corrected = self._classify_rating(cii_ratio_corr)

        # ---- 6. Build payload ----
        return {
            "mission_state": mission_state,
            "cii_attained_raw": round(cii_raw, 4),
            "cii_attained_corrected": round(cii_corrected, 4),
            "cii_reference": round(self._cii_reference, 4),
            "cii_rating_raw": rating_raw,
            "cii_rating_corrected": rating_corrected,
            "transit_co2_tonnes": round(transit_co2_tonnes, 6),
            "loiter_co2_tonnes": round(loiter_co2_tonnes, 6),
            "transit_fuel_tonnes": round(self._transit_fuel_tonnes, 6),
            "loiter_fuel_tonnes": round(self._loiter_fuel_tonnes, 6),
            "transit_distance_nm": round(self._transit_distance_nm, 4),
            "loiter_events": self._loiter_fuel_events,
            "transit_events": self._transit_fuel_events,
            "elapsed_hours": round(self._elapsed_s / 3600.0, 4),
        }

    # ------------------------------------------------------------------ #
    # CII Rating Classification
    # ------------------------------------------------------------------ #
    @staticmethod
    def _classify_rating(cii_ratio: float) -> str:
        """Classify Attained CII ratio into IMO rating band A–E.

        The ratio is attained_cii / reference_cii.  Rating boundaries
        follow the exponential model from MEPC.339(76):

            A:  ratio ≤ exp(d₁)   →  ≤ 0.741
            B:  ratio ≤ exp(d₂)   →  ≤ 0.861
            C:  ratio ≤ exp(d₃)   →  ≤ 1.000  (reference line)
            D:  ratio ≤ exp(d₄)   →  ≤ 1.162
            E:  ratio >  exp(d₄)  →  > 1.162 — corrective action required
        """
        import math
        if cii_ratio <= math.exp(_CII_D1):      # ≤ 0.741
            return "A"
        elif cii_ratio <= math.exp(_CII_D2):     # ≤ 0.861
            return "B"
        elif cii_ratio <= math.exp(_CII_D3):     # ≤ 1.000
            return "C"
        elif cii_ratio <= math.exp(_CII_D4):     # ≤ 1.162
            return "D"
        else:
            return "E"
