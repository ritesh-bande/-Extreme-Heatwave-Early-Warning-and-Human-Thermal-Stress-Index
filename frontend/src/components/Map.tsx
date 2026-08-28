import React, { useEffect } from 'react';
import { MapContainer, TileLayer, Polygon, Tooltip, useMap, CircleMarker, Pane, Rectangle } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import { wardGeoJSON } from '../data/wardBoundaries';
import { WardData } from '../api';
import { RISK_COLORS } from './ui-utils';

interface MapProps {
  wards: WardData[];
  selectedWardId: number | null;
  onSelectWard: (id: number) => void;
  colorMetric: 'mri_score' | 'wbgt' | 'heat_index' | 'utci';
  coolingSites?: any[];
  selectedCity: string;
}

const COLOR_BANDS = RISK_COLORS;

function MapController({ selectedWardId, wards, selectedCity }: { selectedWardId: number | null, wards: WardData[], selectedCity: string }) {
  const map = useMap();
  
  useEffect(() => {
    const CITIES: Record<string, [number, number]> = {
      'Nagpur': [21.1458, 79.0882],
      'Chennai': [13.0827, 80.2707],
      'Ahmedabad': [23.0225, 72.5714]
    };
    const currentCenter = CITIES[selectedCity] || CITIES['Nagpur'];

    if (selectedWardId) {
      const ward = wards.find(w => w.id === selectedWardId);
      if (ward) {
        map.flyTo([ward.centroid_lat, ward.centroid_lon], 13, {
          duration: 1.5,
          easeLinearity: 0.25
        });
      }
    } else {
      map.flyTo(currentCenter, 11, {
        duration: 1.5,
        easeLinearity: 0.25
      });
    }
  }, [selectedWardId, wards, map, selectedCity]);

  return null;
}

export function DashboardMap({ wards, selectedWardId, onSelectWard, colorMetric, coolingSites = [], selectedCity }: MapProps) {
  const CITIES: Record<string, [number, number]> = {
    'Nagpur': [21.1458, 79.0882],
    'Chennai': [13.0827, 80.2707],
    'Ahmedabad': [23.0225, 72.5714]
  };
  const currentCenter = CITIES[selectedCity] || CITIES['Nagpur'];

  // Prepare points for IDW
  const points: any[] = wards
    .filter(w => typeof w[colorMetric] === 'number')
    .map(w => ({
      lat: w.centroid_lat,
      lng: w.centroid_lon,
      val: w[colorMetric] as number
    }));

  let minVal = 0;
  let maxVal = 100;

  if (points.length > 0) {
    minVal = Math.min(...points.map(p => p.val));
    maxVal = Math.max(...points.map(p => p.val));
    if (minVal === maxVal) {
      minVal -= 1;
      maxVal += 1;
    }
  }
  
  // Create a strict gradient string matching the RdBu scale
  
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


  return (
    <>
      <MapContainer 
        center={currentCenter} 
        zoom={11} 
        style={{ height: '100%', width: '100%', zIndex: 0 }}
        zoomControl={false}
      >
        {/* 1. Base Satellite Imagery */}
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

        <MapController selectedWardId={selectedWardId} wards={wards} selectedCity={selectedCity} />
        {/* Crisp Data Polygons */}
        {wardGeoJSON.features.map((feature, idx) => {
          const wardId = feature.properties.id;
          const ward = wards.find(w => w.id === wardId);
          if (!ward) return null;

          const isSelected = selectedWardId === wardId;
          const positions = (feature.geometry.coordinates[0] as number[][]).map(
            coord => [coord[1], coord[0]] as [number, number]
          );

          return (
            <React.Fragment key={wardId}>
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
              </CircleMarker>
              
              {isSelected && (
                <CircleMarker 
                  center={[ward.centroid_lat, ward.centroid_lon]}
                  radius={20}
                  pathOptions={{ 
                    color: '#ffffff', 
                    fillColor: 'transparent',
                    className: 'animate-ping'
                  }}
                  interactive={false}
                />
              )}
            </React.Fragment>
          );
        })}
        
        {coolingSites.map((site, idx) => (
          <CircleMarker 
            key={`rec-cc-${idx}`} 
            center={[site.lat, site.lon]} 
            radius={8} 
            pathOptions={{ fillColor: '#4C9F70', color: '#ffffff', weight: 2, fillOpacity: 1, className: 'animate-pulse' }}
          >
            <Tooltip 
              direction="top" 
              opacity={1} 
              className="card-surface text-accent border border-accent/50 shadow-sm font-sans"
              permanent={false}
            >
              <div className="flex flex-col gap-1 text-xs">
                <span className="text-primary uppercase tracking-ui border-b border-subtle pb-1 text-[10px]">AI RECOMMENDED SITE</span>
                <span className="font-bold">?? {site.ward_name}</span>
                <span className="text-secondary font-normal">{site.reasoning}</span>
              </div>
            </Tooltip>
          </CircleMarker>
        ))}
      </MapContainer>

      {/* Diverging Colormap Legend Overlay with Dynamic Extents */}
      <div className="absolute bottom-6 right-6 z-[1000] card-surface p-3 rounded-xl flex flex-col gap-1 w-64 pointer-events-none">
        <div className="flex justify-between text-xs font-semibold text-secondary uppercase tracking-ui mb-1">
          <span>{minVal.toFixed(1)}</span>
          <span className="text-primary">{colorMetric.replace('_', ' ')}</span>
          <span>{maxVal.toFixed(1)}</span>
        </div>
        <div className="h-3 w-full rounded-sm" style={{ background: gradientString }}></div>
      </div>

      
    </>
  );
}
