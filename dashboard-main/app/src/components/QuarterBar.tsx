/* The quarter selector and what the page is showing. Each quarter is a link (#/?q=2026-Q3), so a chosen
   quarter survives a reload and can be shared; the current quarter is the plain #/. */

import { motion, useReducedMotion } from 'motion/react';
import { useSnapshot } from '@/lib/context';
import { fmtDate, quarterLabel } from '@/lib/format';
import { quarterOptions, useQuarter } from '@/lib/quarter';
import { href } from '@/lib/router';

export default function QuarterBar() {
  const s = useSnapshot();
  // Outside the executive view (tests, a domain page) the snapshot's own quarter is the one shown.
  const q = useQuarter() ?? { quarter: s.quarter, current: s.quarter, closed: false, options: quarterOptions(s) };
  const reduced = useReducedMotion();
  return (
    <div className="flex flex-wrap items-center justify-between gap-x-6 gap-y-3" data-testid="quarter-bar">
      <div className="min-w-0">
        <h1 className="text-heading font-semibold text-ink">
          {quarterLabel(q.quarter)}
          <span className="font-normal text-ink-3">{q.closed ? ', closed' : ', to date'}</span>
        </h1>
        <p className="mt-1 text-body text-ink-3" data-testid="quarter-note">
          {q.closed ? (
            <>
              Status on {fmtDate(s.asOfDate)}, from gate dates. Plans, flags and usage are for the current week only.
            </>
          ) : (
            <>As of {fmtDate(s.asOfDate)}.</>
          )}
        </p>
      </div>
      <nav aria-label="Quarter" className="no-print max-w-full">
        <ul className="m-0 flex list-none items-center gap-0.5 rounded-full border border-line bg-panel p-1">
          {q.options.map((opt) => {
            const on = opt === q.quarter;
            return (
              <li key={opt} className="relative">
                {on && (
                  <motion.span
                    layoutId="quarter-pill"
                    className="absolute inset-0 rounded-full border border-clear/50 bg-panel-3"
                    transition={reduced ? { duration: 0 } : { type: 'spring', stiffness: 420, damping: 36 }}
                    aria-hidden="true"
                  />
                )}
                <a
                  href={href.exec(opt === q.current ? undefined : opt)}
                  aria-current={on ? 'page' : undefined}
                  data-testid={`quarter-${opt}`}
                  className={`relative block rounded-full px-2.5 py-1.5 text-small font-medium sm:px-3.5 sm:text-body whitespace-nowrap no-underline transition-colors duration-150 ${on ? 'text-ink' : 'text-ink-3 hover:text-ink'}`}
                >
                  {quarterLabel(opt)}
                </a>
              </li>
            );
          })}
        </ul>
      </nav>
    </div>
  );
}
