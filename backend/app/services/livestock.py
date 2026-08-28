"""
Livestock Heat Stress & Irrigation Alert Module.

Implements:
  1. Temperature-Humidity Index (THI) for dairy cattle heat stress assessment
  2. THI stress band classification based on published dairy science thresholds
  3. Consecutive-day irrigation alert triggered by sustained high temperatures

These tools support agricultural extension services within the Heatwave EWS,
enabling proactive livestock management and irrigation scheduling decisions.
"""

from __future__ import annotations

# ──────────────────────────────────────────────────────────────────────
# Configurable constants
# ──────────────────────────────────────────────────────────────────────

# THI classification thresholds (dairy cattle)
# Source: Armstrong, 1994; Collier et al., 2012 — widely adopted in
# dairy science literature for Holstein cattle productivity studies.
THI_NO_STRESS_UPPER = 72   # THI < 72 → No stress
THI_MILD_UPPER = 80        # 72 ≤ THI < 80 → Mild
THI_MODERATE_UPPER = 90    # 80 ≤ THI < 90 → Moderate
THI_SEVERE_UPPER = 99      # 90 ≤ THI < 99 → Severe (>98 = Extreme)

# Irrigation alert defaults
# TODO: Make these configurable per crop type / region via API or config file
DEFAULT_TEMP_THRESHOLD_C: float = 38.0   # Air temperature trigger (°C)
DEFAULT_WBGT_THRESHOLD_C: float = 30.0   # WBGT trigger (°C)
DEFAULT_CONSECUTIVE_DAYS: int = 3        # Minimum consecutive days to trigger


# ──────────────────────────────────────────────────────────────────────
# 1. Temperature-Humidity Index (THI)
#    Source: NRC (National Research Council), 1971. "A Guide to
#    Environmental Research on Animals." National Academy of Sciences.
#    Also: Bohmanova et al., 2007. "Temperature-humidity indices as
#    indicators of milk production losses due to heat stress."
#    J. Dairy Sci. 90:1947–1956.
#
#    Formula:
#      THI = (1.8 × T + 32) − (0.55 − 0.0055 × RH) × (1.8 × T − 26)
#
#    where T is dry-bulb temperature (°C) and RH is relative humidity (%).
# ──────────────────────────────────────────────────────────────────────

def compute_livestock_thi(temp_c: float, rh_pct: float) -> float:
    """
    Compute the Temperature-Humidity Index for dairy cattle.

    Uses the NRC (1971) formula widely adopted in dairy science:

        THI = (1.8 × T + 32) − (0.55 − 0.0055 × RH) × (1.8 × T − 26)

    where:
        T  = dry-bulb air temperature (°C)
        RH = relative humidity (%, 0–100)

    This index combines temperature and humidity into a single metric
    reflecting the thermal comfort of dairy cattle.  Values ≥ 72 indicate
    the onset of heat stress with measurable declines in milk yield.

    Args:
        temp_c: Air temperature in °C.
        rh_pct: Relative humidity in % (0–100).

    Returns:
        Temperature-Humidity Index (dimensionless).

    Reference:
        NRC, 1971. "A Guide to Environmental Research on Animals."
        Bohmanova et al., 2007. J. Dairy Sci. 90:1947–1956.
        Armstrong, 1994. "Heat Stress Interaction with Shade and Cooling."
        J. Dairy Sci. 77:2044–2050.

    Example:
        >>> round(compute_livestock_thi(25.0, 50.0), 1)
        72.1
    """
    t_f_component = 1.8 * temp_c + 32.0        # Fahrenheit equivalent
    humidity_factor = 0.55 - 0.0055 * rh_pct    # Humidity depression coefficient
    cooling_potential = 1.8 * temp_c - 26.0     # Evaporative cooling potential

    thi = t_f_component - humidity_factor * cooling_potential
    return round(thi, 2)


# ──────────────────────────────────────────────────────────────────────
# 2. THI Stress Classification
#    Thresholds from Armstrong (1994) and Collier et al. (2012):
#      < 72 : No stress
#      72–79: Mild stress (milk yield declines begin)
#      80–89: Moderate stress (significant production loss)
#      90–98: Severe stress (physiological distress, potential mortality)
#      > 98 : Extreme / Emergency
# ──────────────────────────────────────────────────────────────────────

def classify_thi(thi: float) -> str:
    """
    Classify a THI value into a livestock heat stress category.

    Uses published dairy science thresholds (Armstrong, 1994;
    Collier et al., 2012):

        THI < 72  → 'No stress'
        72 ≤ THI < 80 → 'Mild'
        80 ≤ THI < 90 → 'Moderate'
        90 ≤ THI < 99 → 'Severe'
        THI ≥ 99  → 'Extreme'

    Args:
        thi: Temperature-Humidity Index value.

    Returns:
        One of: 'No stress', 'Mild', 'Moderate', 'Severe', 'Extreme'.

    Reference:
        Armstrong, 1994. J. Dairy Sci. 77:2044–2050.
        Collier et al., 2012. "Use of climate information for modeling
        livestock heat stress." Animal Frontiers, 2(4):5–9.
    """
    if thi < THI_NO_STRESS_UPPER:
        return "No stress"
    elif thi < THI_MILD_UPPER:
        return "Mild"
    elif thi < THI_MODERATE_UPPER:
        return "Moderate"
    elif thi < THI_SEVERE_UPPER:
        return "Severe"
    else:
        return "Extreme"


# ──────────────────────────────────────────────────────────────────────
# 3. Irrigation Alert — consecutive high-heat day detection
#
#    Flags when N or more consecutive forecast days exceed a thermal
#    threshold (either raw temperature or WBGT), recommending that
#    farmers shift irrigation to cooler hours or increase frequency.
#
#    Each forecast day dict should contain at least:
#      { "date": "YYYY-MM-DD", "temp_c": float }
#    and optionally:
#      { "wbgt_c": float }
#
#    TODO: Integrate with crop-specific water-requirement models
#    TODO: Support per-crop / per-region threshold configuration via API
# ──────────────────────────────────────────────────────────────────────

def check_irrigation_alert(
    forecast_days: list[dict],
    temp_threshold_c: float = DEFAULT_TEMP_THRESHOLD_C,
    wbgt_threshold_c: float = DEFAULT_WBGT_THRESHOLD_C,
    consecutive_days: int = DEFAULT_CONSECUTIVE_DAYS,
) -> str | None:
    """
    Check whether a forecast triggers a pre-emptive irrigation alert.

    Scans the list of forecast days for N or more *consecutive* days where
    either:
      • air temperature ≥ temp_threshold_c, **or**
      • WBGT ≥ wbgt_threshold_c (if provided in the forecast dict).

    When the threshold is met, returns an advisory string recommending
    irrigation timing adjustments.  Returns ``None`` if no alert is needed.

    Args:
        forecast_days:    List of daily forecast dicts, each containing at
                          minimum ``{"date": str, "temp_c": float}``.
                          Optionally ``{"wbgt_c": float}``.
        temp_threshold_c: Air temperature threshold in °C (default 38.0).
        wbgt_threshold_c: WBGT threshold in °C (default 30.0).
        consecutive_days: Minimum consecutive days to trigger (default 3).

    Returns:
        An advisory string if the alert is triggered, else ``None``.

    Examples:
        >>> days = [
        ...     {"date": "2025-06-01", "temp_c": 39.0},
        ...     {"date": "2025-06-02", "temp_c": 40.0},
        ...     {"date": "2025-06-03", "temp_c": 38.5},
        ... ]
        >>> check_irrigation_alert(days) is not None
        True
    """
    if consecutive_days < 1:
        raise ValueError("consecutive_days must be ≥ 1")

    streak = 0
    streak_start_date: str | None = None

    for day in forecast_days:
        temp = day.get("temp_c")
        wbgt = day.get("wbgt_c")

        # A day is "hot" if either metric exceeds its threshold
        is_hot = False
        if temp is not None and temp >= temp_threshold_c:
            is_hot = True
        if wbgt is not None and wbgt >= wbgt_threshold_c:
            is_hot = True

        if is_hot:
            if streak == 0:
                streak_start_date = day.get("date", "unknown")
            streak += 1
        else:
            streak = 0
            streak_start_date = None

        if streak >= consecutive_days:
            return (
                f"IRRIGATION ALERT: {streak} consecutive days of extreme heat "
                f"starting {streak_start_date}. "
                f"Recommend shifting irrigation to pre-dawn/evening hours "
                f"and increasing frequency to reduce crop thermal stress."
            )

    return None
