import re

with open("frontend/src/components/Map.tsx", "r", encoding="utf-8") as f:
    content = f.read()

# Fix imports
content = content.replace("CircleMarker } from 'react-leaflet'", "CircleMarker, Pane, Rectangle } from 'react-leaflet'")

# Replace the single TileLayer with the Satellite stack
old_tile_block = """        <TileLayer
          url="https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}"
          className="bright-basemap"
          attribution="&copy; Esri &mdash; Esri, DeLorme, NAVTEQ"
        />"""

new_tile_block = """        {/* 1. Base Satellite Imagery */}
        <TileLayer
          url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
          attribution="&copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community"
        />
        
        {/* 2. Terrain / Hillshade Texture */}
        <TileLayer
          url="https://server.arcgisonline.com/ArcGIS/rest/services/Elevation/World_Hillshade/MapServer/tile/{z}/{y}/{x}"
          opacity={0.45}
          className="hillshade-layer"
        />

        {/* 3. Global Water Cyan Screen Tint */}
        <Pane name="cyanTintPane" style={{ zIndex: 250, mixBlendMode: 'screen', pointerEvents: 'none' }}>
          <Rectangle 
             bounds={[[-90, -180], [90, 180]]} 
             pathOptions={{ color: 'transparent', fillColor: '#06b6d4', fillOpacity: 0.08 }} 
             interactive={false}
          />
        </Pane>

        {/* 4. Dark Scrim to Protect IDW Heat Legibility */}
        <Pane name="scrimPane" style={{ zIndex: 260, pointerEvents: 'none' }}>
          <Rectangle 
             bounds={[[-90, -180], [90, 180]]} 
             pathOptions={{ color: 'transparent', fillColor: '#0a0c0e', fillOpacity: 0.45 }} 
             interactive={false}
          />
        </Pane>"""

content = content.replace(old_tile_block, new_tile_block)

with open("frontend/src/components/Map.tsx", "w", encoding="utf-8") as f:
    f.write(content)

print("Updated Map.tsx")
