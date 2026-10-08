/* Inline icons: no third-party assets (plan guardrail). Each is decorative; text labels carry meaning. */

import type { ReactElement, SVGProps } from 'react';

type P = SVGProps<SVGSVGElement>;
const base = (props: P) => ({ width: 14, height: 14, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', strokeWidth: 2.2, strokeLinecap: 'round' as const, strokeLinejoin: 'round' as const, 'aria-hidden': true, ...props });

export const AlertIcon = (p: P) => (
  <svg {...base(p)}>
    <path d="M12 3 2 20h20L12 3z" />
    <path d="M12 9v5M12 17h.01" />
  </svg>
);
export const ClockIcon = (p: P) => (
  <svg {...base(p)}>
    <circle cx="12" cy="12" r="9" />
    <path d="M12 7v5l3 2" />
  </svg>
);
export const SlipIcon = (p: P) => (
  <svg {...base(p)}>
    <path d="M4 17 10 11l4 4 6-6" />
    <path d="M14 9h6v6" />
  </svg>
);
export const UserOffIcon = (p: P) => (
  <svg {...base(p)}>
    <circle cx="12" cy="8" r="4" />
    <path d="M4 21c0-4 4-6 8-6s8 2 8 6" />
    <path d="M3 3l18 18" />
  </svg>
);
export const PencilOffIcon = (p: P) => (
  <svg {...base(p)}>
    <path d="M4 20h4L19 9l-4-4L4 16v4z" />
    <path d="M3 3l18 18" />
  </svg>
);
export const InboxIcon = (p: P) => (
  <svg {...base(p)}>
    <path d="M3 13h5l2 3h4l2-3h5" />
    <path d="M5 4h14l2 9v7H3v-7l2-9z" />
  </svg>
);
export const TagIcon = (p: P) => (
  <svg {...base(p)}>
    <path d="M3 12V4h8l10 10-8 8L3 12z" />
    <circle cx="8" cy="9" r="1.5" />
  </svg>
);
export const CheckIcon = (p: P) => (
  <svg {...base(p)}>
    <path d="M5 13l4 4L19 7" />
  </svg>
);
export const ArrowUpRightIcon = (p: P) => (
  <svg {...base(p)}>
    <path d="M7 17 17 7M8 7h9v9" />
  </svg>
);

export const TrendUpIcon = (p: P) => (
  <svg {...base(p)}>
    <path d="M3 17 9 11l4 4 8-8" />
    <path d="M15 7h6v6" />
  </svg>
);
export const TrendDownIcon = (p: P) => (
  <svg {...base(p)}>
    <path d="M3 7l6 6 4-4 8 8" />
    <path d="M15 17h6v-6" />
  </svg>
);
export const OctagonAlertIcon = (p: P) => (
  <svg {...base(p)}>
    <path d="M8 2.5h8L21.5 8v8L16 21.5H8L2.5 16V8z" />
    <path d="M12 7.5v5.5M12 16.5h.01" />
  </svg>
);
export const MinusIcon = (p: P) => (
  <svg {...base(p)}>
    <path d="M6 12h12" />
  </svg>
);

export const FLAG_ICONS: Record<string, (p: P) => ReactElement> = {
  OVERDUE: ClockIcon,
  SLIPPING: SlipIcon,
  NO_DPO: UserOffIcon,
  NOT_UPDATED: PencilOffIcon,
  UNUSED: InboxIcon,
  PENDING_URN: TagIcon,
  BEHIND: AlertIcon,
};

export const ChevronUpIcon = (p: P) => (
  <svg {...base(p)}>
    <path d="M6 15l6-6 6 6" />
  </svg>
);
export const ChevronDownIcon = (p: P) => (
  <svg {...base(p)}>
    <path d="M6 9l6 6 6-6" />
  </svg>
);
export const SortIcon = (p: P) => (
  <svg {...base(p)}>
    <path d="M8 10l4-4 4 4M8 14l4 4 4-4" />
  </svg>
);
export const ArrowLeftIcon = (p: P) => (
  <svg {...base(p)}>
    <path d="M19 12H5M11 6l-6 6 6 6" />
  </svg>
);
export const ArrowRightIcon = (p: P) => (
  <svg {...base(p)}>
    <path d="M5 12h14M13 6l6 6-6 6" />
  </svg>
);

/** Disclosure triangle (filled), rotated 90° by the caller when open. */
export const TriangleIcon = (p: P) => (
  <svg width={12} height={12} viewBox="0 0 12 12" aria-hidden="true" {...p}>
    <path d="M4 2.5 9 6l-5 3.5z" fill="currentColor" />
  </svg>
);
export const SearchIcon = (p: P) => (
  <svg {...base(p)}>
    <circle cx="11" cy="11" r="6.5" />
    <path d="m20 20-4.2-4.2" />
  </svg>
);
export const CloseIcon = (p: P) => (
  <svg {...base(p)}>
    <path d="M6 6l12 12M18 6 6 18" />
  </svg>
);
