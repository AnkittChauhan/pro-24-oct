import React from 'react';
import { QuantitativeMetrics } from '../types';
import { Gauge, AlertTriangle, Zap, ArrowUpRight, ArrowDownRight, CheckCircle2 } from 'lucide-react';

interface MetricsCardsProps {
  metrics: QuantitativeMetrics | null;
  isLoading?: boolean;
}

export const MetricsCards: React.FC<MetricsCardsProps> = ({ metrics, isLoading }) => {
  if (isLoading || !metrics) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 animate-pulse">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-32 bg-slate-900/60 rounded-2xl border border-slate-800" />
        ))}
      </div>
    );
  }

  const isOverForecast = metrics.mbe > 0;
  const isUnderForecast = metrics.mbe < 0;

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {/* 1. Mean Absolute Error (MAE) */}
      <div className="bg-slate-900/70 border border-slate-800/80 rounded-2xl p-5 shadow-lg relative overflow-hidden backdrop-blur hover:border-slate-700/80 transition-all">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            Forecast MAE
          </span>
          <div className="p-2 rounded-xl bg-blue-500/10 text-blue-400 border border-blue-500/20">
            <Gauge className="w-4 h-4" />
          </div>
        </div>
        <div className="mt-3 flex items-baseline gap-2">
          <span className="text-2xl font-bold font-mono tracking-tight text-white">
            {metrics.mae.toLocaleString(undefined, { minimumFractionDigits: 1, maximumFractionDigits: 1 })}
          </span>
          <span className="text-xs font-medium text-slate-400">MW</span>
        </div>
        <div className="mt-2.5 flex items-center justify-between text-xs">
          <span className="text-slate-400">WAPE Error:</span>
          <span className="font-mono font-semibold px-2 py-0.5 rounded bg-blue-500/15 text-blue-300 border border-blue-500/30">
            {metrics.wape.toFixed(2)}%
          </span>
        </div>
      </div>

      {/* 2. Root Mean Square Error (RMSE) */}
      <div className="bg-slate-900/70 border border-slate-800/80 rounded-2xl p-5 shadow-lg relative overflow-hidden backdrop-blur hover:border-slate-700/80 transition-all">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            Forecast RMSE
          </span>
          <div className="p-2 rounded-xl bg-amber-500/10 text-amber-400 border border-amber-500/20">
            <AlertTriangle className="w-4 h-4" />
          </div>
        </div>
        <div className="mt-3 flex items-baseline gap-2">
          <span className="text-2xl font-bold font-mono tracking-tight text-white">
            {metrics.rmse.toLocaleString(undefined, { minimumFractionDigits: 1, maximumFractionDigits: 1 })}
          </span>
          <span className="text-xs font-medium text-slate-400">MW</span>
        </div>
        <div className="mt-2.5 flex items-center justify-between text-xs">
          <span className="text-slate-400">Penalty Sensitivity:</span>
          <span className="text-slate-300 text-[11px]">
            Peak Deviations
          </span>
        </div>
      </div>

      {/* 3. Directional Bias (MBE) */}
      <div className="bg-slate-900/70 border border-slate-800/80 rounded-2xl p-5 shadow-lg relative overflow-hidden backdrop-blur hover:border-slate-700/80 transition-all">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            Directional Bias (MBE)
          </span>
          <div className={`p-2 rounded-xl border ${
            isOverForecast 
              ? 'bg-amber-500/10 text-amber-400 border-amber-500/20' 
              : isUnderForecast 
              ? 'bg-rose-500/10 text-rose-400 border-rose-500/20' 
              : 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
          }`}>
            {isOverForecast ? (
              <ArrowUpRight className="w-4 h-4" />
            ) : isUnderForecast ? (
              <ArrowDownRight className="w-4 h-4" />
            ) : (
              <CheckCircle2 className="w-4 h-4" />
            )}
          </div>
        </div>
        <div className="mt-3 flex items-baseline gap-2">
          <span className={`text-2xl font-bold font-mono tracking-tight ${
            isOverForecast ? 'text-amber-400' : isUnderForecast ? 'text-rose-400' : 'text-emerald-400'
          }`}>
            {metrics.mbe > 0 ? `+${metrics.mbe.toFixed(1)}` : metrics.mbe.toFixed(1)}
          </span>
          <span className="text-xs font-medium text-slate-400">MW</span>
        </div>
        <div className="mt-2.5 text-xs truncate">
          {isOverForecast ? (
            <span className="text-amber-400/90 font-medium">Over-Forecast (Surplus / Spill Risk)</span>
          ) : isUnderForecast ? (
            <span className="text-rose-400/90 font-medium">Under-Forecast (Thermal Backup Needed)</span>
          ) : (
            <span className="text-emerald-400 font-medium">Zero Systematic Skew</span>
          )}
        </div>
      </div>

      {/* 4. Thermal Procurement Gap */}
      <div className="bg-slate-900/70 border border-slate-800/80 rounded-2xl p-5 shadow-lg relative overflow-hidden backdrop-blur hover:border-slate-700/80 transition-all">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            Procurement Exposure
          </span>
          <div className="p-2 rounded-xl bg-purple-500/10 text-purple-400 border border-purple-500/20">
            <Zap className="w-4 h-4" />
          </div>
        </div>
        <div className="mt-2.5 space-y-1">
          <div className="flex items-center justify-between text-xs">
            <span className="text-rose-400 flex items-center gap-1">
              Shortfall (Buy):
            </span>
            <span className="font-mono font-bold text-rose-300">
              {metrics.netShortfallMwh.toLocaleString()} MWh
            </span>
          </div>
          <div className="flex items-center justify-between text-xs">
            <span className="text-amber-400 flex items-center gap-1">
              Surplus (Sell):
            </span>
            <span className="font-mono font-bold text-amber-300">
              {metrics.netSurplusMwh.toLocaleString()} MWh
            </span>
          </div>
        </div>
        <div className="mt-2 pt-2 border-t border-slate-800/80 flex items-center justify-between text-[11px] text-slate-400">
          <span>Total Generation:</span>
          <span className="font-mono text-slate-300 font-semibold">
            {metrics.totalActualMwh.toLocaleString()} MWh
          </span>
        </div>
      </div>
    </div>
  );
};
