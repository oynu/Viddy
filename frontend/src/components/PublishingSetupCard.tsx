import React from 'react';
import { Youtube, Share2, Globe, HardDrive, CheckCircle2, AlertTriangle, Key } from 'lucide-react';

interface ChannelStatus {
  connected: boolean;
  account_name?: string;
  channel_id?: string;
}

interface PublishingSetupCardProps {
  currentDestination: string;
  channels: {
    youtube: ChannelStatus;
    tiktok: ChannelStatus;
  };
  onSelectDestination: (dest: string) => Promise<void>;
  onOpenAccountSetup: (platform: string) => void;
}

export const PublishingSetupCard: React.FC<PublishingSetupCardProps> = ({
  currentDestination,
  channels,
  onSelectDestination,
  onOpenAccountSetup
}) => {
  const destinations = [
    {
      id: 'both',
      label: 'Both Platforms',
      sublabel: 'YouTube Shorts + TikTok',
      icon: Globe,
      color: 'from-blue-600/30 to-cyan-500/30 border-cyan-500/50 text-cyan-300'
    },
    {
      id: 'youtube',
      label: 'YouTube Shorts',
      sublabel: 'YouTube Data API v3',
      icon: Youtube,
      color: 'from-red-600/30 to-amber-600/30 border-red-500/50 text-red-300'
    },
    {
      id: 'tiktok',
      label: 'TikTok',
      sublabel: 'Content Posting API',
      icon: Share2,
      color: 'from-cyan-600/30 to-emerald-600/30 border-cyan-400/50 text-cyan-200'
    },
    {
      id: 'local',
      label: 'Local Storage Only',
      sublabel: 'Archive to disk (no cloud upload)',
      icon: HardDrive,
      color: 'from-slate-700/30 to-slate-800/30 border-slate-600/50 text-slate-300'
    }
  ];

  const needsYt = (currentDestination === 'youtube' || currentDestination === 'both') && !channels.youtube.connected;
  const needsTt = (currentDestination === 'tiktok' || currentDestination === 'both') && !channels.tiktok.connected;

  return (
    <div className="glass-panel rounded-2xl p-6 border border-slate-800 shadow-xl bg-slate-900/60">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-5">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-lg font-black text-white flex items-center gap-2">
              <span className="text-cyan-400">🎯</span>
              <span>Publishing Destination & Channel Setup</span>
            </h3>
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
              AUTONOMOUS DISPATCH
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Where should Viddy publish every finished video upon passing Quality Control? (Zero manual confirmation required)
          </p>
        </div>

        {/* Account Quick Statuses */}
        <div className="flex items-center gap-2">
          {/* YouTube quick badge */}
          <button
            onClick={() => onOpenAccountSetup('youtube')}
            className={`px-3 py-1.5 rounded-lg border text-xs font-semibold flex items-center gap-2 transition-all cursor-pointer ${
              channels.youtube.connected
                ? 'bg-red-950/40 border-red-500/40 text-red-300'
                : 'bg-slate-900 hover:bg-slate-800 border-slate-700 text-slate-400'
            }`}
          >
            <Youtube className="w-3.5 h-3.5 text-red-500" />
            <span>{channels.youtube.connected ? (channels.youtube.account_name || 'YouTube Connected') : 'Connect YouTube'}</span>
            {channels.youtube.connected && <CheckCircle2 className="w-3 h-3 text-emerald-400" />}
          </button>

          {/* TikTok quick badge */}
          <button
            onClick={() => onOpenAccountSetup('tiktok')}
            className={`px-3 py-1.5 rounded-lg border text-xs font-semibold flex items-center gap-2 transition-all cursor-pointer ${
              channels.tiktok.connected
                ? 'bg-cyan-950/40 border-cyan-500/40 text-cyan-300'
                : 'bg-slate-900 hover:bg-slate-800 border-slate-700 text-slate-400'
            }`}
          >
            <Share2 className="w-3.5 h-3.5 text-cyan-400" />
            <span>{channels.tiktok.connected ? (channels.tiktok.account_name || 'TikTok Connected') : 'Connect TikTok'}</span>
            {channels.tiktok.connected && <CheckCircle2 className="w-3 h-3 text-emerald-400" />}
          </button>
        </div>
      </div>

      {/* 4 Destination Options */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        {destinations.map(dest => {
          const isSelected = (currentDestination || 'local').toLowerCase() === dest.id;
          const IconComponent = dest.icon;
          return (
            <button
              key={dest.id}
              onClick={() => onSelectDestination(dest.id)}
              className={`p-4 rounded-xl border text-left transition-all cursor-pointer flex flex-col justify-between ${
                isSelected
                  ? `bg-gradient-to-br ${dest.color} ring-2 ring-cyan-500/50 shadow-lg shadow-cyan-500/10`
                  : 'bg-slate-950/60 hover:bg-slate-900 border-slate-800 text-slate-400 hover:border-slate-700'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <div className={`p-2 rounded-lg ${isSelected ? 'bg-black/30' : 'bg-slate-900'}`}>
                  <IconComponent className={`w-4 h-4 ${isSelected ? 'text-white' : 'text-slate-400'}`} />
                </div>
                {isSelected && (
                  <span className="flex items-center gap-1 text-[10px] font-bold text-cyan-400 px-1.5 py-0.5 rounded bg-cyan-950/80 border border-cyan-500/40">
                    ACTIVE
                  </span>
                )}
              </div>
              <div>
                <span className={`text-sm font-bold block ${isSelected ? 'text-white' : 'text-slate-200'}`}>
                  {dest.label}
                </span>
                <span className="text-[11px] text-slate-400 block mt-0.5">
                  {dest.sublabel}
                </span>
              </div>
            </button>
          );
        })}
      </div>

      {/* Warning banner if platform destination selected but not connected */}
      {(needsYt || needsTt) && (
        <div className="mt-4 p-3 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-between text-xs text-amber-300">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 shrink-0 text-amber-400" />
            <span>
              {needsYt && needsTt
                ? 'YouTube and TikTok accounts are not linked yet. Connect them above or completed videos will be saved locally in the meantime.'
                : needsYt
                ? 'YouTube Shorts is selected but your channel is not linked yet. Click "Connect YouTube" above.'
                : 'TikTok is selected but your TikTok account is not linked yet. Click "Connect TikTok" above.'}
            </span>
          </div>
          <button
            onClick={() => onOpenAccountSetup(needsTt ? 'tiktok' : 'youtube')}
            className="px-2.5 py-1 rounded bg-amber-500/20 hover:bg-amber-500/30 text-amber-200 font-bold shrink-0 ml-3 cursor-pointer"
          >
            Connect Now
          </button>
        </div>
      )}
    </div>
  );
};
