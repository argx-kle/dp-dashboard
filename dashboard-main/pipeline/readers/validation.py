"""Repo validation tool results: a summary workbook (title block above each table) or a flat CSV.

One record per keyid (the data_product name in spec.py): finish-spec score, component scores, owner as
declared in the repo. Optional input: problems are warnings.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from pipeline.contracts import DQItem
from pipeline.readers.base import cell_to_str, normalise_header, read_csv_rows

EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
ISO_DATE = re.compile(r"(20\d{2})-(\d{2})-(\d{2})")
OWNER_STATUSES = ["Declared", "Drift", "Unconfirmed", "Unresolved", "Partial", "Suspect", "Missing"]
_KEY_COLUMNS = {"keyid", "score", "completeness", "owner", "how_declared", "owner_status", "domain", "version_sep_30", "version",
                "business_name", "git", "notes", "report_snapshot", "run_at", "catalogue_version", "p1_findings", "first_run_pass", "nextdata_name"}


@dataclass
class ValidationRecord:
    keyid: str
    score: float | None = None
    owner_email: str | None = None
    owner_status: str | None = None
    version: str | None = None
    business_name: str | None = None
    git: str | None = None
    notes: str | None = None
    p1_findings: int | None = None
    components: list[tuple[str, float]] = field(default_factory=list)
    row: int = 0


@dataclass
class ValidationRun:
    file: str
    run_date: date | None
    records: list[ValidationRecord]


def split_keyid(raw: str) -> tuple[str, str | None]:
    """'feed (1.0.2)' -> ('feed', '1.0.2')."""
    m = re.match(r"^\s*([^\s(]+)\s*(?:\(([^)]*)\))?\s*$", raw or "")
    return (m.group(1), m.group(2)) if m else ((raw or "").strip(), None)


def _score(value: str) -> float | None:
    s = (value or "").strip().rstrip("%")
    if not s:
        return None
    try:
        f = float(s)
    except ValueError:
        return None
    if "%" in (value or "") or f > 1:
        f /= 100
    return round(f, 4)


def _owner_status(raw_status: str, owner: str) -> str | None:
    for st in OWNER_STATUSES:
        if st.lower() in (raw_status or "").lower():
            return st
    if raw_status:
        return raw_status.strip()
    return "Declared" if EMAIL.search(owner or "") else ("Missing" if owner else None)


def _tables(rows: list[list[str]]) -> list[tuple[list[str], list[list[str]], int]]:
    """Every header row that names a keyid column starts a table; it runs to the next header or the end."""
    def is_header(r: list[str]) -> bool:
        cols = {normalise_header(c) for c in r}
        return "keyid" in cols and bool(cols & {"score", "completeness", "owner", "owner_status", "business_name", "run_at"})

    starts = [i for i, r in enumerate(rows) if is_header(r)]
    out = []
    for n, s in enumerate(starts):
        end = starts[n + 1] if n + 1 < len(starts) else len(rows)
        body = [r for r in rows[s + 1 : end] if any(c.strip() for c in r)]
        out.append(([normalise_header(c) for c in rows[s]], body, s + 1))
    return out


def _run_date(rows: list[list[str]]) -> date | None:
    for r in rows[:8]:
        for c in r:
            m = ISO_DATE.search(c or "")
            if m:
                try:
                    return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
                except ValueError:
                    continue
    return None


def read_validation(path: Path) -> tuple[ValidationRun | None, list[DQItem]]:
    try:
        if path.suffix.lower() in {".xlsx", ".xlsm"}:
            from openpyxl import load_workbook

            wb = load_workbook(path, read_only=True, data_only=True)
            sheets = [[[cell_to_str(c) for c in r] for r in ws.iter_rows(values_only=True)] for ws in wb.worksheets]
            wb.close()
        else:
            headers, body = read_csv_rows(path)
            sheets = [[headers, *body]]
    except Exception as exc:  # noqa: BLE001 - an unreadable optional file is a warning
        return None, [DQItem("warning", "UNREADABLE", f"Validation results could not be read: {exc}", file=path.name)]

    records: dict[str, ValidationRecord] = {}
    components: dict[str, list[tuple[str | None, list[tuple[str, float]], float | None]]] = {}
    run_date = None
    for rows in sheets:
        run_date = run_date or _run_date(rows)
        for header, body, header_row in _tables(rows):
            is_inventory = bool({"owner", "owner_status", "completeness", "business_name"} & set(header))
            comp_cols = [(i, h) for i, h in enumerate(header) if h and h not in _KEY_COLUMNS]
            for k, r in enumerate(body, start=1):
                rec = dict(zip(header, [*r, *[""] * (len(header) - len(r))]))
                keyid, version_hint = split_keyid(rec.get("keyid", ""))
                if not keyid:
                    continue
                if not run_date and rec.get("run_at"):
                    run_date = _run_date([[rec["run_at"]]])
                score = _score(rec.get("completeness") or rec.get("score", ""))
                comps = []
                for i, h in comp_cols:
                    v = _score(r[i] if i < len(r) else "")
                    if v is not None:
                        comps.append((rows[header_row - 1][i].strip() or h, v))
                if is_inventory or keyid not in records:
                    owner = rec.get("owner", "")
                    email = EMAIL.search(owner or "")
                    p1 = rec.get("p1_findings", "").strip()
                    prior = records.get(keyid)
                    records[keyid] = ValidationRecord(
                        keyid=keyid,
                        score=score if score is not None else (prior.score if prior else None),
                        owner_email=email.group(0).lower() if email else None,
                        owner_status=_owner_status(rec.get("owner_status", ""), owner) if (owner or rec.get("owner_status")) else None,
                        version=(rec.get("version_sep_30") or rec.get("version") or version_hint or "").strip() or None,
                        business_name=(rec.get("business_name") or "").strip() or None,
                        git=(rec.get("git") or "").strip() or None,
                        notes=(rec.get("notes") or "").strip() or None,
                        p1_findings=int(float(p1)) if p1.replace(".", "", 1).isdigit() else None,
                        components=prior.components if prior else [],
                        row=k,
                    )
                if comps:
                    components.setdefault(keyid, []).append((version_hint, comps, score))

    # Component scores may come from a separate table (one row per keyid, or per keyid and version).
    for keyid, options in components.items():
        rec = records.get(keyid)
        if rec is None:
            continue
        chosen = next((o for o in options if o[0] and rec.version and rec.version.startswith(o[0])), None)
        chosen = chosen or next((o for o in options if rec.score is not None and o[2] == rec.score), options[0])
        rec.components = chosen[1]
        if rec.score is None:
            rec.score = chosen[2]
    if not records:
        return None, [DQItem("warning", "UNREADABLE", "No table with a 'keyid' column found in the validation results", file=path.name)]
    issues = []
    if run_date is None:
        run_date = date.fromtimestamp(path.stat().st_mtime)
        issues.append(DQItem("warning", "VAL_NO_DATE", f"No run date in the validation results; using the file date {run_date}", file=path.name))
    return ValidationRun(file=path.name, run_date=run_date, records=list(records.values())), issues
