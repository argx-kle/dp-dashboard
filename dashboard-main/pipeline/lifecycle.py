"""Lifecycle derivation: gate events -> stage, status, iteration, first G4, days in stage.

Rules are in docs/metric-definitions.md, section "Status mapping".
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from pipeline.contracts import GATES, GateEvent, Product

GATE_INDEX = {g: i + 1 for i, g in enumerate(GATES)}

STAGE_BY_GATE = {
    None: "Inception",
    "G1": "Discovery",
    "G2": "Design/Develop",
    "G3": "Test/Launch",
    "G4": "Operate/Support",
    "G6": "Retire",
}
STATUS_BY_GATE = {
    None: "In design",
    "G1": "In design",
    "G2": "In build",
    "G3": "In certification",
    "G4": "Live",
    "G6": "Retired",
}
PIPELINE_STATUSES = {"In design", "In build", "In certification"}

# The six business stages the executive views use instead of gate codes (docs/metric-definitions.md,
# "Lifecycle stages"). Ideation is a registered product that has not passed G1 Intake.
LIFECYCLE_STAGES = ["Ideation", "In design", "In development", "In testing", "Live", "Failed / retired"]
LIFECYCLE_BY_STATUS = {
    "In design": "In design",
    "In build": "In development",
    "In certification": "In testing",
    "Live": "Live",
    "Live · in revision": "Live",
    "Retired": "Failed / retired",
    "Cancelled": "Failed / retired",
}
GATE_NAMES = {"G1": "Intake", "G2": "Contract", "G3": "Build", "G4": "Certify", "G5": "Revise", "G6": "Retire"}

# The stage a product reaches when it passes each gate, for "Live was due 20 Sep" style reasons.
LIFECYCLE_AFTER_GATE = {"G1": "In design", "G2": "In development", "G3": "In testing", "G4": "Live", "G5": "In design", "G6": "Failed / retired"}
LIVE_STATUSES = {"Live", "Live · in revision"}


@dataclass
class GateRec:
    gate: str
    date: date
    iteration: int
    g5_path: str | None = None
    evidence_url: str | None = None


@dataclass
class Derived:
    urn: str
    gates: list[GateRec] = field(default_factory=list)
    stage: str = "Inception"
    status: str = "In design"
    iteration: int = 1
    first_g4: date | None = None
    last_g1: date | None = None
    days_in_stage: int = 0

    @property
    def last_gate(self) -> GateRec | None:
        return self.gates[-1] if self.gates else None

    @property
    def active(self) -> bool:
        return self.status not in {"Retired", "Cancelled"}

    @property
    def live(self) -> bool:
        return self.status in LIVE_STATUSES

    @property
    def in_pipeline(self) -> bool:
        return self.status in PIPELINE_STATUSES

    @property
    def lifecycle(self) -> str:
        if self.status == "In design" and not self.gates:
            return "Ideation"
        return LIFECYCLE_BY_STATUS[self.status]

    @property
    def g1_date(self) -> date | None:
        for g in self.gates:
            if g.gate == "G1":
                return g.date
        return None

    @property
    def passed_gates(self) -> set[str]:
        return {g.gate for g in self.gates}

    def next_gate(self) -> str | None:
        """The gate the product is working towards, or None once Live/Retired/Cancelled."""
        if not self.active:
            return None
        last = self.last_gate
        if last is None:
            return "G1"
        if last.gate == "G4":
            return None
        if last.gate == "G5":
            return "G2"
        idx = GATE_INDEX[last.gate]
        return GATES[idx] if idx < 4 else None


def sort_events(events: list[GateEvent]) -> list[GateEvent]:
    return sorted(events, key=lambda e: (e.date_passed, GATE_INDEX[e.gate]))


def derive(product: Product, events: list[GateEvent], as_of: date) -> Derived:
    d = Derived(urn=product.urn)
    iteration = 1
    had_g4 = False
    for e in sort_events(events):
        if e.gate == "G5":
            iteration += 1
        rec = GateRec(e.gate, e.date_passed, iteration, e.g5_path, e.evidence_url)
        d.gates.append(rec)
        if e.gate == "G4":
            had_g4 = True
            if d.first_g4 is None or e.date_passed < d.first_g4:
                d.first_g4 = e.date_passed
    d.iteration = iteration

    last = d.last_gate
    if last is None:
        d.stage, d.status = "Inception", "In design"
    elif last.gate == "G5":
        d.stage = "Discovery" if (last.g5_path or "scope change") == "scope change" else "Design/Develop"
        d.status = "Live · in revision" if had_g4 else "In design"
    elif last.gate in ("G2", "G3") and iteration > 1 and had_g4:
        d.stage = STAGE_BY_GATE[last.gate]
        d.status = "Live · in revision"
    else:
        d.stage = STAGE_BY_GATE[last.gate]
        d.status = STATUS_BY_GATE[last.gate]

    if product.cancelled_on is not None:
        d.status = "Cancelled"

    anchor = last.date if last else None
    d.days_in_stage = max(0, (as_of - anchor).days) if anchor else 0
    return d
