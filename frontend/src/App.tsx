import { useState, useEffect } from 'react';
import { Header } from './components/Header';
import { DateControls } from './components/DateControls';
import { MetricsCards } from './components/MetricsCards';
import { ForecastChart } from './components/ForecastChart';
import { SettlementTable } from './components/SettlementTable';
import { MonthlySummaryModal } from './components/MonthlySummaryModal';
import { getHealth, getDayAheadData, getDates, getMonthlySummary } from './services/api';
import { DayAheadResponse, MonthlySummaryResponse } from './types';
import { BarChart3, AlertCircle } from 'lucide-react';

export function App() {
  const [isLive, setIsLive] = useState(false);
  const [isSyncing, setIsSyncing] = useState(false);
  const [cacheStats, setCacheStats] = useState<{ actuals: number; forecasts: number }>({ actuals: 0, forecasts: 0 });
  const [selectedDate, setSelectedDate] = useState('2026-01-15');
  const [cutoffTime, setCutoffTime] = useState('12:00');
  const [availableCutoffs, setAvailableCutoffs] = useState<string[]>(['09:00', '11:00', '12:00', '16:00']);

  // Data states
  const [dayAheadData, setDayAheadData] = useState<DayAheadResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Monthly summary modal state
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [monthlySummary, setMonthlySummary] = useState<MonthlySummaryResponse | null>(null);
  const [isLoadingMonthly, setIsLoadingMonthly] = useState(false);

  useEffect(() => {
    checkHealthAndInit();
  }, []);

  useEffect(() => {
    fetchDayAheadEvaluation(selectedDate, cutoffTime);
  }, [selectedDate, cutoffTime]);

  const checkHealthAndInit = async () => {
    try {
      const health = await getHealth();
      setIsLive(health.status === 'healthy');
      if (health.cache_stats) {
        setCacheStats({
          actuals: health.cache_stats.total_actuals_cached,
          forecasts: health.cache_stats.total_forecasts_cached,
        });
      }

      const datesRes = await getDates();
      if (datesRes.availableCutoffs) {
        setAvailableCutoffs(datesRes.availableCutoffs);
      }
    } catch {
      setIsLive(false);
    }
  };

  const fetchDayAheadEvaluation = async (date: string, cutoff: string, force: boolean = false) => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await getDayAheadData(date, cutoff, force);
      setDayAheadData(data);
    } catch (err: any) {
      setError(err?.response?.data?.detail || err.message || 'Failed to load day-ahead data.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSync = async () => {
    setIsSyncing(true);
    await checkHealthAndInit();
    await fetchDayAheadEvaluation(selectedDate, cutoffTime, true);
    setIsSyncing(false);
  };

  const handleOpenMonthlyReport = async () => {
    setIsModalOpen(true);
    setIsLoadingMonthly(true);
    try {
      const summary = await getMonthlySummary(cutoffTime);
      setMonthlySummary(summary);
    } catch (err) {
      console.error('Failed to load monthly summary', err);
    } finally {
      setIsLoadingMonthly(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col text-slate-100 font-sans selection:bg-emerald-500/20 selection:text-emerald-300">
      <Header
        onSync={handleSync}
        isSyncing={isSyncing}
        isLive={isLive}
        cachedCount={cacheStats}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 space-y-6">
        {/* Error Banner */}
        {error && (
          <div className="p-4 rounded-2xl bg-rose-500/10 border border-rose-500/30 flex items-center justify-between gap-3 text-rose-300 text-xs">
            <div className="flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
              <span>{error}</span>
            </div>
            <button
              onClick={() => fetchDayAheadEvaluation(selectedDate, cutoffTime, false)}
              className="px-3 py-1 rounded-lg bg-rose-500/20 hover:bg-rose-500/30 text-rose-200 font-medium cursor-pointer transition-all"
            >
              Retry
            </button>
          </div>
        )}

        {/* 1. Decision Controls Bar */}
        <DateControls
          selectedDate={selectedDate}
          onDateChange={setSelectedDate}
          cutoffTime={cutoffTime}
          onCutoffChange={setCutoffTime}
          availableCutoffs={availableCutoffs}
          isCached={dayAheadData?.cached}
        />

        {/* Action bar for Monthly Evaluation */}
        <div className="flex items-center justify-between text-xs px-2">
          <div className="flex items-center gap-2 text-slate-400 font-mono">
            <span>Evaluating Target:</span>
            <span className="font-bold text-emerald-400">{selectedDate}</span>
            <span>• Cutoff:</span>
            <span className="font-bold text-amber-400">{cutoffTime} UTC</span>
          </div>

          <button
            onClick={handleOpenMonthlyReport}
            className="flex items-center gap-2 px-3.5 py-1.5 rounded-xl bg-slate-900 border border-slate-800 hover:border-slate-700 text-blue-400 hover:text-blue-300 font-medium transition-all cursor-pointer shadow-sm"
          >
            <BarChart3 className="w-3.5 h-3.5" />
            <span>January 2026 Monthly Benchmark Report</span>
          </button>
        </div>

        {/* 2. Executive KPI Summary Cards */}
        <MetricsCards metrics={dayAheadData?.metrics || null} isLoading={isLoading} />

        {/* 3. Interactive Dual-Axis Recharts Visualization */}
        <ForecastChart series={dayAheadData?.series || []} isLoading={isLoading} />

        {/* 4. Granular 48 Settlement Periods Audit Table */}
        <SettlementTable series={dayAheadData?.series || []} deliveryDate={selectedDate} />
      </main>

      {/* Monthly Summary Modal */}
      <MonthlySummaryModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        summary={monthlySummary}
        cutoffTime={cutoffTime}
        isLoading={isLoadingMonthly}
      />

      <footer className="border-t border-slate-800/80 py-4 px-6 text-center text-xs text-slate-500 flex flex-col sm:flex-row items-center justify-between max-w-7xl mx-auto w-full">
        <span>UK Energy Utility Trading Platform • Day-Ahead Wind Forecast Evaluation Desk</span>
        <span className="font-mono text-slate-600 mt-1 sm:mt-0">Elexon BMRS FUELHH & WINDFOR Stream</span>
      </footer>
    </div>
  );
}

export default App;
