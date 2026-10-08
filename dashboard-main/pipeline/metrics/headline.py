"""Headline and supporting metrics. Definitions: docs/metric-definitions.md."""

from __future__ import annotations

from datetime import timedelta

from pipeline.context import MetricContext
from pipeline.dates import UNUSED_AFTER_DAYS, in_trailing_window, quarter_bounds
from pipeline.metrics import MetricResult, count_result, median_result


def certified_in_quarter(ctx: MetricContext, scope: str) -> MetricResult:
    start, end = quarter_bounds(ctx.quarter)
    urns = [pc.urn for pc in ctx.scoped(scope) if pc.d.first_g4 and start <= pc.d.first_g4 <= end]
    return count_result(urns)


def cycle_time(ctx: MetricContext, scope: str) -> MetricResult:
    pairs = []
    for pc in ctx.scoped(scope):
        if not in_trailing_window(pc.d.first_g4, ctx.as_of):
            continue
        g1 = pc.d.g1_date
        if g1 is None:
            continue  # NO_G1 is a blocker upstream; defensive only
        pairs.append((pc.urn, (pc.d.first_g4 - g1).days))
    return median_result(pairs, "No product certified in the trailing 182 days")


def time_to_first_consumer(ctx: MetricContext, scope: str) -> MetricResult:
    pairs = []
    for pc in ctx.scoped(scope):
        fc = pc.p.first_consumer_date
        g1 = pc.d.g1_date
        if g1 is None or not in_trailing_window(fc, ctx.as_of):
            continue
        pairs.append((pc.urn, (fc - g1).days))
    return median_result(pairs, "No first consumer recorded in the trailing 182 days")


NO_PAST_USAGE = "Usage is reported for the current week only"


def active_users_median(ctx: MetricContext, scope: str) -> MetricResult:
    if ctx.closed:
        return MetricResult(None, n=0, urns=[], reason=NO_PAST_USAGE)
    pairs = [(pc.urn, float(pc.p.active_users_30d)) for pc in ctx.scoped(scope) if pc.d.live and pc.p.active_users_30d is not None]
    return median_result(pairs, "No live product with a usage figure")


def live_count(ctx: MetricContext, scope: str) -> MetricResult:
    return count_result([pc.urn for pc in ctx.scoped(scope) if pc.d.live])


def pipeline_count(ctx: MetricContext, scope: str) -> MetricResult:
    return count_result([pc.urn for pc in ctx.scoped(scope) if pc.d.in_pipeline])


def is_unused(ctx: MetricContext, pc) -> bool:
    if not pc.d.live or pc.d.first_g4 is None:
        return False
    if pc.d.first_g4 > ctx.as_of - timedelta(days=UNUSED_AFTER_DAYS):
        return False
    if pc.p.active_users_30d is None:
        return False  # missing usage is a warning, not an unused product
    return pc.p.active_users_30d == 0 and not pc.consumed_by


def certified_unused(ctx: MetricContext, scope: str) -> MetricResult:
    if ctx.closed:
        return MetricResult(None, n=0, urns=[], reason=NO_PAST_USAGE)
    return count_result([pc.urn for pc in ctx.scoped(scope) if is_unused(ctx, pc)])


def is_forecast(ctx: MetricContext, pc) -> bool:
    start, end = quarter_bounds(ctx.quarter)
    ga = pc.p.planned_ga_date
    return (
        not ctx.closed
        and pc.d.active
        and pc.d.first_g4 is None
        and ga is not None
        and start <= ga <= end
        and ga >= ctx.as_of
        and not pc.has_flag("OVERDUE")
    )


def g4_forecast(ctx: MetricContext, scope: str) -> MetricResult:
    """The rings' forecast arc and the Behind flag."""
    return count_result([pc.urn for pc in ctx.scoped(scope) if is_forecast(ctx, pc)])
