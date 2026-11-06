import React from 'react';
import { Terminal, ShieldCheck, AlertCircle, Info } from 'lucide-react';

interface LogItem {
  id: number;
  level: string;
  stage: string;
  message: string;
  created_at?: string;
}

interface ProductionLogsProps {
  logs: LogItem[];
}

export const ProductionLogs: React.FC<ProductionLogsProps> = ({ logs }) => {
  return (
    <div className="glass-panel rounded-2xl p-6 border border-slate-800 shadow-xl">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-base font-bold text-white flex items-center gap-2">
          <Terminal className="w-4 h-4 text-cyan-400" />
          <span>Autonomous Studio Telemetry & Logs</span>
        </h3>
        <span className="text-[11px] font-mono text-slate-400">Live Agent Feed</span>
      </div>

      <div className="bg-slate-950 rounded-xl p-4 font-mono text-xs max-h-56 overflow-y-auto space-y-2 border border-slate-900">
        {logs.length === 0 ? (
          <p className="text-slate-600 italic">No telemetry events logged yet.</p>
        ) : (
          logs.map(log => {
            const isSuccess = log.level === 'SUCCESS';
            const isError = log.level === 'ERROR';
            const isWarning = log.level === 'WARNING';

            return (
              <div key={log.id} className="flex items-start gap-2.5 leading-relaxed text-slate-300">
                <span className="text-[10px] text-slate-400 select-none">
                  {log.created_at ? log.created_at.split('T')[1]?.slice(0, 8) : '--:--:--'}
                </span>
                <span
                  className={`text-[9px] px-1.5 py-0.2 rounded font-bold uppercase tracking-wider ${
                    isSuccess
                      ? 'bg-emerald-500/20 text-emerald-400'
                      : isError
                      ? 'bg-rose-500/20 text-rose-400'
                      : isWarning
                      ? 'bg-amber-500/20 text-amber-400'
                      : 'bg-slate-800 text-slate-400'
                  }`}
                >
                  {log.level}
                </span>
                <span className="text-[10px] text-cyan-400 font-semibold">[{log.stage}]</span>
                <span className="text-slate-200">{log.message}</span>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
