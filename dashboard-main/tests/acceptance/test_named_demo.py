"""AT-DEMO: the named demo (tests/fixtures/inbox-named-demo): real product and domain names, made-up values.

Built the way scripts/make_named_demo.py builds it: weeks 39 and 40 approved first, then week 41.
"""

from __future__ import annotations

from collections import Counter

import pytest

from scripts.make_named_demo import OUT, build_weeks


@pytest.fixture(scope="module")
def demo(tmp_path_factory):
    base = tmp_path_factory.mktemp("named-demo")
    return build_weeks(base, template_path=base / "none").snapshot


def test_at_demo_01_real_names_and_domains(demo, platform_cfg):
    assert len(demo["products"]) == 44
    by_key = {p["urn"].split(":", 1)[1]: p for p in demo["products"]}
    name_of = {d["id"]: d["name"] for d in demo["domains"]}
    for key, domain in platform_cfg.product_domains.items():
        assert name_of[by_key[key]["domain"]] == domain, key


def test_at_demo_02_every_status_signal_and_flag_shows(demo):
    statuses = Counter(p["status"] for p in demo["products"])
    assert set(statuses) == {"In design", "In build", "In certification", "Live", "Live · in revision", "Retired", "Cancelled"}
    assert set(Counter(p["signal"] for p in demo["products"])) == {"red", "orange", "yellow", "green", "grey", "unreported"}
    flags = {f["code"] for p in demo["products"] for f in p["flags"]}
    assert flags == {"OVERDUE", "SLIPPING", "UNUSED", "NO_DPO", "NOT_UPDATED", "PENDING_URN"}
    behind = [m["scope"] for m in demo["metrics"] if m.get("flag") == "BEHIND"]
    at_risk = [h["scope"] for h in demo["health"] if h["quarter"] == demo["quarter"] and h["scope"] != "org" and h["status"] in ("at-risk", "off-track")]
    assert sorted(behind) == sorted(at_risk)  # BEHIND follows the pace verdict (none yet, 10% into the quarter)


def test_at_demo_03_history_and_platform_are_filled(demo):
    assert demo["changes"] and demo["changes"][0].startswith("Certified since 2026-W40")
    org = {r["kind"]: (r["have"], r["of"]) for r in demo["reporting"] if r["scope"] == "org"}
    assert org["validation"][0] == org["validation"][1] and org["nextdata"][0] == org["nextdata"][1]
    assert all(p.get("nextdata", {}).get("url", "").startswith("https://nxd.aks.argenx-dev.com/dp/") for p in demo["products"] if p.get("nextdata", {}).get("deployments"))
    assert not [d for d in demo["dataQuality"] if d["severity"] == "blocker"]
    assert (OUT / "crosswalk.csv").exists()
