"""Generate original synthetic audio and annotations; no external corpus required.

Run: uv run python examples/make_demo.py /path/to/empty/output-directory
"""

import sys
from pathlib import Path

import numpy as np

from langtools_praat.io.audio import write_wav
from langtools_praat.io.textgrid import write
from langtools_praat.model.sound import Sound
from langtools_praat.model.textgrid import Interval, IntervalTier, Point, PointTier, TextGrid
from langtools_praat.model.time import SampledAxis


def main():
    output = Path(sys.argv[1])
    output.mkdir(parents=True, exist_ok=True)
    axis = SampledAxis.recording(96000, 48000)
    times = axis.x1 + np.arange(axis.nx) * axis.dx
    envelope = np.sin(np.pi * times / 2) ** 2
    tone = 0.6 * envelope * np.sin(2 * np.pi * 220 * times)
    write_wav(output / "synthetic.wav", Sound("synthetic", axis, tone[None, :]))
    grid = TextGrid(
        "synthetic",
        0,
        2,
        (
            IntervalTier(
                "segments",
                0,
                2,
                (
                    Interval(0, 0.5, "onset"),
                    Interval(0.5, 1.5, "synthetic tone"),
                    Interval(1.5, 2, "offset"),
                ),
            ),
            IntervalTier("Unicode labels", 0, 2, (Interval(0, 2, "IPA: ɲ ʔ ɑː · e\u0301"),)),
            PointTier("events", 0, 2, (Point(1, "peak envelope"),)),
        ),
    )
    write(output / "synthetic.TextGrid", grid)
    print(f"Created original synthetic demo in {output}")


if __name__ == "__main__":
    main()
