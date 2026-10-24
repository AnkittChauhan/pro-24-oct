import React from 'react';
import { MonthlySummaryResponse } from '../types';
import { X, Calendar, BarChart } from 'lucide-react';

interface MonthlySummaryModalProps {
  isOpen: boolean;
  onClose: () => void;
  summary: MonthlySummaryResponse | null;
  cutoffTime: string;
  isLoading?: boolean;
}

export const MonthlySummaryModal: React.FC<MonthlySummaryModalProps> = ({
  isOpen,
  onClose,
  summary,
  cutoffTime,
  isLoading,
}) => {
  if (!isOpen) return null;

  if (isLoading || !summary) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8 max-w-sm w-full text-center">
          <div className="text-emerald-400 font-semibold text-sm">Aggregating January 2026 Monthly Data...</div>
          <div className="text-xs text-slate-400 mt-2">Computing 31 delivery days accuracy KPIs</div>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-slate-900 border border-slate-800 rounded-3xl max-w-4xl w-full max-h-[90vh] overflow-y-auto shadow-2xl flex flex-col">
        {/* Header */}
        <div className="p-6 border-b border-slate-800 flex items-center justify-between sticky top-0 bg-slate-900/95 backdrop-blur z-10">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-blue-500/10 border border-blue-500/20 text-blue-400">
              <Calendar className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white">
                January 2026 Monthly Benchmark Evaluation
              </h2>
              <p className="text-xs text-slate-400">
                Aggregated performance across all 31 wholesale delivery days with D-1 {cutoffTime} UTC gate closure.
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 transition-all cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Top Monthly KPI Row */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-slate-950 p-4 rounded-2xl border border-slate-800/80">
              <span className="text-xs text-slate-400 font-medium">Monthly Avg MAE</span>
              <div className="mt-1 flex items-baseline gap-1.5 font-mono">
                <span className="text-2xl font-bold text-white">
                  {summary.averageMae.toLocaleString()}
                </span>
                <span className="text-xs text-slate-400">MW</span>
              </div>
              <span className="text-[11px] text-blue-400 font-mono mt-1 block">
                Overall WAPE: {summary.overallWape.toFixed(2)}%
              </span>
            </div>

            <div className="bg-slate-950 p-4 rounded-2xl border border-slate-800/80">
              <span className="text-xs text-slate-400 font-medium">Monthly Avg RMSE</span>
              <div className="mt-1 flex items-baseline gap-1.5 font-mono">
                <span className="text-2xl font-bold text-white">
                  {summary.averageRmse.toLocaleString()}
                </span>
                <span className="text-xs text-slate-400">MW</span>
              </div>
              <span className="text-[11px] text-slate-400 mt-1 block">
                Peak Miss Penalty
              </span>
            </div>

            <div className="bg-slate-950 p-4 rounded-2xl border border-slate-800/80">
              <span className="text-xs text-slate-400 font-medium">Directional Bias</span>
              <div className="mt-1 flex items-baseline gap-1.5 font-mono">
                <span className={`text-2xl font-bold ${
                  summary.averageMbe > 0 ? 'text-amber-400' : summary.averageMbe < 0 ? 'text-rose-400' : 'text-emerald-400'
                }`}>
                  {summary.averageMbe > 0 ? `+${summary.averageMbe}` : summary.averageMbe}
                </span>
                <span className="text-xs text-slate-400">MW</span>
              </div>
              <span className="text-[11px] text-slate-400 mt-1 block">
                {summary.averageMbe > 0 ? 'Net Over-Forecast' : 'Net Under-Forecast'}
              </span>
            </div>

            <div className="bg-slate-950 p-4 rounded-2xl border border-slate-800/80">
              <span className="text-xs text-slate-400 font-medium">Net Imbalance Volume</span>
              <div className="mt-1 space-y-0.5 text-xs font-mono">
                <div className="text-rose-400 font-semibold">
                  Buy: {summary.totalShortfallMwh.toLocaleString()} MWh
                </div>
                <div className="text-amber-400 font-semibold">
                  Sell: {summary.totalSurplusMwh.toLocaleString()} MWh
                </div>
              </div>
            </div>
          </div>

          {/* Daily Table Breakdown */}
          <div>
            <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
              <BarChart className="w-4 h-4 text-emerald-400" />
              Day-by-Day Accuracy Performance (January 1 - January 31, 2026)
            </h3>

            <div className="overflow-x-auto max-h-[360px] overflow-y-auto rounded-xl border border-slate-800">
              <table className="w-full text-left border-collapse text-xs font-mono">
                <thead className="bg-slate-950 text-slate-400 sticky top-0 border-b border-slate-800">
                  <tr>
                    <th className="py-2.5 px-3">Delivery Date</th>
                    <th className="py-2.5 px-3 text-right">MAE (MW)</th>
                    <th className="py-2.5 px-3 text-right">RMSE (MW)</th>
                    <th className="py-2.5 px-3 text-right">WAPE (%)</th>
                    <th className="py-2.5 px-3 text-right">Bias (MW)</th>
                    <th className="py-2.5 px-3 text-right">Actual (MWh)</th>
                    <th className="py-2.5 px-3 text-right">Shortfall (MWh)</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {summary.dailySummaries.map((day) => (
                    <tr key={day.date} className="hover:bg-slate-800/40">
                      <td className="py-2 px-3 font-bold text-white">{day.date}</td>
                      <td className="py-2 px-3 text-right text-blue-400 font-semibold">
                        {day.mae.toFixed(1)}
                      </td>
                      <td className="py-2 px-3 text-right text-slate-300">
                        {day.rmse.toFixed(1)}
                      </td>
                      <td className="py-2 px-3 text-right text-emerald-400">
                        {day.wape.toFixed(2)}%
                      </td>
                      <td className={`py-2 px-3 text-right ${day.mbe > 0 ? 'text-amber-400' : 'text-rose-400'}`}>
                        {day.mbe > 0 ? `+${day.mbe.toFixed(1)}` : day.mbe.toFixed(1)}
                      </td>
                      <td className="py-2 px-3 text-right text-slate-300">
                        {day.actualMwh.toLocaleString()}
                      </td>
                      <td className="py-2 px-3 text-right text-rose-400">
                        {day.netShortfallMwh.toLocaleString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-slate-800 bg-slate-950 flex items-center justify-between text-xs text-slate-500">
          <span>UK Power Trading Decision Desk • January 2026 Audit Report</span>
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-medium transition-all cursor-pointer"
          >
            Close Report
          </button>
        </div>
      </div>
    </div>
  );
};
