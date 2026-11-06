"""Delivery: every data product repository in the GitHub extract and how it deploys, register or not.

Built from the extract alone, so it shows real numbers while the register is still being filled. A repository
is counted unless it is tooling, a template or a test (pipeline/github.py exclusion(), or the crosswalk);
excluded repositories are listed but left out of every total. Delivery health (failing now, production commits
that skipped validation, recovery time, onboarding) comes from the same deployments. Rules:
docs/metric-definitions.md, sections "Delivery" and "Delivery health".
"""

from __future__ import annotations

from collections import Counter
from datetime import date, timedelta
from statistics import median

from pipeline.contracts import Delivery, DeliveryBroken, DeliveryBypass, DeliveryEnv, DeliveryRepo, DeliveryTeam, DeliveryTotals, DeliveryWeek, RepoEnv
from pipeline.dates import iso, week_of
from pipeline.github import (
    WINDOW_DAYS,
    GithubMatch,
    failed,
    failing_streaks,
    in_window,
    reached,
    recent,
    recovery_hours,
    repo_names,
    unvalidated_prod,
    weekly_counts,
    weeks,
)
from pipeline.readers.github import FAILED, GhDeployment, GithubRepo, GithubRun
from pipeline.registry import PlatformConfig


def _envs(run: GithubRun, cfg: PlatformConfig) -> list[str]:
    """The promotion path in its configured order, then the other environments by number of deployments."""
    seen = Counter(d.env for r in run.repos.values() for d in r.deployments)
    path = list(cfg.github_environments)
    return path + [e for e, _ in seen.most_common() if e not in path]


def _repo(repo: GithubRepo, deps: list[GhDeployment], envs: list[str], mondays: list[date], cfg: PlatformConfig, as_of: date, urn: str | None, excluded: str | None) -> DeliveryRepo:
    prod = set(cfg.github_prod_environments)
    window = recent(repo, as_of)
    prod_ok = [d for d in deps if d.env in prod and d.outcome == "success"]
    weekly = weekly_counts(deps, mondays)
    by_env = []
    for e in envs:
        here = [d for d in deps if d.env == e]
        if not here:
            continue
        w = [d for d in window if d.env == e]
        by_env.append(RepoEnv(env=e, lastSuccess=iso(max((d.day for d in here if d.outcome == "success"), default=None)), deploys30d=len(w), failed30d=len(failed(w))))
    return DeliveryRepo(
        name=repo.name,
        url=repo.url,
        team=repo_names(repo.name)[0],
        urn=urn,
        excluded=excluded,
        envs=by_env,
        lastDeploy=iso(max((d.day for d in deps), default=None)),
        lastFailure=iso(max((d.day for d in deps if d.outcome in FAILED), default=None)),
        lastProdDeploy=iso(max((d.day for d in prod_ok), default=None)),
        prodDeploys=len(prod_ok),
        deploys30d=len(window),
        failed30d=len(failed(window)),
        weekly=weekly,
        reached=reached(repo, cfg, as_of),
        failingNow=[s.env for s in failing_streaks(repo, cfg, as_of)],
    )


def compute_delivery(run: GithubRun, match: GithubMatch, cfg: PlatformConfig, as_of: date) -> Delivery:
    envs = _envs(run, cfg)
    prod = set(cfg.github_prod_environments)
    mondays = weeks(as_of)
    urn_of = {r.name: urn for urn, r in match.by_urn.items()} | {r.name: urn for r, urn, _ in match.duplicates}

    repos, counted = [], []
    for repo in sorted(run.repos.values(), key=lambda r: r.name):
        deps = [d for d in repo.deployments if d.day <= as_of]
        row = _repo(repo, deps, envs, mondays, cfg, as_of, urn_of.get(repo.name), match.ignored.get(repo.name))
        repos.append(row)
        if row.excluded is None:
            counted.append((repo, deps, row))

    window = [d for repo, _, _ in counted for d in recent(repo, as_of)]
    prod_window = [d for d in window if d.env in prod]
    last_prod = max(((r.lastProdDeploy, r.name) for _, _, r in counted if r.lastProdDeploy), default=(None, None))

    broken, bypass, recovery = [], [], []
    path_envs = prod_commits = 0
    for repo, deps, row in counted:
        path_envs += sum(1 for e in row.envs if e.env in cfg.github_environments and any(d.env == e.env and d.outcome != "pending" for d in deps))
        for s in failing_streaks(repo, cfg, as_of):
            broken.append(DeliveryBroken(repo=repo.name, urn=row.urn, env=s.env, since=s.since.isoformat(), lastSuccess=iso(s.last_success)))
        skipped, commits = unvalidated_prod(repo, cfg, as_of)
        prod_commits += commits
        bypass += [DeliveryBypass(repo=repo.name, urn=row.urn, sha=d.sha[:7], at=d.day.isoformat()) for d in skipped]
        recovery += recovery_hours(repo, as_of)
    broken.sort(key=lambda b: (b.since, b.repo, b.env))
    bypass.sort(key=lambda b: (b.at, b.repo), reverse=True)
    first_deploy = [min(d.day for d in deps) for _, deps, _ in counted if deps]
    totals = DeliveryTotals(
        repos=len(counted),
        active30d=sum(1 for repo, deps, _ in counted if any(in_window(d, as_of) for d in deps)),
        deploys30d=len(window),
        failed30d=len(failed(window)),
        prodAttempts30d=len(prod_window),
        prodFailed30d=len(failed(prod_window)),
        reachedProd=sum(1 for _, _, r in counted if r.prodDeploys),
        notInRegister=sum(1 for _, _, r in counted if r.urn is None),
        lastProdDeploy=last_prod[0],
        lastProdRepo=last_prod[1],
        brokenNow=len(broken),
        pathEnvs=path_envs,
        bypass30d=len(bypass),
        prodCommits30d=prod_commits,
        recoveryHours30d=round(median(recovery), 1) if recovery else None,
        onboarded=len(first_deploy),
    )

    env_rows = []
    for e in envs:
        w = [d for d in window if d.env == e]
        env_rows.append(
            DeliveryEnv(
                id=e,
                label=cfg.github_environments.get(e, e),
                prod=e in prod,
                path=e in cfg.github_environments,
                repos=sum(1 for _, deps, _ in counted if any(d.env == e and d.outcome == "success" for d in deps)),
                deploys30d=len(w),
                failed30d=len(failed(w)),
            )
        )

    weekly = []
    for m in mondays:
        week = [d for _, deps, _ in counted for d in deps if m <= d.day < m + timedelta(days=7)]
        weekly.append(
            DeliveryWeek(
                week=week_of(m),
                start=m.isoformat(),
                deploys=len(week),
                failed=sum(1 for d in week if d.outcome in FAILED),
                prodSuccess=sum(1 for d in week if d.env in prod and d.outcome == "success"),
                firstDeploys=sum(1 for f in first_deploy if m <= f < m + timedelta(days=7)),
            )
        )

    by_team: dict[str, list[DeliveryRepo]] = {}
    for _, _, r in counted:
        by_team.setdefault(r.team or "other", []).append(r)
    teams = [
        DeliveryTeam(
            team=t,
            label=cfg.teams.get(t, t),
            repos=len(rows),
            deploys30d=sum(r.deploys30d for r in rows),
            failed30d=sum(r.failed30d for r in rows),
            reachedProd=sum(1 for r in rows if r.prodDeploys),
        )
        for t, rows in sorted(by_team.items(), key=lambda kv: (-len(kv[1]), kv[0]))
    ]

    return Delivery(
        fetchedAt=run.fetched_at.isoformat(timespec="seconds"),
        org=run.org,
        windowDays=WINDOW_DAYS,
        envs=env_rows,
        totals=totals,
        weekly=weekly,
        teams=teams,
        repos=repos,
        broken=broken,
        bypass=bypass,
    )
