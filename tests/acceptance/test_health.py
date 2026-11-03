"""AT-HEALTH: lifecycle stages, domain health, the weekly series and the closed quarters
(docs/metric-definitions.md, "Lifecycle stages", "Domain health", "Weekly trend", "Quarter selector")."""

from __future__ import annotations

from datetime import date

import pytest

from conftest import product
from pipeline.contracts import GateEvent, Product
from pipeline.health import health_status
from pipeline.lifecycle import derive

AS_OF = date(2026, 10, 9)


def _derive(*gates, cancelled=None):
    p = Product(urn="urn:dp:test:x", name="X", domain="hcp", row=1, cancelled_on=cancelled)
    events = [GateEvent(urn=p.urn, gate=g, date_passed=date.fromisoformat(d), row=i, g5_path=path) for i, (g, d, path) in enumerate(gates, start=1)]
    return derive(p, events, AS_OF)


@pytest.mark.parametrize(
    "gates, cancelled, expected",
    [
        ([], None, "Ideation"),
        ([("G1", "2026-01-10", None)], None, "In design"),
        ([("G1", "2026-01-10", None), ("G2", "2026-03-01", None)], None, "In development"),
        ([("G1", "2026-01-10", None), ("G2", "2026-03-01", None), ("G3", "2026-05-01", None)], None, "In testing"),
        ([("G1", "2026-01-10", None), ("G2", "2026-03-01", None), ("G3", "2026-05-01", None), ("G4", "2026-06-01", None)], None, "Live"),
        ([("G1", "2026-01-10", None), ("G2", "2026-03-01", None), ("G3", "2026-05-01", None), ("G4", "2026-06-01", None), ("G5", "2026-08-01", "scope change")], None, "Live"),
        ([("G1", "2026-01-10", None), ("G2", "2026-03-01", None), ("G3", "2026-05-01", None), ("G4", "2026-06-01", None), ("G6", "2026-09-01", None)], None, "Failed / retired"),
        ([("G1", "2026-01-10", None)], date(2026, 4, 1), "Failed / retired"),
    ],
    ids=["no-gate", "g1", "g2", "g3", "g4", "g5-after-g4", "g6", "cancelled"],
)
def test_at_health_01_lifecycle_stage_from_gates(gates, cancelled, expected):
    assert _derive(*gates, cancelled=cancelled).lifecycle == expected


@pytest.mark.parametrize(
    "certified, target, elapsed, closed, expected",
    [
        (10, 20, 0.5, False, "on-track"),  # exactly at the expected pace
        (8, 20, 0.5, False, "at-risk"),  # 80% of pace: behind, recoverable
        (3, 20, 0.75, False, "off-track"),  # 20% of pace with a quarter left
        (12, 20, 0.5, False, "ahead"),  # 120% of pace
        (9, 20, 0.5, False, "on-track"),  # 90% is the floor of on track
        (7, 20, 0.5, False, "at-risk"),  # 70% is the floor of at risk
        (0, 2, 0.2, False, "on-track"),  # 0.4 rounds to 0: nothing due yet
        (1, 2, 0.2, False, "ahead"),  # delivered before anything was due
        (0, 2, 0.25, False, "off-track"),  # 0.5 rounds up to 1: one was due
        (9, 20, 0.554, False, "at-risk"),  # 11.08 rounds to 11; 9 / 11 = 82%: Behind
        (0, 0, 0.5, False, "on-track"),
        (2, None, 0.5, False, "no-target"),
        (5, 4, 1.0, True, "above-target"),
        (4, 4, 1.0, True, "met-target"),
        (3, 4, 1.0, True, "below-target"),
    ],
)
def test_at_health_02_pace_rule(certified, target, elapsed, closed, expected):
    assert health_status(certified, target, elapsed, closed) == expected


def _health(snapshot, quarter, scope):
    return next(h for h in snapshot["health"] if h["quarter"] == quarter and h["scope"] == scope)


def test_at_health_03_current_quarter_in_the_golden_week(golden_snapshot):
    """9 Oct is day 9 of 92 in Q4: 9 x 0.098 = 0.88, so 1 of the 9 targeted is expected by today; 3 are certified."""
    org = _health(golden_snapshot, "2026-Q4", "org")
    assert (org["certified"], org["expected"], org["target"], org["status"]) == (3, 1, 9, "ahead")
    assert org["elapsed"] == round(9 / 92, 4)
    assert (org["forecast"], org["late"]) == (4, 2)  # context for the summary, not the verdict
    assert _health(golden_snapshot, "2026-Q4", "market-access")["status"] == "on-track"  # 0.2 rounds to 0: nothing due yet
    assert _health(golden_snapshot, "2026-Q4", "hcp")["status"] == "ahead"
    assert _health(golden_snapshot, "2026-Q4", "channel-partner")["status"] == "no-target"


def test_at_health_04_health_agrees_with_behind(golden_snapshot):
    """BEHIND is exactly "at risk, off track or below target"."""
    for snap_q in ["2026-Q4"]:
        behind = {m["scope"] for m in golden_snapshot["metrics"] if m["id"] == "certified_qtd" and m.get("flag") == "BEHIND"}
        not_on_track = {h["scope"] for h in golden_snapshot["health"] if h["quarter"] == snap_q and h["scope"] != "org" and h["status"] in ("at-risk", "off-track")}
        assert behind == not_on_track
    q3 = next(v for v in golden_snapshot["quarters"] if v["quarter"] == "2026-Q3")
    behind = {m["scope"] for m in q3["metrics"] if m["id"] == "certified_qtd" and m.get("flag") == "BEHIND"}
    below = {h["scope"] for h in golden_snapshot["health"] if h["quarter"] == "2026-Q3" and h["scope"] != "org" and h["status"] == "below-target"}
    assert behind == below == {"market-access", "techops"}


def test_at_health_05_closed_quarters_are_above_met_or_below(golden_snapshot):
    for h in golden_snapshot["health"]:
        if h["quarter"] != "2026-Q4":
            assert h["status"] in ("above-target", "met-target", "below-target", "no-target")
            assert h["forecast"] == 0 and h["late"] == 0 and h["elapsed"] == 1
    q3 = _health(golden_snapshot, "2026-Q3", "org")
    assert (q3["certified"], q3["target"], q3["status"]) == (4, 6, "below-target")


def test_at_health_06_weekly_is_cumulative_and_ends_at_the_quarter_total(golden_snapshot):
    trend = {}
    for t in golden_snapshot["trend"]:
        trend[t["quarter"]] = trend.get(t["quarter"], 0) + t["certified"]
    for q, total in trend.items():
        weeks = [w for w in golden_snapshot["weekly"] if w["quarter"] == q]
        counts = [w["certified"] for w in weeks]
        assert counts == sorted(counts), q
        assert counts[-1] == total, q
        assert all(sum(w["byDomain"].values()) == w["certified"] for w in weeks)
    q4 = [w["week"] for w in golden_snapshot["weekly"] if w["quarter"] == "2026-Q4"]
    assert q4 == ["2026-W40", "2026-W41"]  # the current quarter stops at the as-of week
    assert len([w for w in golden_snapshot["weekly"] if w["quarter"] == "2026-Q3"]) == 14  # 29 Jun to 30 Sep


def test_at_health_07_closed_quarter_view(golden_snapshot):
    views = {v["quarter"]: v for v in golden_snapshot["quarters"]}
    assert sorted(views) == ["2026-Q1", "2026-Q2", "2026-Q3"]
    q3 = views["2026-Q3"]
    assert q3["asOfDate"] == "2026-09-30"
    cert = next(m for m in q3["metrics"] if m["id"] == "certified_qtd" and m["scope"] == "org")
    assert cert["value"] == 4 and cert["target"] == 6
    users = next(m for m in q3["metrics"] if m["id"] == "active_users_median" and m["scope"] == "org")
    assert users["value"] is None and users["reason"]
    forecast = next(m for m in q3["metrics"] if m["id"] == "g4_forecast" and m["scope"] == "org")
    assert forecast["value"] == 0
    # A product live today was still In testing at the end of Q3 when its G4 came in Q4.
    hcp = next(p for p in q3["products"] if p["urn"] == "urn:dp:com:hcp-engagement-mart")
    assert product(golden_snapshot, "urn:dp:com:hcp-engagement-mart")["lifecycle"] == "Live"
    assert hcp["lifecycle"] == "In testing" and "firstG4Date" not in hcp
    # Products with no gate by the quarter end are not in its view.
    urns = {p["urn"] for p in q3["products"]}
    assert all(any(g["date"] <= "2026-09-30" for g in product(golden_snapshot, u)["gates"]) for u in urns)


def test_at_health_08_domains_carry_their_area(golden_snapshot):
    areas = {d["id"]: d["area"] for d in golden_snapshot["domains"]}
    assert areas["patient"] == "Commercial" and areas["techops"] == "TechOps" and areas["r-and-d"] == "R&D" and areas["g-and-a"] == "G&A"
