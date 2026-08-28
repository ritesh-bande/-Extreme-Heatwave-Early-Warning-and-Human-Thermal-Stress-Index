import re

with open("frontend/src/index.css", "r", encoding="utf-8") as f:
    css = f.read()

# Replace the previous Brighten ESRI CSS
old_css = """/* Brighten ESRI Dark Gray Basemap */
.leaflet-layer {
  filter: brightness(1.6) contrast(1.2) saturate(1.2);
}"""

new_css = """/* Satellite + Terrain Base Filter */
.leaflet-tile-pane {
  filter: saturate(1.25) contrast(1.1) brightness(0.95);
}
.hillshade-layer {
  mix-blend-mode: multiply;
}"""

if "Brighten ESRI" in css:
    css = css.replace(old_css, new_css)
else:
    css += "\n" + new_css

with open("frontend/src/index.css", "w", encoding="utf-8") as f:
    f.write(css)

print("Updated index.css")
