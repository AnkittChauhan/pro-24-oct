import React from 'react';
import { Calendar, Sliders, ChevronLeft, ChevronRight, Sparkles, Clock } from 'lucide-react';

interface DateControlsProps {
  selectedDate: string;
  onDateChange: (date: string) => void;
  cutoffTime: string;
  onCutoffChange: (cutoff: string) => void;
  availableCutoffs: string[];
  isCached?: boolean;
}

export const DateControls: React.FC<DateControlsProps> = ({
  selectedDate,
  onDateChange,
  cutoffTime,
  onCutoffChange,
  availableCutoffs,
  isCached,
}) => {
  // Quick day navigation
  const dayNum = parseInt(selectedDate.split('-')[2] || '15', 10);

  const handlePrevDay = () => {
    if (dayNum > 1) {
      const nextDayStr = `2026-01-${String(dayNum - 1).padStart(2, '0')}`;
      onDateChange(nextDayStr);
    }
  };

  const handleNextDay = () => {
    if (dayNum < 31) {
      const nextDayStr = `2026-01-${String(dayNum + 1).padStart(2, '0')}`;
      onDateChange(nextDayStr);
    }
  };

  const scenarios = [
    { label: 'Jan 08 (Calm Anticyclone)', date: '2026-01-08' },
    { label: 'Jan 15 (Storm Peak)', date: '2026-01-15' },
    { label: 'Jan 22 (High Volatility)', date: '2026-01-22' },
  ];

  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 shadow-xl backdrop-blur space-y-5">
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 pb-5 border-b border-slate-800/80">
        <div>
          <h2 className="text-base font-semibold text-white flex items-center gap-2">
            <Sliders className="w-5 h-5 text-emerald-400" />
            Wholesale Gate-Closure & Delivery Parameters
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Configure auction gate closure on Day D-1 to simulate procurement decision accuracy for January 2026.
          </p>
        </div>

        {/* Date Selector & Nav */}
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-1 bg-slate-950 p-1 rounded-xl border border-slate-800">
            <button
              onClick={handlePrevDay}
              disabled={dayNum <= 1}
              className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 disabled:opacity-30 disabled:cursor-not-allowed transition-all cursor-pointer"
              title="Previous Day"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>

            <div className="flex items-center gap-2 px-3 py-1 text-xs">
              <Calendar className="w-4 h-4 text-emerald-400" />
              <span className="text-slate-400">Delivery:</span>
              <input
                type="date"
                min="2026-01-01"
                max="2026-01-31"
                value={selectedDate}
                onChange={(e) => onDateChange(e.target.value)}
                className="bg-transparent font-medium text-white focus:outline-none cursor-pointer font-mono"
              />
            </div>

            <button
              onClick={handleNextDay}
              disabled={dayNum >= 31}
              className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 disabled:opacity-30 disabled:cursor-not-allowed transition-all cursor-pointer"
              title="Next Day"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>

          {/* Quick Scenario Jumps */}
          <div className="hidden sm:flex items-center gap-1.5 text-xs">
            <Sparkles className="w-3.5 h-3.5 text-amber-400" />
            <span className="text-slate-500">Preset:</span>
            {scenarios.map((sc) => (
              <button
                key={sc.date}
                onClick={() => onDateChange(sc.date)}
                className={`px-2.5 py-1 rounded-lg border text-[11px] font-medium transition-all cursor-pointer ${
                  selectedDate === sc.date
                    ? 'bg-amber-500/15 text-amber-300 border-amber-500/30'
                    : 'bg-slate-950/80 text-slate-400 border-slate-800 hover:text-slate-200'
                }`}
              >
                {sc.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Decision Cut-Off Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-2 text-xs text-slate-300">
          <Clock className="w-4 h-4 text-blue-400" />
          <span className="font-semibold text-white">D-1 Gate Closure:</span>
          <span className="text-slate-400">
            Cutoff deadline on Day D-1 prior to delivery
          </span>
          {isCached && (
            <span className="ml-2 font-mono text-[10px] px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              Cached
            </span>
          )}
        </div>

        {/* Cutoff Selector Segmented Control */}
        <div className="flex flex-wrap items-center gap-1.5 bg-slate-950 p-1.5 rounded-xl border border-slate-800 text-xs">
          {availableCutoffs.map((cutoff) => {
            const isSelected = cutoffTime === cutoff;
            const labels: Record<string, string> = {
              '09:00': '09:00 UTC (Early Run)',
              '11:00': '11:00 UTC (NordPool)',
              '12:00': '12:00 UTC (EPEX SPOT)',
              '16:00': '16:00 UTC (Late Update)',
            };
            return (
              <button
                key={cutoff}
                onClick={() => onCutoffChange(cutoff)}
                className={`px-3 py-1.5 rounded-lg font-medium transition-all cursor-pointer ${
                  isSelected
                    ? 'bg-blue-600 text-white font-semibold shadow-md shadow-blue-900/30'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {labels[cutoff] || `${cutoff} UTC`}
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
};
