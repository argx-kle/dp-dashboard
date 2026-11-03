"""AT-GH-FETCH: dp fetch-github without a network. A stub transport answers in place of api.github.com."""

from __future__ import annotations

import json
import re

import pytest
import requests

from pipeline.github_fetch import TABLES, GitHub, ReadOnlySession, write_tables
from pipeline.readers.github import read_github

API = "https://api.test"


class StubAdapter(requests.adapters.BaseAdapter):
    """routes: list of (method, url regex, handler(request) -> (status, body))."""

    def __init__(self, routes):
        super().__init__()
        self.routes = routes
        self.calls: list[tuple[str, str]] = []

    def send(self, request, **kw):
        self.calls.append((request.method, request.url))
        for method, pattern, handler in self.routes:
            if method == request.method and re.search(pattern, request.url):
                status, body = handler(request)
                break
        else:
            status, body = 404, {"message": "Not Found"}
        r = requests.Response()
        r.status_code, r.request, r.url = status, request, request.url
        r._content = json.dumps(body).encode()
        r.headers["content-type"] = "application/json"
        return r

    def close(self):
        pass


def _client(routes) -> tuple[GitHub, StubAdapter]:
    session = ReadOnlySession(API + "/graphql")
    adapter = StubAdapter(routes)
    session.mount(API, adapter)
    return GitHub("t0ken", "example-org", session=session, api=API, sleep=lambda s: None), adapter


def test_at_gh_fetch_01_only_reads():
    gh, adapter = _client([])
    for method in ["PUT", "PATCH", "DELETE"]:
        with pytest.raises(RuntimeError, match="blocked non-read request"):
            gh.session.request(method, API + "/repos/example-org/x")
    with pytest.raises(RuntimeError, match="blocked non-read request"):
        gh.session.post(API + "/repos/example-org/x/dispatches", json={})
    with pytest.raises(AssertionError):
        gh.graphql("mutation { x }")
    assert adapter.calls == []  # nothing reached the transport
    assert gh.session.headers["Authorization"] == "Bearer t0ken"


def test_at_gh_fetch_02_pagination_stops_on_a_short_page():
    def page(req):
        n = int(re.search(r"[?&]page=(\d+)", req.url).group(1))
        return 200, [{"id": i} for i in range(100 if n == 1 else 7)]

    gh, adapter = _client([("GET", r"/items", page)])
    assert len(gh.all_pages("/items")) == 107 and len(adapter.calls) == 2
    gh, _ = _client([])
    assert gh.all_pages("/missing") is None and gh.issues[0]["detail"].startswith("HTTP 404")


def test_at_gh_fetch_03_failed_graphql_batch_falls_back_to_rest():
    deps = [{"repo_name": "edp-ops-dp-a", "deployment_id": 7, "_node_id": "D_7"}, {"repo_name": "edp-ops-dp-a", "deployment_id": 8, "_node_id": "D_8"}]
    gh, adapter = _client(
        [
            ("POST", r"/graphql$", lambda r: (502, {})),
            ("GET", r"/deployments/7/statuses", lambda r: (200, [{"state": "success", "created_at": "2026-10-01T00:00:00Z"}])),
            ("GET", r"/deployments/8/statuses", lambda r: (200, [])),
        ]
    )
    rows = gh.deployment_statuses(deps)
    assert rows == [{"repo_name": "edp-ops-dp-a", "deployment_id": 7, "state": "success", "created_at": "2026-10-01T00:00:00Z", "source": "REST"}]
    assert gh.issues == [{"request": "graphql", "detail": "gave up after retries"}]


def test_at_gh_fetch_04_end_to_end_files_are_what_the_reader_expects(tmp_path):
    repo = {"id": 1, "name": "edp-ops-dp-a", "full_name": "example-org/edp-ops-dp-a", "html_url": "https://github.example/a", "archived": False}
    gql = {"data": {"nodes": [{"databaseId": 7, "statuses": {"nodes": [{"state": "SUCCESS", "createdAt": "2026-10-01T00:05:00Z"}]}}]}}
    gh, adapter = _client(
        [
            ("GET", r"/user\?|/user$", lambda r: (200, {"login": "example-user"})),
            ("GET", r"/user/memberships", lambda r: (200, {"state": "active", "role": "member"})),
            ("GET", r"/rate_limit", lambda r: (200, {"resources": {"core": {"remaining": 4999, "limit": 5000}}})),
            ("GET", r"/orgs/example-org/repos", lambda r: (200, [repo, {**repo, "name": "other-repo"}])),
            ("GET", r"/repos/example-org/edp-ops-dp-a\?|/repos/example-org/edp-ops-dp-a$", lambda r: (200, repo)),
            ("GET", r"/edp-ops-dp-a/deployments", lambda r: (200, [{"id": 7, "node_id": "D_7", "environment": "iac-apply-p", "production_environment": False, "sha": "s", "created_at": "2026-10-01T00:00:00Z"}])),
            ("POST", r"/graphql$", lambda r: (200, gql)),
            ("GET", r"/orgs/example-org/properties/values", lambda r: (200, [{"repository_name": "edp-ops-dp-a", "properties": [{"property_name": "data_product_urn", "value": "urn:dp:a"}]}])),
        ]
    )
    result = gh.fetch("-dp-")
    assert result.login == "example-user" and [r["repo_name"] for r in result.tables["repositories"]] == ["edp-ops-dp-a"]
    assert all(m in ("GET", "POST") for m, _ in adapter.calls)
    write_tables(result.tables, tmp_path / "github")
    assert sorted(p.stem for p in (tmp_path / "github").iterdir()) == sorted(TABLES)
    run, issues = read_github(tmp_path / "github")
    assert issues == []
    a = run.repos["edp-ops-dp-a"]
    assert a.urn == "urn:dp:a" and [(d.env, d.outcome) for d in a.deployments] == [("iac-apply-p", "success")]
    assert run.org == "example-org"
