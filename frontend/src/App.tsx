import React, { useState, useEffect } from 'react';
import { fetchWards, WardData, getCoolingRecommendations } from './api';
import { DashboardMap } from './components/Map';
import { RadialGauge, AnimatedNumber, getRiskColor } from './components/ui-utils';
import { AreaChart, Area, ResponsiveContainer, XAxis, YAxis, Tooltip as RechartsTooltip, LineChart, Line } from 'recharts';
import { CitizenRegistration } from './components/CitizenRegistration';
import { HospitalFeedback } from './components/HospitalFeedback';
import { IVRPlayer } from './components/IVRPlayer';

function App() {
  const [wards, setWards] = useState<WardData[]>([]);
  const [selectedWardId, setSelectedWardId] = useState<number | null>(null);
  const [now, setNow] = useState(new Date());

  const [selectedCity, setSelectedCity] = useState('Nagpur');


  const [mapMetric, setMapMetric] = useState<'mri_score' | 'wbgt' | 'heat_index' | 'utci'>('mri_score');
  const [coolingSites, setCoolingSites] = useState<any[]>([]);
  const [loadingCooling, setLoadingCooling] = useState(false);

  const fetchCoolingSites = async () => {
    setLoadingCooling(true);
    try {
      const data = await getCoolingRecommendations();
      setCoolingSites(data);
    } catch (e) {
      console.error(e);
    }
    setLoadingCooling(false);
  };

  // Simulation State
  const [simTemp, setSimTemp] = useState<number | null>(null);
  const [simRh, setSimRh] = useState<number | null>(null);
  const [isSimulating, setIsSimulating] = useState(false);
  const [previousRiskBand, setPreviousRiskBand] = useState<string>('Green');

  useEffect(() => {
    const loadData = async () => {
      try {
        const data = await fetchWards();
        setWards(data);
      } catch (err) {
        console.error(err);
      }
    };
    
    loadData();
    const interval = setInterval(loadData, 300000);
    const clockInterval = setInterval(() => setNow(new Date()), 30000);
    return () => { clearInterval(interval); clearInterval(clockInterval); };
  }, []);

  useEffect(() => {
    setSimTemp(null);
    setSimRh(null);
    setIsSimulating(false);
  }, [selectedWardId]);

  // Apply blueprint calculation to ALL wards universally
  const processedWards = wards.map(w => {
    const isTarget = w.id === selectedWardId || (!selectedWardId && w.id === wards[0]?.id);
    const temp = (isTarget && isSimulating && simTemp !== null) ? simTemp : w.temp_c;
    const rh = (isTarget && isSimulating && simRh !== null) ? simRh : w.rh_pct;

    // Core Engine: Thermal Stress & Vulnerability Scoring (from Blueprint)
    const baseThermalStress = temp + (0.33 * rh) - 5.33;
    const pctElderly = (w.breakdown?.['pct_elderly'] || 9.4) / 100;
    const pctOutdoorWorkers = (w.breakdown?.['pct_outdoor_workers'] || 9.4) / 100;
    const pctInformalHousing = (w.breakdown?.['pct_informal_housing'] || 6.3) / 100;
    const vulnerabilityMultiplier = 1 + (pctElderly * 1.5) + (pctOutdoorWorkers * 1.2) + (pctInformalHousing * 1.1);
    
    const score = Math.min(100, Math.max(0, baseThermalStress * vulnerabilityMultiplier));
    
    let band = 'Green';
    if (score >= 75) band = 'Red';
    else if (score >= 60) band = 'Yellow';
    else band = 'Green';

    return { ...w, temp_c: temp, rh_pct: rh, mri_score: score, risk_band: band };
  });

  const cityWards = processedWards.filter(w => w.name.includes(selectedCity));
  const rawWard = cityWards.find(w => w.id === selectedWardId) || cityWards[0];
  const currentWard = cityWards.find(w => w.id === (selectedWardId || cityWards[0]?.id)) || null;

  useEffect(() => {
    if (currentWard && currentWard.risk_band === 'Red' && isSimulating) {
       setPreviousRiskBand('Red');
    }
  }, [currentWard?.risk_band, isSimulating]);
  
  const isDangerTransition = isSimulating && currentWard?.risk_band === 'Red';

  const mockHourlyData = [
    { time: '06:00', temp: 32 },
    { time: '09:00', temp: 36 },
    { time: '12:00', temp: 42 },
    { time: '15:00', temp: 44 },
    { time: '18:00', temp: 39 },
    { time: '21:00', temp: 34 }
  ];

  return (
    <div className="flex h-screen bg-base text-slate-100 font-sans overflow-hidden">
      
      {/* City/Ward Selection Sidebar */}
      <aside className="w-80 card-surface  border-r border-subtle flex flex-col h-full z-10 shadow-sm">
        <div className="p-6 border-b border-subtle bg-base/50">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-8 h-8 rounded-full bg-accent flex items-center justify-center text-slate-900 shadow-lg shadow-cyan-500/20">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
            </div>
            <h1 className="font-bold text-primary text-lg tracking-tight uppercase">Command Center</h1>
          </div>
          <div className="flex items-center gap-2 mb-2 bg-surface-raised border border-subtle px-3 py-1.5 rounded-full">
             <span className="w-2 h-2 rounded-full bg-accent animate-pulse"></span>
             <span className="text-xs font-bold text-accent uppercase tracking-ui">IMD Live Stream Active</span>
          </div>
          <p className="text-xs text-secondary uppercase tracking-ui">{cityWards.length} Wards Polled</p>

          <select 
            value={selectedCity} 
            onChange={e => { setSelectedCity(e.target.value); setSelectedWardId(null); }}
            className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-xs text-primary uppercase tracking-ui mt-2 outline-none"
          >
            <option value="Nagpur">Nagpur</option>
            <option value="Chennai">Chennai</option>
            <option value="Ahmedabad">Ahmedabad</option>
          </select>
        </div>

        
        <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-3 custom-scrollbar">
          {wards.length === 0 && <div className="text-center text-tertiary mt-10">Initializing uplink...</div>}
          {[...cityWards].sort((a,b) => (b.mri_score || 0) - (a.mri_score || 0)).map(w => {
            const isSelected = rawWard?.id === w.id;
            return (
              <button 
                key={w.id} 
                onClick={() => setSelectedWardId(w.id)}
                className={`w-full text-left p-4 rounded-xl shrink-0 border transition-all duration-300 ${isSelected ? 'bg-accent/10 border-accent/50 shadow-sm border-accent' : 'card-surface bg-opacity-50 border-subtle hover:bg-slate-800/80 hover:border-slate-700'}`}
              >
                <div className="flex justify-between items-center mb-3">
                  <span className="font-bold text-primary">{w.name}</span>
                  <div className="relative w-8 h-8">
                    <svg className="w-8 h-8 transform -rotate-90">
                      <circle cx="16" cy="16" r="14" fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="3" />
                      <circle cx="16" cy="16" r="14" fill="none" stroke={getRiskColor(w.risk_band)} strokeWidth="3" strokeDasharray="88" strokeDashoffset={88 - ((w.mri_score || 0)/100) * 88} />
                    </svg>
                    <span className="absolute inset-0 flex items-center justify-center text-xs font-bold">{Math.round(w.mri_score || 0)}</span>
                  </div>
                </div>
                
                <div className="flex justify-between items-end">
                  <div className="text-xs text-secondary">
                    <div className="mb-1">{w.temp_c}°C | {w.rh_pct}% RH</div>
                    <div style={{ color: getRiskColor(w.risk_band) }}>{w.risk_band} Risk</div>
                  </div>
                  {/* Mini Sparkline */}
                  <div className="w-16 h-6 opacity-70">
                    <svg viewBox="0 0 100 30" className="w-full h-full" preserveAspectRatio="none">
                      <path 
                        d={`M 0,${25 - (w.id % 5)} Q 20,${30 - (w.id % 10)} 40,${15} T 70,${10} T 100,${5 + (w.id % 8)}`} 
                        fill="none" 
                        stroke={getRiskColor(w.risk_band)} 
                        strokeWidth="3" 
                        strokeLinecap="round" 
                      />
                    </svg>
                  </div>
                </div>

                {isSelected && (
                  <div className="mt-4 pt-3 border-t border-slate-700/50 flex gap-2">
                    <div className="flex-1 bg-base/50 rounded p-2 text-center border border-subtle">
                      <div className="text-[8px] text-tertiary uppercase tracking-ui mb-1">WBGT</div>
                      <div className="text-xs font-bold" style={{ color: getRiskColor(w.temp_c + (w.rh_pct * 0.1) > 32 ? 'Red' : 'Green') }}>
                        {Math.round(w.temp_c + (w.rh_pct * 0.1))}°C
                      </div>
                      <div className="text-[7px] text-slate-600 mt-1 uppercase leading-tight">Outdoor Labor<br/>(ISO 7243)</div>
                    </div>
                    <div className="flex-1 bg-base/50 rounded p-2 text-center border border-subtle">
                      <div className="text-[8px] text-tertiary uppercase tracking-ui mb-1">UTCI</div>
                      <div className="text-xs font-bold" style={{ color: getRiskColor(w.temp_c + 2 > 35 ? 'Yellow' : 'Green') }}>
                        {Math.round(w.temp_c + 2)}°C
                      </div>
                      <div className="text-[7px] text-slate-600 mt-1 uppercase leading-tight">Cross-Climate<br/>Comparison</div>
                    </div>
                    <div className="flex-1 bg-base/50 rounded p-2 text-center border border-subtle">
                      <div className="text-[8px] text-tertiary uppercase tracking-ui mb-1">Heat Index</div>
                      <div className="text-xs font-bold" style={{ color: getRiskColor(w.temp_c + (w.rh_pct * 0.15) > 38 ? 'Orange' : 'Green') }}>
                        {Math.round(w.temp_c + (w.rh_pct * 0.15))}°C
                      </div>
                      <div className="text-[7px] text-slate-600 mt-1 uppercase leading-tight">General Public<br/>SMS Alerts</div>
                    </div>
                  </div>
                )}
              </button>
            )
          })}
        </div>
      </aside>

      {/* Main Content Dashboard */}
      <main className="flex-1 overflow-y-auto p-6 custom-scrollbar bg-base relative">
        {/* Background ambient glow */}
        

        {currentWard ? (
          <div className="grid grid-cols-12 gap-6 relative z-10">
            
            {/* 7. Heatmap (Top) */}
            <div className="col-span-12 card-surface  rounded-3xl p-1 border border-subtle shadow-sm h-[400px] flex flex-col relative overflow-hidden">
              <div className="absolute top-4 left-4 z-10">
                <h3 className="bg-base/80 backdrop-blur px-4 py-2 rounded-full font-bold text-primary text-xs uppercase tracking-ui border border-subtle shadow-sm flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-accent animate-pulse"></span>
                  Live Satellite Telemetry
                </h3>
              </div>
                
              <div className="absolute top-4 right-4 z-10 flex gap-2">
                <button onClick={fetchCoolingSites} disabled={loadingCooling} className="bg-emerald-900/80 hover:bg-emerald-800 backdrop-blur px-4 py-2 rounded-full font-bold text-emerald-100 text-xs uppercase tracking-ui border border-emerald-500/50 shadow-sm transition-colors disabled:opacity-50">
                  {loadingCooling ? 'Calculating...' : 'Recommend New Cooling Sites'}
                </button>
                <select 
                  value={mapMetric} 
                  onChange={e => setMapMetric(e.target.value as any)}
                  className="bg-base/80 backdrop-blur px-4 py-2 rounded-full font-bold text-slate-300 text-xs uppercase tracking-ui border border-subtle shadow-sm outline-none"
                >
                  <option value="mri_score">Layer: MRI Score</option>
                  <option value="wbgt">Layer: WBGT</option>
                  <option value="heat_index">Layer: Heat Index</option>
                  <option value="utci">Layer: UTCI</option>
                </select>
              </div>

              <div className="flex-1 rounded-[1.35rem] overflow-hidden shadow-inner relative bg-black">
                 <DashboardMap 
                    wards={cityWards}
                    selectedCity={selectedCity} 
                    selectedWardId={selectedWardId} 
                    onSelectWard={setSelectedWardId} 
                    colorMetric={mapMetric} 
                    coolingSites={coolingSites}
                 />
              </div>
            </div>
            
            {/* ROW 1 */}
            {/* 3.1 Neighborhood-Level Risk */}
            <div className={`col-span-12 lg:col-span-4 card-surface  rounded-3xl p-6 border ${isDangerTransition ? 'border-red-500/50 animate-risk-flash' : 'border-subtle'} relative overflow-hidden shadow-sm flex flex-col justify-between transition-colors duration-500`}>
              <div 
                className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-64 h-64 rounded-full blur-[80px] opacity-10 transition-colors duration-1000 pointer-events-none" 
                style={{ backgroundColor: getRiskColor(currentWard.risk_band) }}
              ></div>
              
              <div className="relative z-10 flex justify-between items-start mb-2">
                <div>
                  <div className="text-xs font-bold text-secondary uppercase tracking-ui mb-1 flex items-center gap-1.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-accent animate-pulse"></span>
                    MRI Engine
                  </div>
                  <div className="font-bold text-xl text-primary">{currentWard.name}</div>
                </div>
                <div className="flex flex-col items-end gap-2">
                  <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-base/80 text-xs font-bold border border-slate-700 transition-colors duration-500 shadow-lg">
                    <span className="w-2 h-2 rounded-full" style={{ backgroundColor: getRiskColor(currentWard.risk_band) }}></span>
                    {currentWard.risk_band}
                  </div>
                  <div className="text-[8px] text-tertiary bg-base/50 px-2 py-0.5 rounded border border-subtle uppercase tracking-ui text-right">
                    Aligned with NDMA Heat Action Plan protocol
                  </div>
                </div>
              </div>
              <div className="relative z-10 flex items-center justify-center py-4">
                <div className="relative">
                  <RadialGauge value={currentWard.mri_score || 0} color={getRiskColor(currentWard.risk_band)} size={140} strokeWidth={8}>
                    <span className="text-5xl font-black text-primary leading-none drop-shadow-md">
                      <span className="tabular-data"><AnimatedNumber value={currentWard.mri_score || 0} /></span>
                    </span>
                  </RadialGauge>
                </div>
              </div>

              <div className="relative z-10 flex justify-between items-end bg-base/50 p-3 rounded-2xl border border-subtle/50 backdrop-blur-sm">
                <div className="text-center flex-1 border-r border-subtle">
                  <div className="text-xs text-secondary font-semibold uppercase tracking-ui mb-0.5">Temp</div>
                  <div className="text-lg font-bold text-primary transition-all">{currentWard.temp_c.toFixed(1)}°C</div>
                </div>
                <div className="text-center flex-1">
                  <div className="text-xs text-secondary font-semibold uppercase tracking-ui mb-0.5">Humidity</div>
                  <div className="text-lg font-bold text-primary transition-all">{currentWard.rh_pct.toFixed(0)}%</div>
                </div>
              </div>
            </div>

            {/* XAI Explainability Breakdown */}
            <div className="col-span-12 lg:col-span-4 card-surface  rounded-3xl p-6 border border-subtle shadow-sm flex flex-col justify-between">
              <div>
                <div className="flex justify-between items-center mb-6">
                  <h3 className="font-bold text-primary text-sm uppercase tracking-ui">Visual XAI Engine</h3>
                  <svg className="w-4 h-4 text-tertiary" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z"></path></svg>
                </div>
              </div>

              <div className="flex-1 flex flex-col justify-center">
                <div className="text-xs font-semibold text-secondary uppercase mb-4 tracking-ui">Live Risk Multipliers</div>
                {rawWard.breakdown && (() => {
                  // Dynamic multiplier based on live temperature override vs base temperature
                  const tempScale = currentWard.temp_c / rawWard.temp_c; 
                  
                  const posFactors = Object.entries(rawWard.breakdown).filter(([k, v]) => v > 0 && k !== 'thermal_stress').sort((a,b) => b[1] - a[1]);
                  const totalPos = posFactors.reduce((sum, [,v]) => sum + (v * tempScale), 0) || 1;
                  return (
                    <div className="space-y-4">
                      {posFactors.slice(0,3).map(([k, v], i) => {
                        const dynamicV = v * tempScale;
                        return (
                          <div key={k} className="flex flex-col gap-1.5">
                            <div className="flex justify-between items-center text-xs">
                              <span className="text-slate-300 capitalize font-medium">{k.replace(/_/g, ' ')}</span>
                              <span className="text-accent font-bold">+{dynamicV.toFixed(1)}%</span>
                            </div>
                            <div className="w-full h-1.5 rounded-full bg-base overflow-hidden relative border border-subtle">
                               <div 
                                 className="absolute top-0 left-0 h-full bg-accent rounded-full shadow-[0_0_10px_rgba(6,182,212,0.8)] transition-all duration-1000"
                                 style={{ width: `${Math.max((dynamicV / totalPos) * 100, 5)}%` }}
                               ></div>
                            </div>
                          </div>
                        )
                      })}
                    </div>
                  );
                })()}
              </div>
            </div>

            {/* Interactive What-If Simulation */}
            <div className={`col-span-12 lg:col-span-4 card-surface  rounded-3xl p-6 border ${isSimulating ? 'border-accent/30 shadow-[0_0_20px_rgba(6,182,212,0.1)]' : 'border-subtle'} shadow-sm flex flex-col justify-between transition-all duration-500`}>
              <div className="flex justify-between items-center mb-4">
                <h3 className="font-bold text-primary text-sm uppercase tracking-ui">Sim Environment</h3>
                <button 
                  className={`text-xs px-3 py-1.5 rounded-full font-bold transition-all uppercase tracking-ui border ${isSimulating ? 'bg-accent/20 text-accent border-accent/50 shadow-[0_0_15px_rgba(6,182,212,0.4)]' : 'bg-base text-secondary border-slate-700 hover:text-primary'}`}
                  onClick={() => setIsSimulating(!isSimulating)}
                >
                  {isSimulating ? 'Active Override' : 'Enable Override'}
                </button>
              </div>
              <p className="text-xs text-secondary mb-6 leading-relaxed">
                Manually override environmental telemetry. The core AI will instantly recalculate the MRI Risk Level and re-route smart alerts based on the hypothetical scenario.
              </p>
              
              <div className={`space-y-6 transition-all duration-500 ${isSimulating ? 'opacity-100 translate-y-0' : 'opacity-30 pointer-events-none translate-y-2'}`}>
                <div className="bg-base/80 p-4 rounded-2xl border border-subtle shadow-inner">
                  <div className="flex justify-between text-xs mb-3 items-center">
                    <span className="text-secondary font-semibold uppercase tracking-ui text-xs">Ambient Temp</span>
                    <span className="font-bold text-orange-400 text-sm drop-shadow-[0_0_5px_rgba(249,115,22,0.5)]">{currentWard.temp_c.toFixed(1)}°C</span>
                  </div>
                  <input type="range" min="20" max="55" step="0.5" 
                    value={currentWard.temp_c} onChange={(e) => setSimTemp(parseFloat(e.target.value))}
                    className="w-full h-1 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-orange-500" />
                </div>
                <div className="bg-base/80 p-4 rounded-2xl border border-subtle shadow-inner">
                  <div className="flex justify-between text-xs mb-3 items-center">
                    <span className="text-secondary font-semibold uppercase tracking-ui text-xs">Relative Hum</span>
                    <span className="font-bold text-accent text-sm drop-shadow-[0_0_5px_rgba(6,182,212,0.5)]">{currentWard.rh_pct.toFixed(0)}%</span>
                  </div>
                  <input type="range" min="10" max="100" step="1" 
                    value={currentWard.rh_pct} onChange={(e) => setSimRh(parseFloat(e.target.value))}
                    className="w-full h-1 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-cyan-500" />
                </div>
              </div>
            </div>

            {/* ROW 2 */}
            {/* 3.2 Targeted Smart Alerts */}
            <div className="col-span-12 lg:col-span-3 card-surface  rounded-3xl p-5 border border-subtle shadow-sm flex flex-col h-[300px]">
              <div className="flex justify-between items-center mb-3">
                <h3 className="font-bold text-primary text-xs uppercase tracking-ui">Action Routing</h3>
                <span className="flex items-center gap-1.5 text-xs font-bold text-green-400 bg-green-400/10 px-2 py-0.5 rounded-full border border-green-400/20">
                  <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse"></span> ONLINE
                </span>
              </div>
              <div className="bg-[#050505] rounded-xl border border-subtle flex-1 overflow-hidden flex flex-col font-mono text-xs shadow-inner p-4 relative custom-scrollbar">
                <div className="space-y-4 flex flex-col-reverse h-full justify-end">
                  {currentWard.mri_score >= 75 ? (
                    <>
                      <div className="flex gap-3 items-start opacity-100 animate-pulse">
                        <span className="text-red-500 shrink-0 mt-0.5">▶</span>
                        <span className="text-slate-200 leading-relaxed"><b className="text-red-500">HEALTH:</b> CRITICAL: Deploying rapid response to Ward clinics.</span>
                      </div>
                      <div className="flex gap-3 items-start opacity-100">
                        <span className="text-orange-500 shrink-0 mt-0.5">▶</span>
                        <span className="text-slate-200 leading-relaxed"><b className="text-orange-500">LABOR:</b> MANDATORY HALT: All outdoor construction suspended.</span>
                      </div>
                      <div className="flex gap-3 items-start opacity-100">
                        <span className="text-yellow-500 shrink-0 mt-0.5">▶</span>
                        <span className="text-slate-200 leading-relaxed"><b className="text-yellow-500">GRID:</b> EV Throttling at 90% to prevent substation failure.</span>
                      </div>
                    </>
                  ) : currentWard.mri_score >= 60 ? (
                    <>
                      <div className="flex gap-3 items-start opacity-90">
                        <span className="text-yellow-400 shrink-0 mt-0.5">▶</span>
                        <span className="text-slate-300 leading-relaxed"><b className="text-yellow-500">HEALTH:</b> WARNING: Prepare for 15% increase in heat stroke admissions.</span>
                      </div>
                      <div className="flex gap-3 items-start opacity-90">
                        <span className="text-accent shrink-0 mt-0.5">▶</span>
                        <span className="text-slate-300 leading-relaxed"><b className="text-accent">LABOR:</b> ADVISORY: Mandatory shift offsets to pre-10 AM.</span>
                      </div>
                      <div className="flex gap-3 items-start opacity-90">
                        <span className="text-orange-400 shrink-0 mt-0.5">▶</span>
                        <span className="text-slate-300 leading-relaxed"><b className="text-orange-500">GRID:</b> Throttling public EV chargers to 70%.</span>
                      </div>
                    </>
                  ) : (
                    <>
                      <div className="flex gap-3 items-start opacity-60">
                        <span className="text-green-400 shrink-0 mt-0.5">▶</span>
                        <span className="text-secondary leading-relaxed"><b className="text-green-500">SYSTEM:</b> Polling IMD live telemetry API... {wards.length} nodes verified.</span>
                      </div>
                      <div className="flex gap-3 items-start opacity-60">
                        <span className="text-green-400 shrink-0 mt-0.5">▶</span>
                        <span className="text-secondary leading-relaxed"><b className="text-green-500">STATUS:</b> Nominal. Standard hydration breaks advised. Grid stable.</span>
                      </div>
                    </>
                  )}
                </div>
                <div className="absolute bottom-0 left-0 w-full h-12 bg-gradient-to-t from-[#050505] to-transparent pointer-events-none"></div>
              </div>
              <IVRPlayer wardId={currentWard?.id || null} />
            </div>

            {/* Hourly Trajectory - Area Chart */}
            <div className="col-span-12 lg:col-span-3 card-surface  rounded-3xl p-5 border border-subtle shadow-sm flex flex-col h-[300px]">
              <div className="flex justify-between items-center mb-4">
                <h3 className="font-bold text-primary text-xs uppercase tracking-ui">24h Trajectory</h3>
              </div>
              <div className="flex-1 w-full relative -ml-2">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={mockHourlyData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                    <defs>
                      <linearGradient id="colorTemp" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#4C9F70" stopOpacity={0.8}/>
                        <stop offset="95%" stopColor="#15181C" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <XAxis dataKey="time" axisLine={false} tickLine={false} tick={{ fontSize: 9, fill: '#6B7075' }} dy={10} />
                    <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 9, fill: '#6B7075' }} />
                    <RechartsTooltip 
                      contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #1e293b', borderRadius: '8px', fontSize: '10px' }}
                      itemStyle={{ color: '#f97316', fontWeight: 'bold' }}
                    />
                    <Area type="monotone" dataKey="temp" stroke="#4C9F70" strokeWidth={3} fillOpacity={1} fill="url(#colorTemp)" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* 3.3 Farm & Animal Protection */}
            <div className="col-span-12 lg:col-span-3 card-surface  rounded-3xl p-5 border border-subtle shadow-sm flex flex-col h-[300px]">
              <h3 className="font-bold text-primary text-xs mb-3 uppercase tracking-ui">Agri-Shield Protocol</h3>
              <div className="flex-1 flex flex-col gap-3">
                <div className="bg-base/80 p-4 rounded-2xl border border-subtle/50 flex-1 flex flex-col justify-center relative overflow-hidden shadow-inner">
                  <div className="absolute top-0 right-0 p-3 opacity-10">
                    <svg className="w-16 h-16 text-yellow-500" fill="currentColor" viewBox="0 0 24 24"><path d="M12 2L2 12h3v8h14v-8h3L12 2z"/></svg>
                  </div>
                  <div className="flex justify-between items-center mb-2 relative z-10">
                    <span className="text-secondary font-semibold text-xs uppercase tracking-ui">Cattle THI</span>
                    <span className={`text-[8px] font-bold px-2 py-0.5 rounded border ${currentWard.rh_pct > 60 && currentWard.temp_c > 35 ? 'bg-red-500/10 text-accent border-subtle' : 'bg-yellow-500/10 text-yellow-400 border-yellow-500/30'}`}>
                      {currentWard.rh_pct > 60 && currentWard.temp_c > 35 ? 'CRITICAL' : 'ELEVATED'}
                    </span>
                  </div>
                  <div className="text-3xl tabular-data font-black text-primary relative z-10 tracking-tighter">
                    {Math.round((1.8 * currentWard.temp_c + 32) - ((0.55 - 0.0055 * currentWard.rh_pct) * (1.8 * currentWard.temp_c - 26)))}
                  </div>
                  <div className="text-xs text-tertiary mt-2 leading-tight relative z-10">Milk yield reduction detected. Broadcast alert active.</div>
                </div>
                <div className="bg-base/80 p-3 rounded-2xl border border-subtle/50 shadow-inner">
                  <div className="flex justify-between items-center mb-1.5">
                    <span className="text-secondary font-semibold text-xs uppercase tracking-ui">Soil Moisture</span>
                    <span className="text-[8px] font-bold px-2 py-0.5 rounded bg-accent/10 text-accent border border-accent/30">PRE-EMPTIVE IRRIGATION</span>
                  </div>
                  <div className="text-xs text-tertiary leading-tight">Heatwave trajectory active. Watering cycle recommended tonight.</div>
                </div>
              </div>
            </div>

            {/* 3.4 EV Safety */}
            <div className="col-span-12 lg:col-span-3 card-surface  rounded-3xl p-5 border border-subtle shadow-sm flex flex-col h-[300px]">
              <h3 className="font-bold text-primary text-xs mb-3 uppercase tracking-ui">EV Grid Safety</h3>
              <div className="flex-1 flex flex-col justify-center items-center">
                <div className="relative w-36 h-36 flex items-center justify-center mb-4">
                  <svg className="absolute inset-0 w-full h-full transform -rotate-90">
                    <circle cx="72" cy="72" r="64" fill="none" stroke="rgba(255,255,255,0.03)" strokeWidth="8" />
                    <circle 
                      cx="72" cy="72" r="64" fill="none" 
                      stroke={currentWard.mri_score > 60 ? "#ef4444" : "#f97316"} 
                      strokeWidth="8" strokeDasharray="402" 
                      strokeDashoffset={currentWard.mri_score > 60 ? 402 * 0.5 : 402 * 0.3} 
                      strokeLinecap="round" className="transition-all duration-1000" 
                      style={{ filter: 'drop-shadow(0 0 8px currentColor)' }}
                    />
                  </svg>
                  <div className="flex flex-col items-center">
                    <span className="text-3xl tabular-data font-black text-primary tracking-tighter">{currentWard.mri_score > 60 ? '50%' : '70%'}</span>
                    <span className="text-xs font-bold text-secondary uppercase tracking-ui mt-1">Grid Throttle</span>
                  </div>
                </div>
                <div className="bg-orange-500/10 p-3 rounded-xl border border-orange-500/20 text-xs text-orange-200 text-center leading-tight shadow-inner">
                  Public EV chargers API throttled to prevent battery thermal runaway cascade.
                </div>
              </div>
            </div>

            {/* Row 4: New SIH Features */}
            <div className="col-span-12 lg:col-span-4 h-[400px]">
              <CitizenRegistration currentWardId={currentWard?.id || null} />
            </div>
            <div className="col-span-12 lg:col-span-4 h-[400px]">
              <HospitalFeedback currentWardId={currentWard?.id || null} />
            </div>
            
            {/* AC Load Grid Chart */}
            <div className="col-span-12 lg:col-span-4 card-surface  rounded-3xl p-5 border border-subtle shadow-sm flex flex-col h-[400px]">
              <h3 className="font-bold text-primary text-xs mb-3 uppercase tracking-ui flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-orange-500 animate-pulse"></span>
                Power Grid: AC Load Forecast
              </h3>
              <p className="text-xs text-secondary mb-4 uppercase tracking-ui">
                Correlation: 12% load increase per °C above 35°C
              </p>
              <div className="flex-1 w-full relative -ml-2">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={mockHourlyData.map(d => ({ time: d.time, load: Math.max(0, (d.temp - 35) * 12) + 100 }))} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                    <XAxis dataKey="time" axisLine={false} tickLine={false} tick={{ fontSize: 9, fill: '#6B7075' }} dy={10} />
                    <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 9, fill: '#4C9F70' }} domain={['dataMin - 10', 'dataMax + 10']} />
                    <RechartsTooltip 
                      contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #1e293b', borderRadius: '8px', fontSize: '10px' }}
                      itemStyle={{ color: '#f97316', fontWeight: 'bold' }}
                      formatter={(val: number) => [`${val.toFixed(1)} MW`, 'Est. Cooling Load']}
                    />
                    <Line type="monotone" dataKey="load" stroke="#4C9F70" strokeWidth={3} dot={{r: 2, fill: '#4C9F70'}} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>

          </div>
        ) : (
          <div className="flex items-center justify-center h-full text-tertiary text-sm tracking-ui uppercase">
            Initializing telemetry uplink...
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
