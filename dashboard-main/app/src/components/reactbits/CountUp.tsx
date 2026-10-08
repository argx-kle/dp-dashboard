/* react-bits CountUp (TS-TW). Adapted: optional `format`, honours prefers-reduced-motion, and re-renders
   never reset the displayed value (the formatter is read through a ref). */

import { useInView, useMotionValue, useReducedMotion, useSpring } from 'motion/react';
import { useCallback, useEffect, useRef } from 'react';

interface CountUpProps {
  to: number;
  from?: number;
  delay?: number;
  duration?: number;
  className?: string;
  startWhen?: boolean;
  decimals?: number;
  format?: (value: number) => string;
}

export default function CountUp({ to, from = 0, delay = 0, duration = 0.9, className = '', startWhen = true, decimals, format }: CountUpProps) {
  const ref = useRef<HTMLSpanElement>(null);
  const reduced = useReducedMotion();
  const motionValue = useMotionValue(from);

  // Critically damped so the number settles within `duration` rather than drifting for seconds.
  const damping = 26 + 40 * (1 / duration);
  const stiffness = 160 * (1 / duration);
  const springValue = useSpring(motionValue, { damping, stiffness, restDelta: 0.01, restSpeed: 0.01 });
  const isInView = useInView(ref, { once: true, margin: '0px' });

  const maxDecimals = decimals ?? Math.max(getDecimalPlaces(from), getDecimalPlaces(to));

  const formatValue = useCallback(
    (latest: number) => {
      if (format) return format(latest);
      return Intl.NumberFormat('en-GB', { useGrouping: true, minimumFractionDigits: maxDecimals, maximumFractionDigits: maxDecimals }).format(latest);
    },
    [maxDecimals, format],
  );
  const formatRef = useRef(formatValue);
  formatRef.current = formatValue;

  // Reflect the current spring value on every render (never the start value, so re-renders don't reset the text).
  useEffect(() => {
    if (ref.current) ref.current.textContent = formatRef.current(reduced ? to : springValue.get());
  });

  useEffect(() => {
    if (reduced) {
      motionValue.jump(to);
      springValue.jump(to);
      if (ref.current) ref.current.textContent = formatRef.current(to);
      return;
    }
    if (isInView && startWhen) {
      const id = setTimeout(() => motionValue.set(to), delay * 1000);
      return () => clearTimeout(id);
    }
  }, [isInView, startWhen, motionValue, springValue, to, delay, reduced]);

  useEffect(() => {
    const unsubscribe = springValue.on('change', (latest: number) => {
      if (ref.current) ref.current.textContent = formatRef.current(latest);
    });
    return () => unsubscribe();
  }, [springValue]);

  return <span className={className} ref={ref} aria-hidden="true" />;
}

function getDecimalPlaces(num: number): number {
  const str = num.toString();
  if (str.includes('.')) {
    const decimals = str.split('.')[1];
    if (parseInt(decimals) !== 0) return decimals.length;
  }
  return 0;
}
