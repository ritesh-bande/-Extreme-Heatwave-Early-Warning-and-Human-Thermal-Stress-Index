import re
with open("frontend/src/components/HospitalFeedback.tsx", "r", encoding="utf-8") as f:
    c = f.read()

c = c.replace("fill: '#94a3b8'", "fill: '#6B7075'") # tertiary
c = c.replace("fill: '#ef4444'", "fill: '#4C9F70'") # accent
c = c.replace("fill: '#3b82f6'", "fill: '#9BA1A6'") # secondary
c = c.replace("stroke=\"#ef4444\"", "stroke=\"#4C9F70\"")
c = c.replace("stroke=\"#3b82f6\"", "stroke=\"#9BA1A6\"")
c = c.replace("Red: Actual Cases | Blue: MRI Forecast", "Green: Actual Cases | Gray: MRI Forecast")

with open("frontend/src/components/HospitalFeedback.tsx", "w", encoding="utf-8") as f:
    f.write(c)

with open("frontend/src/App.tsx", "r", encoding="utf-8") as f:
    c2 = f.read()

c2 = c2.replace("fill: '#94a3b8'", "fill: '#6B7075'")
c2 = c2.replace("fill: '#f97316'", "fill: '#4C9F70'")
c2 = c2.replace("stroke=\"#f97316\"", "stroke=\"#4C9F70\"")
c2 = c2.replace("stopColor=\"#f97316\"", "stopColor=\"#4C9F70\"")
c2 = c2.replace("stopColor=\"#a855f7\"", "stopColor=\"#15181C\"")

with open("frontend/src/App.tsx", "w", encoding="utf-8") as f:
    f.write(c2)

print("Updated chart colors")
