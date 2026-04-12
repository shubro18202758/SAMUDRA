"""
physics/ais_navigation.py — AIS & NMEA 0183 Geospatial Synthesis
=================================================================
Implements waypoint-based route interpolation and AIVDM Message Type 1
(Position Report Class A) sentence encoding per the NMEA 0183 standard.

Route: A 10-waypoint patrol loop traversing the Arabian Sea, representative
of an Indian Coast Guard OPV patrol pattern.

Reference Standards
-------------------
- ITU-R M.1371-5: Technical characteristics for an automatic identification
  system using TDMA in the VHF maritime mobile band.
- NMEA 0183 v4.11: Standard for Interfacing Marine Electronic Devices.
- IEC 62287-1: AIS — Part 1: Class A shipborne equipment.

AIVDM Message Type 1 — Position Report (Class A, Scheduled)
------------------------------------------------------------
168-bit binary payload → 28 six-bit ASCII-armored characters.

  Bits   0–  5 : Message type           ( 6 bits) = 1
  Bits   6–  7 : Repeat indicator       ( 2 bits) = 0
  Bits   8– 37 : MMSI                   (30 bits)
  Bits  38– 41 : Navigation status      ( 4 bits) = 0 (under way using engine)
  Bits  42– 49 : Rate of turn           ( 8 bits) = −128 (not available)
  Bits  50– 59 : SOG (1/10 kn)          (10 bits)
  Bits  60      : Position accuracy     ( 1 bit)  = 1 (DGPS-quality)
  Bits  61– 88 : Longitude (1/10000′)   (28 bits) signed two's complement
  Bits  89–115 : Latitude  (1/10000′)   (27 bits) signed two's complement
  Bits 116–127 : COG (1/10°)            (12 bits)
  Bits 128–136 : True heading (°)       ( 9 bits)
  Bits 137–142 : UTC second             ( 6 bits)
  Bits 143–144 : Manoeuvre indicator    ( 2 bits) = 0
  Bits 145–147 : Spare                  ( 3 bits) = 0
  Bits 148      : RAIM flag             ( 1 bit)  = 0
  Bits 149–167 : Radio status           (19 bits) = 0
  ───────────────────────────────────────────────────
         Total                           168 bits

Author : SAMUDRA Backend — Phase 3
"""

from __future__ import annotations

import math
import time


# =============================================================================
# Arabian Sea Patrol Route — 10 Hard-Coded Waypoints
# =============================================================================
# Representative Indian Coast Guard OPV patrol pattern:
#   Mumbai → south along India's western coast → Lakshadweep →
#   Minicoy → mid-Arabian Sea patrol leg → return to Mumbai.
#
# Each waypoint: (latitude_deg_N, longitude_deg_E)
WAYPOINTS: list[tuple[float, float]] = [
    (18.922, 72.836),   # WP 0 — Mumbai anchorage
    (16.980, 73.100),   # WP 1 — Off Ratnagiri
    (15.410, 73.780),   # WP 2 — Off Goa (Mormugao)
    (14.800, 74.050),   # WP 3 — Off Karwar
    (12.870, 74.810),   # WP 4 — Off Mangalore
    ( 9.970, 76.260),   # WP 5 — Off Kochi
    (10.570, 72.640),   # WP 6 — Lakshadweep (Kavaratti)
    ( 8.280, 73.040),   # WP 7 — Minicoy Island
    (12.500, 68.000),   # WP 8 — Mid Arabian Sea patrol
    (15.700, 71.000),   # WP 9 — Return leg, off Goa
]

# AIS Vessel Identity — Indian Coast Guard OPV (MID 419 = India)
MMSI: int = 419_001_234

# Earth mean radius (metres) for spherical calculations
_R_EARTH_M: float = 6_371_000.0

# Switch to next waypoint when closer than this (metres)
_ARRIVAL_THRESHOLD_M: float = 200.0


# =============================================================================
# Spherical Geometry — Haversine / Forward Azimuth / Destination Point
# =============================================================================

def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in metres between two WGS-84 points."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = (
        math.sin(dphi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2.0) ** 2
    )
    return 2.0 * _R_EARTH_M * math.asin(math.sqrt(a))


def _bearing_deg(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Initial bearing (forward azimuth) in degrees [0, 360)."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dlam = math.radians(lon2 - lon1)
    x = math.sin(dlam) * math.cos(phi2)
    y = (
        math.cos(phi1) * math.sin(phi2)
        - math.sin(phi1) * math.cos(phi2) * math.cos(dlam)
    )
    return (math.degrees(math.atan2(x, y)) + 360.0) % 360.0


def _destination_point(
    lat: float, lon: float, bearing_deg: float, distance_m: float,
) -> tuple[float, float]:
    """Destination point given start, bearing, and distance along a great circle."""
    phi1 = math.radians(lat)
    lam1 = math.radians(lon)
    brng = math.radians(bearing_deg)
    d_R = distance_m / _R_EARTH_M

    phi2 = math.asin(
        math.sin(phi1) * math.cos(d_R)
        + math.cos(phi1) * math.sin(d_R) * math.cos(brng)
    )
    lam2 = lam1 + math.atan2(
        math.sin(brng) * math.sin(d_R) * math.cos(phi1),
        math.cos(d_R) - math.sin(phi1) * math.sin(phi2),
    )
    return math.degrees(phi2), math.degrees(lam2)


# =============================================================================
# AIVDM Message Type 1 Encoder
# =============================================================================

def _append_uint(bits: list[int], value: int, n: int) -> None:
    """Append *n* bits of unsigned integer *value* (MSB first)."""
    for i in range(n - 1, -1, -1):
        bits.append((value >> i) & 1)


def _append_int(bits: list[int], value: int, n: int) -> None:
    """Append *n* bits of a signed integer in two's complement."""
    if value < 0:
        value = (1 << n) + value
    _append_uint(bits, value, n)


def _armor_payload(bits: list[int]) -> str:
    """Encode a bit-vector into 6-bit ASCII-armored characters (ITU-R M.1371-5 §5)."""
    chars: list[str] = []
    for i in range(0, len(bits), 6):
        val = 0
        for j in range(6):
            idx = i + j
            val = (val << 1) | (bits[idx] if idx < len(bits) else 0)
        val += 48
        if val > 87:
            val += 8
        chars.append(chr(val))
    return "".join(chars)


def _nmea_checksum(body: str) -> str:
    """NMEA 0183 XOR checksum over the sentence body (between ``!`` and ``*``)."""
    chk = 0
    for ch in body:
        chk ^= ord(ch)
    return f"{chk:02X}"


def encode_aivdm_type1(
    mmsi: int,
    lat_deg: float,
    lon_deg: float,
    sog_kts: float,
    cog_deg: float,
    heading_deg: float,
) -> str:
    """Build a complete ``!AIVDM`` sentence for AIS Message Type 1.

    Returns a fully formed NMEA 0183 sentence including the ``*XX``
    XOR checksum, e.g.::

        !AIVDM,1,1,,B,15MgK80P00GJt<0CH5<H10160000,0*3E
    """
    bits: list[int] = []

    _append_uint(bits, 1, 6)                            # Message type = 1
    _append_uint(bits, 0, 2)                            # Repeat indicator
    _append_uint(bits, mmsi, 30)                        # MMSI
    _append_uint(bits, 0, 4)                            # Nav status: under way
    _append_uint(bits, 0x80, 8)                         # ROT: not available
    sog_tenth = min(int(round(sog_kts * 10)), 1022)
    _append_uint(bits, sog_tenth, 10)                   # SOG in 1/10 kn
    _append_uint(bits, 1, 1)                            # Position accuracy: DGPS

    lon_val = int(round(lon_deg * 600_000))
    _append_int(bits, lon_val, 28)                      # Longitude (signed)

    lat_val = int(round(lat_deg * 600_000))
    _append_int(bits, lat_val, 27)                      # Latitude  (signed)

    cog_tenth = min(int(round(cog_deg * 10)) % 3600, 3599)
    _append_uint(bits, cog_tenth, 12)                   # COG in 1/10°

    hdg_int = int(round(heading_deg)) % 360
    _append_uint(bits, hdg_int, 9)                      # True heading

    utc_sec = int(time.time()) % 60
    _append_uint(bits, utc_sec, 6)                      # UTC second

    _append_uint(bits, 0, 2)                            # Manoeuvre indicator
    _append_uint(bits, 0, 3)                            # Spare
    _append_uint(bits, 0, 1)                            # RAIM flag
    _append_uint(bits, 0, 19)                           # Radio status

    assert len(bits) == 168, f"AIVDM Type 1: expected 168 bits, got {len(bits)}"

    payload = _armor_payload(bits)
    body = f"AIVDM,1,1,,B,{payload},0"
    return f"!{body}*{_nmea_checksum(body)}"


# =============================================================================
# AIS Navigator — Waypoint Interpolation Engine
# =============================================================================

class AISNavigator:
    """Navigates a vessel along the hard-coded Arabian Sea patrol route.

    Each call to :meth:`update` advances the vessel position along the
    great-circle path between waypoints, deriving its displacement from
    the SOG provided by the Hydrodynamic Physics engine.

    The heading is computed dynamically as the bearing from the current
    position to the next waypoint.  When the vessel arrives within
    :data:`_ARRIVAL_THRESHOLD_M` of a waypoint it advances to the next,
    looping back to waypoint 0 after the last to ensure continuous
    demonstration operation.
    """

    def __init__(self) -> None:
        # Start at waypoint 0, target waypoint 1
        self._lat, self._lon = WAYPOINTS[0]
        self._wp_index: int = 1
        self._heading: float = _bearing_deg(
            self._lat, self._lon, *WAYPOINTS[self._wp_index]
        )

    @property
    def current_waypoint_index(self) -> int:
        """Index of the waypoint the vessel is currently heading towards."""
        return self._wp_index

    def update(self, sog_kts: float, dt: float) -> dict:
        """Advance position by ``SOG × dt`` along the patrol route.

        Parameters
        ----------
        sog_kts : float
            Speed Over Ground in knots (from hydrodynamic engine).
        dt : float
            Time step in seconds.

        Returns
        -------
        dict
            latitude, longitude, heading_deg, cog_deg, nmea_sentence,
            current_waypoint_index, distance_to_waypoint_nm.
        """
        # Convert SOG to metres: 1 knot = 0.514444 m/s
        distance_m = sog_kts * 0.514_444 * dt

        wp_lat, wp_lon = WAYPOINTS[self._wp_index]
        dist_to_wp = _haversine_m(self._lat, self._lon, wp_lat, wp_lon)

        # Consume distance — may overshoot one or more waypoints
        while distance_m >= dist_to_wp and dist_to_wp > 0:
            self._lat, self._lon = wp_lat, wp_lon
            distance_m -= dist_to_wp
            # Loop back to waypoint 0 after the last
            self._wp_index = (self._wp_index + 1) % len(WAYPOINTS)
            wp_lat, wp_lon = WAYPOINTS[self._wp_index]
            dist_to_wp = _haversine_m(self._lat, self._lon, wp_lat, wp_lon)

        # Move along the great-circle bearing towards the next waypoint
        if dist_to_wp > 0:
            self._heading = _bearing_deg(self._lat, self._lon, wp_lat, wp_lon)
            self._lat, self._lon = _destination_point(
                self._lat, self._lon, self._heading, distance_m,
            )

        # Remaining distance (after move) in nautical miles
        dist_nm = _haversine_m(self._lat, self._lon, wp_lat, wp_lon) / 1852.0

        # COG equals heading during straight-line waypoint navigation
        cog_deg = self._heading

        # Encode AIVDM Message Type 1 sentence
        nmea = encode_aivdm_type1(
            mmsi=MMSI,
            lat_deg=self._lat,
            lon_deg=self._lon,
            sog_kts=sog_kts,
            cog_deg=cog_deg,
            heading_deg=self._heading,
        )

        return {
            "latitude": round(self._lat, 6),
            "longitude": round(self._lon, 6),
            "heading_deg": round(self._heading % 360.0, 1),
            "cog_deg": round(cog_deg % 360.0, 1),
            "nmea_sentence": nmea,
            "current_waypoint_index": self._wp_index,
            "distance_to_waypoint_nm": round(dist_nm, 2),
        }
