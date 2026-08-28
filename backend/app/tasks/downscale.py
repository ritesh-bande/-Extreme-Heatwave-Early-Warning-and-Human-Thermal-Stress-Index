"""
Spatial downscaling — stub for coarse forecast → ward-level data.

For now, uses simple nearest-grid-point assignment: each ward gets
the forecast from its centroid coordinates.

TODO: Production would use a proper statistical downscaling model
(e.g. LSTM/Prophet trained on historical ward vs. station bias)
or inverse-distance weighting between multiple nearby station points.
"""

from typing import Any


def downscale_to_ward(
    coarse_forecast: dict,
    ward_geom: Any,
) -> dict:
    import copy
    forecast = copy.deepcopy(coarse_forecast)
    uhi_multiplier = ward_geom.get("uhi_factor", 0.0)
    
    # Increase temperature up to +4.5°C based on UHI factor
    temp_bump = 4.5 * uhi_multiplier
    
    forecast["current"]["temp_c"] += temp_bump
    if "daily_forecast" in forecast:
        for day in forecast["daily_forecast"]:
            day["temp_mean_c"] += temp_bump
            
    return forecast
