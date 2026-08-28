"""
Alert generation and dispatch system.

Generates role-specific message text based on the ward's risk band and
computed thermal/vulnerability data.
"""

from typing import Dict, Any
from app.services.notifications import get_notification_client
from app.services.livestock import compute_livestock_thi, classify_thi, check_irrigation_alert

def generate_alert(ward_name: str, risk_band: str, mri_data: Dict[str, Any], audience: str, forecast_days: list = None) -> str:
    """
    Generate templated alert text for a specific audience.
    
    Args:
        ward_name: Name of the ward
        risk_band: The computed risk band (e.g., 'Orange', 'Red')
        mri_data: Dictionary containing risk scores and weather data
        audience: Target audience category
        forecast_days: Optional list of daily forecast dicts for irrigation checks
        
    Returns:
        Formatted message string
    """
    # Extract values with safe defaults
    temp = mri_data.get('temp_c', 'N/A')
    rh = mri_data.get('rh_pct', 'N/A')
    wbgt = mri_data.get('wbgt', 'N/A')
    mri = mri_data.get('mri_score', 'N/A')
    
    # Format message based on audience
    if audience == "construction_labor":
        # ISO 7243 threshold guidance
        action = "Stop non-essential outdoor work." if risk_band in ["Red", "Purple"] else "Mandatory 15min rest per hour. Provide shade and hydration."
        return (
            f"🚧 SITE ADVISORY: {ward_name}\n"
            f"WBGT: {wbgt}°C ({risk_band} Alert)\n"
            f"Action: {action}\n"
            f"Risk index: {mri}/100"
        )
        
    elif audience == "healthcare":
        # Example logic: Orange+ triggers admission warnings
        if risk_band in ["Orange", "Red", "Purple"]:
            admissions_est = "+20%" if risk_band == "Orange" else "+40%"
            return (
                f"🏥 HEALTH ALERT: {ward_name}\n"
                f"Severe heat stress expected today (Temp: {temp}°C, MRI: {mri}).\n"
                f"Prepare for estimated {admissions_est} spike in heat-related admissions.\n"
                f"Action: Check IV fluid stocks and activate cooling protocols."
            )
        else:
            return f"🏥 {ward_name} Update: Normal heat operations. MRI: {mri}"
            
    elif audience == "power_grid":
        # Red+ triggers load warnings
        if risk_band in ["Red", "Purple"]:
            return (
                f"⚡ GRID WARNING: {ward_name}\n"
                f"Extreme heat (Temp: {temp}°C). AC cooling load expected to spike.\n"
                f"Risk Band: {risk_band}\n"
                f"Action: Review local transformer capacity."
            )
        else:
            return f"⚡ GRID: {ward_name} cooling load nominal."
            
    elif audience == "farmers":
        # Integrate Livestock & Irrigation logic
        if isinstance(temp, (int, float)) and isinstance(rh, (int, float)):
            thi_val = compute_livestock_thi(temp, rh)
            thi_status = classify_thi(thi_val)
        else:
            thi_status = "Unknown"
            
        irr_alert = ""
        if forecast_days:
            irr_check = check_irrigation_alert(forecast_days)
            if irr_check:
                irr_alert = f"\n{irr_check}"
                
        return (
            f"🚜 AGRI ALERT: {ward_name}\n"
            f"Livestock THI Status: {thi_status}. Provide shade and extra water if moderate/severe."
            f"{irr_alert}"
        )
        
    elif audience == "general_public":
        severity = "EXTREME DANGER" if risk_band in ["Red", "Purple"] else "CAUTION"
        return (
            f"⚠️ HEAT {severity}: {ward_name}\n"
            f"Current Temp: {temp}°C. It feels much hotter.\n"
            f"Stay indoors, drink water, and check on elderly neighbors."
        )
        
    else:
        return f"Alert for {ward_name}: Temp {temp}°C, Band: {risk_band}"


def dispatch_alerts(ward_name: str, mri_data: Dict[str, Any], subscribers: list[Dict[str, str]]):
    """
    Generate and send alerts to a list of subscribers.
    subscribers format: [{"number": "+1234567890", "audience": "healthcare"}, ...]
    """
    client = get_notification_client()
    risk_band = mri_data.get('risk_band', 'Green')
    
    # We generally only alert on Orange and above, unless it's a daily summary
    if risk_band not in ["Orange", "Red", "Purple"]:
        return
        
    for sub in subscribers:
        msg = generate_alert(ward_name, risk_band, mri_data, sub["audience"])
        
        # In a real app, you'd choose SMS vs WhatsApp based on user preference
        client.send_sms(sub["number"], msg)

def generate_ivr_script(ward_id: int, language: str) -> str:
    """
    Generates a spoken-style script (IVR) for the general public based on current risk.
    """
    from app.tasks.scheduler import get_risk_store
    store = get_risk_store()
    ward_bundle = store.get(ward_id)
    
    if not ward_bundle:
        return "Error: Ward data unavailable."
        
    ward_name = ward_bundle["ward"].get("name", f"Ward {ward_id}")
    ward_data = ward_bundle["current"]
    risk_band = ward_data.get("risk_band", "Green")
    temp = round(ward_data.get("temp_c", 30))
    
    if language.lower() == "hindi":
        if risk_band in ["Red", "Purple"]:
            return f"Namaskar. {ward_name} mein aaj bhayankar garmi hai. Tapman {temp} degree hai. Kripaya ghar ke andar rahein, khoob paani piyein, aur bujurgon ka dhyan rakhein."
        elif risk_band in ["Orange", "Yellow"]:
            return f"Namaskar. {ward_name} mein aaj garmi badh gayi hai. Tapman {temp} degree hai. Bahar nikalte samay savdhani bartein aur paani peete rahein."
        else:
            return f"Namaskar. {ward_name} mein aaj mausam samanya hai. Tapman {temp} degree hai."
    
    # Default to English
    if risk_band in ["Red", "Purple"]:
        return f"Attention. The heat risk in {ward_name} is currently critical. The temperature is {temp} degrees. Please stay indoors, drink plenty of water, and check on elderly neighbors."
    elif risk_band in ["Orange", "Yellow"]:
        return f"Attention. The heat risk in {ward_name} is elevated. The temperature is {temp} degrees. Please take precautions if going outside and stay hydrated."
    else:
        return f"Hello. The heat risk in {ward_name} is currently low. The temperature is {temp} degrees. Have a safe day."
