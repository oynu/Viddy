import React from 'react';
import { Play, Pause, Square, RotateCw, Activity, Film, Share2, CheckCircle2, AlertTriangle } from 'lucide-react';

interface AgentStatusProps {
  state: string;
  stats: {
    total_created: number;
    total_published: number;
    youtube_published: number;
    tiktok_published: number;
    failed_count: number;
    daily_produced: number;
    daily_limit: number;
  };
  onStart: () => void;
  onPause: () => void;
  onResume: () => void;
  onStop: () => void;
  loading: boolean;
}

export const AgentStatusCard: React.FC<AgentStatusProps> = ({
  state,
  stats,
  onStart,
  onPause,
  onResume,
  onStop,
  loading
}) => {
  const isRunning = state === 'RUNNING';
  const isPaused = state === 'PAUSED';
  const isStopped = state === 'STOPPED';

  return (
    <div className="glass-panel rounded-2xl p-6 border border-slate-800 shadow-2xl relative overflow-hidden">
      {/* Background ambient gradient */}
      <div className={`absolute -right-20 -top-20 w-64 h-64 rounded-full blur-3xl opacity-20 pointer-events-none transition-all duration-700 ${
        isRunning ? 'bg-viddy-accent' : isPaused ? 'bg-amber-400' : 'bg-rose-500'
      }`} />

      <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6 relative z-10">
        {/* Status Indicator */}
        <div className="flex items-center gap-4">
          <div className="relative">
            <div className={`w-5 h-5 rounded-full ${
              isRunning ? 'bg-emerald-400' : isPaused ? 'bg-amber-400' : 'bg-rose-500'
            }`} />
            {isRunning && (
              <div className="w-5 h-5 rounded-full bg-emerald-400 absolute inset-0 animate-ping opacity-75" />
            )}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs uppercase tracking-widest font-semibold text-slate-400">Agent Status</span>
              <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider ${
                isRunning ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30' :
                isPaused ? 'bg-amber-500/10 text-amber-400 border border-amber-500/30' :
                'bg-rose-500/10 text-rose-400 border border-rose-500/30'
              }`}>
                {state}
              </span>
            </div>
            <h2 className="text-2xl font-black tracking-tight text-white mt-1">
              {isRunning ? 'Continuous Autonomous Production' : isPaused ? 'Production Suspended' : 'Studio Idle'}
            </h2>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-3">
          {isStopped ? (
            <button
              onClick={onStart}
              disabled={loading}
              className="flex items-center gap-2.5 px-6 py-3 rounded-xl bg-gradient-to-r from-cyan-400 to-blue-500 hover:from-cyan-300 hover:to-blue-400 text-slate-950 font-bold text-sm tracking-wide shadow-lg shadow-cyan-500/25 transition-all active:scale-95 disabled:opacity-50 cursor-pointer"
            >
              <Play className="w-4 h-4 fill-current" />
              <span>Start Agent</span>
            </button>
          ) : isPaused ? (
            <>
              <button
                onClick={onResume}
                disabled={loading}
                className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-sm shadow-lg shadow-emerald-500/20 transition-all active:scale-95 cursor-pointer"
              >
                <RotateCw className="w-4 h-4" />
                <span>Resume</span>
              </button>
              <button
                onClick={onStop}
                disabled={loading}
                className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/30 font-semibold text-sm transition-all active:scale-95 cursor-pointer"
              >
                <Square className="w-4 h-4 fill-current" />
                <span>Stop</span>
              </button>
            </>
          ) : (
            <>
              <button
                onClick={onPause}
                disabled={loading}
                className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-amber-500/10 hover:bg-amber-500/20 text-amber-400 border border-amber-500/30 font-semibold text-sm transition-all active:scale-95 cursor-pointer"
              >
                <Pause className="w-4 h-4 fill-current" />
                <span>Pause</span>
              </button>
              <button
                onClick={onStop}
                disabled={loading}
                className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/30 font-semibold text-sm transition-all active:scale-95 cursor-pointer"
              >
                <Square className="w-4 h-4 fill-current" />
                <span>Stop</span>
              </button>
            </>
          )}
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6 pt-6 border-t border-slate-800/80">
        <div className="bg-slate-900/60 rounded-xl p-3.5 border border-slate-800/60">
          <div className="flex items-center gap-2 text-slate-400 text-xs font-medium">
            <Film className="w-4 h-4 text-cyan-400" />
            <span>Generated</span>
          </div>
          <p className="text-2xl font-black text-white mt-1">{stats.total_created}</p>
        </div>

        <div className="bg-slate-900/60 rounded-xl p-3.5 border border-slate-800/60">
          <div className="flex items-center gap-2 text-slate-400 text-xs font-medium">
            <Share2 className="w-4 h-4 text-emerald-400" />
            <span>Published</span>
          </div>
          <p className="text-2xl font-black text-emerald-400 mt-1">{stats.total_published}</p>
        </div>

        <div className="bg-slate-900/60 rounded-xl p-3.5 border border-slate-800/60">
          <div className="flex items-center gap-2 text-slate-400 text-xs font-medium">
            <Activity className="w-4 h-4 text-purple-400" />
            <span>Daily Quota</span>
          </div>
          <p className="text-2xl font-black text-white mt-1">
            {stats.daily_produced} <span className="text-xs text-slate-500 font-normal">/ {stats.daily_limit}</span>
          </p>
        </div>

        <div className="bg-slate-900/60 rounded-xl p-3.5 border border-slate-800/60">
          <div className="flex items-center gap-2 text-slate-400 text-xs font-medium">
            <AlertTriangle className="w-4 h-4 text-rose-400" />
            <span>QC Retries/Fails</span>
          </div>
          <p className="text-2xl font-black text-slate-300 mt-1">{stats.failed_count}</p>
        </div>
      </div>
    </div>
  );
};
