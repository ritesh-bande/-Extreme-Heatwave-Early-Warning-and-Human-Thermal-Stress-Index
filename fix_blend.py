import re

with open("frontend/src/index.css", "r", encoding="utf-8") as f:
    css = f.read()

blend_css = """
.idw-blend-layer {
  mix-blend-mode: multiply;
}
"""
if "idw-blend-layer" not in css:
    css += blend_css

with open("frontend/src/index.css", "w", encoding="utf-8") as f:
    f.write(css)

print("Updated index.css")
