import re

with open("frontend/src/components/Map.tsx", "r", encoding="utf-8") as f:
    content = f.read()

# Make the rectangles cover many wrapped copies of the earth to ensure the scrim never "ends" on pan
content = content.replace("bounds={[[-90, -180], [90, 180]]}", "bounds={[[-90, -1000], [90, 1000]]}")

with open("frontend/src/components/Map.tsx", "w", encoding="utf-8") as f:
    f.write(content)

print("Updated scrim bounds")
