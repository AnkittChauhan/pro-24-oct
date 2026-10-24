import React, { useState } from 'react';
import {
  ResponsiveContainer,
  ComposedChart,
  Line,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ReferenceLine,
  Area,
} from 'recharts';
import { SettlementPeriodData } from '../types';
import { TrendingUp, BarChart3, Layers } from 'lucide-react';

interface ForecastChartProps {
  series: SettlementPeriodData[];
  isLoading?: boolean;
}

export const ForecastChart: React.FC<ForecastChartProps> = ({ series, isLoading }) => {
  const [chartMode, setChartMode] = useState<'profile' | 'variance' | 'both'>('profile');

  if (isLoading || series.length === 0) {
    return (
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 shadow-xl h-[420px] flex items-center justify-center animate-pulse">
        <div className="text-slate-500 text-sm font-medium">Loading 48-period time-series visualization...</div>
      </div>
    );
  }

  // Format data for Recharts
  const chartData = series.map((item) => {
    const timeLabel = item.startTime.substring(11, 16);
    return {
      period: item.settlementPeriod,
      label: `P${item.settlementPeriod} (${timeLabel})`,
      time: timeLabel,
      actual: item.actualGeneration,
      forecast: item.forecastGeneration,
      variance: item.variance,
      absError: item.absError,
      pctError: item.percentageError,
      // Helper for visual error fill
      positiveVariance: (item.variance ?? 0) > 0 ? item.variance : 0,
      negativeVariance: (item.variance ?? 0) < 0 ? item.variance : 0,
    };
  });

  const CustomTooltip = ({ active, payload }: any) => {
    if (!active || !payload || !payload.length) return null;
    const data = payload[0].payload;
    const varianceVal = data.variance ?? 0;
    const isOver = varianceVal > 0;
    const isUnder = varianceVal < 0;

    return (
      <div className="bg-slate-950/95 border border-slate-700 p-4 rounded-xl shadow-2xl backdrop-blur text-xs min-w-[220px]">
        <div className="flex items-center justify-between pb-2 mb-2 border-b border-slate-800">
          <span className="font-bold text-white text-sm">Settlement Period {data.period}</span>
          <span className="text-slate-400 font-mono">{data.time} UTC</span>
        </div>

        <div className="space-y-1.5 font-mono">
          <div className="flex items-center justify-between">
            <span className="text-emerald-400 flex items-center gap-1.5 font-medium">
              <span className="w-2 h-2 rounded-full bg-emerald-400" />
              Actual Outturn:
            </span>
            <span className="text-white font-bold">
              {data.actual !== null ? `${data.actual.toLocaleString()} MW` : 'N/A'}
            </span>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-amber-400 flex items-center gap-1.5 font-medium">
              <span className="w-2 h-2 rounded-full bg-amber-400" />
              D-1 Forecast:
            </span>
            <span className="text-white font-bold">
              {data.forecast !== null ? `${data.forecast.toLocaleString()} MW` : 'N/A'}
            </span>
          </div>

          <div className="pt-2 mt-2 border-t border-slate-800 flex items-center justify-between">
            <span className="text-slate-400">Delta (F - A):</span>
            <span className={`font-bold ${isOver ? 'text-amber-400' : isUnder ? 'text-rose-400' : 'text-slate-300'}`}>
              {varianceVal > 0 ? `+${varianceVal.toFixed(1)}` : varianceVal.toFixed(1)} MW
            </span>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-slate-400">Abs % Error:</span>
            <span className="text-slate-200 font-bold">
              {data.pctError !== null ? `${data.pctError.toFixed(2)}%` : 'N/A'}
            </span>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 shadow-xl backdrop-blur">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-800/80">
        <div>
          <h3 className="text-base font-semibold text-white flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-emerald-400" />
            48-Period Wind Generation & Day-Ahead Forecast Curve
          </h3>
          <p className="text-xs text-slate-400 mt-1">
            Comparing FUELHH actual generation outturn against the latest WINDFOR forecast locked prior to gate closure.
          </p>
        </div>

        {/* View Mode Toggle */}
        <div className="flex items-center gap-1 bg-slate-950 p-1 rounded-xl border border-slate-800 text-xs">
          <button
            onClick={() => setChartMode('profile')}
            className={`px-3 py-1.5 rounded-lg font-medium transition-all cursor-pointer flex items-center gap-1.5 ${
              chartMode === 'profile'
                ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            Profiles (MW)
          </button>
          <button
            onClick={() => setChartMode('variance')}
            className={`px-3 py-1.5 rounded-lg font-medium transition-all cursor-pointer flex items-center gap-1.5 ${
              chartMode === 'variance'
                ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <BarChart3 className="w-3.5 h-3.5" />
            Error Deltas (MW)
          </button>
          <button
            onClick={() => setChartMode('both')}
            className={`px-3 py-1.5 rounded-lg font-medium transition-all cursor-pointer ${
              chartMode === 'both'
                ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Combined
          </button>
        </div>
      </div>

      <div className="h-[380px] w-full pt-4">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={chartData} margin={{ top: 10, right: 20, left: 10, bottom: 0 }}>
            <defs>
              <linearGradient id="actualGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#10b981" stopOpacity={0.25} />
                <stop offset="95%" stopColor="#10b981" stopOpacity={0.0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.4} />
            <XAxis
              dataKey="period"
              stroke="#64748b"
              fontSize={11}
              tickFormatter={(period) => (period % 4 === 1 ? `P${period}` : '')}
            />
            <YAxis
              yAxisId="power"
              stroke="#64748b"
              fontSize={11}
              domain={['auto', 'auto']}
              tickFormatter={(val) => `${(val / 1000).toFixed(0)}k`}
              unit=" MW"
            />
            {(chartMode === 'variance' || chartMode === 'both') && (
              <YAxis
                yAxisId="delta"
                orientation="right"
                stroke="#94a3b8"
                fontSize={11}
                tickFormatter={(val) => `${val > 0 ? '+' : ''}${val}`}
                unit=" MW"
              />
            )}
            <Tooltip content={<CustomTooltip />} />
            <Legend
              verticalAlign="top"
              height={36}
              iconType="circle"
              wrapperStyle={{ fontSize: '12px', paddingBottom: '10px' }}
            />
            <ReferenceLine yAxisId="power" y={0} stroke="#475569" />

            {/* Error Delta Bars */}
            {(chartMode === 'variance' || chartMode === 'both') && (
              <Bar
                yAxisId={chartMode === 'variance' ? 'power' : 'delta'}
                dataKey="variance"
                name="Forecast Delta (MW)"
                fill="#818cf8"
                opacity={0.65}
                radius={[4, 4, 0, 0]}
              />
            )}

            {/* Actual Outturn Curve */}
            {(chartMode === 'profile' || chartMode === 'both') && (
              <Area
                yAxisId="power"
                type="monotone"
                dataKey="actual"
                name="Actual Wind Outturn (FUELHH)"
                stroke="#10b981"
                strokeWidth={2.5}
                fillOpacity={1}
                fill="url(#actualGrad)"
              />
            )}

            {/* Forecast Curve */}
            {(chartMode === 'profile' || chartMode === 'both') && (
              <Line
                yAxisId="power"
                type="monotone"
                dataKey="forecast"
                name="Day-Ahead Forecast (WINDFOR)"
                stroke="#f59e0b"
                strokeWidth={2.2}
                strokeDasharray="4 4"
                dot={{ r: 2, fill: '#f59e0b' }}
                activeDot={{ r: 6 }}
              />
            )}
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      <div className="mt-3 flex flex-wrap items-center justify-between text-xs text-slate-400 border-t border-slate-800/80 pt-3">
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-1.5">
            <span className="w-3 h-0.5 bg-emerald-400" /> Actual Generation (FUELHH)
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-3 h-0.5 border-t border-dashed border-amber-400" /> D-1 Forecast (WINDFOR)
          </span>
        </div>
        <span className="font-mono text-slate-500">48 half-hourly periods • 00:00 - 23:30 UTC</span>
      </div>
    </div>
  );
};
