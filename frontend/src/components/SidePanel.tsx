import React, { useState, useEffect } from 'react';
import { 
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell,
  LineChart, Line, CartesianGrid, AreaChart, Area
} from 'recharts';
import { WardData, fetchWardForecast, fetchAlertPreview, fetchEVStatus, ForecastDay } from '../api';
import { RadialGauge, AnimatedNumber, getRiskColor } from './ui-utils';

interface SidePanelProps {
  ward: WardData | null;
  onClose: () => void;
}

export function SidePanel({ ward, onClose }: SidePanelProps) {
  const [activeTab, setActiveTab] = useState<'overview' | 'alerts' | 'grid'>('overview');
  const [forecast, setForecast] = useState<ForecastDay[]>([]);
  const [alerts, setAlerts] = useState<Record<string, string> | null>(null);
  const [evData, setEvData] = useState<any>(null);
  
  const [loading, setLoading] = useState(false);
  const [showExplanation, setShowExplanation] = useState(false);

  // What-If Simulation State
  const [simTemp, setSimTemp] = useState<number | null>(null);
  const [simRh, setSimRh] = useState<number | null>(null);
  const [isSimulating, setIsSimulating] = useState(false);

  useEffect(() => {
    // Reset simulation when ward changes
    setSimTemp(null);
    setSimRh(null);
    setIsSimulating(false);

    if (ward?.id) {
      setLoading(true);
      Promise.all([
        fetchWardForecast(ward.id).catch(() => []),
        fetchAlertPreview(ward.id).catch(() => null),
        fetchEVStatus(ward.id).catch(() => null)
      ])
      .then(([forecastData, alertData, evResponse]) => {
        setForecast(forecastData);
        setAlerts(alertData ? alertData.alerts : null);
        setEvData(evResponse);
      })
      .finally(() => setLoading(false));
      
      setActiveTab('overview');
      setShowExplanation(false);
    }
  }, [ward?.id]);

  if (!ward) return null;

  // Calculate Simulation Values
  const displayTemp = isSimulating && simTemp !== null ? simTemp : ward.temp_c;
  const displayRh = isSimulating && simRh !== null ? simRh : ward.rh_pct;
  
  let displayMri = ward.mri_score || 0;
  let displayRiskBand = ward.risk_band;
  
  if (isSimulating) {
    // Fake MRI logic: Base MRI + Temp diff + RH diff
    const tempDiff = displayTemp - ward.temp_c;
    const rhDiff = displayRh - ward.rh_pct;
    // Each degree C adds ~2.5 to MRI. Each % RH adds ~0.5 to MRI.
    const mriDelta = (tempDiff * 2.5) + (rhDiff * 0.5);
    displayMri = Math.min(100, Math.max(0, displayMri + mriDelta));
    
    // Assign Risk Band
    if (displayMri < 30) displayRiskBand = 'Green';
    else if (displayMri < 50) displayRiskBand = 'Yellow';
    else if (displayMri < 70) displayRiskBand = 'Orange';
    else if (displayMri < 90) displayRiskBand = 'Red';
    else displayRiskBand = 'Purple';
  }

  const breakdownData = ward.breakdown 
    ? Object.entries(ward.breakdown)
        .map(([name, value]) => ({ name: name.replace(/_/g, ' '), value: Number(value.toFixed(1)) }))
        .sort((a, b) => b.value - a.value)
    : [];

  return (
    <div className="w-full md:w-[480px] bg-[var(--bg-base)] shadow-2xl h-full overflow-y-auto flex flex-col z-10 absolute right-0 top-0 border-l border-[var(--border-subtle)] text-[var(--text-primary)]">
      
      {/* Hero Header */}
      <div className="relative p-6 pb-2">
        <button onClick={onClose} className="absolute right-6 top-6 text-[var(--text-secondary)] hover:text-white transition-colors bg-[var(--bg-card)] hover:bg-[var(--bg-card-hover)] rounded-full w-8 h-8 flex items-center justify-center z-20 shadow">✕</button>
        
        <div className="bg-[var(--bg-card)] rounded-3xl p-6 relative overflow-hidden shadow-lg border border-white/5">
          {/* Soft radial glow background */}
          <div 
            className="absolute -top-1/2 -right-1/4 w-64 h-64 rounded-full blur-[60px] opacity-20 pointer-events-none transition-colors duration-500" 
            style={{ backgroundColor: getRiskColor(displayRiskBand) }}
          ></div>
          
          <div className="relative z-10">
            <h2 className="text-2xl font-bold mb-1 tracking-tight">{ward.name}</h2>
            <div className="text-[var(--text-secondary)] text-sm mb-6 flex items-center gap-2">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"></path><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"></path></svg>
              Monitoring Station
            </div>

            <div className="flex items-center gap-6">
              <div className="relative">
                {/* Gauge Glow */}
                <div 
                  className="absolute inset-0 scale-125 blur-[25px] opacity-25 rounded-full transition-colors duration-500"
                  style={{ backgroundColor: getRiskColor(displayRiskBand) }}
                ></div>
                <RadialGauge value={displayMri} color={getRiskColor(displayRiskBand)} size={110} strokeWidth={8}>
                  <span className="text-4xl font-black text-white leading-none tracking-tighter transition-colors duration-500">
                    <AnimatedNumber value={displayMri} />
                  </span>
                </RadialGauge>
              </div>

              <div>
                <span className="text-xs text-[var(--text-secondary)] font-bold uppercase tracking-widest block mb-1">MRI Score</span>
                <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-[var(--bg-base)] text-sm font-semibold border border-white/5 shadow-inner transition-colors duration-500">
                  <span className="w-2 h-2 rounded-full shadow-[0_0_8px_currentColor] transition-colors duration-500" style={{ backgroundColor: getRiskColor(displayRiskBand), color: getRiskColor(displayRiskBand) }}></span>
                  {displayRiskBand} Risk
                </div>
              </div>
            </div>
          </div>
        </div>
        
        {/* Navigation Tabs */}
        <div className="flex gap-4 px-2 mt-6 relative border-b border-[var(--border-subtle)] overflow-x-auto custom-scrollbar whitespace-nowrap">
          {['overview', 'alerts', 'livestock', 'grid'].map(tab => (
            <button 
              key={tab}
              className={`pb-3 text-sm font-semibold transition-colors border-b-2 relative -bottom-[1px] ${
                activeTab === tab 
                  ? 'border-[var(--color-accent)] text-white' 
                  : 'border-transparent text-[var(--text-secondary)] hover:text-gray-300'
              }`}
              onClick={() => setActiveTab(tab as any)}
            >
              {tab === 'overview' && 'Overview'}
              {tab === 'alerts' && 'Smart Alerts'}
              {tab === 'livestock' && 'Agri/Livestock'}
              {tab === 'grid' && 'EV Grid Shield'}
            </button>
          ))}
        </div>
      </div>

      <div className="p-6 pt-2 flex-1 relative overflow-x-hidden custom-scrollbar">
        {loading && (
          <div className="animate-pulse space-y-4 mt-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="h-24 bg-[var(--bg-card)] rounded-2xl"></div>
              <div className="h-24 bg-[var(--bg-card)] rounded-2xl"></div>
            </div>
            <div className="h-48 bg-[var(--bg-card)] rounded-2xl"></div>
          </div>
        )}
        
        {/* TAB 1: OVERVIEW */}
        {!loading && activeTab === 'overview' && (
          <div className="tab-content-enter-active space-y-4 mt-4">
            
            {/* Stat Tiles Grid */}
            <div className={`grid grid-cols-2 gap-4 ${isSimulating ? 'ring-2 ring-orange-500/50 rounded-2xl' : ''}`}>
              <div className="bg-[var(--bg-card)] rounded-2xl p-4 shadow-sm border border-white/5">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-lg">🌡️</span>
                  <span className="text-xs text-[var(--text-secondary)] font-medium">Ambient Temp</span>
                </div>
                <div className={`text-2xl font-bold tracking-tight ${isSimulating ? 'text-orange-400' : 'text-white'}`}>{displayTemp.toFixed(1)}°C</div>
                <div className="text-[10px] text-[var(--text-secondary)] mt-1">Heat Index: {ward.heat_index}°C</div>
              </div>
              <div className="bg-[var(--bg-card)] rounded-2xl p-4 shadow-sm border border-white/5">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-lg">💧</span>
                  <span className="text-xs text-[var(--text-secondary)] font-medium">Humidity</span>
                </div>
                <div className={`text-2xl font-bold tracking-tight ${isSimulating ? 'text-blue-400' : 'text-white'}`}>{displayRh.toFixed(0)}%</div>
                <div className="text-[10px] text-[var(--text-secondary)] mt-1">Feels highly oppressive</div>
              </div>
            </div>

            {/* What-If Sim Sliders (Prompt Request) */}
            <div className="bg-[var(--bg-card)] rounded-2xl p-5 border border-white/5 shadow-inner">
              <div className="flex justify-between items-center mb-4">
                <h3 className="font-semibold text-white text-sm">Interactive "What-If" Simulation</h3>
                <button 
                  className={`text-[10px] px-2 py-1 rounded font-bold transition-colors ${isSimulating ? 'bg-red-500 text-white' : 'bg-[var(--bg-base)] text-[var(--text-secondary)]'}`}
                  onClick={() => setIsSimulating(!isSimulating)}
                >
                  {isSimulating ? 'SIMULATION ACTIVE' : 'ENABLE'}
                </button>
              </div>
              <div className={`space-y-4 transition-opacity duration-300 ${isSimulating ? 'opacity-100' : 'opacity-30 pointer-events-none'}`}>
                <div>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-[var(--text-secondary)]">Ambient Temperature</span>
                    <span className="font-bold text-orange-400">{displayTemp.toFixed(1)}°C</span>
                  </div>
                  <input type="range" min="20" max="55" step="0.5" 
                    value={displayTemp} onChange={(e) => setSimTemp(parseFloat(e.target.value))}
                    className="w-full h-1.5 bg-[var(--bg-base)] rounded-lg appearance-none cursor-pointer accent-orange-500" />
                </div>
                <div>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-[var(--text-secondary)]">Relative Humidity</span>
                    <span className="font-bold text-blue-400">{displayRh.toFixed(0)}%</span>
                  </div>
                  <input type="range" min="10" max="100" step="1" 
                    value={displayRh} onChange={(e) => setSimRh(parseFloat(e.target.value))}
                    className="w-full h-1.5 bg-[var(--bg-base)] rounded-lg appearance-none cursor-pointer accent-blue-500" />
                </div>
              </div>
            </div>

            {/* Breakdown Chart (Explainability) */}
            <div className="bg-[var(--bg-card)] rounded-3xl shadow-sm p-6 border border-white/5 relative overflow-hidden">
              <div className="flex justify-between items-center mb-6">
                <h3 className="font-semibold text-white flex items-center gap-2 text-sm">
                  Why this score?
                  <div className="group relative cursor-help">
                    <svg className="w-4 h-4 text-[var(--text-secondary)] hover:text-white transition-colors" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd"></path></svg>
                    <div className="absolute left-1/2 -translate-x-1/2 bottom-full mb-2 hidden group-hover:block w-64 p-3 bg-black text-white text-xs rounded-xl shadow-2xl z-50 border border-white/10">
                      The Mortality Risk Index (MRI) combines a physiological heat-stress index (WBGT/Heat Index) with local vulnerability data.
                    </div>
                  </div>
                </h3>
              </div>
              
              <p className="text-xs text-[var(--text-secondary)] mb-6 leading-relaxed bg-[var(--bg-base)] p-4 rounded-2xl border border-white/5">
                {(() => {
                  if (!ward.breakdown) return "Data unavailable.";
                  const factors = Object.entries(ward.breakdown).filter(([k]) => k !== 'thermal_stress');
                  const sortedPos = factors.filter(([,v]) => v > 0).sort((a,b) => b[1] - a[1]);
                  const sortedNeg = factors.filter(([,v]) => v < 0).sort((a,b) => a[1] - b[1]);
                  
                  let text = `This zone's risk is primarily driven by physiological thermal stress (${ward.temp_c}°C, ${ward.rh_pct}% humidity). `;
                  if (sortedPos.length > 0) {
                      text += `The danger is amplified by local vulnerabilities, particularly ${sortedPos[0][0].replace(/_/g, ' ')} `;
                      if (sortedPos.length > 1) text += `and ${sortedPos[1][0].replace(/_/g, ' ')}. `;
                      else text += `. `;
                  }
                  if (sortedNeg.length > 0) {
                      text += `However, this is partially offset by protective infrastructure like ${sortedNeg[0][0].replace(/_/g, ' ')}.`;
                  }
                  return text;
                })()}
              </p>
              
              <div className="mb-2">
                <div className="text-[10px] font-semibold text-[var(--text-secondary)] uppercase mb-3 tracking-widest">Risk Contribution Breakdown</div>
                {ward.breakdown && (() => {
                  const posFactors = Object.entries(ward.breakdown).filter(([,v]) => v > 0).sort((a,b) => b[1] - a[1]);
                  const negFactors = Object.entries(ward.breakdown).filter(([,v]) => v < 0).sort((a,b) => Math.abs(b[1]) - Math.abs(a[1]));
                  const totalPos = posFactors.reduce((sum, [,v]) => sum + v, 0);
                  
                  // Unified accent color for sparkline look
                  const accentColor = 'var(--color-accent)';
                  
                  return (
                    <div className="space-y-5">
                      <div>
                        <div className="flex w-full h-1.5 rounded-full overflow-hidden bg-[var(--bg-base)] shadow-inner">
                          {posFactors.map(([k, v], i) => {
                            const pct = Math.max((v / totalPos) * 100, 2);
                            const opacity = Math.max(1 - (i * 0.2), 0.2); // Fade out subsequent bars
                            return (
                              <div key={k} style={{ width: `${pct}%`, backgroundColor: accentColor, opacity }} className="h-full group relative cursor-pointer border-r border-black hover:opacity-100 transition-all">
                                <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 hidden group-hover:block whitespace-nowrap bg-black text-white text-[10px] px-2 py-1 rounded z-10">
                                  {k.replace(/_/g, ' ')}: +{v.toFixed(1)}%
                                </div>
                              </div>
                            )
                          })}
                        </div>
                        <div className="flex flex-col gap-2 mt-4">
                          {posFactors.map(([k, v], i) => (
                            <div key={k} className="flex justify-between items-center text-xs">
                              <span className="text-[var(--text-secondary)]">{k.replace(/_/g, ' ')}</span>
                              <span className="text-white font-medium">+{v.toFixed(1)}%</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  );
                })()}
              </div>
            </div>

            {/* 5-Day Forecast */}
            <div className="bg-[var(--bg-card)] rounded-3xl shadow-sm p-6 border border-white/5 relative overflow-hidden">
              <h3 className="font-semibold text-white mb-6 text-sm">5-Day Thermal Trajectory</h3>
              {forecast.length > 0 ? (
                <div className="h-40 -ml-4">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={forecast} margin={{ top: 5, right: 10, left: -20, bottom: 5 }}>
                      <defs>
                        <linearGradient id="colorWbgt" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="var(--color-accent)" stopOpacity={0.4}/>
                          <stop offset="95%" stopColor="var(--color-accent)" stopOpacity={0}/>
                        </linearGradient>
                      </defs>
                      <XAxis 
                        dataKey="date" 
                        tickFormatter={(val) => new Date(val).toLocaleDateString(undefined, {weekday: 'short'})} 
                        tick={{fontSize: 10, fill: 'var(--text-secondary)'}}
                        axisLine={false}
                        tickLine={false}
                        dy={10}
                      />
                      <YAxis domain={['auto', 'auto']} tick={{fontSize: 10, fill: 'var(--text-secondary)'}} axisLine={false} tickLine={false} dx={-10} />
                      <Tooltip 
                        contentStyle={{borderRadius: '12px', border: '1px solid rgba(255,255,255,0.1)', backgroundColor: 'var(--bg-card)', boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.5)'}}
                        labelFormatter={(val) => new Date(val).toLocaleDateString()}
                        formatter={(val: number) => [`${val}°C`, 'WBGT']}
                        itemStyle={{color: 'var(--color-accent)', fontWeight: 'bold'}}
                      />
                      <Area 
                        type="monotone" 
                        dataKey="wbgt" 
                        stroke="var(--color-accent)" 
                        strokeWidth={2} 
                        fill="url(#colorWbgt)"
                        activeDot={{r: 4, fill: 'var(--bg-card)', stroke: 'var(--color-accent)', strokeWidth: 2}} 
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <div className="text-[var(--text-secondary)] text-xs text-center py-8">No forecast data available.</div>
              )}
            </div>
          </div>
        )}

        {/* TAB 2: SMART ALERTS (Live Terminal) */}
        {!loading && activeTab === 'alerts' && (
          <div className="tab-content-enter-active space-y-4 mt-4 h-full flex flex-col pb-4">
            <div className="bg-[#050505] rounded-xl border border-white/10 flex-1 overflow-hidden flex flex-col font-mono text-[10px] shadow-inner relative">
              <div className="bg-[#16161d] px-3 py-2 border-b border-white/5 flex justify-between items-center shrink-0">
                <span className="text-[var(--color-accent)] font-bold">TERMINAL // LIVE EVENT STREAM</span>
                <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span> ACTIVE</span>
              </div>
              
              <div className="p-3 overflow-y-auto flex-1 space-y-2 flex flex-col-reverse custom-scrollbar">
                {[
                  { time: 'Just now', msg: `Automated SMS dispatched to 4,200 construction workers in ${ward.name}`, type: 'INFO', color: 'text-blue-400' },
                  { time: '2m ago', msg: `Ward ${ward.name} WBGT threshold exceeded (${ward.wbgt}°C). Alerting heavy industry partners.`, type: 'WARN', color: 'text-yellow-400' },
                  { time: '14m ago', msg: `Hospital capacity warning: projected +12% admission spike. IV fluids low.`, type: 'CRIT', color: 'text-red-400' },
                  { time: '1h ago', msg: `Power grid load increasing rapidly due to AC demand. Issuing voluntary reduction request.`, type: 'WARN', color: 'text-yellow-400' },
                  { time: '3h ago', msg: `Data ingestion cycle completed successfully.`, type: 'SYS', color: 'text-gray-400' }
                ].map((log, idx) => (
                  <div key={idx} className="flex gap-3 leading-relaxed hover:bg-white/5 p-1 rounded transition-colors">
                    <span className="text-[var(--text-secondary)] shrink-0 w-16">[{log.time}]</span>
                    <span className={`${log.color} font-bold shrink-0 w-10`}>{log.type}</span>
                    <span className="text-gray-300">{log.msg}</span>
                  </div>
                ))}
              </div>
              <div className="absolute bottom-0 left-0 w-full h-8 bg-gradient-to-t from-[#050505] to-transparent pointer-events-none"></div>
            </div>
            
            <div className="bg-[var(--bg-card)] rounded-xl p-4 border border-white/5 text-xs text-[var(--text-secondary)]">
              This feed demonstrates the automated audience-specific dispatch logic. In production, these messages are sent via Twilio to registered community leaders, hospitals, and infrastructure managers.
            </div>
          </div>
        )}

        {/* TAB 3: AGRI / LIVESTOCK */}
        {!loading && activeTab === 'livestock' && (
          <div className="tab-content-enter-active mt-4">
            <div className="bg-[var(--bg-card)] rounded-3xl shadow-sm p-6 border border-white/5 relative overflow-hidden">
              <div className="inline-flex items-center justify-center w-12 h-12 bg-green-500/10 text-green-500 rounded-2xl mb-4 ring-1 ring-green-500/30">
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 6l3 1m0 0l-3 9a5.002 5.002 0 006.001 0M6 7l3 9M6 7l6-2m6 2l3-1m-3 1l-3 9a5.002 5.002 0 006.001 0M18 7l3 9m-3-9l-6-2m0-2v2m0 16V5m0 16H9m3 0h3"></path></svg>
              </div>
              <h3 className="text-lg font-bold text-white mb-1">Farm & Animal Protection</h3>
              <p className="text-[var(--text-secondary)] text-xs mb-6 leading-relaxed">
                Automatically computing Temperature-Humidity Index (THI) to text farmers when dairy cattle are at risk, and triggering proactive irrigation alerts before multi-day heat waves.
              </p>

              <div className="space-y-4">
                <div className="bg-[var(--bg-base)] p-4 rounded-2xl border border-white/5">
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-[var(--text-secondary)] font-medium text-xs">Dairy Cattle THI</span>
                    <span className={`text-xs font-bold px-2 py-0.5 rounded ${displayRh > 60 && displayTemp > 35 ? 'bg-red-500/20 text-red-400' : 'bg-yellow-500/20 text-yellow-400'}`}>
                      {displayRh > 60 && displayTemp > 35 ? 'SEVERE STRESS' : 'MODERATE STRESS'}
                    </span>
                  </div>
                  <div className="text-2xl font-black text-white">
                    {Math.round((1.8 * displayTemp + 32) - ((0.55 - 0.0055 * displayRh) * (1.8 * displayTemp - 26)))}
                  </div>
                  <div className="text-[10px] text-[var(--text-secondary)] mt-2">
                    Current THI exceeds dairy safety threshold (72). Milk yield reduction projected. SMS alert queued for local cooperatives.
                  </div>
                </div>

                <div className="bg-[var(--bg-base)] p-4 rounded-2xl border border-white/5">
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-[var(--text-secondary)] font-medium text-xs">Crop Irrigation Warning</span>
                    <span className="text-xs font-bold px-2 py-0.5 rounded bg-blue-500/20 text-blue-400">
                      ACTIVE
                    </span>
                  </div>
                  <div className="text-[10px] text-[var(--text-secondary)]">
                    Projected 3+ days of consecutive Extreme Heat. Advising pre-emptive watering cycle tonight to prevent soil crusting and thermal root shock.
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 4: EV GRID */}
        {!loading && activeTab === 'grid' && (
          <div className="tab-content-enter-active mt-4">
            <div className="bg-[var(--bg-card)] rounded-3xl shadow-sm p-6 border border-white/5 text-center">
              <div className="inline-flex items-center justify-center w-16 h-16 bg-[var(--color-accent)]/10 text-[var(--color-accent)] rounded-full mb-4 ring-1 ring-[var(--color-accent)]/30">
                <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
              </div>
              <h3 className="text-xl font-bold text-white mb-2">EV Thermal Runaway Prevention</h3>
              <p className="text-[var(--text-secondary)] text-sm mb-6">
                Automated API integration with local EV charging infrastructure to prevent battery overheating.
              </p>

              {evData ? (
                <div className="space-y-4">
                  <div className="bg-[var(--bg-base)] p-4 rounded-2xl flex justify-between items-center border border-white/5">
                    <span className="text-[var(--text-secondary)] font-medium">Ambient Temp</span>
                    <span className="text-xl font-bold text-white">{evData.ambient_temp_c}°C</span>
                  </div>
                  <div className="bg-[var(--bg-base)] p-4 rounded-2xl flex justify-between items-center border border-white/5">
                    <span className="text-[var(--text-secondary)] font-medium">Forecast Peak</span>
                    <span className="text-xl font-bold text-red-400">{evData.forecast_peak_temp_c}°C</span>
                  </div>
                  
                  <div className={`p-5 rounded-2xl text-white mt-6
                    ${evData.recommended_charge_rate_multiplier === 1.0 ? 'bg-green-600/80' : ''}
                    ${evData.recommended_charge_rate_multiplier === 0.85 ? 'bg-yellow-600/80' : ''}
                    ${evData.recommended_charge_rate_multiplier === 0.70 ? 'bg-orange-600/80' : ''}
                    ${evData.recommended_charge_rate_multiplier <= 0.50 ? 'bg-red-600/80' : ''}
                  `}>
                    <div className="text-sm font-medium opacity-90 uppercase tracking-wide mb-1">Recommended Throttle</div>
                    <div className="text-4xl font-black mb-2">
                      {evData.recommended_charge_rate_multiplier * 100}% <span className="text-xl font-medium">Max Speed</span>
                    </div>
                    <div className="text-xs bg-black/30 p-2 rounded-xl inline-block mt-2 font-medium">
                      {evData.reason}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="p-4 bg-red-900/30 text-red-400 rounded-2xl">Unable to connect to EV grid API.</div>
              )}
            </div>
          </div>
        )}

      </div>
    </div>
  );
}
