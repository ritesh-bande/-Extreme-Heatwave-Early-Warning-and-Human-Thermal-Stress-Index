import re

with open("frontend/src/api.ts", "r", encoding="utf-8") as f:
    c = f.read()

# Make API_BASE configurable via Environment Variable for Vercel
old_base = "const API_BASE = '/api';"
new_base = "const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api';"

if old_base in c:
    c = c.replace(old_base, new_base)
    with open("frontend/src/api.ts", "w", encoding="utf-8") as f:
        f.write(c)
    print("Updated api.ts for Vercel")
else:
    print("Already updated or not found")
