"""Build register.xlsx from the four CSVs, or an empty DPO template with data validation.

Usage
  python scripts/make_register.py --from-csv tests/fixtures/inbox-golden --out tests/fixtures/inbox-golden-xlsx/register.xlsx
  python scripts/make_register.py --template --out templates/register.xlsx
"""

from __future__ import annotations

import argparse
import csv
import sys
from datetime import date
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill, Protection
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pipeline.readers.register import SPECS  # noqa: E402
from pipeline.registry import load_domains  # noqa: E402

HEADER_FILL = PatternFill("solid", fgColor="002834")
HEADER_FONT = Font(name="Arial", bold=True, color="FFFFFF")
BODY_FONT = Font(name="Arial")
DATE_COLUMNS = {"planned_next_gate_date", "planned_ga_date", "first_consumer_date", "reviewed_on", "cancelled_on", "date_passed"}
TEMPLATE_ROWS = 300


def _style_header(ws, columns: list[str]) -> None:
    for i, col in enumerate(columns, start=1):
        c = ws.cell(row=1, column=i, value=col)
        c.fill, c.font = HEADER_FILL, HEADER_FONT
        c.alignment = Alignment(vertical="center")
        ws.column_dimensions[get_column_letter(i)].width = max(14, min(42, len(col) + 6))
    ws.freeze_panes = "A2"


def _coerce(col: str, value: str):
    if value == "":
        return None
    if col in DATE_COLUMNS:
        return date.fromisoformat(value)
    if col in {"named_consumers", "active_users_30d", "certification_target", "onboarded", "enrolled", "qualified"}:
        return int(value)
    return value


def from_csv(src: Path, out: Path) -> None:
    wb = Workbook()
    wb.remove(wb.active)
    for spec in SPECS.values():
        ws = wb.create_sheet(spec.sheet)
        with open(src / spec.csv, encoding="utf-8-sig", newline="") as fh:
            rows = list(csv.DictReader(fh))
        columns = spec.columns
        _style_header(ws, columns)
        for r, rec in enumerate(rows, start=2):
            for ci, col in enumerate(columns, start=1):
                cell = ws.cell(row=r, column=ci, value=_coerce(col, rec.get(col, "")))
                cell.font = BODY_FONT
                if col in DATE_COLUMNS:
                    cell.number_format = "yyyy-mm-dd"
    out.parent.mkdir(parents=True, exist_ok=True)
    wb.save(out)


def template(out: Path) -> None:
    domains = load_domains()
    wb = Workbook()
    wb.remove(wb.active)
    lists = wb.create_sheet("Lists")
    lists["A1"], lists["B1"], lists["C1"] = "domain", "gate", "g5_path"
    for i, d in enumerate(domains.domains, start=2):
        lists.cell(row=i, column=1, value=d.name)
    for i, g in enumerate(["G1", "G2", "G3", "G4", "G5", "G6"], start=2):
        lists.cell(row=i, column=2, value=g)
    for i, p in enumerate(["scope change", "bug fix"], start=2):
        lists.cell(row=i, column=3, value=p)
    lists.sheet_state = "hidden"

    for spec in SPECS.values():
        ws = wb.create_sheet(spec.sheet)
        columns = spec.columns
        _style_header(ws, columns)
        last = TEMPLATE_ROWS + 1
        for ci, col in enumerate(columns, start=1):
            letter = get_column_letter(ci)
            rng = f"{letter}2:{letter}{last}"
            if col == "domain":
                dv = DataValidation(type="list", formula1=f"=Lists!$A$2:$A${len(domains.domains) + 1}", allow_blank=True)
                dv.error, dv.errorTitle = "Pick a domain from the list.", "Domain"
                ws.add_data_validation(dv)
                dv.add(rng)
            elif col == "gate":
                dv = DataValidation(type="list", formula1="=Lists!$B$2:$B$7", allow_blank=False)
                ws.add_data_validation(dv)
                dv.add(rng)
            elif col == "g5_path":
                dv = DataValidation(type="list", formula1="=Lists!$C$2:$C$3", allow_blank=True)
                ws.add_data_validation(dv)
                dv.add(rng)
            elif col in DATE_COLUMNS:
                dv = DataValidation(type="date", operator="between", formula1="DATE(2020,1,1)", formula2="DATE(2035,12,31)", allow_blank=True)
                dv.error, dv.errorTitle = "Enter a date as YYYY-MM-DD.", "Date"
                ws.add_data_validation(dv)
                dv.add(rng)
                for r in range(2, last + 1):
                    ws.cell(row=r, column=ci).number_format = "yyyy-mm-dd"
            elif col in {"named_consumers", "active_users_30d", "certification_target", "onboarded", "enrolled", "qualified"}:
                dv = DataValidation(type="whole", operator="greaterThanOrEqual", formula1="0", allow_blank=True)
                ws.add_data_validation(dv)
                dv.add(rng)
            for r in range(2, last + 1):
                ws.cell(row=r, column=ci).protection = Protection(locked=False)
        ws.protection.sheet = True  # header row stays locked; data cells are unlocked above
        ws.protection.formatColumns = False
        ws.protection.formatRows = False
        ws.protection.insertRows = False
        ws.protection.sort = False
        ws.protection.autoFilter = False
    readme = wb.create_sheet("README", 0)
    lines = [
        "Data Product register · how to fill this workbook",
        "",
        "Products: one row per data product, keyed on the NextData URN (use pending:<slug> until registered).",
        "GateEvents: one row per gate passed (G1 Intake … G6 Retire) with the date and an evidence link.",
        "Targets: certification target per domain and calendar quarter (2026-Q4). Program lead only.",
        "Capacity: developers onboarded, enrolled and bootcamp-qualified per domain and ISO week (2026-W43).",
        "",
        "Dates are YYYY-MM-DD. Lists (input_products) are separated by semicolons. Header row is locked.",
        "Set reviewed_on every week you review your rows; products not reviewed in 14 days are flagged.",
        "Never put personal or health information in dpo_comment: comments are shown to executives.",
    ]
    for i, line in enumerate(lines, start=1):
        c = readme.cell(row=i, column=1, value=line)
        c.font = Font(name="Arial", bold=(i == 1), size=14 if i == 1 else 11)
    readme.column_dimensions["A"].width = 110
    out.parent.mkdir(parents=True, exist_ok=True)
    wb.save(out)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--from-csv", type=Path)
    ap.add_argument("--template", action="store_true")
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    if args.template:
        template(args.out)
    elif args.from_csv:
        from_csv(args.from_csv, args.out)
    else:
        ap.error("Pass --from-csv DIR or --template")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
