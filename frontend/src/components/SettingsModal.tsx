import React, { useState } from 'react';
import { Settings, Save, Sliders, Shield, Zap, Volume2, Globe } from 'lucide-react';

interface SettingsModalProps {
  settings: {
    running_mode: string;
    publish_destination: string;
    max_daily_videos: number;
    cycle_delay_seconds: number;
    default_voice?: string;
  };
  onSave: (newSettings: any) => Promise<void>;
  onClose: () => void;
}

export const SettingsModal: React.FC<SettingsModalProps> = ({ settings, onSave, onClose }) => {
  const [destination, setDestination] = useState(settings.publish_destination || 'local');
  const [maxDaily, setMaxDaily] = useState(settings.max_daily_videos || 24);
  const [delay, setDelay] = useState(settings.cycle_delay_seconds || 10);
  const [voice, setVoice] = useState(settings.default_voice || 'en-US-ChristopherNeural');
  const [saving, setSaving] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    await onSave({
      publish_destination: destination,
      max_daily_videos: Number(maxDaily),
      cycle_delay_seconds: Number(delay),
      default_voice: voice
    });
    setSaving(false);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md">
      <form
        onSubmit={handleSubmit}
        className="glass-panel rounded-2xl p-6 border border-slate-700 max-w-lg w-full shadow-2xl relative"
      >
        <div className="flex items-center justify-between mb-5">
          <div className="flex items-center gap-2.5">
            <span className="p-2 rounded-xl bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
              <Settings className="w-5 h-5" />
            </span>
            <div>
              <h3 className="text-lg font-bold text-white">Production & Publishing Settings</h3>
              <p className="text-xs text-slate-400">Configure autonomous behavior and rate limits</p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="w-8 h-8 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 flex items-center justify-center text-sm font-bold cursor-pointer"
          >
            ✕
          </button>
        </div>

        <div className="space-y-4 text-xs">
          {/* Destination */}
          <div>
            <label className="font-semibold text-slate-300 block mb-1.5 flex items-center gap-1.5">
              <Globe className="w-3.5 h-3.5 text-cyan-400" />
              <span>Default Publishing Destination</span>
            </label>
            <select
              value={destination}
              onChange={e => setDestination(e.target.value)}
              className="w-full px-3 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-white focus:outline-none focus:border-cyan-400"
            >
              <option value="local">Local Storage Archive Only (No Social Upload)</option>
              <option value="youtube">Always YouTube Shorts</option>
              <option value="tiktok">Always TikTok</option>
              <option value="both">Both YouTube Shorts & TikTok Simultaneously</option>
            </select>
          </div>

          {/* Daily limit */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="font-semibold text-slate-300 block mb-1.5 flex items-center gap-1.5">
                <Shield className="w-3.5 h-3.5 text-purple-400" />
                <span>Max Daily Videos</span>
              </label>
              <input
                type="number"
                min="1"
                max="100"
                value={maxDaily}
                onChange={e => setMaxDaily(Number(e.target.value))}
                className="w-full px-3 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-white focus:outline-none focus:border-cyan-400"
              />
            </div>
            <div>
              <label className="font-semibold text-slate-300 block mb-1.5 flex items-center gap-1.5">
                <Zap className="w-3.5 h-3.5 text-amber-400" />
                <span>Delay Between Cycles (s)</span>
              </label>
              <input
                type="number"
                min="1"
                max="3600"
                value={delay}
                onChange={e => setDelay(Number(e.target.value))}
                className="w-full px-3 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-white focus:outline-none focus:border-cyan-400"
              />
            </div>
          </div>

          {/* Voice selection */}
          <div>
            <label className="font-semibold text-slate-300 block mb-1.5 flex items-center gap-1.5">
              <Volume2 className="w-3.5 h-3.5 text-emerald-400" />
              <span>Neural Narration Voice</span>
            </label>
            <select
              value={voice}
              onChange={e => setVoice(e.target.value)}
              className="w-full px-3 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-white focus:outline-none focus:border-cyan-400"
            >
              <option value="en-US-ChristopherNeural">Christopher (Natural Male, Authoritative)</option>
              <option value="en-US-GuyNeural">Guy (Energetic Male, Fast Paced)</option>
              <option value="en-US-JennyNeural">Jenny (Expressive Female, Educational)</option>
              <option value="en-US-AriaNeural">Aria (Cinematic Female, Engaging)</option>
            </select>
          </div>
        </div>

        <div className="flex items-center justify-end gap-3 mt-6 pt-4 border-t border-slate-800">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold cursor-pointer"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={saving}
            className="flex items-center gap-2 px-5 py-2 rounded-xl bg-gradient-to-r from-cyan-400 to-blue-500 hover:from-cyan-300 hover:to-blue-400 text-slate-950 text-xs font-bold shadow-lg shadow-cyan-500/20 cursor-pointer disabled:opacity-50"
          >
            <Save className="w-3.5 h-3.5" />
            <span>{saving ? 'Saving...' : 'Save Settings'}</span>
          </button>
        </div>
      </form>
    </div>
  );
};
