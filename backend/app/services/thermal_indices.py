"""
Thermal Stress Indices — core heat stress computation engine.

Implements three physiologically-grounded heat stress indices:
  1. Heat Index (NOAA/Rothfusz regression)
  2. WBGT — Wet Bulb Globe Temperature (simplified outdoor estimation per ISO 7243)
  3. UTCI — Universal Thermal Climate Index (polynomial regression approximation)

Each function is a pure function with typed inputs/outputs.
"""

import math


# ──────────────────────────────────────────────────────────────────────
# 1. Heat Index (NOAA / Rothfusz regression)
#    Source: Rothfusz, L.P., 1990. "The Heat Index 'Equation' (or, More Than
#    You Ever Wanted to Know About Heat Index)." NWS Technical Attachment SR 90-23.
#    https://www.wpc.ncep.noaa.gov/html/heatindex_equation.shtml
# ──────────────────────────────────────────────────────────────────────

def compute_heat_index(temp_c: float, rh_pct: float) -> float:
    """
    Compute the NOAA Heat Index.

    Uses the Rothfusz regression (in Fahrenheit internally), with the
    low-heat simple formula fallback and NWS adjustment terms.

    Args:
        temp_c: Air temperature in °C.
        rh_pct: Relative humidity in % (0–100).

    Returns:
        Heat Index in °C.

    Reference:
        Rothfusz, 1990; NWS Heat Index equation page.
    """
    # Convert to Fahrenheit — the Rothfusz regression operates in °F
    t_f = temp_c * 9.0 / 5.0 + 32.0

    # Simple formula for low temperatures (Steadman, 1979)
    hi_simple = 0.5 * (t_f + 61.0 + (t_f - 68.0) * 1.2 + rh_pct * 0.094)

    if hi_simple < 80.0:
        hi_f = hi_simple
    else:
        # Full Rothfusz regression
        hi_f = (
            -42.379
            + 2.04901523 * t_f
            + 10.14333127 * rh_pct
            - 0.22475541 * t_f * rh_pct
            - 6.83783e-3 * t_f ** 2
            - 5.481717e-2 * rh_pct ** 2
            + 1.22874e-3 * t_f ** 2 * rh_pct
            + 8.5282e-4 * t_f * rh_pct ** 2
            - 1.99e-6 * t_f ** 2 * rh_pct ** 2
        )

        # Adjustment for low humidity at high temperatures
        if rh_pct < 13.0 and 80.0 <= t_f <= 112.0:
            adjustment = -((13.0 - rh_pct) / 4.0) * math.sqrt(
                (17.0 - abs(t_f - 95.0)) / 17.0
            )
            hi_f += adjustment

        # Adjustment for high humidity at moderate temperatures
        if rh_pct > 85.0 and 80.0 <= t_f <= 87.0:
            adjustment = ((rh_pct - 85.0) / 10.0) * ((87.0 - t_f) / 5.0)
            hi_f += adjustment

    # Convert back to Celsius
    return (hi_f - 32.0) * 5.0 / 9.0


# ──────────────────────────────────────────────────────────────────────
# 2. WBGT — Wet Bulb Globe Temperature (simplified outdoor estimation)
#    Source: Liljegren, J.C. et al., 2008. "Modeling the Wet Bulb Globe
#    Temperature Using Standard Meteorological Measurements."
#    Also references ISO 7243:2017 for occupational heat stress limits.
#
#    NOTE: A full WBGT requires actual black-globe temperature measurement.
#    This is an estimation from standard weather station variables
#    (temperature, humidity, wind speed, solar radiation) using the
#    simplified approach of approximating Tw and Tg from these inputs.
# ──────────────────────────────────────────────────────────────────────

def _estimate_natural_wet_bulb(temp_c: float, rh_pct: float) -> float:
    """
    Estimate natural wet-bulb temperature from T and RH using
    the Stull (2011) regression formula.

    Source: Stull, R., 2011. "Wet-Bulb Temperature from Relative Humidity
    and Air Temperature." J. Appl. Meteor. Climatol., 50, 2267–2269.
    """
    tw = temp_c * math.atan(0.151977 * (rh_pct + 8.313659) ** 0.5) + \
        math.atan(temp_c + rh_pct) - \
        math.atan(rh_pct - 1.676331) + \
        0.00391838 * rh_pct ** 1.5 * math.atan(0.023101 * rh_pct) - \
        4.686035
    return tw


def _estimate_globe_temperature(
    temp_c: float, wind_ms: float, solar_wm2: float
) -> float:
    """
    Estimate black globe temperature from air temp, wind, and solar radiation.

    Uses the simplified Liljegren approach: globe temperature rises above
    ambient proportional to solar load and inversely proportional to wind
    cooling.

    This is a first-order approximation — production systems should use
    actual Tg measurements or the full Liljegren iterative solver.
    """
    # Simplified model: Tg ≈ Ta + solar_gain - wind_cooling
    # Coefficients from empirical fit (Liljegren et al., 2008 simplified)
    solar_gain = 0.01 * solar_wm2  # ~1°C per 100 W/m²
    wind_cooling = 1.0 * math.sqrt(wind_ms) if wind_ms > 0 else 0.0
    tg = temp_c + solar_gain - wind_cooling
    return tg


def compute_wbgt(
    temp_c: float, rh_pct: float, wind_ms: float, solar_wm2: float
) -> float:
    """
    Compute the simplified outdoor Wet Bulb Globe Temperature (WBGT).

    WBGT_outdoor = 0.7 × Tw + 0.2 × Tg + 0.1 × Ta

    where:
        Tw  = natural wet-bulb temperature (estimated from T and RH)
        Tg  = globe temperature (estimated from T, wind, solar radiation)
        Ta  = dry-bulb (air) temperature

    Args:
        temp_c:    Air temperature in °C.
        rh_pct:    Relative humidity in % (0–100).
        wind_ms:   Wind speed in m/s.
        solar_wm2: Solar radiation in W/m².

    Returns:
        WBGT in °C.

    Reference:
        ISO 7243:2017; Liljegren et al., 2008.
        NOTE: This uses estimated Tw and Tg. A full WBGT needs actual
        black-globe temperature and natural wet-bulb measurements.
    """
    tw = _estimate_natural_wet_bulb(temp_c, rh_pct)
    tg = _estimate_globe_temperature(temp_c, wind_ms, solar_wm2)
    wbgt = 0.7 * tw + 0.2 * tg + 0.1 * temp_c
    return round(wbgt, 2)


# ──────────────────────────────────────────────────────────────────────
# 3. UTCI — Universal Thermal Climate Index
#    Source: Bröde et al., 2012. "Deriving the operational procedure for
#    the Universal Thermal Climate Index (UTCI)."
#
#    The full UTCI uses a 6th-order polynomial with ~210 terms.
#    We wrap the pythermalcomfort library's implementation, falling back
#    to a simplified approximation if the library is unavailable.
# ──────────────────────────────────────────────────────────────────────

def compute_utci(
    temp_c: float, rh_pct: float, wind_ms: float, mrt_c: float
) -> float:
    """
    Compute the Universal Thermal Climate Index (UTCI).

    Uses the pythermalcomfort library's polynomial regression approximation
    with ~210 coefficients. Falls back to a simplified linear model if
    the library is not available.

    Args:
        temp_c: Air temperature in °C.
        rh_pct: Relative humidity in % (0–100).
        wind_ms: Wind speed at 10 m height in m/s.
        mrt_c:  Mean radiant temperature in °C.

    Returns:
        UTCI equivalent temperature in °C.

    Reference:
        Bröde et al., 2012; Fiala et al., 2012.
    """
    try:
        from pythermalcomfort.models import utci_approx

        # pythermalcomfort expects wind speed >= 0.5 m/s for the UTCI model
        wind_clamped = max(wind_ms, 0.5)
        # Convert RH to water vapour pressure (kPa) for pythermalcomfort
        # Some versions accept rh directly; utci_approx uses ta, tr, v, rh
        result = utci_approx(tdb=temp_c, tr=mrt_c, v=wind_clamped, rh=rh_pct)
        return round(result, 2)
    except ImportError:
        pass

    # Fallback: simplified UTCI offset model
    # UTCI ≈ Ta + 0.3 × (MRT - Ta) + 0.1 × RH_effect - wind_chill
    rh_frac = rh_pct / 100.0
    # Water vapour partial pressure approximation (kPa)
    e_sat = 0.6108 * math.exp(17.27 * temp_c / (temp_c + 237.3))
    e_a = rh_frac * e_sat
    mrt_offset = 0.3 * (mrt_c - temp_c)
    humidity_effect = 0.7 * e_a
    wind_effect = -0.5 * math.sqrt(max(wind_ms, 0.5))
    utci = temp_c + mrt_offset + humidity_effect + wind_effect
    return round(utci, 2)


# ──────────────────────────────────────────────────────────────────────
# Risk Classification
#
# Thresholds vary by index and regional standards. The bands below
# follow widely used guidance:
#
# Heat Index (NWS):
#   Green  < 27°C  | Yellow 27–32 | Orange 32–41 | Red 41–54 | Purple > 54
#
# WBGT (ISO 7243, acclimatised moderate work):
#   Green  < 26°C  | Yellow 26–28 | Orange 28–30 | Red 30–33 | Purple > 33
#
# UTCI:
#   Green  < 26°C  | Yellow 26–32 | Orange 32–38 | Red 38–46 | Purple > 46
# ──────────────────────────────────────────────────────────────────────

_THRESHOLDS: dict[str, list[tuple[float, str]]] = {
    "heat_index": [
        (27.0, "Green"),
        (32.0, "Yellow"),
        (41.0, "Orange"),
        (54.0, "Red"),
    ],
    "wbgt": [
        (26.0, "Green"),
        (28.0, "Yellow"),
        (30.0, "Orange"),
        (33.0, "Red"),
    ],
    "utci": [
        (26.0, "Green"),
        (32.0, "Yellow"),
        (38.0, "Orange"),
        (46.0, "Red"),
    ],
}


def classify_risk(index_value: float, index_type: str) -> str:
    """
    Classify a thermal index value into a risk band.

    Args:
        index_value: The computed index value.
        index_type:  One of "heat_index", "wbgt", or "utci".

    Returns:
        One of ["Green", "Yellow", "Orange", "Red", "Purple"].

    Raises:
        ValueError: If index_type is not recognized.
    """
    key = index_type.lower()
    if key not in _THRESHOLDS:
        raise ValueError(
            f"Unknown index_type '{index_type}'. "
            f"Must be one of: {list(_THRESHOLDS.keys())}"
        )

    for threshold, band in _THRESHOLDS[key]:
        if index_value < threshold:
            return band
    return "Purple"
