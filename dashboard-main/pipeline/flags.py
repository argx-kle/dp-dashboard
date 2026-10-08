"""Flag rules. Product rules return a dict of reason fields or None; BEHIND reads computed metrics."""

from __future__ import annotations

from datetime import timedelta

from pipeline.context import MetricContext, ProductCtx
from pipeline.contracts import ProductFlag
from pipeline.dates import OVERDUE_GRACE_DAYS, REVIEW_STALE_DAYS
from pipeline.lifecycle import GATE_NAMES, LIFECYCLE_AFTER_GATE
from pipeline.metrics.headline import is_unused
from pipeline.registry import SIGNAL_RANK, FlagDef


def overdue(ctx: MetricContext, pc: ProductCtx) -> dict | None:
    nxt = pc.d.next_gate()
    planned = pc.p.planned_next_gate_date
    if nxt is None or planned is None:
        return None
    if ctx.as_of > planned + timedelta(days=OVERDUE_GRACE_DAYS):
        return {"gate": nxt, "gate_name": GATE_NAMES[nxt], "stage": LIFECYCLE_AFTER_GATE[nxt], "planned": planned.isoformat(), "days": (ctx.as_of - planned).days}
    return None


def slipping(ctx: MetricContext, pc: ProductCtx, slips: int = 0, baseline: str | None = None) -> dict | None:
    """Slips are counted by build.py from snapshot history and passed in; the rule is the threshold."""
    if pc.d.first_g4 is None and slips >= 2:
        return {"slips": slips, "baseline": baseline or "?"}
    return None


def no_dpo(ctx: MetricContext, pc: ProductCtx) -> dict | None:
    if pc.d.g1_date is not None and not pc.p.dpo:
        return {"stage": pc.d.lifecycle}
    return None


def not_updated(ctx: MetricContext, pc: ProductCtx) -> dict | None:
    """Counts from the first review: a product never reviewed is "Not yet reported" (its signal), not stale."""
    reviewed = pc.p.reviewed_on
    if reviewed is None:
        return None
    days = (ctx.as_of - reviewed).days
    if days > REVIEW_STALE_DAYS:
        return {"reviewed": reviewed.isoformat(), "days": days}
    return None


def unused(ctx: MetricContext, pc: ProductCtx) -> dict | None:
    if is_unused(ctx, pc):
        return {"days": (ctx.as_of - pc.d.first_g4).days}
    return None


def pending_urn(ctx: MetricContext, pc: ProductCtx) -> dict | None:
    return {} if pc.urn.lower().startswith("pending:") else None


def behind(ctx: MetricContext, domain_id: str, certified: int, forecast: int) -> dict | None:
    """Behind = the domain's health is at risk or off track (below target, once the quarter is closed)."""
    from pipeline.health import scope_health

    h = scope_health(ctx, domain_id)
    if h.status in ("at-risk", "off-track", "below-target"):
        return {"certified": certified, "expected": h.expected, "target": h.target}
    return None


def product_signal(pc: ProductCtx, flag_defs: list[FlagDef]) -> str:
    """grey when inactive; else the most severe signal among the product's flags; with no flag,
    unreported when the DPO has never reviewed the row, else green."""
    if not pc.d.active:
        return "grey"
    by_code = {f.code: f.signal for f in flag_defs}
    signals = [by_code[f.code] for f in pc.flags if f.code in by_code]
    if signals:
        return max(signals, key=SIGNAL_RANK.__getitem__)
    return "unreported" if pc.p.reviewed_on is None else "green"


def apply_product_flags(ctx: MetricContext, flag_defs: list[FlagDef], slips: dict[str, tuple[int, str | None]]) -> None:
    """Fill pc.flags for every product. `slips` maps urn -> (ga_slips, baseline_iso)."""
    product_defs = [f for f in flag_defs if f.level == "product"]
    for pc in ctx.products:
        pc.flags = []
        for fd in product_defs:
            if fd.applies_to == "active" and not pc.d.active:
                continue
            fn = fd.resolve()
            if fd.code == "SLIPPING":
                s, b = slips.get(pc.urn, (0, None))
                fields = fn(ctx, pc, slips=s, baseline=b)
            else:
                fields = fn(ctx, pc)
            if fields is not None:
                pc.flags.append(ProductFlag(code=fd.code, reason=fd.reason.format(**fields)))
