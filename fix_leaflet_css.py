import re
with open("frontend/src/index.css", "r", encoding="utf-8") as f:
    css = f.read()

# Add Leaflet Popup overrides
popup_css = """
/* Leaflet Overrides for Dark Mode */
.leaflet-popup-content-wrapper, .leaflet-popup-tip {
  background: theme('colors.surface') !important;
  color: theme('colors.primary') !important;
  box-shadow: 0 1px 3px rgba(0,0,0,0.4) !important;
  border: 1px solid theme('colors.subtle') !important;
}
.leaflet-container a.leaflet-popup-close-button {
  color: theme('colors.secondary') !important;
}
"""
if "leaflet-popup-content-wrapper" not in css:
    css += "\n" + popup_css

with open("frontend/src/index.css", "w", encoding="utf-8") as f:
    f.write(css)
