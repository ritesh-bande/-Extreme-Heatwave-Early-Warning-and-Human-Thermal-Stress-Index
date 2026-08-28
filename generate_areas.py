import json

cities = {
    "Nagpur": {
        "center": [21.1458, 79.0882],
        "grid": (3, 4), # 12 cells, we'll keep 10
        "names": ["Dharampeth", "Sadar", "Sitabuldi", "Mahal", "Itwari", 
                  "Wardhaman Nagar", "Nandanvan", "Manish Nagar", "Pratap Nagar", "Ramdaspeth"]
    },
    "Chennai": {
        "center": [13.0827, 80.2707],
        "grid": (2, 3), # 6 cells
        "names": ["T. Nagar", "Mylapore", "Adyar", "Velachery", "Anna Nagar", "Guindy"]
    },
    "Ahmedabad": {
        "center": [23.0225, 72.5714],
        "grid": (2, 3), # 6 cells
        "names": ["Kalupur", "Navrangpura", "Satellite", "Bopal", "Maninagar", "Vastrapur"]
    }
}

features = []
sample_wards = []
ward_id = 1

for city, info in cities.items():
    center_lat, center_lon = info["center"]
    rows, cols = info["grid"]
    names = info["names"]
    
    # approximate 0.05 degrees per cell (~5km)
    lat_step = 0.04
    lon_step = 0.04
    
    min_lat = center_lat - (rows * lat_step) / 2
    min_lon = center_lon - (cols * lon_step) / 2
    
    name_idx = 0
    for r in range(rows):
        for c in range(cols):
            if name_idx >= len(names):
                continue
                
            cell_min_lat = min_lat + r * lat_step
            cell_max_lat = cell_min_lat + lat_step
            cell_min_lon = min_lon + c * lon_step
            cell_max_lon = cell_min_lon + lon_step
            
            centroid_lat = (cell_min_lat + cell_max_lat) / 2
            centroid_lon = (cell_min_lon + cell_max_lon) / 2
            
            name = f"{city} Ward ({names[name_idx]})"
            
            features.append({
                "type": "Feature",
                "properties": {"id": ward_id, "name": name, "city": city},
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
            })
            
            sample_wards.append({
                "id": ward_id,
                "name": name,
                "centroid_lat": round(centroid_lat, 4),
                "centroid_lon": round(centroid_lon, 4),
                "pct_elderly": 10 + (name_idx * 2) % 15,
                "pct_outdoor_workers": 20 + (name_idx * 5) % 25,
                "pct_informal_housing": 15 + (name_idx * 4) % 30,
                "comorbidity_prevalence": 8 + (name_idx * 3) % 12,
                "tree_cover_pct": 25 - (name_idx * 2) % 20,
                "ac_penetration_pct": 50 - (name_idx * 4) % 40,
                "uhi_factor": 1.0 if name_idx < 3 else 0.3
            })
            
            name_idx += 1
            ward_id += 1

geojson = {"type": "FeatureCollection", "features": features}
with open("frontend/src/data/wardBoundaries.ts", "w") as f:
    f.write("export const wardGeoJSON = " + json.dumps(geojson, indent=2) + ";\n")
with open("backend_sample_wards.json", "w") as f:
    json.dump(sample_wards, f, indent=2)

print("Generated areas data.")
