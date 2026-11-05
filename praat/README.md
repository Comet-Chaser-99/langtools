# Praat workflow prototype

Independent Python implementation following [the master specification](REIMPLEMENTATION.md).
This milestone supports WAV inspection/waveforms and TextGrid editing/interchange. It is
not the complete R1 application and has not been validated against a pinned Praat runtime.

## Run

Install [uv](https://docs.astral.sh/uv/) and Python 3.12 or 3.13, then from this directory:

```bash
uv sync --locked --extra gui
uv run langtools-praat gui
```

Open a mono/stereo PCM WAV, select it, and choose **New TextGrid**. Select a TextGrid
to edit its labels in the table; choose an audio object and then the TextGrid to show
both. Audio and annotations keep their own time domains. Drag the shaded waveform
selection or select a table row. Insert a boundary/point, edit labels, undo/redo, and
save a text TextGrid. Audio playback and acoustic analysis are follow-up work.

![Initial waveform and annotation workspace](docs/screenshots/initial-workflow.png)

For an original synthetic demo:

```bash
uv run python examples/make_demo.py demo-output
uv run langtools-praat gui demo-output/synthetic.wav demo-output/synthetic.TextGrid
```

Headless use (GUI dependencies are optional):

```bash
uv sync --locked
uv run langtools-praat inspect recording.wav
uv run langtools-praat new-textgrid recording.wav labels.TextGrid --interval-tier words --point-tier events
uv run langtools-praat inspect labels.TextGrid
uv run langtools-praat convert-textgrid labels.TextGrid short.TextGrid --short
uv run langtools-praat set-label labels.TextGrid edited.TextGrid --tier 1 --item 1 --label "ʔaɦɔj"
uv run langtools-praat export-annotations edited.TextGrid labels.csv
```

Outputs are not overwritten unless `--overwrite` is passed. GUI saving asks before
replacement. TextGrid saving is atomic; save failure retains the previous target.

## Develop

```bash
uv sync --locked --extra gui
uv run ruff check .
uv run ruff format --check .
uv run pytest
```

GUI tests use Qt's offscreen platform; no microphone, sound device or reference
Praat installation is needed. CI runs Python 3.12 on Linux, Windows and macOS,
plus Python 3.13 on Linux. OS/device behavior still needs manual verification.

See [implementation status and ownership](docs/IMPLEMENTATION_STATUS.md),
[interface contracts](docs/INTERFACES.md), and [compatibility limits](docs/COMPATIBILITY.md)
before starting another task. Claim an issue and open a draft PR early.
