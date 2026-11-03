"""AT-E2E: the built one-file dashboard, opened from file:// in Chromium (Playwright).

Needs app/dist/template.html (run `npm run build` in app/). Skipped when it is missing.
Where Playwright's Chromium download is blocked, PLAYWRIGHT_CHANNEL=msedge runs the installed Edge instead.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

import pytest

from conftest import GOLDEN_INBOX, PLATFORM_INBOX, WEEK
from pipeline import ROOT, TEMPLATE_PATH
from pipeline.build import run_approve, run_build

AXE = ROOT / "app" / "node_modules" / "axe-core" / "axe.min.js"
SIZE_BUDGET = 640 * 1024  # ADR-001, raised from 600 KB on 2026-10-07

pytestmark = pytest.mark.skipif(not TEMPLATE_PATH.exists(), reason="app/dist/template.html not built")


@pytest.fixture(scope="module")
def pack(tmp_path_factory, regs) -> Path:
    base = tmp_path_factory.mktemp("pack")
    res = run_build(GOLDEN_INBOX, WEEK, base / "out", base / "state", regs=regs)
    assert res.built
    return base


@pytest.fixture(scope="module")
def browser():
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        b = p.chromium.launch(channel=os.environ.get("PLAYWRIGHT_CHANNEL") or None)
        yield b
        b.close()


@pytest.fixture
def page(browser, pack):
    ctx = browser.new_context(viewport={"width": 1400, "height": 900}, reduced_motion="reduce")
    pg = ctx.new_page()
    errors: list[str] = []
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    pg.goto((pack / "out" / WEEK / "index.html").as_uri())
    pg.wait_for_selector("[data-testid=exec-view]")
    yield pg
    assert errors == [], errors
    ctx.close()


def _count(page, selector: str) -> int:
    return int(page.get_attribute(selector, "data-count"))


def test_at_e2e_01_every_tile_links_to_a_list_of_the_same_size(page):
    links = page.query_selector_all("[data-testid^=tile-link-]")
    assert len(links) == 5
    for i in range(len(links)):
        link = page.query_selector_all("[data-testid^=tile-link-]")[i]
        expected = int(link.get_attribute("data-count"))
        link.click()
        page.wait_for_selector("[data-testid=products-view]")
        assert _count(page, "[data-testid=products-count]") == expected
        page.go_back()
        page.wait_for_selector("[data-testid=exec-view]")


def test_at_e2e_02_domain_health_numbers_match_their_lists(page):
    page.click("[data-testid=domains-view-table]")
    ids = [el.get_attribute("data-testid") for el in page.query_selector_all("[data-testid^=dh-]")]
    assert len(ids) >= 16
    for tid in ids:
        page.click("[data-testid=domains-view-table]")
        expected = _count(page, f"[data-testid={tid}]")
        page.click(f"[data-testid={tid}]")
        page.wait_for_selector("[data-testid=products-view]")
        assert _count(page, "[data-testid=products-count]") == expected, tid
        page.go_back()
        page.wait_for_selector("[data-testid=exec-view]")
    page.click("[data-testid=domains-view-table]")
    stages = sum(_count(page, f"[data-testid={tid}]") for tid in ids if tid.startswith("dh-stage-"))
    assert stages == 25, "every product counted under exactly one stage"


def test_at_e2e_09_cluster_map_draws_every_product_and_previews_on_hover(page):
    bubbles = page.query_selector_all("[data-testid=cluster-map] [data-testid=cluster-bubble]")
    assert len(bubbles) == 25
    page.hover("[data-testid=cluster-map] [data-urn='urn:dp:com:market-access-insights']")
    preview = page.wait_for_selector("[data-testid=product-preview]")
    text = preview.inner_text()
    assert "Market Access Insights" in text and "In testing" in text and "Overdue" in text
    assert "G4 Certify" in text, "the hover card names the next gate"
    assert "Off track" not in text, "health is a domain verdict, never a product colour"
    # The attention list lights the same product.
    assert page.get_attribute("[data-testid=needs-attention-item] >> nth=0", "href").endswith("market-access-insights")


def test_at_e2e_10_legend_counts_match_their_lists(page):
    total = 0
    for stage in ["Ideation", "In design", "In development", "In testing", "Live", "Failed / retired"]:
        sel = f'[data-testid="legend-count-{stage}"]'
        expected = _count(page, sel)
        total += expected
        page.click(sel)
        page.wait_for_selector("[data-testid=products-view]")
        assert _count(page, "[data-testid=products-count]") == expected, stage
        page.go_back()
        page.wait_for_selector("[data-testid=exec-view]")
    assert total == 25
    attention = _count(page, "[data-testid=legend-count-attention]")
    assert attention == len(page.query_selector_all("[data-testid=attention-dot]")) == 7


def test_at_e2e_03_hash_routes_work_from_file(page):
    page.goto(page.url.split("#")[0] + "#/products")
    page.wait_for_selector("[data-testid=products-view]")
    assert _count(page, "[data-testid=products-count]") == 25
    page.goto(page.url.split("#")[0] + "#/domain/hcp")
    page.wait_for_selector("[data-testid=domain-view]")
    page.goto(page.url.split("#")[0] + "#/products/urn:dp:com:patient-services-ops")
    page.wait_for_selector("[data-testid=product-view]")
    assert "iteration 2" in page.inner_text("[data-testid=product-view]")
    page.goto(page.url.split("#")[0] + "#/definitions")
    page.wait_for_selector("[data-testid=definitions-view]")
    page.goto(page.url.split("#")[0] + "#/nowhere")
    assert "Nothing at" in page.inner_text("main")


def test_at_e2e_04_needs_attention_lists_every_flagged_product(page):
    assert page.inner_text("[data-testid=needs-attention-count]").startswith("7 ")
    page.click("[data-testid=needs-attention-item] >> nth=0")
    page.wait_for_selector("[data-testid=product-view]")
    assert "Overdue" in page.inner_text("[data-testid=product-view]")


def test_at_e2e_05_sign_off_state_lives_in_the_footer(page, pack, browser):
    """Product-owner decision 2026-10-07: no draft or sign-off chip in the header."""
    assert page.query_selector("[data-testid=draft-watermark]") is None
    assert page.query_selector("[data-testid=draft-chip]") is None
    assert "Draft, not yet signed off" in page.inner_text("footer")
    assert "Data Product Delivery" in page.inner_text("header")
    run_approve(WEEK, "Program lead", pack / "out", pack / "state", None)
    ctx = browser.new_context()
    pg = ctx.new_page()
    pg.goto((pack / "out" / WEEK / "index.html").as_uri())
    pg.wait_for_selector("[data-testid=exec-view]")
    assert pg.query_selector("[data-testid=signed-off-chip]") is None
    assert "Signed off by Program lead" in pg.inner_text("footer")
    ctx.close()


def test_at_e2e_06_opens_in_under_two_seconds(browser, pack):
    ctx = browser.new_context()
    pg = ctx.new_page()
    t0 = time.perf_counter()
    pg.goto((pack / "out" / WEEK / "index.html").as_uri())
    pg.wait_for_selector("[data-testid=tile-link-certified_qtd-org]")
    elapsed = time.perf_counter() - t0
    ctx.close()
    assert elapsed < 2.0, f"opened in {elapsed:.2f}s"


def test_at_e2e_07_template_within_size_budget():
    size = TEMPLATE_PATH.stat().st_size
    assert size <= SIZE_BUDGET, f"template is {size / 1024:.0f} KB, budget {SIZE_BUDGET / 1024:.0f} KB"


@pytest.mark.skipif(not AXE.exists(), reason="axe-core not installed in app/node_modules")
@pytest.mark.parametrize("route", ["#/", "#/products", "#/products?metric=cycle_time_g1_g4&scope=org", "#/domain/hcp", "#/products/urn:dp:com:brand-health-tracker", "#/definitions", "#/products?stage=In+testing", "#/?q=2026-Q3"])
def test_at_e2e_08_axe_has_no_serious_violations(page, route):
    page.goto(page.url.split("#")[0] + route)
    page.wait_for_selector("main [data-testid]")
    _axe(page)


def _axe(page):
    if not page.evaluate("typeof axe !== 'undefined'"):
        page.add_script_tag(path=str(AXE))
    result = page.evaluate("async () => await axe.run(document, { runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21aa'] } })")
    serious = [v for v in result["violations"] if v["impact"] in ("serious", "critical")]
    assert serious == [], json.dumps([{"id": v["id"], "help": v["help"], "nodes": [n["target"] for n in v["nodes"]][:5]} for v in serious], indent=2)


def test_at_e2e_11_domain_triangle_opens_exactly_its_products(page):
    page.click("[data-testid=domains-view-table]")
    toggle = "[data-testid=domain-toggle-hcp]"
    assert page.get_attribute(toggle, "aria-expanded") == "false"
    page.click(toggle)
    assert page.get_attribute(toggle, "aria-expanded") == "true"
    rows = page.query_selector_all("[data-testid=domain-rows-hcp] [data-testid=product-row-link]")
    assert len(rows) == 5
    assert "Data product owner" in page.inner_text("[data-testid=domain-rows-hcp]")
    page.click(toggle)
    assert page.query_selector("[data-testid=domain-rows-hcp]") is None


def _products_page(browser, pack, width=1280, route="#/products"):
    ctx = browser.new_context(viewport={"width": width, "height": 800}, reduced_motion="reduce")
    pg = ctx.new_page()
    pg.goto((pack / "out" / WEEK / "index.html").as_uri() + route)
    pg.wait_for_selector("[data-testid=products-view]")
    return ctx, pg


def test_at_e2e_12_products_header_stays_on_top_while_rows_scroll(browser, pack):
    ctx, pg = _products_page(browser, pack)
    vp = "[data-testid=scroll-table-viewport]"
    pg.eval_on_selector(vp, "e => e.scrollIntoView({block: 'start'})")
    top0 = pg.eval_on_selector(vp, "e => e.getBoundingClientRect().top")
    pg.eval_on_selector(vp, "e => { e.scrollTop = 600; }")
    pg.wait_for_timeout(100)
    th = pg.eval_on_selector(f"{vp} thead th", "e => e.getBoundingClientRect().top")
    assert abs(th - top0) <= 2, f"header moved: {th} vs viewport top {top0}"
    assert pg.eval_on_selector(vp, "e => e.scrollTop") > 0
    # Product names stay frozen on the left during horizontal scroll.
    pg.eval_on_selector(vp, "e => { e.scrollLeft = 400; }")
    pg.wait_for_timeout(100)
    left = pg.eval_on_selector(f"{vp} tbody [data-testid=product-row-link]", "e => e.closest('td').getBoundingClientRect().left")
    vleft = pg.eval_on_selector(vp, "e => e.getBoundingClientRect().left")
    assert left - vleft < 80
    ctx.close()


def test_at_e2e_13_drag_the_table_to_scroll_sideways(browser, pack):
    ctx, pg = _products_page(browser, pack, width=1100)
    vp = "[data-testid=scroll-table-viewport]"
    pg.eval_on_selector(vp, "e => e.scrollIntoView({block: 'center'})")
    assert pg.eval_on_selector(vp, "e => e.scrollWidth > e.clientWidth"), "table should overflow at 1100 px"
    # Drag on an empty cell (days in stage column area) to the left.
    box = pg.eval_on_selector(vp, "e => { const r = e.getBoundingClientRect(); return [r.left, r.top, r.width, r.height]; }")
    y = box[1] + box[3] * 0.6
    pg.mouse.move(box[0] + box[2] * 0.75, y)
    pg.mouse.down()
    pg.mouse.move(box[0] + box[2] * 0.35, y, steps=8)
    pg.mouse.up()
    after_drag = pg.eval_on_selector(vp, "e => e.scrollLeft")
    assert after_drag > 100, f"drag did not scroll: {after_drag}"
    assert pg.url.endswith("#/products"), "a drag must not follow a link"
    # No hint line or second scrollbar under the table: the browser's own scrollbar is the only one.
    assert pg.query_selector("[data-testid=scroll-table-track]") is None
    assert "Drag the table" not in pg.inner_text("[data-testid=scroll-table]")
    # The browser's scrollbar (or a trackpad) scrolls the same viewport.
    pg.eval_on_selector(vp, "e => { e.scrollLeft = e.scrollWidth; }")
    assert pg.eval_on_selector(vp, "e => e.scrollLeft + e.clientWidth >= e.scrollWidth - 2")
    # Every row names its lifecycle stage in words.
    assert "In testing" in pg.inner_text("[data-testid=scroll-table]")
    ctx.close()


def test_at_e2e_14_search_matches_words_in_any_order(browser, pack):
    ctx, pg = _products_page(browser, pack)
    pg.keyboard.press("/")
    assert pg.evaluate("document.activeElement.dataset.testid") == "product-search"
    pg.keyboard.type("insights market")
    pg.wait_for_timeout(150)
    assert int(pg.get_attribute("[data-testid=products-count]", "data-count")) == 1
    assert pg.inner_text("[data-testid=product-row-link]") == "Market Access Insights"
    assert "q=insights" in pg.url
    pg.fill("[data-testid=product-search]", "pj360")
    pg.wait_for_timeout(150)
    assert pg.inner_text("[data-testid=product-row-link] >> nth=0") == "Patient Journey 360"
    pg.keyboard.press("Escape")
    pg.wait_for_timeout(150)
    assert int(pg.get_attribute("[data-testid=products-count]", "data-count")) == 25
    ctx.close()


def test_at_e2e_15_map_labels_sit_close_to_their_own_clusters(page):
    gaps = page.evaluate("""() => {
      const snap = JSON.parse(document.getElementById('snapshot').textContent);
      const domainOf = Object.fromEntries(snap.products.map(p => [p.urn, p.domain]));
      const out = {};
      for (const d of snap.domains) {
        const label = document.querySelector(`[data-testid=cluster-map] [data-testid=cluster-label-${d.id}]`);
        const tops = [...document.querySelectorAll('[data-testid=cluster-map] [data-testid=cluster-bubble]')]
          .filter(b => domainOf[b.dataset.urn] === d.id).map(b => b.getBoundingClientRect().top);
        if (!tops.length) continue;  // an empty domain has a label and no bubbles (placement: cluster.test.ts)
        out[d.id] = Math.round(Math.min(...tops) - label.getBoundingClientRect().bottom);
      }
      return out;
    }""")
    assert max(gaps.values()) - min(gaps.values()) <= 14, gaps
    assert max(gaps.values()) <= 70, gaps


@pytest.mark.skipif(not AXE.exists(), reason="axe-core not installed in app/node_modules")
def test_at_e2e_16_domain_tables_open_and_closed(page):
    page.click("[data-testid=domains-view-table]")
    _axe(page)  # executive table, all closed
    page.click("[data-testid=toggle-all-domains]")
    assert page.get_attribute("[data-testid=domain-toggle-r-and-d]", "aria-expanded") == "true"
    _axe(page)  # all open
    page.goto(page.url.split("#")[0] + "#/products")
    page.wait_for_selector("[data-testid=products-view]")
    assert page.get_attribute("[data-testid=domain-toggle-hcp]", "aria-expanded") == "true", "products page starts open"
    page.click("[data-testid=toggle-all-domains]")
    assert page.get_attribute("[data-testid=domain-toggle-hcp]", "aria-expanded") == "false"
    _axe(page)
    page.goto(page.url.split("#")[0] + "#/products?stage=In+testing")
    page.wait_for_selector("[data-testid=products-view]")
    if page.inner_text("[data-testid=toggle-all-domains]") == "Collapse all":
        page.click("[data-testid=toggle-all-domains]")
    page.wait_for_selector("[data-testid^=domain-shown-]")  # a closed group of a filtered list says "n of N products"


# --- Platform files in the inbox (tests/fixtures/inbox-platform) ---------------------------------


@pytest.fixture(scope="module")
def platform_pack(tmp_path_factory, regs) -> Path:
    base = tmp_path_factory.mktemp("platform-pack")
    res = run_build(PLATFORM_INBOX, WEEK, base / "out", base / "state", regs=regs)
    assert res.built
    return base


@pytest.fixture
def ppage(browser, platform_pack):
    ctx = browser.new_context(viewport={"width": 1400, "height": 900}, reduced_motion="reduce")
    pg = ctx.new_page()
    errors: list[str] = []
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    pg.goto((platform_pack / "out" / WEEK / "index.html").as_uri())
    pg.wait_for_selector("[data-testid=exec-view]")
    yield pg
    assert errors == [], errors
    ctx.close()


def test_at_e2e_17_coverage_figures_open_the_products_missing_them(ppage):
    ids = [el.get_attribute("data-testid") for el in ppage.query_selector_all("[data-testid=reporting-strip] a[data-testid^=coverage-]")]
    assert "coverage-reviewed" in ids and "coverage-nextdata" in ids
    for tid in ids:
        expected = _count(ppage, f"[data-testid={tid}]")
        ppage.click(f"[data-testid={tid}]")
        ppage.wait_for_selector("[data-testid=products-view]")
        assert _count(ppage, "[data-testid=products-count]") == expected, tid
        ppage.go_back()
        ppage.wait_for_selector("[data-testid=exec-view]")


def test_at_e2e_18_readiness_figures_match_their_lists(ppage):
    assert "Technical readiness" in ppage.inner_text("[data-testid=readiness-strip]")
    for mid in ["spec_score_median", "runtime_failing"]:
        sel = f"[data-testid=tile-link-{mid}-org]"
        expected = _count(ppage, sel)
        ppage.click(sel)
        ppage.wait_for_selector("[data-testid=products-view]")
        assert _count(ppage, "[data-testid=products-count]") == expected, mid
        ppage.go_back()
        ppage.wait_for_selector("[data-testid=exec-view]")


def test_at_e2e_19_product_page_shows_the_platform(ppage):
    ppage.goto(ppage.url.split("#")[0] + "#/products/nxd:dp-ops-crmsys")
    section = ppage.wait_for_selector("[data-testid=platform-section]")
    text = section.inner_text()
    assert "Started" in text and "crmsys" in text and "73%" in text
    # The NextData link of the best running deployment, and one per deployment.
    assert ppage.get_attribute("[data-testid=nextdata-link]", "href") == "https://nxd.example.dev/dp/dp-ops-crmsys-dev"
    assert len(section.query_selector_all("a[aria-label^='Open ']")) == 3
    ppage.goto(ppage.url.split("#")[0] + "#/products?runtime=Failed")
    ppage.wait_for_selector("[data-testid=products-view]")
    assert _count(ppage, "[data-testid=products-count]") == 1


def test_at_e2e_20_register_only_pack_has_no_platform_panels(page):
    assert page.query_selector("[data-testid=readiness-strip]") is None
    assert page.query_selector("[data-testid=reporting-strip]") is None


@pytest.mark.skipif(not AXE.exists(), reason="axe-core not installed in app/node_modules")
@pytest.mark.parametrize("route", ["#/", "#/products", "#/products/nxd:dp-ops-crmsys", "#/domain/hcp", "#/products?missing=reviewed"])
def test_at_e2e_21_axe_with_platform_data(ppage, route):
    ppage.goto(ppage.url.split("#")[0] + route)
    ppage.wait_for_selector("main [data-testid]")
    _axe(ppage)


def test_at_e2e_22_front_page_order(ppage):
    """Technical readiness sits above Speed and adoption; Reporting coverage closes the page."""
    order = ppage.evaluate("""() => [...document.querySelectorAll('[data-testid=exec-view] > *')].map((el) => el.getAttribute('data-testid') || el.querySelector('[data-testid]')?.getAttribute('data-testid') || el.tagName)""")
    assert order.index("readiness-strip") < order.index("stat-strip")
    assert order[-1] == "reporting-strip", order


def test_at_e2e_22_quarter_selector_shows_a_closed_quarter(page):
    stamp = page.query_selector("header [data-testid=last-updated]")
    assert "Updated" in stamp.inner_text() and "ink-3" in stamp.get_attribute("class"), "a quiet line in the header"
    assert "Last updated" in page.inner_text("footer")
    assert page.query_selector("[data-testid=cluster-map] [data-health]") is None, "health belongs to the quarter panel, not the map"
    assert page.get_attribute("[data-testid=exec-view]", "data-quarter") == "2026-Q4"
    page.click("[data-testid=quarter-2026-Q3]")
    page.wait_for_selector("[data-testid=exec-view][data-quarter='2026-Q3']")
    assert page.url.endswith("#/?q=2026-Q3")
    assert "Below target. 4 of 6 data products went live in Q3 2026" in page.inner_text("[data-testid=quarter-verdict]")
    assert page.query_selector("[data-testid=delivered-list]") is not None
    assert len(page.query_selector_all("[data-testid=delivered-item]")) == 4
    page.reload()
    page.wait_for_selector("[data-testid=exec-view][data-quarter='2026-Q3']")  # the choice survives a reload
    page.click("[data-testid=quarter-2026-Q4]")
    page.wait_for_selector("[data-testid=exec-view][data-quarter='2026-Q4']")


def test_at_e2e_23_trend_by_week_and_hidden_empty_areas(page):
    page.click("[data-testid=trend-unit-weeks]")
    page.wait_for_selector("[data-testid=trend-chart][data-unit=weeks]")
    assert page.get_attribute("[data-testid=trend-week-2026-W41]", "data-value") == "3"
    assert page.get_attribute("[data-testid=trend-week-2026-W40]", "data-value") == "1"
    # G&A and Logistics have no products: no map cluster, no summary row.
    assert page.query_selector("[data-testid=cluster-label-g-and-a]") is None
    assert page.query_selector("[data-testid=cluster-label-logistics]") is None
    assert page.query_selector("[data-testid=cluster-label-techops]") is not None
    assert page.query_selector("[data-testid=domain-health-g-and-a]") is None


def test_at_e2e_24_attention_list_fills_the_column_beside_the_map(page):
    def check():
        page.wait_for_timeout(300)
        att = page.eval_on_selector("[data-testid=attention]", "e => e.getBoundingClientRect().bottom")
        panel = page.eval_on_selector("section[aria-labelledby=domains-h]", "e => e.getBoundingClientRect().bottom")
        assert abs(att - panel) <= 2, (att, panel)
        shown = len(page.query_selector_all("[data-testid=needs-attention-item]"))
        more = page.query_selector("[data-testid=needs-attention-more]")
        rest = int(more.get_attribute("data-count")) if more else 0
        assert shown + rest == 7 and shown >= 1
        return shown

    in_map = check()
    page.click("[data-testid=domains-view-table]")
    in_table = check()
    assert in_map >= in_table, "the taller map leaves room for at least as many items as the table"


# --- GitHub extract in the inbox (tests/fixtures/inbox-platform plus tests/fixtures/github) -----------


@pytest.fixture(scope="module")
def github_pack(tmp_path_factory, regs) -> Path:
    import shutil

    from conftest import FIXTURES

    base = tmp_path_factory.mktemp("github-pack")
    shutil.copytree(PLATFORM_INBOX, base / "inbox")
    shutil.copytree(FIXTURES / "github", base / "inbox" / "github")
    res = run_build(base / "inbox", WEEK, base / "out", base / "state", regs=regs)
    assert res.built
    return base


@pytest.fixture
def gpage(browser, github_pack):
    ctx = browser.new_context(viewport={"width": 1400, "height": 900}, reduced_motion="reduce")
    pg = ctx.new_page()
    errors: list[str] = []
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    pg.goto((github_pack / "out" / WEEK / "index.html").as_uri())
    pg.wait_for_selector("[data-testid=exec-view]")
    yield pg
    assert errors == [], errors
    ctx.close()


def test_at_e2e_25_github_figures_match_their_lists(gpage):
    strip = gpage.inner_text("[data-testid=readiness-strip]")
    assert "GitHub" in strip and "of 7 deployments" in strip
    for mid in ["no_prod_deploy", "deploy_failure_rate"]:
        sel = f"[data-testid=tile-link-{mid}-org]"
        expected = _count(gpage, sel)
        gpage.click(sel)
        gpage.wait_for_selector("[data-testid=products-view]")
        assert _count(gpage, "[data-testid=products-count]") == expected, mid
        gpage.go_back()
        gpage.wait_for_selector("[data-testid=exec-view]")
    gpage.goto(gpage.url.split("#")[0] + "#/products/nxd:dp-ops-crmsys")
    block = gpage.wait_for_selector("[data-testid=platform-github]")
    assert "Last production deploy" in block.inner_text()


@pytest.mark.skipif(not AXE.exists(), reason="axe-core not installed in app/node_modules")
@pytest.mark.parametrize("route", ["#/", "#/products/nxd:dp-ops-crmsys", "#/products/urn:dp:com:legacy-cube", "#/delivery", "#/delivery?all=1"])
def test_at_e2e_26_axe_with_github_data(gpage, route):
    gpage.goto(gpage.url.split("#")[0] + route)
    gpage.wait_for_selector("main [data-testid]")
    _axe(gpage)


def test_at_e2e_27_delivery_tab_only_with_an_extract(page, gpage):
    assert page.locator("[data-testid=nav-delivery]").count() == 0
    assert page.locator("[data-testid=delivery-summary]").count() == 0
    gpage.click("[data-testid=nav-delivery]")
    gpage.wait_for_selector("[data-testid=delivery-view]")
    assert gpage.inner_text("[data-testid=del-reached-prod]").split("\n")[1] == "3"
    assert "of 8 repositories" in gpage.inner_text("[data-testid=del-reached-prod]")
    assert "1 failed, 3 succeeded" in gpage.inner_text("[data-testid=del-prod-attempts]")
    assert _count(gpage, "[data-testid=del-repo-table]") == 8


def test_at_e2e_28_funnel_and_team_filter_the_repositories(gpage):
    gpage.goto(gpage.url.split("#")[0] + "#/delivery")
    prod = "[data-testid=del-funnel-iac-apply-p]"
    expected = _count(gpage, prod)
    gpage.click(prod)
    gpage.wait_for_function(f"document.querySelector('[data-testid=del-repo-table]').dataset.count === '{expected}'")
    assert expected == 3
    gpage.click("[data-testid=del-toggle-all]")
    gpage.wait_for_function("location.hash.includes('all=1')")
    gpage.click("[data-testid=del-clear]")
    gpage.wait_for_function("document.querySelector('[data-testid=del-repo-table]').dataset.count === '10'")
    assert "Not counted: Test" in gpage.inner_text("[data-repo=edp-hcp-dp-survey_test]")
    gpage.goto(gpage.url.split("#")[0] + "#/delivery?team=ops")
    gpage.wait_for_function("document.querySelector('[data-testid=del-repo-table]').dataset.count === '3'")


def test_at_e2e_29_delivery_on_the_overview_and_product_page(gpage):
    order = gpage.evaluate("[...document.querySelectorAll('[data-testid=readiness-strip],[data-testid=delivery-summary]')].map(e => e.dataset.testid)")
    assert order == ["readiness-strip", "delivery-summary"]  # the register has gates: Delivery sits beside readiness
    gpage.goto(gpage.url.split("#")[0] + "#/products/nxd:dp-ops-crmsys")
    facts = gpage.wait_for_selector("[data-testid=github-delivery]").inner_text()
    assert "3 production deploys ever" in facts and "Last failure 1 Oct 2026" in facts


def test_at_e2e_30_delivery_fits_a_phone(browser, github_pack):
    ctx = browser.new_context(viewport={"width": 390, "height": 844})
    pg = ctx.new_page()
    pg.goto((github_pack / "out" / WEEK / "index.html").as_uri() + "#/delivery")
    pg.wait_for_selector("[data-testid=delivery-view]")
    assert pg.evaluate("document.documentElement.scrollWidth") <= 390
    ctx.close()
