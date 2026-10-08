/* Domain health in words with its icon: Ahead, On track, At risk, Off track (Above, Met or Below target once
   the quarter is closed). Icon and colour together, the word always with them. */

import { AlertIcon, CheckIcon, MinusIcon, OctagonAlertIcon, TrendDownIcon, TrendUpIcon } from '@/components/Icons';
import { HEALTH, type Health } from '@/lib/theme';

const ICONS = { 'trend-up': TrendUpIcon, check: CheckIcon, alert: AlertIcon, stop: OctagonAlertIcon, 'trend-down': TrendDownIcon, minus: MinusIcon } as const;

export function HealthMark({ status, size = 14 }: { status: Health; size?: number }) {
  const h = HEALTH[status];
  const Icon = ICONS[h.icon];
  return <Icon width={size} height={size} className="shrink-0" style={{ color: h.color }} data-icon={h.icon} />;
}

export default function HealthBadge({ status, size = 'sm', title, className = '' }: { status: Health; size?: 'sm' | 'md'; title?: string; className?: string }) {
  const h = HEALTH[status];
  const pad = size === 'sm' ? 'h-6 gap-1.5 px-2 text-small' : 'h-8 gap-2 px-3 text-body';
  if (status === 'no-target')
    return (
      <span className={`inline-flex items-center whitespace-nowrap text-small text-ink-3 ${className}`} title={title} data-health={status}>
        No target set
      </span>
    );
  return (
    <span
      className={`inline-flex items-center whitespace-nowrap rounded-full border font-semibold ${pad} ${className}`}
      style={{ color: `color-mix(in srgb, ${h.color} 45%, #f2fafc)`, borderColor: `color-mix(in srgb, ${h.color} 45%, transparent)`, background: `color-mix(in srgb, ${h.color} 10%, transparent)` }}
      title={title}
      data-health={status}
    >
      <HealthMark status={status} size={size === 'sm' ? 13 : 15} />
      {h.label}
    </span>
  );
}
