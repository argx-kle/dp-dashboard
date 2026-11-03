"""AT-GOLD-01: the golden inbox builds the checked-in golden snapshot, byte for byte after normalisation.

Regenerate on purpose with: python scripts/update_golden.py
"""

from __future__ import annotations

import json

from conftest import GOLDEN_SNAPSHOT, normalise


def test_at_gold_01_matches_checked_in_snapshot(golden_snapshot):
    expected = json.loads(GOLDEN_SNAPSHOT.read_text(encoding="utf-8"))
    actual = normalise(golden_snapshot)
    assert actual == normalise(expected)


def test_at_gold_02_reproducible(golden_snapshot, regs, tmp_path):
    from conftest import FIXED_GENERATED_AT, GOLDEN_INBOX, WEEK
    from pipeline.build import run_build

    again = run_build(GOLDEN_INBOX, WEEK, tmp_path / "out", tmp_path / "state", regs=regs, generated_at=FIXED_GENERATED_AT, template_path=tmp_path / "none")
    assert normalise(again.snapshot) == normalise(golden_snapshot)


def test_at_gold_03_platform_snapshot_matches(regs, tmp_path):
    """The platform fixture builds tests/fixtures/golden/platform-2026-W41.json (used by the component tests)."""
    from conftest import FIXED_GENERATED_AT, FIXTURES, PLATFORM_INBOX, WEEK
    from pipeline.build import run_build

    res = run_build(PLATFORM_INBOX, WEEK, tmp_path / "out", tmp_path / "state", regs=regs, generated_at=FIXED_GENERATED_AT, template_path=tmp_path / "none")
    expected = json.loads((FIXTURES / "golden" / "platform-2026-W41.json").read_text(encoding="utf-8"))
    assert normalise(res.snapshot) == normalise(expected)


def test_at_gold_04_github_snapshot_matches(regs, tmp_path):
    """The platform fixture plus tests/fixtures/github builds tests/fixtures/golden/github-2026-W41.json (component tests)."""
    import shutil

    from conftest import FIXED_GENERATED_AT, FIXTURES, PLATFORM_INBOX, WEEK
    from pipeline.build import run_build

    inbox = tmp_path / "inbox"
    shutil.copytree(PLATFORM_INBOX, inbox)
    shutil.copytree(FIXTURES / "github", inbox / "github")
    res = run_build(inbox, WEEK, tmp_path / "out", tmp_path / "state", regs=regs, generated_at=FIXED_GENERATED_AT, template_path=tmp_path / "none")
    expected = json.loads((FIXTURES / "golden" / "github-2026-W41.json").read_text(encoding="utf-8"))
    assert normalise(res.snapshot) == normalise(expected)
