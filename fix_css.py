import re
with open("frontend/src/index.css", "r", encoding="utf-8") as f:
    css = f.read()

# Remove the continuous surface blending CSS block
css = re.sub(r'/\* Continuous Surface Blending \(for Map\) \*/.*?stroke-width: 2px;\n\}', '', css, flags=re.DOTALL)

with open("frontend/src/index.css", "w", encoding="utf-8") as f:
    f.write(css)
