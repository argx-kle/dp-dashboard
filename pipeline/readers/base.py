"""Table reading shared by every reader: CSV or xlsx sheet, header normalisation, column checks."""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path

from pipeline.contracts import DQItem


@dataclass
class TableSpec:
    name: str  # display name, e.g. Products
    sheet: str  # sheet name in register.xlsx
    csv: str  # file name when delivered as CSV
    required: list[str]
    optional: list[str] = field(default_factory=list)

    @property
    def columns(self) -> list[str]:
        return [*self.required, *self.optional]


@dataclass
class RawTable:
    name: str
    file: str
    headers: list[str]
    rows: list[dict[str, str]]  # keyed by normalised header; "" for blanks
    issues: list[DQItem] = field(default_factory=list)
    present: bool = True

    @property
    def blocked(self) -> bool:
        return any(i.severity == "blocker" for i in self.issues)


def normalise_header(header) -> str:
    s = str(header or "").strip().lower()
    s = re.sub(r"[\s\-/]+", "_", s)
    s = re.sub(r"[^a-z0-9_]", "", s)
    return s.strip("_")


def cell_to_str(value) -> str:
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.date().isoformat() if (value.hour, value.minute, value.second) == (0, 0, 0) else value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


def read_csv_rows(path: Path) -> tuple[list[str], list[list[str]]]:
    with open(path, encoding="utf-8-sig", newline="") as fh:
        reader = csv.reader(fh)
        rows = list(reader)
    if not rows:
        return [], []
    return [cell_to_str(h) for h in rows[0]], [[cell_to_str(c) for c in r] for r in rows[1:]]


def read_xlsx_rows(workbook, sheet: str) -> tuple[list[str], list[list[str]]] | None:
    """Sheet lookup is case-insensitive. Returns None when the sheet is missing."""
    match = next((n for n in workbook.sheetnames if n.strip().lower() == sheet.lower()), None)
    if match is None:
        return None
    ws = workbook[match]
    rows = [[cell_to_str(c) for c in r] for r in ws.iter_rows(values_only=True)]
    if not rows:
        return [], []
    return rows[0], rows[1:]


def build_table(spec: TableSpec, file: str, headers: list[str], rows: list[list[str]]) -> RawTable:
    """Apply the spec: normalise headers, flag missing/unknown columns, drop empty rows."""
    norm = [normalise_header(h) for h in headers]
    issues: list[DQItem] = []
    for col in spec.required:
        if col not in norm:
            issues.append(DQItem("blocker", "MISSING_COLUMN", f"{spec.name}: required column '{col}' is missing", file=file))
    for col in spec.optional:
        if col not in norm:
            issues.append(DQItem("warning", "MISSING_COLUMN", f"{spec.name}: optional column '{col}' is missing", file=file))
    known = set(spec.columns)
    for raw, n in zip(headers, norm):
        if n and n not in known:
            issues.append(DQItem("warning", "UNKNOWN_COLUMN", f"{spec.name}: column '{raw}' is not part of the inbox contract and was ignored", file=file))
    seen: set[str] = set()
    for n in norm:
        if n and n in known and n in seen:
            issues.append(DQItem("blocker", "MISSING_COLUMN", f"{spec.name}: column '{n}' appears twice", file=file))
        seen.add(n)

    out_rows: list[dict[str, str]] = []
    for r in rows:
        padded = [*r, *[""] * (len(norm) - len(r))]
        record = {n: v for n, v in zip(norm, padded) if n in known}
        if any(v.strip() for v in record.values()):
            out_rows.append(record)
    return RawTable(spec.name, file, headers, out_rows, issues)


def split_list(value: str) -> list[str]:
    return [p.strip() for p in (value or "").split(";") if p.strip()]


def to_int(value: str, *, default: int | None = None) -> int | None:
    s = (value or "").strip()
    if not s:
        return default
    try:
        f = float(s)
    except ValueError as exc:
        raise ValueError(f"Expected a whole number, got {s!r}") from exc
    if not f.is_integer():
        raise ValueError(f"Expected a whole number, got {s!r}")
    return int(f)
