import { useState, useEffect } from 'react';
import { Header } from './components/Header';
import { getHealth } from './services/api';
import { Calendar, Sliders, ShieldCheck, Database } from 'lucide-react';

export function App() {
  const [isLive, setIsLive] = useState(false);
  const [isSyncing, setIsSyncing] = useState(false);
  const [cacheStats, setCacheStats] = useState<{ actuals: number; forecasts: number }>({ actuals: 0, forecasts: 0 });
  const [selectedDate, setSelectedDate] = useState('2026-01-15');
  const [cutoffTime, setCutoffTime] = useState('12:00');

  useEffect(() => {
    checkBackendHealth();
  }, []);

  const checkBackendHealth = async () => {
    try {
      const health = await getHealth();
      setIsLive(health.status === 'healthy');
      if (health.cache_stats) {
        setCacheStats({
          actuals: health.cache_stats.total_actuals_cached,
          forecasts: health.cache_stats.total_forecasts_cached,
        });
      }
    } catch {
      setIsLive(false);
    }
  };

  const handleSync = async () => {
    setIsSyncing(true);
    await checkBackendHealth();
    setTimeout(() => setIsSyncing(false), 800);
  };

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col text-slate-100">
      <Header onSync={handleSync} isSyncing={isSyncing} isLive={isLive} cachedCount={cacheStats} />

      <main className="flex-1 max-w-7xl w-full mx-auto p-6 space-y-6">
        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 shadow-xl backdrop-blur">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 pb-6 border-b border-slate-800">
            <div>
              <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                <Sliders className="w-5 h-5 text-emerald-400" />
                Day-Ahead Auction Decision Parameters
              </h2>
              <p className="text-xs text-slate-400 mt-1">
                Configure target delivery date and gate-closure cutoff time for January 2026 procurement.
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-4">
              <div className="flex items-center gap-2 bg-slate-800/80 px-3 py-2 rounded-xl border border-slate-700/60 text-xs">
                <Calendar className="w-4 h-4 text-emerald-400" />
                <span className="text-slate-400">Target Delivery:</span>
                <input
                  type="date"
                  min="2026-01-01"
                  max="2026-01-31"
                  value={selectedDate}
                  onChange={(e) => setSelectedDate(e.target.value)}
                  className="bg-transparent font-medium text-white focus:outline-none cursor-pointer"
                />
              </div>

              <div className="flex items-center gap-2 bg-slate-800/80 px-3 py-2 rounded-xl border border-slate-700/60 text-xs">
                <span className="text-slate-400">D-1 Cutoff:</span>
                <select
                  value={cutoffTime}
                  onChange={(e) => setCutoffTime(e.target.value)}
                  className="bg-transparent font-medium text-emerald-400 focus:outline-none cursor-pointer"
                >
                  <option value="09:00" className="bg-slate-900 text-white">09:00 UTC (Early Run)</option>
                  <option value="11:00" className="bg-slate-900 text-white">11:00 UTC (NordPool Cutoff)</option>
                  <option value="12:00" className="bg-slate-900 text-white">12:00 UTC (EPEX SPOT Auction)</option>
                  <option value="16:00" className="bg-slate-900 text-white">16:00 UTC (Late Revision)</option>
                </select>
              </div>
            </div>
          </div>

          <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="flex items-center justify-between p-4 rounded-xl bg-emerald-500/5 border border-emerald-500/20">
              <div className="flex items-center gap-3">
                <ShieldCheck className="w-6 h-6 text-emerald-400" />
                <div>
                  <p className="text-sm font-semibold text-emerald-300">
                    Phase 2 Client & Cache Ingestion Ready
                  </p>
                  <p className="text-xs text-slate-400">
                    ElexonClient + SQLite Read-Through Cache active with WAL mode.
                  </p>
                </div>
              </div>
              <span className="text-xs font-mono px-2.5 py-1 rounded bg-slate-800 text-emerald-300 border border-slate-700">
                Phase 2 Complete
              </span>
            </div>

            <div className="flex items-center justify-between p-4 rounded-xl bg-blue-500/5 border border-blue-500/20">
              <div className="flex items-center gap-3">
                <Database className="w-6 h-6 text-blue-400" />
                <div>
                  <p className="text-sm font-semibold text-blue-300">
                    Local Storage Status
                  </p>
                  <p className="text-xs text-slate-400 font-mono">
                    {cacheStats.actuals} actuals | {cacheStats.forecasts} forecasts
                  </p>
                </div>
              </div>
              <span className="text-xs font-mono px-2.5 py-1 rounded bg-slate-800 text-blue-300 border border-slate-700">
                SQLite WAL
              </span>
            </div>
          </div>
        </div>
      </main>

      <footer className="border-t border-slate-800/80 py-4 text-center text-xs text-slate-500">
        UK Energy Utility Pilot • Day-Ahead Renewable Procurement System • January 2026 Elexon Dataset
      </footer>
    </div>
  );
}

export default App;
