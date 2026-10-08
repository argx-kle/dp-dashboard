"""Data-quality rules. Blockers stop `dp build`; warnings go to the report and the snapshot."""

from __future__ import annotations

from collections import defaultdict
from datetime import date

from pipeline.contracts import DQItem, GateEvent, Inbox, Product
from pipeline.lifecycle import GATE_INDEX, Derived, sort_events
from pipeline.registry import Screening


def run_checks(inbox: Inbox, as_of: date, screening: Screening, derived: dict[str, Derived] | None = None) -> list[DQItem]:
    issues: list[DQItem] = []
    products_file = next((s.file for s in inbox.sources if s.name == "Products"), "Products")
    events_file = next((s.file for s in inbox.sources if s.name == "GateEvents"), "GateEvents")

    # --- Products ----------------------------------------------------------
    seen: dict[str, int] = {}
    for p in inbox.products:
        if p.urn in seen:
            issues.append(DQItem("blocker", "DUPLICATE_URN", f"URN also appears on row {seen[p.urn]}", urn=p.urn, file=products_file, row=p.row))
        else:
            seen[p.urn] = p.row
        hit = screening.match(p.dpo_comment)
        if hit:
            issues.append(DQItem("blocker", "SCREENING", f"dpo_comment matches screening rule ({hit}); remove personal or health data", urn=p.urn, file=products_file, row=p.row))

    known_urns = set(seen)
    # When the Products table itself is blocked no URN is known; reporting every event as unknown is noise.
    products_blocked = any(
        i.severity == "blocker" and i.rule in {"MISSING_TABLE", "MISSING_COLUMN", "UNREADABLE"} and i.file == products_file
        for i in inbox.issues
    )

    # --- Gate events -------------------------------------------------------
    by_urn: dict[str, list[GateEvent]] = defaultdict(list)
    for e in inbox.gate_events:
        if e.urn not in known_urns and products_blocked:
            continue
        if e.urn not in known_urns:
            issues.append(DQItem("blocker", "UNKNOWN_URN", "Gate event for a URN that is not on the Products sheet", urn=e.urn, file=events_file, row=e.row))
            continue
        if e.date_passed > as_of:
            issues.append(DQItem("blocker", "FUTURE_DATE", f"{e.gate} dated {e.date_passed} is after the as-of date {as_of}", urn=e.urn, file=events_file, row=e.row))
        if not e.evidence_url:
            issues.append(DQItem("warning", "NO_EVIDENCE", f"{e.gate} passed without an evidence link", urn=e.urn, file=events_file, row=e.row))
        by_urn[e.urn].append(e)

    for urn, events in by_urn.items():
        _check_order(urn, sort_events(events), events_file, issues)

    # --- Plans and usage (need lifecycle) ----------------------------------
    if derived:
        by_product = {p.urn: p for p in inbox.products}
        for urn, d in derived.items():
            p = by_product[urn]
            _check_plan(p, d, products_file, issues)
            if d.live and p.active_users_30d is None:
                issues.append(DQItem("warning", "NO_USAGE", "Live product without an active-users figure", urn=urn, file=products_file, row=p.row))
    return issues


def _check_order(urn: str, events: list[GateEvent], file: str, issues: list[DQItem]) -> None:
    gates = {e.gate for e in events}
    if gates & {"G2", "G3", "G4"} and "G1" not in gates:
        first = next(e for e in events if e.gate in {"G2", "G3", "G4"})
        issues.append(DQItem("blocker", "NO_G1", f"{first.gate} recorded without a G1 Intake", urn=urn, file=file, row=first.row))

    last_idx = 0  # highest gate index in the current iteration
    had_g4 = False
    retired = False
    for e in events:
        idx = GATE_INDEX[e.gate]
        if retired:
            issues.append(DQItem("blocker", "GATE_ORDER", f"{e.gate} recorded after G6 Retire", urn=urn, file=file, row=e.row))
            continue
        if e.gate == "G5":
            if not had_g4:
                issues.append(DQItem("blocker", "GATE_ORDER", "G5 Revise before any G4 Certify", urn=urn, file=file, row=e.row))
            last_idx = 1  # a new iteration: G2..G4 may follow
            continue
        if e.gate == "G6":
            if not had_g4:
                issues.append(DQItem("blocker", "GATE_ORDER", "G6 Retire before any G4 Certify (use cancelled_on for products stopped before GA)", urn=urn, file=file, row=e.row))
            retired = True
            continue
        if idx <= last_idx:
            issues.append(DQItem("blocker", "GATE_ORDER", f"{e.gate} on {e.date_passed} comes after a later gate in the same iteration", urn=urn, file=file, row=e.row))
        last_idx = max(last_idx, idx)
        if e.gate == "G4":
            had_g4 = True


def _check_plan(p: Product, d: Derived, file: str, issues: list[DQItem]) -> None:
    if not d.active:
        return
    nxt = d.next_gate()
    last = d.last_gate
    if nxt is not None and p.planned_next_gate_date is None:
        issues.append(DQItem("warning", "NO_PLAN", f"No planned date for the next gate ({nxt})", urn=p.urn, file=file, row=p.row))
    if p.planned_next_gate_date is not None and last is not None and p.planned_next_gate_date < last.date:
        issues.append(DQItem("warning", "STALE_PLAN", f"planned_next_gate_date {p.planned_next_gate_date} is before the last gate passed ({last.gate} on {last.date})", urn=p.urn, file=file, row=p.row))
    if d.first_g4 is None and p.planned_ga_date is None:
        issues.append(DQItem("warning", "NO_PLAN", "No planned GA date", urn=p.urn, file=file, row=p.row))


def run_platform_checks(ctx, res, src, as_of: date) -> list[DQItem]:
    """Register against platform: products missing on either side, Live without production, stale validation.

    ctx is the MetricContext with platform products attached; res the Resolution; src the PlatformSources.
    """
    from pipeline.platform import VAL_STALE_DAYS

    issues: list[DQItem] = []
    products_file = "Products"
    list_file = next((s.file for s in src.sources if s.name == "NextData listing"), "nextdata")
    matched: set[str] = set()
    for pc in ctx.products:
        pp = pc.platform
        if pp is not None:
            matched.add(pp.key)
            if not pp.include:
                issues.append(DQItem("warning", "ND_EXCLUDED", f"On the register, but the platform rules leave it out: {pp.reason}", urn=pc.urn, file=products_file, row=pc.p.row))
        pending = pc.urn.lower().startswith("pending:")
        if src.has_listing and not pending and (pp is None or not pp.deployments):
            issues.append(DQItem("warning", "ND_NOT_IN_CATALOG", "Not in the NextData listing", urn=pc.urn, file=products_file, row=pc.p.row))
        if pc.d.live and pp is not None and src.has_listing:
            if not any(d.env == "prod" and d.state == "Started" for d in pp.deployments):
                env = pp.best_env(ctx.platform_cfg) or "no environment"
                issues.append(DQItem("warning", "ND_STATUS", f"Live in the register, but NextData shows no running production deployment ({pp.runtime} in {env})", urn=pc.urn, file=list_file))
    for pp in res.included:
        if pp.key not in matched:
            team = f"({ctx.platform_cfg.teams.get(pp.team, pp.team) if pp.team else 'no team'})"
            name = pp.display_name if pp.display_name.endswith(team) else f"{pp.display_name} {team}"  # two same-named products already carry their team
            issues.append(DQItem("warning", "ND_NOT_IN_REGISTER", f"{name} is counted on the platform but has no row on the Products sheet", urn=f"nxd:{pp.key}", file=products_file))
    for run in src.validation:
        if run.run_date and (as_of - run.run_date).days > VAL_STALE_DAYS:
            issues.append(DQItem("warning", "VAL_STALE", f"Validation results are from {run.run_date}, more than {VAL_STALE_DAYS} days before {as_of}", file=run.file))
    return issues
