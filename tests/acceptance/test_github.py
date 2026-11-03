"""AT-GH: the GitHub extract (inbox/github/) matched to register products, its metrics and warnings.

Rules: docs/metric-definitions.md, sections "Platform sources" (GitHub) and "Technical readiness".
Fixture: tests/fixtures/github (invented; its README lists each case), copied into the platform inbox. As of 2026-10-09.
"""

from __future__ import annotations

import shutil
from datetime import date
from pathlib import Path

import pytest

from conftest import FIXTURES, GOLDEN_INBOX, PLATFORM_INBOX, WEEK, metric
from pipeline.build import run_build, run_check
from pipeline.github import exclusion, repo_names
from pipeline.readers.github import read_github

GITHUB = FIXTURES / "github"
AS_OF = date(2026, 10, 9)


def _inbox(tmp: Path, base: Path = PLATFORM_INBOX) -> Path:
    dst = tmp / "inbox"
    shutil.copytree(base, dst)
    shutil.copytree(GITHUB, dst / "github")
    return dst


@pytest.fixture(scope="module")
def built(tmp_path_factory, regs):
    base = tmp_path_factory.mktemp("github")
    res = run_build(_inbox(base), WEEK, base / "out", base / "state", regs=regs, template_path=base / "none")
    assert res.built, [i.message for i in res.check.blockers]
    return res


@pytest.fixture(scope="module")
def snap(built):
    return built.snapshot


def _product(snap, urn):
    return next(p for p in snap["products"] if p["urn"] == urn)


def _dq(snap, rule):
    return [d for d in snap["dataQuality"] if d["rule"] == rule]


# --- Reader --------------------------------------------------------------------


def test_at_gh_01_outcome_is_the_latest_terminal_status():
    run, issues = read_github(GITHUB)
    assert issues == []
    deps = {d.id: d.outcome for d in run.repos["edp-ops-dp-crmsys"].deployments}
    assert deps["102"] == "success"  # superseded later: inactive is ignored
    assert deps["104"] == "failure"
    assert deps["105"] == "pending"  # queued, in progress: no outcome yet
    assert deps["107"] == "success"  # failed, then re-run successfully (rows out of order in the file)
    assert run.fetched_at.date() == AS_OF and run.org == "example-org"
    assert run.repos["edp-patient-dp-pj_app"].urn == "nxd:hubservice-nxd"


def test_at_gh_02_unavailable_requests_are_warnings(tmp_path):
    folder = tmp_path / "github"
    shutil.copytree(GITHUB, folder)
    (folder / "issues.csv").write_text("request,detail\n/repos/x/y/deployments,HTTP 502: bad gateway\n", encoding="utf-8")
    run, issues = read_github(folder)
    assert run is not None
    assert [(i.severity, i.rule) for i in issues] == [("warning", "GH_FETCH")] and "HTTP 502" in issues[0].message
    many = "request,detail\n" + "".join(f"/r{i},HTTP 500\n" for i in range(9))
    (folder / "issues.csv").write_text(many, encoding="utf-8")
    _, issues = read_github(folder)
    assert len(issues) == 1 and issues[0].message.startswith("9 GitHub requests")


def test_at_gh_03_missing_repository_file_is_a_warning(tmp_path):
    (tmp_path / "github").mkdir()
    run, issues = read_github(tmp_path / "github")
    assert run is None and [i.rule for i in issues] == ["UNREADABLE"] and issues[0].severity == "warning"


# --- Matching ------------------------------------------------------------------


def test_at_gh_04_repository_names(platform_cfg):
    assert repo_names("edp-claims-dp-channel_partner") == ("claims", ["dp-claims-channel-partner", "channel-partner", "channel-partner-nxd"])
    assert repo_names("something-else") == (None, ["something-else"])
    assert exclusion("edp-nxd-dp-template", platform_cfg).startswith("Platform tooling")
    assert exclusion("edp-hcp-dp-survey_test", platform_cfg) == "Test"
    assert exclusion("edp-ops-dp-crmsys", platform_cfg) is None


def test_at_gh_05_products_carry_their_repository(snap):
    crm = _product(snap, "nxd:dp-ops-crmsys")["github"]
    assert crm == {
        "repo": "edp-ops-dp-crmsys",
        "url": "https://github.example/example-org/edp-ops-dp-crmsys",
        "lastProdDeploy": "2026-10-05",  # the deployment on 2026-10-12 is after the as-of date
        "prodDeploys30d": 2,  # 2026-09-25 and 2026-10-05; 2026-08-01 is outside the window
        "deploys30d": 4,  # 102, 103, 104, 107; 105 is pending, 106 after the as-of date
        "failed30d": 1,
    }
    assert _product(snap, "nxd:hubservice-nxd")["github"]["repo"] == "edp-patient-dp-pj_app"  # by data_product_urn
    assert _product(snap, "urn:dp:com:legacy-cube")["github"]["lastProdDeploy"] == "2026-07-01"  # by the URN's last segment
    hcp = _product(snap, "nxd:dp-hcp-hcp-master")["github"]
    assert "lastProdDeploy" not in hcp  # never deployed to production
    assert (hcp["deploys30d"], hcp["failed30d"]) == (2, 1)


def test_at_gh_06_crosswalk_links_and_excludes_repositories(tmp_path, regs):
    inbox = _inbox(tmp_path)
    with open(inbox / "crosswalk.csv", "a", encoding="utf-8") as fh:
        fh.write("github,edp-ops-dp-orphan_feed,nxd:dp-claims-rx-claims,yes,,,,,yes\n")
        fh.write("github,edp-claims-dp-rx_claims,,no,Retired repository,,,,yes\n")
    check, ctx = run_check(inbox, AS_OF, regs)
    by_urn = {pc.urn: pc.github.name for pc in ctx.products if pc.github is not None}
    assert by_urn["nxd:dp-claims-rx-claims"] == "edp-ops-dp-orphan_feed"
    assert not [i for i in check.issues if i.rule == "GH_NOT_IN_REGISTER"]


def test_at_gh_07_matches_without_platform_files(tmp_path, regs):
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    for f in ["products.csv", "gate_events.csv", "targets.csv", "capacity.csv"]:
        shutil.copy(PLATFORM_INBOX / f, inbox / f)
    shutil.copytree(GITHUB, inbox / "github")
    _, ctx = run_check(inbox, AS_OF, regs)
    by_urn = {pc.urn: pc.github.name for pc in ctx.products if pc.github is not None}
    assert by_urn["nxd:dp-ops-crmsys"] == "edp-ops-dp-crmsys" and by_urn["nxd:dp-hcp-hcp-master"] == "edp-hcp-dp-hcp_master"
    assert ctx.has_github and not ctx.has_nextdata


# --- Metrics -------------------------------------------------------------------


def test_at_gh_08_no_prod_deploy(snap):
    m = metric(snap, "no_prod_deploy", "org")
    assert (m["value"], m["n"], m["source"]) == (4, 6, "github")
    assert m["urns"] == ["nxd:dp-claims-rx-claims", "nxd:dp-hcp-hcp-master", "nxd:dp-patient-journey-insights", "nxd:hubservice-nxd"]
    hcp = metric(snap, "no_prod_deploy", "hcp")
    assert (hcp["value"], hcp["n"], hcp["urns"]) == (1, 2, ["nxd:dp-hcp-hcp-master"])


def test_at_gh_09_prod_deploy_frequency(snap):
    m = metric(snap, "prod_deploy_frequency", "org")
    assert (m["value"], m["n"], m["values"]) == (1, 2, [0, 2])  # reached production: crmsys 2, legacy-cube 0 (hcp-master never did); n below min_n lists the values


def test_at_gh_10_deploy_failure_rate(snap):
    m = metric(snap, "deploy_failure_rate", "org")
    assert (m["value"], m["n"], m["urns"]) == (0.2857, 7, ["nxd:dp-hcp-hcp-master", "nxd:dp-ops-crmsys"])  # 2 of 7
    patient = metric(snap, "deploy_failure_rate", "patient")
    assert (patient["value"], patient["n"]) == (0, 1)
    assert metric(snap, "deploy_failure_rate", "market-access")["reason"] == "No deployments in the last 30 days"


def test_at_gh_11_null_with_reason_without_the_extract(golden_snapshot):
    for mid in ["no_prod_deploy", "prod_deploy_frequency", "deploy_failure_rate"]:
        m = metric(golden_snapshot, mid, "org")
        assert m["value"] is None and m["reason"] == "No GitHub extract in the inbox"
    assert all("github" not in p for p in golden_snapshot["products"])
    assert not [r for r in golden_snapshot["reporting"] if r["kind"] == "github"]


def test_at_gh_12_coverage(snap):
    org = {r["kind"]: r for r in snap["reporting"] if r["scope"] == "org"}
    assert (org["github"]["have"], org["github"]["of"], org["github"]["missing"]) == (6, 6, [])
    defs = {m["id"]: m for m in snap["registry"]["metrics"]}
    assert defs["deploy_failure_rate"]["coverage"] == "github" and defs["deploy_failure_rate"]["unit"] == "share"


# --- Checks --------------------------------------------------------------------


def test_at_gh_13_register_against_github_warnings(snap):
    assert [d["urn"] for d in _dq(snap, "GH_STATUS")] == ["nxd:dp-hcp-hcp-master"]  # Live, no prod deployment
    assert [d["message"] for d in _dq(snap, "GH_NOT_IN_REGISTER")] == [  # template and test repos are not counted
        "1 ops repository matches no product on the Products sheet (link or exclude in the crosswalk, source github): edp-ops-dp-orphan_feed"
    ]
    dup = _dq(snap, "GH_DUPLICATE")
    assert [(d["urn"], d["message"].split()[1]) for d in dup] == [("nxd:dp-ops-crmsys", "edp-patient-dp-crmsys")]
    assert _dq(snap, "GH_STALE") == [] and _dq(snap, "GH_FETCH") == []
    src = next(s for s in snap["sources"] if s["name"] == "GitHub")
    assert (src["file"], src["rows"], src["status"]) == ("github/repositories.csv", 10, "ok")


def test_at_gh_14_stale_extract(tmp_path, regs):
    res = run_build(_inbox(tmp_path, GOLDEN_INBOX), "2026-W43", tmp_path / "out", tmp_path / "state", regs=regs, template_path=tmp_path / "none")
    assert res.built
    assert [d["file"] for d in _dq(res.snapshot, "GH_STALE")] == ["github/fetch.csv"]  # fetched 2026-10-09, as of 2026-10-23
