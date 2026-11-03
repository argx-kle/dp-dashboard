import { useEffect, useRef, useState } from 'react';
import GlareHover from '@/components/reactbits/GlareHover';
import wordmark from '@/assets/brand/argenx-wordmark-white-560.webp';
import { useSnapshot } from '@/lib/context';
import { fmtDateTimeZone } from '@/lib/format';
import { href, type Route } from '@/lib/router';
import { C } from '@/lib/theme';

const NAV = [
  { id: 'exec', label: 'Executive', href: href.exec() },
  { id: 'products', label: 'Products', href: href.products() },
  { id: 'delivery', label: 'Delivery', href: href.delivery() },
  { id: 'definitions', label: 'Definitions', href: href.definitions() },
] as const;

function current(route: Route): (typeof NAV)[number]['id'] {
  if (route.view === 'products' || route.view === 'product') return 'products';
  if (route.view === 'definitions') return 'definitions';
  if (route.view === 'delivery') return 'delivery';
  return 'exec';
}

function NavTabs({ route }: { route: Route }) {
  const s = useSnapshot();
  const active = current(route);
  const previous = useRef(active);
  const [sweep, setSweep] = useState<string | null>(null);

  // The react-bits glare crosses the newly current tab once when the view changes.
  useEffect(() => {
    if (previous.current === active) return;
    previous.current = active;
    setSweep(null);
    const start = requestAnimationFrame(() => setSweep(active));
    const end = setTimeout(() => setSweep(null), 900);
    return () => {
      cancelAnimationFrame(start);
      clearTimeout(end);
    };
  }, [active]);

  return (
    <nav aria-label="Views" className="no-print">
      <ul className="m-0 flex list-none items-center gap-0.5 p-0 sm:gap-1">
        {NAV.filter((item) => item.id !== 'delivery' || s.delivery).map((item) => {
          const on = item.id === active;
          return (
            <li key={item.id}>
              <GlareHover
                width="auto"
                height="auto"
                background={on ? C.panel3 : 'transparent'}
                borderRadius="999px"
                borderColor={on ? C.lineStrong : 'transparent'}
                glareColor="#D2F1FA"
                glareOpacity={0.32}
                glareAngle={-30}
                glareSize={300}
                transitionDuration={800}
                playOnce
                sweep={sweep === item.id}
              >
                <a
                  href={item.href}
                  aria-current={on ? 'page' : undefined}
                  data-testid={`nav-${item.id}`}
                  className={`relative block px-2.5 py-1.5 text-body sm:px-4 font-medium no-underline transition-colors duration-150 ${on ? 'text-ink' : 'text-ink-3 hover:text-ink'}`}
                >
                  {item.label}
                </a>
              </GlareHover>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}

export default function Header({ route }: { route: Route }) {
  const s = useSnapshot();
  const week = Number(s.weekId.slice(-2));
  return (
    <header className="sticky top-0 z-40 border-b border-line bg-bg">
      <div className="mx-auto flex min-h-16 max-w-[1440px] flex-wrap items-center gap-x-5 gap-y-2 px-6 py-3 lg:px-10">
        <a href={href.exec()} className="flex items-center gap-4 no-underline" aria-label="argenx Data Product Delivery, executive overview">
          <img src={wordmark} alt="argenx" width={84} height={18} className="h-[18px] w-auto" />
          <span className="h-5 w-px bg-line-strong" aria-hidden="true" />
          <span className="text-lead font-semibold text-ink">
            Data Product <span className="font-accent font-normal italic text-clear">Delivery</span>
          </span>
        </a>
        <span className="text-small text-ink-3" data-testid="last-updated">
          Week {week} · Updated <time dateTime={s.generatedAt}>{fmtDateTimeZone(s.generatedAt)}</time>
        </span>
        <div className="ml-auto">
          <NavTabs route={route} />
        </div>
      </div>
    </header>
  );
}
