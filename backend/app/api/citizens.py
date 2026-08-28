from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List
import uuid

router = APIRouter(prefix="/api/citizens", tags=["citizens"])

# Mock database for citizens
CITIZENS_DB: Dict[str, Any] = {}

class CitizenRegistration(BaseModel):
    phone_or_id: str
    ward_id: int
    age: int
    is_pregnant: bool
    occupation: str  # "outdoor_labor", "indoor_desk", "gig_delivery", "informal_vendor", "unemployed_home", "other"
    has_comorbidity: bool
    housing_type: str  # "has_ac", "fan_only", "no_cooling"

def compute_personal_risk_tier(citizen_profile: CitizenRegistration, ward_base_index: float) -> dict:
    """
    Computes a personalized risk score for a citizen.
    Multipliers are layered on top of the ward's base thermal stress index.
    """
    multiplier = 1.0
    reasons = []

    # 1. Age Factor
    if citizen_profile.age > 65:
        multiplier += 0.25
        reasons.append("Senior citizen (>65)")
    elif citizen_profile.age < 5:
        multiplier += 0.20
        reasons.append("Infant/Toddler (<5)")

    # 2. Pregnancy Factor
    if citizen_profile.is_pregnant:
        multiplier += 0.30
        reasons.append("Pregnancy")

    # 3. Comorbidity Factor
    if citizen_profile.has_comorbidity:
        multiplier += 0.35
        reasons.append("Pre-existing health conditions")

    # 4. Occupation Factor
    if citizen_profile.occupation in ["outdoor_labor", "gig_delivery", "informal_vendor"]:
        multiplier += 0.40
        reasons.append(f"High-exposure occupation ({citizen_profile.occupation.replace('_', ' ')})")
    elif citizen_profile.occupation == "indoor_desk":
        multiplier -= 0.10
        reasons.append("Low-exposure occupation (indoor desk)")

    # 5. Housing Factor
    if citizen_profile.housing_type == "no_cooling":
        multiplier += 0.30
        reasons.append("Lack of home cooling")
    elif citizen_profile.housing_type == "has_ac":
        multiplier -= 0.20
        reasons.append("Access to AC at home")

    # Calculate final personal risk score
    personal_risk_score = min(100.0, max(0.0, ward_base_index * multiplier))
    
    # Determine Tier
    if personal_risk_score >= 80:
        tier = "Critical"
    elif personal_risk_score >= 60:
        tier = "High"
    elif personal_risk_score >= 40:
        tier = "Moderate"
    else:
        tier = "Low"

    # Generate explanation
    reason_str = "Your risk is " + tier.lower() + " because: " + ", ".join(reasons) + "."
    if multiplier <= 1.0:
         reason_str = f"Your risk is {tier.lower()} because you have adequate protective factors (like AC or indoor work)."
    
    return {
        "personal_risk_score": round(personal_risk_score, 1),
        "tier": tier,
        "reason": reason_str,
        "base_ward_index": round(ward_base_index, 1),
        "multiplier_applied": round(multiplier, 2)
    }

@router.post("/register")
async def register_citizen(citizen: CitizenRegistration):
    """Register a new citizen and generate their personal risk profile."""
    # We need the ward base thermal index to compute their actual score.
    # We will fetch this from our mock scheduler state.
    from app.tasks.scheduler import get_risk_store
    
    store = get_risk_store()
    ward_bundle = store.get(citizen.ward_id)
    ward_data = ward_bundle["current"] if ward_bundle else None
    
    # Fallback default if ward not found
    ward_base_index = 45.0 
    if ward_data:
        # Base index = temp + (0.33 * rh) - 5.33 (Using the blueprint formula from earlier for consistency)
        ward_base_index = ward_data.get("temp_c", 35) + (0.33 * ward_data.get("rh_pct", 50)) - 5.33

    profile_result = compute_personal_risk_tier(citizen, ward_base_index)
    
    # Save to mock DB
    citizen_id = str(uuid.uuid4())
    CITIZENS_DB[citizen_id] = {
        "profile": citizen.model_dump(),
        "risk_assessment": profile_result
    }
    
    return {
        "status": "registered",
        "citizen_id": citizen_id,
        "assessment": profile_result
    }

@router.get("/preview_alert/{citizen_id}")
async def preview_personal_alert(citizen_id: str):
    """Preview the SMS alert tailored to a specific citizen's risk tier."""
    if citizen_id not in CITIZENS_DB:
        raise HTTPException(status_code=404, detail="Citizen not found")
        
    citizen = CITIZENS_DB[citizen_id]
    tier = citizen["risk_assessment"]["tier"]
    
    # Simple personalized alert generator
    alert_text = f"EWS Alert: Your personal heat risk is currently {tier.upper()}."
    if tier in ["Critical", "High"]:
        if citizen["profile"]["occupation"] in ["outdoor_labor", "gig_delivery"]:
            alert_text += " MANDATORY: Halt outdoor work between 12 PM - 4 PM."
        if citizen["profile"]["housing_type"] == "no_cooling":
            alert_text += " Please locate your nearest public cooling center immediately."
        if citizen["profile"]["is_pregnant"] or citizen["profile"]["age"] > 65:
            alert_text += " Extremely high physiological risk detected. Stay hydrated and seek AC."
    else:
        alert_text += " Maintain standard hydration and heat precautions."
        
    return {"sms_preview": alert_text}
