import re

with open("frontend/src/components/Map.tsx", "r", encoding="utf-8") as f:
    c = f.read()

# I will update the polygon to have NO fill (just a thin border) and add a solid CircleMarker for the "PT" (point).
polygon_render_old = """            <React.Fragment key={wardId}>
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
              >
                <Tooltip sticky className="font-sans font-medium border border-subtle shadow-sm card-surface text-primary rounded">
                  <div className="flex flex-col text-xs">
                    <span className="uppercase tracking-ui text-secondary mb-1 text-[10px]">{feature.properties.name}</span>
                    <span className="flex items-center gap-2 tabular-data">
                      {colorMetric.toUpperCase()}: <strong className="text-base">{ward[colorMetric]?.toFixed(1)}</strong>
                    </span>
                  </div>
                </Tooltip>
              </Polygon>"""

polygon_render_new = """            <React.Fragment key={wardId}>
              {/* Thin, un-filled boundary so we can see the exact area without foggy overlay */}
              <Polygon 
                positions={positions}
                pathOptions={{ 
                  fillColor: 'transparent', 
                  color: 'rgba(255,255,255,0.2)',
                  weight: isSelected ? 2 : 1,
                  fillOpacity: 0
                }}
                interactive={false}
              />
              
              {/* Crisp colored point (PT) exactly as requested */}
              <CircleMarker
                center={[ward.centroid_lat, ward.centroid_lon]}
                radius={isSelected ? 16 : 12}
                pathOptions={{
                  fillColor: getWardColor(wardId),
                  color: '#ffffff',
                  weight: 2,
                  fillOpacity: 1
                }}
                eventHandlers={{
                  click: () => onSelectWard(wardId),
                  mouseover: (e) => {
                    if (!isSelected) {
                      e.target.setRadius(14);
                    }
                  },
                  mouseout: (e) => {
                    if (!isSelected) {
                      e.target.setRadius(12);
                    }
                  }
                }}
              >
                <Tooltip sticky className="font-sans font-medium border border-subtle shadow-sm card-surface text-primary rounded">
                  <div className="flex flex-col text-xs">
                    <span className="uppercase tracking-ui text-secondary mb-1 text-[10px]">{feature.properties.name}</span>
                    <span className="flex items-center gap-2 tabular-data">
                      {colorMetric.toUpperCase()}: <strong className="text-base">{ward[colorMetric]?.toFixed(1)}</strong>
                    </span>
                  </div>
                </Tooltip>
              </CircleMarker>"""

c = c.replace(polygon_render_old, polygon_render_new)

with open("frontend/src/components/Map.tsx", "w", encoding="utf-8") as f:
    f.write(c)

print("Updated map to use crisp points")
