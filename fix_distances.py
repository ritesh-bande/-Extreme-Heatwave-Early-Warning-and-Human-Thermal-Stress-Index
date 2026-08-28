import re
with open("frontend/src/components/IDWHeatmap.tsx", "r", encoding="utf-8") as f:
    c = f.read()

c = c.replace("const FADE_START = 0.05;", "const FADE_START = 0.10;")
c = c.replace("const MAX_DISTANCE = 0.15;", "const MAX_DISTANCE = 0.25;")
c = c.replace("res.minDistance > 0.15", "res.minDistance > 0.25")

with open("frontend/src/components/IDWHeatmap.tsx", "w", encoding="utf-8") as f:
    f.write(c)

print("Updated fade distances")
