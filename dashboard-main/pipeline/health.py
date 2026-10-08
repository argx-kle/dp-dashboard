"""Domain health: will a domain, and the organisation, hit its quarterly target.

Definitions: docs/metric-definitions.md, section "Domain health". Health is a forecast against the pace expected by
today, not the share of the final target: expected = target x share of the quarter elapsed; pace = certified /
expected. A closed quarter is a result instead: above, met or below its target.
"""

from __future__ import annotations

import math

from pipeline.context import MetricContext, ProductCtx
from pipeline.contracts import HealthItem
from pipeline.dates import quarter_bounds
from pipeline.metrics.headline import certified_in_quarter, is_forecast

AHEAD, ON_TRACK, AT_RISK = 1.10, 0.90, 0.70


def elapsed_share(ctx: MetricContext) -> float:
    """Days from the quarter start to the as-of date, inclusive, over the days in the quarter."""
    start, end = quarter_bounds(ctx.quarter)
    days = (end - start).days + 1
    return max(0.0, min(1.0, ((ctx.as_of - start).days + 1) / days))


def is_late(ctx: MetricContext, pc: ProductCtx) -> bool:
    """Not yet live, go-live due by the quarter end, but not on plan: its next gate is overdue or its date passed."""
    if ctx.closed or not pc.d.active or pc.d.first_g4 is not None or pc.p.planned_ga_date is None:
        return False
    _, end = quarter_bounds(ctx.quarter)
    return pc.p.planned_ga_date <= end and not is_forecast(ctx, pc)


def expected_by_today(target: int, elapsed: float) -> int:
    """Target x share of the quarter elapsed, to the nearest whole product (halves round up), so anyone can check
    the verdict from the numbers on screen."""
    return math.floor(target * elapsed + 0.5)


def health_status(certified: int, target: int | None, elapsed: float, closed: bool = False) -> str:
    if target is None:
        return "no-target"
    if closed:
        return "above-target" if certified > target else "met-target" if certified == target else "below-target"
    expected = expected_by_today(target, elapsed)
    if expected == 0:  # nothing due yet: delivering early is ahead, delivering nothing is still on track
        return "ahead" if certified > 0 else "on-track"
    pace = certified / expected
    if pace >= AHEAD:
        return "ahead"
    if pace >= ON_TRACK:
        return "on-track"
    if pace >= AT_RISK:
        return "at-risk"
    return "off-track"


def scope_health(ctx: MetricContext, scope: str) -> HealthItem:
    products = ctx.scoped(scope)
    certified = int(certified_in_quarter(ctx, scope).value or 0)
    target = ctx.target(scope)
    elapsed = 1.0 if ctx.closed else elapsed_share(ctx)
    expected = expected_by_today(target, elapsed) if target is not None else None
    late = sorted(pc.urn for pc in products if is_late(ctx, pc))
    return HealthItem(
        quarter=ctx.quarter,
        scope=scope,
        status=health_status(certified, target, elapsed, ctx.closed),
        certified=certified,
        target=target,
        expected=expected,
        pace=round(certified / expected, 3) if expected else None,
        elapsed=round(elapsed, 4),
        forecast=sum(1 for pc in products if is_forecast(ctx, pc)),
        late=len(late),
        lateUrns=late,
    )


def compute_health(ctx: MetricContext) -> list[HealthItem]:
    return [scope_health(ctx, scope) for scope in ["org", *ctx.domains.ids]]
