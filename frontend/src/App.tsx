import React, { useState, useEffect, useRef } from 'react';
import { Film, Settings as SettingsIcon, Radio, Sparkles, RefreshCw, Cpu } from 'lucide-react';

import { AgentStatusCard } from './components/AgentStatusCard';
import { PublishingSetupCard } from './components/PublishingSetupCard';
import { ProductionPipelineVisualizer } from './components/ProductionPipelineVisualizer';
import { CurrentProductionView } from './components/CurrentProductionView';
import { VideoLibrary } from './components/VideoLibrary';
import { PlatformAccounts } from './components/PlatformAccounts';
import { SettingsModal } from './components/SettingsModal';
import { ProductionLogs } from './components/ProductionLogs';

export const App: React.FC = () => {
  const [agentStatus, setAgentStatus] = useState<any>({
    state: 'STOPPED',
    stage: 'IDLE',
    progress: 0,
    current_action: 'Studio ready.',
    current_job: null,
    stats: {
      total_created: 0,
      total_published: 0,
      youtube_published: 0,
      tiktok_published: 0,
      failed_count: 0,
      daily_produced: 0,
      daily_limit: 24
    },
    settings: {
      running_mode: 'continuous',
      publish_destination: 'local',
      max_daily_videos: 24,
      cycle_delay_seconds: 10,
      default_voice: 'en-US-ChristopherNeural'
    }
  });

  const [videos, setVideos] = useState<any[]>([]);
  const [channels, setChannels] = useState<any>({
    youtube: { connected: false },
    tiktok: { connected: false }
  });
  const [logs, setLogs] = useState<any[]>([]);
  const [showSettings, setShowSettings] = useState(false);
  const [loading, setLoading] = useState(false);
  const [wsConnected, setWsConnected] = useState(false);
  const accountsRef = useRef<HTMLDivElement>(null);

  // Fetch status via REST
  const fetchStatus = async () => {
    try {
      const res = await fetch('/api/agent/status');
      if (res.ok) {
        const data = await res.json();
        setAgentStatus(data);
      }
    } catch (e) {
      console.error('Failed to fetch status:', e);
    }
  };

  const fetchVideos = async () => {
    try {
      const res = await fetch('/api/videos');
      if (res.ok) {
        const data = await res.json();
        setVideos(data);
      }
    } catch (e) {
      console.error('Failed to fetch videos:', e);
    }
  };

  const fetchChannels = async () => {
    try {
      const res = await fetch('/api/channels');
      if (res.ok) {
        const data = await res.json();
        setChannels(data);
      }
    } catch (e) {
      console.error('Failed to fetch channels:', e);
    }
  };

  const fetchLogs = async () => {
    try {
      const res = await fetch('/api/logs');
      if (res.ok) {
        const data = await res.json();
        setLogs(data);
      }
    } catch (e) {
      console.error('Failed to fetch logs:', e);
    }
  };

  // WebSocket live event listener
  useEffect(() => {
    let ws: WebSocket | null = null;
    let reconnectTimeout: any = null;

    const connectWebSocket = () => {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/ws/events`;
      ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        setWsConnected(true);
      };

      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          if (msg.type === 'INITIAL_STATE' && msg.data) {
            setAgentStatus(msg.data);
          } else {
            // Live pipeline state updates
            if (msg.state) {
              setAgentStatus((prev: any) => ({
                ...prev,
                state: msg.state,
                stage: msg.stage,
                progress: msg.progress ?? prev.progress,
                current_action: msg.current_action ?? prev.current_action
              }));
            }
            if (msg.type === 'VIDEO_COMPLETED') {
              fetchVideos();
              fetchStatus();
            }
          }
          fetchLogs();
        } catch (err) {
          console.error('WebSocket parse error:', err);
        }
      };

      ws.onclose = () => {
        setWsConnected(false);
        reconnectTimeout = setTimeout(connectWebSocket, 3000);
      };

      ws.onerror = () => {
        ws?.close();
      };
    };

    connectWebSocket();
    fetchStatus();
    fetchVideos();
    fetchChannels();
    fetchLogs();

    const interval = setInterval(() => {
      fetchStatus();
      fetchLogs();
    }, 4000);

    return () => {
      if (ws) ws.close();
      if (reconnectTimeout) clearTimeout(reconnectTimeout);
      clearInterval(interval);
    };
  }, []);

  // Agent Controls
  const handleStart = async () => {
    setLoading(true);
    await fetch('/api/agent/start', { method: 'POST' });
    await fetchStatus();
    setLoading(false);
  };

  const handlePause = async () => {
    setLoading(true);
    await fetch('/api/agent/pause', { method: 'POST' });
    await fetchStatus();
    setLoading(false);
  };

  const handleResume = async () => {
    setLoading(true);
    await fetch('/api/agent/resume', { method: 'POST' });
    await fetchStatus();
    setLoading(false);
  };

  const handleStop = async () => {
    setLoading(true);
    await fetch('/api/agent/stop', { method: 'POST' });
    await fetchStatus();
    setLoading(false);
  };

  const handleSaveSettings = async (newSettings: any) => {
    await fetch('/api/settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(newSettings)
    });
    await fetchStatus();
  };

  const handleSelectDestination = async (destination: string) => {
    await handleSaveSettings({ publish_destination: destination });
  };

  const handleOpenAccountSetup = (platform: string) => {
    accountsRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleConnectChannel = async (platform: string, accountName: string) => {
    await fetch('/api/channels/connect', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ platform, account_name: accountName })
    });
    await fetchChannels();
    await fetchStatus();
  };

  return (
    <div className="min-h-screen bg-[#080B11] text-slate-100 flex flex-col selection:bg-cyan-400 selection:text-slate-950">
      {/* Header Bar */}
      <header className="border-b border-slate-800/80 bg-slate-950/70 backdrop-blur-xl sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-400 to-blue-600 flex items-center justify-center text-slate-950 font-black text-xl shadow-lg shadow-cyan-500/20">
              <Film className="w-5 h-5 fill-current" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-lg font-black tracking-tight text-white">VIDDY</h1>
                <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-cyan-500/20 text-cyan-400 border border-cyan-500/30">
                  AUTONOMOUS AI STUDIO
                </span>
              </div>
              <p className="text-[11px] text-slate-400 font-medium">Continuous 24/7 Educational Video Engine</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* Live Socket Status */}
            <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-900/80 border border-slate-800 text-xs">
              <span className={`w-2 h-2 rounded-full ${wsConnected ? 'bg-emerald-400 animate-pulse' : 'bg-slate-500'}`} />
              <span className="text-slate-300 font-medium">{wsConnected ? 'Live Real-Time Feed' : 'Connecting...'}</span>
            </div>

            {/* Settings Trigger */}
            <button
              onClick={() => setShowSettings(true)}
              className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-700/80 text-xs font-semibold text-slate-200 transition-all cursor-pointer shadow-sm"
            >
              <SettingsIcon className="w-4 h-4 text-cyan-400" />
              <span>Studio Settings</span>
            </button>
          </div>
        </div>
      </header>

      {/* Main Studio Dashboard */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Top: Publishing Preferences & Channel Wizard */}
        <PublishingSetupCard
          currentDestination={agentStatus.settings?.publish_destination || 'local'}
          channels={channels}
          onSelectDestination={handleSelectDestination}
          onOpenAccountSetup={handleOpenAccountSetup}
        />

        {/* Agent Status & Lifecycle Controls */}
        <AgentStatusCard
          state={agentStatus.state}
          stats={agentStatus.stats}
          onStart={handleStart}
          onPause={handlePause}
          onResume={handleResume}
          onStop={handleStop}
          loading={loading}
        />

        {/* Pipeline Stepper */}
        <ProductionPipelineVisualizer
          currentStage={agentStatus.stage}
          progress={agentStatus.progress}
          currentAction={agentStatus.current_action}
        />

        {/* Active Production View & Accounts */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2">
            <CurrentProductionView
              currentJob={agentStatus.current_job}
              currentStage={agentStatus.stage}
              progress={agentStatus.progress}
            />
          </div>
          <div ref={accountsRef}>
            <PlatformAccounts
              channels={channels}
              onConnect={handleConnectChannel}
            />
          </div>
        </div>

        {/* Video Library */}
        <VideoLibrary
          videos={videos}
          onRefresh={() => { fetchVideos(); fetchStatus(); }}
        />

        {/* Telemetry Logs */}
        <ProductionLogs logs={logs} />
      </main>

      {/* Settings Modal */}
      {showSettings && (
        <SettingsModal
          settings={agentStatus.settings}
          onSave={handleSaveSettings}
          onClose={() => setShowSettings(false)}
        />
      )}

      {/* Footer */}
      <footer className="border-t border-slate-900 bg-slate-950 py-6 text-center text-xs text-slate-500">
        <p>Viddy Autonomous AI Video Studio — Operating 24/7 with zero human intervention required.</p>
      </footer>
    </div>
  );
};

export default App;
