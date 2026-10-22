'use client';

import React from 'react';
import { 
  Play, 
  Pause, 
  RotateCcw, 
  FastForward, 
  Rewind, 
  Sun, 
  Moon, 
  CloudRain, 
  Wind, 
  Thermometer, 
  Droplets,
  Activity
} from 'lucide-react';
import { UseSimulationPlaybackReturn } from '@/hooks/useSimulationPlayback';

interface SimulationScrubberBarProps {
  playback: UseSimulationPlaybackReturn;
  className?: string;
}

export default function SimulationScrubberBar({
  playback,
  className = '',
}: SimulationScrubberBarProps) {
  const {
    currentStep,
    totalSteps,
    currentTimeString,
    isPlaying,
    speed,
    speeds,
    togglePlay,
    seekToStep,
    setSpeed,
    stepForward,
    stepBackward,
    weatherSnapshot,
  } = playback;

  const currentHour = Math.floor(currentStep / 60) % 24;
  const isDaytime = currentHour >= 6 && currentHour < 19;
  const progressPercent = totalSteps > 0 ? (currentStep / totalSteps) * 100 : 0;

  return (
    <div className={`rounded-2xl border border-emerald-500/30 bg-white/95 dark:bg-[#0a120e]/95 backdrop-blur-xl shadow-xl shadow-emerald-950/20 p-4 transition-all ${className}`}>
      {/* Top Header: Play Controls, Timecode, and Live Weather Telemetry */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 pb-3 border-b border-slate-100 dark:border-emerald-950/70">
        {/* Playback Controls & Speed Multipliers */}
        <div className="flex items-center gap-2">
          {/* Play / Pause Button with Radiant Glow */}
          <button
            onClick={togglePlay}
            className={`flex items-center justify-center h-10 w-10 rounded-xl text-white font-bold transition-all shadow-md cursor-pointer ${
              isPlaying
                ? 'bg-amber-500 hover:bg-amber-600 shadow-amber-500/25 ring-2 ring-amber-400/40 animate-pulse'
                : 'bg-gradient-to-br from-emerald-500 to-teal-600 hover:from-emerald-400 hover:to-teal-500 shadow-emerald-500/30'
            }`}
            title={isPlaying ? 'Pause Simulation Telemetry' : 'Play Simulation Telemetry'}
            aria-label={isPlaying ? 'Pause' : 'Play'}
          >
            {isPlaying ? <Pause className="h-4 w-4 fill-current" /> : <Play className="h-4 w-4 fill-current ml-0.5" />}
          </button>

          {/* Step Backward */}
          <button
            onClick={stepBackward}
            className="flex items-center justify-center h-9 w-9 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900 text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors cursor-pointer"
            title="Step Backward (-15 mins)"
            aria-label="Step Backward"
          >
            <Rewind className="h-4 w-4" />
          </button>

          {/* Step Forward */}
          <button
            onClick={stepForward}
            className="flex items-center justify-center h-9 w-9 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900 text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors cursor-pointer"
            title="Step Forward (+15 mins)"
            aria-label="Step Forward"
          >
            <FastForward className="h-4 w-4" />
          </button>

          {/* Reset / Rewind to 00:00 */}
          <button
            onClick={() => seekToStep(0)}
            className="flex items-center justify-center h-9 w-9 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900 text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors cursor-pointer"
            title="Rewind to Beginning (00:00)"
            aria-label="Reset to Start"
          >
            <RotateCcw className="h-3.5 w-3.5" />
          </button>

          {/* Speed Buttons */}
          <div className="flex items-center bg-slate-100 dark:bg-[#070d0a] p-1 rounded-xl border border-slate-200 dark:border-emerald-950/60 ml-1">
            {speeds.map((s) => (
              <button
                key={s}
                onClick={() => setSpeed(s)}
                className={`px-2 py-1 rounded-lg text-xs font-mono font-bold transition-all cursor-pointer ${
                  speed === s
                    ? 'bg-emerald-600 text-white shadow-xs'
                    : 'text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
                }`}
              >
                {s}x
              </button>
            ))}
          </div>

          {/* Time Display */}
          <div className="flex items-center gap-1.5 ml-2">
            {isDaytime ? (
              <Sun className="h-4 w-4 text-amber-500 animate-spin-slow" />
            ) : (
              <Moon className="h-4 w-4 text-indigo-400" />
            )}
            <span className="font-mono text-sm font-extrabold text-slate-900 dark:text-emerald-300">
              {currentTimeString}
            </span>
            <span className="text-[11px] font-mono text-slate-400 dark:text-slate-500">
              / 24:00
            </span>
          </div>
        </div>

        {/* Live Weather & Telemetry Snapshot Ticker */}
        <div className="flex items-center flex-wrap gap-2 text-xs">
          <div className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-slate-100 dark:bg-[#0d1612] border border-slate-200 dark:border-emerald-950/80 text-slate-700 dark:text-slate-300">
            <Thermometer className="h-3.5 w-3.5 text-rose-500" />
            <span className="font-mono font-bold">{weatherSnapshot.tempC.toFixed(1)}°C</span>
          </div>

          <div className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-slate-100 dark:bg-[#0d1612] border border-slate-200 dark:border-emerald-950/80 text-slate-700 dark:text-slate-300">
            <Droplets className="h-3.5 w-3.5 text-sky-500" />
            <span className="font-mono font-bold">{weatherSnapshot.rhPct.toFixed(0)}% RH</span>
          </div>

          <div className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-slate-100 dark:bg-[#0d1612] border border-slate-200 dark:border-emerald-950/80 text-slate-700 dark:text-slate-300">
            <Sun className="h-3.5 w-3.5 text-amber-500" />
            <span className="font-mono font-bold">{weatherSnapshot.solarWm2.toFixed(0)} W/m²</span>
          </div>

          <div className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-slate-100 dark:bg-[#0d1612] border border-slate-200 dark:border-emerald-950/80 text-slate-700 dark:text-slate-300">
            <Wind className="h-3.5 w-3.5 text-teal-500" />
            <span className="font-mono font-bold">{weatherSnapshot.windSpeedMs.toFixed(1)} m/s</span>
          </div>

          <div className="hidden sm:flex items-center gap-1 px-2.5 py-1 rounded-lg bg-emerald-50 dark:bg-emerald-950/60 border border-emerald-200 dark:border-emerald-800 text-emerald-800 dark:text-emerald-300">
            <Activity className="h-3.5 w-3.5 text-emerald-500" />
            <span className="font-mono font-bold">ET₀: {weatherSnapshot.et0Mm.toFixed(2)} mm</span>
          </div>
        </div>
      </div>

      {/* Scrubber Range Slider with Diurnal Phase Gradient */}
      <div className="pt-3 space-y-1.5">
        <div className="relative flex items-center">
          <input
            type="range"
            min={0}
            max={totalSteps || 1440}
            value={currentStep}
            onChange={(e) => seekToStep(Number(e.target.value))}
            className="w-full h-2 bg-slate-200 dark:bg-slate-800 rounded-lg appearance-none cursor-pointer accent-emerald-500 focus:outline-none"
            style={{
              background: `linear-gradient(to right, #10b981 ${progressPercent}%, rgba(100, 116, 139, 0.2) ${progressPercent}%)`,
            }}
          />
        </div>

        {/* Milestone Marks */}
        <div className="flex justify-between text-[10px] font-mono text-slate-400 dark:text-slate-500 px-0.5">
          <span>00:00 (Night)</span>
          <span>06:00 (Dawn)</span>
          <span className="font-bold text-amber-500">12:00 (Peak ET₀)</span>
          <span>18:00 (Dusk)</span>
          <span>24:00 (Midnight)</span>
        </div>
      </div>
    </div>
  );
}
