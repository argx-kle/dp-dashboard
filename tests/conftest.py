"""Shared fixtures. Agents build and test against synthetic fixtures only."""

from __future__ import annotations

import json
import shutil
from datetime import date, datetime, timezone
from pathlib import Path

import pytest

from pipeline.build import Registries, run_build, run_check
from pipeline.context import build_context
from pipeline.dates import week_friday

FIXTURES = Path(__file__).parent / "fixtures"
GOLDEN_INBOX = FIXTURES / "inbox-golden"
PLATFORM_INBOX = FIXTURES / "inbox-platform"
GOLDEN_XLSX = FIXTURES / "inbox-golden-xlsx"
BLOCKERS_INBOX = FIXTURES / "inbox-blockers"
MISSING_COLUMN_INBOX = FIXTURES / "inbox-missing-column"
GOLDEN_SNAPSHOT = FIXTURES / "golden" / "2026-W41.json"
WEEK = "2026-W41"
AS_OF = week_friday(WEEK)  # 2026-10-09
FIXED_GENERATED_AT = datetime(2026, 10, 8, 9, 0, tzinfo=timezone.utc)


@pytest.fixture(scope="session")
def regs() -> Registries:
    return Registries.load()


@pytest.fixture(scope="session")
def golden_check(regs):
    check, ctx = run_check(GOLDEN_INBOX, AS_OF, regs)
    assert ctx is not None, [i.message for i in check.blockers]
    return check, ctx


@pytest.fixture(scope="session")
def ctx(golden_check):
    return golden_check[1]


@pytest.fixture(scope="session")
def golden_snapshot(tmp_path_factory, regs) -> dict:
    """The snapshot built from the golden inbox with an empty state folder."""
    base = tmp_path_factory.mktemp("golden")
    result = run_build(GOLDEN_INBOX, WEEK, base / "out", base / "state", regs=regs, generated_at=FIXED_GENERATED_AT, template_path=base / "no-template.html")
    assert result.built, [i.message for i in result.check.blockers]
    return result.snapshot


@pytest.fixture(scope="session")
def platform_cfg():
    from pipeline.registry import load_platform_config

    return load_platform_config()


@pytest.fixture
def platform_copy(tmp_path) -> Path:
    dst = tmp_path / "inbox-platform"
    shutil.copytree(PLATFORM_INBOX, dst)
    return dst


@pytest.fixture
def inbox_copy(tmp_path) -> Path:
    dst = tmp_path / "inbox"
    shutil.copytree(GOLDEN_INBOX, dst)
    return dst


def metric(snapshot: dict, metric_id: str, scope: str) -> dict:
    return next(m for m in snapshot["metrics"] if m["id"] == metric_id and m["scope"] == scope)


def product(snapshot: dict, urn: str) -> dict:
    return next(p for p in snapshot["products"] if p["urn"] == urn)


def normalise(snapshot: dict) -> dict:
    """Strip fields that legitimately differ between runs (clock, file mtimes)."""
    data = json.loads(json.dumps(snapshot))
    data["generatedAt"] = "<generated>"
    for s in data["sources"]:
        s["asOf"] = "<mtime>"
    return data
