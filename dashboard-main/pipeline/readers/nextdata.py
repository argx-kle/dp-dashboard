"""NextData exports: the deployment listing (`dp list` text), the catalog lookup (CSV) and the domain tree (CSV).

All three are optional. Problems are warnings: the weekly pack never waits for a platform export.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from pipeline.contracts import DQItem
from pipeline.readers.base import normalise_header, read_csv_rows, split_list

_MISSING = {"", "-", "—", "not found", "null", "none", "n/a"}


@dataclass
class Deployment:
    name: str
    env: str
    version: str
    state: str  # Started | Failed | Unreachable | other, title-cased
    rpc_ready: bool = False
    url: str | None = None


@dataclass
class CatalogEntry:
    name: str
    found: bool
    domain: str | None = None  # normalised path, e.g. EDP/OPS
    version: str | None = None
    state: str | None = None
    owner: str | None = None
    urn: str | None = None
    input_ports: list[str] = field(default_factory=list)
    row: int = 0


@dataclass
class DomainNode:
    path: str  # normalised, e.g. EDP/CLAIMS
    parent: str | None
    description: str | None
    products: int | None
    created: date | None


def normalise_domain(raw: str | None) -> str | None:
    s = (raw or "").strip()
    if s.lower() in _MISSING:
        return None
    return "/".join(part.strip().upper() for part in s.split("/") if part.strip())


def normalise_state(raw: str | None) -> str:
    s = (raw or "").strip()
    if s.lower() in _MISSING:
        return "Unknown"
    return s[:1].upper() + s[1:].lower()


def is_listing(path: Path) -> bool:
    try:
        first = path.read_text(encoding="utf-8-sig", errors="replace").splitlines()[0]
    except (OSError, IndexError):
        return False
    tokens = {t.lower() for t in first.split()}
    return {"name", "env", "state"} <= tokens


def read_listing(path: Path) -> tuple[list[Deployment], list[DQItem]]:
    """Whitespace-separated columns under a header line (NAME ENV VERSION IMAGE STATE RPC BASE_URL); '-' is blank."""
    issues: list[DQItem] = []
    lines = [ln for ln in path.read_text(encoding="utf-8-sig", errors="replace").splitlines() if ln.strip()]
    if not lines:
        return [], [DQItem("warning", "SOURCE_MISSING", "NextData listing is empty", file=path.name)]
    header = [normalise_header(h) for h in lines[0].split()]
    missing = [c for c in ("name", "env", "version", "state") if c not in header]
    if missing:
        return [], [DQItem("warning", "UNREADABLE", f"NextData listing has no {', '.join(missing)} column", file=path.name)]
    out: list[Deployment] = []
    for i, line in enumerate(lines[1:], start=1):
        parts = line.split()
        if len(parts) != len(header):
            issues.append(DQItem("warning", "ND_PARSE", f"Listing line has {len(parts)} values for {len(header)} columns; skipped", file=path.name, row=i))
            continue
        rec = dict(zip(header, parts))
        out.append(
            Deployment(
                name=rec["name"],
                env=rec["env"].lower(),
                version=rec["version"],
                state=normalise_state(rec["state"]),
                rpc_ready=rec.get("rpc", "").lower() == "ready",
                url=None if rec.get("base_url", "-") in _MISSING else rec.get("base_url"),
            )
        )
    return out, issues


def read_catalog(path: Path) -> tuple[list[CatalogEntry], list[DQItem]]:
    headers, rows = read_csv_rows(path)
    norm = [normalise_header(h) for h in headers]
    if "name" not in norm:
        return [], [DQItem("warning", "UNREADABLE", "NextData catalog has no 'name' column", file=path.name)]
    out: list[CatalogEntry] = []
    for i, r in enumerate(rows, start=1):
        rec = dict(zip(norm, [*r, *[""] * (len(norm) - len(r))]))
        name = rec.get("name", "").strip()
        if not name:
            continue
        raw_domain = rec.get("domain", "")
        found = raw_domain.strip().lower() != "not found" and bool(raw_domain.strip() or rec.get("version", "").strip())
        out.append(
            CatalogEntry(
                name=name,
                found=found,
                domain=normalise_domain(raw_domain),
                version=rec.get("version") or None,
                state=normalise_state(rec.get("state")) if rec.get("state") else None,
                owner=(rec.get("owner") or "").strip() or None,
                urn=(rec.get("urn") or "").strip() or None,
                input_ports=split_list(rec.get("input_ports", "")),
                row=i,
            )
        )
    return out, []


_JAMMED = re.compile(r"^(?:(?P<desc>.*?)\s{2,})?(?P<count>\d+|-)\s+(?P<created>\d{4}-\d{2}-\d{2}|-)\s*$")


def read_domain_tree(path: Path) -> tuple[list[DomainNode], list[DQItem]]:
    """Columns domain, parent, description, data_products, created. Also reads the CLI export where the
    last three are jammed into the description cell with padding (and tree glyphs in the trailing cells)."""
    headers, rows = read_csv_rows(path)
    norm = [normalise_header(h) for h in headers]
    if "domain" not in norm:
        return [], [DQItem("warning", "UNREADABLE", "Domain tree has no 'domain' column", file=path.name)]
    out: list[DomainNode] = []
    for r in rows:
        rec = dict(zip(norm, [*r, *[""] * (len(norm) - len(r))]))
        dom = normalise_domain(rec.get("domain"))
        if not dom:
            continue
        desc_cell = rec.get("description", "")
        m = _JAMMED.match(desc_cell.strip())
        if m:
            desc, count, created = m.group("desc"), m.group("count"), m.group("created")
        else:
            desc, count, created = desc_cell, rec.get("data_products", ""), rec.get("created", "")
        out.append(
            DomainNode(
                path=dom,
                parent=normalise_domain(rec.get("parent")),
                description=None if (desc or "").strip() in _MISSING else desc.strip(),
                products=int(count) if str(count).strip().isdigit() else None,
                created=_date_or_none(created),
            )
        )
    return out, []


def _date_or_none(s: str | None) -> date | None:
    try:
        return date.fromisoformat((s or "").strip())
    except ValueError:
        return None
