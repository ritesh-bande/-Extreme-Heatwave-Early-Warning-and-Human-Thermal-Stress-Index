/**
 * API service layer for the Heatwave EWS frontend.
 */

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api';

export interface WardData {
  id: number;
  name: string;
  centroid_lat: number;
  centroid_lon: number;
  risk_band: string;
  mri_score: number;
  heat_index?: number;
  wbgt?: number;
  utci?: number;
  vulnerability_score?: number;
  temp_c?: number;
  rh_pct?: number;
  wind_ms?: number;
  solar_wm2?: number;
  breakdown?: Record<string, number>;
  timestamp?: string;
}

export interface ForecastDay {
  date: string;
  wbgt: number;
  heat_index: number;
  utci: number;
  mri_score: number;
  risk_band: string;
  temp_c: number;
  rh_pct: number;
}

export async function fetchWards(): Promise<WardData[]> {
  const res = await fetch(`${API_BASE}/wards`);
  if (!res.ok) throw new Error('Failed to fetch wards');
  return res.json();
}

export async function triggerIngest(): Promise<void> {
  const res = await fetch(`${API_BASE}/ingest`, { method: 'POST' });
  if (!res.ok) throw new Error('Failed to trigger ingest');
}

export async function fetchWardForecast(wardId: number): Promise<ForecastDay[]> {
  const res = await fetch(`${API_BASE}/wards/${wardId}/forecast`);
  if (!res.ok) throw new Error(`Failed to fetch forecast: ${res.status}`);
  return res.json();
}

export async function fetchAlertPreview(wardId: number): Promise<Record<string, string>> {
  const res = await fetch(`${API_BASE}/alerts/preview/${wardId}`, { method: 'POST' });
  if (!res.ok) throw new Error(`Failed to fetch alerts: ${res.status}`);
  return res.json();
}

export async function fetchEVStatus(wardId: number): Promise<any> {
  const res = await fetch(`${API_BASE}/ev-safety/${wardId}`);
  if (!res.ok) throw new Error(`Failed to fetch EV status: ${res.status}`);
  return res.json();
}

export async function fetchIVRScript(wardId: number, lang: string = 'english'): Promise<{script: string}> {
  const res = await fetch(`${API_BASE}/alerts/ivr/${wardId}?lang=${lang}`);
  if (!res.ok) throw new Error(`Failed to fetch IVR: ${res.status}`);
  return res.json();
}

export async function registerCitizen(data: any): Promise<any> {
  const res = await fetch(`${API_BASE}/citizens/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  if (!res.ok) throw new Error(`Registration failed: ${res.status}`);
  return res.json();
}

export async function fetchPersonalAlert(citizenId: string): Promise<{sms_preview: string}> {
  const res = await fetch(`${API_BASE}/citizens/preview_alert/${citizenId}`);
  if (!res.ok) throw new Error(`Failed to fetch alert preview: ${res.status}`);
  return res.json();
}

export async function getCoolingRecommendations(city: string = 'Nagpur'): Promise<any[]> {
  const res = await fetch(`${API_BASE}/cooling/recommend?city=${city}`);
  if (!res.ok) throw new Error(`Failed to fetch cooling recommendations: ${res.status}`);
  return res.json();
}

export async function submitHospitalFeedback(data: any): Promise<any> {
  const res = await fetch(`${API_BASE}/feedback/heat-admissions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  if (!res.ok) throw new Error(`Failed to submit feedback: ${res.status}`);
  return res.json();
}

export async function fetchWardAccuracy(wardId: number): Promise<any[]> {
  const res = await fetch(`${API_BASE}/feedback/wards/${wardId}/accuracy`);
  if (!res.ok) throw new Error(`Failed to fetch ward accuracy: ${res.status}`);
  return res.json();
}
