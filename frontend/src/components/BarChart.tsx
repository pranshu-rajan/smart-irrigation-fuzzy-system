'use client';

import React from 'react';

export interface BarDataset {
  name: string;
  data: number[];
  color?: string;
}

export interface BarItem {
  label: string;
  value: number;
  target?: number;
  color?: string;
  unit?: string;
}

export interface BarChartProps {
  title?: string;
  subtitle?: string;
  // Format 1: simple items
  data?: BarItem[];
  // Format 2: multi-dataset with labels
  labels?: string[];
  datasets?: BarDataset[];
  maxValue?: number;
  height?: number;
}

export default function BarChart({
  title,
  subtitle,
  data: propData,
  labels: propLabels,
  datasets: propDatasets,
  maxValue: customMax,
  height = 240,
}: BarChartProps) {
  // If Format 2 (labels + datasets)
  if (propLabels && propDatasets) {
    const allValues = propDatasets.flatMap((ds) => ds.data);
    const max = customMax || Math.max(...allValues, 1);

    return (
      <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-4 backdrop-blur-sm space-y-4">
        {(title || subtitle) && (
          <div>
            {title && <h3 className="text-sm font-semibold text-slate-100">{title}</h3>}
            {subtitle && <p className="text-xs text-slate-400">{subtitle}</p>}
          </div>
        )}

        <div className="space-y-4">
          {propLabels.map((lbl, i) => (
            <div key={lbl} className="space-y-1.5">
              <span className="text-xs font-mono font-medium text-slate-300 block">{lbl}</span>
              <div className="space-y-1">
                {propDatasets.map((ds) => {
                  const val = ds.data[i] ?? 0;
                  const pct = Math.min(100, Math.max(0, (val / max) * 100));
                  return (
                    <div key={ds.name} className="flex items-center gap-3 text-xs font-mono">
                      <div className="h-2 flex-1 rounded-full bg-slate-800 overflow-hidden">
                        <div
                          className="h-full rounded-full transition-all duration-500"
                          style={{
                            width: `${pct}%`,
                            backgroundColor: ds.color || '#10b981',
                          }}
                        />
                      </div>
                      <span className="w-20 text-right text-slate-300 text-[11px]">
                        {val.toFixed(1)}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>

        {/* Legend */}
        <div className="flex flex-wrap items-center justify-center gap-4 pt-2 border-t border-slate-800 text-xs">
          {propDatasets.map((ds) => (
            <div key={ds.name} className="flex items-center gap-1.5 font-mono text-[11px] text-slate-300">
              <span
                className="h-2 w-3 rounded-full"
                style={{ backgroundColor: ds.color || '#10b981' }}
              />
              <span>{ds.name}</span>
            </div>
          ))}
        </div>
      </div>
    );
  }

  // Format 1 (simple data list)
  const items = propData || [];
  const max = customMax || Math.max(...items.map((d) => Math.max(d.value, d.target || 0)), 1);

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-4 backdrop-blur-sm space-y-4">
      {(title || subtitle) && (
        <div>
          {title && <h3 className="text-sm font-semibold text-slate-100">{title}</h3>}
          {subtitle && <p className="text-xs text-slate-400">{subtitle}</p>}
        </div>
      )}

      <div className="space-y-3">
        {items.map((item, idx) => {
          const pct = Math.min(100, Math.max(0, (item.value / max) * 100));
          const targetPct = item.target !== undefined ? Math.min(100, (item.target / max) * 100) : null;
          const barColor = item.color || '#10b981';

          return (
            <div key={idx} className="space-y-1.5">
              <div className="flex items-center justify-between text-xs font-mono">
                <span className="font-medium text-slate-300">{item.label}</span>
                <span className="text-slate-200 font-bold">
                  {item.value.toLocaleString()} {item.unit || ''}
                  {item.target !== undefined && (
                    <span className="text-slate-500 font-normal ml-1">
                      / {item.target.toLocaleString()}
                    </span>
                  )}
                </span>
              </div>
              <div className="relative h-2.5 w-full rounded-full bg-slate-800 overflow-hidden">
                <div
                  className="h-full rounded-full transition-all duration-500"
                  style={{ width: `${pct}%`, backgroundColor: barColor }}
                />
                {targetPct !== null && (
                  <div
                    className="absolute top-0 bottom-0 w-0.5 bg-white/70"
                    style={{ left: `${targetPct}%` }}
                    title={`Target: ${item.target}`}
                  />
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
