"""Reads the product register: register.xlsx with four sheets, or the four CSV files."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from pipeline.contracts import (
    G5_PATHS,
    GATES,
    Capacity,
    DQItem,
    GateEvent,
    Inbox,
    Product,
    SourceStatus,
    Target,
)
from pipeline.dates import QUARTER_RE, WEEK_RE, parse_date
from pipeline.readers.base import (
    RawTable,
    TableSpec,
    build_table,
    read_csv_rows,
    read_xlsx_rows,
    split_list,
    to_int,
)
from pipeline.registry import DomainRegistry

WORKBOOK = "register.xlsx"

SPECS: dict[str, TableSpec] = {
    "products": TableSpec(
        name="Products",
        sheet="Products",
        csv="products.csv",
        required=["urn", "name", "domain", "dpo", "planned_next_gate_date", "planned_ga_date", "reviewed_on"],
        optional=["named_consumers", "input_products", "active_users_30d", "first_consumer_date", "dpo_comment", "cancelled_on"],
    ),
    "gate_events": TableSpec(
        name="GateEvents",
        sheet="GateEvents",
        csv="gate_events.csv",
        required=["urn", "gate", "date_passed"],
        optional=["g5_path", "evidence_url"],
    ),
    "targets": TableSpec(
        name="Targets",
        sheet="Targets",
        csv="targets.csv",
        required=["domain", "quarter", "certification_target"],
    ),
    "capacity": TableSpec(
        name="Capacity",
        sheet="Capacity",
        csv="capacity.csv",
        required=["domain", "week", "onboarded", "enrolled", "qualified"],
    ),
}


def _find_file(inbox: Path, name: str) -> Path | None:
    for p in inbox.iterdir() if inbox.exists() else []:
        if p.is_file() and p.name.lower() == name.lower():
            return p
    return None


def _mtime_iso(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat(timespec="seconds")


def load_tables(inbox_dir: Path) -> tuple[dict[str, RawTable], list[SourceStatus], list[DQItem], float]:
    """Locate and read the four register tables. Workbook wins over CSVs when both exist."""
    tables: dict[str, RawTable] = {}
    sources: list[SourceStatus] = []
    issues: list[DQItem] = []
    latest_mtime = 0.0

    workbook_path = _find_file(inbox_dir, WORKBOOK)
    workbook = None
    if workbook_path is not None:
        try:
            from openpyxl import load_workbook

            workbook = load_workbook(workbook_path, read_only=True, data_only=True)
            latest_mtime = max(latest_mtime, workbook_path.stat().st_mtime)
        except Exception as exc:  # noqa: BLE001 - any failure to open is a blocker
            issues.append(DQItem("blocker", "UNREADABLE", f"{WORKBOOK} could not be opened: {exc}", file=WORKBOOK))
            workbook = None

    for key, spec in SPECS.items():
        if workbook is not None:
            file = f"{WORKBOOK}#{spec.sheet}"
            result = read_xlsx_rows(workbook, spec.sheet)
            if result is None:
                issues.append(DQItem("blocker", "MISSING_TABLE", f"Sheet '{spec.sheet}' is missing from {WORKBOOK}", file=file))
                sources.append(SourceStatus(spec.name, file, _mtime_iso(workbook_path), "missing", 0))
                tables[key] = RawTable(spec.name, file, [], [], present=False)
                continue
            headers, rows = result
            table = build_table(spec, file, headers, rows)
            sources.append(SourceStatus(spec.name, file, _mtime_iso(workbook_path), "ok", len(table.rows)))
        else:
            csv_path = _find_file(inbox_dir, spec.csv)
            file = spec.csv
            if csv_path is None:
                issues.append(DQItem("blocker", "MISSING_TABLE", f"Neither {WORKBOOK} (sheet {spec.sheet}) nor {spec.csv} found in the inbox", file=file))
                sources.append(SourceStatus(spec.name, file, "", "missing", 0))
                tables[key] = RawTable(spec.name, file, [], [], present=False)
                continue
            try:
                headers, rows = read_csv_rows(csv_path)
            except Exception as exc:  # noqa: BLE001
                issues.append(DQItem("blocker", "UNREADABLE", f"{spec.csv} could not be read: {exc}", file=file))
                sources.append(SourceStatus(spec.name, file, _mtime_iso(csv_path), "missing", 0))
                tables[key] = RawTable(spec.name, file, [], [], present=False)
                continue
            latest_mtime = max(latest_mtime, csv_path.stat().st_mtime)
            table = build_table(spec, file, headers, rows)
            sources.append(SourceStatus(spec.name, file, _mtime_iso(csv_path), "ok", len(table.rows)))
        tables[key] = table
        issues.extend(table.issues)

    if workbook is not None:
        workbook.close()
    return tables, sources, issues, latest_mtime


# ---------------------------------------------------------------------------
# Row coercion. Every bad value is a row-level blocker, never an exception.
# ---------------------------------------------------------------------------


class _RowErrors:
    def __init__(self, file: str, row: int, urn: str | None, issues: list[DQItem]):
        self.file, self.row, self.urn, self.issues = file, row, urn, issues
        self.failed = False

    def date(self, record: dict[str, str], col: str):
        try:
            return parse_date(record.get(col, ""))
        except ValueError as exc:
            self._bad(col, exc)
            return None

    def int(self, record: dict[str, str], col: str, default: int | None = None):
        try:
            return to_int(record.get(col, ""), default=default)
        except ValueError as exc:
            self._bad(col, exc)
            return default

    def _bad(self, col: str, exc: Exception):
        self.failed = True
        self.issues.append(DQItem("blocker", "BAD_VALUE", f"{col}: {exc}", urn=self.urn, file=self.file, row=self.row))


def _text(record: dict[str, str], col: str) -> str | None:
    v = (record.get(col) or "").strip()
    return v or None


def parse_products(table: RawTable, domains: DomainRegistry, issues: list[DQItem]) -> list[Product]:
    out: list[Product] = []
    if not table.present or table.blocked:
        return out
    for i, rec in enumerate(table.rows, start=1):
        urn = _text(rec, "urn")
        err = _RowErrors(table.file, i, urn, issues)
        if not urn:
            err._bad("urn", ValueError("URN is empty"))
            continue
        name = _text(rec, "name")
        if not name:
            err._bad("name", ValueError("name is empty"))
        raw_domain = _text(rec, "domain")
        domain = domains.resolve(raw_domain)
        if domain is None:
            issues.append(DQItem("blocker", "UNKNOWN_DOMAIN", f"domain {raw_domain!r} is not one of {', '.join(d.name for d in domains.domains)}", urn=urn, file=table.file, row=i))
            err.failed = True
        product = Product(
            urn=urn,
            name=name or "",
            domain=domain.id if domain else "",
            row=i,
            dpo=_text(rec, "dpo"),
            planned_next_gate_date=err.date(rec, "planned_next_gate_date"),
            planned_ga_date=err.date(rec, "planned_ga_date"),
            named_consumers=err.int(rec, "named_consumers", default=0) or 0,
            input_products=split_list(rec.get("input_products", "")),
            active_users_30d=err.int(rec, "active_users_30d"),
            first_consumer_date=err.date(rec, "first_consumer_date"),
            dpo_comment=_text(rec, "dpo_comment"),
            reviewed_on=err.date(rec, "reviewed_on"),
            cancelled_on=err.date(rec, "cancelled_on"),
        )
        if not err.failed:
            out.append(product)
    return out


def parse_gate_events(table: RawTable, issues: list[DQItem]) -> list[GateEvent]:
    out: list[GateEvent] = []
    if not table.present or table.blocked:
        return out
    for i, rec in enumerate(table.rows, start=1):
        urn = _text(rec, "urn")
        err = _RowErrors(table.file, i, urn, issues)
        if not urn:
            err._bad("urn", ValueError("URN is empty"))
            continue
        gate = (_text(rec, "gate") or "").upper().replace(" ", "")
        if gate not in GATES:
            err._bad("gate", ValueError(f"gate must be one of {', '.join(GATES)}, got {rec.get('gate')!r}"))
        when = err.date(rec, "date_passed")
        if when is None and not err.failed:
            err._bad("date_passed", ValueError("date_passed is empty"))
        g5_path = (_text(rec, "g5_path") or "").lower().replace("-", " ").replace("_", " ") or None
        if gate == "G5":
            if g5_path is None:
                issues.append(DQItem("warning", "NO_G5_PATH", "G5 without g5_path; treated as scope change", urn=urn, file=table.file, row=i))
                g5_path = "scope change"
            elif g5_path not in G5_PATHS:
                err._bad("g5_path", ValueError(f"g5_path must be one of {', '.join(G5_PATHS)}, got {rec.get('g5_path')!r}"))
        else:
            g5_path = None
        if not err.failed and when is not None:
            out.append(GateEvent(urn=urn, gate=gate, date_passed=when, row=i, g5_path=g5_path, evidence_url=_text(rec, "evidence_url")))
    return out


def parse_targets(table: RawTable, domains: DomainRegistry, issues: list[DQItem]) -> list[Target]:
    out: list[Target] = []
    if not table.present or table.blocked:
        return out
    for i, rec in enumerate(table.rows, start=1):
        err = _RowErrors(table.file, i, None, issues)
        domain = domains.resolve(_text(rec, "domain"))
        if domain is None:
            issues.append(DQItem("blocker", "UNKNOWN_DOMAIN", f"Targets: domain {rec.get('domain')!r} is unknown", file=table.file, row=i))
            continue
        quarter = (_text(rec, "quarter") or "").upper()
        if not QUARTER_RE.match(quarter):
            err._bad("quarter", ValueError(f"quarter must look like 2026-Q4, got {rec.get('quarter')!r}"))
        target = err.int(rec, "certification_target")
        if target is None and not err.failed:
            err._bad("certification_target", ValueError("certification_target is empty"))
        if not err.failed and target is not None:
            out.append(Target(domain=domain.id, quarter=quarter, certification_target=target, row=i))
    return out


def parse_capacity(table: RawTable, domains: DomainRegistry, issues: list[DQItem]) -> list[Capacity]:
    out: list[Capacity] = []
    if not table.present or table.blocked:
        return out
    for i, rec in enumerate(table.rows, start=1):
        err = _RowErrors(table.file, i, None, issues)
        domain = domains.resolve(_text(rec, "domain"))
        if domain is None:
            issues.append(DQItem("blocker", "UNKNOWN_DOMAIN", f"Capacity: domain {rec.get('domain')!r} is unknown", file=table.file, row=i))
            continue
        week = (_text(rec, "week") or "").upper()
        if not WEEK_RE.match(week):
            err._bad("week", ValueError(f"week must look like 2026-W43, got {rec.get('week')!r}"))
        vals = {c: err.int(rec, c, default=0) or 0 for c in ("onboarded", "enrolled", "qualified")}
        if not err.failed:
            out.append(Capacity(domain=domain.id, week=week, row=i, **vals))
    return out


def read_register(inbox_dir: Path, domains: DomainRegistry) -> Inbox:
    tables, sources, issues, latest_mtime = load_tables(inbox_dir)
    inbox = Inbox(sources=sources, issues=issues, latest_mtime=latest_mtime)
    inbox.products = parse_products(tables["products"], domains, issues)
    inbox.gate_events = parse_gate_events(tables["gate_events"], issues)
    inbox.targets = parse_targets(tables["targets"], domains, issues)
    inbox.capacity = parse_capacity(tables["capacity"], domains, issues)
    return inbox
