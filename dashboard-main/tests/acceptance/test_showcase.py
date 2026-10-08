"""AT-SHOW: the showcase week (scripts/make_showcase.py) shows everything the dashboard can draw."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.make_showcase import build_weeks  # noqa: E402


@pytest.fixture(scope="module")
def show(tmp_path_factory):
    res = build_weeks(tmp_path_factory.mktemp("showcase"), template_path=Path("/nonexistent"))
    assert res.built and not res.check.blockers
    return res.snapshot


def test_at_show_01_every_stage_flag_and_health(show):
    assert {p["lifecycle"] for p in show["products"]} == {"Ideation", "In design", "In development", "In testing", "Live", "Failed / retired"}
    assert {f["code"] for p in show["products"] for f in p["flags"]} == {"OVERDUE", "SLIPPING", "UNUSED", "NO_DPO", "NOT_UPDATED", "PENDING_URN"}
    now = {h["status"] for h in show["health"] if h["quarter"] == show["quarter"] and h["scope"] != "org"}
    assert {"ahead", "on-track", "at-risk", "off-track", "no-target"} <= now
    closed = {h["status"] for h in show["health"] if h["quarter"] != show["quarter"] and h["scope"] == "org"}
    assert closed == {"below-target", "met-target", "above-target"}


def test_at_show_02_all_four_areas_have_products(show):
    area = {d["id"]: d["area"] for d in show["domains"]}
    assert {area[p["domain"]] for p in show["products"]} == {"Commercial", "TechOps", "R&D", "G&A"}
    assert not [p for p in show["products"] if p["domain"] == "logistics"], "Logistics stays empty, so it is hidden"


def test_at_show_03_a_quarter_recovers_over_the_pace(show):
    """Q3 starts behind its target pace and ends above it, visible week by week."""
    from datetime import date

    target = sum(t["target"] or 0 for t in show["trend"] if t["quarter"] == "2026-Q3")
    start, days = date(2026, 7, 1), 92
    behind = ahead = False
    for w in (w for w in show["weekly"] if w["quarter"] == "2026-Q3"):
        pace = target * ((date.fromisoformat(w["end"]) - start).days + 1) / days
        behind |= w["certified"] < pace * 0.9
        ahead |= behind and w["certified"] >= pace
    assert behind and ahead
