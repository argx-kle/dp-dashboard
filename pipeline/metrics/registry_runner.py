"""Runs every registry metric at every level and shapes the MetricValue list."""

from __future__ import annotations

from pipeline.context import MetricContext
from pipeline.contracts import MetricValue
from pipeline.metrics import MetricResult
from pipeline.registry import FlagDef, MetricDef


def compute_metrics(ctx: MetricContext, defs: list[MetricDef], flag_defs: list[FlagDef]) -> list[MetricValue]:
    out: list[MetricValue] = []
    behind_def = next((f for f in flag_defs if f.code == "BEHIND"), None)
    results: dict[tuple[str, str], MetricResult] = {}

    for md in defs:
        fn = md.resolve()
        scopes = []
        if "org" in md.levels:
            scopes.append("org")
        if "domain" in md.levels:
            scopes.extend(ctx.domains.ids)
        for scope in scopes:
            res: MetricResult = fn(ctx, scope)
            results[(md.id, scope)] = res
            mv = MetricValue(id=md.id, scope=scope, value=res.value, source=md.source)
            if res.n is not None:
                mv.n = res.n
            if md.min_n and res.values is not None and 0 < (res.n or 0) < md.min_n:
                mv.values = res.values
            if md.compare_to == "target":
                mv.target = ctx.target(scope)
            if res.reason:
                mv.reason = res.reason
            if res.urns is not None:
                mv.urns = res.urns
            out.append(mv)

    # Domain BEHIND flag lives on certified_qtd at domain level.
    if behind_def is not None:
        fn = behind_def.resolve()
        for mv in out:
            if mv.id != "certified_qtd" or mv.scope == "org":
                continue
            forecast = results.get(("g4_forecast", mv.scope))
            fields = fn(ctx, mv.scope, int(mv.value or 0), int(forecast.value or 0) if forecast else 0)
            if fields is not None:
                mv.flag = "BEHIND"
                mv.reason = behind_def.reason.format(**fields)
    return out
