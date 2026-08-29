"""
Background scheduler — runs weather ingestion + risk computation every 3 hours.

Uses APScheduler to periodically:
  1. Fetch weather for each ward's centroid
  2. Compute thermal indices (HI, WBGT, UTCI)
  3. Compute vulnerability + MRI scores
  4. Store results in the computed_risk table
"""

import logging
from datetime import datetime, timezone

from app.tasks.fetch_weather import fetch_weather
from app.tasks.downscale import downscale_to_ward
from app.services.thermal_indices import (
    compute_heat_index,
    compute_wbgt,
    compute_utci,
    classify_risk,
)
from app.services.vulnerability import (
    compute_vulnerability_score,
    compute_mortality_risk_index,
)

logger = logging.getLogger(__name__)

# ── Sample wards for demo (real wards would come from the DB) ──
# These are used when the DB is not yet populated.
SAMPLE_WARDS = [
    {
        "id": 1,
        "name": "Nagpur Ward (Dharampeth)",
        "centroid_lat": 21.1058,
        "centroid_lon": 79.0282,
        "pct_elderly": 10,
        "pct_outdoor_workers": 20,
        "pct_informal_housing": 15,
        "comorbidity_prevalence": 8,
        "tree_cover_pct": 25,
        "ac_penetration_pct": 50,
        "uhi_factor": 1.0
    },
    {
        "id": 2,
        "name": "Nagpur Ward (Sadar)",
        "centroid_lat": 21.1058,
        "centroid_lon": 79.0682,
        "pct_elderly": 12,
        "pct_outdoor_workers": 25,
        "pct_informal_housing": 19,
        "comorbidity_prevalence": 11,
        "tree_cover_pct": 23,
        "ac_penetration_pct": 46,
        "uhi_factor": 1.0
    },
    {
        "id": 3,
        "name": "Nagpur Ward (Sitabuldi)",
        "centroid_lat": 21.1058,
        "centroid_lon": 79.1082,
        "pct_elderly": 14,
        "pct_outdoor_workers": 30,
        "pct_informal_housing": 23,
        "comorbidity_prevalence": 14,
        "tree_cover_pct": 21,
        "ac_penetration_pct": 42,
        "uhi_factor": 1.0
    },
    {
        "id": 4,
        "name": "Nagpur Ward (Mahal)",
        "centroid_lat": 21.1058,
        "centroid_lon": 79.1482,
        "pct_elderly": 16,
        "pct_outdoor_workers": 35,
        "pct_informal_housing": 27,
        "comorbidity_prevalence": 17,
        "tree_cover_pct": 19,
        "ac_penetration_pct": 38,
        "uhi_factor": 0.3
    },
    {
        "id": 5,
        "name": "Nagpur Ward (Itwari)",
        "centroid_lat": 21.1458,
        "centroid_lon": 79.0282,
        "pct_elderly": 18,
        "pct_outdoor_workers": 40,
        "pct_informal_housing": 31,
        "comorbidity_prevalence": 8,
        "tree_cover_pct": 17,
        "ac_penetration_pct": 34,
        "uhi_factor": 0.3
    },
    {
        "id": 6,
        "name": "Nagpur Ward (Wardhaman Nagar)",
        "centroid_lat": 21.1458,
        "centroid_lon": 79.0682,
        "pct_elderly": 20,
        "pct_outdoor_workers": 20,
        "pct_informal_housing": 35,
        "comorbidity_prevalence": 11,
        "tree_cover_pct": 15,
        "ac_penetration_pct": 30,
        "uhi_factor": 0.3
    },
    {
        "id": 7,
        "name": "Nagpur Ward (Nandanvan)",
        "centroid_lat": 21.1458,
        "centroid_lon": 79.1082,
        "pct_elderly": 22,
        "pct_outdoor_workers": 25,
        "pct_informal_housing": 39,
        "comorbidity_prevalence": 14,
        "tree_cover_pct": 13,
        "ac_penetration_pct": 26,
        "uhi_factor": 0.3
    },
    {
        "id": 8,
        "name": "Nagpur Ward (Manish Nagar)",
        "centroid_lat": 21.1458,
        "centroid_lon": 79.1482,
        "pct_elderly": 24,
        "pct_outdoor_workers": 30,
        "pct_informal_housing": 43,
        "comorbidity_prevalence": 17,
        "tree_cover_pct": 11,
        "ac_penetration_pct": 22,
        "uhi_factor": 0.3
    },
    {
        "id": 9,
        "name": "Nagpur Ward (Pratap Nagar)",
        "centroid_lat": 21.1858,
        "centroid_lon": 79.0282,
        "pct_elderly": 11,
        "pct_outdoor_workers": 35,
        "pct_informal_housing": 17,
        "comorbidity_prevalence": 8,
        "tree_cover_pct": 9,
        "ac_penetration_pct": 18,
        "uhi_factor": 0.3
    },
    {
        "id": 10,
        "name": "Nagpur Ward (Ramdaspeth)",
        "centroid_lat": 21.1858,
        "centroid_lon": 79.0682,
        "pct_elderly": 13,
        "pct_outdoor_workers": 40,
        "pct_informal_housing": 21,
        "comorbidity_prevalence": 11,
        "tree_cover_pct": 7,
        "ac_penetration_pct": 14,
        "uhi_factor": 0.3
    },
    {
        "id": 11,
        "name": "Chennai Ward (T. Nagar)",
        "centroid_lat": 13.0627,
        "centroid_lon": 80.2307,
        "pct_elderly": 10,
        "pct_outdoor_workers": 20,
        "pct_informal_housing": 15,
        "comorbidity_prevalence": 8,
        "tree_cover_pct": 25,
        "ac_penetration_pct": 50,
        "uhi_factor": 1.0
    },
    {
        "id": 12,
        "name": "Chennai Ward (Mylapore)",
        "centroid_lat": 13.0627,
        "centroid_lon": 80.2707,
        "pct_elderly": 12,
        "pct_outdoor_workers": 25,
        "pct_informal_housing": 19,
        "comorbidity_prevalence": 11,
        "tree_cover_pct": 23,
        "ac_penetration_pct": 46,
        "uhi_factor": 1.0
    },
    {
        "id": 13,
        "name": "Chennai Ward (Adyar)",
        "centroid_lat": 13.0627,
        "centroid_lon": 80.3107,
        "pct_elderly": 14,
        "pct_outdoor_workers": 30,
        "pct_informal_housing": 23,
        "comorbidity_prevalence": 14,
        "tree_cover_pct": 21,
        "ac_penetration_pct": 42,
        "uhi_factor": 1.0
    },
    {
        "id": 14,
        "name": "Chennai Ward (Velachery)",
        "centroid_lat": 13.1027,
        "centroid_lon": 80.2307,
        "pct_elderly": 16,
        "pct_outdoor_workers": 35,
        "pct_informal_housing": 27,
        "comorbidity_prevalence": 17,
        "tree_cover_pct": 19,
        "ac_penetration_pct": 38,
        "uhi_factor": 0.3
    },
    {
        "id": 15,
        "name": "Chennai Ward (Anna Nagar)",
        "centroid_lat": 13.1027,
        "centroid_lon": 80.2707,
        "pct_elderly": 18,
        "pct_outdoor_workers": 40,
        "pct_informal_housing": 31,
        "comorbidity_prevalence": 8,
        "tree_cover_pct": 17,
        "ac_penetration_pct": 34,
        "uhi_factor": 0.3
    },
    {
        "id": 16,
        "name": "Chennai Ward (Guindy)",
        "centroid_lat": 13.1027,
        "centroid_lon": 80.3107,
        "pct_elderly": 20,
        "pct_outdoor_workers": 20,
        "pct_informal_housing": 35,
        "comorbidity_prevalence": 11,
        "tree_cover_pct": 15,
        "ac_penetration_pct": 30,
        "uhi_factor": 0.3
    },
    {
        "id": 17,
        "name": "Ahmedabad Ward (Kalupur)",
        "centroid_lat": 23.0025,
        "centroid_lon": 72.5314,
        "pct_elderly": 10,
        "pct_outdoor_workers": 20,
        "pct_informal_housing": 15,
        "comorbidity_prevalence": 8,
        "tree_cover_pct": 25,
        "ac_penetration_pct": 50,
        "uhi_factor": 1.0
    },
    {
        "id": 18,
        "name": "Ahmedabad Ward (Navrangpura)",
        "centroid_lat": 23.0025,
        "centroid_lon": 72.5714,
        "pct_elderly": 12,
        "pct_outdoor_workers": 25,
        "pct_informal_housing": 19,
        "comorbidity_prevalence": 11,
        "tree_cover_pct": 23,
        "ac_penetration_pct": 46,
        "uhi_factor": 1.0
    },
    {
        "id": 19,
        "name": "Ahmedabad Ward (Satellite)",
        "centroid_lat": 23.0025,
        "centroid_lon": 72.6114,
        "pct_elderly": 14,
        "pct_outdoor_workers": 30,
        "pct_informal_housing": 23,
        "comorbidity_prevalence": 14,
        "tree_cover_pct": 21,
        "ac_penetration_pct": 42,
        "uhi_factor": 1.0
    },
    {
        "id": 20,
        "name": "Ahmedabad Ward (Bopal)",
        "centroid_lat": 23.0425,
        "centroid_lon": 72.5314,
        "pct_elderly": 16,
        "pct_outdoor_workers": 35,
        "pct_informal_housing": 27,
        "comorbidity_prevalence": 17,
        "tree_cover_pct": 19,
        "ac_penetration_pct": 38,
        "uhi_factor": 0.3
    },
    {
        "id": 21,
        "name": "Ahmedabad Ward (Maninagar)",
        "centroid_lat": 23.0425,
        "centroid_lon": 72.5714,
        "pct_elderly": 18,
        "pct_outdoor_workers": 40,
        "pct_informal_housing": 31,
        "comorbidity_prevalence": 8,
        "tree_cover_pct": 17,
        "ac_penetration_pct": 34,
        "uhi_factor": 0.3
    },
    {
        "id": 22,
        "name": "Ahmedabad Ward (Vastrapur)",
        "centroid_lat": 23.0425,
        "centroid_lon": 72.6114,
        "pct_elderly": 20,
        "pct_outdoor_workers": 20,
        "pct_informal_housing": 35,
        "comorbidity_prevalence": 11,
        "tree_cover_pct": 15,
        "ac_penetration_pct": 30,
        "uhi_factor": 0.3
    }
]

# In-memory store for computed risks (used when DB is not available)
# Maps ward_id → list of risk records
_risk_store: dict[int, list[dict]] = {}


def get_risk_store() -> dict[int, list[dict]]:
    """Access the in-memory risk store."""
    return _risk_store


def compute_ward_risk(ward: dict, weather: dict) -> dict:
    """
    Compute all thermal indices and MRI for a single ward given weather data.

    Returns a risk record dict ready for storage.
    """
    current = weather["current"]
    temp = current["temp_c"]
    rh = current["rh_pct"]
    wind = current["wind_ms"]
    solar = current["solar_wm2"]

    # Compute thermal indices
    hi = compute_heat_index(temp, rh)
    wbgt = compute_wbgt(temp, rh, wind, solar)
    # For UTCI, estimate MRT as ~Ta + solar contribution
    mrt = temp + 0.015 * solar  # simplified MRT estimation
    utci = compute_utci(temp, rh, wind, mrt)

    # Compute vulnerability
    vuln_score = compute_vulnerability_score(ward)

    # Compute MRI (using WBGT as primary index)
    mri_result = compute_mortality_risk_index(
        wbgt, "wbgt", vuln_score, ward_data=ward
    )

    return {
        "ward_id": ward["id"],
        "ward_name": ward["name"],
        "timestamp": current.get("timestamp", datetime.now(timezone.utc).isoformat()),
        "temp_c": round(temp, 1),
        "rh_pct": round(rh, 1),
        "wind_ms": round(wind, 1),
        "solar_wm2": round(solar, 1),
        "heat_index": round(hi, 2),
        "wbgt": round(wbgt, 2),
        "utci": round(utci, 2),
        "vulnerability_score": round(vuln_score, 2),
        "mri_score": mri_result["mri_score"],
        "risk_band": mri_result["risk_band"],
        "breakdown": mri_result["breakdown"],
    }


def compute_ward_forecast(ward: dict, weather: dict) -> list[dict]:
    """
    Compute 5-day forecast risk records for a ward.
    """
    forecast_records = []
    for day in weather.get("daily_forecast", []):
        temp = day["temp_mean_c"]
        rh = day["rh_mean_pct"]
        wind = day["wind_max_ms"]
        solar = day["solar_mean_wm2"]

        hi = compute_heat_index(temp, rh)
        wbgt = compute_wbgt(temp, rh, wind, solar)
        mrt = temp + 0.015 * solar
        utci = compute_utci(temp, rh, wind, mrt)

        vuln_score = compute_vulnerability_score(ward)
        mri_result = compute_mortality_risk_index(
            wbgt, "wbgt", vuln_score, ward_data=ward
        )

        forecast_records.append({
            "date": day["date"],
            "temp_c": round(temp, 1),
            "rh_pct": round(rh, 1),
            "wind_ms": round(wind, 1),
            "solar_wm2": round(solar, 1),
            "heat_index": round(hi, 2),
            "wbgt": round(wbgt, 2),
            "utci": round(utci, 2),
            "mri_score": mri_result["mri_score"],
            "risk_band": mri_result["risk_band"],
            "breakdown": mri_result["breakdown"],
        })

    return forecast_records


async def run_ingestion():
    """
    Main ingestion job — fetches weather + computes risk for all wards.
    Called by the scheduler every WEATHER_FETCH_INTERVAL_HOURS.
    """
    logger.info("Starting weather ingestion cycle...")

    for ward in SAMPLE_WARDS:
        try:
            weather = await fetch_weather(
                ward["centroid_lat"], ward["centroid_lon"]
            )
            ward_weather = downscale_to_ward(weather, ward)

            # Compute current risk
            risk = compute_ward_risk(ward, ward_weather)
            logger.info(
                f"Ward {ward['name']}: WBGT={risk['wbgt']}, "
                f"MRI={risk['mri_score']}, Band={risk['risk_band']}"
            )

            # Compute forecast
            forecast = compute_ward_forecast(ward, ward_weather)

            # Store in memory (would go to DB in production)
            _risk_store[ward["id"]] = {
                "current": risk,
                "forecast": forecast,
                "ward": ward,
            }

        except Exception as e:
            logger.error(f"Failed to process ward {ward['name']}: {e}")

    logger.info(f"Ingestion complete. Processed {len(SAMPLE_WARDS)} wards.")
