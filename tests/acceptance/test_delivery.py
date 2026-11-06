"""AT-DEL: the Delivery section, built from the GitHub extract alone (every repository, register or not).

Rules: docs/metric-definitions.md, section "Delivery". Fixture: tests/fixtures/github (its README lists each case),
copied into the platform inbox. As of 2026-10-09 (Friday of 2026-W41); window (2026-09-09, 2026-10-09].
"""

from __future__ import annotations

import shutil
from datetime import date, datetime, timezone

import pytest

from conftest import FIXTURES, PLATFORM_INBOX, WEEK
from pipeline.build import run_build
from pipeline.github import failing_streaks, recovery_hours, unvalidated_prod
from pipeline.readers.github import GhDeployment, GithubRepo

AS_OF = date(2026, 10, 9)


@pytest.fixture(scope="module")
def delivery(tmp_path_factory, regs):
    base = tmp_path_factory.mktemp("delivery")
    inbox = base / "inbox"
    shutil.copytree(PLATFORM_INBOX, inbox)
    shutil.copytree(FIXTURES / "github", inbox / "github")
    res = run_build(inbox, WEEK, base / "out", base / "state", regs=regs, template_path=base / "none")
    assert res.built
    return res.snapshot["delivery"]


def _repo(delivery, name):
    return next(r for r in delivery["repos"] if r["name"] == name)


def test_at_del_01_tooling_and_tests_are_listed_but_not_counted(delivery):
    excluded = {r["name"]: r["excluded"] for r in delivery["repos"] if r.get("excluded")}
    assert excluded == {"edp-nxd-dp-template": "Platform tooling, not a business data product", "edp-hcp-dp-survey_test": "Test"}
    assert len(delivery["repos"]) == 10 and delivery["totals"]["repos"] == 8


def test_at_del_02_totals_over_the_window(delivery):
    t = delivery["totals"]
    # crmsys 4 (one pending, one after the as-of date), hcp_master 2, journey_insights 1, patient crmsys 1, orphan_feed 1
    assert (t["deploys30d"], t["failed30d"]) == (9, 3)
    assert (t["prodAttempts30d"], t["prodFailed30d"]) == (4, 1)
    assert t["active30d"] == 5  # a pending deployment still counts as activity
    assert t["reachedProd"] == 3  # crmsys, legacy_cube (before the window), orphan_feed
    assert (t["lastProdDeploy"], t["lastProdRepo"]) == ("2026-10-05", "edp-ops-dp-crmsys")  # 10-12 is after the as-of date
    assert t["notInRegister"] == 1  # orphan_feed; a second repository of a product still has its URN


def test_at_del_03_promotion_path_in_configured_order(delivery):
    envs = [(e["id"], e["label"], e["path"], e["prod"], e["repos"], e["deploys30d"], e["failed30d"]) for e in delivery["envs"]]
    assert envs == [
        ("iac-apply-d", "Dev", True, False, 2, 4, 2),
        ("iac-apply-v", "Validation", True, False, 1, 1, 0),
        ("iac-apply-p", "Production", True, True, 3, 4, 1),
    ]


def test_at_del_04_twelve_weeks_up_to_the_as_of_week(delivery):
    weeks = delivery["weekly"]
    assert len(weeks) == 12 and weeks[0]["week"] == "2026-W30" and weeks[-1]["week"] == "2026-W41"
    assert weeks[-1] == {"week": "2026-W41", "start": "2026-10-05", "deploys": 3, "failed": 1, "prodSuccess": 1, "firstDeploys": 0}
    assert weeks[-2] == {"week": "2026-W40", "start": "2026-09-28", "deploys": 5, "failed": 2, "prodSuccess": 1, "firstDeploys": 3}


def test_at_del_05_teams(delivery):
    teams = [(t["team"], t["label"], t["repos"], t["deploys30d"], t["failed30d"], t["reachedProd"]) for t in delivery["teams"]]
    assert teams == [
        ("ops", "Source systems", 3, 5, 1, 3),
        ("patient", "Patient team", 3, 2, 1, 0),
        ("claims", "Claims team", 1, 0, 0, 0),
        ("hcp", "HCP team", 1, 2, 1, 0),
    ]


def test_at_del_06_repository_row(delivery):
    r = _repo(delivery, "edp-ops-dp-crmsys")
    assert r["urn"] == "nxd:dp-ops-crmsys" and r["team"] == "ops"
    assert r["envs"] == [
        {"env": "iac-apply-d", "lastSuccess": "2026-10-02", "deploys30d": 2, "failed30d": 1},
        {"env": "iac-apply-p", "lastSuccess": "2026-10-05", "deploys30d": 2, "failed30d": 0},
    ]
    assert (r["prodDeploys"], r["lastProdDeploy"], r["lastDeploy"], r["lastFailure"]) == (3, "2026-10-05", "2026-10-08", "2026-10-01")
    assert r["weekly"][-1] == 2  # 103 and the pending 105
    assert _repo(delivery, "edp-patient-dp-crmsys")["urn"] == "nxd:dp-ops-crmsys"
    assert "urn" not in _repo(delivery, "edp-ops-dp-orphan_feed")
    assert _repo(delivery, "edp-claims-dp-rx_claims")["envs"] == []


def test_at_del_07_absent_without_the_extract(golden_snapshot):
    assert "delivery" not in golden_snapshot


# --- Delivery health (docs/metric-definitions.md, "Delivery health") ---------------------------------------------


def _dep(env, day, outcome, sha="", hour=10):
    return GhDeployment(id=f"{env}{day}{hour}", env=env, created_at=datetime(2026, 10, day, hour, tzinfo=timezone.utc), outcome=outcome, sha=sha)


def test_at_del_08_failing_now(delivery):
    t = delivery["totals"]
    # hcp_master dev ended in error; the second crmsys repository's only production deployment failed
    assert [(b["repo"], b["env"], b["since"], b.get("lastSuccess")) for b in delivery["broken"]] == [
        ("edp-patient-dp-crmsys", "iac-apply-p", "2026-10-01", None),
        ("edp-hcp-dp-hcp_master", "iac-apply-d", "2026-10-06", None),
    ]
    # crmsys dev and prod, hcp_master dev and validation, journey_insights dev, legacy_cube, patient crmsys and orphan_feed prod
    assert (t["brokenNow"], t["pathEnvs"]) == (2, 8)
    assert _repo(delivery, "edp-hcp-dp-hcp_master")["failingNow"] == ["iac-apply-d"]
    assert _repo(delivery, "edp-hcp-dp-hcp_master")["reached"] == "iac-apply-v"
    assert "reached" not in _repo(delivery, "edp-claims-dp-rx_claims")


def test_at_del_09_failing_since_the_first_failure_after_the_last_success(platform_cfg):
    repo = GithubRepo(name="r", deployments=[
        _dep("iac-apply-d", 2, "success"), _dep("iac-apply-d", 3, "failure"), _dep("iac-apply-d", 5, "error"),
        _dep("iac-apply-d", 6, "pending"),  # no outcome yet: says nothing
        _dep("iac-apply-v", 4, "failure"), _dep("iac-apply-v", 5, "success"),
    ])
    [s] = failing_streaks(repo, platform_cfg, AS_OF)
    assert (s.env, s.since, s.last_success) == ("iac-apply-d", date(2026, 10, 3), date(2026, 10, 2))


def test_at_del_10_production_commits_without_validation(delivery, platform_cfg):
    t = delivery["totals"]
    # crmsys a2 and a3 and orphan_feed f1 reached production in the window; none was deployed to validation
    assert (t["bypass30d"], t["prodCommits30d"]) == (3, 3)
    assert [(b["repo"], b["sha"], b["at"]) for b in delivery["bypass"]] == [
        ("edp-ops-dp-crmsys", "a3", "2026-10-05"),
        ("edp-ops-dp-orphan_feed", "f1", "2026-10-01"),
        ("edp-ops-dp-crmsys", "a2", "2026-09-25"),
    ]
    repo = GithubRepo(name="r", deployments=[
        _dep("iac-apply-v", 1, "success", "s1"), _dep("iac-apply-p", 2, "success", "s1"),  # validated first
        _dep("iac-apply-p", 3, "success", "s1"),  # the same commit again: one commit
        _dep("iac-apply-v", 4, "failure", "s2"), _dep("iac-apply-p", 4, "success", "s2", hour=11),  # validation failed
        _dep("iac-apply-p", 6, "success", "s3"), _dep("iac-apply-v", 7, "success", "s3"),  # validated only afterwards
        _dep("iac-apply-p", 7, "failure", "s4"),  # a failed production deployment is not a production commit
    ])
    skipped, commits = unvalidated_prod(repo, platform_cfg, AS_OF)
    assert commits == 3 and sorted(d.sha for d in skipped) == ["s2", "s3"]


def test_at_del_11_recovery_time(delivery):
    # crmsys dev: failed on 10-01 10:00, next success started 10-02 10:00
    assert delivery["totals"]["recoveryHours30d"] == 24.0
    repo = GithubRepo(name="r", deployments=[
        _dep("iac-apply-d", 1, "failure"), _dep("iac-apply-d", 1, "failure", hour=11), _dep("iac-apply-d", 1, "success", hour=13),
        _dep("iac-apply-p", 2, "failure"),  # never recovered: not counted
    ])
    assert recovery_hours(repo, AS_OF) == [3.0]  # from the first failure of the run


def test_at_del_12_onboarding(delivery):
    # first deployments: crmsys W31, hcp_master W38, journey_insights, patient crmsys and orphan_feed W40;
    # legacy_cube (2026-07-01) is before the 12 weeks; rx_claims has none
    assert delivery["totals"]["onboarded"] == 6
    assert [w["firstDeploys"] for w in delivery["weekly"]] == [0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 3, 0]
