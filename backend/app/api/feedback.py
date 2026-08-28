from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, List, Any
from datetime import date, timedelta

router = APIRouter(prefix="/api/feedback", tags=["feedback"])

# Mock database for hospital reports: { ward_id: [ {date, reported_admissions, predicted_mri} ] }
HOSPITAL_DB: Dict[int, List[Dict[str, Any]]] = {}

class HeatAdmissionReport(BaseModel):
    ward_id: int
    report_date: str # YYYY-MM-DD
    reported_heat_admissions: int

@router.post("/heat-admissions")
async def log_heat_admissions(report: HeatAdmissionReport):
    if report.ward_id not in HOSPITAL_DB:
        # Pre-seed with some historical mock data so the chart isn't empty
        HOSPITAL_DB[report.ward_id] = []
        base_date = date.fromisoformat(report.report_date)
        for i in range(14, 0, -1):
            hist_date = base_date - timedelta(days=i)
            # Fake some correlation
            HOSPITAL_DB[report.ward_id].append({
                "date": hist_date.isoformat(),
                "reported_admissions": 10 + (i % 5),
                "predicted_mri": 50 + (i % 10) * 2
            })
            
    # Fetch current MRI prediction from store if possible, else mock
    from app.tasks.scheduler import get_risk_store
    store = get_risk_store()
    ward_bundle = store.get(report.ward_id)
    ward_data = ward_bundle["current"] if ward_bundle else None
    predicted_mri = ward_data.get("mri_score", 60) if ward_data else 60

    HOSPITAL_DB[report.ward_id].append({
        "date": report.report_date,
        "reported_admissions": report.reported_heat_admissions,
        "predicted_mri": predicted_mri
    })
    
    return {"status": "logged", "entries": len(HOSPITAL_DB[report.ward_id])}

@router.get("/wards/{ward_id}/accuracy")
async def get_ward_accuracy(ward_id: int):
    # Return historical data + newly logged data
    if ward_id not in HOSPITAL_DB:
        return []
    return HOSPITAL_DB[ward_id][-14:] # Return last 14 days
