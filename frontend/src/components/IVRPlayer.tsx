import React, { useState } from 'react';
import { fetchIVRScript } from '../api';

export function IVRPlayer({ wardId }: { wardId: number | null }) {
  const [language, setLanguage] = useState('english');
  const [playing, setPlaying] = useState(false);
  const [loading, setLoading] = useState(false);

  const handlePlay = async () => {
    if (!wardId) return;
    setLoading(true);
    try {
      const { script } = await fetchIVRScript(wardId, language);
      
      const utterance = new SpeechSynthesisUtterance(script);
      utterance.lang = language === 'hindi' ? 'hi-IN' : 'en-US';
      
      utterance.onstart = () => setPlaying(true);
      utterance.onend = () => setPlaying(false);
      utterance.onerror = () => setPlaying(false);
      
      window.speechSynthesis.cancel(); // Stop anything playing
      window.speechSynthesis.speak(utterance);
    } catch (e) {
      console.error(e);
      setPlaying(false);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex items-center gap-2 mt-2 pt-2 border-t border-subtle">
      <select 
        value={language} 
        onChange={(e) => setLanguage(e.target.value)}
        className="bg-slate-900 border border-slate-700 rounded px-2 py-1 text-xs text-slate-300 uppercase tracking-ui outline-none"
      >
        <option value="english">English</option>
        <option value="hindi">Hindi</option>
      </select>
      <button 
        disabled={!wardId || playing || loading}
        onClick={handlePlay}
        className="bg-cyan-900/40 hover:bg-cyan-800/60 border border-cyan-700/50 text-cyan-400 px-3 py-1 rounded text-xs uppercase tracking-ui font-bold transition-colors flex items-center gap-1 disabled:opacity-50"
      >
        {playing ? (
          <><span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse"></span> Playing...</>
        ) : loading ? (
          'Loading...'
        ) : (
          '▶ Play IVR Preview'
        )}
      </button>
    </div>
  );
}
