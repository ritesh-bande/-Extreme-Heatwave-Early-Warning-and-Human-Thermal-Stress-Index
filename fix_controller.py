import re
with open("frontend/src/components/Map.tsx", "r", encoding="utf-8") as f:
    c = f.read()

c = c.replace("{/* Crisp Data Polygons */}", "<MapController selectedWardId={selectedWardId} wards={wards} selectedCity={selectedCity} />\n        {/* Crisp Data Polygons */}")

with open("frontend/src/components/Map.tsx", "w", encoding="utf-8") as f:
    f.write(c)

print("Restored MapController")
