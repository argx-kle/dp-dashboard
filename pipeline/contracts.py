"""The two contracts in Python form.

Inbox rows are plain dataclasses filled by the readers after coercion.
Snapshot models are pydantic and mirror schema/snapshot.schema.json field for field
(tests/acceptance/test_schema.py checks the two never drift).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict

# ---------------------------------------------------------------------------
# Inbox contract
# ---------------------------------------------------------------------------

GATES = ["G1", "G2", "G3", "G4", "G5", "G6"]
G5_PATHS = ["scope change", "bug fix"]


@dataclass
class DQItem:
    severity: Literal["blocker", "warning"]
    rule: str
    message: str
    urn: str | None = None
    file: str | None = None
    row: int | None = None


@dataclass
class SourceStatus:
    name: str
    file: str
    as_of: str
    status: Literal["ok", "missing"]
    rows: int


@dataclass
class Product:
    urn: str
    name: str
    domain: str  # domain id from registry/domains.yaml
    row: int
    dpo: str | None = None
    planned_next_gate_date: date | None = None
    planned_ga_date: date | None = None
    named_consumers: int = 0
    input_products: list[str] = field(default_factory=list)
    active_users_30d: int | None = None
    first_consumer_date: date | None = None
    dpo_comment: str | None = None
    reviewed_on: date | None = None
    cancelled_on: date | None = None


@dataclass
class GateEvent:
    urn: str
    gate: str
    date_passed: date
    row: int
    g5_path: str | None = None
    evidence_url: str | None = None


@dataclass
class Target:
    domain: str
    quarter: str
    certification_target: int
    row: int


@dataclass
class Capacity:
    domain: str
    week: str
    onboarded: int
    enrolled: int
    qualified: int
    row: int


@dataclass
class Inbox:
    products: list[Product] = field(default_factory=list)
    gate_events: list[GateEvent] = field(default_factory=list)
    targets: list[Target] = field(default_factory=list)
    capacity: list[Capacity] = field(default_factory=list)
    sources: list[SourceStatus] = field(default_factory=list)
    issues: list[DQItem] = field(default_factory=list)
    latest_mtime: float = 0.0

    @property
    def blockers(self) -> list[DQItem]:
        return [i for i in self.issues if i.severity == "blocker"]


# ---------------------------------------------------------------------------
# Snapshot contract (camelCase on purpose: these are the JSON names)
# ---------------------------------------------------------------------------


class _Model(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SignOff(_Model):
    status: Literal["draft", "approved"]
    approvedBy: str | None = None
    approvedAt: str | None = None


class DomainInfo(_Model):
    id: str
    name: str
    area: str


class SourceInfo(_Model):
    name: str
    file: str
    asOf: str
    status: Literal["ok", "missing"]
    rows: int


CoverageKind = Literal["gates", "plans", "reviewed", "dpo", "usage", "consumers", "validation", "nextdata", "github"]


class MetricDefinition(_Model):
    id: str
    label: str
    shortLabel: str
    definition: str
    levels: list[Literal["org", "domain"]]
    unit: Literal["count", "days", "share", "people"]
    compareTo: Literal["target"] | None = None
    minN: int | None = None
    execTile: bool
    order: int
    coverage: CoverageKind | None = None


class FlagDefinition(_Model):
    code: str
    label: str
    level: Literal["domain", "product"]
    definition: str
    signal: Literal["red", "orange", "yellow"]


class RegistryInfo(_Model):
    metrics: list[MetricDefinition]
    flags: list[FlagDefinition]


Number = int | float


class MetricValue(_Model):
    id: str
    scope: str
    value: Number | None
    n: int | None = None
    values: list[Number] | None = None
    target: Number | None = None
    source: Literal["register", "self-reported", "snowflake", "nextdata", "validation", "github"]
    flag: Literal["BEHIND"] | None = None
    reason: str | None = None
    urns: list[str] | None = None


class GateRecord(_Model):
    gate: Literal["G1", "G2", "G3", "G4", "G5", "G6"]
    date: str
    iteration: int
    g5Path: Literal["scope change", "bug fix"] | None = None
    evidenceUrl: str | None = None


class PlannedGate(_Model):
    gate: Literal["G1", "G2", "G3", "G4", "G5", "G6"]
    plannedDate: str
    baselineDate: str
    slips: int
    overdueDays: int


class PlannedGA(_Model):
    plannedDate: str
    baselineDate: str
    slips: int


class SourcedNumber(_Model):
    value: Number
    source: Literal["self-reported", "snowflake"]


class SourcedDate(_Model):
    value: str
    source: Literal["self-reported", "snowflake"]


class ComponentScore(_Model):
    label: str
    score: Number


class ValidationSummary(_Model):
    lastRun: str
    p1Findings: int | None = None
    score: Number | None = None
    components: list[ComponentScore] | None = None
    ownerStatus: str | None = None
    keyids: list[str] | None = None


class NextDataDeployment(_Model):
    name: str
    env: str
    version: str
    state: str
    url: str | None = None


class NextDataSummary(_Model):
    names: list[str]
    runtime: str
    env: str | None = None
    url: str | None = None
    team: str | None = None
    deployments: list[NextDataDeployment]


class GithubDeploy(_Model):
    env: str
    at: str
    outcome: Literal["success", "failure", "error", "pending"]


class GithubSummary(_Model):
    repo: str
    url: str | None = None
    lastProdDeploy: str | None = None
    prodDeploys30d: int
    deploys30d: int
    failed30d: int
    reached: str | None = None
    failingNow: list[str]
    recent: list[GithubDeploy]
    weekly: list[int]


class DeliveryEnv(_Model):
    id: str
    label: str
    prod: bool
    path: bool
    repos: int
    deploys30d: int
    failed30d: int


class DeliveryTotals(_Model):
    repos: int
    active30d: int
    deploys30d: int
    failed30d: int
    prodAttempts30d: int
    prodFailed30d: int
    reachedProd: int
    notInRegister: int
    lastProdDeploy: str | None = None
    lastProdRepo: str | None = None
    brokenNow: int
    pathEnvs: int
    bypass30d: int
    prodCommits30d: int
    recoveryHours30d: float | None = None
    onboarded: int


class DeliveryWeek(_Model):
    week: str
    start: str
    deploys: int
    failed: int
    prodSuccess: int
    firstDeploys: int


class DeliveryTeam(_Model):
    team: str
    label: str
    repos: int
    deploys30d: int
    failed30d: int
    reachedProd: int


class RepoEnv(_Model):
    env: str
    lastSuccess: str | None = None
    deploys30d: int
    failed30d: int


class DeliveryRepo(_Model):
    name: str
    url: str | None = None
    team: str | None = None
    urn: str | None = None
    excluded: str | None = None
    envs: list[RepoEnv]
    lastDeploy: str | None = None
    lastFailure: str | None = None
    lastProdDeploy: str | None = None
    prodDeploys: int
    deploys30d: int
    failed30d: int
    weekly: list[int]
    reached: str | None = None
    failingNow: list[str]


class DeliveryBroken(_Model):
    repo: str
    urn: str | None = None
    env: str
    since: str
    lastSuccess: str | None = None


class DeliveryBypass(_Model):
    repo: str
    urn: str | None = None
    sha: str
    at: str


class Delivery(_Model):
    fetchedAt: str
    org: str | None = None
    windowDays: int
    envs: list[DeliveryEnv]
    totals: DeliveryTotals
    weekly: list[DeliveryWeek]
    teams: list[DeliveryTeam]
    repos: list[DeliveryRepo]
    broken: list[DeliveryBroken]
    bypass: list[DeliveryBypass]


class ReportingItem(_Model):
    kind: CoverageKind
    scope: str
    have: int
    of: int
    missing: list[str]


class ProductFlag(_Model):
    code: Literal["OVERDUE", "SLIPPING", "NO_DPO", "NOT_UPDATED", "UNUSED", "PENDING_URN"]
    reason: str


Stage = Literal["Inception", "Discovery", "Design/Develop", "Test/Launch", "Operate/Support", "Retire"]
Lifecycle = Literal["Ideation", "In design", "In development", "In testing", "Live", "Failed / retired"]
Status = Literal["In design", "In build", "In certification", "Live", "Live · in revision", "Retired", "Cancelled"]


class ProductRow(_Model):
    urn: str
    name: str
    domain: str
    dpo: str | None = None
    stage: Stage
    status: Status
    lifecycle: Lifecycle
    signal: Literal["red", "orange", "yellow", "green", "grey", "unreported"]
    iteration: int
    gates: list[GateRecord]
    lastGate: GateRecord | None = None
    firstG4Date: str | None = None
    daysInStage: int
    nextGate: PlannedGate | None = None
    plannedGA: PlannedGA | None = None
    inputProducts: list[str]
    consumedByProducts: list[str]
    namedConsumers: int
    activeUsers30d: SourcedNumber | None = None
    firstConsumerDate: SourcedDate | None = None
    validation: ValidationSummary | None = None
    nextdata: NextDataSummary | None = None
    platformDomain: str | None = None
    github: GithubSummary | None = None
    flags: list[ProductFlag]
    dpoComment: str | None = None
    reviewedOn: str | None = None
    cancelledOn: str | None = None


class TrendPoint(_Model):
    quarter: str
    domain: str
    certified: int
    target: int | None


class HealthItem(_Model):
    quarter: str
    scope: str
    status: Literal["ahead", "on-track", "at-risk", "off-track", "above-target", "met-target", "below-target", "no-target"]
    certified: int
    target: int | None
    expected: int | None
    pace: Number | None
    elapsed: Number
    forecast: int
    late: int
    lateUrns: list[str]


class WeeklyPoint(_Model):
    quarter: str
    week: str
    end: str
    certified: int
    byDomain: dict[str, int]


class QuarterProduct(_Model):
    urn: str
    lifecycle: Lifecycle
    status: Status
    lastGate: GateRecord | None = None
    firstG4Date: str | None = None


class QuarterView(_Model):
    quarter: str
    asOfDate: str
    metrics: list[MetricValue]
    products: list[QuarterProduct]


class DataQualityItem(_Model):
    severity: Literal["blocker", "warning"]
    rule: str
    message: str
    urn: str | None = None
    file: str | None = None
    row: int | None = None


class Snapshot(_Model):
    schemaVersion: Literal["1.0"]
    weekId: str
    asOfDate: str
    quarter: str
    generatedAt: str
    signOff: SignOff
    domains: list[DomainInfo]
    sources: list[SourceInfo]
    registry: RegistryInfo
    metrics: list[MetricValue]
    products: list[ProductRow]
    trend: list[TrendPoint]
    changes: list[str]
    dataQuality: list[DataQualityItem]
    reporting: list[ReportingItem] | None = None
    health: list[HealthItem] | None = None
    weekly: list[WeeklyPoint] | None = None
    quarters: list[QuarterView] | None = None
    delivery: Delivery | None = None


# Fields that stay in the JSON even when null (required + nullable in the schema).
NULLABLE_REQUIRED = {MetricValue: {"value"}, TrendPoint: {"target"}, HealthItem: {"target", "expected", "pace"}}
