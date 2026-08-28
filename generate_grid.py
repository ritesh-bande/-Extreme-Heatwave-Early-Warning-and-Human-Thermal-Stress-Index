import json
import math

min_lat, max_lat = 21.05, 21.25
min_lon, max_lon = 78.95, 79.15
rows, cols = 10, 15

lat_step = (max_lat - min_lat) / rows
lon_step = (max_lon - min_lon) / cols

center_lat = (min_lat + max_lat) / 2
center_lon = (min_lon + max_lon) / 2
max_dist = math.sqrt((max_lat - center_lat)**2 + (max_lon - center_lon)**2)

features = []
sample_wards = []

ward_id = 1
for r in range(rows):
    for c in range(cols):
        cell_min_lat = min_lat + r * lat_step
        cell_max_lat = cell_min_lat + lat_step
        cell_min_lon = min_lon + c * lon_step
        cell_max_lon = cell_min_lon + lon_step
        
        centroid_lat = (cell_min_lat + cell_max_lat) / 2
        centroid_lon = (cell_min_lon + cell_max_lon) / 2
        
        # Calculate UHI multiplier (0.0 to 1.0, 1.0 being center)
        dist = math.sqrt((centroid_lat - center_lat)**2 + (centroid_lon - center_lon)**2)
        uhi_factor = max(0, 1.0 - (dist / max_dist))
        
        name = f"Grid Cell {ward_id} (Nagpur)"
        
        # GeoJSON Feature
        feature = {
            "type": "Feature",
            "properties": {
                "id": ward_id,
                "name": name,
                "uhi_factor": round(uhi_factor, 3)
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [cell_min_lon, cell_min_lat],
                    [cell_max_lon, cell_min_lat],
                    [cell_max_lon, cell_max_lat],
                    [cell_min_lon, cell_max_lat],
                    [cell_min_lon, cell_min_lat]
                ]]
            }
        }
        features.append(feature)
        
        # Backend Sample Ward
        sample_wards.append({
            "id": ward_id,
            "name": name,
            "centroid_lat": round(centroid_lat, 4),
            "centroid_lon": round(centroid_lon, 4),
            "uhi_factor": round(uhi_factor, 3)
        })
        
        ward_id += 1

geojson = {
    "type": "FeatureCollection",
    "features": features
}

with open("frontend/src/data/wardBoundaries.ts", "w") as f:
    f.write("export const wardGeoJSON = " + json.dumps(geojson, indent=2) + ";\n")

with open("backend_sample_wards.json", "w") as f:
    json.dump(sample_wards, f, indent=2)

print("Generated grid data.")
