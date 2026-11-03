"""The computed view of the inbox that metric and flag functions read from."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from pipeline.contracts import DQItem, Inbox, Product, ProductFlag, Target
from pipeline.dates import quarter_of
from pipeline.lifecycle import Derived, derive
from pipeline.registry import DomainRegistry, PlatformConfig


@dataclass
class ProductCtx:
    p: Product
    d: Derived
    consumed_by: list[str] = field(default_factory=list)
    flags: list[ProductFlag] = field(default_factory=list)
    platform: object | None = None  # pipeline.platform.PlatformProduct when the platform files know the product
    github: object | None = None  # pipeline.readers.github.GithubRepo when the GitHub extract has its repository

    @property
    def urn(self) -> str:
        return self.p.urn

    @property
    def domain(self) -> str:
        return self.p.domain

    def has_flag(self, code: str) -> bool:
        return any(f.code == code for f in self.flags)


@dataclass
class MetricContext:
    as_of: date
    quarter: str
    products: list[ProductCtx]
    targets: dict[tuple[str, str], int]
    domains: DomainRegistry
    warnings: list[DQItem] = field(default_factory=list)
    platform_cfg: PlatformConfig | None = None
    has_validation: bool = False  # validation results are in the inbox
    has_nextdata: bool = False  # a NextData listing is in the inbox
    has_github: bool = False  # a GitHub extract is in the inbox
    closed: bool = False  # a past quarter seen from its last day: nothing is forecast, usage is not known

    def scoped(self, scope: str) -> list[ProductCtx]:
        return self.products if scope == "org" else [pc for pc in self.products if pc.domain == scope]

    def target(self, scope: str, quarter: str | None = None) -> int | None:
        q = quarter or self.quarter
        if scope == "org":
            vals = [t for (dom, qq), t in self.targets.items() if qq == q]
            return sum(vals) if vals else None
        return self.targets.get((scope, q))

    def by_urn(self, urn: str) -> ProductCtx | None:
        return next((pc for pc in self.products if pc.urn == urn), None)


def build_context(inbox: Inbox, as_of: date, domains: DomainRegistry) -> MetricContext:
    events_by_urn: dict[str, list] = {}
    for e in inbox.gate_events:
        events_by_urn.setdefault(e.urn, []).append(e)
    products = [ProductCtx(p, derive(p, events_by_urn.get(p.urn, []), as_of)) for p in inbox.products]

    # Consumers: active products that declare this product as an input (self-references ignored).
    active_by_urn = {pc.urn: pc for pc in products if pc.d.active}
    for consumer in products:
        if not consumer.d.active:
            continue
        for inp in consumer.p.input_products:
            if inp == consumer.urn:
                continue
            target = next((pc for pc in products if pc.urn == inp), None)
            if target is not None and consumer.urn in active_by_urn:
                target.consumed_by.append(consumer.urn)
    for pc in products:
        pc.consumed_by.sort()

    targets = {(t.domain, t.quarter): t.certification_target for t in inbox.targets}
    return MetricContext(as_of=as_of, quarter=quarter_of(as_of), products=products, targets=targets, domains=domains)
