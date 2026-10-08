"""AT-FLAG: flag rules (docs/metric-definitions.md, "Flags")."""

from __future__ import annotations

from conftest import metric, product


def _codes(snapshot, urn):
    return sorted(f["code"] for f in product(snapshot, urn)["flags"])


def test_at_flag_01_behind_domains(golden_snapshot, regs, tmp_path):
    # Week 41 is 10% into the quarter: less than one product is due anywhere, so nobody is behind yet.
    assert not [m for m in golden_snapshot["metrics"] if m.get("flag") == "BEHIND"]
    # Six weeks on (20 Nov, 56% elapsed) Market access has 0 of the 1 expected: off track, so behind.
    from conftest import FIXED_GENERATED_AT, GOLDEN_INBOX
    from pipeline.build import run_build

    later = run_build(GOLDEN_INBOX, "2026-W47", tmp_path / "out", tmp_path / "state", regs=regs, generated_at=FIXED_GENERATED_AT, template_path=tmp_path / "none").snapshot
    behind = {m["scope"]: m["reason"] for m in later["metrics"] if m["id"] == "certified_qtd" and m.get("flag") == "BEHIND"}
    # Rounding to whole products: 1 x 0.55 rounds to 1, so Patient and R&D owe one each too.
    assert behind == {"market-access": "0 live, 1 expected by today, target 2", "patient": "0 live, 1 expected by today, target 1", "r-and-d": "0 live, 1 expected by today, target 1"}
    assert metric(later, "certified_qtd", "org").get("flag") is None, "BEHIND is a domain flag"


def test_at_flag_02_overdue_after_14_days_only(golden_snapshot):
    assert _codes(golden_snapshot, "urn:dp:com:market-access-insights") == ["OVERDUE"]
    assert _codes(golden_snapshot, "urn:dp:tq:supplier-quality-scorecard") == ["OVERDUE"]
    assert product(golden_snapshot, "urn:dp:com:market-access-insights")["nextGate"]["overdueDays"] == 19
    # 8 days past plan: not yet overdue
    assert _codes(golden_snapshot, "urn:dp:tq:equipment-calibration-status") == []


def test_at_flag_03_no_dpo_only_after_g1(golden_snapshot):
    assert _codes(golden_snapshot, "urn:dp:com:field-force-activity") == ["NO_DPO"]
    assert _codes(golden_snapshot, "urn:dp:rd:study-budget-forecast") == ["NO_DPO"]


def test_at_flag_04_not_updated(golden_snapshot):
    assert _codes(golden_snapshot, "urn:dp:ga:procurement-spend-cube") == ["NOT_UPDATED"]
    assert "38 days old" in product(golden_snapshot, "urn:dp:ga:procurement-spend-cube")["flags"][0]["reason"]


def test_at_flag_05_unused_needs_a_usage_figure(golden_snapshot):
    assert _codes(golden_snapshot, "urn:dp:com:rep-targeting-lists") == ["UNUSED"]
    # Live without usage figure: warning, not a flag
    assert _codes(golden_snapshot, "urn:dp:com:patient-services-ops") == []
    # Live 2 days: too early
    assert _codes(golden_snapshot, "urn:dp:tq:manufacturing-batch-genealogy") == []


def test_at_flag_06_pending_urn(golden_snapshot):
    assert _codes(golden_snapshot, "pending:eu-kol-network") == ["PENDING_URN"]


def test_at_flag_07_inactive_products_carry_no_flags(golden_snapshot):
    assert _codes(golden_snapshot, "urn:dp:com:legacy-sales-cube") == []
    assert _codes(golden_snapshot, "urn:dp:com:pricing-scenario-model") == []


def test_at_flag_08_overdue_products_are_not_in_the_forecast(golden_snapshot):
    forecast = metric(golden_snapshot, "g4_forecast", "org")["urns"]
    assert "urn:dp:com:market-access-insights" not in forecast
    assert sorted(forecast) == [
        "urn:dp:com:omnichannel-campaign-analytics",
        "urn:dp:ga:procurement-spend-cube",
        "urn:dp:rd:biomarker-discovery-feed",
        "urn:dp:rd:pharmacovigilance-signals",
    ]


def test_at_flag_09_exactly_seven_flagged_products(golden_snapshot):
    flagged = [p["urn"] for p in golden_snapshot["products"] if p["flags"]]
    assert len(flagged) == 7


def test_at_flag_10_product_signal_is_the_most_severe_flag(golden_snapshot):
    sig = {p["urn"]: p["signal"] for p in golden_snapshot["products"]}
    assert sig["urn:dp:com:market-access-insights"] == "red"  # OVERDUE
    assert sig["urn:dp:tq:supplier-quality-scorecard"] == "red"  # OVERDUE
    assert sig["urn:dp:com:rep-targeting-lists"] == "orange"  # UNUSED
    assert sig["urn:dp:com:field-force-activity"] == "yellow"  # NO_DPO
    assert sig["urn:dp:ga:procurement-spend-cube"] == "yellow"  # NOT_UPDATED
    assert sig["pending:eu-kol-network"] == "yellow"  # PENDING_URN
    assert sig["urn:dp:com:legacy-sales-cube"] == "grey"  # Retired
    assert sig["urn:dp:com:pricing-scenario-model"] == "grey"  # Cancelled
    assert sig["urn:dp:com:patient-journey-360"] == "green"
    counts = {s: list(sig.values()).count(s) for s in ("red", "orange", "yellow", "green", "grey")}
    assert counts == {"red": 2, "orange": 1, "yellow": 4, "green": 16, "grey": 2}


def test_at_flag_11_worst_signal_wins_and_slipping_is_orange(tmp_path, inbox_copy, regs):
    """A product that is both SLIPPING (orange) and NOT_UPDATED (yellow) shows orange."""
    from pipeline.context import ProductCtx
    from pipeline.contracts import ProductFlag
    from pipeline.flags import product_signal

    class D:
        active = True

    pc = ProductCtx(p=None, d=D())  # type: ignore[arg-type]
    pc.flags = [ProductFlag(code="NOT_UPDATED", reason=""), ProductFlag(code="SLIPPING", reason="")]
    assert product_signal(pc, regs.flags) == "orange"
    pc.flags.append(ProductFlag(code="OVERDUE", reason=""))
    assert product_signal(pc, regs.flags) == "red"
