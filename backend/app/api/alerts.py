"""
Alerts API endpoints.

Provides preview capabilities for role-specific alerts.
"""

from fastapi import APIRouter, HTTPException
from app.tasks.scheduler import get_risk_store, SAMPLE_WARDS
from app.services.alerts import generate_alert

router = APIRouter(prefix="/api/alerts", tags=["alerts"])

AUDIENCES = [
    "construction_labor",
    "healthcare",
    "power_grid",
    "farmers",
    "general_public"
]

@router.post("/preview/{ward_id}")
async def preview_alerts(ward_id: int):
    """
    Preview what alerts WOULD be sent for each audience right now for a given ward.
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
            detail="Risk data not yet available for this ward."
        )
        
    current_risk = ward_data["current"]
    risk_band = current_risk.get("risk_band", "Green")
    
    previews = {}
    for audience in AUDIENCES:
        msg = generate_alert(ward["name"], risk_band, current_risk, audience)
        previews[audience] = msg
        
    return {
        "ward_name": ward["name"],
        "risk_band": risk_band,
        "mri_score": current_risk.get("mri_score"),
        "alerts": previews
    }

from app.services.alerts import generate_ivr_script

@router.get("/ivr/{ward_id}")
async def get_ivr_script(ward_id: int, lang: str = "english"):
    script = generate_ivr_script(ward_id, lang)
    return {"script": script}
