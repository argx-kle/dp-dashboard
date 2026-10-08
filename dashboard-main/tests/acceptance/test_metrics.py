"""AT-MET: every registry metric against the golden inbox, expected values computed by hand
from docs/metric-definitions.md (as of 2026-10-09, quarter 2026-Q4, trailing window from 2026-04-11).

Domains changed on 2026-10-07 (Patient, HCP, Market access, Channel partner, Revenue / vials, Medical affairs,
Logistics, Unknown) and areas came on 2026-10-08 (Commercial, TechOps, R&D, G&A). The golden products kept their
values and moved domain, so the org rows are unchanged and each domain row is the old figures regrouped:
R&D = the urn:dp:rd products, TechOps = the urn:dp:tq products, Medical affairs = KOL Network Graph only (no G4),
Logistics and G&A = none, Revenue / vials = old G&A + EU Sales Performance + Legacy Sales Cube."""

from __future__ import annotations

import pytest

from conftest import metric

# (metric id, scope, value, n, values-when-n<min_n, target)
EXPECTED = [
    ("certified_qtd", "org", 3, 3, None, 9),
    ("certified_qtd", "patient", 0, 0, None, 1),
    ("certified_qtd", "hcp", 1, 1, None, 2),
    ("certified_qtd", "market-access", 0, 0, None, 2),
    ("certified_qtd", "revenue-vials", 1, 1, None, 2),
    ("certified_qtd", "r-and-d", 0, 0, None, 1),
    ("certified_qtd", "medical-affairs", 0, 0, None, None),
    ("certified_qtd", "techops", 1, 1, None, 1),
    ("certified_qtd", "channel-partner", 0, 0, None, None),
    ("cycle_time_g1_g4", "org", 173, 10, None, None),
    ("cycle_time_g1_g4", "patient", 160, 1, [160], None),
    ("cycle_time_g1_g4", "hcp", 162, 3, None, None),
    ("cycle_time_g1_g4", "market-access", None, 0, None, None),
    ("cycle_time_g1_g4", "revenue-vials", 209, 3, None, None),
    ("cycle_time_g1_g4", "r-and-d", 159, 2, [142, 176], None),
    ("cycle_time_g1_g4", "medical-affairs", None, 0, None, None),
    ("cycle_time_g1_g4", "techops", 201, 1, [201], None),
    ("cycle_time_g1_g4", "channel-partner", None, 0, None, None),
    ("time_to_first_consumer", "org", 184, 8, None, None),
    ("time_to_first_consumer", "patient", 172, 1, [172], None),
    ("time_to_first_consumer", "hcp", 182, 2, [147, 217], None),
    ("time_to_first_consumer", "market-access", None, 0, None, None),
    ("time_to_first_consumer", "revenue-vials", 211, 3, None, None),
    ("time_to_first_consumer", "r-and-d", 169.5, 2, [153, 186], None),
    ("time_to_first_consumer", "medical-affairs", None, 0, None, None),
    ("time_to_first_consumer", "techops", None, 0, None, None),
    ("time_to_first_consumer", "channel-partner", None, 0, None, None),
    ("active_users_median", "org", 19, 10, None, None),
    ("active_users_median", "patient", 42, 1, [42], None),
    ("active_users_median", "hcp", 12, 3, None, None),
    ("active_users_median", "market-access", None, 0, None, None),
    ("active_users_median", "revenue-vials", 20, 3, None, None),
    ("active_users_median", "r-and-d", 36.5, 2, [18, 55], None),
    ("active_users_median", "medical-affairs", None, 0, None, None),
    ("active_users_median", "techops", 9, 1, [9], None),
    ("active_users_median", "channel-partner", None, 0, None, None),
    ("live_count", "org", 11, 11, None, None),
    ("live_count", "patient", 2, 2, None, None),
    ("live_count", "hcp", 3, 3, None, None),
    ("live_count", "market-access", 0, 0, None, None),
    ("live_count", "revenue-vials", 3, 3, None, None),
    ("live_count", "r-and-d", 2, 2, None, None),
    ("live_count", "medical-affairs", 0, 0, None, None),
    ("live_count", "techops", 1, 1, None, None),
    ("live_count", "channel-partner", 0, 0, None, None),
    ("pipeline_count", "org", 12, 12, None, None),
    ("pipeline_count", "patient", 0, 0, None, None),
    ("pipeline_count", "hcp", 2, 2, None, None),
    ("pipeline_count", "market-access", 1, 1, None, None),
    ("pipeline_count", "revenue-vials", 2, 2, None, None),
    ("pipeline_count", "r-and-d", 3, 3, None, None),
    ("pipeline_count", "medical-affairs", 1, 1, None, None),
    ("pipeline_count", "techops", 3, 3, None, None),
    ("pipeline_count", "channel-partner", 0, 0, None, None),
    ("certified_unused", "org", 1, 1, None, None),
    ("certified_unused", "patient", 0, 0, None, None),
    ("certified_unused", "hcp", 1, 1, None, None),
    ("certified_unused", "market-access", 0, 0, None, None),
    ("certified_unused", "revenue-vials", 0, 0, None, None),
    ("certified_unused", "r-and-d", 0, 0, None, None),
    ("certified_unused", "medical-affairs", 0, 0, None, None),
    ("certified_unused", "techops", 0, 0, None, None),
    ("certified_unused", "channel-partner", 0, 0, None, None),
    ("g4_forecast", "org", 4, 4, None, None),
    ("g4_forecast", "patient", 0, 0, None, None),
    ("g4_forecast", "hcp", 1, 1, None, None),
    ("g4_forecast", "market-access", 0, 0, None, None),
    ("g4_forecast", "revenue-vials", 1, 1, None, None),
    ("g4_forecast", "r-and-d", 2, 2, None, None),
    ("g4_forecast", "medical-affairs", 0, 0, None, None),
    ("g4_forecast", "techops", 0, 0, None, None),
    ("g4_forecast", "channel-partner", 0, 0, None, None),
]


@pytest.mark.parametrize("metric_id, scope, value, n, values, target", EXPECTED, ids=[f"AT-MET-{e[0]}-{e[1]}" for e in EXPECTED])
def test_metric_values(golden_snapshot, metric_id, scope, value, n, values, target):
    m = metric(golden_snapshot, metric_id, scope)
    assert m["value"] == value
    assert m.get("n") == n
    assert m.get("values") == values, "raw values are listed only when n is below min_n"
    assert m.get("target") == target


def test_at_met_09_counts_are_integers_in_json(golden_snapshot):
    for m in golden_snapshot["metrics"]:
        if m["id"] in {"certified_qtd", "live_count", "pipeline_count", "certified_unused", "g4_forecast"}:
            assert isinstance(m["value"], int)


def test_at_met_10_every_number_links_to_its_products(golden_snapshot):
    """The list a number opens must contain exactly the products counted (plan section 11, rules)."""
    units = {d["id"]: d["unit"] for d in golden_snapshot["registry"]["metrics"]}
    for m in golden_snapshot["metrics"]:
        urns = m.get("urns")
        assert urns is not None, m["id"]
        if m["value"] is None and units[m["id"]] == "count":
            assert urns == [] and m.get("reason"), m["id"]  # no number shown: its source is not in the inbox
        elif units[m["id"]] == "count":
            assert len(urns) == m["value"]
        elif units[m["id"]] == "share":
            assert m["value"] is None or len(urns) == round(m["value"] * m["n"])
        else:
            assert len(urns) == m["n"]


def test_at_met_11_certified_qtd_counts_first_g4_only(golden_snapshot):
    """Patient Services Ops was re-certified on 2026-09-25 after a G5; its first G4 was 2026-02-20, so it is not QTD."""
    m = metric(golden_snapshot, "certified_qtd", "hcp")
    assert "urn:dp:com:patient-services-ops" not in m["urns"]
    assert m["urns"] == ["urn:dp:com:hcp-engagement-mart"]


def test_at_met_12_quarter_boundary_sep_30_is_q3(golden_snapshot):
    assert "urn:dp:com:eu-sales-performance" not in metric(golden_snapshot, "certified_qtd", "org")["urns"]
    q3 = {t["domain"]: t["certified"] for t in golden_snapshot["trend"] if t["quarter"] == "2026-Q3"}
    assert q3["revenue-vials"] == 1 and sum(q3.values()) == 4  # EU Sales Performance counts in Q3, not Q4


def test_at_met_13_self_reference_and_inactive_consumers_are_ignored(golden_snapshot):
    from conftest import product

    assert product(golden_snapshot, "urn:dp:com:rep-targeting-lists")["consumedByProducts"] == []
    # Legacy Sales Cube (retired) and Pricing Scenario Model (cancelled) declare inputs but do not count
    assert "urn:dp:com:legacy-sales-cube" not in product(golden_snapshot, "urn:dp:com:patient-journey-360")["consumedByProducts"]
    assert product(golden_snapshot, "urn:dp:com:eu-sales-performance")["consumedByProducts"] == ["urn:dp:com:market-access-insights"]


def test_at_met_14_trend_covers_four_quarters_with_targets(golden_snapshot):
    quarters = sorted({t["quarter"] for t in golden_snapshot["trend"]})
    assert quarters == ["2026-Q1", "2026-Q2", "2026-Q3", "2026-Q4"]
    assert len(golden_snapshot["trend"]) == 4 * len(golden_snapshot["domains"])
    with_target = {t["domain"] for t in golden_snapshot["trend"] if t["target"] is not None}
    assert with_target == {"patient", "hcp", "market-access", "revenue-vials", "r-and-d", "techops"}  # no target row: Channel partner, Medical affairs, Logistics, G&A, Unknown
