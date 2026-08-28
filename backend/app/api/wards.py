"""
Ward API endpoints.

Provides:
  - GET /api/wards           → All wards with current risk data
  - GET /api/wards/{ward_id} → Single ward detail
  - GET /api/wards/{ward_id}/forecast → 5-day forecast for a ward
"""

from fastapi import APIRouter, HTTPException

from app.tasks.scheduler import get_risk_store, SAMPLE_WARDS

router = APIRouter(prefix="/api/wards", tags=["wards"])


@router.get("")
async def list_wards():
    """
    List all wards with their current risk data.

    Returns a list of ward objects, each including current thermal indices,
    vulnerability score, MRI score, and risk band.
    """
    store = get_risk_store()

    wards = []
    for ward in SAMPLE_WARDS:
        ward_data = store.get(ward["id"])
        if ward_data:
            wards.append({
                "id": ward["id"],
                "name": ward["name"],
                "centroid_lat": ward["centroid_lat"],
                "centroid_lon": ward["centroid_lon"],
                **ward_data["current"],
            })
        else:
            # Ward hasn't been processed yet
            wards.append({
                "id": ward["id"],
                "name": ward["name"],
                "centroid_lat": ward["centroid_lat"],
                "centroid_lon": ward["centroid_lon"],
                "risk_band": "Green",
                "mri_score": 0,
                "message": "Awaiting first ingestion cycle",
            })

    return wards


@router.get("/{ward_id}")
async def get_ward(ward_id: int):
    """
    Get detailed risk data for a specific ward.
    """
    store = get_risk_store()

    # Find the ward
    ward = next((w for w in SAMPLE_WARDS if w["id"] == ward_id), None)
    if ward is None:
        raise HTTPException(status_code=404, detail=f"Ward {ward_id} not found")

    ward_data = store.get(ward_id)
    if ward_data is None:
        return {
            "id": ward_id,
            "name": ward["name"],
            "message": "Awaiting first ingestion cycle",
        }

    return {
        "id": ward_id,
        "ward": ward,
        "current": ward_data["current"],
    }


@router.get("/{ward_id}/forecast")
async def get_ward_forecast(ward_id: int):
    """
    Get 5-day forecast with risk data for a specific ward.

    Returns an array of daily forecast objects:
    {date, wbgt, heat_index, mri_score, risk_band}
    """
    store = get_risk_store()

    # Find the ward
    ward = next((w for w in SAMPLE_WARDS if w["id"] == ward_id), None)
    if ward is None:
        raise HTTPException(status_code=404, detail=f"Ward {ward_id} not found")

    ward_data = store.get(ward_id)
    if ward_data is None:
        raise HTTPException(
            status_code=503,
            detail="Weather data not yet available. Wait for ingestion cycle.",
        )

    return ward_data["forecast"]
