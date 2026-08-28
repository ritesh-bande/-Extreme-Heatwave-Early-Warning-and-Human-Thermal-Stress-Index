import re
with open("frontend/src/components/IDWHeatmap.tsx", "r", encoding="utf-8") as f:
    c = f.read()

c = c.replace("opacity={0.75}", "opacity={0.8}")

with open("frontend/src/components/IDWHeatmap.tsx", "w", encoding="utf-8") as f:
    f.write(c)

print("Updated opacity")
