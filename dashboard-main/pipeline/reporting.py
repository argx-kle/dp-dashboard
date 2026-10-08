"""Data coverage: for each kind of input, how many products have it, per scope.

A metric built on missing inputs must never read like a delivery result: the app shows "gate dates for 0 of 44
products" next to it. Definitions: docs/metric-definitions.md, section "Data coverage".
"""

from __future__ import annotations

from collections.abc import Callable

from pipeline.context import MetricContext, ProductCtx
from pipeline.contracts import ReportingItem


def _kinds(ctx: MetricContext) -> list[tuple[str, Callable[[ProductCtx], bool], Callable[[ProductCtx], bool]]]:
    """(kind, belongs to the base, has the data)."""
    kinds = [
        ("gates", lambda pc: pc.d.active, lambda pc: bool(pc.d.gates)),
        ("plans", lambda pc: pc.d.active and pc.d.first_g4 is None, lambda pc: pc.p.planned_ga_date is not None),
        ("reviewed", lambda pc: pc.d.active, lambda pc: pc.p.reviewed_on is not None),
        ("dpo", lambda pc: pc.d.active, lambda pc: bool(pc.p.dpo)),
        ("usage", lambda pc: pc.d.live, lambda pc: pc.p.active_users_30d is not None),
        ("consumers", lambda pc: pc.d.live, lambda pc: pc.p.first_consumer_date is not None),
    ]
    if ctx.has_validation:
        kinds.append(("validation", lambda pc: pc.d.active, lambda pc: getattr(getattr(pc.platform, "validation", None), "score", None) is not None))
    if ctx.has_nextdata:
        kinds.append(("nextdata", lambda pc: pc.d.active, lambda pc: bool(getattr(pc.platform, "deployments", None))))
    return kinds


def compute_reporting(ctx: MetricContext) -> list[ReportingItem]:
    out: list[ReportingItem] = []
    for scope in ["org", *ctx.domains.ids]:
        products = ctx.scoped(scope)
        for kind, base, has in _kinds(ctx):
            pool = [pc for pc in products if base(pc)]
            missing = sorted(pc.urn for pc in pool if not has(pc))
            out.append(ReportingItem(kind=kind, scope=scope, have=len(pool) - len(missing), of=len(pool), missing=missing))
    return out
