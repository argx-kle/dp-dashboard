"""AT-PLAT-2x: platform data merged into the snapshot. Register and platform files of tests/fixtures/inbox-platform.

Register (6 products): crmsys Live (dev deployments only), hcp-master Live (prod), journey-insights In build,
rx-claims In design and never reviewed, hubservice with no gate and never reviewed, legacy-cube not in NextData.
"""

from __future__ import annotations

from datetime import date

import pytest

from conftest import PLATFORM_INBOX, WEEK, metric
from pipeline.build import run_build


@pytest.fixture(scope="module")
def built(tmp_path_factory, regs):
    base = tmp_path_factory.mktemp("platform")
    res = run_build(PLATFORM_INBOX, WEEK, base / "out", base / "state", regs=regs, template_path=base / "none")
    assert res.built, [i.message for i in res.check.blockers]
    return res


@pytest.fixture(scope="module")
def snap(built):
    return built.snapshot


def _product(snap, urn):
    return next(p for p in snap["products"] if p["urn"] == urn)


def _dq(snap, rule):
    return [d for d in snap["dataQuality"] if d["rule"] == rule]


def test_at_plat_20_products_carry_their_platform_facts(snap):
    crm = _product(snap, "nxd:dp-ops-crmsys")
    assert crm["nextdata"]["names"] == ["dp-ops-crmsys", "crmsys"]
    assert crm["nextdata"]["runtime"] == "Started" and crm["nextdata"]["env"] == "dev"
    assert [d["state"] for d in crm["nextdata"]["deployments"]] == ["Failed", "Failed", "Started"]  # dev deployments, by name then version
    assert crm["validation"]["score"] == 0.7341 and crm["validation"]["lastRun"] == "2026-10-02"
    assert crm["validation"]["ownerStatus"] == "Declared" and crm["validation"]["keyids"] == ["crmsys"]
    assert [c["label"] for c in crm["validation"]["components"]] == ["Product spec", "Metadata", "Runtime"]
    assert _product(snap, "nxd:dp-patient-journey-insights")["platformDomain"] == "EDP/PATIENT"
    assert _product(snap, "nxd:dp-hcp-hcp-master")["nextdata"]["env"] == "prod"
    legacy = _product(snap, "urn:dp:com:legacy-cube")
    assert "nextdata" not in legacy and "validation" not in legacy


def test_at_plat_21_register_against_platform_warnings(snap):
    assert [d["urn"] for d in _dq(snap, "ND_STATUS")] == ["nxd:dp-ops-crmsys"]  # hcp-master runs in prod
    assert [d["urn"] for d in _dq(snap, "ND_NOT_IN_CATALOG")] == ["urn:dp:com:legacy-cube"]
    assert len(_dq(snap, "ND_NOT_IN_REGISTER")) == 18 - 5  # counted on the platform, no register row
    assert _dq(snap, "VAL_STALE") == []  # run 2026-10-02, as of 2026-10-09
    assert {s["name"] for s in snap["sources"]} >= {"NextData listing", "NextData catalog", "NextData domains", "Validation results", "Crosswalk"}


def test_at_plat_22_readiness_indicators(snap):
    spec = metric(snap, "spec_score_median", "org")
    assert (spec["value"], spec["n"], spec["source"]) == (0.7353, 4, "validation")  # median of 0.6401, 0.7341, 0.7365, 0.8812
    failing = metric(snap, "runtime_failing", "org")
    assert (failing["value"], failing["n"], failing["urns"]) == (1, 5, ["nxd:dp-claims-rx-claims"])
    ids = {m["id"] for m in snap["registry"]["metrics"]}
    assert not ids & {"spec_complete", "owner_coverage", "in_flight_age"}, "removed on 2026-10-07"


def test_at_plat_23_data_coverage(snap):
    org = {r["kind"]: r for r in snap["reporting"] if r["scope"] == "org"}
    assert (org["gates"]["have"], org["gates"]["of"], org["gates"]["missing"]) == (5, 6, ["nxd:hubservice-nxd"])
    assert (org["reviewed"]["have"], org["reviewed"]["missing"]) == (4, ["nxd:dp-claims-rx-claims", "nxd:hubservice-nxd"])
    assert (org["validation"]["have"], org["validation"]["of"]) == (4, 6)
    assert (org["nextdata"]["have"], org["nextdata"]["missing"]) == (5, ["urn:dp:com:legacy-cube"])
    assert (org["usage"]["have"], org["usage"]["of"]) == (2, 2)
    defs = {m["id"]: m.get("coverage") for m in snap["registry"]["metrics"]}
    assert defs["certified_qtd"] == "gates" and defs["g4_forecast"] == "plans" and defs["spec_score_median"] == "validation"


def test_at_plat_24_never_reviewed_is_not_yet_reported(snap):
    rx = _product(snap, "nxd:dp-claims-rx-claims")
    assert rx["signal"] == "unreported" and rx["flags"] == []  # not NOT_UPDATED: the clock starts at the first review
    assert _product(snap, "nxd:hubservice-nxd")["signal"] == "unreported"
    assert _product(snap, "nxd:dp-hcp-hcp-master")["signal"] == "green"


def test_at_plat_25_dq_report_lists_what_is_not_counted(built):
    html = (built.out_dir / "dq-report.html").read_text(encoding="utf-8")
    assert "Products on the platform" in html and "Not counted" in html
    assert "Placeholder name (dp-&lt;team&gt;-&lt;word&gt;-dp)" in html


def test_at_plat_26_stale_validation(tmp_path, regs):
    res = run_build(PLATFORM_INBOX, "2026-W44", tmp_path / "out", tmp_path / "state", regs=regs, template_path=tmp_path / "none", as_of=date(2026, 10, 30))
    assert res.built
    assert [d["file"] for d in _dq(res.snapshot, "VAL_STALE")] == ["validation/validation-summary.xlsx"]


def test_at_plat_27_register_only_inbox_has_no_platform_fields(golden_snapshot):
    assert all("nextdata" not in p and "validation" not in p for p in golden_snapshot["products"])
    kinds = {r["kind"] for r in golden_snapshot["reporting"]}
    assert "validation" not in kinds and "nextdata" not in kinds
    assert metric(golden_snapshot, "spec_score_median", "org")["reason"] == "No validation results in the inbox"
