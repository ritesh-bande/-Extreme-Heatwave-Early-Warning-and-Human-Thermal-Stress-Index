import re

with open("frontend/src/components/IDWHeatmap.tsx", "r", encoding="utf-8") as f:
    c = f.read()

# 1. Update IDW formula (lower p-value for smoother blending instead of blobs)
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
    // Using p=1.2 for much smoother spatial interpolation (less "blobby" than p=2)
    const w = 1 / Math.pow(Math.sqrt(d2), 1.2);
    num += w * p.val;
    den += w;
  }
  return { val: num / den, minDistance: Math.sqrt(minD2) };
}
"""
c = re.sub(r'export function computeIDW.*?return \{ val: num / den, minDistance: Math.sqrt\(minD2\) \};\n\}', compute_idw_new, c, flags=re.DOTALL)

# 2. Increase Resolution
c = c.replace("const RESOLUTION = 4;", "const RESOLUTION = 2;")

# 3. Reduce Opacity & Add Blend Mode Class
c = c.replace('opacity={0.8}', 'opacity={0.6} className="idw-blend-layer"')
c = c.replace('opacity={0.75}', 'opacity={0.6} className="idw-blend-layer"')

with open("frontend/src/components/IDWHeatmap.tsx", "w", encoding="utf-8") as f:
    f.write(c)

print("Updated IDWHeatmap")
