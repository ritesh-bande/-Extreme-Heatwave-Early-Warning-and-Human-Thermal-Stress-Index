import React, { useState, useEffect } from 'react';
import { submitHospitalFeedback, fetchWardAccuracy } from '../api';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

export function HospitalFeedback({ currentWardId }: { currentWardId: number | null }) {
  const [reportDate, setReportDate] = useState(new Date().toISOString().split('T')[0]);
  const [admissions, setAdmissions] = useState<number>(0);
  const [history, setHistory] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (currentWardId) {
      loadHistory();
    }
  }, [currentWardId]);

  const loadHistory = async () => {
    if (!currentWardId) return;
    try {
      const data = await fetchWardAccuracy(currentWardId);
      // Data format: { date, reported_admissions, predicted_mri }
      setHistory(data.map((d: any) => ({
        date: d.date.substring(5), // Just MM-DD
        'Reported Cases': d.reported_admissions,
        'Forecast MRI': d.predicted_mri
      })));
    } catch (err) {
      console.error(err);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentWardId) return;
    setLoading(true);
    try {
      await submitHospitalFeedback({
        ward_id: currentWardId,
        report_date: reportDate,
        reported_heat_admissions: admissions
      });
      await loadHistory();
      setAdmissions(0);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card-surface  rounded-3xl p-5 border border-subtle shadow-sm flex flex-col h-full overflow-hidden">
      <h3 className="font-bold text-primary text-xs mb-3 uppercase tracking-ui flex items-center gap-2">
        <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse"></span>
        Hospital Reporting
      </h3>

      <form onSubmit={handleSubmit} className="flex gap-2 mb-4 text-xs text-slate-300">
        <input required type="date" className="bg-base border border-subtle rounded p-1.5 text-primary flex-1" 
          value={reportDate} onChange={e => setReportDate(e.target.value)} />
        <input required type="number" min="0" placeholder="Cases" className="bg-base border border-subtle rounded p-1.5 text-primary w-20" 
          value={admissions || ''} onChange={e => setAdmissions(parseInt(e.target.value))} />
        <button disabled={loading || !currentWardId} type="submit" 
          className="px-3 bg-red-900/50 hover:bg-red-800 text-red-200 border border-red-800/50 rounded font-bold uppercase tracking-wider text-xs transition-colors disabled:opacity-50">
          Log
        </button>
      </form>

      <div className="flex-1 w-full relative -ml-4">
        {history.length > 0 ? (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={history} margin={{ top: 5, right: 5, left: 0, bottom: 5 }}>
              <XAxis dataKey="date" axisLine={false} tickLine={false} tick={{ fontSize: 9, fill: '#6B7075' }} dy={10} />
              <YAxis yAxisId="left" axisLine={false} tickLine={false} tick={{ fontSize: 9, fill: '#4C9F70' }} />
              <YAxis yAxisId="right" orientation="right" axisLine={false} tickLine={false} tick={{ fontSize: 9, fill: '#9BA1A6' }} />
              <Tooltip 
                contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #1e293b', borderRadius: '8px', fontSize: '10px' }}
              />
              <Line yAxisId="left" type="monotone" dataKey="Reported Cases" stroke="#4C9F70" strokeWidth={2} dot={{ r: 2 }} />
              <Line yAxisId="right" type="monotone" dataKey="Forecast MRI" stroke="#9BA1A6" strokeWidth={2} dot={false} strokeDasharray="3 3" />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <div className="flex items-center justify-center h-full text-xs text-tertiary">No historical data</div>
        )}
      </div>
      <div className="text-center text-xs text-tertiary mt-2 uppercase tracking-ui">
        Green: Actual Cases | Gray: MRI Forecast
      </div>
    </div>
  );
}
