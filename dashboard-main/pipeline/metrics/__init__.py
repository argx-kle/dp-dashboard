"""Metric functions. Each takes (ctx, scope) and returns a MetricResult.

A function never reads the registry; the registry decides where and how its result is shown.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from statistics import median as _median


@dataclass
class MetricResult:
    value: float | None
    n: int | None = None
    values: list[float] | None = None
    urns: list[str] = field(default_factory=list)
    reason: str | None = None


def median_result(pairs: list[tuple[str, float]], empty_reason: str) -> MetricResult:
    """pairs: (urn, value). Returns the median with n, raw values and urns."""
    if not pairs:
        return MetricResult(None, n=0, values=[], urns=[], reason=empty_reason)
    values = [_tidy(v) for _, v in pairs]
    m = _tidy(_median(values))
    return MetricResult(m, n=len(values), values=sorted(values), urns=sorted(u for u, _ in pairs))


def _tidy(v: float) -> float | int:
    return int(v) if float(v).is_integer() else round(float(v), 1)


def count_result(urns: list[str]) -> MetricResult:
    return MetricResult(len(urns), n=len(urns), urns=sorted(urns))


def share_result(numerator: list[str], denominator: int, empty_reason: str) -> MetricResult:
    if denominator == 0:
        return MetricResult(None, n=0, urns=[], reason=empty_reason)
    return MetricResult(round(len(numerator) / denominator, 4), n=denominator, urns=sorted(numerator))
