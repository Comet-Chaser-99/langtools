"""Intensity contour (``Sound: To Intensity...``) and its averaging queries (spec §9).

``to_intensity`` follows the reference's documented rules:

- Logical window 3.2 / pitch floor; physical window twice that. The default time
  step is a quarter of the logical window (0.8 / pitch floor).
- Short-term grid: ``1 + floor((N dx - physical) / step)`` frames, centred in the
  analysed part. Each frame uses the sample nearest its time as the window centre,
  with ``floor(physical / 2 / dx)`` samples on either side, clipped to the part.
- Window ``I0((2 pi^2 + 0.5) sqrt(1 - x^2))`` (Kaiser, beta ~ 20.2), with ``I0`` the
  Abramowitz & Stegun 9.8.1/9.8.2 polynomial approximation.
- With ``subtract_mean`` the window segment's own mean is removed per channel before
  squaring (a local mean, not a global DC removal).
- ``P = sum_ch sum(x^2 w) / sum_ch sum(w)``: channel energies are pooled, so
  ``ChannelPolicy.combined()`` gives the mean of the per-channel powers.
- dB re (2e-5 Pa)^2; a relative power below 1e-30 is -300 dB. Silence is therefore a
  finite -300 dB, not undefined, as in the reference.

``average`` reproduces ``Intensity: Get mean...`` (energy, sones, dB: the area under the
linearly interpolated curve in that unit, divided by the defined range) and the
median (``Get quantile`` at 0.5). Undefined (NaN) frames are skipped by both.

Numerical parity with the reference is unverified until oracle capture.
"""

from __future__ import annotations

import math
from enum import StrEnum

import numpy as np
from numpy.typing import NDArray

from ..errors import InvalidInput
from ..model.sound import Sound
from ..model.time import SampledAxis
from .contracts import (
    Algorithm,
    AnalysisKind,
    AnalysisRequest,
    ChannelMode,
    Intensity,
    IntensitySettings,
    Provenance,
)
from .spectrogram import _part

ALGORITHM = Algorithm("intensity.kaiser-mean-square", "1")
PERIODS_PER_WINDOW = 3.2
DEFAULT_OVERSAMPLING = 4.0
KAISER_BETA = 2.0 * math.pi * math.pi + 0.5
HEARING_THRESHOLD_PA2 = 2.0e-5 * 2.0e-5
SILENCE_DB = -300.0
_FRAMES_PER_BLOCK = 256


def bessel_i0(x: NDArray[np.float64]) -> NDArray[np.float64]:
    """Modified Bessel I0, Abramowitz & Stegun 9.8.1 / 9.8.2 (relative error < 2e-7)."""
    x = np.abs(np.asarray(x, dtype=np.float64))
    small = x < 3.75
    t = np.where(small, x / 3.75, 1.0) ** 2
    low = 1.0 + t * (
        3.5156229
        + t * (3.0899424 + t * (1.2067492 + t * (0.2659732 + t * (0.0360768 + t * 0.0045813))))
    )
    big = np.where(small, 3.75, x)
    u = 3.75 / big
    poly = 0.39894228 + u * (
        0.01328592
        + u
        * (
            0.00225319
            + u
            * (
                -0.00157565
                + u
                * (
                    0.00916281
                    + u * (-0.02057706 + u * (0.02635537 + u * (-0.01647633 + u * 0.00392377)))
                )
            )
        )
    )
    high = np.exp(big) / np.sqrt(big) * poly
    return np.where(small, low, high)


def kaiser_window(half_samples: int, dx: float, half_duration: float) -> NDArray[np.float64]:
    """The 2 * half_samples + 1 window weights, centre sample in the middle."""
    x = np.arange(-half_samples, half_samples + 1, dtype=np.float64) * dx / half_duration
    return bessel_i0(KAISER_BETA * np.sqrt(np.maximum(0.0, 1.0 - x * x)))


def _to_db(power: NDArray[np.float64]) -> NDArray[np.float64]:
    relative = power / HEARING_THRESHOLD_PA2
    with np.errstate(divide="ignore"):
        db = 10.0 * np.log10(np.maximum(relative, 1e-300))
    return np.where(relative < 1.0e-30, SILENCE_DB, db)


def to_intensity(sound: Sound, request: AnalysisRequest) -> Intensity:
    """Compute an Intensity contour for ``request`` over ``sound``.

    Channel rule for ``ChannelPolicy.combined()``: channel energies are pooled, i.e.
    the mean of the per-channel windowed powers.
    """
    settings = request.settings
    if request.kind is not AnalysisKind.INTENSITY or not isinstance(settings, IntensitySettings):
        raise InvalidInput("This request is not an intensity request.")
    if request.source_id != sound.id or request.revision != sound.revision:
        raise InvalidInput("The request does not describe this sound revision.")
    request.channels.check(sound.channels)
    axis, samples = _part(sound, request.time_range.start, request.time_range.end)
    if request.channels.mode is ChannelMode.SINGLE:
        samples = samples[request.channels.channel : request.channels.channel + 1]

    dx = axis.dx
    logical = PERIODS_PER_WINDOW * (1.0 / settings.pitch_floor)  # same rounding as the reference
    time_step = settings.time_step if settings.time_step else logical / DEFAULT_OVERSAMPLING
    physical = 2.0 * logical
    duration = dx * axis.nx
    if physical > duration:
        raise InvalidInput(
            "The sound is too short for this pitch floor: it must be at least "
            f"6.4 / pitch floor = {physical:.6g} s long."
        )
    frames = 1 + math.floor((duration - physical) / time_step)
    mid = axis.x1 - 0.5 * dx + 0.5 * duration
    t1 = mid - 0.5 * frames * time_step + 0.5 * time_step

    half_duration = 0.5 * physical
    half = math.floor(half_duration / dx)
    window = kaiser_window(half, dx, half_duration)

    times = t1 + np.arange(frames) * time_step
    centres = np.floor((times - axis.x1) / dx + 0.5).astype(np.int64)  # nearest sample
    power = np.empty(frames, dtype=np.float64)
    inside = (centres - half >= 0) & (centres + half <= axis.nx - 1)

    offsets = np.arange(-half, half + 1)
    full = np.flatnonzero(inside)
    for begin in range(0, full.size, _FRAMES_PER_BLOCK):
        rows = full[begin : begin + _FRAMES_PER_BLOCK]
        index = centres[rows, None] + offsets[None, :]
        energy = np.zeros(rows.size)
        for channel in samples:
            segment = channel[index]
            if settings.subtract_mean:
                segment = segment - segment.mean(axis=1, keepdims=True)
            energy += (segment * segment) @ window
        power[rows] = energy / (samples.shape[0] * float(window.sum()))

    for row in np.flatnonzero(~inside):  # edge frames: window clipped to the part
        left = max(0, int(centres[row]) - half)
        right = min(axis.nx - 1, int(centres[row]) + half)
        if right < left:
            raise InvalidInput("Analysis frames do not fit inside the sound.")
        weights = window[left - (int(centres[row]) - half) : right - (int(centres[row]) - half) + 1]
        energy = 0.0
        for channel in samples:
            segment = channel[left : right + 1]
            if settings.subtract_mean:
                segment = segment - segment.mean()
            energy += float((segment * segment) @ weights)
        power[row] = energy / (samples.shape[0] * float(weights.sum()))
    time_axis = SampledAxis(axis.xmin, axis.xmax, frames, time_step, t1)
    return Intensity(Provenance(request, ALGORITHM), time_axis, _to_db(power))


# ---------------------------------------------------------------------------
# Queries (``Intensity: Get mean...`` and the median)


class Averaging(StrEnum):
    """``Intensity: Get mean...`` averaging methods (reference unit codes 1, 2, 3; median 0)."""

    ENERGY = "energy"
    SONES = "sones"
    DB = "dB"
    MEDIAN = "median"


def _to_unit(db: NDArray[np.float64], method: Averaging) -> NDArray[np.float64]:
    if method is Averaging.ENERGY:
        return np.power(10.0, 0.1 * db)
    if method is Averaging.SONES:
        return np.power(2.0, 0.1 * db)
    return db


def _from_unit(value: float, method: Averaging) -> float:
    if not math.isfinite(value):
        return math.nan
    if method is Averaging.ENERGY:
        return 10.0 * math.log10(value)
    if method is Averaging.SONES:
        return 10.0 * math.log2(value)
    return value


def _domain_window(intensity: Intensity, start: float, end: float) -> tuple[float, float] | None:
    """Reference auto-window (start >= end means the whole object), then domain intersection."""
    axis = intensity.time
    if start >= end:
        start, end = axis.xmin, axis.xmax
    start, end = max(start, axis.xmin), min(end, axis.xmax)
    if end <= start:
        return None
    return start, end


def _window_samples(intensity: Intensity, start: float, end: float) -> tuple[int, int]:
    """One-based [imin, imax] of frames whose times lie in [start, end] (may be empty)."""
    axis = intensity.time
    imin = 1 + math.ceil((start - axis.x1) / axis.dx)
    imax = 1 + math.floor((end - axis.x1) / axis.dx)
    return max(imin, 1), min(imax, axis.nx)


def _pieces(values: NDArray[np.float64], axis: SampledAxis) -> tuple[NDArray[np.float64], ...]:
    """Linear pieces (a, b, value at a, value at b) of the contour's defined curve.

    Between two defined frames the curve is the straight line joining them. A
    defined frame next to an undefined one, or at either end of the grid, holds its
    value for half a frame step on that side. Nothing else is defined.
    """
    dx, n = axis.dx, axis.nx
    t = axis.x1 + np.arange(n) * dx
    ok = ~np.isnan(values)
    a, b, va, vb = [], [], [], []

    def add(lo, hi, vlo, vhi):
        a.append(lo)
        b.append(hi)
        va.append(vlo)
        vb.append(vhi)

    both = ok[:-1] & ok[1:]
    add(t[:-1][both], t[1:][both], values[:-1][both], values[1:][both])
    right_only_left = ok[:-1] & ~ok[1:]  # defined frame, undefined successor
    add(
        t[:-1][right_only_left],
        t[:-1][right_only_left] + 0.5 * dx,
        values[:-1][right_only_left],
        values[:-1][right_only_left],
    )
    left_only_right = ~ok[:-1] & ok[1:]  # undefined frame, defined successor
    add(
        t[1:][left_only_right] - 0.5 * dx,
        t[1:][left_only_right],
        values[1:][left_only_right],
        values[1:][left_only_right],
    )
    if ok[0]:
        add(np.array([t[0] - 0.5 * dx]), t[:1], values[:1], values[:1])
    if ok[-1]:
        add(t[-1:], np.array([t[-1] + 0.5 * dx]), values[-1:], values[-1:])
    return tuple(np.concatenate(part) for part in (a, b, va, vb))


def _interpolated_mean(
    values: NDArray[np.float64], intensity: Intensity, start: float, end: float
) -> float:
    """Area under the defined curve within [start, end], divided by its defined length."""
    a, b, va, vb = _pieces(values, intensity.time)
    lo, hi = np.maximum(a, start), np.minimum(b, end)
    keep = hi > lo
    if not keep.any():
        return math.nan
    a, b, va, vb, lo, hi = a[keep], b[keep], va[keep], vb[keep], lo[keep], hi[keep]
    slope = np.where(b > a, (vb - va) / (b - a), 0.0)
    area = (hi - lo) * (va + slope * (0.5 * (lo + hi) - a))  # line value at the midpoint
    return float(area.sum() / (hi - lo).sum())


def _quantile(sorted_values: NDArray[np.float64], factor: float) -> float:
    size = sorted_values.size
    if size < 1:
        return math.nan
    if size == 1:
        return float(sorted_values[0])
    place = factor * size + 0.5
    left = min(max(math.floor(place), 1), size - 1)
    low, high = float(sorted_values[left - 1]), float(sorted_values[left])
    if high == low:
        return low
    return low + (place - left) * (high - low)


def average(
    intensity: Intensity,
    method: Averaging,
    time_range: tuple[float, float] = (0.0, 0.0),
) -> float:
    """``Get mean...`` in dB for ``method`` over ``time_range``; NaN if nothing is defined.

    As in the reference, ``start >= end`` means the whole object, and the range is
    intersected with the object's domain. The median uses the frames whose times lie
    in the range; the means use the interpolated area described above.
    """
    method = Averaging(method)
    start, end = float(time_range[0]), float(time_range[1])
    if math.isnan(start) or math.isnan(end):
        raise InvalidInput("The time range must not be NaN.")
    window = _domain_window(intensity, start, end)
    if window is None:
        return math.nan
    start, end = window
    if method is Averaging.MEDIAN:
        imin, imax = _window_samples(intensity, start, end)
        part = intensity.values[imin - 1 : imax] if imin <= imax else intensity.values[:0]
        return _quantile(np.sort(part[~np.isnan(part)]), 0.5)
    mean = _interpolated_mean(_to_unit(np.asarray(intensity.values), method), intensity, start, end)
    return _from_unit(mean, method)
