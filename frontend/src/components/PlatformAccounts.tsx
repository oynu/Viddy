import React, { useState } from 'react';
import { Youtube, Share2, CheckCircle2, AlertCircle, Link2, Key } from 'lucide-react';

interface ChannelStatus {
  connected: boolean;
  account_name?: string;
  channel_id?: string;
  token_expiry?: string;
}

interface PlatformAccountsProps {
  channels: {
    youtube: ChannelStatus;
    tiktok: ChannelStatus;
  };
  onConnect: (platform: string, accountName: string) => Promise<void>;
}

export const PlatformAccounts: React.FC<PlatformAccountsProps> = ({ channels, onConnect }) => {
  const [connectingPlatform, setConnectingPlatform] = useState<string | null>(null);
  const [accountName, setAccountName] = useState('');

  const handleConnectSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!connectingPlatform) return;
    await onConnect(connectingPlatform, accountName || `${connectingPlatform.toUpperCase()} Creator Account`);
    setConnectingPlatform(null);
    setAccountName('');
  };

  return (
    <div className="glass-panel rounded-2xl p-6 border border-slate-800 shadow-xl">
      <div className="mb-6">
        <h3 className="text-xl font-black text-white flex items-center gap-2.5">
          <Link2 className="w-5 h-5 text-cyan-400" />
          <span>Publishing Accounts & Integrations</span>
        </h3>
        <p className="text-xs text-slate-400 mt-0.5">
          OAuth connectors for automated publishing to YouTube Shorts and TikTok Content Posting API
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {/* YouTube Card */}
        <div className="bg-slate-900/80 rounded-xl p-5 border border-slate-800/80 hover:border-slate-700 transition-all flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-red-600/10 border border-red-600/30 flex items-center justify-center text-red-500">
                  <Youtube className="w-5 h-5" />
                </div>
                <div>
                  <h4 className="text-sm font-bold text-white">YouTube Shorts</h4>
                  <span className="text-[11px] text-slate-400">YouTube Data API v3</span>
                </div>
              </div>
              <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold flex items-center gap-1 ${
                channels.youtube.connected
                  ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                  : 'bg-slate-800 text-slate-400'
              }`}>
                {channels.youtube.connected ? (
                  <>
                    <CheckCircle2 className="w-3 h-3" />
                    <span>Connected</span>
                  </>
                ) : (
                  <span>Not Connected</span>
                )}
              </span>
            </div>

            <p className="text-xs text-slate-400 leading-relaxed mb-4">
              {channels.youtube.connected
                ? `Authorized as: ${channels.youtube.account_name || 'Channel Linked'}. Videos auto-upload with #Shorts tags.`
                : 'Connect your channel to publish 1080x1920 vertical animations directly to YouTube Shorts with descriptions & tags.'}
            </p>
          </div>

          <button
            onClick={() => setConnectingPlatform('youtube')}
            className="w-full py-2.5 rounded-xl bg-red-600/10 hover:bg-red-600/20 border border-red-600/30 text-red-400 text-xs font-bold transition-all flex items-center justify-center gap-2 cursor-pointer"
          >
            <Key className="w-3.5 h-3.5" />
            <span>{channels.youtube.connected ? 'Update Connection / Refresh' : 'Connect YouTube Account'}</span>
          </button>
        </div>

        {/* TikTok Card */}
        <div className="bg-slate-900/80 rounded-xl p-5 border border-slate-800/80 hover:border-slate-700 transition-all flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
                  <Share2 className="w-5 h-5" />
                </div>
                <div>
                  <h4 className="text-sm font-bold text-white">TikTok</h4>
                  <span className="text-[11px] text-slate-400">Content Posting API v2</span>
                </div>
              </div>
              <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold flex items-center gap-1 ${
                channels.tiktok.connected
                  ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                  : 'bg-slate-800 text-slate-400'
              }`}>
                {channels.tiktok.connected ? (
                  <>
                    <CheckCircle2 className="w-3 h-3" />
                    <span>Connected</span>
                  </>
                ) : (
                  <span>Not Connected</span>
                )}
              </span>
            </div>

            <p className="text-xs text-slate-400 leading-relaxed mb-4">
              {channels.tiktok.connected
                ? `Authorized as: ${channels.tiktok.account_name || 'Creator Linked'}. Direct posting active.`
                : 'Connect your creator account to automatically publish videos with optimized captions, hashtags and sound.'}
            </p>
          </div>

          <button
            onClick={() => setConnectingPlatform('tiktok')}
            className="w-full py-2.5 rounded-xl bg-cyan-500/10 hover:bg-cyan-500/20 border border-cyan-500/30 text-cyan-400 text-xs font-bold transition-all flex items-center justify-center gap-2 cursor-pointer"
          >
            <Key className="w-3.5 h-3.5" />
            <span>{channels.tiktok.connected ? 'Update Connection / Refresh' : 'Connect TikTok Account'}</span>
          </button>
        </div>
      </div>

      {/* Connection Modal */}
      {connectingPlatform && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md">
          <form
            onSubmit={handleConnectSubmit}
            className="glass-panel rounded-2xl p-6 border border-slate-700 max-w-md w-full shadow-2xl relative"
          >
            <h3 className="text-lg font-bold text-white mb-2">
              Connect {connectingPlatform === 'youtube' ? 'YouTube Shorts' : 'TikTok'}
            </h3>
            <p className="text-xs text-slate-400 mb-4 leading-relaxed">
              Enter your account handle or creator channel name. In production mode, this initiates official OAuth consent for automated posting.
            </p>

            <label className="text-xs font-semibold text-slate-300 block mb-1.5">
              Account / Channel Handle
            </label>
            <input
              type="text"
              placeholder="@MyAwesomeScienceChannel"
              value={accountName}
              onChange={e => setAccountName(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-white text-xs placeholder-slate-500 focus:outline-none focus:border-cyan-400 mb-5"
              required
            />

            <div className="flex items-center justify-end gap-3">
              <button
                type="button"
                onClick={() => setConnectingPlatform(null)}
                className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold cursor-pointer"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-5 py-2 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 text-xs font-bold shadow-lg shadow-cyan-500/20 cursor-pointer"
              >
                Authorize & Link
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
};
