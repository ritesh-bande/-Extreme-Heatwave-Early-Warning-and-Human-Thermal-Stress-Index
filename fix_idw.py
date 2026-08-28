import re
with open("frontend/src/components/IDWHeatmap.tsx", "r", encoding="utf-8") as f:
    c = f.read()

# Replace computeIDW to also return minDistance
compute_idw_new = """
export function computeIDW(lat: number, lng: number, points: HeatPoint[]): { val: number, minDistance: number } {
  if (points.length === 0) return { val: 0, minDistance: Infinity };
  let num = 0;
  let den = 0;
  let minD2 = Infinity;
  for (const p of points) {
    const dx = p.lng - lng;
    const dy = p.lat - lat;
    const d2 = dx*dx + dy*dy;
    if (d2 < minD2) minD2 = d2;
    
    if (d2 < 0.0000000001) {
      return { val: p.val, minDistance: 0 };
    }
    const w = 1 / d2;
    num += w * p.val;
    den += w;
  }
  return { val: num / den, minDistance: Math.sqrt(minD2) };
}
"""
c = re.sub(r'export function computeIDW.*?return num / den;\n\}', compute_idw_new, c, flags=re.DOTALL)

# Update the loop to use minDistance for alpha fading
loop_new = """
          const idwResult = computeIDW(lat, lng, points);
          const val = idwResult.val;
          const minDistance = idwResult.minDistance;
          
          const norm = (val - minVal) / range;
          const [r, g, b] = interpolateColor(norm);

          // Smooth fade out beyond the city bounds (approx 5km to 15km)
          const FADE_START = 0.05; 
          const MAX_DISTANCE = 0.15; 
          
          let alpha = 255;
          if (minDistance > FADE_START) {
            if (minDistance > MAX_DISTANCE) {
              alpha = 0;
            } else {
              const fadeRatio = 1 - (minDistance - FADE_START) / (MAX_DISTANCE - FADE_START);
              alpha = Math.floor(255 * fadeRatio);
            }
          }

          const idx = (y * width + x) * 4;
          data[idx] = r;
          data[idx+1] = g;
          data[idx+2] = b;
          data[idx+3] = alpha;
"""
c = re.sub(r'const val = computeIDW\(lat, lng, points\);.*?data\[idx\+3\] = 255;', loop_new, c, flags=re.DOTALL)

# Update the Click handler
click_new = """
    click(e) {
      const res = computeIDW(e.latlng.lat, e.latlng.lng, points);
      if (res.minDistance > 0.15) return; // Don't show tooltip if completely outside data
      setClickPos({ lat: e.latlng.lat, lng: e.latlng.lng, val: res.val });
    }
"""
c = re.sub(r'click\(e\) \{.*?\}', click_new, c, flags=re.DOTALL)

with open("frontend/src/components/IDWHeatmap.tsx", "w", encoding="utf-8") as f:
    f.write(c)

print("Updated IDWHeatmap")
