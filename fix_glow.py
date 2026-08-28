import re
with open("frontend/src/App.tsx", "r", encoding="utf-8") as f:
    c = f.read()

c = c.replace("blur-[80px] opacity-40", "blur-[80px] opacity-10")

with open("frontend/src/App.tsx", "w", encoding="utf-8") as f:
    f.write(c)
