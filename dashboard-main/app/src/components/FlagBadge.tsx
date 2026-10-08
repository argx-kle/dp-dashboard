/* Icon + label, never colour alone. One calm style for every flag: the health colour lives on the
   signal mark and the ring arcs, so flags inform without competing with the numbers. */

import { useSnapshot } from '@/lib/context';
import { FLAG_ICONS, AlertIcon } from '@/components/Icons';
import { flagColor } from '@/lib/theme';

interface Props {
  code: string;
  reason?: string;
  size?: 'sm' | 'md';
  className?: string;
}

export default function FlagBadge({ code, reason, size = 'sm', className = '' }: Props) {
  const s = useSnapshot();
  const def = s.registry.flags.find((f) => f.code === code);
  const Icon = FLAG_ICONS[code] ?? AlertIcon;
  const pad = size === 'sm' ? 'h-6 px-2 text-small' : 'h-8 px-3 text-body';
  return (
    <span className={`inline-flex items-center gap-1.5 whitespace-nowrap rounded-full border border-line-strong font-medium text-ink-2 ${pad} ${className}`} title={reason ?? def?.definition}>
      <Icon width={14} height={14} style={{ color: flagColor(def?.signal) }} />
      {def?.label ?? code}
    </span>
  );
}
