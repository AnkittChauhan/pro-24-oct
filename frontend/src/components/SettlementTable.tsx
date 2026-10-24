import React, { useState } from 'react';
import { SettlementPeriodData } from '../types';
import { Table, Download, Filter, CheckCircle, AlertOctagon, AlertCircle } from 'lucide-react';

interface SettlementTableProps {
  series: SettlementPeriodData[];
  deliveryDate: string;
}

export const SettlementTable: React.FC<SettlementTableProps> = ({ series, deliveryDate }) => {
  const [filter, setFilter] = useState<'all' | 'shortfall' | 'surplus' | 'large_error'>('all');

  const filteredSeries = series.filter((item) => {
    if (filter === 'shortfall') return (item.variance ?? 0) < -200;
    if (filter === 'surplus') return (item.variance ?? 0) > 200;
    if (filter === 'large_error') return (item.absError ?? 0) >= 1000;
    return true;
  });

  const handleExportCSV = () => {
    const headers = [
      'SettlementPeriod',
      'StartTime',
      'ActualGenerationMW',
      'ForecastGenerationMW',
      'ForecastPublishTime',
      'VarianceMW',
      'AbsErrorMW',
      'PercentageError',
    ];

    const rows = series.map((s) => [
      s.settlementPeriod,
      s.startTime,
      s.actualGeneration ?? '',
      s.forecastGeneration ?? '',
      s.forecastPublishTime ?? '',
      s.variance ?? '',
      s.absError ?? '',
      s.percentageError ?? '',
    ]);

    const csvContent =
      'data:text/csv;charset=utf-8,' +
      [headers.join(','), ...rows.map((e) => e.join(','))].join('\n');

    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `uk_wind_day_ahead_${deliveryDate}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const getStatusBadge = (item: SettlementPeriodData) => {
    const variance = item.variance ?? 0;
    const absErr = item.absError ?? 0;

    if (absErr <= 400 || (item.percentageError !== null && item.percentageError <= 4.0)) {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
          <CheckCircle className="w-3 h-3" />
          Balanced Target
        </span>
      );
    }
    if (variance < 0) {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-rose-500/10 text-rose-400 border border-rose-500/20">
          <AlertOctagon className="w-3 h-3" />
          Shortfall Exposure
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-amber-500/10 text-amber-400 border border-amber-500/20">
        <AlertCircle className="w-3 h-3" />
        Surplus Exposure
      </span>
    );
  };

  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 shadow-xl backdrop-blur">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-800/80">
        <div>
          <h3 className="text-base font-semibold text-white flex items-center gap-2">
            <Table className="w-5 h-5 text-emerald-400" />
            48 Settlement Periods Audit & Imbalance Breakdown
          </h3>
          <p className="text-xs text-slate-400 mt-1">
            Granular half-hourly outturn, matched Day-Ahead forecast snapshot, and individual volume exposures.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {/* Filters */}
          <div className="flex items-center gap-1 bg-slate-950 p-1 rounded-xl border border-slate-800 text-xs">
            <Filter className="w-3.5 h-3.5 text-slate-400 ml-2" />
            <button
              onClick={() => setFilter('all')}
              className={`px-2.5 py-1 rounded-lg transition-all cursor-pointer ${
                filter === 'all' ? 'bg-slate-800 text-white font-semibold' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              All ({series.length})
            </button>
            <button
              onClick={() => setFilter('shortfall')}
              className={`px-2.5 py-1 rounded-lg transition-all cursor-pointer ${
                filter === 'shortfall' ? 'bg-rose-500/20 text-rose-300 font-semibold' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Shortfall
            </button>
            <button
              onClick={() => setFilter('surplus')}
              className={`px-2.5 py-1 rounded-lg transition-all cursor-pointer ${
                filter === 'surplus' ? 'bg-amber-500/20 text-amber-300 font-semibold' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Surplus
            </button>
            <button
              onClick={() => setFilter('large_error')}
              className={`px-2.5 py-1 rounded-lg transition-all cursor-pointer ${
                filter === 'large_error' ? 'bg-purple-500/20 text-purple-300 font-semibold' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Misses &gt;1GW
            </button>
          </div>

          {/* Export Button */}
          <button
            onClick={handleExportCSV}
            className="flex items-center gap-1.5 text-xs font-semibold px-3 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700/60 transition-all cursor-pointer"
          >
            <Download className="w-3.5 h-3.5" />
            Export CSV
          </button>
        </div>
      </div>

      <div className="mt-4 overflow-x-auto max-h-[460px] overflow-y-auto rounded-xl border border-slate-800">
        <table className="w-full text-left border-collapse text-xs">
          <thead className="bg-slate-950/90 text-slate-400 sticky top-0 z-10 border-b border-slate-800">
            <tr>
              <th className="py-3 px-4 font-semibold">Period</th>
              <th className="py-3 px-4 font-semibold">Time (UTC)</th>
              <th className="py-3 px-4 font-semibold text-right">Actual (MW)</th>
              <th className="py-3 px-4 font-semibold text-right">D-1 Forecast (MW)</th>
              <th className="py-3 px-4 font-semibold text-right">Variance (MW)</th>
              <th className="py-3 px-4 font-semibold text-right">Abs Error (MW)</th>
              <th className="py-3 px-4 font-semibold text-right">% Error</th>
              <th className="py-3 px-4 font-semibold text-center">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 font-mono">
            {filteredSeries.map((item) => {
              const timeLabel = item.startTime.substring(11, 16);
              const variance = item.variance ?? 0;
              const isOver = variance > 0;
              const isUnder = variance < 0;

              return (
                <tr key={item.settlementPeriod} className="hover:bg-slate-800/40 transition-colors">
                  <td className="py-2.5 px-4 font-bold text-slate-300">
                    #{item.settlementPeriod}
                  </td>
                  <td className="py-2.5 px-4 text-slate-400">
                    {timeLabel}
                  </td>
                  <td className="py-2.5 px-4 text-right font-semibold text-emerald-400">
                    {item.actualGeneration !== null ? item.actualGeneration.toLocaleString() : 'N/A'}
                  </td>
                  <td className="py-2.5 px-4 text-right font-semibold text-amber-400">
                    {item.forecastGeneration !== null ? item.forecastGeneration.toLocaleString() : 'N/A'}
                  </td>
                  <td className={`py-2.5 px-4 text-right font-bold ${
                    isOver ? 'text-amber-400' : isUnder ? 'text-rose-400' : 'text-slate-300'
                  }`}>
                    {variance > 0 ? `+${variance.toFixed(1)}` : variance.toFixed(1)}
                  </td>
                  <td className="py-2.5 px-4 text-right text-slate-300">
                    {item.absError !== null ? item.absError.toFixed(1) : 'N/A'}
                  </td>
                  <td className="py-2.5 px-4 text-right text-slate-300">
                    {item.percentageError !== null ? `${item.percentageError.toFixed(2)}%` : 'N/A'}
                  </td>
                  <td className="py-2.5 px-4 text-center">
                    {getStatusBadge(item)}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
