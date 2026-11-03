"""Seed register.xlsx from the platform files: one Products row per counted product, everything else empty.

Prefilled: urn (nxd:<product>), name, domain, and dpo when the repository declares an owner (as the
email's user name; replace it with the person's name). Gate dates, plans, usage, targets and capacity stay
empty for DPOs and the program lead. A Provenance sheet records where each prefilled value came from.

Usage
  python scripts/seed_register.py --inbox inbox             # writes inbox/register.xlsx (refuses to overwrite without --force)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from openpyxl import load_workbook
from openpyxl.styles import Font

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pipeline.platform import load_platform, resolve  # noqa: E402
from pipeline.readers.register import SPECS  # noqa: E402
from pipeline.registry import load_domains, load_platform_config  # noqa: E402
from scripts.make_register import template  # noqa: E402

OWNER_STATUSES = {"Declared", "Drift"}


def seed_rows(inbox: Path) -> tuple[list[dict], list[tuple[str, str, str, str]], list[str]]:
    """Returns (product rows, provenance rows, warnings)."""
    cfg = load_platform_config()
    domains = load_domains()
    src = load_platform(inbox)
    if not src.present:
        raise SystemExit(f"No platform files under {inbox}/nextdata or {inbox}/validation")
    res = resolve(src, cfg)
    rows, prov, warnings = [], [], []
    order = {d.id: i for i, d in enumerate(domains.domains)}
    for p in res.included:
        urn = f"nxd:{p.key}"
        dom = domains.resolve(p.domain)
        if dom is None:
            warnings.append(f"{urn}: domain {p.domain!r} is unknown; using {cfg.default_domain}")
            dom = domains.resolve(cfg.default_domain)
        row = {"urn": urn, "name": p.display_name, "domain": dom.name}
        prov.append((urn, "urn", urn, "NextData name" if p.names else "validation keyid (not in NextData)"))
        prov.append((urn, "name", p.display_name, "crosswalk, repository business name or the technical name"))
        prov.append((urn, "domain", dom.name, {"product-domains.yaml": "registry/product-domains.yaml", "name rule": "name rule (registry/platform.yaml)", "team": "team of the name prefix", "default": "no rule matched: Unknown"}.get(p.domain_rule, p.domain_rule)))
        rec = p.validation
        if rec and rec.owner_email and rec.owner_status in OWNER_STATUSES:
            row["dpo"] = rec.owner_email.split("@")[0]
            prov.append((urn, "dpo", row["dpo"], f"repository owner ({rec.owner_status}); replace with the person's name"))
        rows.append(row)
    rows.sort(key=lambda r: (order[domains.resolve(r["domain"]).id], r["name"].lower()))
    return rows, prov, warnings


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--inbox", type=Path, default=Path("inbox"))
    ap.add_argument("--out", type=Path)
    ap.add_argument("--force", action="store_true", help="overwrite an existing register")
    args = ap.parse_args()
    out = args.out or args.inbox / "register.xlsx"
    if out.exists() and not args.force:
        sys.exit(f"{out} exists; pass --force to overwrite it (DPO entries would be lost)")

    rows, prov, warnings = seed_rows(args.inbox)
    template(out)
    wb = load_workbook(out)
    ws = wb["Products"]
    cols = SPECS["products"].columns
    for r, rec in enumerate(rows, start=2):
        for c, col in enumerate(cols, start=1):
            if rec.get(col):
                ws.cell(row=r, column=c, value=rec[col])
    pv = wb.create_sheet("Provenance")
    for c, h in enumerate(["urn", "field", "value", "source"], start=1):
        pv.cell(row=1, column=c, value=h).font = Font(bold=True)
    for r, line in enumerate(prov, start=2):
        for c, v in enumerate(line, start=1):
            pv.cell(row=r, column=c, value=v)
    pv.column_dimensions["A"].width = 44
    pv.column_dimensions["D"].width = 60
    wb.save(out)
    print(f"wrote {out}: {len(rows)} products seeded; gate dates, plans and usage are left for the DPOs")
    for w in warnings:
        print("  warning:", w)


if __name__ == "__main__":
    main()
