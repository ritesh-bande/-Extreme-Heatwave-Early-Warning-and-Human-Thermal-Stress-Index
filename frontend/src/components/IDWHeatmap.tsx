import React, { useEffect, useState } from 'react';
import { useMap, ImageOverlay, Popup, useMapEvents } from 'react-leaflet';
import L from 'leaflet';

export interface HeatPoint {
  lat: number;
  lng: number;
  val: number;
}

interface IDWHeatmapProps {
  points: HeatPoint[];
  minVal: number;
  maxVal: number;
}

const COLOR_STOPS = [
  { p: 0.00, hex: '#053061' },
  { p: 0.25, hex: '#4393C3' },
  { p: 0.45, hex: '#D1E5F0' },
  { p: 0.50, hex: '#F7F7F7' },
  { p: 0.55, hex: '#FDDBC7' },
  { p: 0.75, hex: '#D6604D' },
  { p: 1.00, hex: '#67001F' },
];

function hexToRgb(hex: string) {
  const match = hex.match(/\w\w/g);
  return match ? [parseInt(match[0], 16), parseInt(match[1], 16), parseInt(match[2], 16)] : [0,0,0];
}

function interpolateColor(t: number) {
  t = Math.max(0, Math.min(1, t));
  let i = 0;
  while (i < COLOR_STOPS.length - 1 && t > COLOR_STOPS[i + 1].p) i++;
  const s1 = COLOR_STOPS[i];
  const s2 = COLOR_STOPS[i + 1] || s1;
  const range = s2.p - s1.p;
  const factor = range === 0 ? 0 : (t - s1.p) / range;
  
  const c1 = hexToRgb(s1.hex);
  const c2 = hexToRgb(s2.hex);
  return [
    Math.round(c1[0] + factor * (c2[0] - c1[0])),
    Math.round(c1[1] + factor * (c2[1] - c1[1])),
    Math.round(c1[2] + factor * (c2[2] - c1[2])),
  ];
}

// Compute IDW mathematically for a single lat/lng


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



export function IDWHeatmap({ points, minVal, maxVal }: IDWHeatmapProps) {
  const map = useMap();
  const [overlay, setOverlay] = useState<{url: string, bounds: L.LatLngBoundsExpression} | null>(null);
  const [clickPos, setClickPos] = useState<{lat: number, lng: number, val: number} | null>(null);

  
  // Click Handler for Debug/Verification Tooltip
  useMapEvents({
    click(e) {
      const res = computeIDW(e.latlng.lat, e.latlng.lng, points);
      if (res.minDistance > 0.25) return; // Don't show tooltip if completely outside data
      setClickPos({ lat: e.latlng.lat, lng: e.latlng.lng, val: res.val });
    }
  });

  useEffect(() => {

    if (!points || points.length === 0) return;

    const updateHeatmap = () => {
      const bounds = map.getBounds();
      const size = map.getSize();
      
      // Downscale to 4x4 pixel grid for math performance on huge screens
      const RESOLUTION = 2; 
      const width = Math.max(1, Math.floor(size.x / RESOLUTION));
      const height = Math.max(1, Math.floor(size.y / RESOLUTION));
      
      const canvas = document.createElement('canvas');
      canvas.width = width;
      canvas.height = height;
      const ctx = canvas.getContext('2d');
      if (!ctx) return;
      
      const imgData = ctx.createImageData(width, height);
      const data = imgData.data;

      const nw = bounds.getNorthWest();
      const se = bounds.getSouthEast();
      const latStep = (nw.lat - se.lat) / height;
      const lngStep = (se.lng - nw.lng) / width;

      // Safe range
      const range = maxVal - minVal === 0 ? 1 : maxVal - minVal;

      for (let y = 0; y < height; y++) {
        const lat = nw.lat - y * latStep;
        for (let x = 0; x < width; x++) {
          const lng = nw.lng + x * lngStep;
          
          
          const idwResult = computeIDW(lat, lng, points);
          const val = idwResult.val;
          const minDistance = idwResult.minDistance;
          
          const norm = (val - minVal) / range;
          const [r, g, b] = interpolateColor(norm);

          // Smooth fade out beyond the city bounds (approx 5km to 15km)
          const FADE_START = 0.10; 
          const MAX_DISTANCE = 0.25; 
          
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

        }
      }
      ctx.putImageData(imgData, 0, 0);
      
      setOverlay({
        url: canvas.toDataURL(),
        bounds: [
          [nw.lat, nw.lng],
          [se.lat, se.lng]
        ]
      });
    };

    updateHeatmap();
    map.on('moveend', updateHeatmap);
    map.on('zoomend', updateHeatmap);
    
    return () => {
      map.off('moveend', updateHeatmap);
      map.off('zoomend', updateHeatmap);
    };
  }, [map, points, minVal, maxVal]);

  return (
    <>
      {overlay && <ImageOverlay url={overlay.url} bounds={overlay.bounds} opacity={0.6} className="idw-blend-layer" zIndex={10} />}
      {clickPos && (
        <Popup 
          position={[clickPos.lat, clickPos.lng]} 
          onClose={() => setClickPos(null)}
          className="idw-tooltip"
        >
          <div className="font-sans text-xs flex flex-col items-center p-1">
            <span className="text-secondary font-semibold uppercase tracking-ui text-[10px] mb-1">Interpolated Value</span>
            <span className="tabular-data text-base font-bold text-base bg-surface px-2 py-1 rounded border border-subtle">
              {clickPos.val.toFixed(2)}
            </span>
          </div>
        </Popup>
      )}
    </>
  );
}
