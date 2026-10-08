"""AT-READ: inbox readers. Written from docs/metric-definitions.md and the inbox contract (plan section 5)."""

from __future__ import annotations

from datetime import date

from conftest import AS_OF, GOLDEN_INBOX, GOLDEN_XLSX, MISSING_COLUMN_INBOX, normalise
from pipeline.build import run_build
from pipeline.readers.base import normalise_header, split_list
from pipeline.readers.register import read_register


def test_at_read_01_headers_are_matched_case_insensitively():
    assert normalise_header("Planned Next Gate Date") == "planned_next_gate_date"
    assert normalise_header(" URN ") == "urn"
    assert normalise_header("Date-passed") == "date_passed"
    assert normalise_header("G5 path") == "g5_path"


def test_at_read_02_csv_and_xlsx_inboxes_produce_the_same_snapshot(tmp_path, regs):
    a = run_build(GOLDEN_INBOX, "2026-W41", tmp_path / "a", tmp_path / "sa", regs=regs, template_path=tmp_path / "none")
    b = run_build(GOLDEN_XLSX, "2026-W41", tmp_path / "b", tmp_path / "sb", regs=regs, template_path=tmp_path / "none")
    assert a.built and b.built
    na, nb = normalise(a.snapshot), normalise(b.snapshot)
    for s in na["sources"] + nb["sources"]:
        s["file"] = "<file>"
    for d in na["dataQuality"] + nb["dataQuality"]:
        d["file"] = "<file>"
    assert na == nb


def test_at_read_03_missing_required_column_is_a_blocker_and_unknown_column_a_warning(regs):
    inbox = read_register(MISSING_COLUMN_INBOX, regs.domains)
    rules = {(i.severity, i.rule) for i in inbox.issues}
    assert ("blocker", "MISSING_COLUMN") in rules
    assert ("warning", "UNKNOWN_COLUMN") in rules
    assert any("Owner Team" in i.message for i in inbox.issues)


def test_at_read_04_lists_are_semicolon_separated():
    assert split_list("a; b ;;c") == ["a", "b", "c"]
    assert split_list("") == []


def test_at_read_05_dates_are_iso_and_rows_are_typed(regs):
    inbox = read_register(GOLDEN_INBOX, regs.domains)
    p = next(p for p in inbox.products if p.urn == "urn:dp:com:patient-journey-360")
    assert p.first_consumer_date == date(2026, 8, 1)
    assert p.active_users_30d == 42
    assert p.named_consumers == 5
    assert p.domain == "patient"
    e = next(e for e in inbox.gate_events if e.urn == "urn:dp:com:brand-health-tracker" and e.gate == "G5")
    assert e.g5_path == "bug fix"
    assert e.date_passed == date(2026, 9, 10)


def test_at_read_06_sources_report_rows_and_status(regs):
    inbox = read_register(GOLDEN_INBOX, regs.domains)
    by_name = {s.name: s for s in inbox.sources}
    assert set(by_name) == {"Products", "GateEvents", "Targets", "Capacity"}
    assert by_name["Products"].rows == 25
    assert by_name["GateEvents"].rows == 78
    assert all(s.status == "ok" for s in inbox.sources)
    assert inbox.latest_mtime > 0


def test_at_read_07_missing_inbox_folder_blocks_every_table(tmp_path, regs):
    inbox = read_register(tmp_path / "nowhere", regs.domains)
    assert sum(1 for i in inbox.blockers if i.rule == "MISSING_TABLE") == 4
    assert all(s.status == "missing" for s in inbox.sources)
    assert AS_OF == date(2026, 10, 9)
