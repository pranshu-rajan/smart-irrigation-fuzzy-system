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
        className="flex items-center justify-center rounded-xl border border-dashed border-slate-200 bg-slate-50 text-xs text-slate-400 font-mono"
      >
        No telemetry data available
      </div>
    );
  }

  return (
    <div className="w-full space-y-2">
      {(title || subtitle) && (
        <div className="flex justify-between items-center text-xs">
          {title && <span className="font-semibold text-slate-800">{title}</span>}
          {subtitle && <span className="text-slate-500">{subtitle}</span>}
        </div>
      )}

      {/* SVG Canvas */}
      <div className="relative w-full overflow-hidden rounded-xl bg-white border border-slate-200/90 shadow-2xs p-2">
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
                  stroke="#f1f5f9"
                  strokeWidth="1"
                />
                <line
                  x1={padding.left}
                  y1={y}
                  x2={chartWidth - padding.right}
                  y2={y}
                  stroke="#e2e8f0"
                  strokeWidth="0.75"
                  strokeDasharray="3 3"
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
              strokeWidth="1.5"
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
              stroke="#059669"
              strokeWidth="1.5"
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
        <div className="flex flex-wrap items-center justify-center gap-4 pt-2 mt-1 border-t border-slate-100 text-xs">
          {normalizedSeries.map((s) => (
            <div key={s.key} className="flex items-center gap-1.5 font-mono text-[11px] text-slate-700">
              <span
                className="h-2 w-4 rounded-full"
                style={{ backgroundColor: s.color }}
              />
              <span className="font-sans font-medium text-slate-700">{s.label}</span>
              {hoverIndex !== null && normalizedData[hoverIndex] && (
                <span className="font-bold text-slate-900 ml-1">
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
