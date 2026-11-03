"""AT-PLAT: platform sources (NextData listing, catalog and domain tree; validation tool) and product identity.

Rules: docs/metric-definitions.md, section "Platform sources". Fixture: tests/fixtures/inbox-platform (invented).
"""

from __future__ import annotations

import csv
from datetime import date

import pytest

from conftest import PLATFORM_INBOX
from pipeline.platform import crosswalk_rows, load_platform, platform_checks, resolve
from pipeline.readers.nextdata import read_catalog, read_domain_tree, read_listing
from pipeline.readers.validation import read_validation

ND = PLATFORM_INBOX / "nextdata"


@pytest.fixture(scope="module")
def src():
    return load_platform(PLATFORM_INBOX)


@pytest.fixture(scope="module")
def res(src, platform_cfg):
    return resolve(src, platform_cfg)


def _rules(issues):
    return [i.rule for i in issues]


# --- Readers -------------------------------------------------------------------


def test_at_plat_01_listing_is_one_row_per_deployment():
    deps, issues = read_listing(ND / "data-products.txt")
    assert issues == []
    assert len(deps) == 29
    assert len({d.name for d in deps}) == 27  # dp-ops-crmsys (two versions) and dp-hcp-hcp-master (dev and prod) run twice
    states = {d.state for d in deps}
    assert states == {"Started", "Failed", "Unreachable"}  # UNREACHABLE normalised
    master = [d for d in deps if d.name == "dp-hcp-hcp-master"]
    assert {d.env for d in master} == {"dev", "prod"}
    assert any(d.rpc_ready for d in master)


def test_at_plat_02_catalog_normalises_domains_and_reads_not_found():
    entries, _ = read_catalog(ND / "nextdata_catalog.csv")
    by = {e.name: e for e in entries}
    assert by["rxfeed-monthly"].domain == "COMMERCIAL" and by["dp-ops-rxfeed"].domain == "EDP/OPS"
    assert by["lost-glossary"].found is False and by["lost-glossary"].domain is None
    assert by["dp-hcp-hcp-master"].owner == "HCP data team"


def test_at_plat_03_domain_tree_reads_the_jammed_cli_export():
    nodes, issues = read_domain_tree(ND / "domains.csv")
    assert issues == []
    by = {n.path: n for n in nodes}
    assert by["EDP"].products == 10 and by["EDP"].description == "Enterprise data platform"
    assert by["EDP/CLAIMS"].products is None and by["EDP/CLAIMS"].parent == "EDP"
    assert by["EDP/OPS"].created == date(2026, 7, 1)
    assert sum(n.products for n in nodes if not n.parent and n.products) == 29


def test_at_plat_04_validation_workbook_tables_under_title_blocks():
    run, issues = read_validation(PLATFORM_INBOX / "validation" / "validation-summary.xlsx")
    assert issues == []
    assert run.run_date == date(2026, 10, 2)
    by = {r.keyid: r for r in run.records}
    assert len(by) == 12, sorted(by)  # the Sources sheet's 'keyid' topic row is not a table
    assert by["crmsys"].owner_email == "a.lane@example.com" and by["crmsys"].owner_status == "Declared"
    assert by["hubservice"].owner_status == "Unconfirmed" and by["feed-lab-weekly"].owner_email is None
    assert by["hcp-master"].score == 0.8812
    # Two component rows for payer-directory; the inventory version decides which one applies.
    assert dict(by["payer-directory"].components)["Product spec"] == 0.9
    assert [c for c, _ in by["crmsys"].components] == ["Product spec", "Metadata", "Runtime"]


def test_at_plat_05_flat_validation_csv(tmp_path):
    p = tmp_path / "validation.csv"
    p.write_text("keyid,run_at,score,owner,owner_status,p1_findings,first_run_pass\nfoo,2026-10-01,73%,x@example.com,Declared,2,no\n", encoding="utf-8")
    run, issues = read_validation(p)
    assert issues == [] and run.run_date == date(2026, 10, 1)
    rec = run.records[0]
    assert (rec.score, rec.p1_findings) == (0.73, 2)


def test_at_plat_05b_audit_workbook_names_folders_not_keyids(tmp_path):
    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active
    ws.title = "DP summary"
    for r in [
        [None, "DP summary"],
        [None, "2 product(s) audited on 2026-10-14 20:38 UTC."],
        [],
        [None, "Data product", "Completeness score"],
        [None, "dp-ops-feed-1.0.0-dev (4)", 0.5811],
        [None, "hubservice-6.0.0", 0.9419],
        [None, "Use the component table below to locate weak areas."],
        [],
        [None, "Data product", "Product spec", "Metadata", "Traceability"],
        [None, "dp-ops-feed-1.0.0-dev (4)", 0.9045, 0.0625, None],
        [None, "hubservice-6.0.0", 0.9, 0.8829, None],
    ]:
        ws.append(r)
    tracker = wb.create_sheet("Field tracker")
    tracker.append([None, "Data product", "#", "Component", "Status", "Priority"])
    tracker.append([None, "hubservice-6.0.0", "A1", "Product spec", "Filled", None])
    p = tmp_path / "DP Validation Report -Oct 14.xlsx"
    wb.save(p)
    run, issues = read_validation(p)
    assert issues == [] and run.run_date == date(2026, 10, 14)
    by = {r.keyid: r for r in run.records}
    assert sorted(by) == ["dp-ops-feed", "hubservice"]
    assert (by["dp-ops-feed"].version, by["dp-ops-feed"].score) == ("1.0.0-dev", 0.5811)
    assert by["dp-ops-feed"].components == [("Product spec", 0.9045), ("Metadata", 0.0625)]
    assert by["hubservice"].version == "6.0.0"


# --- Identity ------------------------------------------------------------------


def test_at_plat_06_not_counted_with_a_reason(res):
    reasons = {p.key: p.reason for p in res.excluded}
    assert reasons == {
        "dp-ops-sample-template": "Template",
        "dp-ops-load-test": "Test",
        "dp-ops-dummy-widgets": "Sandbox or synthetic data",
        "dp-ops-alpha-dp": "Placeholder name (dp-<team>-<word>-dp)",
        "dp-gov-policy-framework": "Governance tooling, not a business data product",
        "lost-glossary": "Unreachable and not in the NextData catalog",
        "synthetic-feed": "Sandbox or synthetic data",
    }
    # demo-glossary is demo-only and never validated, but the crosswalk counts it on purpose.
    assert res.products["demo-glossary"].include


def test_at_plat_07_aliases_merge_names_of_one_product(res):
    assert res.products["dp-ops-crmsys"].names == ["dp-ops-crmsys", "crmsys"]
    assert res.products["dp-patient-journey-insights"].names == ["dp-patient-journey-insights", "journey-insights", "journey-insights-v2"]
    # payer-directory's repository says it belongs to the ops team: a different product from dp-claims-payer-directory.
    assert res.products["payer-directory"].include and res.products["dp-claims-payer-directory"].include
    assert res.lookup["payer-directory"] == "payer-directory"


def test_at_plat_08_validation_keyids_find_their_product(res):
    rule = {d.name: d.rule for d in res.decisions if d.source == "validation"}
    product = {d.name: d.product for d in res.decisions if d.source == "validation"}
    assert (product["crmsys"], rule["crmsys"]) == ("dp-ops-crmsys", "keyid:exact")
    assert (product["hcp-master"], rule["hcp-master"]) == ("dp-hcp-hcp-master", "keyid:team-prefix")
    assert (product["hubservice"], rule["hubservice"]) == ("hubservice-nxd", "keyid:nxd-suffix")
    assert (product["feed-lab-weekly"], rule["feed-lab-weekly"]) == ("lab-feed-weekly", "keyid:word-order")
    assert (product["marketmix"], rule["marketmix"]) == ("marketmix-monthly", "keyid:prefix")
    assert product["marketmix-jdoe"] == "marketmix-monthly"  # identical results to marketmix
    assert rule["planning-tool"] == "validation-only" and res.products["planning-tool"].runtime == "Not deployed"
    # The product carries the keyid that matched its best deployment.
    assert res.products["dp-patient-journey-insights"].validation.keyid == "journey-insights"


def test_at_plat_09_team_layer_rules(res, platform_cfg):
    team = {k: (platform_cfg.teams.get(p.team) if p.team else None, p.team_rule) for k, p in res.products.items()}
    assert team["dp-hcp-call-activity"] == ("HCP team", "name prefix")
    assert team["hubservice-nxd"] == ("Source systems", "repository name")
    assert team["rxfeed-quarterly"] == ("Source systems", "NextData domain")
    assert team["rxfeed-monthly"] == ("Source systems", "same family as other products")
    assert team["patient-registry"] == ("Patient team", "team word in the name")
    assert team["marketmix-monthly"] == (None, None)


def test_at_plat_09b_business_domain_precedence(res, platform_cfg):
    """Crosswalk, then registry/product-domains.yaml, then name rules, then the team, then Unknown."""
    dom = {k: (p.domain, p.domain_rule) for k, p in res.products.items()}
    assert dom["dp-ops-crmsys"] == ("HCP", "crosswalk")
    assert dom["rxfeed-monthly"] == ("Logistics", "crosswalk")
    assert dom["dp-claims-rx-claims"] == ("Market access", "name rule")  # "claims"
    assert dom["dp-claims-payer-directory"] == ("Market access", "name rule")
    assert dom["dp-hcp-call-activity"] == ("HCP", "name rule")  # "hcp"
    assert dom["patient-registry"] == ("Patient", "name rule")
    assert dom["lab-feed-weekly"] == ("Unknown", "default")
    # Rules: phrases beat words, and the first matching rule wins.
    from pipeline.platform import business_domain

    from copy import copy

    probe = copy(res.products["lab-feed-weekly"])  # a copy: res is shared by the module's tests
    for key, expected in [("dp-claims-channel-partner", "Channel partner"), ("dp-ops-buy-n-bill", "Revenue / vials"), ("kol-insights", "Medical affairs"),
                          ("iqvia-laad-weekly", "Market access"), ("veeva-crm", "HCP"), ("dp-patient-x", "Patient"), ("3pl-shipments", "Logistics")]:
        probe.key, probe.names, probe.keyids, probe.team = key, [], [], None
        assert business_domain(probe, platform_cfg)[0] == expected, key
    probe.key, probe.team = "unnamed-feed", "claims"  # no rule word: the team decides
    assert business_domain(probe, platform_cfg) == ("Market access", "team")


def test_at_plat_09c_product_domains_file_wins_over_rules(platform_cfg):
    from dataclasses import replace

    from pipeline.platform import business_domain

    cfg = replace(platform_cfg, product_domains={"lab-feed-weekly": "Logistics"})
    res = resolve(load_platform(PLATFORM_INBOX), cfg)
    assert (res.products["lab-feed-weekly"].domain, res.products["lab-feed-weekly"].domain_rule) == ("Logistics", "product-domains.yaml")
    # The committed map names every product of the real inventory and only domains that exist.
    from pipeline.registry import load_domains

    domains = load_domains()
    assert all(domains.resolve(d) for d in platform_cfg.product_domains.values())
    assert len(platform_cfg.product_domains) == 44


def test_at_plat_10_display_names(res):
    name = {k: p.display_name for k, p in res.products.items()}
    assert name["lab-feed-weekly"] == "Lab Feed Weekly"  # clean business name from the repository
    assert name["dp-hcp-hcp-master"] == "HCP master"  # lower-case business name -> made from the technical name
    assert name["dp-ops-crmsys"] == "CRM system"  # crosswalk
    assert name["payer-directory"] == "Payer directory (Source systems)"
    assert name["dp-claims-payer-directory"] == "Payer directory (Claims team)"


def test_at_plat_11_crosswalk_overrides_and_reports(src, res, platform_cfg):
    assert res.products["rxfeed-monthly"].domain == "Logistics"
    rules = _rules(platform_checks(src, res, platform_cfg))
    assert "XWALK_NEW" in rules and "XWALK_UNREVIEWED" in rules
    # Re-pointing a name to another product moves it, and its deployments, there.
    src.crosswalk[("nextdata", "rxfeed-monthly")].product = "dp-ops-rxfeed"
    try:
        moved = resolve(src, platform_cfg)
        assert "rxfeed-monthly" in moved.products["dp-ops-rxfeed"].names
        assert "rxfeed-monthly" not in moved.products
    finally:
        src.crosswalk[("nextdata", "rxfeed-monthly")].product = "rxfeed-monthly"


def test_at_plat_12_platform_checks(src, res, platform_cfg):
    issues = platform_checks(src, res, platform_cfg)
    by = {}
    for i in issues:
        by.setdefault(i.rule, []).append(i)
    assert [i.urn for i in by["ND_NOT_FOUND"]] == ["nxd:dp-ops-crmsys"]
    assert by["ND_NO_OWNER"][0].message == "NextData records no owner for 16 of 17 products"
    claims = next(i for i in by["ND_DOMAIN"] if "Claims" in i.message)
    assert claims.message == "2 Claims team products are registered under COMMERCIAL; the team domain EDP/CLAIMS holds 0"
    assert {i.urn for i in by["ND_DUPLICATE"]} == {"nxd:dp-ops-crmsys", "nxd:dp-patient-journey-insights"}
    assert "ND_RECONCILE" not in by  # tree counts match the listing


def test_at_plat_13_reconciliation_and_missing_crosswalk(platform_copy, platform_cfg):
    (platform_copy / "crosswalk.csv").unlink()
    tree = platform_copy / "nextdata" / "domains.csv"
    tree.write_text(tree.read_text(encoding="utf-8").replace("COMMERCIAL,,17 ", "COMMERCIAL,,18 "), encoding="utf-8")
    s = load_platform(platform_copy)
    rules = _rules(platform_checks(s, resolve(s, platform_cfg), platform_cfg))
    assert "XWALK_MISSING" in rules and "ND_RECONCILE" in rules


def test_at_plat_14_crosswalk_round_trip(platform_copy, platform_cfg):
    """A crosswalk written from the rules reproduces the same products."""
    (platform_copy / "crosswalk.csv").unlink()
    s = load_platform(platform_copy)
    before = resolve(s, platform_cfg)
    rows = crosswalk_rows(before)
    with open(platform_copy / "crosswalk.csv", "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    after = resolve(load_platform(platform_copy), platform_cfg)
    assert {k: (p.include, p.names, p.keyids, p.domain, p.display_name) for k, p in before.products.items()} == {
        k: (p.include, p.names, p.keyids, p.domain, p.display_name) for k, p in after.products.items()
    }


def test_at_plat_15_seeded_register_passes_dp_check(platform_copy, tmp_path, regs):
    from pipeline.build import run_check
    from scripts.seed_register import seed_rows

    rows, prov, warnings = seed_rows(platform_copy)
    s = load_platform(platform_copy)
    from pipeline.registry import load_platform_config

    counted = resolve(s, load_platform_config()).included
    assert len(rows) == len(counted) == 18 and warnings == []
    assert all(r["urn"].startswith("nxd:") for r in rows)
    by = {r["urn"]: r for r in rows}
    assert by["nxd:dp-ops-crmsys"]["dpo"] == "a.lane"  # Declared owner, as the user name only
    assert "dpo" not in by["nxd:hubservice-nxd"]  # Unconfirmed owner is not seeded
    assert by["nxd:rxfeed-monthly"]["domain"] == "Logistics"
    assert ("nxd:dp-ops-crmsys", "dpo", "a.lane", "repository owner (Declared); replace with the person's name") in prov

    # Written as CSVs next to the platform files, the seeded register builds with no blocker.
    inbox = tmp_path / "seeded"
    import shutil

    shutil.copytree(platform_copy / "nextdata", inbox / "nextdata")
    from pipeline.readers.register import SPECS

    cols = SPECS["products"].columns
    with open(inbox / "products.csv", "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows({c: r.get(c, "") for c in cols} for r in rows)
    for spec in ("gate_events", "targets", "capacity"):
        with open(inbox / SPECS[spec].csv, "w", encoding="utf-8", newline="") as fh:
            csv.writer(fh).writerow(SPECS[spec].columns)
    check, ctx = run_check(inbox, date(2026, 10, 9), regs)
    assert check.blockers == [], [i.message for i in check.blockers]
    assert len(ctx.products) == 18
