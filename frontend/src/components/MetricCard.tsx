import React from 'react';

export interface MetricCardProps {
  label?: string;
  title?: string;
  value: string | number;
  unit?: string;
  subtext?: string;
  change?: string;
  icon?: React.ComponentType<{ className?: string }>;
  variant?: 'default' | 'emerald' | 'cyan' | 'amber' | 'rose' | 'purple' | 'blue';
  color?: string;
  trend?: 'up' | 'down' | 'neutral';
}

export default function MetricCard({
  label,
  title,
  value,
  unit,
  subtext,
  change,
  icon: Icon,
  variant,
  color,
  trend,
}: MetricCardProps) {
  const displayTitle = title || label || 'Metric';
  const displaySubtext = change || subtext;

  const resolvedVariant = variant || (color as any) || 'default';

  const variantStyles: Record<string, string> = {
    default: 'border-slate-800 bg-slate-900/60 text-slate-200',
    emerald: 'border-emerald-500/30 bg-emerald-950/20 text-emerald-400',
    cyan: 'border-cyan-500/30 bg-cyan-950/20 text-cyan-400',
    amber: 'border-amber-500/30 bg-amber-950/20 text-amber-400',
    rose: 'border-rose-500/30 bg-rose-950/20 text-rose-400',
    purple: 'border-purple-500/30 bg-purple-950/20 text-purple-400',
    blue: 'border-blue-500/30 bg-blue-950/20 text-blue-400',
  };

  const textStyles: Record<string, string> = {
    default: 'text-white',
    emerald: 'text-emerald-400',
    cyan: 'text-cyan-400',
    amber: 'text-amber-400',
    rose: 'text-rose-400',
    purple: 'text-purple-400',
    blue: 'text-blue-400',
  };

  const trendIcons = {
    up: '↑',
    down: '↓',
    neutral: '→',
  };

  return (
    <div
      className={`rounded-xl border p-4 backdrop-blur-sm transition-all hover:border-slate-700 ${
        variantStyles[resolvedVariant] || variantStyles.default
      }`}
    >
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium uppercase tracking-wider text-slate-400">
          {displayTitle}
        </span>
        {Icon && <Icon className="h-4 w-4 opacity-75" />}
      </div>
      <div className="mt-2 flex items-baseline gap-1.5">
        <span
          className={`text-2xl font-bold tracking-tight font-mono ${
            textStyles[resolvedVariant] || textStyles.default
          }`}
        >
          {value}
        </span>
        {unit && <span className="text-xs text-slate-400 font-mono">{unit}</span>}
      </div>
      {displaySubtext && (
        <p className="mt-1 flex items-center gap-1 text-xs text-slate-400 font-light truncate">
          {trend && (
            <span
              className={
                trend === 'up'
                  ? 'text-emerald-400'
                  : trend === 'down'
                  ? 'text-rose-400'
                  : 'text-slate-400'
              }
            >
              {trendIcons[trend]}
            </span>
          )}
          <span>{displaySubtext}</span>
        </p>
      )}
    </div>
  );
}
