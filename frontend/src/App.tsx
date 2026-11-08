import React, { useState, useEffect, useRef } from 'react';
import {
  UploadCloud,
  Check,
  ExternalLink,
  RefreshCw,
  Copy,
  Hash,
  MessageSquareQuote,
  Trash2,
  Sparkles,
  Film,
  ArrowUpRight,
  AlertCircle,
  Loader2,
  Square,
  Play
} from 'lucide-react';

export const App: React.FC = () => {
  const [videos, setVideos] = useState<any[]>([]);
  const [channels, setChannels] = useState<any>({
    youtube: { connected: false },
    tiktok: { connected: false }
  });
  const [queueStatus, setQueueStatus] = useState<any>({
    is_running: false,
    queued_count: 0,
    completed_count: 0,
    failed_count: 0,
    active_item: null
  });

  const [destination, setDestination] = useState<'tiktok' | 'youtube' | 'both'>('tiktok');
  const [autoPublishOnDrop, setAutoPublishOnDrop] = useState<boolean>(true);
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const [notification, setNotification] = useState<string | null>(null);
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  // Platform connect inputs
  const [showChannelsModal, setShowChannelsModal] = useState<boolean>(false);
  const [ytToken, setYtToken] = useState<string>('');
  const [ttCookies, setTtCookies] = useState<string>('');

  const fileInputRef = useRef<HTMLInputElement>(null);

  const showNotification = (msg: string) => {
    setNotification(msg);
    setTimeout(() => setNotification(null), 4000);
  };

  const fetchVideos = async () => {
    try {
      const res = await fetch('/api/videos');
      if (res.ok) setVideos(await res.json());
    } catch (_) {}
  };

  const fetchChannels = async () => {
    try {
      const res = await fetch('/api/channels');
      if (res.ok) setChannels(await res.json());
    } catch (_) {}
  };

  const fetchQueueStatus = async () => {
    try {
      const res = await fetch('/api/queue/status');
      if (res.ok) setQueueStatus(await res.json());
    } catch (_) {}
  };

  useEffect(() => {
    fetchVideos();
    fetchChannels();
    fetchQueueStatus();

    const interval = setInterval(() => {
      fetchVideos();
      fetchQueueStatus();
    }, 3000);

    return () => clearInterval(interval);
  }, []);

  const handleFileUpload = async (fileList: FileList | null) => {
    if (!fileList || fileList.length === 0) return;

    setIsUploading(true);
    showNotification(`Importing ${fileList.length} video(s)... Extracting scripts & crafting viral captions...`);

    const formData = new FormData();
    for (let i = 0; i < fileList.length; i++) {
      formData.append('files', fileList[i]);
    }
    formData.append('destination', destination);
    formData.append('auto_publish', autoPublishOnDrop ? 'true' : 'false');

    try {
      const res = await fetch('/api/videos/upload', {
        method: 'POST',
        body: formData
      });
      const data = await res.json();
      if (data.success) {
        if (autoPublishOnDrop) {
          showNotification(`🚀 ${data.count} video(s) imported & auto-publishing to ${destination.toUpperCase()} now!`);
        } else {
          showNotification(`✓ ${data.count} video(s) ready with viral captions & reach hashtags!`);
        }
        await fetchVideos();
        await fetchQueueStatus();
      } else {
        showNotification(data.message || 'Upload failed.');
      }
    } catch (e: any) {
      showNotification('Error uploading videos: ' + e.message);
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handlePublishAll = async () => {
    try {
      const res = await fetch('/api/queue/publish-all', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ destination })
      });
      const data = await res.json();
      if (data.success) {
        showNotification(`Started auto-publishing ${data.enqueued_count} videos to ${destination.toUpperCase()} via Brave!`);
        await fetchQueueStatus();
        await fetchVideos();
      }
    } catch (e) {
      showNotification('Failed to start publishing queue.');
    }
  };

  const handleStopQueue = async () => {
    try {
      await fetch('/api/queue/stop', { method: 'POST' });
      showNotification('Publishing queue stopped.');
      await fetchQueueStatus();
    } catch (e) {
      showNotification('Failed to stop queue.');
    }
  };

  const handlePublishSingle = async (videoId: number) => {
    try {
      const res = await fetch(`/api/videos/${videoId}/publish`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ destination })
      });
      const data = await res.json();
      if (data.success) {
        showNotification(`Publishing video to ${destination.toUpperCase()} via Brave...`);
        await fetchQueueStatus();
        await fetchVideos();
      }
    } catch (e) {
      showNotification('Failed to publish video.');
    }
  };

  const handleRegenerateMetadata = async (videoId: number) => {
    try {
      showNotification('Generating viral hook, hashtags and comment...');
      const res = await fetch(`/api/videos/${videoId}/auto-metadata`, { method: 'POST' });
      const data = await res.json();
      if (data.success) {
        showNotification('Viral caption & hashtags generated!');
        await fetchVideos();
      }
    } catch (e) {
      showNotification('Failed to generate metadata.');
    }
  };

  const handleDeleteVideo = async (videoId: number) => {
    try {
      const res = await fetch(`/api/videos/${videoId}`, { method: 'DELETE' });
      if (res.ok) {
        setVideos(prev => prev.filter(v => v.id !== videoId));
        showNotification('Video removed from queue.');
      }
    } catch (e) {
      showNotification('Failed to delete video.');
    }
  };

  const handleLaunchBraveTikTok = async () => {
    try {
      showNotification('Launching Brave Browser... Sign in to TikTok Studio to save session.');
      await fetch('/api/channels/tiktok/login-browser', { method: 'POST' });
      const pollTimer = setInterval(async () => {
        try {
          const res = await fetch('/api/channels');
          const data = await res.json();
          if (data?.tiktok?.connected) {
            setChannels(data);
            showNotification('✓ TikTok Brave session connected and verified!');
            clearInterval(pollTimer);
          }
        } catch (_) {}
      }, 3000);
      setTimeout(() => clearInterval(pollTimer), 120000);
    } catch (e) {
      showNotification('Failed to launch Brave browser login.');
    }
  };

  const handleSaveYouTubeToken = async () => {
    if (!ytToken.trim()) return;
    try {
      const res = await fetch('/api/channels/youtube/token', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token_json: ytToken.trim() })
      });
      const data = await res.json();
      if (data.success) {
        showNotification('✓ YouTube Shorts API connected!');
        setYtToken('');
        await fetchChannels();
      } else {
        showNotification(data.error || 'Failed to save token.');
      }
    } catch (e) {
      showNotification('Error saving YouTube token.');
    }
  };

  const handleDisconnect = async (platform: string) => {
    await fetch(`/api/channels/disconnect?platform=${platform}`, { method: 'POST' });
    await fetchChannels();
    showNotification(`Disconnected ${platform}.`);
  };

  const copyToClipboard = (text: string, key: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  const readyVideosCount = videos.filter(v => v.status === 'ready' || v.status === 'queued' || v.status === 'failed').length;

  return (
    <div className="min-h-screen bg-black text-white selection:bg-white selection:text-black font-sans antialiased">
      {/* Toast Notification */}
      {notification && (
        <div className="fixed top-5 right-5 z-50 bg-white text-black px-4 py-2.5 rounded shadow-2xl text-xs font-mono flex items-center gap-2">
          <Check className="w-4 h-4 text-black" />
          <span>{notification}</span>
        </div>
      )}

      {/* Top Header */}
      <header className="border-b border-[#1f1f1f] px-6 py-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <span className="font-mono text-base tracking-widest font-black uppercase">VIDDY</span>
          <span className="text-xs text-[#555] font-mono">/</span>
          <span className="text-xs text-[#999] font-medium tracking-tight">Bulk Video Auto-Publisher</span>
        </div>

        {/* Platform Connection Status Pills */}
        <div className="flex items-center gap-2.5">
          {/* TikTok Pill */}
          <button
            onClick={channels.tiktok?.connected ? () => setShowChannelsModal(true) : handleLaunchBraveTikTok}
            className={`px-3 py-1.5 rounded text-xs font-mono flex items-center gap-1.5 transition-all cursor-pointer border ${
              channels.tiktok?.connected
                ? 'bg-[#111] text-white border-[#333] hover:border-white'
                : 'bg-white text-black font-semibold border-white hover:bg-[#eaeaea]'
            }`}
          >
            <span className={`w-2 h-2 rounded-full ${channels.tiktok?.connected ? 'bg-white' : 'bg-black'}`} />
            <span>{channels.tiktok?.connected ? 'TikTok (Brave Active)' : 'Connect TikTok in Brave'}</span>
          </button>

          {/* YouTube Shorts Pill */}
          <button
            onClick={() => setShowChannelsModal(true)}
            className={`px-3 py-1.5 rounded text-xs font-mono flex items-center gap-1.5 transition-all cursor-pointer border ${
              channels.youtube?.connected
                ? 'bg-[#111] text-white border-[#333] hover:border-white'
                : 'bg-[#161616] text-[#888] border-[#2a2a2a] hover:text-white'
            }`}
          >
            <span className={`w-2 h-2 rounded-full ${channels.youtube?.connected ? 'bg-white' : 'bg-[#555]'}`} />
            <span>{channels.youtube?.connected ? 'YouTube Shorts (Active)' : 'Connect YouTube'}</span>
          </button>
        </div>
      </header>

      {/* Main Studio Container */}
      <main className="max-w-4xl mx-auto px-6 py-10 space-y-10">
        
        {/* Drop & Import Zone */}
        <section
          onDragOver={(e) => {
            e.preventDefault();
            setIsDragging(true);
          }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={(e) => {
            e.preventDefault();
            setIsDragging(false);
            handleFileUpload(e.dataTransfer.files);
          }}
          className={`border-2 border-dashed rounded-xl p-10 text-center transition-all cursor-pointer ${
            isDragging
              ? 'border-white bg-[#141414]'
              : 'border-[#262626] bg-[#0a0a0a] hover:border-[#444] hover:bg-[#0f0f0f]'
          }`}
          onClick={() => fileInputRef.current?.click()}
        >
          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept="video/mp4,video/quicktime,video/webm,video/*"
            className="hidden"
            onChange={(e) => handleFileUpload(e.target.files)}
          />

          <div className="flex flex-col items-center justify-center space-y-3">
            <div className="w-12 h-12 rounded-full bg-[#161616] border border-[#2a2a2a] flex items-center justify-center">
              {isUploading ? (
                <Loader2 className="w-6 h-6 text-white animate-spin" />
              ) : (
                <UploadCloud className="w-6 h-6 text-white" />
              )}
            </div>

            <div>
              <h2 className="text-base font-bold text-white tracking-tight">
                {isUploading ? 'Analyzing scripts & crafting captions...' : 'Drop video files here or click to import'}
              </h2>
              <p className="text-xs text-[#777] mt-1 max-w-md mx-auto">
                Imports multiple videos, transcribes the spoken script, generates viral hooks, reach hashtags, and posts automatically via Brave.
              </p>
            </div>

            {/* Quick Auto-Publish Toggle */}
            <div
              className="inline-flex items-center gap-2 pt-2 text-xs font-mono text-[#aaa]"
              onClick={(e) => e.stopPropagation()}
            >
              <input
                type="checkbox"
                id="autoDropToggle"
                checked={autoPublishOnDrop}
                onChange={(e) => setAutoPublishOnDrop(e.target.checked)}
                className="w-4 h-4 rounded bg-black border-[#444] text-white focus:ring-0 cursor-pointer"
              />
              <label htmlFor="autoDropToggle" className="cursor-pointer select-none">
                ⚡ Auto-publish immediately upon drop (No extra clicks needed)
              </label>
            </div>
          </div>
        </section>

        {/* Batch Queue & Destination Controls */}
        <section className="bg-[#0a0a0a] border border-[#222] rounded-xl p-6 space-y-5">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <span className="text-[10px] font-mono uppercase tracking-widest text-[#777] block">
                Target Platform
              </span>
              <div className="flex items-center gap-2 mt-2">
                {[
                  { id: 'tiktok', label: 'TikTok (via Brave)' },
                  { id: 'youtube', label: 'YouTube Shorts' },
                  { id: 'both', label: 'Both (TikTok + Shorts)' }
                ].map(p => (
                  <button
                    key={p.id}
                    onClick={() => setDestination(p.id as any)}
                    className={`px-3 py-1.5 rounded text-xs font-medium border transition-all cursor-pointer ${
                      destination === p.id
                        ? 'bg-white text-black border-white font-semibold'
                        : 'bg-black text-[#888] border-[#2a2a2a] hover:border-[#444] hover:text-white'
                    }`}
                  >
                    {p.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex items-center gap-2 shrink-0">
              {queueStatus.is_running ? (
                <button
                  onClick={handleStopQueue}
                  className="px-4 py-2 rounded bg-black text-white border border-[#444] hover:border-white text-xs font-semibold flex items-center gap-2 cursor-pointer transition-all"
                >
                  <Square className="w-3.5 h-3.5 fill-current" />
                  <span>Pause Queue</span>
                </button>
              ) : (
                <button
                  onClick={handlePublishAll}
                  disabled={readyVideosCount === 0}
                  className={`px-5 py-2 rounded text-xs font-bold flex items-center gap-2 transition-all cursor-pointer shadow-lg ${
                    readyVideosCount > 0
                      ? 'bg-white text-black hover:bg-[#eaeaea]'
                      : 'bg-[#222] text-[#666] cursor-not-allowed border border-[#333]'
                  }`}
                >
                  <Play className="w-3.5 h-3.5 fill-current" />
                  <span>Auto-Publish All ({readyVideosCount})</span>
                </button>
              )}
            </div>
          </div>

          {/* Active Queue Status Bar */}
          {queueStatus.is_running && queueStatus.active_item && (
            <div className="pt-4 border-t border-[#1a1a1a] flex items-center justify-between text-xs font-mono">
              <div className="flex items-center gap-2 text-white">
                <Loader2 className="w-3.5 h-3.5 animate-spin text-white" />
                <span>
                  Publishing: <strong className="font-bold">{queueStatus.active_item.title}</strong> to{' '}
                  {queueStatus.active_item.destination?.toUpperCase()}...
                </span>
              </div>
              <span className="text-[#888]">
                Remaining: {queueStatus.queued_count} | Done: {queueStatus.completed_count}
              </span>
            </div>
          )}
        </section>

        {/* Video Queue List */}
        <section className="space-y-6">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-mono uppercase tracking-wider text-[#888]">
              Video Publishing Queue ({videos.length})
            </h3>
            {videos.length > 0 && (
              <span className="text-xs text-[#666] font-mono">
                {videos.filter(v => v.status === 'published').length} published · {readyVideosCount} ready
              </span>
            )}
          </div>

          {videos.length === 0 ? (
            <div className="border border-dashed border-[#222] rounded-xl p-12 text-center text-xs text-[#666]">
              No videos in queue. Drag & drop your video files into the box above to get started.
            </div>
          ) : (
            <div className="space-y-6">
              {videos.map(video => (
                <article
                  key={video.id}
                  className="border border-[#222] bg-[#0a0a0a] rounded-xl p-6 space-y-5 transition-all hover:border-[#333]"
                >
                  {/* Top Bar: Title & Status */}
                  <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] font-mono uppercase text-[#777]">
                          {video.duration ? `${video.duration.toFixed(1)}s` : 'Short'} · {video.category || 'Custom'}
                        </span>

                        {/* Status Badge */}
                        <span
                          className={`text-[10px] font-mono px-2 py-0.5 rounded border uppercase ${
                            video.status === 'published'
                              ? 'bg-[#0f2913] text-[#4ade80] border-[#166534]'
                              : video.status === 'publishing'
                              ? 'bg-[#291b0f] text-[#fb923c] border-[#9a3412] animate-pulse'
                              : video.status === 'failed'
                              ? 'bg-[#290f0f] text-[#f87171] border-[#991b1b]'
                              : 'bg-[#161616] text-[#aaa] border-[#333]'
                          }`}
                        >
                          {video.status === 'published'
                            ? 'Published'
                            : video.status === 'publishing'
                            ? 'Publishing via Brave...'
                            : video.status === 'failed'
                            ? 'Upload Failed'
                            : 'Ready to Publish'}
                        </span>
                      </div>

                      <h4 className="text-base font-bold text-white tracking-tight">{video.title}</h4>
                    </div>

                    {/* Action Buttons */}
                    <div className="flex items-center gap-2 shrink-0">
                      {video.status === 'published' ? (
                        <div className="flex items-center gap-2">
                          {video.tiktok_url && (
                            <a
                              href="https://www.tiktok.com/tiktokstudio/manage"
                              target="_blank"
                              rel="noreferrer"
                              className="px-3 py-1.5 rounded bg-white text-black hover:bg-[#eaeaea] text-xs font-semibold flex items-center gap-1.5 transition-all shadow-sm"
                            >
                              <span>TikTok Post</span>
                              <ArrowUpRight className="w-3 h-3 text-black" />
                            </a>
                          )}
                          {video.youtube_url && (
                            <a
                              href={video.youtube_url}
                              target="_blank"
                              rel="noreferrer"
                              className="px-3 py-1.5 rounded bg-[#161616] text-white border border-[#333] hover:border-white text-xs font-medium flex items-center gap-1.5 transition-all"
                            >
                              <span>Shorts Link</span>
                              <ExternalLink className="w-3 h-3" />
                            </a>
                          )}
                        </div>
                      ) : (
                        <button
                          onClick={() => handlePublishSingle(video.id)}
                          disabled={video.status === 'publishing'}
                          className="px-3.5 py-1.5 rounded bg-white text-black hover:bg-[#eaeaea] text-xs font-semibold flex items-center gap-1.5 cursor-pointer transition-all shadow-sm"
                        >
                          <Play className="w-3 h-3 fill-current" />
                          <span>Publish Now</span>
                        </button>
                      )}

                      <button
                        onClick={() => handleRegenerateMetadata(video.id)}
                        title="Regenerate viral caption, hashtags, and discussion comment"
                        className="p-1.5 rounded bg-black border border-[#2a2a2a] hover:border-white text-[#888] hover:text-white transition-all cursor-pointer"
                      >
                        <Sparkles className="w-3.5 h-3.5" />
                      </button>

                      <button
                        onClick={() => handleDeleteVideo(video.id)}
                        title="Remove from queue"
                        className="p-1.5 rounded bg-black border border-[#2a2a2a] hover:border-[#666] text-[#666] hover:text-[#f87171] transition-all cursor-pointer"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>

                  {/* Video Player Preview */}
                  {video.video_path && (
                    <div className="bg-black rounded border border-[#1a1a1a] flex justify-center p-3 relative">
                      <video
                        controls
                        className="max-h-80 w-auto rounded shadow-xl"
                        src={`/media/${video.video_path.replace(/\\/g, '/').split('output/')[1] || 'uploads/video.mp4'}`}
                      />
                    </div>
                  )}

                  {/* Detected / Extracted Script */}
                  {video.script && (
                    <div className="p-3 bg-black border border-[#1a1a1a] rounded text-xs space-y-1">
                      <span className="font-mono text-[10px] uppercase text-[#777] block">
                        Transcribed Spoken Script
                      </span>
                      <p className="text-[#aaa] leading-relaxed text-xs">{video.script}</p>
                    </div>
                  )}

                  {/* Viral Caption & Algorithm Reach Hashtags */}
                  {video.tiktok_hashtags && (
                    <div className="p-3.5 bg-black border border-[#1f1f1f] rounded space-y-2 text-xs">
                      <div className="flex items-center justify-between text-[#888]">
                        <span className="font-mono text-[11px] uppercase text-white font-semibold flex items-center gap-1.5">
                          <Hash className="w-3.5 h-3.5 text-white" />
                          <span>Generated Caption & Viral Reach Hashtags</span>
                        </span>
                        <button
                          onClick={() => {
                            const full = `${video.title}\n\n${video.tiktok_hashtags}`;
                            copyToClipboard(full, `cap-${video.id}`);
                          }}
                          className="text-xs hover:text-white flex items-center gap-1 cursor-pointer font-mono"
                        >
                          {copiedKey === `cap-${video.id}` ? (
                            <>
                              <Check className="w-3 h-3 text-white" />
                              <span className="text-white">Copied</span>
                            </>
                          ) : (
                            <>
                              <Copy className="w-3 h-3" />
                              <span>Copy Caption</span>
                            </>
                          )}
                        </button>
                      </div>
                      <p className="text-[#ccc] text-xs font-mono select-all bg-[#0a0a0a] p-2.5 rounded border border-[#181818]">
                        <span className="text-white font-bold">{video.title}</span>
                        <br /><br />
                        <span className="text-[#888]">{video.tiktok_hashtags}</span>
                      </p>
                    </div>
                  )}

                  {/* Pinned Discussion Commentary */}
                  {video.tiktok_commentary && (
                    <div className="p-3.5 bg-black border border-[#1f1f1f] rounded space-y-2 text-xs">
                      <div className="flex items-center justify-between text-[#888]">
                        <span className="font-mono text-[11px] uppercase text-white font-semibold flex items-center gap-1.5">
                          <MessageSquareQuote className="w-3.5 h-3.5 text-white" />
                          <span>TikTok Pinned Comment (Drives Replies & Retention)</span>
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
                      <p className="text-white text-xs leading-relaxed font-mono select-all bg-[#0a0a0a] p-2.5 rounded border border-[#181818]">
                        {video.tiktok_commentary}
                      </p>
                    </div>
                  )}

                  {/* Failure Details */}
                  {video.error_message && video.status === 'failed' && (
                    <div className="p-3 bg-[#1a0a0a] border border-[#3b1212] rounded text-xs text-[#f87171] flex items-center gap-2">
                      <AlertCircle className="w-4 h-4 shrink-0" />
                      <span>{video.error_message}</span>
                    </div>
                  )}
                </article>
              ))}
            </div>
          )}
        </section>
      </main>

      {/* Platform Channel Connection Modal */}
      {showChannelsModal && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#0f0f0f] border border-[#2a2a2a] rounded-xl max-w-lg w-full p-6 space-y-6 shadow-2xl">
            <div className="flex items-center justify-between border-b border-[#222] pb-4">
              <h3 className="text-sm font-bold tracking-tight text-white font-mono uppercase">
                Platform Channel Accounts
              </h3>
              <button
                onClick={() => setShowChannelsModal(false)}
                className="text-[#666] hover:text-white text-xs font-mono cursor-pointer"
              >
                ✕ Close
              </button>
            </div>

            {/* TikTok Session */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-xs font-bold text-white block">TikTok (Brave Browser Engine)</span>
                  <span className="text-[11px] text-[#777]">
                    {channels.tiktok?.connected
                      ? 'Active session in Brave. Uploads run in the background.'
                      : 'Connect your TikTok account via Brave.'}
                  </span>
                </div>
                {channels.tiktok?.connected ? (
                  <button
                    onClick={() => handleDisconnect('tiktok')}
                    className="text-xs text-[#f87171] hover:underline cursor-pointer"
                  >
                    Disconnect
                  </button>
                ) : null}
              </div>

              <div className="flex gap-2">
                <button
                  onClick={handleLaunchBraveTikTok}
                  className="px-3.5 py-1.5 rounded bg-white text-black text-xs font-semibold hover:bg-[#eaeaea] cursor-pointer flex items-center gap-1.5"
                >
                  <ExternalLink className="w-3.5 h-3.5" />
                  <span>{channels.tiktok?.connected ? 'Re-open Brave Login' : 'Log In via Brave'}</span>
                </button>
              </div>
            </div>

            {/* YouTube Shorts */}
            <div className="space-y-3 pt-4 border-t border-[#222]">
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-xs font-bold text-white block">YouTube Shorts (Google Data API v3)</span>
                  <span className="text-[11px] text-[#777]">
                    {channels.youtube?.connected
                      ? 'OAuth credentials active. Auto-publishes to Shorts shelf.'
                      : 'Paste OAuth JSON or refresh token.'}
                  </span>
                </div>
                {channels.youtube?.connected ? (
                  <button
                    onClick={() => handleDisconnect('youtube')}
                    className="text-xs text-[#f87171] hover:underline cursor-pointer"
                  >
                    Disconnect
                  </button>
                ) : null}
              </div>

              {!channels.youtube?.connected && (
                <div className="space-y-2">
                  <input
                    type="text"
                    placeholder="Paste youtube_token.json content or OAuth credentials..."
                    value={ytToken}
                    onChange={(e) => setYtToken(e.target.value)}
                    className="w-full bg-black border border-[#2c2c2c] rounded px-3 py-1.5 text-xs text-white placeholder-[#555] font-mono focus:outline-none focus:border-white"
                  />
                  <button
                    onClick={handleSaveYouTubeToken}
                    className="px-3.5 py-1.5 rounded bg-white text-black text-xs font-semibold hover:bg-[#eaeaea] cursor-pointer"
                  >
                    Save YouTube Token
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default App;
