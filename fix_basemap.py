import re
with open("frontend/src/components/Map.tsx", "r", encoding="utf-8") as f:
    c = f.read()

# Change TileLayer
old_tile = 'url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"'
new_tile = 'url="https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}"\n          className="bright-basemap"'
c = c.replace(old_tile, new_tile)

# Add attribution for ESRI
c = c.replace('attribution="&copy; OpenStreetMap contributors &copy; CARTO"', 'attribution="&copy; Esri &mdash; Esri, DeLorme, NAVTEQ"')

with open("frontend/src/components/Map.tsx", "w", encoding="utf-8") as f:
    f.write(c)

with open("frontend/src/index.css", "r", encoding="utf-8") as f:
    css = f.read()

# Add bright-basemap class
css_override = """
/* Brighten ESRI Dark Gray Basemap */
.leaflet-layer {
  filter: brightness(1.6) contrast(1.2) saturate(1.2);
}
.leaflet-overlay-pane {
  filter: none; 
}
"""
if "brighten ESRI" not in css.lower():
    css += "\n" + css_override
with open("frontend/src/index.css", "w", encoding="utf-8") as f:
    f.write(css)

print("Updated basemap")
