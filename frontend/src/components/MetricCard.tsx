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
    default: 'border-slate-200 bg-white text-slate-800 shadow-2xs hover:border-slate-300',
    emerald: 'border-emerald-200/80 bg-emerald-50/40 text-emerald-900 shadow-2xs hover:border-emerald-300',
    cyan: 'border-teal-200/80 bg-teal-50/40 text-teal-900 shadow-2xs hover:border-teal-300',
    amber: 'border-amber-200/80 bg-amber-50/40 text-amber-900 shadow-2xs hover:border-amber-300',
    rose: 'border-rose-200/80 bg-rose-50/40 text-rose-900 shadow-2xs hover:border-rose-300',
    purple: 'border-purple-200/80 bg-purple-50/40 text-purple-900 shadow-2xs hover:border-purple-300',
    blue: 'border-sky-200/80 bg-sky-50/40 text-sky-900 shadow-2xs hover:border-sky-300',
  };

  const badgeStyles: Record<string, string> = {
    default: 'bg-slate-100 text-slate-700',
    emerald: 'bg-emerald-100/70 text-emerald-800',
    cyan: 'bg-teal-100/70 text-teal-800',
    amber: 'bg-amber-100/70 text-amber-800',
    rose: 'bg-rose-100/70 text-rose-800',
    purple: 'bg-purple-100/70 text-purple-800',
    blue: 'bg-sky-100/70 text-sky-800',
  };

  const trendIcons = {
    up: '↑',
    down: '↓',
    neutral: '→',
  };

  return (
    <div
      className={`relative overflow-hidden rounded-2xl border p-5 transition-all duration-200 hover:-translate-y-0.5 hover:shadow-sm ${
        variantStyles[resolvedVariant] || variantStyles.default
      }`}
    >
      <div className="flex items-center justify-between gap-2">
        <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
          {displayTitle}
        </div>
        {Icon && (
          <div className={`p-1.5 rounded-lg ${badgeStyles[resolvedVariant] || badgeStyles.default}`}>
            <Icon className="h-4 w-4" />
          </div>
        )}
      </div>

      <div className="mt-2.5 flex items-baseline gap-1.5">
        <span className="text-2xl font-bold tracking-tight text-slate-900 font-mono">{value}</span>
        {unit && <span className="text-xs font-medium text-slate-500">{unit}</span>}
      </div>

      {displaySubtext && (
        <div className="mt-2 flex items-center gap-1.5 text-xs text-slate-500 font-medium">
          {trend && (
            <span
              className={`font-bold ${
                trend === 'up'
                  ? 'text-emerald-600'
                  : trend === 'down'
                  ? 'text-rose-500'
                  : 'text-slate-400'
              }`}
            >
              {trendIcons[trend]}
            </span>
          )}
          <span>{displaySubtext}</span>
        </div>
      )}
    </div>
  );
}
