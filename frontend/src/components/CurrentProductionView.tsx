import React from 'react';
import { Sparkles, Clock, Layers, FileText, CheckCircle2, AlertCircle } from 'lucide-react';

interface CurrentProductionProps {
  currentJob: any;
  currentStage: string;
  progress: number;
}

export const CurrentProductionView: React.FC<CurrentProductionProps> = ({
  currentJob,
  currentStage,
  progress
}) => {
  return (
    <div className="glass-panel rounded-2xl p-6 border border-slate-800 shadow-xl flex flex-col justify-between">
      <div>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <span className="p-1.5 rounded-lg bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
              <Sparkles className="w-4 h-4" />
            </span>
            <h3 className="text-base font-bold text-white">Active Production Job</h3>
          </div>
          <span className="px-2.5 py-0.5 rounded-full text-[11px] font-mono font-semibold bg-slate-800 text-slate-300">
            {currentJob ? `JOB #${currentJob.id}` : 'STANDBY'}
          </span>
        </div>

        {currentJob ? (
          <div className="space-y-4">
            <div className="bg-slate-900/80 rounded-xl p-4 border border-slate-800/80">
              <span className="text-[10px] uppercase font-bold tracking-wider text-cyan-400">Current Phase</span>
              <p className="text-lg font-bold text-white mt-0.5">{currentJob.stage}</p>
              <p className="text-xs text-slate-400 mt-1 line-clamp-2">{currentJob.current_action}</p>
            </div>

            {/* Spec details */}
            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="bg-slate-950/40 p-3 rounded-lg border border-slate-800/40">
                <span className="text-slate-500 block">Resolution</span>
                <span className="font-semibold text-slate-200">1080 × 1920 (9:16)</span>
              </div>
              <div className="bg-slate-950/40 p-3 rounded-lg border border-slate-800/40">
                <span className="text-slate-500 block">Framerate</span>
                <span className="font-semibold text-slate-200">30 FPS H.264</span>
              </div>
              <div className="bg-slate-950/40 p-3 rounded-lg border border-slate-800/40">
                <span className="text-slate-500 block">Subtitles</span>
                <span className="font-semibold text-slate-200">ASS Kinetic Styled</span>
              </div>
              <div className="bg-slate-950/40 p-3 rounded-lg border border-slate-800/40">
                <span className="text-slate-500 block">Voice Engine</span>
                <span className="font-semibold text-slate-200">Neural Edge-TTS</span>
              </div>
            </div>
          </div>
        ) : (
          <div className="py-12 flex flex-col items-center justify-center text-center">
            <div className="w-12 h-12 rounded-2xl bg-slate-800/50 flex items-center justify-center text-slate-500 mb-3">
              <Layers className="w-6 h-6" />
            </div>
            <p className="text-sm font-semibold text-slate-300">No active production job</p>
            <p className="text-xs text-slate-500 mt-1 max-w-xs">
              Press "Start Agent" to kick off the autonomous discovery and rendering loop.
            </p>
          </div>
        )}
      </div>

      <div className="mt-6 pt-4 border-t border-slate-800/60 flex items-center justify-between text-xs text-slate-400">
        <span>Autonomous Loop Mode</span>
        <span className="text-emerald-400 font-semibold flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
          Infinite Chained Production
        </span>
      </div>
    </div>
  );
};
