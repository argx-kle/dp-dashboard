"""The state folder: approved snapshots and plan baselines. Written only by dp."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Baseline:
    urn: str
    field: str  # a gate id (G1..G6) for the next-gate plan, or "GA"
    baseline_date: str
    first_seen_week: str


class State:
    def __init__(self, state_dir: Path):
        self.dir = state_dir
        self.snapshots_dir = state_dir / "snapshots"
        self.baselines_path = state_dir / "baselines.csv"
        self.baselines: dict[tuple[str, str], Baseline] = {}
        if self.baselines_path.exists():
            with open(self.baselines_path, encoding="utf-8", newline="") as fh:
                for row in csv.DictReader(fh):
                    b = Baseline(row["urn"], row["field"], row["baseline_date"], row["first_seen_week"])
                    self.baselines[(b.urn, b.field)] = b

    # --- snapshots ----------------------------------------------------------
    def approved_weeks(self) -> list[str]:
        if not self.snapshots_dir.exists():
            return []
        return sorted(p.stem for p in self.snapshots_dir.glob("*.json"))

    def latest_approved_before(self, week_id: str) -> dict | None:
        weeks = [w for w in self.approved_weeks() if w < week_id]
        if not weeks:
            return None
        with open(self.snapshots_dir / f"{weeks[-1]}.json", encoding="utf-8") as fh:
            return json.load(fh)

    def save_approved(self, snapshot: dict) -> Path:
        self.snapshots_dir.mkdir(parents=True, exist_ok=True)
        path = self.snapshots_dir / f"{snapshot['weekId']}.json"
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(snapshot, fh, indent=2, ensure_ascii=False)
        return path

    # --- baselines ----------------------------------------------------------
    def baseline(self, urn: str, field: str) -> Baseline | None:
        return self.baselines.get((urn, field))

    def record_baselines(self, snapshot: dict) -> int:
        """Write the first plan seen for each (urn, gate) and (urn, GA). Returns the number added."""
        added = 0
        week = snapshot["weekId"]
        for p in snapshot["products"]:
            ng = p.get("nextGate")
            if ng and (p["urn"], ng["gate"]) not in self.baselines:
                self.baselines[(p["urn"], ng["gate"])] = Baseline(p["urn"], ng["gate"], ng["plannedDate"], week)
                added += 1
            ga = p.get("plannedGA")
            if ga and (p["urn"], "GA") not in self.baselines:
                self.baselines[(p["urn"], "GA")] = Baseline(p["urn"], "GA", ga["plannedDate"], week)
                added += 1
        self.dir.mkdir(parents=True, exist_ok=True)
        with open(self.baselines_path, "w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["urn", "field", "baseline_date", "first_seen_week"])
            for b in sorted(self.baselines.values(), key=lambda b: (b.urn, b.field)):
                w.writerow([b.urn, b.field, b.baseline_date, b.first_seen_week])
        return added
