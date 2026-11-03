import { useLayoutEffect, useRef, useState } from 'react';

/** Content-box width of an element, kept current with ResizeObserver. */
export function useWidth<T extends HTMLElement>(fallback = 960) {
  const ref = useRef<T>(null);
  const [width, setWidth] = useState(fallback);
  useLayoutEffect(() => {
    const el = ref.current;
    if (!el) return;
    // A hidden element (display: none, e.g. the map while the Table view shows) measures 0: keep the
    // last real width so the layout is already right when it reappears.
    const measure = () => {
      const w = Math.round(el.getBoundingClientRect().width);
      if (w > 0) setWidth(Math.max(240, w));
    };
    measure();
    const ro = new ResizeObserver(measure);
    ro.observe(el);
    return () => ro.disconnect();
  }, []);
  return [ref, width] as const;
}
