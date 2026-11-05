"""Immutable annotation geometry, independent of codecs and GUI (§11)."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from uuid import uuid4

from ..errors import InvalidInput
from .time import domain


def new_id() -> str:
    return str(uuid4())


@dataclass(frozen=True)
class Interval:
    xmin: float
    xmax: float
    label: str = ""
    id: str = field(default_factory=new_id)

    def __post_init__(self) -> None:
        domain(self.xmin, self.xmax)


@dataclass(frozen=True)
class Point:
    time: float
    label: str = ""
    id: str = field(default_factory=new_id)

    def __post_init__(self) -> None:
        if not math.isfinite(self.time):
            raise InvalidInput("Point time must be finite.")


@dataclass(frozen=True)
class IntervalTier:
    name: str
    xmin: float
    xmax: float
    intervals: tuple[Interval, ...]
    id: str = field(default_factory=new_id)

    def __post_init__(self) -> None:
        domain(self.xmin, self.xmax)
        object.__setattr__(self, "intervals", tuple(self.intervals))
        if not self.intervals:
            raise InvalidInput("Interval tiers require at least one interval.")
        for left, right in zip(self.intervals, self.intervals[1:], strict=False):
            if left.xmax != right.xmin:
                raise InvalidInput("Intervals must be exactly adjacent without gaps or overlaps.")


@dataclass(frozen=True)
class PointTier:
    name: str
    xmin: float
    xmax: float
    points: tuple[Point, ...] = ()
    id: str = field(default_factory=new_id)

    def __post_init__(self) -> None:
        domain(self.xmin, self.xmax)
        object.__setattr__(self, "points", tuple(self.points))
        for left, right in zip(self.points, self.points[1:], strict=False):
            if left.time >= right.time:
                raise InvalidInput(
                    "Point times must be strictly increasing; duplicates are invalid."
                )


type Tier = IntervalTier | PointTier


@dataclass(frozen=True)
class TextGrid:
    name: str
    xmin: float
    xmax: float
    tiers: tuple[Tier, ...] = ()
    id: str = field(default_factory=new_id)
    revision: int = 0
    kind: str = field(default="TextGrid", init=False)

    def __post_init__(self) -> None:
        domain(self.xmin, self.xmax)
        object.__setattr__(self, "tiers", tuple(self.tiers))
        ids = [self.id]
        for tier in self.tiers:
            ids.append(tier.id)
            entities = tier.intervals if isinstance(tier, IntervalTier) else tier.points
            ids.extend(entity.id for entity in entities)
        if len(ids) != len(set(ids)):
            raise InvalidInput("Annotation IDs must be unique, even when names are duplicated.")

    @classmethod
    def create(
        cls, name: str, xmin: float, xmax: float, tiers: tuple[tuple[str, str], ...]
    ) -> TextGrid:
        result = []
        for tier_name, kind in tiers:
            if kind == "interval":
                result.append(IntervalTier(tier_name, xmin, xmax, (Interval(xmin, xmax),)))
            elif kind == "point":
                result.append(PointTier(tier_name, xmin, xmax))
            else:
                raise InvalidInput(f"Unknown tier kind: {kind}")
        return cls(name, xmin, xmax, tuple(result))

    def domain_warnings(self) -> tuple[str, ...]:
        warnings = []
        for tier in self.tiers:
            if (tier.xmin, tier.xmax) != (self.xmin, self.xmax):
                warnings.append(f"Tier {tier.name!r} has a different domain from its grid.")
            if isinstance(tier, IntervalTier) and (
                tier.intervals[0].xmin != tier.xmin or tier.intervals[-1].xmax != tier.xmax
            ):
                warnings.append(f"Intervals on {tier.name!r} do not cover its declared domain.")
            if isinstance(tier, PointTier) and any(
                p.time < tier.xmin or p.time > tier.xmax for p in tier.points
            ):
                warnings.append(f"Points on {tier.name!r} lie outside its declared domain.")
        return tuple(warnings)
