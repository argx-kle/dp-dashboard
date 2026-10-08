"""AT-STATE: baselines, slips and the "what changed" note across approved weeks."""

from __future__ import annotations

import csv

from conftest import metric, product
from pipeline.build import run_approve, run_build

URN = "urn:dp:com:omnichannel-campaign-analytics"  # In build, planned GA 2026-12-10


def _set_planned_ga(inbox, urn, new_date):
    path = inbox / "products.csv"
    with open(path, encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
        fields = list(rows[0].keys())
    for r in rows:
        if r["urn"] == urn:
            r["planned_ga_date"] = new_date
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def _build_and_approve(inbox, week, tmp_path, regs):
    res = run_build(inbox, week, tmp_path / "out", tmp_path / "state", regs=regs, template_path=tmp_path / "none")
    assert res.built, [i.message for i in res.check.blockers]
    run_approve(week, "Program lead", tmp_path / "out", tmp_path / "state", None, template_path=tmp_path / "none")
    return res.snapshot


def test_at_state_01_first_plan_becomes_the_baseline_and_slips_count_per_week(tmp_path, inbox_copy, regs):
    s41 = _build_and_approve(inbox_copy, "2026-W41", tmp_path, regs)
    ga = product(s41, URN)["plannedGA"]
    assert ga == {"plannedDate": "2026-12-10", "baselineDate": "2026-12-10", "slips": 0}

    _set_planned_ga(inbox_copy, URN, "2026-12-20")  # moved later once
    s42 = _build_and_approve(inbox_copy, "2026-W42", tmp_path, regs)
    assert product(s42, URN)["plannedGA"] == {"plannedDate": "2026-12-20", "baselineDate": "2026-12-10", "slips": 1}
    assert not any(f["code"] == "SLIPPING" for f in product(s42, URN)["flags"])

    _set_planned_ga(inbox_copy, URN, "2026-12-18")  # moved earlier: not a slip
    s43 = _build_and_approve(inbox_copy, "2026-W43", tmp_path, regs)
    assert product(s43, URN)["plannedGA"]["slips"] == 1

    _set_planned_ga(inbox_copy, URN, "2027-01-15")  # moved later again: second slip -> SLIPPING
    res = run_build(inbox_copy, "2026-W44", tmp_path / "out", tmp_path / "state", regs=regs, template_path=tmp_path / "none")
    p = product(res.snapshot, URN)
    assert p["plannedGA"] == {"plannedDate": "2027-01-15", "baselineDate": "2026-12-10", "slips": 2}
    codes = {f["code"]: f["reason"] for f in p["flags"]}
    assert "SLIPPING" in codes
    assert "NOT_UPDATED" in codes, "by 2026-10-30 the 2026-10-06 review is 24 days old"
    assert "2 times. First plan: 2026-12-10" in codes["SLIPPING"]
    # The product left the Q4 forecast of its domain (HCP)
    assert URN not in metric(res.snapshot, "g4_forecast", "hcp")["urns"]


def test_at_state_02_changes_note_compares_with_last_approved_week(tmp_path, inbox_copy, regs):
    s41 = _build_and_approve(inbox_copy, "2026-W41", tmp_path, regs)
    assert s41["changes"] == ["First snapshot: no previous approved week to compare."]

    # Week 42: Pharmacovigilance Signals passes G4 on 2026-10-14 and Procurement is reviewed again
    with open(inbox_copy / "gate_events.csv", "a", encoding="utf-8", newline="") as fh:
        fh.write("urn:dp:rd:pharmacovigilance-signals,G4,2026-10-14,,https://evidence.example/pv/G4\n")
    path = inbox_copy / "products.csv"
    text = path.read_text(encoding="utf-8").replace(",2026-09-01,\n", ",2026-10-14,\n")
    path.write_text(text, encoding="utf-8")
    res = run_build(inbox_copy, "2026-W42", tmp_path / "out", tmp_path / "state", regs=regs, template_path=tmp_path / "none")
    assert res.built
    changes = res.snapshot["changes"]
    assert len(changes) <= 3
    assert changes[0] == "Certified since 2026-W41: Pharmacovigilance Signals."
    assert any("Cleared: Procurement Spend Cube (NOT_UPDATED)" in c for c in changes)


def test_at_state_03_baselines_file_is_written_once_per_gate(tmp_path, inbox_copy, regs):
    _build_and_approve(inbox_copy, "2026-W41", tmp_path, regs)
    with open(tmp_path / "state" / "baselines.csv", encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    keys = {(r["urn"], r["field"]) for r in rows}
    assert (URN, "GA") in keys and (URN, "G3") in keys
    assert all(r["first_seen_week"] == "2026-W41" for r in rows)
    n = len(rows)
    _build_and_approve(inbox_copy, "2026-W42", tmp_path, regs)
    with open(tmp_path / "state" / "baselines.csv", encoding="utf-8", newline="") as fh:
        assert len(list(csv.DictReader(fh))) == n, "no new baselines when plans did not change gate"
