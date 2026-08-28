import React, { useState } from 'react';
import { registerCitizen, fetchPersonalAlert } from '../api';

export function CitizenRegistration({ currentWardId }: { currentWardId: number | null }) {
  const [formData, setFormData] = useState({
    phone_or_id: '',
    age: 30,
    is_pregnant: false,
    occupation: 'indoor_desk',
    has_comorbidity: false,
    housing_type: 'has_ac'
  });

  const [result, setResult] = useState<any>(null);
  const [alertPreview, setAlertPreview] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentWardId) return;
    setLoading(true);
    try {
      const res = await registerCitizen({ ...formData, ward_id: currentWardId });
      setResult(res);
      setAlertPreview(null);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handlePreview = async () => {
    if (!result?.citizen_id) return;
    try {
      const res = await fetchPersonalAlert(result.citizen_id);
      setAlertPreview(res.sms_preview);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="card-surface  rounded-3xl p-5 border border-subtle shadow-sm flex flex-col h-full overflow-y-auto custom-scrollbar">
      <h3 className="font-bold text-primary text-xs mb-3 uppercase tracking-ui">My Personal Risk Profile</h3>
      
      {!result ? (
        <form onSubmit={handleSubmit} className="flex-1 flex flex-col gap-3 text-xs text-slate-300">
          <div>
            <label className="block mb-1 opacity-70">Phone / ID</label>
            <input required type="text" className="w-full bg-base border border-subtle rounded p-2 text-primary" 
              value={formData.phone_or_id} onChange={e => setFormData({...formData, phone_or_id: e.target.value})} />
          </div>
          
          <div className="flex gap-3">
            <div className="flex-1">
              <label className="block mb-1 opacity-70">Age: {formData.age}</label>
              <input type="range" min="1" max="100" className="w-full accent-cyan-500" 
                value={formData.age} onChange={e => setFormData({...formData, age: parseInt(e.target.value)})} />
            </div>
          </div>

          <div>
            <label className="block mb-1 opacity-70">Occupation</label>
            <select className="w-full bg-base border border-subtle rounded p-2 text-primary"
              value={formData.occupation} onChange={e => setFormData({...formData, occupation: e.target.value})}>
              <option value="indoor_desk">Indoor Desk Work</option>
              <option value="outdoor_labor">Outdoor Labor</option>
              <option value="gig_delivery">Gig / Delivery Worker</option>
              <option value="informal_vendor">Informal Vendor</option>
              <option value="unemployed_home">Home / Unemployed</option>
              <option value="other">Other</option>
            </select>
          </div>

          <div>
            <label className="block mb-1 opacity-70">Housing Cooling Status</label>
            <select className="w-full bg-base border border-subtle rounded p-2 text-primary"
              value={formData.housing_type} onChange={e => setFormData({...formData, housing_type: e.target.value})}>
              <option value="has_ac">Has Air Conditioning</option>
              <option value="fan_only">Fan Only</option>
              <option value="no_cooling">No Cooling Available</option>
            </select>
          </div>

          <div className="flex gap-4 mt-1">
            <label className="flex items-center gap-2 cursor-pointer">
              <input type="checkbox" className="accent-cyan-500" 
                checked={formData.is_pregnant} onChange={e => setFormData({...formData, is_pregnant: e.target.checked})} />
              Pregnant
            </label>
            <label className="flex items-center gap-2 cursor-pointer">
              <input type="checkbox" className="accent-cyan-500" 
                checked={formData.has_comorbidity} onChange={e => setFormData({...formData, has_comorbidity: e.target.checked})} />
              Health Conditions
            </label>
          </div>

          <button disabled={loading || !currentWardId} type="submit" 
            className="mt-auto w-full py-2 bg-cyan-600 hover:bg-cyan-500 text-primary rounded font-bold uppercase tracking-wider text-xs transition-colors disabled:opacity-50">
            {loading ? 'Processing...' : 'Calculate Personal Risk'}
          </button>
        </form>
      ) : (
        <div className="flex-1 flex flex-col gap-4">
          <div className={`p-4 rounded-xl border flex items-center justify-between shadow-inner 
            ${result.assessment.tier === 'Critical' ? 'bg-red-500/10 border-red-500/30' : 
              result.assessment.tier === 'High' ? 'bg-orange-500/10 border-orange-500/30' : 
              result.assessment.tier === 'Moderate' ? 'bg-yellow-500/10 border-yellow-500/30' : 
              'bg-green-500/10 border-green-500/30'}`}>
            <div>
              <div className="text-xs font-bold uppercase tracking-ui opacity-70 mb-1">{result.assessment.tier} Risk</div>
              <div className="text-3xl tabular-data font-black">{result.assessment.personal_risk_score}</div>
            </div>
            <div className="text-right text-xs opacity-70">
              Base Ward Index: {result.assessment.base_ward_index}<br/>
              Your Multiplier: x{result.assessment.multiplier_applied}
            </div>
          </div>
          
          <p className="text-xs text-slate-300 leading-relaxed bg-base/50 p-3 rounded border border-subtle">
            {result.assessment.reason}
          </p>
          
          <div className="mt-auto flex flex-col gap-2">
            {alertPreview && (
              <div className="bg-[#050505] border border-subtle p-3 rounded text-xs text-green-400 font-mono">
                {alertPreview}
              </div>
            )}
            <button onClick={handlePreview} className="w-full py-2 border border-slate-700 hover:bg-slate-800 text-primary rounded font-bold uppercase tracking-wider text-xs transition-colors">
              Preview SMS Alert
            </button>
            <button onClick={() => setResult(null)} className="w-full py-2 text-tertiary hover:text-primary uppercase tracking-wider text-xs transition-colors">
              Recalculate
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
