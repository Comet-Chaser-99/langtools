# Implementation status and handoff

Owner of this initial implementation: @jaas29. Tracking: [issue #9](https://github.com/mhulden/langtools/issues/9). Branch: `praat/initial-workflow`.

Work in progress: Python package and CI; Sound/time model; WAV adapters and waveform summaries; TextGrid model/codec and annotation commands; shared workspace/CLI; basic Qt editor. The draft PR is the authoritative list of current changes. Check it before starting overlapping work.

The canonical requirements remain in `../REIMPLEMENTATION.md`. This file tracks implementation, not a replacement specification. R1 is not complete; no oracle parity is claimed.

## Follow-up work available

- Pin and capture the reference executable; resolve D03 and other runtime discrepancies.
- Acoustic analysis: Gaussian spectrogram, filtered-AC pitch, Burg formants and intensity. Agree result/settings types before implementation.
- Advanced annotation gestures, search and playback timing; build on the shared command layer.
- Project recovery, packaged distributions and accessibility/manual platform checks.

Claim a small issue with acceptance criteria, name the modules/interfaces affected, and open a linked draft PR early. Other students should branch from upstream main after this foundation merges, or explicitly coordinate a dependency on this branch. Do not copy modules between forks or create a second TextGrid serializer.
