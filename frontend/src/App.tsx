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
      fetchVideos();
      fetchQueueStatus();
    }, 2500);

    return () => clearInterval(interval);
  }, []);

  const handleFileUpload = async (fileList: FileList | null) => {
    if (!fileList || fileList.length === 0) return;

    setIsUploading(true);
    showNotification(`Importing ${fileList.length} video(s)... Generating viral captions & hashtags...`);

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
          showNotification(`🚀 ${data.count} video(s) imported & publishing to ${destination.toUpperCase()} now!`);
        } else {
          showNotification(`✓ ${data.count} video(s) imported with viral captions & hashtags ready!`);
        }
        await fetchVideos();
        await fetchQueueStatus();
      } else {
        showNotification(data.message || 'Upload failed.');
      }
    } catch (e: any) {
      showNotification('Error importing videos: ' + e.message);
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
      showNotification('Regenerating viral caption & hashtags...');
      const res = await fetch(`/api/videos/${videoId}/auto-metadata`, { method: 'POST' });
      const data = await res.json();
      if (data.success) {
        showNotification('Viral caption & reach hashtags updated!');
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

  const pendingVideos = videos.filter(v => v.status === 'ready' || v.status === 'queued' || v.status === 'failed');

  return (
    <div className="min-h-screen bg-black text-white selection:bg-white selection:text-black font-sans antialiased">
      {/* Toast Notification */}
      {notification && (
        <div className="fixed top-5 right-5 z-50 bg-white text-black px-4 py-2.5 rounded shadow-2xl text-xs font-mono flex items-center gap-2">
          <Check className="w-4 h-4 text-black" />
          <span>{notification}</span>
        </div>
      )}

      {/* Top Minimal Header */}
      <header className="border-b border-[#1c1c1c] px-6 py-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <span className="font-mono text-base tracking-widest font-black uppercase text-white">VIDDY</span>
          <span className="text-xs text-[#444] font-mono">/</span>
          <span className="text-xs text-[#888] font-medium tracking-tight">Auto-Video Publisher</span>
        </div>

        {/* Platform Account Badges & Clear */}
        <div className="flex items-center gap-2.5">
          {/* TikTok Pill */}
          <button
            onClick={channels.tiktok?.connected ? () => setShowChannelsModal(true) : handleLaunchBrowserTikTok}
            className={`px-3 py-1.5 rounded text-xs font-mono flex items-center gap-1.5 transition-all cursor-pointer border ${
              channels.tiktok?.connected
                ? 'bg-[#111] text-white border-[#333] hover:border-white'
                : 'bg-white text-black font-semibold border-white hover:bg-[#eaeaea]'
            }`}
          >
            <span className={`w-2 h-2 rounded-full ${channels.tiktok?.connected ? 'bg-white' : 'bg-black'}`} />
            <span>{channels.tiktok?.connected ? `TikTok (${browserName} Active)` : `Connect TikTok in ${browserName}`}</span>
          </button>

          {/* YouTube Shorts Pill */}
          <button
            onClick={() => setShowChannelsModal(true)}
            className={`px-3 py-1.5 rounded text-xs font-mono flex items-center gap-1.5 transition-all cursor-pointer border ${
              channels.youtube?.connected
                ? 'bg-[#111] text-white border-[#333] hover:border-white'
                : 'bg-[#141414] text-[#777] border-[#262626] hover:text-white'
            }`}
          >
            <span className={`w-2 h-2 rounded-full ${channels.youtube?.connected ? 'bg-white' : 'bg-[#555]'}`} />
            <span>{channels.youtube?.connected ? 'Shorts API (Active)' : 'Connect YouTube'}</span>
          </button>

          {videos.length > 0 && (
            <button
              onClick={handleClearAll}
              title="Clear all videos"
              className="p-1.5 rounded bg-black border border-[#262626] hover:border-[#666] text-[#666] hover:text-[#f87171] transition-all cursor-pointer"
            >
              <Trash2 className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </header>

      {/* Main Container */}
      <main className="max-w-3xl mx-auto px-6 py-10 space-y-8">
        
        {/* Destination Picker */}
        <div className="flex items-center justify-between">
          <span className="text-xs font-mono uppercase tracking-wider text-[#777]">
            Upload Target
          </span>
          <div className="flex items-center gap-2">
            {[
              { id: 'tiktok', label: `TikTok (${browserName})` },
              { id: 'youtube', label: 'YouTube Shorts' },
              { id: 'both', label: 'Both' }
            ].map(p => (
              <button
                key={p.id}
                onClick={() => setDestination(p.id as any)}
                className={`px-3 py-1.5 rounded text-xs font-medium border transition-all cursor-pointer ${
                  destination === p.id
                    ? 'bg-white text-black border-white font-semibold'
                    : 'bg-[#0f0f0f] text-[#888] border-[#222] hover:border-[#444] hover:text-white'
                }`}
              >
                {p.label}
              </button>
            ))}
          </div>
        </div>

        {/* The Core Upload / Drop Box */}
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
          className={`border-2 border-dashed rounded-2xl p-12 text-center transition-all cursor-pointer ${
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

          <div className="flex flex-col items-center justify-center space-y-3.5">
            <div className="w-12 h-12 rounded-full bg-[#141414] border border-[#2a2a2a] flex items-center justify-center">
              {isUploading ? (
                <Loader2 className="w-6 h-6 text-white animate-spin" />
              ) : (
                <UploadCloud className="w-6 h-6 text-white" />
              )}
            </div>

            <div>
              <h2 className="text-base font-bold text-white tracking-tight">
                {isUploading ? 'Importing and crafting viral captions...' : 'Drop your videos here or click to import'}
              </h2>
              <p className="text-xs text-[#777] mt-1 max-w-sm mx-auto">
                Auto-transcribes the script, crafts retention captions & reach hashtags, and uploads to {destination.toUpperCase()}.
              </p>
            </div>

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
                ⚡ Auto-post immediately upon drop
              </label>
            </div>
          </div>
        </section>

        {/* Batch Action Bar (if videos exist) */}
        {videos.length > 0 && (
          <div className="flex items-center justify-between pt-2">
            <span className="text-xs font-mono text-[#777]">
              {videos.length} video(s) · {videos.filter(v => v.status === 'published').length} published
            </span>

            {pendingVideos.length > 0 && (
              <button
                onClick={handlePublishAll}
                className="px-4 py-2 rounded bg-white text-black hover:bg-[#eaeaea] text-xs font-bold flex items-center gap-2 transition-all cursor-pointer shadow-lg"
              >
                <Play className="w-3.5 h-3.5 fill-current" />
                <span>Upload & Post All ({pendingVideos.length})</span>
              </button>
            )}
          </div>
        )}

        {/* Video Cards */}
        {videos.length > 0 && (
          <div className="space-y-6">
            {videos.map(video => (
              <article
                key={video.id}
                className="border border-[#222] bg-[#0a0a0a] rounded-xl p-5 space-y-4 transition-all"
              >
                {/* Header: Title & Status */}
                <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] font-mono uppercase text-[#777]">
                        {video.duration ? `${video.duration.toFixed(1)}s` : 'Video'}
                      </span>

                      {/* Status Tag */}
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
                          ? `Publishing in ${browserName}...`
                          : video.status === 'failed'
                          ? 'Failed'
                          : 'Ready to Post'}
                      </span>
                    </div>

                    <h3 className="text-sm font-bold text-white tracking-tight">{video.title}</h3>
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
                            className="px-3 py-1.5 rounded bg-white text-black hover:bg-[#eaeaea] text-xs font-semibold flex items-center gap-1.5 transition-all"
                          >
                            <span>TikTok Studio</span>
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
                            <span>YouTube</span>
                            <ExternalLink className="w-3 h-3" />
                          </a>
                        )}
                      </div>
                    ) : (
                      <button
                        onClick={() => handlePublishSingle(video.id)}
                        disabled={video.status === 'publishing'}
                        className="px-3 py-1.5 rounded bg-white text-black hover:bg-[#eaeaea] text-xs font-semibold flex items-center gap-1.5 cursor-pointer transition-all shadow-sm"
                      >
                        <Play className="w-3 h-3 fill-current" />
                        <span>Post Now</span>
                      </button>
                    )}

                    <button
                      onClick={() => handleRegenerateMetadata(video.id)}
                      title="Regenerate viral caption and hashtags"
                      className="p-1.5 rounded bg-black border border-[#2a2a2a] hover:border-white text-[#888] hover:text-white transition-all cursor-pointer"
                    >
                      <Sparkles className="w-3.5 h-3.5" />
                    </button>

                    <button
                      onClick={() => handleDeleteVideo(video.id)}
                      title="Delete video"
                      className="p-1.5 rounded bg-black border border-[#2a2a2a] hover:border-[#666] text-[#666] hover:text-[#f87171] transition-all cursor-pointer"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>

                {/* Video Preview */}
                {video.video_path && (
                  <div className="bg-black rounded border border-[#1a1a1a] flex justify-center p-2 relative">
                    <video
                      controls
                      className="max-h-64 w-auto rounded shadow-lg"
                      src={`/media/${video.video_path.replace(/\\/g, '/').split('output/')[1] || 'uploads/video.mp4'}`}
                    />
                  </div>
                )}

                {/* Extracted Script */}
                {video.script && (
                  <div className="p-2.5 bg-black border border-[#1a1a1a] rounded text-xs space-y-1">
                    <span className="font-mono text-[10px] uppercase text-[#666] block">
                      Spoken Script
                    </span>
                    <p className="text-[#999] text-xs leading-relaxed">{video.script}</p>
                  </div>
                )}

                {/* Viral Caption & Hashtags Box */}
                {video.tiktok_hashtags && (
                  <div className="p-3 bg-black border border-[#1f1f1f] rounded space-y-2 text-xs">
                    <div className="flex items-center justify-between text-[#888]">
                      <span className="font-mono text-[10px] uppercase text-white font-semibold flex items-center gap-1">
                        <Hash className="w-3 h-3 text-white" />
                        <span>Viral Caption & Hashtags</span>
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
                            <span>Copy</span>
                          </>
                        )}
                      </button>
                    </div>
                    <p className="text-[#ccc] text-xs font-mono select-all bg-[#0a0a0a] p-2 rounded border border-[#181818]">
                      <span className="text-white font-bold">{video.title}</span>
                      <br /><br />
                      <span className="text-[#777]">{video.tiktok_hashtags}</span>
                    </p>
                  </div>
                )}

                {/* Pinned Discussion Comment */}
                {video.tiktok_commentary && (
                  <div className="p-3 bg-black border border-[#1f1f1f] rounded space-y-1.5 text-xs">
                    <div className="flex items-center justify-between text-[#888]">
                      <span className="font-mono text-[10px] uppercase text-white font-semibold flex items-center gap-1">
                        <MessageSquareQuote className="w-3 h-3 text-white" />
                        <span>TikTok Pinned Comment</span>
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
                            <span>Copy</span>
                          </>
                        )}
                      </button>
                    </div>
                    <p className="text-white text-xs leading-relaxed font-mono select-all bg-[#0a0a0a] p-2 rounded border border-[#181818]">
                      {video.tiktok_commentary}
                    </p>
                  </div>
                )}

                {/* Error Banner */}
                {video.error_message && video.status === 'failed' && (
                  <div className="p-2.5 bg-[#1a0a0a] border border-[#3b1212] rounded text-xs text-[#f87171] flex items-center gap-2">
                    <AlertCircle className="w-4 h-4 shrink-0" />
                    <span>{video.error_message}</span>
                  </div>
                )}
              </article>
            ))}
          </div>
        )}
      </main>

      {/* Platform Channel Connection Modal */}
      {showChannelsModal && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#0f0f0f] border border-[#2a2a2a] rounded-xl max-w-lg w-full p-6 space-y-6 shadow-2xl">
            <div className="flex items-center justify-between border-b border-[#222] pb-4">
              <h3 className="text-sm font-bold tracking-tight text-white font-mono uppercase">
                Platform Accounts
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
                  <span className="text-xs font-bold text-white block">TikTok ({browserName})</span>
                  <span className="text-[11px] text-[#777]">
                    {channels.tiktok?.connected
                      ? `Session saved in ${browserName}. Background uploads active.`
                      : `Log into TikTok once in ${browserName} to save your session.`}
                  </span>
                </div>
              </div>

              <button
                onClick={handleLaunchBrowserTikTok}
                className="px-3.5 py-1.5 rounded bg-white text-black text-xs font-semibold hover:bg-[#eaeaea] cursor-pointer flex items-center gap-1.5"
              >
                <ExternalLink className="w-3.5 h-3.5" />
                <span>{channels.tiktok?.connected ? `Re-open ${browserName} Login` : `Log In via ${browserName}`}</span>
              </button>
            </div>

            {/* YouTube Shorts */}
            <div className="space-y-3 pt-4 border-t border-[#222]">
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-xs font-bold text-white block">YouTube Shorts</span>
                  <span className="text-[11px] text-[#777]">
                    {channels.youtube?.connected
                      ? 'OAuth credentials active.'
                      : 'Paste OAuth JSON or refresh token.'}
                  </span>
                </div>
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
