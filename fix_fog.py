import re

with open("frontend/src/components/Map.tsx", "r", encoding="utf-8") as f:
    c = f.read()

# 1. Remove IDWHeatmap import
c = re.sub(r'import \{ IDWHeatmap, HeatPoint \} from \'\./IDWHeatmap\';\n', '', c)

# 2. Remove IDW rendering and panes
start_idx = c.find("{/* The true IDW interpolated Heatmap Canvas Layer */}")
end_idx = c.find("{/* Transparent Interactive Polygons */}")
if start_idx != -1 and end_idx != -1:
    c = c[:start_idx] + c[end_idx:]

# 3. Remove cyanTintPane and scrimPane
start_idx = c.find("{/* 3. Global Water Cyan Screen Tint */}")
end_idx = c.find("{/* 1. Base Satellite Imagery */}") # wait, it's after Satellite
end_idx = c.find("{/* The true IDW interpolated Heatmap Canvas Layer */}") 
# Let's use regex to strip the panes
c = re.sub(r'\{\/\* 3\. Global Water Cyan Screen Tint \*\/\}.*?\{\/\* Transparent Interactive Polygons \*\/\}', '{/* Crisp Data Polygons */}', c, flags=re.DOTALL)

# 4. Fix polygon rendering to be CRISP solid colors without blur
polygon_render_old = """            <React.Fragment key={wardId}>
              <Polygon 
                positions={positions}
                pathOptions={{ 
                  fillColor: 'transparent', 
                  color: isSelected ? '#ffffff' : 'transparent',
                  weight: isSelected ? 2 : 0,
                  fillOpacity: 0
                }}
                eventHandlers={{
                  click: () => onSelectWard(wardId),
                  mouseover: (e) => {
                    if (!isSelected) {
                      e.target.setStyle({ weight: 1, color: 'rgba(255,255,255,0.4)' });
                    }
                  },
                  mouseout: (e) => {
                    if (!isSelected) {
                      e.target.setStyle({ weight: 0, color: 'transparent' });
                    }
                  }
                }}
              >"""

polygon_render_new = """            <React.Fragment key={wardId}>
              <Polygon 
                positions={positions}
                pathOptions={{ 
                  fillColor: getWardColor(wardId), 
                  color: isSelected ? '#ffffff' : '#ffffff',
                  weight: isSelected ? 3 : 1,
                  fillOpacity: isSelected ? 0.7 : 0.5
                }}
                eventHandlers={{
                  click: () => onSelectWard(wardId),
                  mouseover: (e) => {
                    if (!isSelected) {
                      e.target.setStyle({ fillOpacity: 0.8, weight: 2 });
                    }
                  },
                  mouseout: (e) => {
                    if (!isSelected) {
                      e.target.setStyle({ fillOpacity: 0.5, weight: 1 });
                    }
                  }
                }}
              >"""

c = c.replace(polygon_render_old, polygon_render_new)

# 5. Bring back getWardColor
get_ward_color = """
  // Discrete color bands for clean, foggy-free visualization
  const getWardColor = (id: number) => {
    const ward = wards.find(w => w.id === id);
    if (!ward) return '#808080';
    const val = ward[colorMetric];
    if (typeof val !== 'number') return '#808080';
    
    // Scale for discrete colors: Deep Blue, Light Blue, Yellow, Orange, Red
    const norm = (val - minVal) / (maxVal - minVal === 0 ? 1 : maxVal - minVal);
    if (norm < 0.2) return '#3b82f6'; // Blue
    if (norm < 0.4) return '#22c55e'; // Green
    if (norm < 0.6) return '#eab308'; // Yellow
    if (norm < 0.8) return '#f97316'; // Orange
    return '#ef4444'; // Red
  };

  const gradientString = `linear-gradient(to right, #3b82f6 0%, #22c55e 25%, #eab308 50%, #f97316 75%, #ef4444 100%)`;
"""
c = c.replace("const gradientString = `linear-gradient(to right, #053061 0%, #4393C3 25%, #D1E5F0 45%, #F7F7F7 50%, #FDDBC7 55%, #D6604D 75%, #67001F 100%)`;", get_ward_color)

with open("frontend/src/components/Map.tsx", "w", encoding="utf-8") as f:
    f.write(c)

print("Reverted to crisp polygons")
