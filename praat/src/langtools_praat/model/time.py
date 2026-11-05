"""Sample centers and declared domains are distinct (master specification §4)."""

from __future__ import annotations

import math
from dataclasses import dataclass

from ..errors import InvalidInput


def domain(xmin: float, xmax: float) -> None:
    if not math.isfinite(xmin) or not math.isfinite(xmax) or xmin >= xmax:
        raise InvalidInput("Time domain must have finite bounds with xmin < xmax.")


@dataclass(frozen=True)
class SampledAxis:
    xmin: float
    xmax: float
    nx: int
    dx: float
    x1: float

    def __post_init__(self) -> None:
        domain(self.xmin, self.xmax)
        if type(self.nx) is not int or self.nx < 1:
            raise InvalidInput("A sampled axis requires a positive integer sample count.")
        if not math.isfinite(self.dx) or self.dx <= 0 or not math.isfinite(self.x1):
            raise InvalidInput("Sampling period must be positive; sample origin must be finite.")
        if self.x1 < self.xmin or self.x1 + (self.nx - 1) * self.dx > self.xmax:
            raise InvalidInput("Sample centers must lie in the declared time domain.")

    @classmethod
    def recording(cls, frames: int, sample_rate: float, xmin: float = 0.0) -> SampledAxis:
        if not math.isfinite(sample_rate) or sample_rate <= 0:
            raise InvalidInput("Sample rate must be finite and positive.")
        dx = 1.0 / sample_rate
        return cls(xmin, xmin + frames * dx, frames, dx, xmin + dx / 2)

    @property
    def sample_rate(self) -> float:
        return 1.0 / self.dx

    def time(self, sample_number: float) -> float:
        """One-based, potentially fractional public sample number; no implicit rounding."""
        if not math.isfinite(sample_number):
            raise InvalidInput("Sample number must be finite.")
        return self.x1 + (sample_number - 1) * self.dx

    def sample_number(self, time: float) -> float:
        if not math.isfinite(time):
            raise InvalidInput("Time must be finite.")
        return 1 + (time - self.x1) / self.dx

    def frame_range(self, start: float, end: float) -> tuple[int, int]:
        """Zero-based slice for centers in [start, end); this project's range convention.

        Domain bounds clip the selection. Sample-position values within 1e-9 of an
        integer are snapped to that integer to absorb floating-point conversion error.
        This is not a claim about every Praat command's rounding convention.
        """
        if not math.isfinite(start) or not math.isfinite(end) or start > end:
            raise InvalidInput("Selection needs finite ordered bounds.")

        def boundary(time: float) -> int:
            position = (time - self.x1) / self.dx
            nearest = round(position)
            if abs(position - nearest) <= 1e-9:
                position = nearest
            return max(0, min(self.nx, math.ceil(position)))

        return boundary(start), boundary(end)
