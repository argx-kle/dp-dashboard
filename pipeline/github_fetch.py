"""dp fetch-github: read the data product repositories of the GitHub org into inbox/github/ (read-only).

Connection: the token comes from GITHUB_TOKEN or GH_TOKEN, else from `gh auth token` (run `gh auth login`
once); it needs the repo and read:org scopes. Behind a TLS-inspecting proxy (Netskope) nothing extra is needed
on Windows: Python's default context loads the Windows certificate store, which holds the proxy's root CA.
Elsewhere set SSL_CERT_FILE to a PEM bundle that contains it.

Only GET requests and read-only GraphQL queries are sent. Deployment statuses come from GraphQL, 100
deployments per call (one REST call per deployment would use most of the hourly limit); a batch that fails
falls back to REST. What the files mean: docs/metric-definitions.md, section "Platform sources".
"""

from __future__ import annotations

import base64
import concurrent.futures as cf
import csv
import os
import re
import ssl
import subprocess
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import requests

API = "https://api.github.com"
TLS_HINT = (
    "Python does not trust the certificate presented for api.github.com. On a corporate network "
    "(Netskope, Zscaler) export the proxy root CA to a PEM file and set SSL_CERT_FILE to it."
)

# Columns of each file in inbox/github/. pipeline/readers/github.py reads them.
TABLES = {
    "repositories": ["repo_id", "repo_name", "full_name", "html_url", "archived", "data_product_urn", "data_product_urn_source"],
    "deployments": ["repo_name", "deployment_id", "environment", "production_environment", "sha", "created_at"],
    "deployment_statuses": ["repo_name", "deployment_id", "state", "created_at", "source"],
    "issues": ["request", "detail"],
    "fetch": ["fetched_at", "org", "login", "repos"],
}

STATUS_QUERY = """query($ids: [ID!]!) { nodes(ids: $ids) { ... on Deployment {
  databaseId statuses(first: 100) { nodes { state createdAt } } } } }"""


class FetchError(RuntimeError):
    """The extract cannot run: no token, no access or an untrusted certificate."""


def github_token() -> tuple[str, str]:
    """(token, where it came from)."""
    for var in ("GITHUB_TOKEN", "GH_TOKEN"):
        if os.environ.get(var, "").strip():
            return os.environ[var].strip(), var
    try:
        tok = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        tok = ""
    if not tok:
        raise FetchError("No GitHub token found: run `gh auth login` or set GITHUB_TOKEN")
    return tok, "gh auth token"


def _ssl_context() -> ssl.SSLContext:
    # create_default_context() loads the OS trust store on Windows, which holds the corporate proxy CA.
    ctx = ssl.create_default_context(cafile=os.environ.get("SSL_CERT_FILE") or os.environ.get("REQUESTS_CA_BUNDLE"))
    ctx.verify_flags &= ~getattr(ssl, "VERIFY_X509_STRICT", 0)  # proxy CAs often lack key usage (Python 3.13+)
    return ctx


class _Adapter(requests.adapters.HTTPAdapter):
    def init_poolmanager(self, *a, **kw):
        kw["ssl_context"] = _ssl_context()
        return super().init_poolmanager(*a, **kw)

    def proxy_manager_for(self, *a, **kw):
        kw["ssl_context"] = _ssl_context()
        return super().proxy_manager_for(*a, **kw)


class ReadOnlySession(requests.Session):
    """Refuses anything but GET, and POST to the GraphQL endpoint (used only for read queries)."""

    def __init__(self, graphql_url: str):
        super().__init__()
        self.graphql_url = graphql_url

    def request(self, method, url, *a, **kw):
        if method.upper() != "GET" and not (method.upper() == "POST" and url == self.graphql_url):
            raise RuntimeError(f"blocked non-read request: {method} {url}")
        return super().request(method, url, *a, **kw)


def default_session(api: str = API) -> ReadOnlySession:
    s = ReadOnlySession(api + "/graphql")
    s.mount("https://", _Adapter(pool_maxsize=16))
    return s


@dataclass
class FetchResult:
    tables: dict[str, list[dict]]
    login: str
    rate_remaining: object = "?"
    seconds: float = 0.0
    issues: list[dict] = field(default_factory=list)


def _joined(v) -> str | None:
    if v is None or v == "":
        return None
    return "; ".join(str(x) for x in v) if isinstance(v, list) else str(v)


class GitHub:
    """Read-only client for one org. Unavailable requests are recorded in `issues`; they never stop the run."""

    def __init__(self, token: str, org: str, session: requests.Session | None = None, api: str = API, sleep: Callable[[float], None] = time.sleep):
        self.org = org
        self.api = api
        self.graphql_url = api + "/graphql"
        self.session = session or default_session(api)
        self.session.headers.update({"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28", "Authorization": f"Bearer {token}"})
        self.sleep = sleep
        self.issues: list[dict] = []
        self._lock = threading.Lock()

    def issue(self, request: str, detail: str) -> None:
        with self._lock:
            self.issues.append({"request": request, "detail": detail})

    # -- Transport ------------------------------------------------------------

    def _wait_for_rate_limit(self, r: requests.Response) -> bool:
        if r.status_code not in (403, 429):
            return False
        if r.headers.get("retry-after"):
            wait = int(r.headers["retry-after"])
        elif r.headers.get("x-ratelimit-remaining") == "0":
            wait = int(r.headers.get("x-ratelimit-reset", time.time() + 60)) - int(time.time())
        else:
            return False
        wait = min(max(wait, 1) + 1, 3700)
        print(f"\n  rate limited, waiting {wait}s", flush=True)
        self.sleep(wait)
        return True

    def get(self, path: str, quiet404: bool = False, **params):
        """GET a REST path; parsed JSON, or None (and an issue) when unavailable."""
        why = None
        for attempt in range(8):
            try:
                r = self.session.get(self.api + path, params=params, timeout=60)
            except requests.exceptions.SSLError as exc:
                raise FetchError(f"TLS error: {exc}\n{TLS_HINT}") from exc
            except requests.exceptions.RequestException as exc:
                why = type(exc).__name__
                self.sleep(min(2**attempt, 30))
                continue
            if self._wait_for_rate_limit(r):
                continue
            if r.status_code in (500, 502, 503, 504):
                why = r.status_code
                self.sleep(min(2**attempt, 30))
                continue
            break
        else:
            self.issue(path, f"gave up after retries ({why})")
            return None
        if r.status_code >= 400:
            if not (quiet404 and r.status_code == 404):
                self.issue(path, f"HTTP {r.status_code}: {r.text[:150]}")
            return None
        return r.json()

    def all_pages(self, path: str, key: str | None = None, quiet404: bool = False, **params):
        """Every item of a paginated REST list (key: the list field of a wrapped response); None if unavailable."""
        out, page = [], 1
        while True:
            d = self.get(path, quiet404=quiet404, per_page=100, page=page, **params)
            items = (d or {}).get(key) if key and isinstance(d, dict) else d
            if not isinstance(items, list):
                return out if page > 1 else None
            out += items
            if len(items) < 100:
                return out
            page += 1

    def graphql(self, query: str, **variables):
        assert not query.lstrip().startswith("mutation"), "read-only: mutations are not allowed"
        for attempt in range(5):
            try:
                r = self.session.post(self.graphql_url, json={"query": query, "variables": variables}, timeout=120)
            except requests.exceptions.SSLError as exc:
                raise FetchError(f"TLS error: {exc}\n{TLS_HINT}") from exc
            except requests.exceptions.RequestException:
                self.sleep(2**attempt)
                continue
            if self._wait_for_rate_limit(r):
                continue
            if r.status_code in (500, 502, 503, 504):
                self.sleep(2**attempt)
                continue
            break
        else:
            self.issue("graphql", "gave up after retries")
            return None
        body = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
        if r.status_code >= 400 or body.get("errors"):
            self.issue("graphql", f"HTTP {r.status_code}: {str(body.get('errors') or r.text)[:150]}")
        return body.get("data")

    # -- Connection -----------------------------------------------------------

    def check_connection(self) -> dict:
        """login, org membership state and role, REST rate limit. Raises FetchError when the token is refused."""
        user = self.get("/user")
        if not user:
            raise FetchError(f"Cannot authenticate to GitHub: {self.issues[-1]['detail'] if self.issues else 'no response'}")
        member = self.get(f"/user/memberships/orgs/{self.org}") or {}
        core = ((self.get("/rate_limit") or {}).get("resources") or {}).get("core", {})
        return {
            "login": user["login"],
            "state": member.get("state", "unknown"),
            "role": member.get("role", "unknown"),
            "remaining": core.get("remaining", "?"),
            "limit": core.get("limit", "?"),
        }

    def rate_remaining(self):
        return ((self.get("/rate_limit") or {}).get("resources") or {}).get("core", {}).get("remaining", "?")

    # -- Data -----------------------------------------------------------------

    def list_repos(self, pattern: str) -> list[dict]:
        return [r for r in self.all_pages(f"/orgs/{self.org}/repos", type="all") or [] if pattern in r["name"]]

    def collect_repo(self, listed: dict) -> dict[str, list[dict]]:
        name = listed["name"]
        r = self.get(f"/repos/{self.org}/{name}") or listed  # the org listing carries the same fields
        out: dict[str, list[dict]] = {"repositories": [], "deployments": []}
        out["repositories"].append({"repo_id": r.get("id"), "repo_name": name, "full_name": r.get("full_name"), "html_url": r.get("html_url"), "archived": r.get("archived")})
        for d in self.all_pages(f"/repos/{self.org}/{name}/deployments") or []:
            out["deployments"].append(
                {
                    "repo_name": name,
                    "deployment_id": d["id"],
                    "environment": d.get("environment"),
                    "production_environment": d.get("production_environment"),
                    "sha": d.get("sha"),
                    "created_at": d.get("created_at"),
                    "_node_id": d.get("node_id"),
                }
            )
        return out

    def deployment_statuses(self, deployments: list[dict], progress: Callable[[], None] = lambda: None) -> list[dict]:
        """Statuses of every deployment: GraphQL in batches of 100, REST per deployment for a batch that fails."""
        rows = []
        for i in range(0, len(deployments), 100):
            batch = deployments[i : i + 100]
            data = self.graphql(STATUS_QUERY, ids=[d["_node_id"] for d in batch]) if all(d.get("_node_id") for d in batch) else None
            nodes = {n["databaseId"]: n for n in (data or {}).get("nodes") or [] if n}
            for d in batch:
                n = nodes.get(d["deployment_id"])
                if n:
                    sts = [{"state": s["state"].lower(), "created_at": s["createdAt"], "source": "GraphQL"} for s in n["statuses"]["nodes"]]
                else:
                    path = f"/repos/{self.org}/{d['repo_name']}/deployments/{d['deployment_id']}/statuses"
                    sts = [{"state": s.get("state"), "created_at": s.get("created_at"), "source": "REST"} for s in self.all_pages(path) or []]
                rows += [{"repo_name": d["repo_name"], "deployment_id": d["deployment_id"], **s} for s in sts]
            progress()
        return rows

    def urn_lookup(self, repo_names: list[str]) -> dict[str, tuple[str, str]]:
        """data_product_urn per repo: org custom properties, else each repo's properties, then a code search."""
        found: dict[str, tuple[str, str]] = {}
        org_vals = self.all_pages(f"/orgs/{self.org}/properties/values")
        if org_vals is not None:
            for r in org_vals:
                for p in r.get("properties") or []:
                    if p.get("property_name") == "data_product_urn" and p.get("value"):
                        found[r["repository_name"]] = (_joined(p["value"]), "org custom property")
        else:
            for name in repo_names:
                for p in self.get(f"/repos/{self.org}/{name}/properties/values") or []:
                    if p.get("property_name") == "data_product_urn" and p.get("value"):
                        found[name] = (_joined(p["value"]), "repo custom property")
        missing = set(repo_names) - set(found)
        if missing:
            hits = self.get("/search/code", q=f"data_product_urn org:{self.org}") or {}
            for item in hits.get("items") or []:
                name = item["repository"]["name"]
                if name not in missing or name in found:
                    continue
                blob = self.get(f"/repos/{self.org}/{name}/contents/{item['path']}") or {}
                text = base64.b64decode(blob.get("content") or "").decode("utf-8", "ignore")
                m = re.search(r"data_product_urn[\"']?\s*[:=]\s*[\"']?([^\s\"'#,]+)", text)
                if m:
                    found[name] = (m.group(1), f"code: {item['path']}")
        return found

    def fetch(self, pattern: str, only: list[str] | None = None, workers: int = 4, login: str | None = None, progress: Callable[[], None] = lambda: None) -> FetchResult:
        t0 = time.time()
        login = login or self.check_connection()["login"]
        repos = self.list_repos(pattern)
        if only:
            repos = [r for r in repos if r["name"] in set(only)]
        tables: dict[str, list[dict]] = {t: [] for t in TABLES}

        def one(r: dict) -> dict[str, list[dict]]:
            part = self.collect_repo(r)
            progress()
            return part

        with cf.ThreadPoolExecutor(workers) as ex:
            for part in ex.map(one, repos):
                for t, rows in part.items():
                    tables[t] += rows
        tables["deployment_statuses"] = self.deployment_statuses(tables["deployments"], progress)
        urns = self.urn_lookup([r["name"] for r in repos])
        for row in tables["repositories"]:
            row["data_product_urn"], row["data_product_urn_source"] = urns.get(row["repo_name"], (None, None))
        for t in ("repositories", "deployments", "deployment_statuses"):
            tables[t].sort(key=lambda row, t=t: [str(row.get(c) or "") for c in TABLES[t][:3]])
        tables["issues"] = list(self.issues)
        fetched_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
        tables["fetch"] = [{"fetched_at": fetched_at, "org": self.org, "login": login, "repos": len(repos)}]
        return FetchResult(tables=tables, login=login, rate_remaining=self.rate_remaining(), seconds=time.time() - t0, issues=list(self.issues))


def write_tables(tables: dict[str, list[dict]], folder: Path) -> list[Path]:
    """One CSV per table in folder (inbox/github/), replacing the previous extract."""
    folder.mkdir(parents=True, exist_ok=True)
    written = []
    for t, cols in TABLES.items():
        path = folder / f"{t}.csv"
        with open(path, "w", newline="", encoding="utf-8-sig") as fh:
            w = csv.writer(fh)
            w.writerow(cols)
            w.writerows(["" if row.get(c) is None else row.get(c) for c in cols] for row in tables.get(t, []))
        written.append(path)
    return written
