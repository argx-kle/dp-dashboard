"""AT-LIFE: status mapping (docs/metric-definitions.md, "Status mapping")."""

from __future__ import annotations

from datetime import date

import pytest

from pipeline.contracts import GateEvent, Product
from pipeline.lifecycle import derive

AS_OF = date(2026, 10, 9)


def _product(**kw) -> Product:
    base = dict(urn="urn:dp:test:x", name="X", domain="hcp", row=1)
    base.update(kw)
    return Product(**base)


def _events(*specs) -> list[GateEvent]:
    out = []
    for i, spec in enumerate(specs, start=1):
        gate, d = spec[0], spec[1]
        path = spec[2] if len(spec) > 2 else None
        out.append(GateEvent(urn="urn:dp:test:x", gate=gate, date_passed=date.fromisoformat(d), row=i, g5_path=path))
    return out


@pytest.mark.parametrize(
    "events, stage, status",
    [
        ([], "Inception", "In design"),
        ([("G1", "2026-08-01")], "Discovery", "In design"),
        ([("G1", "2026-06-01"), ("G2", "2026-08-01")], "Design/Develop", "In build"),
        ([("G1", "2026-04-01"), ("G2", "2026-06-01"), ("G3", "2026-08-01")], "Test/Launch", "In certification"),
        ([("G1", "2026-02-01"), ("G2", "2026-04-01"), ("G3", "2026-06-01"), ("G4", "2026-08-01")], "Operate/Support", "Live"),
        ([("G1", "2025-02-01"), ("G4", "2025-08-01"), ("G6", "2026-06-01")], "Retire", "Retired"),
    ],
    ids=["AT-LIFE-01-none", "AT-LIFE-02-G1", "AT-LIFE-03-G2", "AT-LIFE-04-G3", "AT-LIFE-05-G4", "AT-LIFE-06-G6"],
)
def test_status_from_most_recent_event(events, stage, status):
    d = derive(_product(), _events(*events), AS_OF)
    assert (d.stage, d.status) == (stage, status)


def test_at_life_07_g5_scope_change_loop_with_recertification():
    events = _events(
        ("G1", "2025-09-01"), ("G2", "2025-10-15"), ("G3", "2026-01-10"), ("G4", "2026-02-20"),
        ("G5", "2026-06-01", "scope change"), ("G2", "2026-07-01"), ("G3", "2026-08-20"), ("G4", "2026-09-25"),
    )
    d = derive(_product(), events, AS_OF)
    assert d.status == "Live"
    assert d.iteration == 2
    assert d.first_g4 == date(2026, 2, 20), "first G4 decides the certification date; re-certification is separate"
    assert [g.iteration for g in d.gates] == [1, 1, 1, 1, 2, 2, 2, 2]
    # Mid-loop: after the G5 and the second G2 the product is Live · in revision in Design/Develop
    mid = derive(_product(), events[:6], AS_OF)
    assert (mid.stage, mid.status) == ("Design/Develop", "Live · in revision")
    just_g5 = derive(_product(), events[:5], AS_OF)
    assert (just_g5.stage, just_g5.status) == ("Discovery", "Live · in revision")


def test_at_life_08_g5_bug_fix_path():
    d = derive(_product(), _events(("G1", "2026-01-05"), ("G2", "2026-02-10"), ("G3", "2026-04-01"), ("G4", "2026-05-15"), ("G5", "2026-09-10", "bug fix")), AS_OF)
    assert (d.stage, d.status, d.iteration) == ("Design/Develop", "Live · in revision", 2)
    assert d.next_gate() == "G2"
    assert d.days_in_stage == 29


def test_at_life_09_cancelled_keeps_stage_and_leaves_active_set():
    d = derive(_product(cancelled_on=date(2026, 8, 20)), _events(("G1", "2026-02-01"), ("G2", "2026-04-15")), AS_OF)
    assert (d.stage, d.status) == ("Design/Develop", "Cancelled")
    assert not d.active and not d.live and not d.in_pipeline
    assert d.next_gate() is None


def test_at_life_10_days_in_stage_and_next_gate():
    d = derive(_product(), _events(("G1", "2026-05-04"), ("G2", "2026-07-01"), ("G3", "2026-09-15")), AS_OF)
    assert d.days_in_stage == 24
    assert d.next_gate() == "G4"
    assert derive(_product(), [], AS_OF).next_gate() == "G1"
    live = derive(_product(), _events(("G1", "2026-01-01"), ("G4", "2026-06-01")), AS_OF)
    assert live.next_gate() is None
