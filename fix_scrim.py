import re

with open("frontend/src/components/Map.tsx", "r", encoding="utf-8") as f:
    c = f.read()

# Reduce scrim opacity
c = c.replace("fillColor: '#0a0c0e', fillOpacity: 0.45", "fillColor: '#0a0c0e', fillOpacity: 0.25")

with open("frontend/src/components/Map.tsx", "w", encoding="utf-8") as f:
    f.write(c)

print("Updated Map scrim")
