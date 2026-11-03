"""The showcase week: a made-up portfolio written to show everything the dashboard can do.

  python scripts/make_showcase.py generate   # -> tests/fixtures/inbox-showcase/
  python scripts/make_showcase.py build      # -> demo/index.html and tests/fixtures/showcase/2026-W47.json
                                             #    (the snapshot `npm run dev` previews; needs app/dist/template.html for the html)

Every value is written out below, so the same script always gives the same week. The as-of date is Friday
20 Nov 2026 (week 47), 55% into Q4, late enough for every health state to show: two domains off track, one
behind, three on track, two ahead, one without a target; Logistics has no products and stays hidden. All four areas
have products. HCP fell behind pace in October and caught up in November (visible week by week); Q3 started slow
and finished above target. Every lifecycle stage and every flag appears, with usage, consumers, a revision, a
retirement, a cancellation, NextData deployments, validation scores and a GitHub extract (the Delivery view). Weeks 45 and 46 are built and approved
first, so plan slips and "what changed" are real pipeline results.
"""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import sys
import tempfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pipeline.build import run_approve, run_build  # noqa: E402
from pipeline.github_fetch import write_tables  # noqa: E402
from pipeline.platform import CROSSWALK_COLUMNS, crosswalk_rows, load_platform, resolve  # noqa: E402
from pipeline.readers.register import SPECS  # noqa: E402
from pipeline.registry import load_platform_config  # noqa: E402

OUT = ROOT / "tests" / "fixtures" / "inbox-showcase"
SNAPSHOT = ROOT / "tests" / "fixtures" / "showcase" / "2026-W47.json"
DEMO = ROOT / "demo" / "index.html"
WEEK, AS_OF = "2026-W47", date(2026, 11, 20)
HISTORY = [("2026-W45", date(2026, 11, 6), 28), ("2026-W46", date(2026, 11, 13), 14)]  # week, as of, days earlier a slipping GA was planned
D = date.fromisoformat

# (domain, name, owner, kind, date, modifiers)
#   live <G4>        G1 to G4 passed; G4 on the date, G1 95 to 204 days before (varies by product)
#   revision <G5>    live since early 2026, a G5 scope change on the date
#   retired <G6>     live in 2025, retired on the date
#   test <GA>        G3 passed, GA (next gate G4) planned on the date
#   dev <GA>         G2 passed, GA planned on the date; next gate G3 30 days before it
#   design <GA>      G1 passed, GA planned on the date; next gate G2 90 days before it
#   idea             registered, no gate, never reviewed
#   cancelled <day>  G1 and G2 passed, cancelled on the date
# Modifiers: overdue=<planned next gate>, slipping, nodpo, stale=<reviewed on>, pending, unused, users=<n>,
#   nousers, consumer=<days after G4>, inputs=<slug;slug>, comment=<text>
PRODUCTS = [
    # Commercial · Patient: target 2, 1 live by now (on track)
    ("Patient", "Patient Journey 360", "Maya Okafor", "live", "2025-11-14", "users=142 inputs=patient-master"),
    ("Patient", "Patient Master", "Maya Okafor", "live", "2026-02-20", "users=96"),
    ("Patient", "Patient Program Enrollment", "Daniel Reyes", "live", "2026-05-12", "users=38 inputs=patient-master"),
    ("Patient", "Patient Treatment Adherence", "Daniel Reyes", "live", "2026-08-21", "users=27 inputs=patient-master;patient-program-enrollment"),
    ("Patient", "Patient Support Calls", "Daniel Reyes", "live", "2026-10-14", "users=9 inputs=patient-master"),
    ("Patient", "Patient Universe", "Maya Okafor", "test", "2026-12-10", "comment=Certification evidence pack in review."),
    ("Patient", "Patient Sentiment", "Daniel Reyes", "design", "2027-04-15", ""),
    ("Patient", "Caregiver Insights", "Maya Okafor", "idea", "", ""),
    # Commercial · HCP: target 2, nothing until W46, then 2 (ahead)
    ("HCP", "HCP HCO Master", "Priya Nair", "live", "2025-12-09", "users=181"),
    ("HCP", "Call Interaction", "Priya Nair", "live", "2026-03-18", "users=64 inputs=hcp-hco-master"),
    ("HCP", "Territory and Alignment", "Lukas Brandt", "live", "2026-06-04", "users=22 inputs=hcp-hco-master"),
    ("HCP", "HCP Targeting", "Lukas Brandt", "live", "2026-07-10", "users=45 inputs=hcp-hco-master;call-interaction"),
    ("HCP", "Media Interaction", "Priya Nair", "live", "2026-09-15", "users=18 inputs=hcp-hco-master"),
    ("HCP", "Survey Interaction", "Priya Nair", "live", "2026-11-10", "users=4 inputs=hcp-hco-master consumer=6"),
    ("HCP", "Omnichannel Engagement", "Lukas Brandt", "live", "2026-11-12", "users=3 inputs=call-interaction;media-interaction consumer=5"),
    ("HCP", "Rep Next Best Action", "Lukas Brandt", "test", "2026-12-05", ""),
    ("HCP", "KOL Network Graph", "Priya Nair", "dev", "2027-02-26", ""),
    ("HCP", "Speaker Programs", "", "design", "2027-05-20", "nodpo"),
    # Commercial · Market access: target 2, none live (off track)
    ("Market access", "Payer Master", "Tom Verbeke", "live", "2026-04-22", "users=51"),
    ("Market access", "Medical Claims", "Tom Verbeke", "live", "2026-08-28", "users=33 inputs=payer-master"),
    ("Market access", "Payer Performance", "Tom Verbeke", "test", "2026-10-30", "overdue=2026-10-20 inputs=payer-master;medical-claims comment=Waiting on the claims refresh before certification."),
    ("Market access", "Pharmacy Claims", "Sofia Lindqvist", "dev", "2026-12-18", "slipping"),
    ("Market access", "Payer Policy Context", "Sofia Lindqvist", "design", "2027-03-31", ""),
    ("Market access", "Pricing Scenario Model", "Tom Verbeke", "cancelled", "2026-06-15", ""),
    # Commercial · Channel partner: no target set
    ("Channel partner", "Specialty Pharmacy Feed", "Omar Haddad", "dev", "2027-02-12", ""),
    ("Channel partner", "Channel Inventory", "Omar Haddad", "design", "2027-05-28", ""),
    # Commercial · Revenue / vials: target 1, 0.6 due by now (on track)
    ("Revenue / vials", "Vials Sold", "Hannah Weiss", "live", "2026-01-28", "users=74"),
    ("Revenue / vials", "Net Revenue Bridge", "Hannah Weiss", "live", "2026-07-30", "users=0 unused"),
    ("Revenue / vials", "Legacy Sales Cube", "Hannah Weiss", "retired", "2026-09-04", ""),
    ("Revenue / vials", "Gross to Net", "Hannah Weiss", "live", "2026-11-02", "users=5 inputs=vials-sold"),
    ("Revenue / vials", "Rebate Accruals", "Hannah Weiss", "dev", "2026-12-15", "inputs=vials-sold"),
    ("Revenue / vials", "Demand Forecast", "Hannah Weiss", "idea", "", ""),
    # Commercial · Medical affairs: target 2, 1 live (on track)
    ("Medical affairs", "Medical Inquiries", "Ana Lane", "live", "2026-05-27", "users=29"),
    ("Medical affairs", "Field Medical Insights", "Ana Lane", "live", "2026-10-22", "users=11 inputs=medical-inquiries"),
    ("Medical affairs", "Scientific Publications", "Ana Lane", "test", "2026-12-01", ""),
    ("Medical affairs", "Advisory Boards", "Ana Lane", "dev", "2027-01-29", "stale=2026-10-23"),
    ("Medical affairs", "Medical Education Reach", "Ana Lane", "design", "2027-04-30", "pending"),
    # TechOps: target 5, 2 live (at risk)
    ("TechOps", "Batch Genealogy", "Elena Rossi", "revision", "2026-10-12", "users=58"),
    ("TechOps", "Deviation and CAPA", "Elena Rossi", "live", "2026-03-05", "users=40"),
    ("TechOps", "Supplier Quality Scorecard", "Jonas Pieters", "live", "2026-06-25", "users=21"),
    ("TechOps", "Equipment Calibration", "Jonas Pieters", "live", "2026-09-18", "users=14"),
    ("TechOps", "Cold Chain Monitoring", "Jonas Pieters", "live", "2026-09-24", "users=19 inputs=batch-genealogy"),
    ("TechOps", "Plant Capacity", "Elena Rossi", "live", "2026-10-08", "users=8"),
    ("TechOps", "Lot Release Cycle Time", "Elena Rossi", "live", "2026-11-04", "users=6 inputs=batch-genealogy consumer=8"),
    ("TechOps", "Serialization Events", "Jonas Pieters", "live", "2026-11-18", "users=2 consumer=1"),
    ("TechOps", "Warehouse Temperature", "Jonas Pieters", "test", "2026-12-12", ""),
    ("TechOps", "Inventory Positions", "Elena Rossi", "dev", "2026-12-20", "overdue=2026-10-25"),
    ("TechOps", "Maintenance Work Orders", "", "design", "2027-03-15", "nodpo"),
    # R&D: target 2, 2 live (ahead)
    ("R&D", "Clinical Trial Enrollment", "Farid Amin", "live", "2026-04-08", "users=55"),
    ("R&D", "Lab Results Harmonised", "Farid Amin", "live", "2026-09-09", "users=24"),
    ("R&D", "Site Performance", "Dana Voss", "live", "2026-10-20", "users=12 inputs=clinical-trial-enrollment"),
    ("R&D", "Biomarker Discovery Feed", "Dana Voss", "live", "2026-11-17", "nousers"),
    ("R&D", "Study Budget Forecast", "Dana Voss", "test", "2027-01-20", ""),
    ("R&D", "Pharmacovigilance Signals", "Farid Amin", "dev", "2027-03-05", ""),
    # G&A: target 3, 1 live (off track)
    ("G&A", "Headcount and Cost", "Chris Ngata", "live", "2026-05-20", "users=47"),
    ("G&A", "Finance Close Tracker", "Chris Ngata", "live", "2026-09-29", "users=16"),
    ("G&A", "Procurement Spend", "Chris Ngata", "live", "2026-10-27", "users=7"),
    ("G&A", "Travel and Expense", "Chris Ngata", "test", "2026-11-01", "overdue=2026-11-01"),
    ("G&A", "Legal Matters", "Chris Ngata", "design", "2027-02-26", "stale=2026-10-20"),
    ("G&A", "Workforce Planning", "Chris Ngata", "idea", "", ""),
]

# Quarterly certification targets per domain (Q1 below target, Q2 met, Q3 above, Q4 in play).
TARGETS = {
    "2026-Q1": {"Patient": 1, "HCP": 2, "Market access": 1, "Revenue / vials": 1, "TechOps": 1},
    "2026-Q2": {"Patient": 1, "HCP": 1, "Market access": 1, "Medical affairs": 1, "TechOps": 1, "R&D": 1, "G&A": 1},
    "2026-Q3": {"Patient": 1, "HCP": 2, "Market access": 1, "Revenue / vials": 1, "TechOps": 1, "R&D": 1, "G&A": 1},
    "2026-Q4": {"Patient": 2, "HCP": 2, "Market access": 3, "Revenue / vials": 1, "Medical affairs": 2, "TechOps": 7, "R&D": 2, "G&A": 4},
}
AREA = {"Patient": "com", "HCP": "com", "Market access": "com", "Channel partner": "com", "Revenue / vials": "com", "Medical affairs": "com", "TechOps": "tq", "R&D": "rd", "G&A": "ga"}
NEXTDATA_TEAM = {"com": "EDP/COMMERCIAL", "tq": "EDP/TECHOPS", "rd": "EDP/RND", "ga": "EDP/GNA"}
COMPONENTS = ["Product spec", "Metadata", "Semantic models", "Input ports", "Transform", "Output ports", "Data quality", "Runtime", "Hygiene"]


def slug(name: str) -> str:
    return "-".join("".join(ch.lower() if ch.isalnum() else " " for ch in name).split())


def _mods(text: str) -> dict[str, str]:
    out = {}
    for part in text.split():
        k, _, v = part.partition("=")
        out[k] = v
    if "comment=" in text:
        out["comment"] = text.split("comment=", 1)[1]
    return out


def generate() -> None:
    rows, gates, deps, val, cat, slipping, gh = [], [], [], [], [], [], []
    for i, (domain, name, owner, kind, when, mods_text) in enumerate(PRODUCTS):
        m = _mods(mods_text)
        key = slug(name)
        area = AREA[domain]
        urn = f"{'pending' if 'pending' in m else 'urn:dp:' + area}:{key}"
        rec = {"urn": urn, "name": name, "domain": domain, "dpo": owner, "reviewed_on": (AS_OF - timedelta(days=i % 6)).isoformat()}
        g: list[tuple[str, date, str]] = []
        live = kind in ("live", "revision", "retired")
        if live:
            g4 = D(when) if kind == "live" else D("2026-02-11") if kind == "revision" else D("2025-10-21")
            span = 95 + (i * 23) % 110  # G1 to G4 between 95 and 204 days, so domains differ
            g = [("G1", g4 - timedelta(days=span), ""), ("G2", g4 - timedelta(days=span * 2 // 3), ""), ("G3", g4 - timedelta(days=span // 4), ""), ("G4", g4, "")]
            rec["planned_ga_date"] = g4.isoformat()
            rec["named_consumers"] = 1 + i % 5
            if kind == "revision":
                g.append(("G5", D(when), "scope change"))
                rec["planned_next_gate_date"] = (AS_OF + timedelta(days=24)).isoformat()
            if kind == "retired":
                g.append(("G6", D(when), ""))
            if "users" in m:
                rec["active_users_30d"] = int(m["users"])
            if "unused" not in m and kind != "retired":
                rec["first_consumer_date"] = min(g4 + timedelta(days=int(m.get("consumer", 12 + i % 20))), AS_OF).isoformat()
        elif kind in ("test", "dev", "design"):
            ga = D(when)
            if kind == "test":
                g1 = AS_OF - timedelta(days=200 + 7 * (i % 5))
                g = [("G1", g1, ""), ("G2", g1 + timedelta(days=60), ""), ("G3", AS_OF - timedelta(days=40 + i % 30), "")]
                nxt = ga
            elif kind == "dev":
                g1 = AS_OF - timedelta(days=150 + 5 * (i % 6))
                g = [("G1", g1, ""), ("G2", AS_OF - timedelta(days=45 + i % 25), "")]
                nxt = ga - timedelta(days=30)
            else:
                g = [("G1", AS_OF - timedelta(days=30 + 4 * (i % 9)), "")]
                nxt = ga - timedelta(days=90)
            rec["planned_ga_date"] = ga.isoformat()
            rec["planned_next_gate_date"] = (D(m["overdue"]) if "overdue" in m else max(nxt, AS_OF + timedelta(days=5))).isoformat()
            rec["named_consumers"] = i % 3
        elif kind == "cancelled":
            g = [("G1", D("2026-01-12"), ""), ("G2", D("2026-03-02"), "")]
            rec["cancelled_on"] = when
        else:  # idea
            rec.pop("reviewed_on")
        if "stale" in m:
            rec["reviewed_on"] = m["stale"]
        if "inputs" in m:
            rec["input_products"] = ";".join(f"urn:dp:{area}:{s}" for s in m["inputs"].split(";"))
        if "comment" in m:
            rec["dpo_comment"] = m["comment"]
        if "slipping" in m:
            slipping.append(urn)
        rows.append(rec)
        for gate, d, path in g:
            gates.append({"urn": urn, "gate": gate, "date_passed": d.isoformat(), "g5_path": path, "evidence_url": f"https://evidence.example/{key}/{gate}"})

        # NextData: live products run in prod and dev; work in progress in dev; a few failing.
        version = f"1.{i % 4}.{(i * 3) % 10}"
        if live and kind != "retired":
            envs = [("prod", "Failed" if key == "cold-chain-monitoring" else "Started"), ("dev", "Started")]
        elif kind in ("test", "dev"):
            envs = [("dev", "Unreachable" if key == "inventory-positions" else "Started")]
        elif kind in ("retired", "cancelled"):
            envs = [("dev", "Failed")]
        else:
            envs = []
        for env, state in envs:
            deps.append((key, env, version if env == "prod" else f"{version}-dev", state))
        if envs:
            cat.append((key, NEXTDATA_TEAM[area], version, envs[0][1], owner or "Unassigned"))
        if kind not in ("idea", "cancelled"):
            gh.append((f"edp-{GH_TEAM[domain]}-dp-{key.replace('-', '_')}", key, kind, when if kind == "live" else "", i))
        if kind not in ("idea",):
            base = {"live": 0.84, "revision": 0.8, "retired": 0.62, "test": 0.76, "dev": 0.64, "design": 0.48, "cancelled": 0.4}[kind]
            score = round(min(0.97, base + ((i * 37) % 13 - 6) / 100), 4)
            comps = [round(max(0.0, min(1.0, score + ((i * 7 + c * 11) % 21 - 10) / 50)), 4) for c in range(len(COMPONENTS))]
            val.append({"keyid": key, "run_at": "2026-11-16", "score": score, "owner": "", "owner_status": "Drift" if i % 11 == 3 else "Declared", "p1_findings": 0 if score > 0.85 else 1 + i % 4, **dict(zip(COMPONENTS, comps))})

    targets = [{"domain": d, "quarter": q, "certification_target": t} for q, by in TARGETS.items() for d, t in by.items()]
    domains = sorted({r["domain"] for r in rows})
    capacity = [{"domain": d, "week": WEEK, "onboarded": 3 + 2 * n, "enrolled": 2 + n, "qualified": 1 + n // 2} for d in domains for n in [sum(1 for r in rows if r["domain"] == d)]]

    # Delete the old files but keep the folders: OneDrive can hold a folder open and refuse to remove it.
    for f in OUT.rglob("*") if OUT.exists() else []:
        if f.is_file():
            f.unlink()
    (OUT / "nextdata").mkdir(parents=True, exist_ok=True)
    (OUT / "validation").mkdir(exist_ok=True)
    _write(OUT / "products.csv", SPECS["products"].columns, rows)
    _write(OUT / "gate_events.csv", SPECS["gate_events"].columns, sorted(gates, key=lambda e: (e["urn"], e["date_passed"])))
    _write(OUT / "targets.csv", SPECS["targets"].columns, targets)
    _write(OUT / "capacity.csv", SPECS["capacity"].columns, capacity)
    head = ["NAME", "ENV", "VERSION", "IMAGE", "STATE", "RPC", "BASE_URL"]
    lines = [(n, e, v, f"{n}:{v}", s, "READY" if e == "prod" else "-", f"https://nxd.example.com/dp/{n}-{e}") for n, e, v, s in deps]
    widths = [max(len(str(x[c])) for x in [head, *lines]) for c in range(len(head))]
    (OUT / "nextdata" / "data-products.txt").write_text("\n".join(" " + "  ".join(str(c).ljust(w) for c, w in zip(r, widths)) for r in [head, *lines]) + "\n", encoding="utf-8")
    _write(OUT / "nextdata" / "nextdata_catalog.csv", ["name", "domain", "version", "state", "owner"], [dict(zip(["name", "domain", "version", "state", "owner"], c)) for c in cat])
    _write(OUT / "validation" / "validation.csv", ["keyid", "run_at", "score", "owner", "owner_status", "p1_findings", *COMPONENTS], val)
    xw = crosswalk_rows(resolve(load_platform(OUT), load_platform_config()))
    by_key = {slug(n): d for d, n, *_ in PRODUCTS}
    for r in xw:
        r["reviewed"] = "yes"
        if r["product"] in by_key:
            r["domain"] = by_key[r["product"]]
            r["display_name"] = next(n for _, n, *_ in PRODUCTS if slug(n) == r["product"])
    _write(OUT / "crosswalk.csv", CROSSWALK_COLUMNS, xw)
    gh += [(f"edp-{team}-dp-{name}", name, kind, "", 100 + j) for j, (team, name, kind) in enumerate(GH_EXTRA)]
    write_tables(_github(gh), OUT / "github")
    (OUT / "slipping.txt").write_text("\n".join(slipping) + "\n", encoding="utf-8")
    print(f"wrote {OUT}: {len(rows)} products, {len(gates)} gate events, {len(deps)} deployments, {len(gh)} GitHub repositories")


# GitHub: one repository per product that has a NextData deployment, edp-<team>-dp-<key_with_underscores>, so the
# name rules match it. The to-be state: live products ship to production every week or two, in-test products
# reach validation, products in development deploy to dev; failures are rare and mostly in dev. Cold Chain
# Monitoring (failing in NextData) also fails its last production deployments. Two repositories are not on the
# register yet and two are tooling, to show both filters of the Delivery view.
GH_TEAM = {"Patient": "patient", "HCP": "hcp", "Market access": "claims", "Channel partner": "ops", "Revenue / vials": "ops", "Medical affairs": "medaff", "TechOps": "techops", "R&D": "rnd", "G&A": "gna"}
GH_START = date(2026, 7, 27)
GH_EXTRA = [("rnd", "genomics_raw", "dev"), ("ops", "vendor_returns", "test"), ("gov", "data_control_framework", "live"), ("ops", "sandbox_demo", "dev")]


def _github(products: list[tuple[str, str, str, str, int]]) -> dict[str, list[dict]]:
    """products: (repo, key, kind, live-since date or '', index). Returns the five tables of `dp fetch-github`."""
    repos, deps, sts = [], [], []
    dep_id = 5000
    for repo, key, kind, since, i in products:
        repos.append({"repo_id": 9000 + i, "repo_name": repo, "full_name": f"example-org/{repo}", "html_url": f"https://github.example/example-org/{repo}", "archived": "False", "data_product_urn": "", "data_product_urn_source": ""})
        start, end = GH_START, AS_OF
        if kind == "retired":
            end = D("2026-09-04")
        elif kind == "cancelled":
            continue  # cancelled in June, nothing in the extract's window
        elif kind == "design":
            start = AS_OF - timedelta(days=21)
        every = {"live": 4 + i % 3, "revision": 3, "retired": 7, "test": 3 + i % 2, "dev": 2 + i % 2, "design": 6}[kind]
        fail_pct = 4 if kind in ("live", "revision", "retired") else 9 if kind == "test" else 14
        n, d = 0, start + timedelta(days=i % every)
        while d <= end:
            envs = ["iac-apply-d"]
            if kind in ("live", "revision", "retired", "test") and n % 2 == 1:
                envs.append("iac-apply-v")
            if kind in ("live", "revision", "retired") and n % 2 == 1 and (not since or d >= D(since) - timedelta(days=21)):
                envs.append("iac-apply-p")
            for k, env in enumerate(envs):
                dep_id += 1
                at = datetime(d.year, d.month, d.day, 9 + k, (i * 7) % 60, tzinfo=timezone.utc)
                bad = (i * 31 + n * 17 + k * 7) % 100 < (fail_pct if env != "iac-apply-p" else fail_pct // 2)
                if key == "cold-chain-monitoring" and env == "iac-apply-p" and d >= AS_OF - timedelta(days=14):
                    bad = True
                deps.append({"repo_name": repo, "deployment_id": dep_id, "environment": env, "production_environment": "False", "sha": f"{dep_id:x}", "created_at": at.isoformat().replace("+00:00", "Z")})
                sts.append({"repo_name": repo, "deployment_id": dep_id, "state": "in_progress", "created_at": (at + timedelta(minutes=1)).isoformat().replace("+00:00", "Z"), "source": "GraphQL"})
                if not (d == AS_OF and k == len(envs) - 1 and i % 5 == 0):  # a few of today's runs are still running
                    sts.append({"repo_name": repo, "deployment_id": dep_id, "state": "failure" if bad else "success", "created_at": (at + timedelta(minutes=6)).isoformat().replace("+00:00", "Z"), "source": "GraphQL"})
            n += 1
            d += timedelta(days=every)
    fetch = [{"fetched_at": f"{AS_OF.isoformat()}T06:00:00+00:00", "org": "example-org", "login": "showcase", "repos": len(repos)}]
    return {"repositories": repos, "deployments": deps, "deployment_statuses": sts, "issues": [], "fetch": fetch}


def _write(path: Path, cols: list[str], rows: list[dict]) -> None:
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def _week_inbox(src: Path, dst: Path, as_of: date, slip_days: int) -> None:
    """The inbox as it stood on an earlier week: later gates not yet passed, the slipping GAs still earlier."""
    shutil.copytree(src, dst)
    slipping = set((src / "slipping.txt").read_text(encoding="utf-8").split())
    with open(dst / "gate_events.csv", encoding="utf-8") as fh:
        events = [e for e in csv.DictReader(fh) if date.fromisoformat(e["date_passed"]) <= as_of]
    _write(dst / "gate_events.csv", SPECS["gate_events"].columns, events)
    with open(dst / "products.csv", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    for r in rows:
        if r["urn"] in slipping and r["planned_ga_date"]:
            r["planned_ga_date"] = (date.fromisoformat(r["planned_ga_date"]) - timedelta(days=slip_days)).isoformat()
        for col in ("reviewed_on", "first_consumer_date"):
            if r.get(col) and date.fromisoformat(r[col]) > as_of:
                r[col] = as_of.isoformat() if col == "reviewed_on" else ""
    _write(dst / "products.csv", SPECS["products"].columns, rows)


def build_weeks(base: Path, template_path: Path | None = None):
    """Build and approve weeks 45 and 46, then build week 47. Returns the week-47 BuildResult."""
    kw = {"template_path": template_path} if template_path else {}
    for week, as_of, slip in HISTORY:
        inbox = base / f"inbox-{week}"
        _week_inbox(OUT, inbox, as_of, slip)
        res = run_build(inbox, week, base / "out", base / "state", **kw)
        if not res.built:
            raise RuntimeError(f"{week}: " + "; ".join(i.message for i in res.check.blockers))
        run_approve(week, "Program lead", base / "out", base / "state", None, now=datetime.combine(as_of, datetime.min.time(), tzinfo=timezone.utc), **kw)
    res = run_build(OUT, WEEK, base / "out", base / "state", generated_at=datetime(2026, 11, 20, 8, 30, tzinfo=timezone.utc), **kw)
    if not res.built:
        raise RuntimeError("; ".join(i.message for i in res.check.blockers))
    return res


def build() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        res = build_weeks(Path(tmp))
        SNAPSHOT.parent.mkdir(parents=True, exist_ok=True)
        data = res.snapshot
        for s in data["sources"]:
            s["asOf"] = "<mtime>"
        SNAPSHOT.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"wrote {SNAPSHOT}")
        html = Path(tmp) / "out" / WEEK / "index.html"
        if html.exists():
            shutil.copy(html, DEMO)
            print(f"wrote {DEMO}")
        else:
            print("no index.html: run `npm run build` in app/ first", file=sys.stderr)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=["generate", "build"])
    generate() if ap.parse_args().command == "generate" else build()


if __name__ == "__main__":
    main()
