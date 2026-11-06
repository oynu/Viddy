import React, { useState } from 'react';
import { Film, Play, ExternalLink, Download, CheckCircle2, Clock, Share2, Youtube } from 'lucide-react';

interface VideoItem {
  id: number;
  title: string;
  topic: string;
  category: string;
  script: string;
  hook?: string;
  duration: number;
  status: string;
  video_path?: string;
  thumbnail_path?: string;
  published_destinations: string;
  youtube_url?: string;
  tiktok_url?: string;
  qc_passed: boolean;
  created_at?: string;
}

interface VideoLibraryProps {
  videos: VideoItem[];
  onRefresh: () => void;
}

export const VideoLibrary: React.FC<VideoLibraryProps> = ({ videos, onRefresh }) => {
  const [selectedVideo, setSelectedVideo] = useState<VideoItem | null>(null);

  return (
    <div className="glass-panel rounded-2xl p-6 border border-slate-800 shadow-xl">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-xl font-black text-white flex items-center gap-2.5">
            <Film className="w-5 h-5 text-cyan-400" />
            <span>Autonomous Video Library</span>
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Archive of all programmatically produced educational 3D short-form videos
          </p>
        </div>
        <button
          onClick={onRefresh}
          className="px-3.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-300 transition-all cursor-pointer"
        >
          Refresh Library
        </button>
      </div>

      {videos.length === 0 ? (
        <div className="py-16 text-center text-slate-500">
          <Film className="w-12 h-12 mx-auto mb-3 opacity-30" />
          <p className="text-base font-semibold text-slate-400">Library is currently empty</p>
          <p className="text-xs text-slate-500 mt-1">
            As Viddy discovers, renders and publishes videos, they will appear here automatically.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {videos.map(video => (
            <div
              key={video.id}
              className="bg-slate-900/80 rounded-xl overflow-hidden border border-slate-800/80 hover:border-slate-700 transition-all group flex flex-col justify-between"
            >
              {/* Thumbnail / Header */}
              <div className="relative aspect-[9/12] bg-slate-950 flex items-center justify-center overflow-hidden">
                <div className="absolute inset-0 bg-gradient-to-t from-slate-950 via-transparent to-transparent z-10 opacity-80" />
                
                {/* Visual placeholder or real thumbnail */}
                <div className="w-full h-full flex flex-col items-center justify-center p-6 text-center relative z-0 bg-slate-900">
                  <div className="w-16 h-16 rounded-2xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400 mb-3 group-hover:scale-110 transition-transform">
                    <Play className="w-8 h-8 fill-current ml-1" />
                  </div>
                  <span className="text-[10px] uppercase font-bold tracking-widest text-cyan-400">
                    {video.category || 'Science'}
                  </span>
                  <p className="text-sm font-bold text-white mt-1 line-clamp-3">
                    {video.title}
                  </p>
                </div>

                {/* Duration badge */}
                <span className="absolute bottom-3 right-3 z-20 px-2 py-0.5 rounded-md bg-black/80 backdrop-blur text-[11px] font-mono font-semibold text-slate-200">
                  {video.duration ? `${video.duration.toFixed(1)}s` : '35.0s'}
                </span>

                {/* QC badge */}
                {video.qc_passed && (
                  <span className="absolute top-3 left-3 z-20 flex items-center gap-1 px-2 py-0.5 rounded-md bg-emerald-500/20 backdrop-blur border border-emerald-500/40 text-[10px] font-bold text-emerald-400">
                    <CheckCircle2 className="w-3 h-3" />
                    <span>QC PASSED</span>
                  </span>
                )}
              </div>

              {/* Details & Platform Links */}
              <div className="p-4">
                <h4 className="text-sm font-bold text-slate-100 line-clamp-2 leading-snug">
                  {video.title}
                </h4>
                {video.hook && (
                  <p className="text-xs text-slate-400 mt-1 line-clamp-2 italic">
                    "{video.hook}"
                  </p>
                )}

                {/* Published destinations buttons */}
                <div className="flex items-center gap-2 mt-4 pt-3 border-t border-slate-800">
                  {video.youtube_url ? (
                    <a
                      href={video.youtube_url}
                      target="_blank"
                      rel="noreferrer"
                      className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-red-600/10 hover:bg-red-600/20 border border-red-600/30 text-red-400 text-xs font-semibold transition-all"
                    >
                      <Youtube className="w-3.5 h-3.5" />
                      <span>YouTube</span>
                      <ExternalLink className="w-2.5 h-2.5" />
                    </a>
                  ) : null}

                  {video.tiktok_url ? (
                    <a
                      href={video.tiktok_url}
                      target="_blank"
                      rel="noreferrer"
                      className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-cyan-500/10 hover:bg-cyan-500/20 border border-cyan-500/30 text-cyan-400 text-xs font-semibold transition-all"
                    >
                      <Share2 className="w-3.5 h-3.5" />
                      <span>TikTok</span>
                      <ExternalLink className="w-2.5 h-2.5" />
                    </a>
                  ) : null}

                  {video.video_path ? (
                    <button
                      onClick={() => setSelectedVideo(video)}
                      className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold transition-all cursor-pointer"
                    >
                      <Play className="w-3.5 h-3.5 fill-current" />
                      <span>Inspect</span>
                    </button>
                  ) : null}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Video Inspector Modal */}
      {selectedVideo && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md">
          <div className="glass-panel rounded-2xl p-6 border border-slate-700 max-w-xl w-full shadow-2xl relative">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold text-white truncate max-w-md">{selectedVideo.title}</h3>
              <button
                onClick={() => setSelectedVideo(null)}
                className="w-8 h-8 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 flex items-center justify-center text-sm font-bold cursor-pointer"
              >
                ✕
              </button>
            </div>

            <div className="bg-slate-950 rounded-xl p-4 mb-4 border border-slate-800">
              <span className="text-[11px] font-bold text-cyan-400 uppercase tracking-wider block mb-1">
                Narration Script
              </span>
              <p className="text-xs text-slate-300 leading-relaxed max-h-48 overflow-y-auto">
                {selectedVideo.script || 'Script unavailable.'}
              </p>
            </div>

            <div className="grid grid-cols-2 gap-3 text-xs mb-4">
              <div className="bg-slate-900 p-2.5 rounded-lg border border-slate-800">
                <span className="text-slate-500 block">Created At</span>
                <span className="font-semibold text-slate-300">{selectedVideo.created_at || 'Just now'}</span>
              </div>
              <div className="bg-slate-900 p-2.5 rounded-lg border border-slate-800">
                <span className="text-slate-500 block">Duration</span>
                <span className="font-semibold text-slate-300">{selectedVideo.duration.toFixed(1)} seconds</span>
              </div>
            </div>

            <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
              <button
                onClick={() => setSelectedVideo(null)}
                className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold cursor-pointer"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
