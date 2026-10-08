"""The closed quarters of the trend, each rebuilt as it stood on its last day, for the quarter selector.

Gate dates are history, so lifecycle stages, certifications, cycle times and first-consumer dates can be recomputed
for any past day. Plans, flags and usage are only known for the current week: a closed quarter forecasts nothing,
raises no product flag and shows no usage figure. Definitions: docs/metric-definitions.md, "Quarter selector".
"""

from __future__ import annotations

from dataclasses import replace

from pipeline.context import MetricContext, build_context
from pipeline.contracts import GateRecord, HealthItem, Inbox, QuarterProduct, QuarterView
from pipeline.dates import iso, quarter_bounds
from pipeline.health import compute_health
from pipeline.metrics.registry_runner import compute_metrics
from pipeline.registry import FlagDef, MetricDef
from pipeline.trend import trend_quarters


def closed_context(inbox: Inbox, current: MetricContext, quarter: str) -> MetricContext:
    _, end = quarter_bounds(quarter)
    events = [e for e in inbox.gate_events if e.date_passed <= end]
    seen = {e.urn for e in events}
    products = [replace(p, cancelled_on=p.cancelled_on if p.cancelled_on and p.cancelled_on <= end else None) for p in inbox.products if p.urn in seen]
    ctx = build_context(Inbox(products=products, gate_events=events, targets=inbox.targets), end, current.domains)
    ctx.closed = True
    ctx.platform_cfg = current.platform_cfg
    return ctx


def compute_quarters(inbox: Inbox, current: MetricContext, metric_defs: list[MetricDef], flag_defs: list[FlagDef]) -> tuple[list[QuarterView], list[HealthItem]]:
    views: list[QuarterView] = []
    health: list[HealthItem] = []
    for q in trend_quarters(current)[:-1]:
        ctx = closed_context(inbox, current, q)
        views.append(
            QuarterView(
                quarter=q,
                asOfDate=ctx.as_of.isoformat(),
                metrics=compute_metrics(ctx, metric_defs, flag_defs),
                products=[
                    QuarterProduct(
                        urn=pc.urn,
                        lifecycle=pc.d.lifecycle,
                        status=pc.d.status,
                        lastGate=GateRecord(gate=g.gate, date=g.date.isoformat(), iteration=g.iteration, g5Path=g.g5_path, evidenceUrl=g.evidence_url) if (g := pc.d.last_gate) else None,
                        firstG4Date=iso(pc.d.first_g4),
                    )
                    for pc in ctx.products
                ],
            )
        )
        health.extend(compute_health(ctx))
    return views, health
