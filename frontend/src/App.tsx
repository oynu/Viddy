import React, { useState, useEffect, useRef } from 'react';
import {
  UploadCloud,
  Check,
  ExternalLink,
  Copy,
  Hash,
  MessageSquareQuote,
  Trash2,
  Sparkles,
  ArrowUpRight,
  AlertCircle,
  Loader2,
  Play,
  Zap
} from 'lucide-react';
import { LiquidGlassCanvas } from './components/LiquidGlassCanvas';

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

  // Platform connect modal
  const [showChannelsModal, setShowChannelsModal] = useState<boolean>(false);
  const [ytToken, setYtToken] = useState<string>('');

  const fileInputRef = useRef<HTMLInputElement>(null);
  const browserName = channels?.browser?.name || 'Browser';

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
      fetchQueueStatus();
      fetchVideos();
    }, 4000);
    return () => clearInterval(interval);
  }, []);

  const handleFileUpload = async (files: FileList | null) => {
    if (!files || files.length === 0) return;
    setIsUploading(true);
    showNotification(`Importing ${files.length} video(s)...`);

    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
      formData.append('files', files[i]);
    }
    formData.append('destination', destination);
    formData.append('auto_publish', String(autoPublishOnDrop));

    try {
      const res = await fetch('/api/videos/upload', {
        method: 'POST',
        body: formData
      });
      const data = await res.json();
      if (data.success) {
        showNotification(data.message || `Successfully imported ${data.count} videos.`);
        await fetchVideos();
        await fetchQueueStatus();
      } else {
        showNotification(data.error || 'Failed to import videos.');
      }
    } catch (e) {
      showNotification('Error uploading videos.');
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
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
        showNotification(`Publishing video to ${destination.toUpperCase()} via ${browserName}...`);
        await fetchQueueStatus();
        await fetchVideos();
      }
    } catch (e) {
      showNotification('Failed to publish video.');
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
        showNotification(`Publishing ${data.enqueued_count} videos to ${destination.toUpperCase()} via ${browserName}!`);
        await fetchQueueStatus();
        await fetchVideos();
      }
    } catch (e) {
      showNotification('Failed to start publishing.');
    }
  };

  const handleClearAll = async () => {
    try {
      await fetch('/api/videos/clear', { method: 'POST' });
      setVideos([]);
      showNotification('Cleared all videos.');
      await fetchQueueStatus();
    } catch (e) {
      showNotification('Failed to clear videos.');
    }
  };

  const handleDeleteVideo = async (videoId: number) => {
    try {
      const res = await fetch(`/api/videos/${videoId}`, { method: 'DELETE' });
      if (res.ok) {
        setVideos(prev => prev.filter(v => v.id !== videoId));
        showNotification('Video removed.');
      }
    } catch (e) {
      showNotification('Failed to delete video.');
    }
  };

  const handleRegenerateMetadata = async (videoId: number) => {
    try {
      showNotification('Regenerating caption & hashtags...');
      const res = await fetch(`/api/videos/${videoId}/auto-metadata`, { method: 'POST' });
      const data = await res.json();
      if (data.success) {
        showNotification('Caption & hashtags updated!');
        await fetchVideos();
      }
    } catch (e) {
      showNotification('Failed to generate metadata.');
    }
  };

  const handleLaunchBrowserTikTok = async () => {
    try {
      showNotification(`Launching ${browserName}... Sign in to TikTok to save your session.`);
      await fetch('/api/channels/tiktok/login-browser', { method: 'POST' });
      const pollTimer = setInterval(async () => {
        try {
          const res = await fetch('/api/channels');
          const data = await res.json();
          if (data?.tiktok?.connected) {
            setChannels(data);
            showNotification(`✓ TikTok ${browserName} session connected and verified!`);
            clearInterval(pollTimer);
          }
        } catch (_) {}
      }, 3000);
      setTimeout(() => clearInterval(pollTimer), 120000);
    } catch (e) {
      showNotification(`Failed to launch ${browserName} login.`);
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

  const copyToClipboard = (text: string, key: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  const pendingVideos = videos.filter(
    v => v.status === 'ready' || v.status === 'queued' || v.status === 'failed'
  );

  return (
    <div className="min-h-screen text-white selection:bg-purple-500 selection:text-white font-sans antialiased relative overflow-x-hidden pb-24">
      {/* Interactive 3D Liquid Glass & Playful Cursor Canvas */}
      <LiquidGlassCanvas />

      {/* Ambient Deep Purple & White Liquid Glow Spheres */}
      <div className="fixed -top-44 left-1/2 -translate-x-1/2 w-[960px] h-[520px] bg-gradient-to-b from-purple-500/[0.18] via-fuchsia-500/[0.06] to-transparent rounded-full blur-[130px] pointer-events-none -z-10" />
      <div className="fixed top-1/4 -left-40 w-[580px] h-[580px] bg-violet-600/[0.1] rounded-full blur-[130px] pointer-events-none -z-10" />
      <div className="fixed top-1/2 -right-40 w-[580px] h-[580px] bg-purple-500/[0.1] rounded-full blur-[130px] pointer-events-none -z-10" />

      {/* Liquid Glass Toast Notification */}
      {notification && (
        <div className="fixed top-6 right-6 z-50 glass-modal px-4 py-2.5 rounded-full text-xs font-medium flex items-center gap-2.5 shadow-2xl border border-purple-400/35 animate-in fade-in slide-in-from-top-2 duration-200">
          <span className="w-2 h-2 rounded-full bg-purple-400 shadow-[0_0_10px_rgba(192,132,252,1)] animate-pulse" />
          <span className="text-white tracking-tight">{notification}</span>
        </div>
      )}

      {/* Floating Liquid Glass Header Capsule */}
      <div className="sticky top-5 z-40 max-w-4xl mx-auto px-4 w-full relative">
        <header className="glass-panel rounded-2xl px-5 py-3 flex flex-col sm:flex-row sm:items-center justify-between gap-4 transition-all relative overflow-hidden">
          <div className="absolute top-0 left-10 right-10 h-[1px] bg-gradient-to-r from-transparent via-purple-300/60 to-transparent pointer-events-none" />

          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-white via-purple-100 to-purple-400 flex items-center justify-center text-black font-black text-xs shadow-[0_0_20px_rgba(168,85,247,0.5)] border border-white/80">
              V
            </div>
            <div className="flex items-center gap-2.5">
              <span className="font-mono text-sm tracking-widest font-black uppercase bg-gradient-to-r from-white via-purple-100 to-purple-300 bg-clip-text text-transparent">
                VIDDY
              </span>
              <span className="text-xs text-purple-400/40 font-mono">/</span>
              <span className="text-xs text-zinc-300/90 font-medium tracking-tight">
                Auto-Video Publisher
              </span>
            </div>

            {queueStatus?.is_running && (
              <span className="ml-2 px-2.5 py-0.5 rounded-full text-[10px] font-mono bg-purple-500/20 border border-purple-400/40 text-purple-200 flex items-center gap-1.5 animate-pulse">
                <Loader2 className="w-2.5 h-2.5 animate-spin" />
                Queue Active ({queueStatus.queued_count})
              </span>
            )}
          </div>

          {/* Platform Account Badges & Clear */}
          <div className="flex items-center gap-2.5 flex-wrap">
            <button
              onClick={
                channels.tiktok?.connected
                  ? () => setShowChannelsModal(true)
                  : handleLaunchBrowserTikTok
              }
              className={`px-3.5 py-1.5 rounded-full text-xs font-mono flex items-center gap-2 transition-all cursor-pointer ${
                channels.tiktok?.connected
                  ? 'glass-pill text-white border-purple-400/35 hover:border-purple-300/70'
                  : 'liquid-btn-primary font-semibold'
              }`}
            >
              <span
                className={`w-2 h-2 rounded-full ${
                  channels.tiktok?.connected
                    ? 'bg-emerald-400 shadow-[0_0_10px_rgba(52,211,153,0.95)]'
                    : 'bg-purple-700'
                }`}
              />
              <span>
                {channels.tiktok?.connected
                  ? `TikTok (${browserName} Active)`
                  : `Connect TikTok in ${browserName}`}
              </span>
            </button>

            <button
              onClick={() => setShowChannelsModal(true)}
              className={`px-3.5 py-1.5 rounded-full text-xs font-mono flex items-center gap-2 transition-all cursor-pointer glass-pill ${
                channels.youtube?.connected
                  ? 'text-white border-purple-400/35 hover:border-purple-300/70'
                  : 'text-zinc-300 hover:text-white border-white/[0.12]'
              }`}
            >
              <span
                className={`w-2 h-2 rounded-full ${
                  channels.youtube?.connected
                    ? 'bg-emerald-400 shadow-[0_0_10px_rgba(52,211,153,0.95)]'
                    : 'bg-purple-400/50'
                }`}
              />
              <span>
                {channels.youtube?.connected ? 'Shorts API (Active)' : 'Connect YouTube'}
              </span>
            </button>

            {videos.length > 0 && (
              <button
                onClick={handleClearAll}
                title="Clear all videos"
                className="p-2 rounded-full glass-pill hover:border-rose-500/50 text-zinc-300 hover:text-rose-400 transition-all cursor-pointer"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
        </header>
      </div>

      {/* Main Container */}
      <main className="max-w-3xl mx-auto px-6 pt-10 space-y-8 relative z-10">
        {/* Destination Picker Segmented Control */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-purple-400 shadow-[0_0_8px_rgba(192,132,252,0.9)]" />
            <span className="text-xs font-mono uppercase tracking-widest text-purple-200/80 font-semibold">
              Upload Target
            </span>
          </div>

          <div className="p-1 rounded-full glass-panel flex items-center gap-1 shadow-inner">
            {[
              { id: 'tiktok', label: `TikTok (${browserName})` },
              { id: 'youtube', label: 'YouTube Shorts' },
              { id: 'both', label: 'Both' }
            ].map(p => (
              <button
                key={p.id}
                onClick={() => setDestination(p.id as any)}
                className={`px-4 py-1.5 rounded-full text-xs transition-all cursor-pointer ${
                  destination === p.id
                    ? 'glass-pill-active font-semibold shadow-md'
                    : 'text-zinc-300 hover:text-white font-medium hover:bg-purple-500/[0.12]'
                }`}
              >
                {p.label}
              </button>
            ))}
          </div>
        </div>

        {/* Clean, Minimalist Liquid Glass Drop Box */}
        <section
          onDragOver={e => {
            e.preventDefault();
            setIsDragging(true);
          }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={e => {
            e.preventDefault();
            setIsDragging(false);
            handleFileUpload(e.dataTransfer.files);
          }}
          className={`rounded-3xl p-12 text-center transition-all cursor-pointer group relative overflow-hidden glass-dropzone ${
            isDragging ? 'glass-dropzone-dragover' : ''
          }`}
          onClick={() => fileInputRef.current?.click()}
        >
          {/* Top & Bottom Specular Refracting Lines */}
          <div className="absolute top-0 left-1/6 right-1/6 h-[1.5px] bg-gradient-to-r from-transparent via-white/80 to-transparent pointer-events-none group-hover:via-purple-200 transition-all duration-300" />
          <div className="absolute bottom-0 left-1/4 right-1/4 h-[1px] bg-gradient-to-r from-transparent via-purple-400/50 to-transparent pointer-events-none" />

          {/* Ambient Internal Purple Core Glow */}
          <div className="absolute -top-24 left-1/2 -translate-x-1/2 w-80 h-48 bg-purple-500/20 rounded-full blur-3xl pointer-events-none group-hover:bg-purple-500/30 transition-all duration-500" />

          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept="video/mp4,video/quicktime,video/webm,video/x-matroska,video/avi,video/*"
            className="hidden"
            onChange={e => handleFileUpload(e.target.files)}
          />

          <div className="flex flex-col items-center justify-center space-y-5 relative z-10">
            {/* 3D Levitating Liquid Orb Icon */}
            <div className="relative">
              <div className="absolute -inset-2 rounded-3xl bg-gradient-to-tr from-purple-500/40 via-fuchsia-400/20 to-white/30 blur-xl opacity-70 group-hover:opacity-100 transition-opacity duration-300" />
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-b from-white/[0.22] via-purple-500/[0.12] to-black/40 border border-white/[0.35] shadow-[inset_0_1.5px_2px_rgba(255,255,255,0.6),inset_0_-1.5px_2px_rgba(168,85,247,0.4),0_16px_32px_rgba(0,0,0,0.6)] flex items-center justify-center group-hover:scale-105 group-hover:-translate-y-0.5 transition-all duration-300 backdrop-blur-xl relative">
                {isUploading ? (
                  <Loader2 className="w-7 h-7 text-purple-200 animate-spin" />
                ) : (
                  <UploadCloud className="w-7 h-7 text-white drop-shadow-[0_0_12px_rgba(192,132,252,0.8)]" />
                )}
              </div>
            </div>

            <h2 className="text-base font-semibold text-white tracking-tight">
              {isUploading
                ? 'Importing your videos...'
                : 'Drop your videos here or click to import'}
            </h2>

            {/* Custom Liquid Glass Toggle Switch */}
            <div
              className="pt-1"
              onClick={e => {
                e.stopPropagation();
                setAutoPublishOnDrop(!autoPublishOnDrop);
              }}
            >
              <div className="inline-flex items-center gap-3 px-4 py-2 rounded-full glass-pill border-white/20 hover:border-purple-300/50 cursor-pointer select-none">
                <button
                  type="button"
                  role="switch"
                  aria-checked={autoPublishOnDrop}
                  className={`w-9 h-5 flex items-center rounded-full p-0.5 transition-colors duration-300 ${
                    autoPublishOnDrop
                      ? 'bg-gradient-to-r from-purple-500 to-fuchsia-500 shadow-[0_0_12px_rgba(168,85,247,0.7)]'
                      : 'bg-white/15'
                  }`}
                >
                  <span
                    className={`bg-white w-4 h-4 rounded-full shadow-md transform transition-transform duration-300 ${
                      autoPublishOnDrop ? 'translate-x-4' : 'translate-x-0'
                    }`}
                  />
                </button>
                <span className="text-xs font-mono text-zinc-200 flex items-center gap-1.5">
                  <Zap className="w-3.5 h-3.5 text-purple-300 fill-purple-300" />
                  Auto-post immediately upon drop
                </span>
              </div>
            </div>
          </div>
        </section>

        {/* Batch Action Bar (if videos exist) */}
        {videos.length > 0 && (
          <div className="flex items-center justify-between pt-2 glass-panel px-5 py-3 rounded-2xl">
            <span className="text-xs font-mono text-purple-100/80">
              {videos.length} video(s) ·{' '}
              <span className="text-white font-semibold">
                {videos.filter(v => v.status === 'published').length} published
              </span>
            </span>

            {pendingVideos.length > 0 && (
              <button
                onClick={handlePublishAll}
                className="px-5 py-2 rounded-full liquid-btn-primary text-xs font-bold flex items-center gap-2 transition-all cursor-pointer"
              >
                <Play className="w-3.5 h-3.5 fill-current" />
                <span>Upload & Post All ({pendingVideos.length})</span>
              </button>
            )}
          </div>
        )}

        {/* Video Cards with Purple & White Liquid Glass Styling */}
        {videos.length > 0 && (
          <div className="space-y-6">
            {videos.map(video => (
              <article
                key={video.id}
                className="glass-card rounded-3xl p-6 space-y-4 relative overflow-hidden group"
              >
                <div className="absolute top-0 left-8 right-8 h-[1.5px] bg-gradient-to-r from-transparent via-purple-200/60 to-transparent pointer-events-none group-hover:via-white/90 transition-all duration-300" />

                {/* Header: Title & Status */}
                <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
                  <div className="space-y-1.5">
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] font-mono uppercase px-2.5 py-0.5 rounded-full bg-purple-500/15 border border-purple-400/25 text-purple-200">
                        {video.duration ? `${video.duration.toFixed(1)}s` : 'Video'}
                      </span>

                      <span
                        className={`text-[10px] font-mono px-3 py-0.5 rounded-full border uppercase backdrop-blur-md ${
                          video.status === 'published'
                            ? 'bg-emerald-500/15 text-emerald-300 border-emerald-400/35 shadow-[0_0_12px_rgba(52,211,153,0.25)]'
                            : video.status === 'publishing'
                            ? 'bg-purple-500/25 text-purple-200 border-purple-400/45 animate-pulse shadow-[0_0_14px_rgba(168,85,247,0.35)]'
                            : video.status === 'failed'
                            ? 'bg-rose-500/15 text-rose-300 border-rose-500/35'
                            : 'bg-white/[0.07] text-zinc-200 border-white/[0.16]'
                        }`}
                      >
                        {video.status === 'published'
                          ? 'Published'
                          : video.status === 'publishing'
                          ? `Publishing in ${browserName}...`
                          : video.status === 'failed'
                          ? 'Failed'
                          : 'Ready to Post'}
                      </span>
                    </div>

                    <h3 className="text-base font-semibold text-white tracking-tight">
                      {video.title}
                    </h3>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-2 shrink-0">
                    {video.status === 'published' ? (
                      <div className="flex items-center gap-2">
                        {video.tiktok_url && (
                          <a
                            href="https://www.tiktok.com/tiktokstudio/manage"
                            target="_blank"
                            rel="noreferrer"
                            className="px-3.5 py-1.5 rounded-full liquid-btn-primary text-xs font-semibold flex items-center gap-1.5 transition-all"
                          >
                            <span>TikTok Studio</span>
                            <ArrowUpRight className="w-3.5 h-3.5 text-black" />
                          </a>
                        )}
                        {video.youtube_url && (
                          <a
                            href={video.youtube_url}
                            target="_blank"
                            rel="noreferrer"
                            className="px-3.5 py-1.5 rounded-full glass-pill hover:border-purple-300/50 text-xs font-medium flex items-center gap-1.5 transition-all"
                          >
                            <span>YouTube</span>
                            <ExternalLink className="w-3 h-3" />
                          </a>
                        )}
                      </div>
                    ) : (
                      <button
                        onClick={() => handlePublishSingle(video.id)}
                        disabled={video.status === 'publishing'}
                        className="px-4 py-1.5 rounded-full liquid-btn-primary text-xs font-semibold flex items-center gap-1.5 cursor-pointer transition-all shadow-sm disabled:opacity-50"
                      >
                        <Play className="w-3 h-3 fill-current" />
                        <span>Post Now</span>
                      </button>
                    )}

                    <button
                      onClick={() => handleRegenerateMetadata(video.id)}
                      title="Regenerate caption and hashtags"
                      className="p-2 rounded-full glass-pill hover:border-purple-300/50 text-purple-200 hover:text-white transition-all cursor-pointer"
                    >
                      <Sparkles className="w-3.5 h-3.5" />
                    </button>

                    <button
                      onClick={() => handleDeleteVideo(video.id)}
                      title="Delete video"
                      className="p-2 rounded-full glass-pill hover:border-rose-500/50 text-zinc-400 hover:text-rose-400 transition-all cursor-pointer"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>

                {/* Video Preview */}
                {video.video_path && (
                  <div className="rounded-2xl border border-purple-300/[0.16] bg-black/70 flex justify-center p-2.5 relative overflow-hidden backdrop-blur-md shadow-2xl">
                    <video
                      controls
                      className="max-h-72 w-auto rounded-xl shadow-xl"
                      src={`/media/${
                        video.video_path.replace(/\\/g, '/').split('output/')[1] ||
                        'uploads/video.mp4'
                      }`}
                    />
                  </div>
                )}

                {/* Extracted Script */}
                {video.script && (
                  <div className="p-3.5 bg-purple-950/[0.18] border border-purple-300/[0.14] rounded-2xl text-xs space-y-1 backdrop-blur-md">
                    <span className="font-mono text-[10px] uppercase text-purple-300/80 block tracking-wider">
                      Spoken Script
                    </span>
                    <p className="text-zinc-200 text-xs leading-relaxed">{video.script}</p>
                  </div>
                )}

                {/* Caption & Hashtags Box */}
                {video.tiktok_hashtags && (
                  <div className="p-4 bg-white/[0.04] border border-purple-300/[0.16] rounded-2xl space-y-2.5 text-xs backdrop-blur-md">
                    <div className="flex items-center justify-between text-zinc-300">
                      <span className="font-mono text-[10px] uppercase text-purple-200 font-semibold flex items-center gap-1.5">
                        <Hash className="w-3.5 h-3.5 text-purple-400" />
                        <span>Caption & Hashtags</span>
                      </span>
                      <button
                        onClick={() => {
                          const full = `${video.title}\n\n${video.tiktok_hashtags}`;
                          copyToClipboard(full, `cap-${video.id}`);
                        }}
                        className="text-xs hover:text-white flex items-center gap-1.5 cursor-pointer font-mono text-purple-200/80 transition-colors"
                      >
                        {copiedKey === `cap-${video.id}` ? (
                          <>
                            <Check className="w-3.5 h-3.5 text-emerald-400" />
                            <span className="text-emerald-400 font-semibold">Copied</span>
                          </>
                        ) : (
                          <>
                            <Copy className="w-3.5 h-3.5" />
                            <span>Copy</span>
                          </>
                        )}
                      </button>
                    </div>
                    <p className="text-zinc-200 text-xs font-mono select-all bg-black/65 p-3.5 rounded-xl border border-purple-400/[0.15] leading-relaxed">
                      <span className="text-white font-semibold">{video.title}</span>
                      <br />
                      <br />
                      <span className="text-purple-300/90">{video.tiktok_hashtags}</span>
                    </p>
                  </div>
                )}

                {/* Pinned Discussion Comment */}
                {video.tiktok_commentary && (
                  <div className="p-4 bg-white/[0.04] border border-purple-300/[0.16] rounded-2xl space-y-2 text-xs backdrop-blur-md">
                    <div className="flex items-center justify-between text-zinc-300">
                      <span className="font-mono text-[10px] uppercase text-purple-200 font-semibold flex items-center gap-1.5">
                        <MessageSquareQuote className="w-3.5 h-3.5 text-purple-400" />
                        <span>TikTok Pinned Comment</span>
                      </span>
                      <button
                        onClick={() =>
                          copyToClipboard(video.tiktok_commentary, `comm-${video.id}`)
                        }
                        className="text-xs hover:text-white flex items-center gap-1.5 cursor-pointer font-mono text-purple-200/80 transition-colors"
                      >
                        {copiedKey === `comm-${video.id}` ? (
                          <>
                            <Check className="w-3.5 h-3.5 text-emerald-400" />
                            <span className="text-emerald-400 font-semibold">Copied</span>
                          </>
                        ) : (
                          <>
                            <Copy className="w-3.5 h-3.5" />
                            <span>Copy</span>
                          </>
                        )}
                      </button>
                    </div>
                    <p className="text-zinc-200 text-xs leading-relaxed font-mono select-all bg-black/65 p-3.5 rounded-xl border border-purple-400/[0.15]">
                      {video.tiktok_commentary}
                    </p>
                  </div>
                )}

                {/* Error Banner */}
                {video.error_message && video.status === 'failed' && (
                  <div className="p-3.5 bg-rose-500/10 border border-rose-500/30 rounded-2xl text-xs text-rose-300 flex items-center gap-2.5 backdrop-blur-md">
                    <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" />
                    <span>{video.error_message}</span>
                  </div>
                )}
              </article>
            ))}
          </div>
        )}
      </main>

      {/* Liquid Glass Channel Connection Modal */}
      {showChannelsModal && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-2xl flex items-center justify-center p-4 animate-in fade-in duration-200">
          <div className="glass-modal rounded-3xl max-w-lg w-full p-6 space-y-6 shadow-2xl relative overflow-hidden animate-in zoom-in-95 duration-200">
            <div className="absolute top-0 left-8 right-8 h-[1.5px] bg-gradient-to-r from-transparent via-purple-300/70 to-transparent pointer-events-none" />

            <div className="flex items-center justify-between border-b border-white/[0.12] pb-4">
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-purple-400 shadow-[0_0_8px_rgba(192,132,252,1)]" />
                <h3 className="text-sm font-semibold tracking-wider text-white font-mono uppercase">
                  Platform Accounts
                </h3>
              </div>
              <button
                onClick={() => setShowChannelsModal(false)}
                className="w-7 h-7 rounded-full glass-pill flex items-center justify-center text-zinc-300 hover:text-white text-xs font-mono cursor-pointer transition-colors"
              >
                ✕
              </button>
            </div>

            {/* TikTok Session */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-xs font-semibold text-white block">
                    TikTok ({browserName})
                  </span>
                  <span className="text-[11px] text-zinc-300/80">
                    {channels.tiktok?.connected
                      ? `Session saved in ${browserName}. Background uploads active.`
                      : `Log into TikTok once in ${browserName} to save your session.`}
                  </span>
                </div>
              </div>

              <button
                onClick={handleLaunchBrowserTikTok}
                className="px-4 py-2 rounded-full liquid-btn-primary text-xs font-semibold cursor-pointer flex items-center gap-2 transition-all shadow-sm"
              >
                <ExternalLink className="w-3.5 h-3.5" />
                <span>
                  {channels.tiktok?.connected
                    ? `Re-open ${browserName} Login`
                    : `Log In via ${browserName}`}
                </span>
              </button>
            </div>

            {/* YouTube Shorts */}
            <div className="space-y-3 pt-4 border-t border-white/[0.12]">
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-xs font-semibold text-white block">YouTube Shorts</span>
                  <span className="text-[11px] text-zinc-300/80">
                    {channels.youtube?.connected
                      ? 'OAuth credentials active.'
                      : 'Paste OAuth JSON or refresh token.'}
                  </span>
                </div>
              </div>

              {!channels.youtube?.connected && (
                <div className="space-y-2.5">
                  <input
                    type="text"
                    placeholder="Paste youtube_token.json content or OAuth credentials..."
                    value={ytToken}
                    onChange={e => setYtToken(e.target.value)}
                    className="w-full bg-white/[0.05] border border-purple-300/[0.22] rounded-xl px-3.5 py-2 text-xs text-white placeholder-zinc-500 font-mono focus:outline-none focus:border-purple-400/80 focus:bg-white/[0.08] transition-all"
                  />
                  <button
                    onClick={handleSaveYouTubeToken}
                    className="px-4 py-2 rounded-full liquid-btn-primary text-xs font-semibold cursor-pointer shadow-sm"
                  >
                    Save Token
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
