"""
EV Thermal Runaway Prevention — Charging Rate Advisory API.

Provides:
  - GET /api/ev-safety/{ward_id} → Recommended max charging‐rate multiplier
    based on current ambient temperature and forecast peak temperature.

# ─────────────────────────────────────────────────────────────────────
# IMPORTANT — PLACEHOLDER POLICY
# The temperature thresholds and multiplier values below are DEMO
# placeholders only.  Real deployments MUST source thresholds from:
#   • OEM battery thermal management specifications
#   • SAE J2464 / IEC 62660‑2 abuse‑test standards
#   • Cell chemistry data‑sheets (NMC vs LFP onset temps differ)
#   • Charging‑infrastructure vendor guidelines (CCS / CHAdeMO / GB/T)
#
# TODO: Replace with a config‑driven lookup or ML model trained on
#       real cell‑temperature telemetry.
# ─────────────────────────────────────────────────────────────────────

Source context:
  - IEC 62660-2: Reliability and abuse testing for lithium-ion cells
  - SAE J2464: Abuse testing for rechargeable energy storage systems
"""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException

from app.tasks.scheduler import get_risk_store, SAMPLE_WARDS

router = APIRouter(prefix="/api/ev-safety", tags=["ev-safety"])

# ── Configurable charging-rate derating policy ──────────────────────
# Each tuple: (lower_bound_°C, upper_bound_°C, multiplier, reason)
# Evaluated top-down; first matching band wins.
# NOTE: These thresholds are PLACEHOLDERS for demo purposes.
# Real thresholds should come from EV battery thermal management specs
# and cell-chemistry datasheets.
CHARGING_DERATING_POLICY: list[tuple[float, float, float, str]] = [
    (45.0, float("inf"), 0.30, "Extreme heat — severe derating to prevent thermal runaway"),
    (42.0, 45.0,         0.50, "Severe heat — significant derating recommended"),
    (40.0, 42.0,         0.70, "Moderate heat — reduced charging rate advised"),
    (35.0, 40.0,         0.85, "Mild caution — slight derating as precaution"),
]

# Default when temperature is below all thresholds (< 35 °C)
DEFAULT_MULTIPLIER: float = 1.0
DEFAULT_REASON: str = "Normal conditions — full charging rate permitted"


def _get_charge_rate_multiplier(temp_c: float) -> tuple[float, str]:
    """
    Look up the recommended charging‐rate multiplier for a given
    effective temperature.

    Parameters
    ----------
    temp_c : float
        The effective temperature to evaluate (°C).  Typically the
        *higher* of ambient and forecast‐peak.

    Returns
    -------
    tuple[float, str]
        (multiplier, human‐readable reason)

    Examples
    --------
    >>> _get_charge_rate_multiplier(32.0)
    (1.0, 'Normal conditions — full charging rate permitted')
    >>> _get_charge_rate_multiplier(43.5)
    (0.5, 'Severe heat — significant derating recommended')
    """
    for lower, upper, multiplier, reason in CHARGING_DERATING_POLICY:
        if lower <= temp_c < upper:
            return multiplier, reason
    # Falls through when temp_c < lowest threshold
    return DEFAULT_MULTIPLIER, DEFAULT_REASON


def _extract_temperatures(ward_data: dict) -> tuple[float, float]:
    """
    Extract current ambient temp and forecast peak temp from a ward's
    risk-store entry.

    Parameters
    ----------
    ward_data : dict
        The value stored in ``get_risk_store()[ward_id]``.

    Returns
    -------
    tuple[float, float]
        (ambient_temp_c, forecast_peak_temp_c)
    """
    ambient_temp_c: float = ward_data["current"]["temp_c"]

    # Forecast peak = max daily temp across the forecast horizon
    forecast_temps: list[float] = [
        day.get("temp_c", 0.0)
        for day in ward_data.get("forecast", [])
    ]
    forecast_peak_c: float = max(forecast_temps) if forecast_temps else ambient_temp_c

    return ambient_temp_c, forecast_peak_c


@router.get("/{ward_id}")
async def ev_charging_advisory(ward_id: int) -> dict:
    """
    Return a recommended max charging‐rate multiplier for the given ward.

    The multiplier is determined by the *higher* of the current ambient
    temperature and the forecast peak temperature, evaluated against the
    ``CHARGING_DERATING_POLICY`` thresholds.

    Response follows a webhook‐style payload schema so that downstream
    charging‐station controllers can consume it directly.

    Parameters
    ----------
    ward_id : int
        Numeric ward identifier (must exist in SAMPLE_WARDS).

    Returns
    -------
    dict
        Webhook payload::

            {
              "ward_id": 1,
              "timestamp": "2026-05-15T10:30:00+00:00",
              "ambient_temp_c": 38.2,
              "forecast_peak_temp_c": 43.1,
              "recommended_charge_rate_multiplier": 0.5,
              "reason": "Severe heat — significant derating recommended"
            }

    Raises
    ------
    HTTPException 404
        Ward ID not found in SAMPLE_WARDS.
    HTTPException 503
        Weather/risk data not yet ingested for the ward.
    """
    # ── Validate ward exists ──
    ward = next((w for w in SAMPLE_WARDS if w["id"] == ward_id), None)
    if ward is None:
        raise HTTPException(status_code=404, detail=f"Ward {ward_id} not found")

    # ── Retrieve risk data ──
    store = get_risk_store()
    ward_data = store.get(ward_id)
    if ward_data is None:
        raise HTTPException(
            status_code=503,
            detail="Weather data not yet available. Wait for ingestion cycle.",
        )

    # ── Compute advisory ──
    ambient_temp_c, forecast_peak_c = _extract_temperatures(ward_data)

    # Use the worse-case temperature for the derating decision
    effective_temp = max(ambient_temp_c, forecast_peak_c)
    multiplier, reason = _get_charge_rate_multiplier(effective_temp)

    return {
        "ward_id": ward_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "ambient_temp_c": round(ambient_temp_c, 1),
        "forecast_peak_temp_c": round(forecast_peak_c, 1),
        "recommended_charge_rate_multiplier": multiplier,
        "reason": reason,
    }
