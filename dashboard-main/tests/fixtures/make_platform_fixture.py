"""Write tests/fixtures/inbox-platform/: a register plus NextData and validation-tool exports. Invented names and values.

The layouts copy the real exports (fixed-width listing, catalog lookup with NOT FOUND rows, a domain tree whose
columns are jammed into one cell with tree glyphs, a validation workbook with title blocks above its tables),
so every reader rule and identity rule has a case here.

Usage: python tests/fixtures/make_platform_fixture.py
"""

from __future__ import annotations

import csv
from pathlib import Path

from openpyxl import Workbook

OUT = Path(__file__).resolve().parent / "inbox-platform"

# name, env, version, state, rpc
LISTING = [
    ("dp-ops-crmsys", "dev", "1.2.0", "Started", "READY"),
    ("dp-ops-crmsys", "dev", "1.1.0", "Failed", "READY"),
    ("crmsys", "dev", "1.0.0-dev", "Failed", "-"),
    ("dp-ops-rxfeed", "dev", "1.1.0", "Started", "-"),
    ("rxfeed-quarterly", "dev", "1.0.0-dev", "Failed", "-"),
    ("rxfeed-monthly", "dev", "1.0.0-dev", "Started", "-"),
    ("lab-feed-weekly", "dev", "1.0.0-dev", "Started", "READY"),
    ("marketmix-monthly", "dev", "1.0.0-dev", "Failed", "-"),
    ("hubservice-nxd", "dev", "3.0.0", "Started", "READY"),
    ("dp-hcp-hcp-master", "dev", "1.1.0", "Started", "-"),
    ("dp-hcp-hcp-master", "prod", "1.1.0", "Started", "READY"),
    ("dp-hcp-call-activity", "dev", "1.1.0", "Started", "-"),
    ("dp-hcp-territory-plan", "dev", "1.0.0-dev", "Started", "-"),
    ("dp-patient-patient-journey", "dev", "1.0.0-dev", "Started", "-"),
    ("dp-patient-journey-insights", "dev", "1.0.0-dev", "Started", "-"),
    ("journey-insights", "nxd", "1.0.0-dev", "Started", "READY"),
    ("journey-insights-v2", "demo", "1.0.0-dev", "Started", "READY"),
    ("patient-registry", "demo", "0.1.0-dev", "Failed", "-"),
    ("dp-claims-rx-claims", "dev", "1.0.0-dev", "Failed", "-"),
    ("dp-claims-payer-directory", "dev", "1.0.0-dev", "Failed", "-"),
    ("payer-directory", "dev", "0.1.0-dev", "Started", "-"),
    ("dp-ops-sample-template", "dev", "1.0.0-dev", "Failed", "-"),
    ("dp-ops-load-test", "dev", "1.0.0-dev", "Failed", "-"),
    ("dp-ops-dummy-widgets", "dev", "0.1.0-dev", "Started", "-"),
    ("dp-ops-alpha-dp", "dev", "1.0.0-dev", "UNREACHABLE", "-"),
    ("dp-gov-policy-framework", "dev", "1.0.1", "Started", "-"),
    ("lost-glossary", "demo", "1.0.0-dev", "UNREACHABLE", "-"),
    ("demo-glossary", "demo", "1.0.0-dev", "Started", "-"),
    ("synthetic-feed", "dev", "1.0.0-dev", "Started", "-"),
]

CATALOG_DOMAIN = {
    "dp-ops-crmsys": "NOT FOUND",  # two deployments: the lookup was ambiguous
    "crmsys": "COMMERCIAL",
    "dp-ops-rxfeed": "EDP/Ops",
    "rxfeed-quarterly": "EDP/Ops",
    "rxfeed-monthly": "commercial",
    "lab-feed-weekly": "EDP/Ops",
    "marketmix-monthly": "COMMERCIAL",
    "hubservice-nxd": "COMMERCIAL",
    "dp-hcp-hcp-master": "commercial",
    "dp-hcp-call-activity": "commercial",
    "dp-hcp-territory-plan": "Commercial",
    "dp-patient-patient-journey": "commercial",
    "dp-patient-journey-insights": "EDP/Patient",
    "journey-insights": "COMMERCIAL",
    "journey-insights-v2": "COMMERCIAL",
    "patient-registry": "COMMERCIAL",
    "dp-claims-rx-claims": "commercial",
    "dp-claims-payer-directory": "commercial",
    "payer-directory": "COMMERCIAL",
    "dp-ops-sample-template": "EDP/Ops",
    "dp-ops-load-test": "commercial",
    "dp-ops-dummy-widgets": "EDP/Ops",
    "dp-ops-alpha-dp": "NOT FOUND",
    "dp-gov-policy-framework": "governance",
    "lost-glossary": "NOT FOUND",
    "demo-glossary": "ENTERPRISE",
    "synthetic-feed": "COMMERCIAL",
}
CATALOG_OWNER = {"dp-hcp-hcp-master": "HCP data team"}

# domain, parent, description, deployments, created. Top-level counts sum to len(LISTING).
TREE = [
    ("COMMERCIAL", "", "", "17", ""),
    ("COMMERCIAL/ANALYTICS", "COMMERCIAL", "", "", ""),
    ("EDP", "", "Enterprise data platform", "10", "2026-07-01"),
    ("EDP/OPS", "EDP", "Ops team domain (managed by IaC)", "8", "2026-07-01"),
    ("EDP/HCP", "EDP", "HCP team domain (managed by IaC)", "", "2026-07-01"),
    ("EDP/PATIENT", "EDP", "Patient team domain (managed by IaC)", "1", "2026-07-20"),
    ("EDP/CLAIMS", "EDP", "Claims team domain (managed by IaC)", "", "2026-09-01"),
    ("EDP/GOV", "EDP", "Gov team domain (managed by IaC)", "1", "2026-08-15"),
    ("ENTERPRISE", "", "", "1", ""),
    ("GOVERNANCE", "", "", "1", ""),
    ("SANDBOX", "", "", "", ""),
]

# keyid (with optional version), score, component scores (spec, metadata, runtime)
STATUS = [
    ("crmsys", 0.7341, [1, 0.1219, 1]),
    ("feed-lab-weekly", 0.7175, [0.85, 0.1971, 1]),
    ("marketmix", 0.6009, [0.6773, 0.0571, 0.725]),
    ("marketmix-jdoe", 0.6009, [0.6773, 0.0571, 0.725]),
    ("hubservice", 0.6401, [0.7227, 0.0571, 1]),
    ("hcp-master", 0.8812, [1, 0.62, 1]),
    ("journey-insights", 0.7365, [1, 0.1219, 1]),
    ("journey-insights-v2", 0.695, [1, 0.0625, 1]),
    ("patient-registry", 0.638, [0.9045, 0.0625, 1]),
    ("payer-directory (0.1.0-dev)", 0.7103, [0.9, 0.1971, 0.7643]),
    ("payer-directory (0.0.9)", 0.644, [0.7727, 0.0571, 0.7643]),
    ("planning-tool", 0.6386, [0.7727, 0.0571, 1]),
    ("synthetic-feed", 0.5915, [0.9045, 0.0625, 0.7643]),
]

# keyid, owner, how declared, owner status, domain, version, completeness, business_name, git, notes
INVENTORY = [
    ("crmsys", "a.lane@example.com", "owner control", "Declared", "COMMERCIAL", "1.0.0-dev", 0.7341, "crm system", "https://git.example/edp-ops-dp-crmsys", ""),
    ("feed-lab-weekly", "Unresolved (_OWNER_EMAIL)", "metadata Drift / env", "Unresolved", "env _DOMAIN", "1.0.0-dev", 0.7175, "Lab Feed Weekly", "", ""),
    ("marketmix", "Missing", "—", "Missing", "COMMERCIAL", "1.0.0-dev", 0.6009, "Missing", "", "Clone of marketmix-jdoe"),
    ("marketmix-jdoe", "Missing", "—", "Missing", "COMMERCIAL", "1.1.1-dev", 0.6009, "Missing", "", ""),
    ("hubservice", "b.ortiz@example.com (code default; unconfirmed)", "_OWNER_EMAIL unresolved", "Unconfirmed", "COMMERCIAL / env", "3.0.0", 0.6401, "Missing", "https://git.example/edp-ops-dp-hubservice/", ""),
    ("hcp-master", "c.ngata@example.com", "metadata (Drift)", "Drift", "env _DOMAIN", "1.1.0", 0.8812, "hcp master", "", ""),
    ("journey-insights", "d.voss@example.com", "owner control", "Declared", "COMMERCIAL", "1.0.0-dev", 0.7365, "Journey Insights", "https://git.example/examples/journey-insights-v1", ""),
    ("journey-insights-v2", "d.voss@example.com", "owner control", "Declared", "COMMERCIAL", "1.0.0-dev", 0.695, "Missing", "", "demo"),
    ("patient-registry", "e.kim@example.com", "owner control", "Declared", "COMMERCIAL", "0.1.0-dev", 0.638, "Missing", "", ""),
    ("payer-directory", "f.amin@example.com on 0.1.0-dev only", "metadata Drift", "Suspect", "COMMERCIAL", "0.1.0-dev (also 0.0.9)", 0.7103, "1.0 wrongly = crm system", "https://git.example/edp-ops-dp-payer_directory/", ""),
    ("planning-tool", "Missing", "—", "Missing", "COMMERCIAL", "1.0.0-dev", 0.6386, "Missing", "https://git.example/edp-ops-dp-planning_tool/", "Not deployed yet"),
    ("synthetic-feed", "g.ruiz@example.com", "owner control", "Declared", "COMMERCIAL", "1.0.0-dev", 0.5915, "Missing", "", "Sandbox"),
]

PRODUCTS = [
    # urn, name, domain, dpo, planned_next_gate_date, planned_ga_date, named_consumers, input_products, active_users_30d, first_consumer_date, dpo_comment, reviewed_on, cancelled_on
    ("nxd:dp-ops-crmsys", "CRM system", "HCP", "Ana Lane", "", "2026-08-01", "3", "", "14", "2026-08-20", "", "2026-10-06", ""),
    ("nxd:dp-hcp-hcp-master", "HCP master", "HCP", "Chris Ngata", "", "2026-10-01", "4", "nxd:dp-ops-crmsys", "22", "2026-10-05", "", "2026-10-07", ""),
    ("nxd:dp-patient-journey-insights", "Journey insights", "Patient", "Dana Voss", "2026-11-20", "2026-12-15", "1", "nxd:dp-ops-crmsys", "", "", "", "2026-10-02", ""),
    ("nxd:dp-claims-rx-claims", "Rx claims", "Market access", "Farid Amin", "2026-10-30", "2027-02-01", "0", "", "", "", "", "", ""),
    ("nxd:hubservice-nxd", "Hub service", "Unknown", "", "", "", "0", "", "", "", "", "", ""),
    ("urn:dp:com:legacy-cube", "Legacy cube", "Revenue / vials", "Ana Lane", "2026-11-01", "2026-12-01", "0", "", "", "", "", "2026-10-05", ""),
]
GATES = [
    ("nxd:dp-ops-crmsys", "G1", "2026-02-02", "", "https://evidence.example/crmsys/G1"),
    ("nxd:dp-ops-crmsys", "G2", "2026-03-16", "", "https://evidence.example/crmsys/G2"),
    ("nxd:dp-ops-crmsys", "G3", "2026-05-18", "", "https://evidence.example/crmsys/G3"),
    ("nxd:dp-ops-crmsys", "G4", "2026-07-27", "", "https://evidence.example/crmsys/G4"),
    ("nxd:dp-hcp-hcp-master", "G1", "2026-03-02", "", "https://evidence.example/hcp-master/G1"),
    ("nxd:dp-hcp-hcp-master", "G2", "2026-04-20", "", "https://evidence.example/hcp-master/G2"),
    ("nxd:dp-hcp-hcp-master", "G3", "2026-07-06", "", "https://evidence.example/hcp-master/G3"),
    ("nxd:dp-hcp-hcp-master", "G4", "2026-10-01", "", "https://evidence.example/hcp-master/G4"),
    ("nxd:dp-patient-journey-insights", "G1", "2026-06-01", "", "https://evidence.example/journey-insights/G1"),
    ("nxd:dp-patient-journey-insights", "G2", "2026-08-17", "", "https://evidence.example/journey-insights/G2"),
    ("nxd:dp-claims-rx-claims", "G1", "2026-09-07", "", "https://evidence.example/rx-claims/G1"),
    ("urn:dp:com:legacy-cube", "G1", "2026-05-04", "", ""),
]
TARGETS = [("HCP", "2026-Q4", "2"), ("Patient", "2026-Q4", "1"), ("Logistics", "2026-Q4", "1")]
CAPACITY = [("HCP", "2026-W41", "12", "8", "5")]

CROSSWALK = [
    # source, name, product, include, reason, rule, domain, display_name, reviewed
    ("nextdata", "dp-ops-crmsys", "dp-ops-crmsys", "yes", "Data product", "canonical", "HCP", "CRM system", "yes"),
    ("nextdata", "crmsys", "dp-ops-crmsys", "yes", "Older name of dp-ops-crmsys", "alias:team-prefix", "", "", "yes"),
    ("nextdata", "rxfeed-monthly", "rxfeed-monthly", "yes", "Shipment feed", "canonical", "Logistics", "", "yes"),
    ("nextdata", "demo-glossary", "demo-glossary", "yes", "Enterprise glossary, counted on purpose", "canonical", "", "Demo glossary", ""),
    ("validation", "marketmix-jdoe", "marketmix-monthly", "yes", "Personal copy of marketmix", "keyid:clone", "", "", "yes"),
]


def _csv(path: Path, header: list[str], rows: list[tuple]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)


def write_listing(path: Path) -> None:
    head = ["NAME", "ENV", "VERSION", "IMAGE", "STATE", "RPC", "BASE_URL"]
    rows = [(n, e, v, f"{n}:{v}", s, r, f"https://nxd.example.dev/dp/{n}-{e}") for n, e, v, s, r in LISTING]
    widths = [max(len(str(x[i])) for x in [head, *rows]) for i in range(len(head))]
    lines = [" " + "  ".join(str(c).ljust(w) for c, w in zip(row, widths)) for row in [head, *rows]]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_tree(path: Path) -> None:
    """The CLI export: description, count and created date padded into one cell, tree glyphs in the trailing cells."""
    rows = []
    for dom, parent, desc, count, created in TREE:
        jammed = f"{desc + '  ' if desc else ''}{count or '-':<15}{created or '-'}"
        glyph = "Γöö " if parent else ""
        rows.append((dom, parent, jammed, f"{glyph}{dom}   {count or '-'}", created.replace("-", "/") if created else ""))
    _csv(path, ["domain", "parent", "description", "data_products", "created"], rows)


def write_validation(path: Path) -> None:
    wb = Workbook()
    st = wb.active
    st.title = "Status"
    st["B2"] = "Data product status inventory"
    st["B3"] = "Cut: validation report (catalogue v9.9, 2026-10-02 08:00 UTC). Static completeness only."
    st["B5"] = "Estate is structurally built, not finish-spec complete."
    st.append([])
    st.append([None, "Item", "Value"])
    st.append([None, "Products in report", "13 snapshots"])
    st.append([])
    st.append([None, "keyid", "Score", "Product spec", "Metadata", "Runtime"])
    for keyid, score, comps in STATUS:
        st.append([None, keyid, score, *comps])
    inv = wb.create_sheet("Inventory")
    inv["B2"] = "Inventory by keyid"
    inv["B3"] = "keyid = spec.py data_product(name=...). Owner from .control('owner')."
    inv.append([])
    inv.append([None, "keyid", "Owner", "How declared", "Owner status", "Domain", "Version (Sep 30)", "Completeness", "business_name", "Git", "Notes"])
    for rec in INVENTORY:
        inv.append([None, *rec])
    src = wb.create_sheet("Sources")
    src["B2"] = "Sources and caveats"
    src.append([])
    src.append([None, "Topic", "Detail"])
    src.append([None, "keyid", "data_product(name=...) in spec.py"])
    src.append([None, "Owner rule", "Prefer the owner control"])
    path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(path)


def main() -> None:
    nd = OUT / "nextdata"
    write_listing(nd / "data-products.txt")
    names = list(dict.fromkeys(n for n, *_ in LISTING))
    _csv(nd / "nextdata_catalog.csv", ["name", "domain", "version", "state", "owner"], [
        (n, CATALOG_DOMAIN[n], "" if CATALOG_DOMAIN[n] == "NOT FOUND" else next(v for m, _e, v, *_ in LISTING if m == n),
         "" if CATALOG_DOMAIN[n] == "NOT FOUND" else next(s for m, _e, _v, s, _r in LISTING if m == n), CATALOG_OWNER.get(n, ""))
        for n in names
    ])
    write_tree(nd / "domains.csv")
    write_validation(OUT / "validation" / "validation-summary.xlsx")
    _csv(OUT / "products.csv", ["urn", "name", "domain", "dpo", "planned_next_gate_date", "planned_ga_date", "named_consumers", "input_products", "active_users_30d", "first_consumer_date", "dpo_comment", "reviewed_on", "cancelled_on"], PRODUCTS)
    _csv(OUT / "gate_events.csv", ["urn", "gate", "date_passed", "g5_path", "evidence_url"], GATES)
    _csv(OUT / "targets.csv", ["domain", "quarter", "certification_target"], TARGETS)
    _csv(OUT / "capacity.csv", ["domain", "week", "onboarded", "enrolled", "qualified"], CAPACITY)
    _csv(OUT / "crosswalk.csv", ["source", "name", "product", "include", "reason", "rule", "domain", "display_name", "reviewed"], CROSSWALK)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
