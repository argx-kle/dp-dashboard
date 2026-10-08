"""Technical readiness from the platform sources (validation tool, NextData).

It moves every week, long before a certification: how complete each product's specification is and whether
it runs. Definitions: docs/metric-definitions.md, section "Technical readiness".
"""

from __future__ import annotations

from statistics import median

from pipeline.context import MetricContext
from pipeline.metrics import MetricResult, count_result

NO_VALIDATION = "No validation results in the inbox"
NO_LISTING = "No NextData listing in the inbox"
FAILING = {"Failed", "Unreachable"}


def _scored(ctx: MetricContext, scope: str) -> list[tuple[str, float]]:
    out = []
    for pc in ctx.scoped(scope):
        rec = getattr(pc.platform, "validation", None)
        if pc.d.active and rec is not None and rec.score is not None:
            out.append((pc.urn, rec.score))
    return out


def spec_score_median(ctx: MetricContext, scope: str) -> MetricResult:
    if not ctx.has_validation:
        return MetricResult(None, n=0, urns=[], reason=NO_VALIDATION)
    pairs = _scored(ctx, scope)
    if not pairs:
        return MetricResult(None, n=0, values=[], urns=[], reason="No validation results for these products")
    values = sorted(round(v, 4) for _, v in pairs)
    return MetricResult(round(median(values), 4), n=len(values), values=values, urns=sorted(u for u, _ in pairs))


def runtime_failing(ctx: MetricContext, scope: str) -> MetricResult:
    if not ctx.has_nextdata:
        return MetricResult(None, n=0, urns=[], reason=NO_LISTING)
    on_platform = [pc for pc in ctx.scoped(scope) if pc.d.active and getattr(pc.platform, "deployments", None)]
    res = count_result([pc.urn for pc in on_platform if pc.platform.runtime in FAILING])
    res.n = len(on_platform)
    return res
