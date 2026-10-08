"""Certified per quarter per domain, with targets, for the last four quarters; and the same week by week."""

from __future__ import annotations

from datetime import timedelta

from pipeline.context import MetricContext
from pipeline.contracts import TrendPoint, WeeklyPoint
from pipeline.dates import quarter_bounds, quarters_ending_at, week_of

TREND_QUARTERS = 4


def trend_quarters(ctx: MetricContext) -> list[str]:
    return quarters_ending_at(ctx.quarter, TREND_QUARTERS)


def compute_trend(ctx: MetricContext) -> list[TrendPoint]:
    out: list[TrendPoint] = []
    for q in trend_quarters(ctx):
        start, end = quarter_bounds(q)
        for dom in ctx.domains.ids:
            certified = sum(1 for pc in ctx.products if pc.domain == dom and pc.d.first_g4 and start <= pc.d.first_g4 <= end)
            out.append(TrendPoint(quarter=q, domain=dom, certified=certified, target=ctx.target(dom, q)))
    return out


def compute_weekly(ctx: MetricContext) -> list[WeeklyPoint]:
    """For each trend quarter, certified so far at the end of every ISO week (Monday to Sunday) that overlaps
    the quarter. The current quarter stops at the week containing the as-of date, counted up to the as-of date."""
    out: list[WeeklyPoint] = []
    for q in trend_quarters(ctx):
        start, end = quarter_bounds(q)
        limit = min(end, ctx.as_of)
        monday = start - timedelta(days=start.weekday())
        while monday <= limit:
            last = min(monday + timedelta(days=6), limit)
            done = [pc for pc in ctx.products if pc.d.first_g4 and start <= pc.d.first_g4 <= last]
            by_domain: dict[str, int] = {}
            for pc in done:
                by_domain[pc.domain] = by_domain.get(pc.domain, 0) + 1
            out.append(WeeklyPoint(quarter=q, week=week_of(monday), end=last.isoformat(), certified=len(done), byDomain={d: by_domain[d] for d in ctx.domains.ids if d in by_domain}))
            monday += timedelta(days=7)
    return out
