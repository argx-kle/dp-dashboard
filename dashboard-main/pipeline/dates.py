"""Week, quarter and date helpers. Calendar quarters; ISO weeks; the as-of date is the Friday."""

from __future__ import annotations

import re
from datetime import date, datetime, timedelta

WEEK_RE = re.compile(r"^(\d{4})-W(\d{2})$")
QUARTER_RE = re.compile(r"^(\d{4})-Q([1-4])$")
ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")

TRAILING_DAYS = 182
OVERDUE_GRACE_DAYS = 14
REVIEW_STALE_DAYS = 14
UNUSED_AFTER_DAYS = 60


def parse_week(week_id: str) -> tuple[int, int]:
    m = WEEK_RE.match(week_id or "")
    if not m:
        raise ValueError(f"Week must look like 2026-W43, got {week_id!r}")
    year, week = int(m.group(1)), int(m.group(2))
    date.fromisocalendar(year, week, 1)  # raises ValueError when the week does not exist
    return year, week


def week_friday(week_id: str) -> date:
    year, week = parse_week(week_id)
    return date.fromisocalendar(year, week, 5)


def week_of(d: date) -> str:
    iso = d.isocalendar()
    return f"{iso[0]}-W{iso[1]:02d}"


def quarter_of(d: date) -> str:
    return f"{d.year}-Q{(d.month - 1) // 3 + 1}"


def quarter_bounds(quarter: str) -> tuple[date, date]:
    m = QUARTER_RE.match(quarter or "")
    if not m:
        raise ValueError(f"Quarter must look like 2026-Q4, got {quarter!r}")
    year, n = int(m.group(1)), int(m.group(2))
    start = date(year, 3 * (n - 1) + 1, 1)
    end = (date(year + 1, 1, 1) if n == 4 else date(year, 3 * n + 1, 1)) - timedelta(days=1)
    return start, end


def quarters_ending_at(quarter: str, count: int) -> list[str]:
    """`count` consecutive quarters ending with `quarter`, oldest first."""
    m = QUARTER_RE.match(quarter)
    if not m:
        raise ValueError(f"Quarter must look like 2026-Q4, got {quarter!r}")
    year, n = int(m.group(1)), int(m.group(2))
    out: list[str] = []
    for _ in range(count):
        out.append(f"{year}-Q{n}")
        n -= 1
        if n == 0:
            n, year = 4, year - 1
    return list(reversed(out))


def parse_date(value) -> date | None:
    """ISO date (YYYY-MM-DD) or a date/datetime object. Empty -> None. Anything else raises ValueError."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    s = str(value).strip()
    if not s:
        return None
    if not ISO_DATE_RE.match(s):
        raise ValueError(f"Dates must be ISO (YYYY-MM-DD), got {s!r}")
    return date.fromisoformat(s[:10])


def in_trailing_window(d: date | None, as_of: date, days: int = TRAILING_DAYS) -> bool:
    """Half-open window (as_of - days, as_of]."""
    return d is not None and (as_of - timedelta(days=days)) < d <= as_of


def iso(d: date | None) -> str | None:
    return d.isoformat() if d else None
