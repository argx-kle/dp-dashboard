"""The named demo: the real data product names and domains, with made-up values in every other field.

  python scripts/make_named_demo.py generate --inbox inbox   # real names from the inbox's platform files -> tests/fixtures/inbox-named-demo/
  python scripts/make_named_demo.py build                    # -> demo/index-named.html (needs app/dist/template.html)

`generate` reads only the identity of each counted product (key, other names, display name, domain, team) from
the real NextData and validation files. Everything else (gate dates, plans, owners, usage, consumers, comments,
targets, capacity, deployments and their states, validation scores) is invented with a fixed seed, so the same
names always give the same demo. The mix is chosen to show every status, signal and flag.

`build` builds weeks 39 and 40 first and approves them, so plan slips, baselines and "what changed" are real
results of the pipeline, then builds week 41.
"""

from __future__ import annotations

import argparse
import csv
import random
import shutil
import sys
import tempfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pipeline.build import run_approve, run_build  # noqa: E402
from pipeline.platform import CROSSWALK_COLUMNS, crosswalk_rows, load_platform, resolve  # noqa: E402
from pipeline.readers.register import SPECS  # noqa: E402
from pipeline.registry import load_platform_config  # noqa: E402

OUT = ROOT / "tests" / "fixtures" / "inbox-named-demo"
DEMO = ROOT / "demo" / "index-named.html"
WEEK, AS_OF = "2026-W41", date(2026, 10, 9)
HISTORY = [("2026-W39", date(2026, 9, 25), 28), ("2026-W40", date(2026, 10, 2), 14)]  # week, as of, days earlier the slipping GA was planned
SEED = 41

OWNERS = ["Ana Lane", "Chris Ngata", "Dana Voss", "Farid Amin", "Elena Rossi", "Jonas Pieters", "Maya Okafor", "Lukas Brandt", "Priya Nair", "Tom Verbeke", "Sofia Lindqvist", "Hannah Weiss", "Omar Haddad", "Daniel Reyes"]
COMMENTS = [
    "Waiting on the upstream refresh before the next gate.",
    "Contract reviewed with consumers; build on track.",
    "Certification evidence pack in review.",
    "Two consuming teams onboarded this month.",
    "Scope trimmed to the first two use cases.",
    "Metadata and glossary links being completed.",
]
COMPONENTS = ["Product spec", "Metadata", "Semantic models", "Input ports", "Transform", "Output ports", "Data quality", "Runtime", "Hygiene"]

# Profiles, from most to least mature. Counts are for 44 products and scale with the product count.
PROFILES = [("retired", 1), ("live", 13), ("certified_qtd", 3), ("revision", 2), ("cert", 6), ("build", 8), ("design", 8), ("cancelled", 1), ("inception", 2)]


def _d(rng: random.Random, start: date, lo: int, hi: int) -> date:
    return start + timedelta(days=rng.randint(lo, hi))


def _profiles(n: int) -> list[str]:
    total = sum(c for _, c in PROFILES)
    out = []
    for name, c in PROFILES:
        out += [name] * max(1 if c else 0, round(c * n / total))
    while len(out) > n:
        out.remove("design")
    while len(out) < n:
        out.insert(len(out) - 2, "design")
    return out


def generate(inbox: Path) -> None:
    cfg = load_platform_config()
    res = resolve(load_platform(inbox), cfg)
    real = sorted(res.included, key=lambda p: p.key)
    rng = random.Random(SEED)

    source = {p.key for p in real if p.team not in ("hcp", "patient", "claims")}
    # Source systems tend to be further along: sort by a seeded maturity, then hand out profiles in order.
    order = sorted(real, key=lambda p: rng.random() - (0.45 if p.key in source else 0))
    profile = dict(zip((p.key for p in order), _profiles(len(order))))

    rows, gates, deps, val, cat = [], [], [], [], []
    plan_ga: dict[str, date] = {}
    for p in real:
        prof = profile[p.key]
        urn = f"nxd:{p.key}"
        g: list[tuple[str, date, str]] = []
        rec = {"urn": urn, "name": p.display_name, "domain": p.domain, "dpo": rng.choice(OWNERS), "reviewed_on": (AS_OF - timedelta(days=rng.randint(0, 9))).isoformat()}
        if prof in ("live", "retired", "certified_qtd", "revision"):
            g1 = _d(rng, date(2025, 10, 1), 0, 150)
            g2 = _d(rng, g1, 30, 60)
            g3 = _d(rng, g2, 40, 75)
            g4 = _d(rng, g3, 25, 60)
            if prof == "certified_qtd":
                g4 = date(2026, 10, rng.randint(1, 8))
                g3 = min(g3, g4 - timedelta(days=30))
                g2, g1 = min(g2, g3 - timedelta(days=40)), min(g1, g3 - timedelta(days=100))
            g4 = min(g4, date(2026, 9, 28)) if prof != "certified_qtd" else g4
            g = [("G1", g1, ""), ("G2", g2, ""), ("G3", g3, ""), ("G4", g4, "")]
            rec["planned_ga_date"] = g4.isoformat()
            rec["named_consumers"] = rng.randint(1, 6)
            rec["active_users_30d"] = rng.randint(6, 140)
            rec["first_consumer_date"] = min(_d(rng, g4, 3, 25), AS_OF).isoformat()
            if prof == "revision":
                g.append(("G5", min(_d(rng, g4, 20, 40), AS_OF - timedelta(days=3)), "scope change"))
                rec["planned_next_gate_date"] = _d(rng, AS_OF, 15, 60).isoformat()
            if prof == "retired":
                g.append(("G6", min(_d(rng, g4, 40, 90), date(2026, 9, 20)), ""))
                rec.pop("active_users_30d")
        elif prof in ("cert", "build", "design"):
            g1 = _d(rng, date(2026, 1, 10), 0, 200)
            g = [("G1", g1, "")]
            if prof in ("cert", "build"):
                g.append(("G2", min(_d(rng, g1, 30, 60), AS_OF - timedelta(days=20)), ""))
            if prof == "cert":
                g.append(("G3", min(_d(rng, g[-1][1], 30, 60), AS_OF - timedelta(days=5)), ""))
            ga = _d(rng, AS_OF, 10, 120)
            rec["planned_ga_date"] = ga.isoformat()
            rec["planned_next_gate_date"] = (ga if prof == "cert" else _d(rng, AS_OF, 7, 60)).isoformat()
            rec["named_consumers"] = rng.randint(0, 3)
        elif prof == "cancelled":
            g1 = date(2026, 2, 2) + timedelta(days=rng.randint(0, 20))
            g = [("G1", g1, ""), ("G2", g1 + timedelta(days=45), "")]
            rec["cancelled_on"] = (g1 + timedelta(days=120)).isoformat()
        else:  # inception: registered, nothing yet, never reviewed
            rec.pop("reviewed_on")
        plan_ga[urn] = date.fromisoformat(rec["planned_ga_date"]) if rec.get("planned_ga_date") else None
        for gate, when, path in sorted(g, key=lambda x: x[1]):
            gates.append({"urn": urn, "gate": gate, "date_passed": when.isoformat(), "g5_path": path, "evidence_url": f"https://evidence.example/{p.key}/{gate}"})
        rec["_profile"] = prof
        rows.append(rec)

        # NextData: deployments under the product's real names, made-up versions and states.
        live = prof in ("live", "certified_qtd", "revision")
        version = f"1.{rng.randint(0, 3)}.{rng.randint(0, 9)}"
        envs = [("prod", "Started"), ("dev", "Started")] if live else [("dev", rng.choice(["Started"] * 4 + ["Failed"]))]
        if prof in ("cancelled", "retired"):
            envs = [("dev", "Failed")]
        if prof == "inception":
            envs = [("dev", "Unreachable")] if rng.random() < 0.5 else []
        for env, state in envs:
            deps.append((p.key, env, version if env == "prod" else f"{version}-dev", state))
        for alias in p.names[1:]:
            deps.append((alias, "dev", "1.0.0-dev", "Failed"))
        team_domain = f"EDP/{p.team.upper()}" if p.team in ("ops", "hcp", "patient", "claims") else "COMMERCIAL"
        cat.append((p.key, team_domain, version, envs[0][1] if envs else "", rec["dpo"]))

        maturity = {"live": 0.82, "certified_qtd": 0.86, "revision": 0.8, "retired": 0.7, "cert": 0.76, "build": 0.66, "design": 0.52, "cancelled": 0.45, "inception": 0.35}[prof]
        score = max(0.2, min(0.97, rng.gauss(maturity, 0.06)))
        comps = [round(max(0.0, min(1.0, rng.gauss(score, 0.18))), 4) for _ in COMPONENTS]
        val.append({"keyid": p.key, "run_at": "2026-10-05", "score": round(score, 4), "owner": "", "owner_status": rng.choice(["Declared"] * 6 + ["Drift", "Missing"]),
                    "p1_findings": 0 if score > 0.85 else rng.randint(1, 4), **dict(zip(COMPONENTS, comps))})

    # Flags: overdue, slipping, unused, no DPO, not updated, pending URN, each on chosen products.
    by = {r["urn"]: r for r in rows}

    def pick(prof: str, k: int, exclude: set[str]) -> list[str]:
        pool = [r["urn"] for r in rows if r["_profile"] == prof and r["urn"] not in exclude]
        return rng.sample(pool, min(k, len(pool)))

    used: set[str] = set()
    for urn in pick("cert", 1, used) + pick("build", 1, used):
        by[urn]["planned_next_gate_date"] = (AS_OF - timedelta(days=rng.randint(20, 35))).isoformat()  # OVERDUE
        used.add(urn)
    slipping = pick("build", 1, used) + pick("cert", 1, used)
    for urn in slipping:
        by[urn]["planned_ga_date"] = (AS_OF + timedelta(days=60)).isoformat()
        used.add(urn)
    for urn in pick("design", 2, used):
        by[urn].pop("dpo")  # NO_DPO
        used.add(urn)
    for urn in pick("live", 1, used) + pick("build", 1, used) + pick("design", 1, used):
        by[urn]["reviewed_on"] = (AS_OF - timedelta(days=rng.randint(18, 40))).isoformat()  # NOT_UPDATED
        used.add(urn)
    pending = pick("design", 1, used)

    # Inputs: built products (team-prefixed) declare one or two source systems of their domain as inputs.
    sources_by_domain: dict[str, list[str]] = {}
    for r in rows:
        if r["urn"][4:] in source and r["_profile"] in ("live", "certified_qtd", "revision"):
            sources_by_domain.setdefault(r["domain"], []).append(r["urn"])
    unused = [u for u in pick("live", 4, used)][:2]
    for r in rows:
        if r["urn"][4:] in source or r["_profile"] in ("inception", "cancelled"):
            continue
        pool = [u for u in sources_by_domain.get(r["domain"], []) if u not in unused] or [u for v in sources_by_domain.values() for u in v if u not in unused]
        if pool:
            r["input_products"] = ";".join(rng.sample(pool, min(len(pool), rng.randint(1, 2))))
    for urn in unused:
        old = by[urn]
        old["active_users_30d"] = 0  # UNUSED: live 60+ days, no users, no consuming product
        g4 = next(date.fromisoformat(e["date_passed"]) for e in gates if e["urn"] == urn and e["gate"] == "G4")
        if (AS_OF - g4).days < 60:
            for e in gates:
                if e["urn"] == urn:
                    e["date_passed"] = (date.fromisoformat(e["date_passed"]) - timedelta(days=60)).isoformat()
            old["planned_ga_date"] = (date.fromisoformat(old["planned_ga_date"]) - timedelta(days=60)).isoformat()
            old["first_consumer_date"] = (date.fromisoformat(old["first_consumer_date"]) - timedelta(days=60)).isoformat()
    for r in rng.sample(rows, 7):
        if r["_profile"] not in ("inception", "cancelled"):
            r["dpo_comment"] = rng.choice(COMMENTS)
    for urn in pending:
        new = "pending:" + urn[4:]
        by[urn]["urn"] = new
        for e in gates:
            if e["urn"] == urn:
                e["urn"] = new
        for r in rows:
            if r.get("input_products"):
                r["input_products"] = r["input_products"].replace(urn, new)

    # Targets: past quarters near what was certified; this quarter set so that two domains fall behind.
    domains = sorted({r["domain"] for r in rows} - {"Unknown"})  # no target for products without a domain
    first_g4: dict[str, date] = {}
    for e in gates:
        if e["gate"] == "G4":
            first_g4.setdefault(e["urn"], date.fromisoformat(e["date_passed"]))
    dom_of = {r["urn"]: r["domain"] for r in rows}
    targets = []
    behind = set(rng.sample(domains, 2))
    for q, (start, end) in enumerate([(date(2026, 1, 1), date(2026, 3, 31)), (date(2026, 4, 1), date(2026, 6, 30)), (date(2026, 7, 1), date(2026, 9, 30)), (date(2026, 10, 1), date(2026, 12, 31))], start=1):
        for dom in domains:
            done = sum(1 for u, d in first_g4.items() if dom_of[u] == dom and start <= d <= end)
            if q < 4:
                t = max(0, done + rng.choice([-1, 0, 0, 1]))
            else:
                forecast = sum(1 for r in rows if r["domain"] == dom and _forecast(r, end))
                t = done + forecast + (1 if dom in behind else 0)
            targets.append({"domain": dom, "quarter": f"2026-Q{q}", "certification_target": t})
    capacity = [{"domain": dom, "week": WEEK, "onboarded": 3 + 2 * n, "enrolled": 2 + n, "qualified": 1 + n // 2} for dom in domains for n in [sum(1 for r in rows if r["domain"] == dom)]]

    # Write the inbox.
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "nextdata").mkdir(parents=True)
    (OUT / "validation").mkdir()
    _write(OUT / "products.csv", SPECS["products"].columns, rows)
    _write(OUT / "gate_events.csv", SPECS["gate_events"].columns, sorted(gates, key=lambda e: (e["urn"], e["date_passed"])))
    _write(OUT / "targets.csv", SPECS["targets"].columns, targets)
    _write(OUT / "capacity.csv", SPECS["capacity"].columns, capacity)
    head = ["NAME", "ENV", "VERSION", "IMAGE", "STATE", "RPC", "BASE_URL"]
    lines = [(n, e, v, f"{n}:{v}", s, "READY" if e == "prod" else "-", f"https://nxd.aks.argenx-dev.com/dp/{n}-{e}") for n, e, v, s in deps]
    widths = [max(len(str(x[i])) for x in [head, *lines]) for i in range(len(head))]
    (OUT / "nextdata" / "data-products.txt").write_text("\n".join(" " + "  ".join(str(c).ljust(w) for c, w in zip(row, widths)) for row in [head, *lines]) + "\n", encoding="utf-8")
    _write(OUT / "nextdata" / "nextdata_catalog.csv", ["name", "domain", "version", "state", "owner"], [dict(zip(["name", "domain", "version", "state", "owner"], c)) for c in cat])
    _write(OUT / "validation" / "validation.csv", ["keyid", "run_at", "score", "owner", "owner_status", "p1_findings", *COMPONENTS], val)
    xw = crosswalk_rows(resolve(load_platform(OUT), cfg))
    for r in xw:
        r["reviewed"] = "yes"
    _write(OUT / "crosswalk.csv", CROSSWALK_COLUMNS, xw)
    (OUT / "slipping.txt").write_text("\n".join(by_urn for by_urn in slipping) + "\n", encoding="utf-8")
    print(f"wrote {OUT}: {len(rows)} products, {len(gates)} gate events, {len(deps)} deployments")


def _forecast(r: dict, quarter_end: date) -> bool:
    """The pipeline's G4 forecast rule (pipeline/metrics/headline.py): not yet certified, GA planned between the
    as-of date and the quarter end, next gate not overdue."""
    if r["_profile"] not in ("cert", "build", "design") or not r.get("planned_ga_date") or r.get("cancelled_on"):
        return False
    ga = date.fromisoformat(r["planned_ga_date"])
    nxt = r.get("planned_next_gate_date")
    overdue = bool(nxt) and AS_OF > date.fromisoformat(nxt) + timedelta(days=14)
    return AS_OF <= ga <= quarter_end and not overdue


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
        if r.get("reviewed_on") and date.fromisoformat(r["reviewed_on"]) > as_of:
            r["reviewed_on"] = as_of.isoformat()
    _write(dst / "products.csv", SPECS["products"].columns, rows)


def build_weeks(base: Path, template_path: Path | None = None):
    """Build and approve the history weeks, then build week 41. Returns the week-41 BuildResult."""
    kw = {"template_path": template_path} if template_path else {}
    for week, as_of, slip in HISTORY:
        inbox = base / f"inbox-{week}"
        _week_inbox(OUT, inbox, as_of, slip)
        res = run_build(inbox, week, base / "out", base / "state", **kw)
        if not res.built:
            raise RuntimeError(f"{week}: " + "; ".join(i.message for i in res.check.blockers))
        run_approve(week, "Program lead", base / "out", base / "state", None, now=datetime.combine(as_of, datetime.min.time(), tzinfo=timezone.utc), **kw)
    res = run_build(OUT, WEEK, base / "out", base / "state", **kw)
    if not res.built:
        raise RuntimeError("; ".join(i.message for i in res.check.blockers))
    return res


def build() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        build_weeks(Path(tmp))
        DEMO.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(Path(tmp) / "out" / WEEK / "index.html", DEMO)
    print(f"wrote {DEMO}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=["generate", "build"])
    ap.add_argument("--inbox", type=Path, default=ROOT / "inbox")
    args = ap.parse_args()
    generate(args.inbox) if args.command == "generate" else build()


if __name__ == "__main__":
    main()
