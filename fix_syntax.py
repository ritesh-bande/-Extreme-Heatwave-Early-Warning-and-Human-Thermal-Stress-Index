import re
with open("frontend/src/components/IDWHeatmap.tsx", "r", encoding="utf-8") as f:
    c = f.read()

# Fix the syntax error manually
correct_click = """
  // Click Handler for Debug/Verification Tooltip
  useMapEvents({
    click(e) {
      const res = computeIDW(e.latlng.lat, e.latlng.lng, points);
      if (res.minDistance > 0.25) return; // Don't show tooltip if completely outside data
      setClickPos({ lat: e.latlng.lat, lng: e.latlng.lng, val: res.val });
    }
  });

  useEffect(() => {
"""

c = re.sub(r'// Click Handler for Debug/Verification Tooltip\s+useMapEvents\(\{\s+click\(e\) \{.*?\);\s+\}\s+\}\);\s+useEffect\(\(\) => \{', correct_click, c, flags=re.DOTALL)

with open("frontend/src/components/IDWHeatmap.tsx", "w", encoding="utf-8") as f:
    f.write(c)

print("Syntax fixed")
