"""Peak-preserving waveform summaries bounded by viewport width and block size."""

from dataclasses import dataclass
from threading import Event

import numpy as np
from numpy.typing import NDArray

from ..errors import Cancelled, InvalidInput
from ..io.audio import AudioFile


@dataclass(frozen=True)
class Waveform:
    times: NDArray[np.float64]
    minimum: NDArray[np.float64]
    maximum: NDArray[np.float64]


def summarize(
    source: AudioFile,
    start: float,
    end: float,
    *,
    channel: int = 0,
    pixels: int = 1000,
    cancellation: Event | None = None,
) -> Waveform:
    """Channel is zero-based. Empty selections return empty arrays, never fake silence."""
    if type(channel) is not int or not 0 <= channel < source.channels:
        raise InvalidInput("Channel index is outside this recording.")
    if type(pixels) is not int or not 1 <= pixels <= 16_384:
        raise InvalidInput("Waveform width must be between 1 and 16384 pixels.")
    first, last = source.axis.frame_range(start, end)
    if first == last:
        return Waveform(np.array([]), np.array([]), np.array([]))
    bins = min(pixels, last - first)
    edges = np.linspace(first, last, bins + 1, dtype=np.int64)
    minima, maxima = np.full(bins, np.inf), np.full(bins, -np.inf)
    # One file read per block, not per pixel; peak allocations are O(block + pixels).
    for begin in range(first, last, 65_536):
        if cancellation is not None and cancellation.is_set():
            raise Cancelled("Waveform cancelled.")
        stop = min(begin + 65_536, last)
        values = source.read_frames(begin, stop - begin, cancellation)[channel]
        left_bin = max(0, int(np.searchsorted(edges, begin, side="right")) - 1)
        right_bin = min(bins, int(np.searchsorted(edges, stop, side="left")))
        for bucket in range(left_bin, right_bin):
            lo, hi = max(begin, edges[bucket]), min(stop, edges[bucket + 1])
            segment = values[lo - begin : hi - begin]
            if segment.size:
                minima[bucket] = min(minima[bucket], float(segment.min()))
                maxima[bucket] = max(maxima[bucket], float(segment.max()))
    times = source.axis.x1 + (edges[:-1] + edges[1:] - 1) * 0.5 * source.axis.dx
    return Waveform(times, minima, maxima)
