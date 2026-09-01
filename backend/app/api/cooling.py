from fastapi import APIRouter
from typing import List, Dict, Any
import math

router = APIRouter(prefix="/api/cooling", tags=["cooling-centers"])

# Mock existing cooling centers (lat, lon)
EXISTING_CENTERS = [
    {"lat": 21.1458, "lon": 79.0882}, # Central Nagpur
    {"lat": 21.1200, "lon": 79.0500}  # South West Nagpur
]

def calculate_distance(lat1, lon1, lat2, lon2):
    """Simple euclidean distance for mock grid scoring."""
    return math.sqrt((lat1 - lat2)**2 + (lon1 - lon2)**2)

@router.get("/recommend")
async def recommend_cooling_center_sites(city: str = 'Nagpur'):
    """
    Recommends 3 optimal sites for new cooling centers based on:
    Population Density * Vulnerability Score * Distance to Nearest Center
    """
    from app.tasks.scheduler import get_risk_store
    store = get_risk_store()
    
    recommendations = []
    
    for ward_id, bundle in store.items():
        ward = bundle["ward"]
        if city.lower() not in ward.get("name", "").lower():
            continue
        current = bundle["current"]
        
        lat = ward.get("centroid_lat", 0)
        lon = ward.get("centroid_lon", 0)
        
        # 1. Distance Gap: Find nearest existing center
        min_dist = float('inf')
        for center in EXISTING_CENTERS:
            dist = calculate_distance(lat, lon, center["lat"], center["lon"])
            if dist < min_dist:
                min_dist = dist
                
        # Fake a distance if no centers (fallback)
        if min_dist == float('inf'):
            min_dist = 0.1
            
        # 2. Vulnerability (using the MRI score we calculated or a fallback)
        vuln_score = current.get("mri_score", 50)
        
        # 3. Population Density (Mocked based on ward ID for demo)
        pop_density = 5000 + (ward_id * 1000)
        
        # Score = Density * Vulnerability * Distance Gap
        # Normalize distance a bit so it's not tiny
        dist_factor = min_dist * 100 
        optim_score = pop_density * vuln_score * dist_factor
        
        additional_coverage = int(pop_density * 0.4 * (dist_factor))
        
        recommendations.append({
            "ward_id": ward_id,
            "ward_name": ward.get("name", f"Ward {ward_id}"),
            "lat": lat,
            "lon": lon,
            "optimization_score": round(optim_score, 2),
            "nearest_center_km": round(min_dist * 111, 1), # rough degree to km conversion
            "coverage_improvement": additional_coverage,
            "reasoning": f"High density area with vulnerability score {round(vuln_score,1)}. Nearest center is {round(min_dist * 111, 1)}km away. Would cover ~{additional_coverage} additional at-risk residents."
        })
        
    # Return top 3
    recommendations.sort(key=lambda x: x["optimization_score"], reverse=True)
    return recommendations[:3]
