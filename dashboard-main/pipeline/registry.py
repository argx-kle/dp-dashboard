"""Loaders for the YAML registries. Registries are data; nothing here knows what a metric means."""

from __future__ import annotations

import importlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import yaml

from pipeline import REGISTRY_DIR


@dataclass
class MetricDef:
    id: str
    label: str
    short_label: str
    definition: str
    levels: list[str]
    unit: str
    exec_tile: bool
    order: int
    source: str
    compare_to: str | None = None
    min_n: int | None = None
    fn: str | None = None
    coverage: str | None = None

    def resolve(self) -> Callable:
        return _resolve(self.fn)


SIGNAL_RANK = {"red": 3, "orange": 2, "yellow": 1}


@dataclass
class FlagDef:
    code: str
    label: str
    level: str
    definition: str
    signal: str
    fn: str
    reason: str
    applies_to: str = "all"

    def __post_init__(self) -> None:
        if self.signal not in SIGNAL_RANK:
            raise ValueError(f"flags.yaml: {self.code} has signal {self.signal!r}; use one of {', '.join(SIGNAL_RANK)}")

    def resolve(self) -> Callable:
        return _resolve(self.fn)


@dataclass
class DomainDef:
    id: str
    name: str
    aliases: list[str]
    area: str = "Commercial"


@dataclass
class Screening:
    patterns: dict[str, re.Pattern]
    terms: list[re.Pattern]

    def match(self, text: str | None) -> str | None:
        """Return the name of the first matching pattern/term, or None."""
        if not text:
            return None
        for name, pat in self.patterns.items():
            if pat.search(text):
                return name
        for pat in self.terms:
            if pat.search(text):
                return f"term '{pat.pattern}'"
        return None


class DomainRegistry:
    def __init__(self, domains: list[DomainDef]):
        self.domains = domains
        self._by_alias: dict[str, DomainDef] = {}
        for d in domains:
            for a in [d.id, d.name, *d.aliases]:
                self._by_alias[_key(a)] = d

    def resolve(self, raw: str | None) -> DomainDef | None:
        return self._by_alias.get(_key(raw or ""))

    def get(self, domain_id: str) -> DomainDef:
        for d in self.domains:
            if d.id == domain_id:
                return d
        raise KeyError(domain_id)

    @property
    def ids(self) -> list[str]:
        return [d.id for d in self.domains]


def _key(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


def _resolve(dotted: str | None) -> Callable:
    if not dotted:
        raise ValueError("No function declared")
    module, _, name = dotted.rpartition(".")
    return getattr(importlib.import_module(module), name)


def _load(name: str, registry_dir: Path) -> Any:
    with open(registry_dir / name, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def load_metrics(registry_dir: Path = REGISTRY_DIR) -> list[MetricDef]:
    defs = [MetricDef(**e) for e in _load("metrics.yaml", registry_dir)]
    ids = [d.id for d in defs]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate metric id in metrics.yaml")
    return sorted(defs, key=lambda d: d.order)


def load_flags(registry_dir: Path = REGISTRY_DIR) -> list[FlagDef]:
    return [FlagDef(**e) for e in _load("flags.yaml", registry_dir)]


def load_domains(registry_dir: Path = REGISTRY_DIR) -> DomainRegistry:
    return DomainRegistry([DomainDef(**e) for e in _load("domains.yaml", registry_dir)])


@dataclass
class DomainRule:
    domain: str
    phrases: list[str]
    words: set[str]

    def matches(self, name: str) -> bool:
        n = name.lower()
        return any(p in n for p in self.phrases) or bool(self.words & set(re.split(r"[-_\s]+", n)))


@dataclass
class PlatformConfig:
    teams: dict[str, str]
    default_domain: str
    domain_rules: list[DomainRule]
    team_domains: dict[str, str]
    product_domains: dict[str, str]  # product key -> domain name (registry/product-domains.yaml)
    exclude_patterns: list[tuple[re.Pattern, str]]
    exclude_teams: list[str]
    exclude_unreachable_not_in_catalog: bool
    exclude_demo_only_unvalidated: bool
    env_rank: list[str]
    acronyms: set[str]

    def env_index(self, env: str | None) -> int:
        return self.env_rank.index(env) if env in self.env_rank else len(self.env_rank)


def load_platform_config(registry_dir: Path = REGISTRY_DIR) -> PlatformConfig:
    raw = _load("platform.yaml", registry_dir)
    mapping = _load("product-domains.yaml", registry_dir) if (registry_dir / "product-domains.yaml").exists() else {}
    product_domains: dict[str, str] = {}
    for domain, keys in (mapping or {}).items():
        for key in keys or []:
            if key in product_domains:
                raise ValueError(f"product-domains.yaml: {key} is listed under {product_domains[key]} and {domain}")
            product_domains[key] = domain
    return PlatformConfig(
        teams={str(k): str(v) for k, v in raw["teams"].items()},
        default_domain=raw["default_domain"],
        domain_rules=[DomainRule(r["domain"], [p.lower() for p in r.get("phrases") or []], {w.lower() for w in r.get("words") or []}) for r in raw.get("domain_rules") or []],
        team_domains={str(k): str(v) for k, v in (raw.get("team_domains") or {}).items()},
        product_domains=product_domains,
        exclude_patterns=[(re.compile(e["pattern"], re.IGNORECASE), e["reason"]) for e in raw.get("exclude_patterns") or []],
        exclude_teams=list(raw.get("exclude_teams") or []),
        exclude_unreachable_not_in_catalog=bool(raw.get("exclude_unreachable_not_in_catalog", True)),
        exclude_demo_only_unvalidated=bool(raw.get("exclude_demo_only_unvalidated", True)),
        env_rank=list(raw.get("env_rank") or []),
        acronyms={a.lower() for a in raw.get("acronyms") or []},
    )


def load_screening(registry_dir: Path = REGISTRY_DIR) -> Screening:
    raw = _load("screening.yaml", registry_dir)
    patterns = {k: re.compile(v, re.IGNORECASE) for k, v in (raw.get("patterns") or {}).items()}
    terms = [re.compile(t, re.IGNORECASE) for t in (raw.get("terms") or [])]
    return Screening(patterns, terms)
