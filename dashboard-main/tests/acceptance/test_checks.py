"""AT-DQ: data-quality rules (docs/metric-definitions.md, "Data-quality rules")."""

from __future__ import annotations

import pytest

from conftest import AS_OF, BLOCKERS_INBOX, GOLDEN_INBOX, MISSING_COLUMN_INBOX
from pipeline.build import run_check


@pytest.fixture(scope="module")
def blockers(regs):
    check, ctx = run_check(BLOCKERS_INBOX, AS_OF, regs)
    assert ctx is None
    return check


def _has(check, rule, urn=None, severity="blocker"):
    return any(i.rule == rule and i.severity == severity and (urn is None or i.urn == urn) for i in check.issues)


def test_at_dq_01_duplicate_urn(blockers):
    assert _has(blockers, "DUPLICATE_URN", "urn:dp:com:dup-product")


def test_at_dq_02_gate_events_out_of_order(blockers):
    assert _has(blockers, "GATE_ORDER", "urn:dp:tq:out-of-order")


def test_at_dq_03_gate_event_in_the_future(blockers):
    assert _has(blockers, "FUTURE_DATE", "urn:dp:ga:future-gate")


def test_at_dq_04_g4_without_g1(blockers):
    assert _has(blockers, "NO_G1", "urn:dp:rd:regulatory-submissions-tracker")


def test_at_dq_05_screening_email_and_health_term(blockers):
    assert _has(blockers, "SCREENING", "urn:dp:com:screened-comment")
    assert _has(blockers, "SCREENING", "urn:dp:rd:health-comment")


def test_at_dq_06_bad_value_and_unknown_domain_are_row_level(blockers):
    bad = next(i for i in blockers.issues if i.rule == "BAD_VALUE")
    assert bad.row == 8 and bad.file == "products.csv" and "ISO" in bad.message
    assert _has(blockers, "UNKNOWN_DOMAIN", "urn:dp:com:bad-domain")


def test_at_dq_07_unknown_urn_and_g5_before_g4(blockers):
    assert _has(blockers, "UNKNOWN_URN", "urn:dp:xx:ghost")
    assert _has(blockers, "GATE_ORDER", "urn:dp:tq:early-g5")


def test_at_dq_08_missing_required_column_blocks_without_cascading(regs):
    check, ctx = run_check(MISSING_COLUMN_INBOX, AS_OF, regs)
    assert ctx is None
    assert _has(check, "MISSING_COLUMN")
    assert not _has(check, "UNKNOWN_URN"), "a blocked Products table must not turn every event into an unknown URN"


def test_at_dq_09_golden_inbox_has_only_the_expected_warnings(regs):
    check, ctx = run_check(GOLDEN_INBOX, AS_OF, regs)
    assert check.blockers == []
    rules = sorted((i.rule, i.urn) for i in check.warnings)
    assert rules == [
        ("NO_EVIDENCE", "urn:dp:com:field-force-activity"),
        ("NO_EVIDENCE", "urn:dp:tq:equipment-calibration-status"),
        ("NO_USAGE", "urn:dp:com:patient-services-ops"),
    ]


def test_at_dq_10_screening_patterns(regs):
    s = regs.screening
    assert s.match("Contact jane.doe@argenx.com") == "email"
    assert s.match("call +32 470 12 34 56") == "phone"
    assert s.match("ref AB-1234567 on file") == "id_like"
    assert s.match("Patient diagnosed in March") is not None
    assert s.match("Stable; onboarding EU field teams in Q4.") is None
    assert s.match("Re-certified Sep 25 after scope change (new hub integration).") is None
    assert s.match(None) is None
