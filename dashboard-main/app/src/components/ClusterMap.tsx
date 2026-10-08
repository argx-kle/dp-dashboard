/* Domains as clusters, products as bubbles. Each domain's outline is the union of halos around its
   products, so the cluster hugs its members. Each bubble carries the product's name; its ring is the
   lifecycle stage (colour and arc length; health is a domain verdict and lives on the cluster label).
   Moving the pointer magnifies nearby bubbles (react-bits Dock-style proximity scaling); hovering or
   focusing one lifts it and opens a preview card. */

import { memo, useEffect, useMemo, useRef, useState, type ReactNode } from 'react';
import { AnimatePresence, motion, useMotionValue, useReducedMotion, useSpring, type MotionValue } from 'motion/react';
import { fitName, layoutGroups } from '@/lib/cluster';
import { ATTENTION, C, STAGES } from '@/lib/theme';
import { href } from '@/lib/router';
import { useFocusTarget } from '@/lib/focus';
import { useWidth } from '@/lib/useWidth';
import { StageRing } from '@/components/StageMark';
import ProductPreview from '@/components/ProductPreview';
import type { ProductRow } from '@/types/snapshot';

export interface ClusterGroup {
  id: string;
  label: string;
  href?: string;
  badge?: ReactNode;
  meta?: ReactNode;
  items: ProductRow[];
}

interface Props {
  groups: ClusterGroup[];
  bubbleR?: number;
  ariaLabel: string;
  testId?: string;
}

const HALO = 12;
const LABEL_SPACE = 56;
const PAD_X = 12;
const OFF = -1e6;
const PREVIEW_W = 300;

export default function ClusterMap({ groups, bubbleR = 36, ariaLabel, testId = 'cluster-map' }: Props) {
  const reduced = useReducedMotion() ?? false;
  const [wrapRef, available] = useWidth<HTMLDivElement>();
  const svgRef = useRef<SVGSVGElement>(null);
  const mx = useMotionValue(OFF);
  const my = useMotionValue(OFF);
  const { focus, setFocus } = useFocusTarget();
  const [local, setLocal] = useState<string | null>(null);

  const layout = useMemo(
    () =>
      layoutGroups(
        groups.map((g) => ({
          id: g.id,
          // Room for the label: about 8.5 px per character at 15 px semibold, plus the health badge.
          minWidth: g.label.length * 8.5 + (g.badge ? 104 : 0),
          items: g.items.map((p) => ({ key: p.urn })),
        })),
        { bubbleR, gap: 6, groupPad: HALO, groupGap: 32, labelTop: LABEL_SPACE, labelBottom: 8, rowGap: 20, rowWidth: (available - PAD_X * 2) * 1.12 }, // up to 12% shrink before wrapping, so a scrollbar or a few px never break the row
      ),
    [groups, bubbleR, available],
  );

  const placed = useMemo(() => {
    const m = new Map<string, { p: ProductRow; group: string; x: number; y: number; i: number }>();
    for (const g of layout.groups) {
      const src = groups.find((x) => x.id === g.id)!;
      g.bubbles.forEach((b, i) => m.set(b.key, { p: src.items.find((p) => p.urn === b.key)!, group: g.id, x: b.x, y: b.y, i }));
    }
    return m;
  }, [layout, groups]);

  const vbX = -PAD_X;
  const vbW = layout.width + PAD_X * 2;
  const vbH = layout.height;
  const pctX = (x: number) => `${((x - vbX) / vbW) * 100}%`;
  const pctY = (y: number) => `${(y / vbH) * 100}%`;

  const onPointerMove = (e: React.PointerEvent<SVGSVGElement>) => {
    if (reduced || !svgRef.current) return;
    const ctm = svgRef.current.getScreenCTM();
    if (!ctm) return;
    const pt = new DOMPoint(e.clientX, e.clientY).matrixTransform(ctm.inverse());
    mx.set(pt.x);
    my.set(pt.y);
  };
  const onLeave = () => {
    mx.set(OFF);
    my.set(OFF);
  };
  const activate = (urn: string | null) => {
    setLocal(urn);
    setFocus(urn);
  };

  const focused = focus ? placed.get(focus) : undefined;
  const preview = local && local === focus ? focused : undefined;

  return (
    <div ref={wrapRef} className="w-full min-w-0" data-testid={testId}>
      {/* Drawn at 1 unit = 1 px so bubbles and labels keep their size; wraps into rows when narrow. */}
      <div className="relative mx-auto select-none" style={{ width: Math.min(vbW, available), maxWidth: '100%' }}>
      <svg ref={svgRef} viewBox={`${vbX} 0 ${vbW} ${vbH}`} className="block h-auto w-full overflow-visible" role="group" aria-label={ariaLabel} onPointerMove={onPointerMove} onPointerLeave={onLeave}>
        {layout.groups.map((g) => {
          const lit = focused?.group === g.id;
          return (
            <g key={g.id} aria-hidden="true">
              {/* Domain region: union of halos. The outline layer is one step larger, the fill layer
                  sits on top, so only the outer edge of the union shows. */}
              <g>
                {g.bubbles.map((b) => (
                  <circle key={b.key} cx={b.x} cy={b.y} r={bubbleR + HALO + 1.25} fill={lit ? C.lineStrong : C.line} style={{ transition: 'fill 200ms' }} />
                ))}
              </g>
              <g>
                {g.bubbles.map((b) => (
                  <circle key={b.key} cx={b.x} cy={b.y} r={bubbleR + HALO} fill={C.panel2} />
                ))}
              </g>
            </g>
          );
        })}
        {Array.from(placed.entries()).map(([urn, info]) => (
          <Bubble
            key={urn}
            p={info.p}
            x={info.x}
            y={info.y}
            r={bubbleR}
            index={info.i}
            mx={mx}
            my={my}
            reduced={reduced}
            active={focus === urn}
            // Every map on the page dims while one product is in focus, wherever that product sits.
            dimmed={focus !== null && focus !== urn}
            onActivate={activate}
          />
        ))}
      </svg>

      {/* Group labels: HTML so they stay crisp, reuse badges and stay keyboard-reachable. */}
      {layout.groups.map((g) => {
        const src = groups.find((x) => x.id === g.id)!;
        const top = g.hullTop - 10; // 10 px above this cluster's own outline (outlines in a row share a top edge)
        return (
          <div key={g.id} className="absolute flex -translate-x-1/2 -translate-y-full flex-col items-center gap-1 text-center" style={{ left: pctX(g.cx), top: pctY(top) }}>
            <div className="flex items-center gap-2">
              {src.href ? (
                <a href={src.href} className="whitespace-nowrap text-body font-semibold text-ink no-underline hover:text-clear" data-testid={`cluster-label-${g.id}`}>
                  {src.label}
                </a>
              ) : (
                <span className="whitespace-nowrap text-body font-semibold text-ink">{src.label}</span>
              )}
              {src.badge}
            </div>
            {src.meta && <div className="whitespace-nowrap text-small text-ink-3">{src.meta}</div>}
          </div>
        );
      })}

      <AnimatePresence>
        {preview &&
          (() => {
            // Beside the hovered bubble, on the side with more room; ProductPreview then keeps the
            // whole card inside the visible viewport.
            const roomRight = vbX + vbW - preview.x;
            const right = roomRight >= PREVIEW_W + bubbleR + 24 || roomRight > preview.x - vbX;
            const left = right ? preview.x + bubbleR + 16 : preview.x - bubbleR - 16 - PREVIEW_W;
            return <ProductPreview key={preview.p.urn} product={preview.p} left={pctX(left)} top={pctY(preview.y)} width={PREVIEW_W} />;
          })()}
      </AnimatePresence>
      </div>
    </div>
  );
}

interface BubbleProps {
  p: ProductRow;
  x: number;
  y: number;
  r: number;
  index: number;
  mx: MotionValue<number>;
  my: MotionValue<number>;
  reduced: boolean;
  active: boolean;
  dimmed: boolean;
  onActivate: (urn: string | null) => void;
}

const Bubble = memo(function Bubble({ p, x, y, r, index, mx, my, reduced, active, dimmed, onActivate }: BubbleProps) {
  const target = useMotionValue(reduced ? 1 : 0);
  const scale = useSpring(target, reduced ? { duration: 0 } : { stiffness: 340, damping: 26, mass: 0.6 });
  const mounted = useRef(reduced);

  useEffect(() => {
    const reach = r * 5;
    const update = () => {
      if (!mounted.current) return;
      const base = 1;
      if (active) return target.set(base * (reduced ? 1.06 : 1.14));
      if (reduced) return target.set(base);
      const d = Math.hypot(mx.get() - x, my.get() - y);
      target.set(base * (1 + 0.08 * Math.max(0, 1 - d / reach)));
    };
    const t = mounted.current
      ? undefined
      : setTimeout(() => {
          mounted.current = true;
          update();
        }, 80 + index * 30);
    update();
    const a = mx.on('change', update);
    const b = my.on('change', update);
    return () => {
      if (t) clearTimeout(t);
      a();
      b();
    };
  }, [active, reduced, mx, my, x, y, r, index, target]);

  const st = STAGES[p.lifecycle];
  const ended = !!st.ended;
  const ring = Math.max(1.2, r / 22);
  const name = useMemo(() => fitName(p.name, r - ring - 3), [p.name, r, ring]);
  const flags = p.flags.map((f) => f.code.replace(/_/g, ' ').toLowerCase()).join(', ');
  const label = `${p.name}. ${p.lifecycle}${flags ? `. Flagged: ${flags}` : ''}. Open product.`;

  return (
    <g transform={`translate(${x} ${y})`}>
      <motion.g style={{ scale }} animate={{ opacity: dimmed ? 0.35 : 1 }} transition={{ duration: 0.2 }}>
        <a
          href={href.product(p.urn)}
          aria-label={label}
          data-testid="cluster-bubble"
          data-urn={p.urn}
          data-stage={p.lifecycle}
          onPointerEnter={() => onActivate(p.urn)}
          onPointerLeave={() => onActivate(null)}
          onFocus={() => onActivate(p.urn)}
          onBlur={() => onActivate(null)}
          className="cursor-pointer no-underline outline-none [&:focus-visible_.focus-ring]:opacity-100"
        >
          {/* Hit area larger than the mark (>= 24px) and symmetric, so scaling stays centred. */}
          <circle r={r + 4} fill="transparent" />
          <circle className="focus-ring" r={r + 4} fill="none" stroke={C.clear} strokeWidth={1.5} opacity={0} />
          {active && <circle r={r + 6} fill={st.color} opacity={0.18} style={{ filter: 'blur(8px)' }} />}
          <circle r={r} fill={ended ? C.bg : C.panel} />
          {p.lifecycle === 'Live' && <circle r={r} fill={st.color} opacity={active ? 0.18 : 0.1} />}
          <g opacity={ended && !active ? 0.8 : 1}>
            <StageRing stage={p.lifecycle} r={p.lifecycle === 'Failed / retired' ? r - 4 * ring : r - ring} width={ring} />
          </g>
          {p.flags.length > 0 && (
            <circle cx={r * 0.72} cy={-r * 0.72} r={Math.max(4.5, r / 6.5)} fill={ATTENTION} stroke={C.bg} strokeWidth={2} data-testid="attention-dot">
              <title>Needs attention</title>
            </circle>
          )}
          <text textAnchor="middle" fontSize={name.size} fontWeight={600} fill={ended ? C.ink3 : C.ink} style={{ pointerEvents: 'none', fontFamily: 'var(--font-sans)', textDecoration: 'none' }}>
            {name.lines.map((line, i) => (
              <tspan key={i} x={0} y={(i - (name.lines.length - 1) / 2) * name.size * 1.14} dy="0.35em">
                {line}
              </tspan>
            ))}
          </text>
        </a>
      </motion.g>
    </g>
  );
});
