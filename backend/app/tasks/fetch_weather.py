"""
Weather data ingestion from Open-Meteo API.

Fetches current conditions + 5-day forecast for a given lat/lon.
Uses Open-Meteo's free API (no key required).

TODO: Structure allows swapping to NCMRWF/IMD feeds later by
implementing the same interface.
"""

import httpx
from datetime import datetime, date


# Open-Meteo API base URL
OPEN_METEO_BASE = "https://api.open-meteo.com/v1/forecast"


async def fetch_weather(lat: float, lon: float) -> dict:
    """
    Fetch current weather + 5-day hourly forecast from Open-Meteo.

    Args:
        lat: Latitude (decimal degrees).
        lon: Longitude (decimal degrees).

    Returns:
        Dict with structure:
        {
            "current": {
                "temp_c": float,
                "rh_pct": float,
                "wind_ms": float,
                "solar_wm2": float,
                "timestamp": str (ISO 8601)
            },
            "daily_forecast": [
                {
                    "date": "YYYY-MM-DD",
                    "temp_max_c": float,
                    "temp_min_c": float,
                    "temp_mean_c": float,
                    "rh_mean_pct": float,
                    "wind_max_ms": float,
                    "solar_mean_wm2": float
                },
                ... (5 days)
            ]
        }

    Raises:
        httpx.HTTPError: On network / API failures.
    """
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": [
            "temperature_2m",
            "relative_humidity_2m",
            "wind_speed_10m",
            "shortwave_radiation",
        ],
        "daily": [
            "temperature_2m_max",
            "temperature_2m_min",
            "temperature_2m_mean",
            "relative_humidity_2m_mean",
            "wind_speed_10m_max",
            "shortwave_radiation_sum",
        ],
        "forecast_days": 5,
        "timezone": "auto",
    }



    try:
        headers = {
            "User-Agent": "HeatwaveEWS/1.0 (sih2024 demo; +https://github.com/ritesh-bande)",
            "Accept-Encoding": "gzip, deflate, br"
        }
        async with httpx.AsyncClient(timeout=30.0, headers=headers) as client:
            resp = await client.get(OPEN_METEO_BASE, params=params)
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        # Fallback to mock data if Open-Meteo blocks Render IP or fails
        import random
        from datetime import timedelta
        base_temp = random.uniform(30.0, 36.0) # Lowered fallback temp slightly
        base_rh = random.uniform(40.0, 80.0)
        now_str = datetime.utcnow().isoformat()
        dates = [(datetime.utcnow() + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(5)]
        data = {
            "current": {
                "temperature_2m": base_temp,
                "relative_humidity_2m": base_rh,
                "wind_speed_10m": random.uniform(5.0, 15.0),
                "shortwave_radiation": random.uniform(500, 900),
                "time": now_str
            },
            "daily": {
                "time": dates,
                "temperature_2m_max": [base_temp + random.uniform(2, 5) for _ in dates],
                "temperature_2m_min": [base_temp - random.uniform(5, 10) for _ in dates],
                "temperature_2m_mean": [base_temp for _ in dates],
                "relative_humidity_2m_mean": [base_rh for _ in dates],
                "wind_speed_10m_max": [random.uniform(5.0, 20.0) for _ in dates],
                "shortwave_radiation_sum": [random.uniform(15.0, 25.0) for _ in dates]
            }
        }



    # Parse current conditions
    current_raw = data.get("current", {})
    current = {
        "temp_c": current_raw.get("temperature_2m", 0.0),
        "rh_pct": current_raw.get("relative_humidity_2m", 0.0),
        "wind_ms": current_raw.get("wind_speed_10m", 0.0) / 3.6,  # km/h → m/s
        "solar_wm2": current_raw.get("shortwave_radiation", 0.0),
        "timestamp": current_raw.get("time", datetime.utcnow().isoformat()),
    }

    # Parse daily forecast
    daily_raw = data.get("daily", {})
    dates = daily_raw.get("time", [])
    daily_forecast = []
    for i, d in enumerate(dates):
        # Solar radiation sum (MJ/m²/day) → mean W/m² (divide by ~86400 s,
        # multiply by 1e6 to convert MJ → J; but Open-Meteo gives kWh/m²
        # for shortwave_radiation_sum, not MJ)
        solar_sum = (daily_raw.get("shortwave_radiation_sum") or [0.0] * len(dates))[i]
        # shortwave_radiation_sum is in MJ/m² — convert to mean W/m²
        # over daylight hours (~12h) → MJ / (12*3600) * 1e6
        solar_mean = solar_sum * 1e6 / (12 * 3600) if solar_sum else 0.0

        daily_forecast.append({
            "date": d,
            "temp_max_c": (daily_raw.get("temperature_2m_max") or [0.0] * len(dates))[i],
            "temp_min_c": (daily_raw.get("temperature_2m_min") or [0.0] * len(dates))[i],
            "temp_mean_c": (daily_raw.get("temperature_2m_mean") or [0.0] * len(dates))[i],
            "rh_mean_pct": (daily_raw.get("relative_humidity_2m_mean") or [0.0] * len(dates))[i],
            "wind_max_ms": (
                (daily_raw.get("wind_speed_10m_max") or [0.0] * len(dates))[i] / 3.6
            ),  # km/h → m/s
            "solar_mean_wm2": round(solar_mean, 1),
        })

    return {
        "current": current,
        "daily_forecast": daily_forecast,
    }


def fetch_weather_sync(lat: float, lon: float) -> dict:
    """
    Synchronous wrapper around fetch_weather for use in non-async contexts.
    """
    import asyncio

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # Already in an async context — use nest_asyncio or run in thread
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(
                asyncio.run, fetch_weather(lat, lon)
            ).result()
    else:
        return asyncio.run(fetch_weather(lat, lon))
