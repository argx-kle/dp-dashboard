"""Assemble and validate the snapshot. Validation uses schema/snapshot.schema.json, nothing else."""

from __future__ import annotations

import json
from datetime import date
from functools import lru_cache
from typing import Any

from jsonschema import Draft7Validator

from pipeline import SCHEMA_PATH
from pipeline.contracts import NULLABLE_REQUIRED, DQItem, HealthItem, MetricValue, Snapshot, TrendPoint


@lru_cache(maxsize=1)
def load_schema() -> dict:
    with open(SCHEMA_PATH, encoding="utf-8") as fh:
        return json.load(fh)


def _strip_none(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _strip_none(v) for k, v in obj.items() if v is not None}
    if isinstance(obj, list):
        return [_strip_none(v) for v in obj]
    return obj


def to_json_dict(snapshot: Snapshot) -> dict:
    """Snapshot -> plain dict matching the schema: optional nulls dropped, required nulls kept."""
    data = _strip_none(snapshot.model_dump())
    for m in data["metrics"]:
        for k in NULLABLE_REQUIRED[MetricValue]:
            m.setdefault(k, None)
    for t in data["trend"]:
        for k in NULLABLE_REQUIRED[TrendPoint]:
            t.setdefault(k, None)
    for h in data.get("health") or []:
        for k in NULLABLE_REQUIRED[HealthItem]:
            h.setdefault(k, None)
    for q in data.get("quarters") or []:
        for m in q["metrics"]:
            for k in NULLABLE_REQUIRED[MetricValue]:
                m.setdefault(k, None)
    return data


def validate(data: dict) -> list[DQItem]:
    validator = Draft7Validator(load_schema())
    issues = []
    for err in sorted(validator.iter_errors(data), key=lambda e: list(e.absolute_path)):
        path = "/".join(str(p) for p in err.absolute_path) or "(root)"
        issues.append(DQItem("blocker", "SCHEMA", f"{path}: {err.message}"))
    return issues


def dq_to_model(items: list[DQItem]) -> list[dict]:
    return [
        {k: v for k, v in {"severity": i.severity, "rule": i.rule, "message": i.message, "urn": i.urn, "file": i.file, "row": i.row}.items() if v is not None}
        for i in items
    ]


def dumps(data: dict) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False, default=_json_default)


def _json_default(o):
    if isinstance(o, date):
        return o.isoformat()
    raise TypeError(f"Not serialisable: {type(o).__name__}")
