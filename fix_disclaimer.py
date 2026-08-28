import re
with open("frontend/src/components/Map.tsx", "r", encoding="utf-8") as f:
    c = f.read()

c = re.sub(r'\{\/\* Grid Disclaimer \*\/\}.*?<\/div>', '', c, flags=re.DOTALL)

with open("frontend/src/components/Map.tsx", "w", encoding="utf-8") as f:
    f.write(c)

print("Removed disclaimer")
