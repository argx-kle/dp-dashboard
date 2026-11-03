"""Orchestration for dp check, dp build and dp approve."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path

from pipeline import SCHEMA_VERSION, TEMPLATE_PATH
from pipeline.changes import compute_changes
from pipeline.checks import run_checks, run_github_checks, run_platform_checks
from pipeline.context import MetricContext, ProductCtx, build_context
from pipeline.contracts import (
    DataQualityItem,
    DomainInfo,
    DQItem,
    FlagDefinition,
    GateRecord,
    GithubSummary,
    Inbox,
    MetricDefinition,
    NextDataDeployment,
    NextDataSummary,
    ComponentScore,
    PlannedGA,
    PlannedGate,
    ProductRow,
    RegistryInfo,
    SignOff,
    Snapshot,
    SourcedDate,
    SourcedNumber,
    SourceInfo,
    ValidationSummary,
)
from pipeline.dates import iso, week_friday
from pipeline.dqreport import render as render_dq
from pipeline.flags import apply_product_flags, product_signal
from pipeline.delivery import compute_delivery
from pipeline.github import GithubMatch, GithubSources, failed, in_window, last_prod_deploy, load_github, match_repos, prod_successes, recent
from pipeline.health import compute_health
from pipeline.inject import inject_file
from pipeline.metrics.registry_runner import compute_metrics
from pipeline.platform import PlatformSources, Resolution, load_platform, platform_checks, resolve
from pipeline.readers.register import read_register
from pipeline.registry import (
    DomainRegistry,
    FlagDef,
    MetricDef,
    PlatformConfig,
    load_domains,
    load_flags,
    load_metrics,
    load_platform_config,
    load_screening,
)
from pipeline.quarters import compute_quarters
from pipeline.reporting import compute_reporting
from pipeline.snapshot import dq_to_model, dumps, to_json_dict, validate
from pipeline.state import State
from pipeline.trend import compute_trend, compute_weekly


@dataclass
class Registries:
    metrics: list[MetricDef]
    flags: list[FlagDef]
    domains: DomainRegistry
    screening: object
    platform: PlatformConfig

    @classmethod
    def load(cls) -> "Registries":
        return cls(load_metrics(), load_flags(), load_domains(), load_screening(), load_platform_config())


@dataclass
class CheckResult:
    inbox: Inbox
    issues: list[DQItem]
    as_of: date
    platform: PlatformSources | None = None
    resolution: Resolution | None = None
    github: GithubSources | None = None
    github_match: GithubMatch | None = None

    @property
    def blockers(self) -> list[DQItem]:
        return [i for i in self.issues if i.severity == "blocker"]

    @property
    def warnings(self) -> list[DQItem]:
        return [i for i in self.issues if i.severity == "warning"]


@dataclass
class BuildResult:
    check: CheckResult
    snapshot: dict | None
    out_dir: Path
    files: list[Path] = field(default_factory=list)

    @property
    def built(self) -> bool:
        return self.snapshot is not None


def resolve_as_of(week_id: str, as_of: date | None) -> date:
    return as_of or week_friday(week_id)


def run_check(inbox_dir: Path, as_of: date, regs: Registries | None = None) -> tuple[CheckResult, MetricContext | None]:
    regs = regs or Registries.load()
    inbox = read_register(inbox_dir, regs.domains)
    issues = list(inbox.issues)
    platform = load_platform(inbox_dir)
    res = None
    if platform.present:
        res = resolve(platform, regs.platform)
        inbox.sources.extend(platform.sources)
        issues.extend(platform.issues)
        issues.extend(platform_checks(platform, res, regs.platform))
    github = load_github(inbox_dir)
    inbox.sources.extend(github.sources)
    issues.extend(github.issues)
    ctx, match = None, None
    if not inbox.blockers:
        ctx = build_context(inbox, as_of, regs.domains)
        ctx.platform_cfg = regs.platform
        if res is not None:
            ctx.has_validation = bool(platform.validation)
            ctx.has_nextdata = platform.has_listing
            for pc in ctx.products:
                pc.platform = res.match(pc.urn)
        issues.extend(run_checks(inbox, as_of, regs.screening, {pc.urn: pc.d for pc in ctx.products}))
        if res is not None:
            issues.extend(run_platform_checks(ctx, res, platform, as_of))
        if github.run is not None:
            match = match_repos(github.run, ctx.products, platform.crosswalk or {}, regs.platform)
            ctx.has_github = True
            for pc in ctx.products:
                pc.github = match.by_urn.get(pc.urn)
            issues.extend(run_github_checks(ctx, match, github.run, as_of))
    else:
        issues.extend(run_checks(inbox, as_of, regs.screening, None))
    issues = _dedupe(issues)
    return CheckResult(inbox=inbox, issues=issues, as_of=as_of, platform=platform if res else None, resolution=res, github=github if github.run else None, github_match=match), ctx


def _dedupe(issues: list[DQItem]) -> list[DQItem]:
    seen = set()
    out = []
    for i in issues:
        key = (i.severity, i.rule, i.message, i.urn, i.file, i.row)
        if key not in seen:
            seen.add(key)
            out.append(i)
    order = {"blocker": 0, "warning": 1}
    return sorted(out, key=lambda i: (order[i.severity], i.file or "", i.row or 0, i.rule))


def _slips_from_history(ctx: MetricContext, previous: dict | None, state: State) -> tuple[dict[str, tuple[int, str | None]], dict[str, tuple[int, str | None]]]:
    """Returns (ga_slips, next_gate_slips) keyed by urn -> (slips, baseline_iso)."""
    prev_products = {p["urn"]: p for p in previous["products"]} if previous else {}
    ga: dict[str, tuple[int, str | None]] = {}
    ng: dict[str, tuple[int, str | None]] = {}
    for pc in ctx.products:
        prev = prev_products.get(pc.urn, {})
        if pc.p.planned_ga_date is not None:
            cur = pc.p.planned_ga_date.isoformat()
            b = state.baseline(pc.urn, "GA")
            baseline = b.baseline_date if b else (prev.get("plannedGA", {}).get("baselineDate") or cur)
            prev_ga = prev.get("plannedGA")
            slips = prev_ga["slips"] if prev_ga else 0
            if prev_ga and cur > prev_ga["plannedDate"]:
                slips += 1
            ga[pc.urn] = (slips, baseline)
        nxt = pc.d.next_gate()
        if nxt and pc.p.planned_next_gate_date is not None:
            cur = pc.p.planned_next_gate_date.isoformat()
            b = state.baseline(pc.urn, nxt)
            prev_ng = prev.get("nextGate")
            same_gate = bool(prev_ng and prev_ng["gate"] == nxt)
            baseline = b.baseline_date if b else ((prev_ng["baselineDate"] if same_gate else None) or cur)
            slips = prev_ng["slips"] if same_gate else 0
            if same_gate and cur > prev_ng["plannedDate"]:
                slips += 1
            ng[pc.urn] = (slips, baseline)
    return ga, ng


def _product_rows(ctx: MetricContext, ga_slips: dict, ng_slips: dict, flag_defs: list[FlagDef]) -> list[ProductRow]:
    rows: list[ProductRow] = []

    def order(pc: ProductCtx):
        return (ctx.domains.ids.index(pc.domain), pc.p.name.lower())

    for pc in sorted(ctx.products, key=order):
        p, d = pc.p, pc.d
        gates = [GateRecord(gate=g.gate, date=g.date.isoformat(), iteration=g.iteration, g5Path=g.g5_path, evidenceUrl=g.evidence_url) for g in d.gates]
        next_gate = None
        nxt = d.next_gate()
        if nxt and p.planned_next_gate_date is not None:
            slips, baseline = ng_slips.get(pc.urn, (0, None))
            next_gate = PlannedGate(
                gate=nxt,
                plannedDate=p.planned_next_gate_date.isoformat(),
                baselineDate=baseline or p.planned_next_gate_date.isoformat(),
                slips=slips,
                overdueDays=(ctx.as_of - p.planned_next_gate_date).days,
            )
        planned_ga = None
        if p.planned_ga_date is not None:
            slips, baseline = ga_slips.get(pc.urn, (0, None))
            planned_ga = PlannedGA(plannedDate=p.planned_ga_date.isoformat(), baselineDate=baseline or p.planned_ga_date.isoformat(), slips=slips)
        rows.append(
            ProductRow(
                urn=p.urn,
                name=p.name,
                domain=p.domain,
                dpo=p.dpo,
                stage=d.stage,
                status=d.status,
                lifecycle=d.lifecycle,
                signal=product_signal(pc, flag_defs),
                iteration=d.iteration,
                gates=gates,
                lastGate=gates[-1] if gates else None,
                firstG4Date=iso(d.first_g4),
                daysInStage=d.days_in_stage,
                nextGate=next_gate,
                plannedGA=planned_ga,
                inputProducts=list(p.input_products),
                consumedByProducts=list(pc.consumed_by),
                namedConsumers=p.named_consumers,
                activeUsers30d=SourcedNumber(value=p.active_users_30d, source="self-reported") if p.active_users_30d is not None else None,
                firstConsumerDate=SourcedDate(value=p.first_consumer_date.isoformat(), source="self-reported") if p.first_consumer_date else None,
                flags=list(pc.flags),
                **_platform_fields(pc, ctx),
                dpoComment=p.dpo_comment,
                reviewedOn=iso(p.reviewed_on),
                cancelledOn=iso(p.cancelled_on),
            )
        )
    return rows


def _github_summary(pc: ProductCtx, ctx: MetricContext) -> GithubSummary:
    repo, cfg, as_of = pc.github, ctx.platform_cfg, ctx.as_of
    deps = recent(repo, as_of)
    return GithubSummary(
        repo=repo.name,
        url=repo.url,
        lastProdDeploy=iso(last_prod_deploy(repo, cfg, as_of)),
        prodDeploys30d=len([d for d in prod_successes(repo, cfg, as_of) if in_window(d, as_of)]),
        deploys30d=len(deps),
        failed30d=len(failed(deps)),
    )


def _platform_fields(pc: ProductCtx, ctx: MetricContext) -> dict:
    out: dict = {}
    if ctx.has_github and pc.github is not None:
        out["github"] = _github_summary(pc, ctx)
    pp = pc.platform
    if pp is None:
        return out
    cfg = ctx.platform_cfg
    if ctx.has_nextdata:
        deps = sorted(pp.deployments, key=lambda d: (cfg.env_index(d.env), d.name, d.version))
        best = pp.best_deployment(cfg)
        out["nextdata"] = NextDataSummary(
            names=list(pp.names),
            runtime=pp.runtime,
            env=pp.best_env(cfg),
            url=best.url if best else None,
            team=cfg.teams.get(pp.team) if pp.team else None,
            deployments=[NextDataDeployment(name=d.name, env=d.env, version=d.version, state=d.state, url=d.url) for d in deps],
        )
    if pp.platform_domain:
        out["platformDomain"] = pp.platform_domain
    rec = pp.validation
    if rec is not None and pp.run_date is not None:
        out["validation"] = ValidationSummary(
            lastRun=pp.run_date.isoformat(),
            p1Findings=rec.p1_findings,
            score=rec.score,
            components=[ComponentScore(label=label, score=score) for label, score in rec.components] or None,
            ownerStatus=rec.owner_status,
            keyids=list(pp.keyids) or None,
        )
    return out


def _registry_info(regs: Registries) -> RegistryInfo:
    return RegistryInfo(
        metrics=[
            MetricDefinition(
                id=m.id, label=m.label, shortLabel=m.short_label, definition=m.definition, levels=m.levels,
                unit=m.unit, compareTo=m.compare_to, minN=m.min_n, execTile=m.exec_tile, order=m.order, coverage=m.coverage,
            )
            for m in regs.metrics
        ],
        flags=[FlagDefinition(code=f.code, label=f.label, level=f.level, definition=f.definition, signal=f.signal) for f in regs.flags],
    )


def assemble(ctx: MetricContext, check: CheckResult, week_id: str, regs: Registries, state: State, generated_at: datetime | None = None) -> dict:
    previous = state.latest_approved_before(week_id)
    ga_slips, ng_slips = _slips_from_history(ctx, previous, state)
    apply_product_flags(ctx, regs.flags, ga_slips)
    metrics = compute_metrics(ctx, regs.metrics, regs.flags)
    quarters, past_health = compute_quarters(check.inbox, ctx, regs.metrics, regs.flags)
    snapshot = Snapshot(
        schemaVersion=SCHEMA_VERSION,
        weekId=week_id,
        asOfDate=ctx.as_of.isoformat(),
        quarter=ctx.quarter,
        generatedAt=(generated_at or datetime.now(timezone.utc)).isoformat(timespec="seconds"),
        signOff=SignOff(status="draft"),
        domains=[DomainInfo(id=d.id, name=d.name, area=d.area) for d in regs.domains.domains],
        sources=[SourceInfo(name=s.name, file=s.file, asOf=s.as_of, status=s.status, rows=s.rows) for s in check.inbox.sources],
        registry=_registry_info(regs),
        metrics=metrics,
        products=_product_rows(ctx, ga_slips, ng_slips, regs.flags),
        trend=compute_trend(ctx),
        changes=[],
        dataQuality=[DataQualityItem(**i) for i in dq_to_model(check.issues)],
        reporting=compute_reporting(ctx),
        health=past_health + compute_health(ctx),
        weekly=compute_weekly(ctx),
        quarters=quarters,
        delivery=compute_delivery(check.github.run, check.github_match, regs.platform, ctx.as_of) if check.github and check.github_match else None,
    )
    data = to_json_dict(snapshot)
    data["changes"] = compute_changes(data, previous)
    return data


def run_build(
    inbox_dir: Path,
    week_id: str,
    out_root: Path,
    state_dir: Path,
    as_of: date | None = None,
    template_path: Path = TEMPLATE_PATH,
    regs: Registries | None = None,
    generated_at: datetime | None = None,
) -> BuildResult:
    regs = regs or Registries.load()
    as_of_date = resolve_as_of(week_id, as_of)
    check, ctx = run_check(inbox_dir, as_of_date, regs)
    out_dir = out_root / week_id
    out_dir.mkdir(parents=True, exist_ok=True)
    result = BuildResult(check=check, snapshot=None, out_dir=out_dir)

    if check.blockers or ctx is None:
        (out_dir / "dq-report.html").write_text(render_dq(week_id, as_of_date.isoformat(), check.inbox.sources, check.issues, built=False, resolution=check.resolution), encoding="utf-8")
        result.files.append(out_dir / "dq-report.html")
        return result

    state = State(state_dir)
    data = assemble(ctx, check, week_id, regs, state, generated_at)
    schema_issues = validate(data)
    if schema_issues:
        check.issues.extend(schema_issues)
        (out_dir / "dq-report.html").write_text(render_dq(week_id, as_of_date.isoformat(), check.inbox.sources, check.issues, built=False, resolution=check.resolution), encoding="utf-8")
        result.files.append(out_dir / "dq-report.html")
        return result

    json_text = dumps(data)
    (out_dir / "snapshot.json").write_text(json_text, encoding="utf-8")
    result.files.append(out_dir / "snapshot.json")
    if template_path.exists():
        inject_file(template_path, json_text, out_dir / "index.html")
        result.files.append(out_dir / "index.html")
    else:
        check.issues.append(DQItem("warning", "NO_TEMPLATE", f"App template not found at {template_path}; index.html not written (run `sh scripts/setup.sh`, or `npm run build` in app/)"))
    (out_dir / "dq-report.html").write_text(render_dq(week_id, as_of_date.isoformat(), check.inbox.sources, check.issues, built=True, resolution=check.resolution), encoding="utf-8")
    result.files.append(out_dir / "dq-report.html")
    result.snapshot = data
    return result


def run_approve(week_id: str, approved_by: str, out_root: Path, state_dir: Path, inbox_dir: Path | None, template_path: Path = TEMPLATE_PATH, now: datetime | None = None) -> Path:
    out_dir = out_root / week_id
    snapshot_path = out_dir / "snapshot.json"
    if not snapshot_path.exists():
        raise FileNotFoundError(f"No draft snapshot at {snapshot_path}; run `dp build --week {week_id}` first")
    if inbox_dir is not None and inbox_dir.exists():
        latest_inbox = max((p.stat().st_mtime for p in inbox_dir.rglob("*") if p.is_file()), default=0.0)
        if latest_inbox > snapshot_path.stat().st_mtime:
            raise RuntimeError("The inbox changed after the draft was built; run `dp build` again before approving")
    data = json.loads(snapshot_path.read_text(encoding="utf-8"))
    if data["signOff"]["status"] == "approved":
        raise RuntimeError(f"{week_id} is already approved by {data['signOff'].get('approvedBy')}")
    data["signOff"] = {"status": "approved", "approvedBy": approved_by, "approvedAt": (now or datetime.now(timezone.utc)).isoformat(timespec="seconds")}
    issues = validate(data)
    if issues:
        raise RuntimeError("Approved snapshot fails schema validation: " + "; ".join(i.message for i in issues))
    json_text = dumps(data)
    snapshot_path.write_text(json_text, encoding="utf-8")
    if template_path.exists():
        inject_file(template_path, json_text, out_dir / "index.html")
    state = State(state_dir)
    saved = state.save_approved(data)
    state.record_baselines(data)
    return saved
