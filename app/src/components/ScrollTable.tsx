/* A table viewport for wide tables: the column header stays pinned while rows scroll, frozen
   columns stay on the left, and the table pans sideways when you press on empty space and drag.
   The browser's own scrollbar handles the rest. */

import { useCallback, useEffect, useLayoutEffect, useRef, useState, type ReactNode } from 'react';

interface Props {
  children: ReactNode;
  maxHeight?: string;
  testId?: string;
  label: string;
}

const INTERACTIVE = 'a,button,input,select,textarea,label,summary,[role="button"],[role="scrollbar"],[contenteditable="true"]';

export default function ScrollTable({ children, maxHeight = 'calc(100dvh - 190px)', testId = 'scroll-table', label }: Props) {
  const vp = useRef<HTMLDivElement>(null);
  const [geo, setGeo] = useState({ sw: 0, cw: 0, sl: 0 });
  const [dragging, setDragging] = useState(false);

  const measure = useCallback(() => {
    const el = vp.current;
    if (!el) return;
    setGeo({ sw: el.scrollWidth, cw: el.clientWidth, sl: el.scrollLeft });
  }, []);

  useLayoutEffect(() => {
    measure();
    const el = vp.current;
    if (!el) return;
    const ro = new ResizeObserver(measure);
    ro.observe(el);
    if (el.firstElementChild) ro.observe(el.firstElementChild);
    return () => ro.disconnect();
  }, [measure]);

  const overflow = geo.sw > geo.cw + 1;

  // Drag on the table body to pan sideways (mouse only; touch keeps native scrolling).
  const pan = useRef<{ x: number; left: number; moved: boolean; id: number } | null>(null);
  const onPointerDown = (e: React.PointerEvent<HTMLDivElement>) => {
    if (!overflow || e.button !== 0 || e.pointerType !== 'mouse') return;
    if ((e.target as HTMLElement).closest(INTERACTIVE)) return;
    pan.current = { x: e.clientX, left: vp.current!.scrollLeft, moved: false, id: e.pointerId };
  };
  const onPointerMove = (e: React.PointerEvent<HTMLDivElement>) => {
    const d = pan.current;
    if (!d) return;
    const dx = e.clientX - d.x;
    if (!d.moved && Math.abs(dx) > 4) {
      d.moved = true;
      vp.current!.setPointerCapture(d.id);
      window.getSelection()?.removeAllRanges();
      setDragging(true);
    }
    if (d.moved) {
      vp.current!.scrollLeft = d.left - dx;
      e.preventDefault();
    }
  };
  const endPan = () => {
    const d = pan.current;
    pan.current = null;
    if (!d?.moved) return;
    try {
      vp.current?.releasePointerCapture(d.id);
    } catch {
      /* already released */
    }
    setDragging(false);
    // A drag must not also click whatever it ended on.
    const stop = (ev: MouseEvent) => {
      ev.stopPropagation();
      ev.preventDefault();
    };
    window.addEventListener('click', stop, { capture: true, once: true });
    setTimeout(() => window.removeEventListener('click', stop, { capture: true }), 0);
  };

  useEffect(() => {
    if (!dragging) return;
    document.body.style.userSelect = 'none';
    return () => {
      document.body.style.userSelect = '';
    };
  }, [dragging]);

  return (
    <div className="overflow-hidden rounded-panel border border-line bg-panel" data-testid={testId}>
      <div
        ref={vp}
        role="region"
        aria-label={label}
        tabIndex={0}
        data-scrolled={geo.sl > 0 ? 'true' : 'false'}
        onScroll={measure}
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={endPan}
        onPointerCancel={endPan}
        className={`group/scroll overflow-auto overscroll-x-contain outline-none print:!max-h-none print:overflow-visible ${overflow ? (dragging ? 'cursor-grabbing' : 'cursor-grab') : ''}`}
        style={{ maxHeight }}
        data-testid={`${testId}-viewport`}
      >
        {children}
      </div>
    </div>
  );
}
