import React from 'react';
import { CheckCircle2, Clock, RefreshCw, AlertTriangle, XCircle, Skull } from 'lucide-react';

const STATUS_CONFIGS = {
  SUCCESS: {
    label: 'SUCCESS',
    bg: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
    icon: CheckCircle2,
  },
  PENDING: {
    label: 'PENDING',
    bg: 'bg-slate-500/10 text-slate-400 border-slate-500/20',
    icon: Clock,
  },
  PROCESSING: {
    label: 'PROCESSING',
    bg: 'bg-blue-500/10 text-blue-400 border-blue-500/20 animate-pulse',
    icon: RefreshCw,
  },
  RETRY_SCHEDULED: {
    label: 'RETRY SCHEDULED',
    bg: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
    icon: AlertTriangle,
  },
  FAILED: {
    label: 'FAILED',
    bg: 'bg-rose-500/10 text-rose-400 border-rose-500/20',
    icon: XCircle,
  },
  DEAD_LETTERED: {
    label: 'DEAD LETTERED',
    bg: 'bg-purple-500/10 text-purple-400 border-purple-500/20',
    icon: Skull,
  },
};

export default function StatusBadge({ status, size = 'sm' }) {
  const normalized = status ? status.toUpperCase() : 'PENDING';
  const cfg = STATUS_CONFIGS[normalized] || STATUS_CONFIGS.PENDING;
  const Icon = cfg.icon;

  const sizeClasses = size === 'xs'
    ? 'px-2 py-0.5 text-[10px] gap-1'
    : 'px-2.5 py-1 text-xs gap-1.5 font-medium';

  return (
    <span
      className={`inline-flex items-center rounded-full border font-mono tracking-wider transition-colors ${cfg.bg} ${sizeClasses}`}
    >
      <Icon className={size === 'xs' ? 'w-2.5 h-2.5' : 'w-3.5 h-3.5'} />
      {cfg.label}
    </span>
  );
}

