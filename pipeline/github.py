"""GitHub as a platform source: the extract in inbox/github/, matched to register products.

Rules: docs/metric-definitions.md, section "Platform sources" (GitHub). A repository named edp-<team>-dp-<x_y>
belongs to a register product, first hit wins:
1. the crosswalk row with source github (product: a register URN, or a NextData name or product key);
2. the repository's data_product_urn custom property equals the register URN;
3. dp-<team>-x-y, x-y or x-y-nxd is the last segment of the register URN, or a NextData name of its platform product.
Tooling teams and names matching any exclude_patterns entry (registry/platform.yaml) are not counted, as for NextData names.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path

from pipeline.contracts import DQItem, SourceStatus
from pipeline.readers.github import FAILED, GhDeployment, GithubRepo, GithubRun, read_github
from pipeline.registry import PlatformConfig

FOLDER = "github"
WINDOW_DAYS = 30
STALE_DAYS = 7
_REPO_NAME = re.compile(r"^edp-([a-z0-9]+)-dp-(.+)$")


@dataclass
class GithubSources:
    run: GithubRun | None = None
    issues: list[DQItem] = field(default_factory=list)
    sources: list[SourceStatus] = field(default_factory=list)


def load_github(inbox_dir: Path) -> GithubSources:
    folder = inbox_dir / FOLDER
    if not folder.is_dir():
        return GithubSources()
    run, issues = read_github(folder)
    as_of = run.fetched_at.isoformat(timespec="seconds") if run else ""
    status = SourceStatus("GitHub", f"{FOLDER}/repositories.csv", as_of, "ok" if run and run.repos else "missing", len(run.repos) if run else 0)
    return GithubSources(run=run, issues=issues, sources=[status])


# ---------------------------------------------------------------------------
# Matching
# ---------------------------------------------------------------------------


def repo_names(repo: str) -> tuple[str | None, list[str]]:
    """edp-claims-dp-channel_partner -> ('claims', ['dp-claims-channel-partner', 'channel-partner', 'channel-partner-nxd'])."""
    m = _REPO_NAME.match(repo.lower())
    if not m:
        return None, [repo.lower()]
    team, rest = m.group(1), m.group(2).replace("_", "-")
    return team, [f"dp-{team}-{rest}", rest, f"{rest}-nxd"]


def exclusion(repo: str, cfg: PlatformConfig) -> str | None:
    team, names = repo_names(repo)
    if team in cfg.exclude_teams:
        return f"{cfg.teams.get(team, team)} tooling, not a business data product"
    for pat, reason in cfg.exclude_patterns:
        if any(pat.search(n) for n in names):
            return reason
    return None


@dataclass
class GithubMatch:
    by_urn: dict[str, GithubRepo] = field(default_factory=dict)
    rule: dict[str, str] = field(default_factory=dict)  # repo -> crosswalk | data_product_urn | name
    unmatched: list[GithubRepo] = field(default_factory=list)  # counted repositories with no register product
    duplicates: list[tuple[GithubRepo, str, GithubRepo]] = field(default_factory=list)  # (repo, urn, the repo the product kept)
    ignored: dict[str, str] = field(default_factory=dict)  # repo -> reason it is not counted


def _product_names(pc) -> list[str]:
    names = [pc.urn]
    if pc.urn.lower().startswith("nxd:"):
        names.append(pc.urn[4:])
    names.append(pc.urn.rsplit(":", 1)[-1])
    pp = pc.platform
    if pp is not None:
        names += [pp.key, *pp.names, *pp.keyids]
    return names


def match_repos(run: GithubRun, products: list, crosswalk: dict, cfg: PlatformConfig) -> GithubMatch:
    """products: ProductCtx list (platform products attached when platform files are present)."""
    index: dict[str, str] = {}
    for pc in products:
        for n in _product_names(pc):
            index.setdefault(n.lower(), pc.urn)

    out = GithubMatch()
    proposals: dict[str, list[tuple[int, str, GithubRepo, str]]] = {}
    for repo in run.repos.values():
        xw = crosswalk.get(("github", repo.name))
        if xw is not None and xw.include is False:
            out.ignored[repo.name] = xw.reason or "Not counted (crosswalk)"
            continue
        if xw is None or xw.include is None:
            reason = exclusion(repo.name, cfg)
            if reason:
                out.ignored[repo.name] = reason
                continue
        target, rank, rule = None, 9, ""
        if xw is not None and xw.product:
            target, rank, rule = index.get(xw.product.lower()), 0, "crosswalk"
        if target is None and repo.urn:
            target, rank, rule = index.get(repo.urn.lower()), 1, "data_product_urn"
        if target is None:
            target = next((index[n] for n in repo_names(repo.name)[1] if n in index), None)
            rank, rule = 2, "name"
        if target is None:
            out.unmatched.append(repo)
        else:
            proposals.setdefault(target, []).append((rank, repo.name, repo, rule))
    for urn, props in proposals.items():
        props.sort(key=lambda p: (p[0], p[1]))
        kept = props[0][2]
        out.by_urn[urn] = kept
        out.rule[kept.name] = props[0][3]
        for _, _, repo, rule in props[1:]:
            out.rule[repo.name] = rule
            out.duplicates.append((repo, urn, kept))
    out.unmatched.sort(key=lambda r: r.name)
    return out


# ---------------------------------------------------------------------------
# Facts per repository (as seen on the as-of date)
# ---------------------------------------------------------------------------


def in_window(d: GhDeployment, as_of: date, days: int = WINDOW_DAYS) -> bool:
    return as_of - timedelta(days=days) < d.day <= as_of


def prod_successes(repo: GithubRepo, cfg: PlatformConfig, as_of: date) -> list[GhDeployment]:
    envs = set(cfg.github_prod_environments)
    return [d for d in repo.deployments if d.env in envs and d.outcome == "success" and d.day <= as_of]


def last_prod_deploy(repo: GithubRepo, cfg: PlatformConfig, as_of: date) -> date | None:
    return max((d.day for d in prod_successes(repo, cfg, as_of)), default=None)


def recent(repo: GithubRepo, as_of: date) -> list[GhDeployment]:
    """Deployments with an outcome in the trailing window (pending ones say nothing yet)."""
    return [d for d in repo.deployments if d.outcome != "pending" and in_window(d, as_of)]


def failed(deps: list[GhDeployment]) -> list[GhDeployment]:
    return [d for d in deps if d.outcome in FAILED]
