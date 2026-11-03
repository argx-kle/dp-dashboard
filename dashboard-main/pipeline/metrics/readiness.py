"""Technical readiness from the platform sources (validation tool, NextData, GitHub).

It moves every week, long before a certification: how complete each product's specification is, whether it
runs, and how its repository deploys. Definitions: docs/metric-definitions.md, section "Technical readiness".
"""

from __future__ import annotations

from statistics import median

from pipeline.context import MetricContext
from pipeline.github import failed, in_window, prod_successes, recent
from pipeline.metrics import MetricResult, count_result, median_result

NO_VALIDATION = "No validation results in the inbox"
NO_LISTING = "No NextData listing in the inbox"
NO_GITHUB = "No GitHub extract in the inbox"
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


def _with_repo(ctx: MetricContext, scope: str) -> list:
    return [pc for pc in ctx.scoped(scope) if pc.d.active and pc.github is not None]


def no_prod_deploy(ctx: MetricContext, scope: str) -> MetricResult:
    if not ctx.has_github:
        return MetricResult(None, n=0, urns=[], reason=NO_GITHUB)
    pool = _with_repo(ctx, scope)
    res = count_result([pc.urn for pc in pool if not prod_successes(pc.github, ctx.platform_cfg, ctx.as_of)])
    res.n = len(pool)
    return res


def prod_deploy_frequency(ctx: MetricContext, scope: str) -> MetricResult:
    if not ctx.has_github:
        return MetricResult(None, n=0, urns=[], reason=NO_GITHUB)
    # Over the products whose repository has reached production, not register-live ones: GitHub says which
    # products ship, whether or not the register has their gates yet.
    shipped = [(pc.urn, prod_successes(pc.github, ctx.platform_cfg, ctx.as_of)) for pc in _with_repo(ctx, scope)]
    pairs = [(urn, len([d for d in ok if in_window(d, ctx.as_of)])) for urn, ok in shipped if ok]
    return median_result(pairs, "No product's repository has deployed to production")


def deploy_failure_rate(ctx: MetricContext, scope: str) -> MetricResult:
    if not ctx.has_github:
        return MetricResult(None, n=0, urns=[], reason=NO_GITHUB)
    total, bad, urns = 0, 0, []
    for pc in _with_repo(ctx, scope):
        deps = recent(pc.github, ctx.as_of)
        total += len(deps)
        n_failed = len(failed(deps))
        bad += n_failed
        if n_failed:
            urns.append(pc.urn)
    if total == 0:
        return MetricResult(None, n=0, urns=[], reason="No deployments in the last 30 days")
    return MetricResult(round(bad / total, 4), n=total, urns=sorted(urns))
