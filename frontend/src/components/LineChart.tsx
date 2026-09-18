'use client';

import React, { useState, useMemo } from 'react';

export interface Series {
  key: string;
  label: string;
  color: string;
  unit?: string;
  dashed?: boolean;
}

export interface Dataset {
  name: string;
  data: number[];
  color: string;
  dashed?: boolean;
}

export interface LineChartProps {
  title?: string;
  subtitle?: string;
  // Format 1: data + series
  data?: Array<{ x: number | string; [key: string]: any }>;
  series?: Series[];
  // Format 2: labels + datasets
  labels?: (string | number)[];
  datasets?: Dataset[];
  unit?: string;
  height?: number;
  yMin?: number;
  yMax?: number;
  xAxisLabel?: string;
  yAxisLabel?: string;
  referenceLines?: Array<{ y: number; label: string; color: string; dashed?: boolean }>;
}

export default function LineChart({
  title,
  subtitle,
  data: propData,
  series: propSeries,
  labels: propLabels,
  datasets: propDatasets,
  unit,
  height = 240,
  yMin: customYMin,
  yMax: customYMax,
  xAxisLabel = 'Time',
  yAxisLabel,
  referenceLines = [],
}: LineChartProps) {
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);

  // Normalize into standard data and series
  const { normalizedData, normalizedSeries } = useMemo(() => {
    if (propDatasets && propLabels) {
      const s: Series[] = propDatasets.map((ds, idx) => ({
        key: `k_${idx}`,
        label: ds.name,
        color: ds.color,
        dashed: ds.dashed,
        unit: unit,
      }));

      const d = propLabels.map((lbl, i) => {
        const row: Record<string, any> = { x: lbl };
        propDatasets.forEach((ds, idx) => {
          row[`k_${idx}`] = ds.data[i] ?? 0;
        });
        return row;
      });

      return { normalizedData: d, normalizedSeries: s };
    }

    return {
      normalizedData: propData || [],
      normalizedSeries: propSeries || [],
    };
  }, [propData, propSeries, propLabels, propDatasets, unit]);

  const padding = { top: 15, right: 20, bottom: 30, left: 45 };
  const chartWidth = 650;
  const chartHeight = height;

  // Compute min/max
  const { minVal, maxVal } = useMemo(() => {
    let min = Infinity;
    let max = -Infinity;

    normalizedData.forEach((d) => {
      normalizedSeries.forEach((s) => {
        const val = d[s.key];
        if (typeof val === 'number' && !isNaN(val)) {
          if (val < min) min = val;
          if (val > max) max = val;
        }
      });
    });

    if (min === Infinity || max === -Infinity) {
      return { minVal: 0, maxVal: 1 };
    }

    const yMin = customYMin !== undefined ? customYMin : min > 0 ? 0 : min;
    const yMax = customYMax !== undefined ? customYMax : max === min ? max + 1 : max * 1.05;

    return { minVal: yMin, maxVal: yMax };
  }, [normalizedData, normalizedSeries, customYMin, customYMax]);

  const plotWidth = chartWidth - padding.left - padding.right;
  const plotHeight = chartHeight - padding.top - padding.bottom;

  const getX = (index: number) => {
    if (normalizedData.length <= 1) return padding.left;
    return padding.left + (index / (normalizedData.length - 1)) * plotWidth;
  };

  const getY = (val: number) => {
    if (maxVal === minVal) return padding.top + plotHeight / 2;
    const ratio = (val - minVal) / (maxVal - minVal);
    return padding.top + plotHeight - ratio * plotHeight;
  };

  if (normalizedData.length === 0) {
    return (
      <div
        style={{ height }}
        className="flex items-center justify-center rounded-lg border border-slate-800 bg-slate-950 text-xs text-slate-500 font-mono"
      >
        No telemetry data available
      </div>
    );
  }

  return (
    <div className="w-full space-y-2">
      {(title || subtitle) && (
        <div className="flex justify-between items-center text-xs">
          {title && <span className="font-semibold text-white">{title}</span>}
          {subtitle && <span className="text-slate-400">{subtitle}</span>}
        </div>
      )}

      {/* SVG Canvas */}
      <div className="relative w-full overflow-hidden rounded-lg bg-slate-950/80 border border-slate-800/80 p-1">
        <svg
          className="w-full"
          style={{ height }}
          viewBox={`0 0 ${chartWidth} ${chartHeight}`}
          preserveAspectRatio="none"
          onMouseLeave={() => setHoverIndex(null)}
        >
          {/* Y Grid Lines */}
          {[0, 0.25, 0.5, 0.75, 1].map((ratio) => {
            const y = padding.top + plotHeight * ratio;
            const val = maxVal - ratio * (maxVal - minVal);
            return (
              <g key={ratio}>
                <line
                  x1={padding.left}
                  y1={y}
                  x2={chartWidth - padding.right}
                  y2={y}
                  stroke="#334155"
                  strokeWidth="0.5"
                  strokeDasharray="2 2"
                />
                <text
                  x={padding.left - 6}
                  y={y + 3}
                  textAnchor="end"
                  fontSize="9"
                  fill="#64748b"
                  fontFamily="monospace"
                >
                  {val.toFixed(val < 10 && val > -10 ? 1 : 0)}
                </text>
              </g>
            );
          })}

          {/* Reference Lines */}
          {referenceLines.map((ref, idx) => (
            <line
              key={idx}
              x1={padding.left}
              y1={getY(ref.y)}
              x2={chartWidth - padding.right}
              y2={getY(ref.y)}
              stroke={ref.color}
              strokeWidth="1"
              strokeDasharray={ref.dashed ? '4 4' : undefined}
            />
          ))}

          {/* Series Polyline paths */}
          {normalizedSeries.map((s) => {
            const points = normalizedData
              .map((d, i) => {
                const val = d[s.key];
                if (typeof val !== 'number' || isNaN(val)) return null;
                return `${getX(i)},${getY(val)}`;
              })
              .filter(Boolean)
              .join(' ');

            return (
              <polyline
                key={s.key}
                points={points}
                fill="none"
                stroke={s.color}
                strokeWidth="2"
                strokeDasharray={s.dashed ? '4 4' : undefined}
              />
            );
          })}

          {/* Hover tracker */}
          {hoverIndex !== null && hoverIndex < normalizedData.length && (
            <line
              x1={getX(hoverIndex)}
              y1={padding.top}
              x2={getX(hoverIndex)}
              y2={padding.top + plotHeight}
              stroke="#94a3b8"
              strokeWidth="1"
              strokeDasharray="3 3"
            />
          )}

          {/* Interactive Mouse Capture Rects */}
          {normalizedData.map((_, i) => (
            <rect
              key={i}
              x={getX(i) - plotWidth / (normalizedData.length * 2)}
              y={padding.top}
              width={plotWidth / normalizedData.length}
              height={plotHeight}
              fill="transparent"
              onMouseEnter={() => setHoverIndex(i)}
            />
          ))}
        </svg>

        {/* Legend */}
        <div className="flex flex-wrap items-center justify-center gap-4 pt-2 border-t border-slate-900 text-xs">
          {normalizedSeries.map((s) => (
            <div key={s.key} className="flex items-center gap-1.5 font-mono text-[11px] text-slate-300">
              <span
                className="h-2 w-4 rounded-full"
                style={{ backgroundColor: s.color }}
              />
              <span>{s.label}</span>
              {hoverIndex !== null && normalizedData[hoverIndex] && (
                <span className="font-bold text-white ml-1">
                  : {Number(normalizedData[hoverIndex][s.key] ?? 0).toFixed(2)} {s.unit || ''}
                </span>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
