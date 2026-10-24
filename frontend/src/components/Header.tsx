import React from 'react';
import { Wind, Activity, RefreshCw, Database } from 'lucide-react';

interface HeaderProps {
  onSync: () => void;
  isSyncing: boolean;
  isLive: boolean;
  cachedCount?: { actuals: number; forecasts: number };
}

export const Header: React.FC<HeaderProps> = ({ onSync, isSyncing, isLive, cachedCount }) => {
  return (
    <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur sticky top-0 z-50 px-6 py-4">
      <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
            <Wind className="w-6 h-6 animate-pulse" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold tracking-tight text-white">
                UK Day-Ahead Wind Workbench
              </h1>
              <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-medium">
                Pilot v1.0
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Wholesale Power Procurement & Renewable Forecast Error Quantification Desk
            </p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          {cachedCount && (
            <div className="hidden lg:flex items-center gap-2 text-xs px-3 py-1.5 rounded-lg bg-slate-800/50 border border-slate-700/50 text-slate-400">
              <Database className="w-3.5 h-3.5 text-blue-400" />
              <span>Cache:</span>
              <span className="font-mono text-slate-200">{cachedCount.actuals} actuals / {cachedCount.forecasts} forecasts</span>
            </div>
          )}

          <div className="flex items-center gap-2 text-xs px-3 py-1.5 rounded-lg bg-slate-800/80 border border-slate-700/60">
            <Activity className={`w-3.5 h-3.5 ${isLive ? 'text-emerald-400 animate-pulse' : 'text-amber-400'}`} />
            <span className="text-slate-300 font-medium">Elexon Stream:</span>
            <span className={isLive ? 'text-emerald-400' : 'text-amber-400 font-semibold'}>
              {isLive ? 'Online' : 'Offline'}
            </span>
          </div>

          <button
            onClick={onSync}
            disabled={isSyncing}
            className="flex items-center gap-2 text-xs font-semibold px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 active:scale-95 text-white shadow-lg shadow-emerald-950/40 transition-all disabled:opacity-50 cursor-pointer"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isSyncing ? 'animate-spin' : ''}`} />
            <span>{isSyncing ? 'Streaming...' : 'Sync Live'}</span>
          </button>
        </div>
      </div>
    </header>
  );
};
