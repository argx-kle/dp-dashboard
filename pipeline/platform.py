"""Platform sources -> data products. Rules: docs/metric-definitions.md, section "Platform sources".

NextData lists deployments, not products, and the validation tool uses its own keyids. This module decides
which names are one product, which are not counted and why, and what each product looks like on the platform:
1. Aliases: dp-<team>-X and a bare X are one product (the team-prefixed name is canonical); X-vN is a version of X.
2. Validation keyids match a name exactly, with a team prefix, with an -nxd suffix, with the same words in another
   order, as the prefix of exactly one name, or as a clone (identical results) of a matched keyid. A keyid that
   matches nothing is a product known only to the validation tool.
3. Not counted: name patterns, tooling teams, unreachable and unknown to the catalog, demo-only and never validated.
4. inbox/crosswalk.csv overrides every rule, name by name.
"""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path

from pipeline.contracts import DQItem, SourceStatus
from pipeline.readers.base import normalise_header, read_csv_rows
from pipeline.readers.nextdata import (
    CatalogEntry,
    Deployment,
    DomainNode,
    is_listing,
    read_catalog,
    read_domain_tree,
    read_listing,
)
from pipeline.readers.validation import ValidationRecord, ValidationRun, read_validation
from pipeline.registry import PlatformConfig

CROSSWALK = "crosswalk.csv"
CROSSWALK_COLUMNS = ["source", "name", "product", "include", "reason", "rule", "domain", "domain_by_rule", "display_name", "reviewed"]
VAL_STALE_DAYS = 14


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------


@dataclass
class XwalkRow:
    source: str
    name: str
    product: str | None
    include: bool | None
    reason: str | None
    domain: str | None
    display_name: str | None
    reviewed: bool
    row: int


@dataclass
class PlatformSources:
    deployments: list[Deployment] = field(default_factory=list)
    catalog: dict[str, CatalogEntry] = field(default_factory=dict)
    tree: list[DomainNode] = field(default_factory=list)
    validation: list[ValidationRun] = field(default_factory=list)
    crosswalk: dict[tuple[str, str], XwalkRow] | None = None
    sources: list[SourceStatus] = field(default_factory=list)
    issues: list[DQItem] = field(default_factory=list)
    has_listing: bool = False
    has_catalog: bool = False

    @property
    def present(self) -> bool:
        return bool(self.deployments or self.catalog or self.validation)


def _mtime(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat(timespec="seconds")


def _yes(value: str) -> bool | None:
    v = (value or "").strip().lower()
    if v in {"yes", "y", "true", "1", "include", "included"}:
        return True
    if v in {"no", "n", "false", "0", "exclude", "excluded"}:
        return False
    return None


def read_crosswalk(path: Path) -> tuple[dict[tuple[str, str], XwalkRow], list[DQItem]]:
    headers, rows = read_csv_rows(path)
    norm = [normalise_header(h) for h in headers]
    if "name" not in norm:
        return {}, [DQItem("warning", "UNREADABLE", "crosswalk.csv has no 'name' column", file=CROSSWALK)]
    out: dict[tuple[str, str], XwalkRow] = {}
    for i, r in enumerate(rows, start=1):
        rec = dict(zip(norm, [*r, *[""] * (len(norm) - len(r))]))
        name = rec.get("name", "").strip()
        if not name:
            continue
        source = (rec.get("source") or "nextdata").strip().lower()
        out[(source, name)] = XwalkRow(
            source=source,
            name=name,
            product=rec.get("product", "").strip() or None,
            include=_yes(rec.get("include", "")),
            reason=rec.get("reason", "").strip() or None,
            domain=rec.get("domain", "").strip() or None,
            display_name=rec.get("display_name", "").strip() or None,
            reviewed=bool(_yes(rec.get("reviewed", ""))),
            row=i,
        )
    return out, []


def _files(folder: Path, suffixes: tuple[str, ...]) -> list[Path]:
    if not folder.is_dir():
        return []
    return sorted(p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in suffixes and not p.name.startswith(("~", ".")))


def load_platform(inbox_dir: Path) -> PlatformSources:
    """inbox/nextdata/ (listing .txt, catalog and domain-tree .csv), inbox/validation/ (.xlsx or .csv), inbox/crosswalk.csv."""
    src = PlatformSources()
    nd = inbox_dir / "nextdata"
    for path in _files(nd, (".txt", ".csv", ".tsv")):
        label = f"nextdata/{path.name}"
        if path.suffix.lower() == ".txt" or is_listing(path):
            deps, issues = read_listing(path)
            src.deployments.extend(deps)
            src.has_listing = src.has_listing or bool(deps)
            src.sources.append(SourceStatus("NextData listing", label, _mtime(path), "ok" if deps else "missing", len(deps)))
        else:
            headers, _ = read_csv_rows(path)
            norm = {normalise_header(h) for h in headers}
            if "parent" in norm:
                nodes, issues = read_domain_tree(path)
                src.tree.extend(nodes)
                src.sources.append(SourceStatus("NextData domains", label, _mtime(path), "ok" if nodes else "missing", len(nodes)))
            else:
                entries, issues = read_catalog(path)
                for e in entries:
                    src.catalog[e.name] = e
                src.has_catalog = src.has_catalog or bool(entries)
                src.sources.append(SourceStatus("NextData catalog", label, _mtime(path), "ok" if entries else "missing", len(entries)))
        for i in issues:
            i.file = label
        src.issues.extend(issues)
    for path in _files(inbox_dir / "validation", (".xlsx", ".xlsm", ".csv")):
        label = f"validation/{path.name}"
        run, issues = read_validation(path)
        for i in issues:
            i.file = label
        src.issues.extend(issues)
        if run is not None:
            run.file = label
            src.validation.append(run)
        src.sources.append(SourceStatus("Validation results", label, _mtime(path), "ok" if run else "missing", len(run.records) if run else 0))
    xw = next((p for p in inbox_dir.iterdir() if p.is_file() and p.name.lower() == CROSSWALK), None) if inbox_dir.is_dir() else None
    if xw is not None:
        rows, issues = read_crosswalk(xw)
        src.crosswalk = rows
        src.issues.extend(issues)
        src.sources.append(SourceStatus("Crosswalk", CROSSWALK, _mtime(xw), "ok", len(rows)))
    return src


# ---------------------------------------------------------------------------
# Resolution
# ---------------------------------------------------------------------------


@dataclass
class Decision:
    source: str  # nextdata | validation
    name: str
    product: str
    include: bool
    reason: str
    rule: str
    reviewed: bool = False


@dataclass
class PlatformProduct:
    key: str
    include: bool
    reason: str  # why it is counted or not
    names: list[str]
    keyids: list[str]
    display_name: str
    team: str | None
    team_rule: str | None
    domain: str
    domain_rule: str  # how the domain was decided: crosswalk, product-domains.yaml, name rule, team, default
    platform_domain: str | None
    deployments: list[Deployment]
    validation: ValidationRecord | None
    run_date: date | None
    catalog_owner: str | None
    catalog_urn: str | None = None

    @property
    def runtime(self) -> str:
        states = {d.state for d in self.deployments}
        for s in ("Started", "Failed", "Unreachable"):
            if s in states:
                return s
        return self.deployments[0].state if self.deployments else "Not deployed"

    def best_deployment(self, cfg: PlatformConfig) -> Deployment | None:
        """The deployment that represents the product: running first, then the best environment, then the newest version."""
        pool = [d for d in self.deployments if d.state == "Started"] or self.deployments
        return min(pool, key=lambda d: (cfg.env_index(d.env), _version_key(d.version)), default=None)

    def best_env(self, cfg: PlatformConfig) -> str | None:
        best = self.best_deployment(cfg)
        return best.env if best else None


@dataclass
class Resolution:
    products: dict[str, PlatformProduct]  # every product key, counted or not
    decisions: list[Decision]
    lookup: dict[str, str]  # any NextData name, keyid, product key or catalog URN -> product key

    @property
    def included(self) -> list[PlatformProduct]:
        return [p for p in self.products.values() if p.include]

    @property
    def excluded(self) -> list[PlatformProduct]:
        return [p for p in self.products.values() if not p.include]

    def match(self, urn: str) -> PlatformProduct | None:
        """A register URN -> its platform product: nxd:<name>, a catalog URN, or a URN whose last segment is a name."""
        candidates = [urn]
        if urn.lower().startswith("nxd:"):
            candidates.append(urn[4:])
        candidates.append(urn.rsplit(":", 1)[-1])
        for c in candidates:
            key = self.lookup.get(c)
            if key is not None:
                return self.products[key]
        return None


def _version_key(version: str) -> tuple:
    """Sorts newest first: 1.0.5 before 1.0.4, a release before its -dev."""
    nums = [int(x) for x in re.findall(r"\d+", version.split("-")[0])]
    return tuple(-n for n in nums) + ((1,) if "-" in version else (0,))


_TEAM_NAME = re.compile(r"^dp-([a-z0-9]+)-(.+)$")


def team_of(name: str, cfg: PlatformConfig) -> tuple[str | None, str]:
    m = _TEAM_NAME.match(name)
    if m and m.group(1) in cfg.teams:
        return m.group(1), m.group(2)
    return None, name


def humanize(key: str, cfg: PlatformConfig) -> str:
    _, rest = team_of(key, cfg)
    words = [w for w in re.split(r"[-_\s]+", rest) if w]
    out = []
    for i, w in enumerate(words):
        lw = w.lower()
        if lw in cfg.acronyms:
            out.append(lw.upper())
        elif i == 0:
            out.append(lw[:1].upper() + lw[1:])
        else:
            out.append(lw)
    return " ".join(out) or key


def _clean_business_name(name: str | None) -> str | None:
    if not name or name.strip().lower() in {"missing", "n/a", "-"}:
        return None
    if not re.fullmatch(r"[A-Za-z0-9 &/.]+", name.strip()) or not re.search(r"[A-Z]", name):
        return None
    return name.strip()


_KEYID_RANK = {"keyid:exact": 0, "keyid:team-prefix": 1, "keyid:nxd-suffix": 2, "keyid:word-order": 3, "keyid:prefix": 4, "keyid:clone": 5}


def _merged_records(runs: list[ValidationRun]) -> dict[str, tuple[ValidationRecord, date | None]]:
    """Latest run wins per keyid."""
    out: dict[str, tuple[ValidationRecord, date | None]] = {}
    for run in sorted(runs, key=lambda r: r.run_date or date.min):
        for rec in run.records:
            out[rec.keyid] = (rec, run.run_date)
    return out


def resolve(src: PlatformSources, cfg: PlatformConfig) -> Resolution:
    names: list[str] = []
    for n in [d.name for d in src.deployments] + list(src.catalog):
        if n not in names:
            names.append(n)
    name_set = set(names)
    deps_by_name: dict[str, list[Deployment]] = defaultdict(list)
    for d in src.deployments:
        deps_by_name[d.name].append(d)

    records = _merged_records(src.validation)

    # 1. Aliases. A bare name is an older name of dp-<team>-<name> unless its repository or NextData domain
    #    points to another team (dp-claims-x built on the source system x is a different product).
    def evidence_team(n: str) -> str | None:
        rec = records.get(n, (None, None))[0]
        cat = src.catalog.get(n)
        return _team(n, [], rec, cat if cat and cat.found else None, cfg)[0]

    canon = {n: n for n in names}
    rule = {n: "canonical" for n in names}
    for n in names:
        team, rest = team_of(n, cfg)
        if team and rest in name_set and canon[rest] == rest and evidence_team(rest) in (None, team):
            canon[rest], rule[rest] = n, "alias:team-prefix"
    for n in names:
        m = re.match(r"^(.+)-v\d+$", n)
        if m and m.group(1) in name_set:
            canon[n], rule[n] = canon[m.group(1)], "alias:version"

    # 2. Validation keyids.
    key_match: dict[str, tuple[str, str]] = {}
    keyid_set = set(records)
    for k in records:
        prefixed = [f"dp-{t}-{k}" for t in cfg.teams if f"dp-{t}-{k}" in name_set]
        words = sorted(k.split("-"))
        same_words = [n for n in names if sorted(n.split("-")) == words]
        starts = [n for n in names if n.startswith(k + "-") and n not in keyid_set]
        if k in name_set:
            key_match[k] = (k, "keyid:exact")
        elif prefixed:
            key_match[k] = (prefixed[0], "keyid:team-prefix")
        elif f"{k}-nxd" in name_set:
            key_match[k] = (f"{k}-nxd", "keyid:nxd-suffix")
        elif len(same_words) == 1:
            key_match[k] = (same_words[0], "keyid:word-order")
        elif len(starts) == 1:
            key_match[k] = (starts[0], "keyid:prefix")
    for k, (rec, _) in records.items():
        if k in key_match:
            continue
        for j, (name, _r) in list(key_match.items()):
            other = records[j][0]
            if k.startswith(j + "-") and rec.score == other.score and rec.components == other.components:
                key_match[k] = (name, "keyid:clone")
                break

    # 3. Automatic decisions.
    def anchor_key(source: str, name: str) -> str:
        if source == "nextdata":
            return canon[name]
        return canon[key_match[name][0]] if name in key_match else name

    members: dict[str, list[str]] = defaultdict(list)
    keyids: dict[str, list[str]] = defaultdict(list)
    for n in names:
        members[canon[n]].append(n)
    for k in records:
        keyids[anchor_key("validation", k)].append(k)

    def auto_exclusion(key: str) -> tuple[str, str] | None:
        for pat, reason in cfg.exclude_patterns:
            if pat.search(key):
                return reason, "exclude:pattern"
        team, _ = team_of(key, cfg)
        if team in cfg.exclude_teams:
            return f"{cfg.teams[team]} tooling, not a business data product", "exclude:team"
        deps = [d for n in members.get(key, []) for d in deps_by_name.get(n, [])]
        if cfg.exclude_unreachable_not_in_catalog and deps and all(d.state == "Unreachable" for d in deps):
            if not any(src.catalog.get(n) and src.catalog[n].found for n in members.get(key, [])):
                return "Unreachable and not in the NextData catalog", "exclude:unreachable"
        if cfg.exclude_demo_only_unvalidated and deps and all(d.env == "demo" for d in deps) and not keyids.get(key):
            return "Deployed in a demo environment only and never validated", "exclude:demo-only"
        return None

    decisions: list[Decision] = []
    for n in names:
        key = canon[n]
        excl = auto_exclusion(key)
        if rule[n] == "alias:team-prefix":
            reason = f"Older name of {key}"
        elif rule[n] == "alias:version":
            reason = f"Another version of {key}"
        else:
            reason = "Data product"
        if excl:
            reason = excl[0] if n == key else f"{reason}; {excl[0].lower()}"
        decisions.append(Decision("nextdata", n, key, excl is None, reason, excl[1] if excl and n == key else rule[n]))
    for k in records:
        key = anchor_key("validation", k)
        excl = auto_exclusion(key)
        if k in key_match:
            reason, r = f"Validation results for {key}", key_match[k][1]
        else:
            reason, r = "Known only to the validation tool (not in NextData)", "validation-only"
        if excl and key == k:
            reason, r = excl[0], excl[1]
        decisions.append(Decision("validation", k, key, excl is None, reason, r))

    # 4. Crosswalk overrides, name by name.
    xw = src.crosswalk or {}
    for dec in decisions:
        row = xw.get((dec.source, dec.name))
        if row is None:
            continue
        dec.reviewed = row.reviewed
        changed = False
        if row.product and row.product != dec.product:
            dec.product, changed = row.product, True
        if row.include is not None and row.include != dec.include:
            dec.include, changed = row.include, True
        if row.reason:
            dec.reason = row.reason
        if changed:
            dec.rule = "crosswalk"

    # 5. Products.
    by_key: dict[str, list[Decision]] = defaultdict(list)
    for dec in decisions:
        by_key[dec.product].append(dec)
    match_rank = {k: _KEYID_RANK.get(r, 9) for k, (_, r) in key_match.items()}
    products: dict[str, PlatformProduct] = {}
    lookup: dict[str, str] = {}
    for key, decs in by_key.items():
        nd_names = [d.name for d in decs if d.source == "nextdata"]
        nd_names.sort(key=lambda n: (n != key, n))
        kids = [d.name for d in decs if d.source == "validation"]
        anchor = next((d for d in decs if d.name == key), None)
        include = anchor.include if anchor else any(d.include for d in decs)
        reason = anchor.reason if anchor else next((d.reason for d in decs if d.include == include), "")
        deps = [d for n in nd_names for d in deps_by_name.get(n, [])]
        primary = None
        if kids:
            def rank(k: str) -> tuple:
                matched = key_match.get(k, (k, ""))[0]
                envs = [d.env for d in deps_by_name.get(matched, [])]
                return (match_rank.get(k, 9), min((cfg.env_index(e) for e in envs), default=99), k)

            primary = min(kids, key=rank)
        rec, run_date = records[primary] if primary else (None, None)
        cat = next((src.catalog[n] for n in nd_names if n in src.catalog and src.catalog[n].found), None)
        rows = [xw.get((d.source, d.name)) for d in decs]
        rows = [r for r in rows if r is not None]
        rows.sort(key=lambda r: r.name != key)
        team, team_rule = _team(key, nd_names, rec, cat, cfg)
        products[key] = PlatformProduct(
            key=key,
            include=include,
            reason=reason,
            names=nd_names,
            keyids=sorted(kids),
            display_name=next((r.display_name for r in rows if r.display_name), None) or _clean_business_name(rec.business_name if rec else None) or humanize(key, cfg),
            team=team,
            team_rule=team_rule,
            domain=next((r.domain for r in rows if r.domain), None) or "",
            domain_rule="crosswalk" if any(r.domain for r in rows) else "",
            platform_domain=cat.domain if cat else None,
            deployments=deps,
            validation=rec,
            run_date=run_date,
            catalog_owner=cat.owner if cat else None,
            catalog_urn=cat.urn if cat else None,
        )
        for n in [key, *nd_names, *kids]:
            lookup.setdefault(n, key)
        if cat and cat.urn:
            lookup.setdefault(cat.urn, key)

    _family_teams(products, cfg)
    for p in products.values():
        if not p.domain:
            p.domain, p.domain_rule = business_domain(p, cfg)
    _distinct_names(products, cfg)
    return Resolution(products=products, decisions=decisions, lookup=lookup)


def business_domain(p: PlatformProduct, cfg: PlatformConfig) -> tuple[str, str]:
    """registry/product-domains.yaml (by key or any other name), then the name rules, then the team, then the default."""
    for n in [p.key, *p.names, *p.keyids]:
        if n in cfg.product_domains:
            return cfg.product_domains[n], "product-domains.yaml"
    for rule in cfg.domain_rules:
        if rule.matches(p.key):
            return rule.domain, "name rule"
    if p.team in cfg.team_domains:
        return cfg.team_domains[p.team], "team"
    return cfg.default_domain, "default"


def _distinct_names(products: dict[str, PlatformProduct], cfg: PlatformConfig) -> None:
    """Two counted products with the same display name get their team in brackets."""
    seen: dict[str, list[PlatformProduct]] = defaultdict(list)
    for p in products.values():
        if p.include:
            seen[p.display_name.lower()].append(p)
    for group in seen.values():
        if len(group) > 1:
            for p in group:
                label = cfg.teams.get(p.team) if p.team else None
                if label:
                    p.display_name = f"{p.display_name} ({label})"


def _team(key: str, names: list[str], rec: ValidationRecord | None, cat: CatalogEntry | None, cfg: PlatformConfig) -> tuple[str | None, str | None]:
    for n in [key, *names]:
        team, _ = team_of(n, cfg)
        if team:
            return team, "name prefix"
    if rec and rec.git:
        m = re.search(r"-([a-z0-9]+)-dp-", rec.git.lower())
        if m and m.group(1) in cfg.teams:
            return m.group(1), "repository name"
    if cat and cat.domain and "/" in cat.domain:
        t = cat.domain.split("/")[1].lower()
        if t in cfg.teams:
            return t, "NextData domain"
    return None, None


def _family_teams(products: dict[str, PlatformProduct], cfg: PlatformConfig) -> None:
    """Second pass for products without a team: same first word as products of one team, else a team word in the name."""
    def first_word(p: PlatformProduct) -> str:
        return team_of(p.key, cfg)[1].split("-")[0]

    known: dict[str, set[str]] = defaultdict(set)
    for p in products.values():
        if p.team and team_of(p.key, cfg)[0] is None:  # vendor families come from bare names only
            known[first_word(p)].add(p.team)
    for p in products.values():
        if p.team:
            continue
        teams = known.get(first_word(p), set())
        if len(teams) == 1:
            p.team, p.team_rule = next(iter(teams)), "same family as other products"
        else:
            words = set(p.key.split("-"))
            hit = [t for t in cfg.teams if t in words and t not in cfg.exclude_teams]
            if len(hit) == 1:
                p.team, p.team_rule = hit[0], "team word in the name"


# ---------------------------------------------------------------------------
# Checks that need only the platform files
# ---------------------------------------------------------------------------


def platform_checks(src: PlatformSources, res: Resolution, cfg: PlatformConfig) -> list[DQItem]:
    issues: list[DQItem] = []
    included = res.included
    cat_file = next((s.file for s in src.sources if s.name == "NextData catalog"), "nextdata")
    list_file = next((s.file for s in src.sources if s.name == "NextData listing"), "nextdata")

    if src.has_catalog:
        for p in included:
            for n in p.names:
                e = src.catalog.get(n)
                if e is not None and not e.found:
                    issues.append(DQItem("warning", "ND_NOT_FOUND", f"{n}: in the NextData listing, but the catalog lookup returned NOT FOUND", urn=f"nxd:{p.key}", file=cat_file))
        missing_owner = [p for p in included if p.names and not p.catalog_owner]
        if missing_owner:
            issues.append(DQItem("warning", "ND_NO_OWNER", f"NextData records no owner for {len(missing_owner)} of {len([p for p in included if p.names])} products", file=cat_file))

    tree = {n.path: n for n in src.tree}
    if tree:
        groups: dict[tuple[str, str], list[str]] = defaultdict(list)
        for p in included:
            team, _ = team_of(p.key, cfg)
            expected = f"EDP/{team.upper()}" if team else None
            if expected and expected in tree and p.platform_domain and p.platform_domain != expected:
                groups[(team, p.platform_domain)].append(p.key)
        for (team, dom), keys in sorted(groups.items()):
            expected = f"EDP/{team.upper()}"
            held = tree[expected].products or 0
            many = len(keys) != 1
            issues.append(DQItem("warning", "ND_DOMAIN", f"{len(keys)} {cfg.teams[team]} product{'s are' if many else ' is'} registered under {dom}; the team domain {expected} holds {held}", file=cat_file))
        top = [n for n in src.tree if not n.parent and n.products is not None]
        if src.deployments and top and sum(n.products for n in top) != len(src.deployments):
            issues.append(DQItem("warning", "ND_RECONCILE", f"The domain tree counts {sum(n.products for n in top)} deployments; the listing has {len(src.deployments)}", file=list_file))

    for p in included:
        running_names = sorted({d.name for d in p.deployments})
        if len(running_names) > 1:
            issues.append(DQItem("warning", "ND_DUPLICATE", f"Deployed under {len(running_names)} names: {', '.join(running_names)}", urn=f"nxd:{p.key}", file=list_file))

    if src.crosswalk is None:
        issues.append(DQItem("warning", "XWALK_MISSING", "No crosswalk.csv: product identity is decided by the rules alone. Run scripts/seed_crosswalk.py and review it", file=CROSSWALK))
    else:
        new = [d.name for d in res.decisions if (d.source, d.name) not in src.crosswalk]
        if new:
            issues.append(DQItem("warning", "XWALK_NEW", f"{len(new)} names are not in the crosswalk yet (decided by rule): {', '.join(new[:8])}{' …' if len(new) > 8 else ''}", file=CROSSWALK))
        unreviewed = [r for r in src.crosswalk.values() if not r.reviewed]
        if unreviewed:
            issues.append(DQItem("warning", "XWALK_UNREVIEWED", f"{len(unreviewed)} of {len(src.crosswalk)} crosswalk decisions are not marked reviewed", file=CROSSWALK))
    return issues


def crosswalk_rows(res: Resolution) -> list[dict[str, str]]:
    """Rows for crosswalk.csv: one per NextData name and per validation keyid, product attributes on the product's own row."""
    out = []
    for d in sorted(res.decisions, key=lambda d: (d.product, d.source != "nextdata", d.name != d.product, d.name)):
        p = res.products[d.product]
        own = d.name == d.product
        out.append(
            {
                "source": d.source,
                "name": d.name,
                "product": d.product,
                "include": "yes" if d.include else "no",
                "reason": d.reason,
                "rule": d.rule,
                "domain": p.domain if own and p.include and p.domain_rule == "crosswalk" else "",
                "domain_by_rule": f"{p.domain} ({p.domain_rule})" if own and p.include and p.domain_rule != "crosswalk" else "",
                "display_name": p.display_name if own and p.include else "",
                "reviewed": "yes" if d.reviewed else "",
            }
        )
    return out
