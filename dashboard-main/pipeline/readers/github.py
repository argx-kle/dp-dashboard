"""GitHub extract (dp fetch-github, inbox/github/): data product repositories and their deployments.

One record per repository with every deployment and its outcome. A deployment's outcome is its latest terminal
status (success, failure or error); GitHub marks a superseded success inactive, and queued or in_progress say
nothing yet, so those are ignored. A deployment with no terminal status is pending. Optional input: problems
are warnings.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path

from pipeline.contracts import DQItem
from pipeline.readers.base import normalise_header, read_csv_rows

TERMINAL = {"success", "failure", "error"}
FAILED = {"failure", "error"}
MAX_FETCH_LINES = 5  # more unavailable requests than this are summarised in one line


@dataclass
class GhDeployment:
    id: str
    env: str
    created_at: datetime
    outcome: str  # success | failure | error | pending

    @property
    def day(self) -> date:
        return self.created_at.date()


@dataclass
class GithubRepo:
    name: str
    url: str | None = None
    archived: bool = False
    urn: str | None = None
    deployments: list[GhDeployment] = field(default_factory=list)


@dataclass
class GithubRun:
    fetched_at: datetime
    org: str | None
    repos: dict[str, GithubRepo]


def _rows(path: Path) -> list[dict[str, str]]:
    headers, body = read_csv_rows(path)
    norm = [normalise_header(h) for h in headers]
    return [dict(zip(norm, [*r, *[""] * (len(norm) - len(r))])) for r in body if any(c.strip() for c in r)]


def _time(value: str) -> datetime | None:
    try:
        t = datetime.fromisoformat((value or "").strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    return t if t.tzinfo else t.replace(tzinfo=timezone.utc)


def read_github(folder: Path) -> tuple[GithubRun | None, list[DQItem]]:
    repo_file = folder / "repositories.csv"
    if not repo_file.is_file():
        return None, [DQItem("warning", "UNREADABLE", "The GitHub folder has no repositories.csv; run `dp fetch-github`", file="github/")]
    issues: list[DQItem] = []
    try:
        repos: dict[str, GithubRepo] = {}
        for r in _rows(repo_file):
            name = r.get("repo_name", "").strip()
            if name:
                repos[name] = GithubRepo(name=name, url=r.get("html_url") or None, archived=r.get("archived", "").lower() == "true", urn=(r.get("data_product_urn") or "").strip() or None)

        statuses: dict[str, list[tuple[datetime, str]]] = {}
        if (folder / "deployment_statuses.csv").is_file():
            for r in _rows(folder / "deployment_statuses.csv"):
                t = _time(r.get("created_at", ""))
                state = r.get("state", "").strip().lower()
                if t is not None and state in TERMINAL:
                    statuses.setdefault(r.get("deployment_id", "").strip(), []).append((t, state))

        bad = 0
        if (folder / "deployments.csv").is_file():
            for r in _rows(folder / "deployments.csv"):
                repo = repos.get(r.get("repo_name", "").strip())
                t = _time(r.get("created_at", ""))
                if repo is None or t is None:
                    bad += 1
                    continue
                dep_id = r.get("deployment_id", "").strip()
                terminal = sorted(statuses.get(dep_id, []))
                repo.deployments.append(GhDeployment(id=dep_id, env=r.get("environment", "").strip(), created_at=t, outcome=terminal[-1][1] if terminal else "pending"))
        if bad:
            issues.append(DQItem("warning", "GH_FETCH", f"{bad} deployments name no known repository or have no date and were ignored", file="github/deployments.csv"))

        fetched_at, org = None, None
        if (folder / "fetch.csv").is_file():
            meta = _rows(folder / "fetch.csv")
            if meta:
                fetched_at, org = _time(meta[0].get("fetched_at", "")), meta[0].get("org") or None
        if fetched_at is None:
            fetched_at = datetime.fromtimestamp(repo_file.stat().st_mtime, tz=timezone.utc)

        if (folder / "issues.csv").is_file():
            unavailable = _rows(folder / "issues.csv")
            if len(unavailable) > MAX_FETCH_LINES:
                issues.append(DQItem("warning", "GH_FETCH", f"{len(unavailable)} GitHub requests were unavailable when the extract ran; affected values are blank (see issues.csv)", file="github/issues.csv"))
            else:
                for r in unavailable:
                    issues.append(DQItem("warning", "GH_FETCH", f"GitHub request unavailable when the extract ran: {r.get('request', '')}: {r.get('detail', '')}", file="github/issues.csv"))
    except Exception as exc:  # noqa: BLE001 - an unreadable optional file is a warning
        return None, [DQItem("warning", "UNREADABLE", f"The GitHub extract could not be read: {exc}", file="github/")]
    return GithubRun(fetched_at=fetched_at, org=org, repos=repos), issues
