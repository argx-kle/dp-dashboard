"""AT-CLI: dp check / build / approve behaviour and template injection."""

from __future__ import annotations

import json
import os
import time

from click.testing import CliRunner

from conftest import BLOCKERS_INBOX, GOLDEN_INBOX
from dp.cli import main
from pipeline.inject import escape_for_script, inject

TEMPLATE = '<!doctype html><html><head><title>t</title></head><body><div id="root"></div><script type="application/json" id="snapshot">{}</script><script>app()</script></body></html>'


def test_at_cli_01_check_exits_zero_on_clean_inbox_and_one_on_blockers():
    runner = CliRunner()
    ok = runner.invoke(main, ["check", "--inbox", str(GOLDEN_INBOX), "--week", "2026-W41"])
    assert ok.exit_code == 0, ok.output
    assert "0 blocker(s), 3 warning(s)" in ok.output
    bad = runner.invoke(main, ["check", "--inbox", str(BLOCKERS_INBOX), "--week", "2026-W41"])
    assert bad.exit_code == 1
    assert "BLOCKER" in bad.output and "row 3" in bad.output


def test_at_cli_02_build_writes_snapshot_dashboard_and_report(tmp_path):
    template = tmp_path / "template.html"
    template.write_text(TEMPLATE, encoding="utf-8")
    runner = CliRunner()
    res = runner.invoke(main, ["build", "--inbox", str(GOLDEN_INBOX), "--week", "2026-W41", "--out", str(tmp_path / "out"), "--state", str(tmp_path / "state"), "--template", str(template)])
    assert res.exit_code == 0, res.output
    out = tmp_path / "out" / "2026-W41"
    assert (out / "snapshot.json").exists() and (out / "index.html").exists() and (out / "dq-report.html").exists()
    html = (out / "index.html").read_text(encoding="utf-8")
    assert '<script type="application/json" id="snapshot">{' in html
    data = json.loads((out / "snapshot.json").read_text(encoding="utf-8"))
    assert data["signOff"] == {"status": "draft"}
    assert "Draft pack built" in res.output


def test_at_cli_03_build_refuses_on_blockers(tmp_path):
    runner = CliRunner()
    res = runner.invoke(main, ["build", "--inbox", str(BLOCKERS_INBOX), "--week", "2026-W41", "--out", str(tmp_path / "out"), "--state", str(tmp_path / "state")])
    assert res.exit_code == 1
    assert not (tmp_path / "out" / "2026-W41" / "snapshot.json").exists()
    assert (tmp_path / "out" / "2026-W41" / "dq-report.html").exists()
    assert "Pack NOT built" in res.output


def test_at_cli_04_injection_escapes_script_terminators():
    payload = json.dumps({"name": "</script><script>alert(1)</script>", "line": "a b"})
    html = inject(TEMPLATE, payload)
    body = html.split('id="snapshot">', 1)[1].split("</script>", 1)[0]
    assert "</script" not in body
    assert "<\\/script>" in body
    assert " " not in body
    # Round trip: the browser's JSON.parse sees the original text
    assert json.loads(escape_for_script(payload)) == json.loads(payload)
    assert html.count('id="snapshot"') == 1


def test_at_cli_05_approve_requires_a_fresh_draft(tmp_path, inbox_copy):
    runner = CliRunner()
    args = ["--inbox", str(inbox_copy), "--out", str(tmp_path / "out"), "--state", str(tmp_path / "state")]
    res = runner.invoke(main, ["build", "--week", "2026-W41", *args, "--template", str(tmp_path / "none.html")])
    assert res.exit_code == 0, res.output
    # Touch the inbox after the build: approve must refuse
    time.sleep(0.05)
    p = inbox_copy / "products.csv"
    os.utime(p, None)
    res = runner.invoke(main, ["approve", "--week", "2026-W41", "--by", "Program lead", *args, "--template", str(tmp_path / "none.html")])
    assert res.exit_code == 1 and "inbox changed" in res.output
    # Rebuild, then approve succeeds and stores the snapshot in state/
    runner.invoke(main, ["build", "--week", "2026-W41", *args, "--template", str(tmp_path / "none.html")])
    res = runner.invoke(main, ["approve", "--week", "2026-W41", "--by", "Program lead", *args, "--template", str(tmp_path / "none.html")])
    assert res.exit_code == 0, res.output
    stored = json.loads((tmp_path / "state" / "snapshots" / "2026-W41.json").read_text(encoding="utf-8"))
    assert stored["signOff"]["status"] == "approved" and stored["signOff"]["approvedBy"] == "Program lead"
    assert (tmp_path / "state" / "baselines.csv").exists()
    # Approving twice is refused
    res = runner.invoke(main, ["approve", "--week", "2026-W41", "--by", "Program lead", *args, "--template", str(tmp_path / "none.html")])
    assert res.exit_code == 1 and "already approved" in res.output
