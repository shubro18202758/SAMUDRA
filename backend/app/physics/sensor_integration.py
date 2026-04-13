"""
physics/sensor_integration.py — Comprehensive Maritime Sensor Integration Hub
===============================================================================
Models a unified sensor ecosystem for an Indian Coast Guard OPV, integrating
diverse physical sensor systems as specified in DISC 14 Problem Statement 77.

Sensor Systems Modelled
-----------------------
1. **ECDIS** (Electronic Chart Display & Information System)
   - IHO S-57/S-100 chart data, UKC monitoring, ENC cell tracking
   - Generates route safety assessments and grounding risk indices

2. **EMCS** (Engine Monitoring & Control System)
   - Cylinder-level exhaust gas temperatures, turbocharger RPM
   - Lube oil pressure, coolant temperatures, fuel injection timing
   - Governor rack position, scavenge air pressure

3. **FOMS** (Fuel Oil Management System)
   - Mass flow meters (Coriolis type), density, viscosity, water content
   - Bunker tank levels, settling/service tank monitoring
   - ISO 8217 fuel quality parameters

4. **Weather Station** (Shipboard Meteorological Sensors)
   - Barometric pressure, relative humidity, air temperature
   - Anemometer (true/apparent wind), rain intensity
   - UV index, visibility distance

5. **VDR** (Voyage Data Recorder — S-VDR per IMO MSC.333(90))
   - Continuous 12-hour rolling buffer of all bridge data
   - Audio channels, radar imagery hashes, hull stress
   - Event bookmarking, compliance snapshot generation

Reference Standards
-------------------
- IEC 61162-1/2: Maritime NMEA OneNet, serial/UDP sensor bus
- IEC 61174: ECDIS operational and performance standards
- IMO MSC.333(90): S-VDR performance standards
- ISO 8217:2024: Marine fuel specifications

Author : SAMUDRA Backend — Phase 4 (Sensor Overhaul)
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from typing import Any

import numpy as np


# ═══════════════════════════════════════════════════════════════════════════
# ECDIS — Electronic Chart Display & Information System
# ═══════════════════════════════════════════════════════════════════════════
@dataclass
class ECDISData:
    """IHO S-57 chart-derived navigation safety data."""
    under_keel_clearance_m: float = 25.0       # UKC (deep water default)
    chart_datum: str = "LAT"                    # Lowest Astronomical Tide
    enc_cell_id: str = "IN3MUMB1"              # Current ENC cell
    safety_contour_m: float = 10.0             # Set safety contour depth
    grounding_risk_index: float = 0.0          # 0-1 (0=safe, 1=critical)
    cross_track_error_nm: float = 0.0          # XTE from planned route
    route_safety_status: str = "SAFE"          # SAFE | CAUTION | DANGER
    next_turn_bearing_deg: float = 0.0
    next_turn_distance_nm: float = 0.0
    water_depth_m: float = 120.0               # Depth from echosounder


class ECDISSensor:
    """Simulates ECDIS safety computations and chart overlay data."""

    # Depth profile along Arabian Sea patrol route (simplified bathymetry)
    _DEPTH_PROFILE = [
        (18.9, 72.8, 15.0),   # Mumbai approach — shallow
        (17.0, 73.1, 45.0),   # Off Ratnagiri
        (15.4, 73.8, 80.0),   # Off Goa
        (14.8, 74.1, 120.0),  # Off Karwar
        (12.9, 74.8, 200.0),  # Off Mangalore — shelf edge
        (10.0, 76.3, 50.0),   # Off Kochi — shallow
        (10.6, 72.6, 1200.0), # Lakshadweep — deep channel
        (8.3, 73.0, 2500.0),  # Minicoy — deep ocean
        (12.5, 68.0, 3800.0), # Mid Arabian Sea
        (15.7, 71.0, 2200.0), # Return leg
    ]

    def __init__(self, seed: int | None = None) -> None:
        self._rng = np.random.default_rng(seed)
        self._data = ECDISData()

    def update(self, lat: float, lon: float, heading_deg: float,
               sog_kts: float, wp_index: int, dist_to_wp_nm: float) -> dict:
        # Interpolate water depth from nearest profile point
        min_dist = float('inf')
        nearest_depth = 120.0
        for plat, plon, depth in self._DEPTH_PROFILE:
            d = math.sqrt((lat - plat) ** 2 + (lon - plon) ** 2)
            if d < min_dist:
                min_dist = d
                nearest_depth = depth

        depth_noise = float(self._rng.normal(0.0, nearest_depth * 0.02))
        self._data.water_depth_m = max(5.0, nearest_depth + depth_noise)

        # Under Keel Clearance (vessel draft ~4.2m for OPV)
        vessel_draft_m = 4.2
        squat_m = 0.01 * (sog_kts ** 2)  # Barrass squat formula simplified
        self._data.under_keel_clearance_m = max(
            0.0, self._data.water_depth_m - vessel_draft_m - squat_m
        )

        # Grounding risk index
        if self._data.under_keel_clearance_m < 2.0:
            self._data.grounding_risk_index = 1.0
            self._data.route_safety_status = "DANGER"
        elif self._data.under_keel_clearance_m < 5.0:
            self._data.grounding_risk_index = 0.7
            self._data.route_safety_status = "CAUTION"
        elif self._data.under_keel_clearance_m < 10.0:
            self._data.grounding_risk_index = 0.3
            self._data.route_safety_status = "CAUTION"
        else:
            self._data.grounding_risk_index = max(0.0, 0.1 - self._data.under_keel_clearance_m * 0.001)
            self._data.route_safety_status = "SAFE"

        # Cross-track error — random wander from planned route
        self._data.cross_track_error_nm = abs(float(self._rng.normal(0.0, 0.08)))
        if self._data.cross_track_error_nm > 0.5:
            self._data.route_safety_status = "CAUTION"

        # ENC cell tracking
        enc_cells = ["IN3MUMB1", "IN3RATN1", "IN3GOA01", "IN3KARW1",
                      "IN3MANG1", "IN3KOCH1", "IN3LKSH1", "IN3MNIC1",
                      "IN3ARAB1", "IN3ARAB2"]
        self._data.enc_cell_id = enc_cells[wp_index % len(enc_cells)]

        self._data.next_turn_distance_nm = round(dist_to_wp_nm, 2)
        self._data.next_turn_bearing_deg = round(heading_deg, 1)

        return {
            "under_keel_clearance_m": round(self._data.under_keel_clearance_m, 2),
            "water_depth_m": round(self._data.water_depth_m, 1),
            "chart_datum": self._data.chart_datum,
            "enc_cell_id": self._data.enc_cell_id,
            "safety_contour_m": self._data.safety_contour_m,
            "grounding_risk_index": round(self._data.grounding_risk_index, 3),
            "cross_track_error_nm": round(self._data.cross_track_error_nm, 3),
            "route_safety_status": self._data.route_safety_status,
            "next_turn_bearing_deg": self._data.next_turn_bearing_deg,
            "next_turn_distance_nm": self._data.next_turn_distance_nm,
        }


# ═══════════════════════════════════════════════════════════════════════════
# EMCS — Engine Monitoring & Control System
# ═══════════════════════════════════════════════════════════════════════════
class EMCSSensor:
    """Cylinder-level engine instrumentation for a SEMT Pielstick 16PA6V280
    marine diesel (representative of ICG OPV main engines).

    12 cylinders, 2 turbochargers, lube oil system, coolant circuit.
    """

    _NUM_CYLINDERS = 12
    _NUM_TURBOCHARGERS = 2

    def __init__(self, seed: int | None = None) -> None:
        self._rng = np.random.default_rng(seed)
        self._cyl_temps = [280.0] * self._NUM_CYLINDERS
        self._tc_rpms = [15000.0, 15200.0]
        self._lube_pressure_bar = 4.5
        self._coolant_temp_c = 72.0
        self._scavenge_air_bar = 2.8
        self._fuel_rack_pct = 50.0

    def update(self, rpm: float, power_kw: float, load_pct: float) -> dict:
        # Cylinder exhaust gas temperatures — correlated with load
        base_temp = 250.0 + 2.0 * load_pct
        for i in range(self._NUM_CYLINDERS):
            noise = float(self._rng.normal(0.0, 3.0))
            # Cylinder imbalance: slight deviation per cylinder
            imbalance = float(self._rng.normal(0.0, 5.0))
            self._cyl_temps[i] = max(180.0, base_temp + imbalance + noise)

        # Turbocharger RPM — proportional to engine load
        for i in range(self._NUM_TURBOCHARGERS):
            tc_base = 8000.0 + 120.0 * load_pct
            self._tc_rpms[i] = max(5000.0, tc_base + float(self._rng.normal(0.0, 50.0)))

        # Lube oil pressure — drops with age/contamination, rises with RPM
        lo_base = 3.5 + 0.015 * rpm
        self._lube_pressure_bar = max(2.0, lo_base + float(self._rng.normal(0.0, 0.1)))

        # Coolant temperature — rises with power
        ct_base = 65.0 + 0.003 * power_kw
        self._coolant_temp_c = float(np.clip(
            ct_base + float(self._rng.normal(0.0, 0.8)), 60.0, 95.0
        ))

        # Scavenge air pressure
        sa_base = 1.5 + 0.02 * load_pct
        self._scavenge_air_bar = max(1.0, sa_base + float(self._rng.normal(0.0, 0.05)))

        # Fuel rack position — proportional to load
        self._fuel_rack_pct = float(np.clip(load_pct + float(self._rng.normal(0.0, 1.0)), 0, 100))

        # Max cylinder deviation — important health metric
        mean_cyl = sum(self._cyl_temps) / len(self._cyl_temps)
        max_dev = max(abs(t - mean_cyl) for t in self._cyl_temps)

        return {
            "cylinder_exhaust_temps_c": [round(t, 1) for t in self._cyl_temps],
            "cylinder_mean_temp_c": round(mean_cyl, 1),
            "cylinder_max_deviation_c": round(max_dev, 1),
            "turbocharger_rpms": [round(r, 0) for r in self._tc_rpms],
            "lube_oil_pressure_bar": round(self._lube_pressure_bar, 2),
            "coolant_temp_c": round(self._coolant_temp_c, 1),
            "scavenge_air_pressure_bar": round(self._scavenge_air_bar, 2),
            "fuel_rack_position_pct": round(self._fuel_rack_pct, 1),
            "num_cylinders": self._NUM_CYLINDERS,
        }


# ═══════════════════════════════════════════════════════════════════════════
# FOMS — Fuel Oil Management System
# ═══════════════════════════════════════════════════════════════════════════
class FOMSSensor:
    """Coriolis mass flow meter + fuel quality parameters per ISO 8217."""

    def __init__(self, seed: int | None = None) -> None:
        self._rng = np.random.default_rng(seed)
        self._bunker_level_pct = 92.0          # Start at 92% bunker
        self._settling_tank_pct = 85.0
        self._service_tank_pct = 78.0
        self._total_consumed_kg = 0.0

    def update(self, fuel_flow_kgh: float, dt: float) -> dict:
        consumed_kg = fuel_flow_kgh * (dt / 3600.0)
        self._total_consumed_kg += consumed_kg

        # Tank levels drain proportionally
        drain_pct = consumed_kg / (350_000.0) * 100.0  # 350 tonnes capacity
        self._bunker_level_pct = max(0.0, self._bunker_level_pct - drain_pct * 0.4)
        self._settling_tank_pct = max(0.0, self._settling_tank_pct - drain_pct * 0.3)
        self._service_tank_pct = max(0.0, self._service_tank_pct - drain_pct * 0.3)

        # Fuel quality parameters (ISO 8217 RMG 380)
        density_15c = 991.0 + float(self._rng.normal(0.0, 0.5))  # kg/m³
        viscosity_50c = 380.0 + float(self._rng.normal(0.0, 5.0))  # cSt
        water_content_pct = max(0.0, 0.3 + float(self._rng.normal(0.0, 0.05)))
        sulphur_pct = max(0.0, 2.8 + float(self._rng.normal(0.0, 0.1)))
        ccai = 850 + float(self._rng.normal(0.0, 2.0))  # Calculated Carbon Aromaticity Index

        # Mass flow from Coriolis meter (cross-checks engine fuel flow)
        coriolis_flow_kgh = fuel_flow_kgh + float(self._rng.normal(0.0, 0.5))

        return {
            "coriolis_mass_flow_kgh": round(max(0.0, coriolis_flow_kgh), 2),
            "density_15c_kgm3": round(density_15c, 1),
            "viscosity_50c_cst": round(max(10.0, viscosity_50c), 1),
            "water_content_pct": round(water_content_pct, 3),
            "sulphur_content_pct": round(sulphur_pct, 2),
            "ccai": round(ccai, 0),
            "bunker_tank_level_pct": round(self._bunker_level_pct, 1),
            "settling_tank_level_pct": round(self._settling_tank_pct, 1),
            "service_tank_level_pct": round(self._service_tank_pct, 1),
            "total_consumed_kg": round(self._total_consumed_kg, 2),
            "fuel_quality_status": "COMPLIANT" if sulphur_pct < 3.5 and water_content_pct < 0.5 else "NON-COMPLIANT",
        }


# ═══════════════════════════════════════════════════════════════════════════
# Weather Station — Shipboard Meteorological Sensors
# ═══════════════════════════════════════════════════════════════════════════
class WeatherStationSensor:
    """Integrated met station: barometer, hygrometer, thermometer, anemometer."""

    def __init__(self, seed: int | None = None) -> None:
        self._rng = np.random.default_rng(seed)
        self._pressure_hpa = 1013.25
        self._humidity_pct = 78.0
        self._air_temp_c = 29.0
        self._dew_point_c = 24.0
        self._visibility_nm = 10.0

    def update(self, wind_speed_kts: float, wave_height_m: float,
               monsoon_active: bool) -> dict:
        # Barometric pressure — drops during storm
        if monsoon_active:
            target = 998.0 + float(self._rng.normal(0.0, 2.0))
        else:
            target = 1013.25 + float(self._rng.normal(0.0, 1.0))
        self._pressure_hpa += 0.05 * (target - self._pressure_hpa)

        # Humidity — higher during monsoon
        hum_base = 85.0 if monsoon_active else 72.0
        self._humidity_pct = float(np.clip(
            hum_base + float(self._rng.normal(0.0, 3.0)), 40.0, 100.0
        ))

        # Air temperature — Indian Ocean tropics
        self._air_temp_c = float(np.clip(
            29.0 + float(self._rng.normal(0.0, 1.0)) - (2.0 if monsoon_active else 0.0),
            22.0, 36.0
        ))

        # Dew point from Magnus formula approximation
        a, b = 17.27, 237.7
        alpha = (a * self._air_temp_c) / (b + self._air_temp_c) + math.log(self._humidity_pct / 100.0)
        self._dew_point_c = (b * alpha) / (a - alpha)

        # Visibility — reduced in rain/monsoon
        if monsoon_active:
            self._visibility_nm = max(0.5, 3.0 + float(self._rng.normal(0.0, 1.0)))
        else:
            self._visibility_nm = max(2.0, 10.0 + float(self._rng.normal(0.0, 1.5)))

        # Rain intensity — mm/hr
        rain_mmhr = max(0.0, float(self._rng.exponential(5.0)) if monsoon_active else 0.0)

        # UV index (tropical Indian Ocean)
        uv_index = float(np.clip(8.0 + float(self._rng.normal(0.0, 2.0)), 0.0, 14.0))

        return {
            "barometric_pressure_hpa": round(self._pressure_hpa, 1),
            "relative_humidity_pct": round(self._humidity_pct, 1),
            "air_temperature_c": round(self._air_temp_c, 1),
            "dew_point_c": round(self._dew_point_c, 1),
            "visibility_nm": round(self._visibility_nm, 1),
            "rain_intensity_mmhr": round(rain_mmhr, 1),
            "uv_index": round(uv_index, 1),
            "weather_severity": "STORM" if monsoon_active and wind_speed_kts > 25 else
                                "HEAVY" if monsoon_active else
                                "MODERATE" if wind_speed_kts > 15 else "FAIR",
        }


# ═══════════════════════════════════════════════════════════════════════════
# VDR — Simplified Voyage Data Recorder (IMO MSC.333(90))
# ═══════════════════════════════════════════════════════════════════════════
class VDRSensor:
    """Simplified S-VDR: maintains rolling 12-hour buffer of critical data."""

    _BUFFER_CAPACITY = 172_800  # 12 hours at 4 Hz = 172,800 frames

    def __init__(self) -> None:
        self._buffer_size: int = 0
        self._event_log: list[dict] = []
        self._hull_stress_kpa = 0.0
        self._recording: bool = True
        self._last_snapshot_t: float = 0.0

    def update(self, wave_height_m: float, roll_deg: float,
               pitch_deg: float, sog_kts: float, dt: float) -> dict:
        # Buffer size tracking
        if self._recording:
            self._buffer_size = min(self._buffer_size + 1, self._BUFFER_CAPACITY)

        # Hull stress — simplified Von Mises estimation from wave/motion
        wave_stress = wave_height_m * 12.0  # kPa per meter wave height
        motion_stress = (abs(roll_deg) * 3.0 + abs(pitch_deg) * 5.0)
        speed_stress = sog_kts * 0.8
        self._hull_stress_kpa = wave_stress + motion_stress + speed_stress

        # Buffer utilization
        buffer_pct = (self._buffer_size / self._BUFFER_CAPACITY) * 100.0

        # Compliance status
        compliant = self._recording and buffer_pct > 0

        return {
            "recording_active": self._recording,
            "buffer_utilization_pct": round(buffer_pct, 1),
            "buffer_frames": self._buffer_size,
            "hull_stress_kpa": round(self._hull_stress_kpa, 1),
            "hull_stress_status": "CRITICAL" if self._hull_stress_kpa > 200 else
                                  "WARNING" if self._hull_stress_kpa > 120 else "NORMAL",
            "events_logged": len(self._event_log),
            "compliance_status": "COMPLIANT" if compliant else "NON-COMPLIANT",
        }

    def bookmark_event(self, event_type: str, description: str) -> None:
        self._event_log.append({
            "time": time.time(),
            "type": event_type,
            "description": description,
        })


# ═══════════════════════════════════════════════════════════════════════════
# Unified Sensor Hub — Aggregates all sensor subsystems
# ═══════════════════════════════════════════════════════════════════════════
class SensorIntegrationHub:
    """Central aggregator for all maritime sensor subsystems.

    Provides a single update() call that fans out to all sensors and returns
    a unified sensor status dictionary.
    """

    def __init__(self, seed: int | None = None) -> None:
        self.ecdis = ECDISSensor(seed=seed)
        self.emcs = EMCSSensor(seed=seed)
        self.foms = FOMSSensor(seed=seed)
        self.weather = WeatherStationSensor(seed=seed)
        self.vdr = VDRSensor()

    def update(
        self,
        lat: float, lon: float, heading_deg: float,
        sog_kts: float, wp_index: int, dist_to_wp_nm: float,
        rpm: float, power_kw: float, mcr_load_pct: float,
        fuel_flow_kgh: float, wind_speed_kts: float,
        wave_height_m: float, monsoon_active: bool,
        roll_deg: float, pitch_deg: float, dt: float,
    ) -> dict:
        ecdis = self.ecdis.update(lat, lon, heading_deg, sog_kts, wp_index, dist_to_wp_nm)
        emcs = self.emcs.update(rpm, power_kw, mcr_load_pct)
        foms = self.foms.update(fuel_flow_kgh, dt)
        weather = self.weather.update(wind_speed_kts, wave_height_m, monsoon_active)
        vdr = self.vdr.update(wave_height_m, roll_deg, pitch_deg, sog_kts, dt)

        # Compute overall sensor health
        sensor_count = 5
        healthy = sum([
            ecdis["route_safety_status"] != "DANGER",
            emcs["cylinder_max_deviation_c"] < 30.0,
            foms["fuel_quality_status"] == "COMPLIANT",
            weather["weather_severity"] != "STORM",
            vdr["compliance_status"] == "COMPLIANT",
        ])

        return {
            "ecdis": ecdis,
            "emcs": emcs,
            "foms": foms,
            "weather_station": weather,
            "vdr": vdr,
            "sensor_health": {
                "total_sensors": sensor_count,
                "healthy_sensors": healthy,
                "health_pct": round(healthy / sensor_count * 100.0, 1),
                "status": "ALL_NOMINAL" if healthy == sensor_count else
                          "DEGRADED" if healthy >= 3 else "CRITICAL",
            },
        }
