import React from 'react';
import { Sparkles, BookOpen, FileText, Camera, Box, Mic, CheckCircle, UploadCloud } from 'lucide-react';

interface PipelineVisualizerProps {
  currentStage: string;
  progress: number;
  currentAction: string;
}

const STAGES = [
  { id: 'DISCOVER', label: 'Idea Discovery', icon: Sparkles, desc: 'Original concept' },
  { id: 'RESEARCH', label: 'Fact Research', icon: BookOpen, desc: 'Scientific accuracy' },
  { id: 'SCRIPT', label: 'Scriptwriting', icon: FileText, desc: 'Hooks & pacing' },
  { id: 'SCENE_PLAN', label: 'Scene Director', icon: Camera, desc: '3D choreography' },
  { id: 'RENDER_3D', label: 'Low-Poly 3D', icon: Box, desc: 'Blender Python' },
  { id: 'AUDIO_ASSEMBLY', label: 'Voice & Mux', icon: Mic, desc: 'Edge-TTS & FFmpeg' },
  { id: 'QC', label: 'Quality Control', icon: CheckCircle, desc: 'Automated audit' },
  { id: 'PUBLISH', label: 'Publishing', icon: UploadCloud, desc: 'Shorts & TikTok' }
];

export const ProductionPipelineVisualizer: React.FC<PipelineVisualizerProps> = ({
  currentStage,
  progress,
  currentAction
}) => {
  const currentIndex = STAGES.findIndex(s => s.id === currentStage);

  return (
    <div className="glass-panel rounded-2xl p-6 border border-slate-800 shadow-xl">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-6">
        <div>
          <h3 className="text-lg font-bold text-white flex items-center gap-2">
            <span>Autonomous Production Pipeline</span>
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">Continuous hands-off workflow from ideation to release</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="text-right">
            <span className="text-xs text-slate-400 uppercase tracking-wider font-semibold">Stage Progress</span>
            <p className="text-sm font-bold text-cyan-400 font-mono">{progress.toFixed(0)}%</p>
          </div>
          <div className="w-24 h-2 bg-slate-800 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-cyan-400 to-blue-500 rounded-full transition-all duration-500"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      </div>

      {/* Stepper Timeline */}
      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3">
        {STAGES.map((stage, idx) => {
          const Icon = stage.icon;
          const isActive = stage.id === currentStage;
          const isCompleted = currentIndex > idx;
          const isPending = currentIndex < idx;

          return (
            <div
              key={stage.id}
              className={`rounded-xl p-3 border transition-all duration-300 flex flex-col items-center text-center relative ${
                isActive
                  ? 'bg-cyan-950/40 border-cyan-500/60 shadow-lg shadow-cyan-500/10 scale-105 z-10'
                  : isCompleted
                  ? 'bg-slate-900/60 border-emerald-500/30 text-emerald-400'
                  : 'bg-slate-900/30 border-slate-800/60 text-slate-500'
              }`}
            >
              <div
                className={`w-9 h-9 rounded-lg flex items-center justify-center mb-2.5 transition-all ${
                  isActive
                    ? 'bg-cyan-500 text-slate-950 font-bold shadow-md shadow-cyan-500/30 animate-pulse'
                    : isCompleted
                    ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40'
                    : 'bg-slate-800/70 text-slate-400'
                }`}
              >
                <Icon className="w-4 h-4" />
              </div>
              <span className={`text-xs font-bold leading-tight ${isActive ? 'text-white' : isCompleted ? 'text-slate-200' : 'text-slate-400'}`}>
                {stage.label}
              </span>
              <span className="text-[10px] text-slate-400 mt-1 line-clamp-1">{stage.desc}</span>
            </div>
          );
        })}
      </div>

      {/* Current Activity Message */}
      <div className="mt-5 pt-4 border-t border-slate-800/60 flex items-center gap-3 text-xs text-slate-300 bg-slate-950/40 px-4 py-2.5 rounded-xl border border-slate-800/40">
        <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping" />
        <span className="font-semibold text-slate-400">Current Action:</span>
        <span className="text-slate-200 font-mono truncate">{currentAction || 'Awaiting instructions...'}</span>
      </div>
    </div>
  );
};
