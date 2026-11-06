import React, { useState, useEffect } from 'react';
import { Play, Pause, Square, Copy, Check, ExternalLink, RefreshCw, Film } from 'lucide-react';

export const App: React.FC = () => {
  const [agentStatus, setAgentStatus] = useState<any>({
    state: 'STOPPED',
    stage: 'IDLE',
    progress: 0,
    current_action: 'Studio ready.',
    settings: {
      publish_destination: 'local',
      running_mode: 'continuous'
    }
  });

  const [videos, setVideos] = useState<any[]>([]);
  const [channels, setChannels] = useState<any>({
    youtube: { connected: false },
    tiktok: { connected: false }
  });
  const [loading, setLoading] = useState(false);
  const [wsConnected, setWsConnected] = useState(false);
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  // Account connection inputs
  const [ytInput, setYtInput] = useState('');
  const [ttInput, setTtInput] = useState('');

  const fetchStatus = async () => {
    try {
      const res = await fetch('/api/agent/status');
      if (res.ok) setAgentStatus(await res.json());
    } catch (e) {
      console.error(e);
    }
  };

  const fetchVideos = async () => {
    try {
      const res = await fetch('/api/videos');
      if (res.ok) setVideos(await res.json());
    } catch (e) {
      console.error(e);
    }
  };

  const fetchChannels = async () => {
    try {
      const res = await fetch('/api/channels');
      if (res.ok) setChannels(await res.json());
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    let ws: WebSocket | null = null;
    let reconnectTimeout: any = null;

    const connectWebSocket = () => {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/ws/events`;
      ws = new WebSocket(wsUrl);

      ws.onopen = () => setWsConnected(true);
      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          if (msg.type === 'INITIAL_STATE' && msg.data) {
            setAgentStatus(msg.data);
          } else if (msg.state) {
            setAgentStatus((prev: any) => ({
              ...prev,
              state: msg.state,
              stage: msg.stage,
              progress: msg.progress ?? prev.progress,
              current_action: msg.current_action ?? prev.current_action
            }));
            if (msg.type === 'VIDEO_COMPLETED') {
              fetchVideos();
              fetchStatus();
            }
          }
        } catch (err) {}
      };

      ws.onclose = () => {
        setWsConnected(false);
        reconnectTimeout = setTimeout(connectWebSocket, 3000);
      };
      ws.onerror = () => ws?.close();
    };

    connectWebSocket();
    fetchStatus();
    fetchVideos();
    fetchChannels();

    const interval = setInterval(() => {
      fetchStatus();
      fetchVideos();
    }, 4000);

    return () => {
      if (ws) ws.close();
      if (reconnectTimeout) clearTimeout(reconnectTimeout);
      clearInterval(interval);
    };
  }, []);

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

  const handleSetDestination = async (dest: string) => {
    await fetch('/api/settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ publish_destination: dest })
    });
    await fetchStatus();
  };

  const handleConnect = async (platform: string, name: string) => {
    if (!name.trim()) return;
    await fetch('/api/channels/connect', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ platform, account_name: name.trim() })
    });
    if (platform === 'youtube') setYtInput('');
    if (platform === 'tiktok') setTtInput('');
    await fetchChannels();
    await fetchStatus();
  };

  const handleDisconnect = async (platform: string) => {
    await fetch(`/api/channels/disconnect?platform=${platform}`, { method: 'POST' });
    await fetchChannels();
    await fetchStatus();
  };

  const copyToClipboard = (text: string, key: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  const isRunning = agentStatus.state === 'RUNNING';
  const isPaused = agentStatus.state === 'PAUSED';
  const currentDest = agentStatus.settings?.publish_destination || 'local';

  return (
    <div className="min-h-screen bg-black text-white selection:bg-white selection:text-black font-sans antialiased">
      {/* Minimal Header */}
      <header className="border-b border-[#1f1f1f] px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="font-mono text-sm tracking-widest font-black uppercase">VIDDY</span>
          <span className="text-xs text-[#666666]">/</span>
          <span className="text-xs text-[#888888] font-medium tracking-tight">Autonomous 24/7 AI Studio</span>
        </div>
        <div className="flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${isRunning ? 'bg-white animate-pulse' : 'bg-[#444444]'}`} />
          <span className="text-xs text-[#888888] font-mono uppercase">{isRunning ? 'Running' : isPaused ? 'Paused' : 'Idle'}</span>
        </div>
      </header>

      {/* Main Container */}
      <main className="max-w-4xl mx-auto px-6 py-10 space-y-12">
        {/* Core Controls */}
        <section className="border border-[#222222] bg-[#0a0a0a] rounded-lg p-6 space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <div className="text-xs font-mono uppercase text-[#777777] mb-1">Status</div>
              <div className="text-2xl font-bold tracking-tight">
                {isRunning ? 'Continuous 24/7 Production Active' : isPaused ? 'Production Paused' : 'Production Stopped'}
              </div>
            </div>

            {/* Actions */}
            <div className="flex items-center gap-2">
              {!isRunning && !isPaused && (
                <button
                  onClick={handleStart}
                  disabled={loading}
                  className="px-5 py-2.5 bg-white text-black font-semibold text-xs rounded hover:bg-[#eaeaea] transition-all cursor-pointer flex items-center gap-2"
                >
                  <Play className="w-3.5 h-3.5 fill-current" />
                  <span>Start Studio</span>
                </button>
              )}

              {isRunning && (
                <>
                  <button
                    onClick={handlePause}
                    disabled={loading}
                    className="px-4 py-2 bg-[#1a1a1a] text-white border border-[#333333] font-semibold text-xs rounded hover:bg-[#252525] transition-all cursor-pointer flex items-center gap-2"
                  >
                    <Pause className="w-3.5 h-3.5" />
                    <span>Pause</span>
                  </button>
                  <button
                    onClick={handleStop}
                    disabled={loading}
                    className="px-4 py-2 bg-transparent text-[#888888] hover:text-white border border-[#262626] hover:border-[#444444] font-semibold text-xs rounded transition-all cursor-pointer flex items-center gap-2"
                  >
                    <Square className="w-3.5 h-3.5 fill-current" />
                    <span>Stop</span>
                  </button>
                </>
              )}

              {isPaused && (
                <>
                  <button
                    onClick={handleResume}
                    disabled={loading}
                    className="px-5 py-2.5 bg-white text-black font-semibold text-xs rounded hover:bg-[#eaeaea] transition-all cursor-pointer flex items-center gap-2"
                  >
                    <Play className="w-3.5 h-3.5 fill-current" />
                    <span>Resume</span>
                  </button>
                  <button
                    onClick={handleStop}
                    disabled={loading}
                    className="px-4 py-2 bg-transparent text-[#888888] hover:text-white border border-[#262626] hover:border-[#444444] font-semibold text-xs rounded transition-all cursor-pointer flex items-center gap-2"
                  >
                    <Square className="w-3.5 h-3.5 fill-current" />
                    <span>Stop</span>
                  </button>
                </>
              )}
            </div>
          </div>

          {/* Real-time Current Action */}
          <div className="pt-4 border-t border-[#1a1a1a] space-y-2">
            <div className="flex items-center justify-between text-xs text-[#888888]">
              <span className="font-mono text-[11px] truncate">{agentStatus.current_action}</span>
              <span className="font-mono">{agentStatus.progress?.toFixed(0) || 0}%</span>
            </div>
            <div className="w-full bg-[#161616] h-1 rounded overflow-hidden">
              <div
                className="bg-white h-full transition-all duration-300"
                style={{ width: `${agentStatus.progress || 0}%` }}
              />
            </div>
          </div>
        </section>

        {/* Publishing Destination */}
        <section className="space-y-4">
          <div className="text-xs font-mono uppercase text-[#777777]">Publishing Destination</div>
          
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
            {[
              { id: 'local', label: 'Local Archive' },
              { id: 'youtube', label: 'YouTube Shorts' },
              { id: 'tiktok', label: 'TikTok' },
              { id: 'both', label: 'Both (YT + TikTok)' }
            ].map(d => (
              <button
                key={d.id}
                onClick={() => handleSetDestination(d.id)}
                className={`py-3 px-4 rounded border text-xs font-medium text-center transition-all cursor-pointer ${
                  currentDest === d.id
                    ? 'bg-white text-black border-white'
                    : 'bg-[#0a0a0a] text-[#888888] border-[#222222] hover:border-[#383838] hover:text-white'
                }`}
              >
                {d.label}
              </button>
            ))}
          </div>

          {/* Minimal Channel Connect Rows */}
          {(currentDest === 'youtube' || currentDest === 'both') && (
            <div className="p-4 bg-[#0a0a0a] border border-[#222222] rounded flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
              <div>
                <span className="font-bold text-white block">YouTube Shorts Channel</span>
                <span className="text-[#777777]">
                  {channels.youtube.connected
                    ? `Connected as @${channels.youtube.account_name}`
                    : 'Connect your channel or videos will be saved locally.'}
                </span>
              </div>
              {channels.youtube.connected ? (
                <button
                  onClick={() => handleDisconnect('youtube')}
                  className="text-[#666666] hover:text-white underline text-xs cursor-pointer self-start sm:self-auto"
                >
                  Disconnect
                </button>
              ) : (
                <div className="flex items-center gap-2">
                  <input
                    type="text"
                    placeholder="Channel / Handle Name"
                    value={ytInput}
                    onChange={(e) => setYtInput(e.target.value)}
                    className="bg-black border border-[#2c2c2c] rounded px-3 py-1.5 text-xs text-white placeholder-[#555] focus:outline-none focus:border-white"
                  />
                  <button
                    onClick={() => handleConnect('youtube', ytInput)}
                    className="px-3 py-1.5 bg-white text-black font-semibold rounded text-xs hover:bg-[#eaeaea] cursor-pointer"
                  >
                    Connect
                  </button>
                </div>
              )}
            </div>
          )}

          {(currentDest === 'tiktok' || currentDest === 'both') && (
            <div className="p-4 bg-[#0a0a0a] border border-[#222222] rounded flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
              <div>
                <span className="font-bold text-white block">TikTok Account</span>
                <span className="text-[#777777]">
                  {channels.tiktok.connected
                    ? `Connected as @${channels.tiktok.account_name}`
                    : 'Connect your TikTok username or videos will be saved locally.'}
                </span>
              </div>
              {channels.tiktok.connected ? (
                <button
                  onClick={() => handleDisconnect('tiktok')}
                  className="text-[#666666] hover:text-white underline text-xs cursor-pointer self-start sm:self-auto"
                >
                  Disconnect
                </button>
              ) : (
                <div className="flex items-center gap-2">
                  <input
                    type="text"
                    placeholder="TikTok Username"
                    value={ttInput}
                    onChange={(e) => setTtInput(e.target.value)}
                    className="bg-black border border-[#2c2c2c] rounded px-3 py-1.5 text-xs text-white placeholder-[#555] focus:outline-none focus:border-white"
                  />
                  <button
                    onClick={() => handleConnect('tiktok', ttInput)}
                    className="px-3 py-1.5 bg-white text-black font-semibold rounded text-xs hover:bg-[#eaeaea] cursor-pointer"
                  >
                    Connect
                  </button>
                </div>
              )}
            </div>
          )}
        </section>

        {/* Video Production Feed */}
        <section className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="text-xs font-mono uppercase text-[#777777]">
              Produced Videos ({videos.length})
            </div>
            <button
              onClick={() => { fetchVideos(); fetchStatus(); }}
              className="text-xs text-[#888888] hover:text-white flex items-center gap-1 cursor-pointer"
            >
              <RefreshCw className="w-3 h-3" />
              <span>Refresh</span>
            </button>
          </div>

          {videos.length === 0 ? (
            <div className="border border-dashed border-[#222222] rounded-lg p-12 text-center text-xs text-[#666666]">
              No videos produced yet. Start the studio above to produce your first video.
            </div>
          ) : (
            <div className="space-y-6">
              {videos.map(video => (
                <article
                  key={video.id}
                  className="border border-[#222222] bg-[#0a0a0a] rounded-lg p-5 space-y-4"
                >
                  {/* Top Bar: Title & Metadata */}
                  <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-2">
                    <div>
                      <span className="text-[10px] font-mono uppercase text-[#777777] block mb-0.5">
                        {video.category || 'Science'} · {video.duration ? `${video.duration.toFixed(1)}s` : '35s'} · QC Passed
                      </span>
                      <h3 className="text-base font-bold text-white">
                        {video.title}
                      </h3>
                    </div>

                    <div className="flex items-center gap-2 shrink-0">
                      {video.youtube_url && (
                        <a
                          href={video.youtube_url}
                          target="_blank"
                          rel="noreferrer"
                          className="px-2.5 py-1 rounded bg-[#161616] hover:bg-[#222222] text-xs font-medium text-white border border-[#2a2a2a] flex items-center gap-1"
                        >
                          <span>YouTube</span>
                          <ExternalLink className="w-3 h-3" />
                        </a>
                      )}
                      {video.tiktok_url && (
                        <a
                          href={video.tiktok_url}
                          target="_blank"
                          rel="noreferrer"
                          className="px-2.5 py-1 rounded bg-[#161616] hover:bg-[#222222] text-xs font-medium text-white border border-[#2a2a2a] flex items-center gap-1"
                        >
                          <span>TikTok</span>
                          <ExternalLink className="w-3 h-3" />
                        </a>
                      )}
                    </div>
                  </div>

                  {/* Embedded Video Player */}
                  {video.video_path && (
                    <div className="bg-black rounded border border-[#1a1a1a] flex justify-center p-2">
                      <video
                        controls
                        className="max-h-80 w-auto rounded"
                        src={`/media/${video.video_path.replace(/\\/g, '/').split('output/')[1] || 'video.mp4'}`}
                      />
                    </div>
                  )}

                  {/* TikTok Pinned Commentary Box */}
                  {video.tiktok_commentary && (
                    <div className="p-3 bg-black border border-[#1f1f1f] rounded space-y-1.5 text-xs">
                      <div className="flex items-center justify-between text-[#888888]">
                        <span className="font-mono text-[11px] uppercase text-white font-medium">
                          TikTok Pinned Comment (Boosts Engagement)
                        </span>
                        <button
                          onClick={() => copyToClipboard(video.tiktok_commentary, `comm-${video.id}`)}
                          className="text-xs hover:text-white flex items-center gap-1 cursor-pointer font-mono"
                        >
                          {copiedKey === `comm-${video.id}` ? (
                            <>
                              <Check className="w-3 h-3 text-white" />
                              <span className="text-white">Copied</span>
                            </>
                          ) : (
                            <>
                              <Copy className="w-3 h-3" />
                              <span>Copy Comment</span>
                            </>
                          )}
                        </button>
                      </div>
                      <p className="text-white text-xs leading-relaxed font-mono select-all">
                        {video.tiktok_commentary}
                      </p>
                    </div>
                  )}

                  {/* TikTok Caption & Viral Reach Hashtags */}
                  {video.tiktok_hashtags && (
                    <div className="p-3 bg-black border border-[#1f1f1f] rounded space-y-1.5 text-xs">
                      <div className="flex items-center justify-between text-[#888888]">
                        <span className="font-mono text-[11px] uppercase text-white font-medium">
                          TikTok Caption & Hashtags
                        </span>
                        <button
                          onClick={() => {
                            const full = `${video.title} 🤯 Science breakdown you didn't know!\n\n${video.tiktok_hashtags}`;
                            copyToClipboard(full, `tags-${video.id}`);
                          }}
                          className="text-xs hover:text-white flex items-center gap-1 cursor-pointer font-mono"
                        >
                          {copiedKey === `tags-${video.id}` ? (
                            <>
                              <Check className="w-3 h-3 text-white" />
                              <span className="text-white">Copied</span>
                            </>
                          ) : (
                            <>
                              <Copy className="w-3 h-3" />
                              <span>Copy Caption & Tags</span>
                            </>
                          )}
                        </button>
                      </div>
                      <p className="text-[#cccccc] text-xs font-mono select-all">
                        {video.title} 🤯 Science breakdown you didn't know!
                        <br />
                        <span className="text-[#888888]">{video.tiktok_hashtags}</span>
                      </p>
                    </div>
                  )}
                </article>
              ))}
            </div>
          )}
        </section>
      </main>
    </div>
  );
};

export default App;
