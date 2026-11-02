# Praat Reimplementation Plan

**Course repository:** [mhulden/langtools](https://github.com/mhulden/langtools)  
**Target directory:** `praat/`  
**Prepared:** 2026-11-02  
**Status:** Research-backed proposal for merging three students' contributions. No implementation is included, and proposed choices are not yet team decisions.

## 1. Goal and constraints

Build an independent, cross-platform speech analysis and annotation application that reproduces documented Praat behavior for a declared feature subset. Praat supports acoustic analysis, annotation, speech synthesis and manipulation, scripting, graphics, and other specialized tools; the first release below covers a practical teaching workflow, not all of Praat. [S1, S2]

- **Fresh implementation:** derive requirements from official manuals, published algorithm descriptions, file-format specifications, and observed input/output behavior. Do not port, translate, or copy the old implementation.
- **Behavior first:** preserve scientific meaning, units, time alignment, file interoperability, and supported command semantics. Modernize presentation without silently changing analysis results.
- **Three platforms:** macOS, Windows, and Linux must run the same analysis core and pass the same compatibility suite.
- **Modern dependencies:** use maintained stable libraries with documented APIs, reproducible dependency versions, and working packages on every target platform.
- **Documentation first:** each supported feature needs documented parameters, defaults, edge cases, examples, and acceptance criteria before implementation.
- **Exceptions:** the user's “unless excellent” exception does not preapprove reuse. Any later proposal to reuse legacy code must identify the exact component, explain its quality, record provenance and license requirements, and receive a team decision before inclusion. This plan assumes no such reuse.

The supplied [praat/praat.github.io repository](https://github.com/praat/praat.github.io) contains application sources as well as documentation despite its name. Use its README and published manuals for orientation; do not use implementation files as the blueprint. The inspected class repository contains only a brief README and provides no additional architecture or language requirements. [S1, S3]

## 2. Compatibility target and evidence

Before writing algorithms, create `docs/compatibility.md` and record:

- Exact reference Praat release, platform, executable checksum, and acquisition URL. Select one release available to the class; “latest” is not a reproducible target.
- Documentation URLs, access dates, and snapshots or hashes of the pages used, subject to their redistribution terms. Online manuals may describe a different release.
- For each command: inputs, parameter order/types, defaults, output types, timing rules, errors, and known uncertainties.
- Reference runs with explicit parameters. Record actual frame coordinates and output units, not only screenshots or aggregate means.
- Known deviations and unsupported features. Do not call an approximation “Praat compatible” until its acceptance tests pass.

Evidence order: selected release's manual, published method descriptions linked by the manual, then black-box experiments with that release. If these disagree, record the discrepancy and resolve the intended behavior with the team. No reference executable is a runtime dependency.

## 3. Scope and priorities

| Capability | First release | Later compatibility work |
|---|---|---|
| Sound I/O | Mono/stereo WAV import/export; preserve sample rate and channels | AIFF/FLAC, more encodings, long-file streaming |
| Sound workspace | Named objects, select/rename/remove, metadata, open editor | Broader object types and multiple specialized editors |
| Editor | Waveform, time cursor/range, zoom/pan, selected playback | Destructive editing, advanced extraction, recording |
| Spectral analysis | Documented Gaussian spectrogram and numerical queries | Other window shapes, spectral slices and derived representations |
| Pitch | Explicit filtered-autocorrelation analysis, voiced/unvoiced contour | Raw autocorrelation and other named methods |
| Intensity | Documented windowed intensity contour and queries | Additional statistics and tier-based transformations |
| Formants | Burg formant analysis, configurable parameters, F1–F3 display | Tracking, robust methods, other LPC methods |
| Annotation | Interval and point tiers; edit labels/boundaries; undo/redo; TextGrid text I/O | Binary TextGrid, more editor operations |
| Automation | Python API and headless CLI using the same core | Explicitly enumerated Praat scripting subset |
| Export | Measurement CSV plus settings/provenance JSON | Publication graphics and additional Praat object formats |

The first release is complete only when all entries in its column meet the validation gates. A smaller milestone must be labeled as such. Full scripting compatibility, pitch/duration manipulation, synthesis, voice-quality measures, forced alignment, listening experiments, neural networks, grammar learning, and statistical tools remain outside this first release. They are real parts of Praat's broader feature set, not features presumed unnecessary. [S1, S2]

## 4. End-to-end workflow

1. Open a WAV file; show its name, channel count, sample rate, duration, and waveform.
2. Select a sound object and open its editor. Set a cursor or time range; zoom and play the selection.
3. Enable spectrogram, pitch, intensity, or formants. Display units and active parameters; allow numerical queries at a time or over a range where defined.
4. Create or load a TextGrid; insert a boundary or point, type IPA/Unicode labels, and revise timing while listening.
5. Save annotations, export measurements with analysis metadata, close, and reopen without losing annotation content or timing.
6. Run the same analysis headlessly and obtain the same numerical results as the GUI.

This workflow follows the organization of Praat's introductory tutorial. Exact supported menu labels and shortcuts must be captured against the chosen release; pixel-identical windows are not a requirement. [S2]

## 5. Behavioral contracts

### 5.1 Sound and time

- Store sample values, channel count, sample count, `xmin`, `xmax`, sample period `dx`, and first-sample time `x1`. Preserve the time domain independently of array indexing.
- For Praat's public one-based sample number `i`, use `t(i) = x1 + (i - 1) * dx`. Internally, zero-based index `j` maps to `x1 + j * dx`.
- The inverse query returns a fractional position, `1 + (time - x1) / dx`; rounding is a separate operation. [S21]
- A common imported sound starts at zero with `dx = 1 / sample_rate`, `x1 = dx / 2`, and `xmax = sample_count * dx`; do not put its first sample at zero by accident. [S4]
- Example: one second at 16 kHz has 16,000 samples; first and last sample centers are 0.00003125 s and 0.99996875 s. Its domain still ends at 1 s.
- Keep original audio unchanged during analysis. Do not normalize, resample, or downmix implicitly. Specify and verify each analysis's multichannel rule separately.
- Define selection endpoints, rounding, out-of-domain queries, interpolation, and empty selections in `docs/compatibility.md` from reference observations. Do not apply one invented rounding rule to every Praat command.

### 5.2 Spectrogram

- Use short-time spectral analysis with configurable window length, maximum frequency, time step, frequency step, and window shape.
- Gaussian analysis uses a physical window longer than its nominal effective length. Requested grid spacing can differ from the resulting spacing; preserve and expose actual coordinates.
- Separate numerical spectral power from display choices such as contrast and dynamic range. Verify scaling, frequency bins, edge frames, and multichannel handling before claiming equivalence. A library's default STFT is not sufficient. [S5]

### 5.3 Pitch

- Name the method explicitly: **filtered autocorrelation**. It low-pass filters the signal before autocorrelation, then chooses a path through voiced and unvoiced candidates.
- The manual lists floor 50 Hz, top 800 Hz, automatic step `0.75 / floor`, 15 candidates, accurate mode off, and attenuation at top 0.03. Path settings include silence threshold 0.09, voicing threshold 0.50, octave cost 0.055, octave-jump cost 0.35, and voiced/unvoiced cost 0.14. Verify these for the selected release.
- The filter response is `attenuation_at_top ** ((frequency / pitch_top) ** 2)`. Normal effective window length is `3 / floor`; accurate mode changes the window.
- Implement candidate generation, refinement, and path selection from the documented method and linked paper. Verify time-step-dependent transition penalties.
- Keep “pitch top” distinct from another method's ceiling. Retain frame times and voiced/unvoiced state; missing F0 must not be plotted or averaged as a real 0 Hz measurement. [S6]

### 5.4 Intensity

- Implement the documented squared-signal smoothing with a Kaiser-20 window; effective window length is `3.2 / pitch_floor`, and automatic step is `0.8 / pitch_floor`.
- Expose the subtract-mean setting. Verify reference-pressure conversion, channel treatment, silence representation, and aggregation separately.
- Distinguish acoustic dB relative to the documented pressure reference from dBFS. An uncalibrated recording does not establish a physical sound-pressure level. Simple unwindowed RMS does not reproduce this contour. [S7, S8]

### 5.5 Formants

- Follow the documented sequence: resample to twice the formant ceiling, pre-emphasize, apply Gaussian-like windows, estimate Burg LPC coefficients, and obtain resonances from poles.
- Expose time step, maximum formant count, ceiling, window length, and pre-emphasis frequency. The LPC order is twice the maximum formant count; half-integer counts are meaningful.
- The physical window is twice the effective length. Remove candidates below 50 Hz and above ceiling minus 50 Hz for the documented Burg command.
- Preserve frequency, bandwidth, frame timing, and missing candidates. Never fabricate F1–F3 when fewer valid resonances exist. Validate resampling and root selection as well as LPC estimation. [S9]

### 5.6 TextGrid

- Preserve grid and tier domains, tier ordering/names, interval labels, and point marks. Support `IntervalTier` and `TextTier`.
- Intervals have positive duration and touch their neighbors; points have strictly increasing times. Empty labels occupy time. Preserve imported tier/grid domain differences: matching outer bounds are weaker invariants.
- Read full and short text forms through a tokenizer for numbers, quoted strings, and flags, rather than fixed line positions. Handle documented comments, doubled quotation marks, multiline strings, and Unicode.
- Write UTF-8 full text; read UTF-8 and BOM-marked UTF-16 BE/LE with LF, CRLF, or CR line endings. Declare legacy encoding/trigraph limits. Reject binary files explicitly until implemented.
- Test files in both directions with reference Praat. Compare parsed content and times rather than byte-for-byte formatting. [S10]
- Match documented editing: splitting divides the label at its text cursor; boundary deletion concatenates adjacent labels, keeping only one copy when they are equal. Selection covers an interval and Tab plays it. Verify these against the pinned release. [S20]
- Moving a shared boundary updates adjacent intervals atomically; prevent crossings and invalid moves. Every edit supports undo/redo and unsaved-change protection.

### 5.7 Queries, errors, and automation

- Return units and explicit undefined states. Define whether each supported query samples, interpolates, or aggregates; never interpolate through unvoiced gaps without a documented rule.
- Invalid files, impossible parameters, unsupported formats, missing devices, and permission errors need useful messages and must leave existing objects unchanged.
- CLI proposal: `langtools-praat analyze INPUT.wav --config settings.json --output measurements.csv`. This is a new interface, not a promise of Praat command-line syntax compatibility.
- Use UTF-8, locale-independent numeric serialization, deterministic output ordering, and exit codes 0 for success, 2 for invalid input/configuration, and 1 for execution failure. Keep diagnostics separate from machine-readable output.
- Native Praat scripting is deferred. Document unsupported commands explicitly if a subset is later introduced; never silently execute them as Python. Praat has its own scripting language and object-selection behavior. [S11]

## 6. Proposed modern stack

These are starting recommendations for the group merge, not requirements discovered in the class repository. Choose concrete supported stable versions and commit a lockfile after a three-platform installation spike; do not depend on development releases or unbounded “latest” versions.

| Component | Proposal | Role and limits |
|---|---|---|
| Language | Python 3.12 or newer supported common baseline | Accessible scientific ecosystem; select one baseline verified with all dependencies |
| Numerical core | NumPy and SciPy | Arrays, FFTs, filtering, resampling, linear algebra; explicit parameters instead of library defaults [S12, S13] |
| Desktop UI | PySide6 / Qt 6 | One desktop toolkit across operating systems [S14] |
| Plotting | PyQtGraph | Interactive waveforms/images with Qt and NumPy [S15] |
| Audio files | SoundFile / libsndfile | WAV decoding/encoding; verify subtype, scaling, and bundled native library [S16] |
| Playback | sounddevice / PortAudio | Documented Linux, macOS, and Windows support; isolate device-specific behavior [S17] |
| Tests | pytest; pytest-qt for GUI interactions | Numerical/format tests headless; selected GUI tests per platform |
| Distribution | Python package plus PyInstaller bundles | Build and smoke-test on each target OS; PyInstaller does not cross-build OS bundles [S18] |

- Implement Praat-specific analysis and TextGrid semantics independently over general-purpose primitives.
- **Do not use Parselmouth as the engine:** it directly accesses Praat's existing C/C++ implementation, so wrapping it would not satisfy this assignment. Prefer the reference executable only in an isolated oracle test environment. [S19]
- Do not substitute generic pitch or LPC functions merely because their names resemble Praat commands; numerical and framing behavior must pass the same fixtures.
- Review direct and bundled dependency licenses before distribution. Keep third-party notices; choose the new project's license with the class. Documentation excerpts and reused assets also require attribution under their own terms. [S1]

## 7. Architecture and proposed layout

GUI and CLI call a shared application layer, which coordinates domain models, pure analysis functions, and I/O adapters. Analysis modules must not import Qt, open dialogs, or require an audio device. Typed settings objects and result objects carry units, time/frequency coordinates, validity masks, algorithm identifiers, and provenance.

```text
praat/
  REIMPLEMENTATION.md
  pyproject.toml
  docs/
    compatibility.md
    decisions.md
    usage.md
  src/langtools_praat/
    model/          # Sound, sampled results, TextGrid and tiers
    analysis/       # spectrogram, pitch, intensity, formants
    io/             # WAV, TextGrid, CSV and provenance
    application/    # commands, object registry, undo/redo
    gui/            # Qt workspace, editor and settings
    cli.py
  tests/
    unit/
    interoperability/
    gui/
    fixtures/       # generated/licensed inputs, reference outputs, manifests
```

Only `REIMPLEMENTATION.md` is created in this step; the rest is a proposed future layout.

- Use float64 computation initially; measure memory before optimizing. Internal precision is a design choice, not a claim about Praat's storage type.
- Run expensive analyses outside the UI thread. Cancellation and job identifiers prevent old results replacing those from newer settings.
- Cache by audio content/revision plus every analysis parameter and algorithm version. Audio or setting changes invalidate the affected result.
- Keep annotation edits separate from audio samples and derived analysis. Save atomically and confirm overwrites; preserve the previous file on write failure.
- Process speech locally by default. Reference fixtures use generated audio or consented, redistributable recordings, with provenance and licenses.

## 8. Cross-platform requirements

| Platform | Initial verification target | Required checks |
|---|---|---|
| macOS | macOS 14+ on Apple Silicon; Intel support verified separately | Application launch, Qt plugins, Unicode paths, playback, file dialogs |
| Windows | Windows 11 x86-64 | Application launch, paths with spaces/non-ASCII, playback, bundled native libraries |
| Linux | Ubuntu 24.04 x86-64 | Application launch, GUI plugin/system dependencies, playback through available host audio |

These are proposed test baselines, not verified support claims. Add architectures only when dependencies, CI, and bundle tests cover them.

- Use `pathlib`, platform data-directory APIs, and argument arrays for subprocesses. Avoid hard-coded separators, shell commands, and working-directory assumptions.
- Test installation from a fresh environment on all three systems. Keep numeric tests independent of sound devices and displays.
- Package on the target OS. Document Linux system prerequisites and macOS signing/notarization status; distinguish packaged prototypes from signed releases.
- Test playback manually on real hardware; headless CI cannot establish audio-device correctness. Device failure must not block offline analysis.

## 9. Validation and acceptance gates

Capture reference results before changing the implementation to match them. Each fixture manifest records input hash/license, reference version/platform, complete settings, command, output schema, and any excluded edge regions with a reason. A fixture generator may invoke the reference executable, but the shipped app and its runtime dependencies must remain independent.

| Gate | Required evidence |
|---|---|
| Audio/time | Known mono/stereo fixtures at 16, 44.1, and 48 kHz preserve sample count, rate, channels, duration, and sample-center alignment. PCM exports agree within half a quantization step when rounding without dither or clipping. |
| Spectrogram | Sine, impulse, silence, and chirp fixtures match reference grid coordinates and power scaling. Test Gaussian effective/physical windows and frequency/time-step adjustment explicitly. |
| Pitch | Pure tones, harmonic complexes, silence, octave transitions, and licensed speech test frame timing, voiced decisions, and F0. Report gross octave errors separately from average frequency error. |
| Intensity | Test silence, DC offset, channel differences, and amplitude scaling. Doubling amplitude raises nonsilent intensity by approximately 6.0206 dB under identical settings; compare reference smoothing and boundaries. |
| Formants | Synthetic source-filter vowels with known resonances plus speech fixtures compare frequency, bandwidth, missing candidates, and frame times against reference. |
| TextGrid | Round trips preserve every tier/name/label/time, empty labels, quotes, multiline text, IPA, and encoding cases. Reference Praat opens exported files. Malformed input yields clear errors without partial replacement. |
| UI | Open → select/play → analyze → annotate → undo/redo → save → reopen passes on all platforms. Changing parameters cannot display stale analysis. |
| Automation | GUI and CLI use identical settings and produce identical core results; invalid input exits predictably. |
| Distribution | Clean install and packaged-launch smoke tests pass for each declared platform; reference Praat is absent from the runtime environment. |

**Proposed starting numerical budgets, to ratify before coding:** sample/frame timestamps within `1e-9` seconds after matching grid construction; pitch within 1% on stable voiced synthetic frames; formant frequencies within `max(20 Hz, 2%)` on specified synthetic fixtures; intensity within 0.1 dB and spectrogram power within 0.5 dB on defined nonsilent interior bins. These are project acceptance proposals, not accuracy guarantees or published Praat tolerances.

Voicing masks, frame counts, missing values, spectral floors, and edge handling receive separate assertions; an average error cannot hide structural mismatches. Fix fixture-specific tolerances before accepting results, report real-speech error distributions, and document deviations instead of relaxing thresholds after failures. TextGrid numeric round trips use enough decimal precision to preserve stored doubles.

Performance measurement proposal: benchmark a fixed 60-second mono 48 kHz recording, record hardware and peak memory, and measure each analysis plus UI latency. Aim for selection/zoom feedback under 100 ms once data is loaded, asynchronous analysis with cancellation, and bounded allocations. Establish measured analysis-time budgets during the initial spike rather than inventing untested speed claims.

## 10. Milestones and three-person merge plan

| Milestone | Deliverable | Exit condition |
|---|---|---|
| M0: Specification | Merge the three research contributions; fix scope, stack, reference release, defaults, tolerances, and licenses | Every first-release feature has a source and an acceptance test definition |
| M1: Foundation | Domain models, WAV I/O, fixture capture, headless CLI skeleton | Sound/time gate passes on all three platforms |
| M2: Annotation workflow | Workspace/editor, playback, TextGrid import/edit/export | End-to-end annotation round trip and undo/redo pass |
| M3: Acoustic analysis | Spectrogram, pitch, intensity, Burg formants | Each feature passes its numerical and structural gates |
| M4: Delivery | Documentation, package bundles, compatibility report | All first-release gates pass; deviations are published |

Suggested research ownership for merging the three students' documents:

- **Student A:** workflows, objects, audio I/O, TextGrid, and interoperability cases.
- **Student B:** acoustic methods, parameters, time/frequency grids, reference fixtures, and tolerances.
- **Student C:** architecture, dependency assessment, cross-platform packaging, CLI, and CI.

Everyone reviews shared contracts: sample timing, channel semantics, undefined values, settings serialization, and result schemas. Merge by topic into one canonical document, deduplicate repeated requirements, and record conflicting proposals in `docs/decisions.md`; do not concatenate three incompatible plans. These roles are suggestions, not assignments to classmates.

### Decisions still needed at the group merge

- Exact reference release and whether the class expects a broader feature set than this first-release proposal.
- Agreement on Python/Qt or an alternative stack, supported OS/CPU baselines, and concrete dependency versions.
- Query/selection edge semantics and release-specific defaults not established by this research.
- Fixture corpus, finalized numerical budgets, and independently reviewed expected outputs.
- New-project license, distribution format, team ownership, and schedule.

## 11. Primary sources

Research accessed 2026-11-02. Manuals are living pages; implementation work must bind them to the selected reference release. Library links justify proposed roles, not proven compatibility of this unbuilt application.

- **S1:** [Praat repository README: features and licensing](https://github.com/praat/praat.github.io).
- **S2:** [Praat introductory manual and workflow](https://praat.org/manual/Intro.html).
- **S3:** [Class repository README at inspected commit](https://github.com/mhulden/langtools/blob/6d560d40ed57ac54d6cb158c00f003db80460d92/README.md).
- **S4:** [Sound object, time domain, and sample coordinates](https://praat.org/manual/Sound.html).
- **S5:** [Sound: To Spectrogram](https://praat.org/manual/Sound__To_Spectrogram___.html).
- **S6:** [Pitch analysis by filtered autocorrelation](https://praat.org/manual/pitch_analysis_by_filtered_autocorrelation.html).
- **S7:** [Sound: To Intensity](https://praat.org/manual/Sound__To_Intensity___.html).
- **S8:** [Intensity object and units](https://praat.org/manual/Intensity.html).
- **S9:** [Sound: To Formant (burg)](https://praat.org/manual/Sound__To_Formant__burg____.html).
- **S10:** [TextGrid file syntax and semantics](https://praat.org/manual/TextGrid_file_formats.html).
- **S11:** [Praat scripting manual](https://praat.org/manual/Scripting.html).
- **S12:** [NumPy documentation](https://numpy.org/doc/stable/).
- **S13:** [SciPy documentation](https://docs.scipy.org/doc/scipy/).
- **S14:** [Qt for Python / PySide6 documentation](https://doc.qt.io/qtforpython-6/).
- **S15:** [PyQtGraph documentation](https://pyqtgraph.readthedocs.io/en/latest/).
- **S16:** [SoundFile documentation](https://python-soundfile.readthedocs.io/).
- **S17:** [sounddevice documentation](https://python-sounddevice.readthedocs.io/).
- **S18:** [PyInstaller platform-specific builds](https://pyinstaller.org/en/stable/operating-mode.html).
- **S19:** [Parselmouth documentation: direct access to Praat code](https://parselmouth.readthedocs.io/en/stable/).
- **S20:** [TextGridEditor selection, playback, splitting, and merging](https://praat.org/manual/TextGridEditor.html).
- **S21:** [Fractional sample number from time](https://praat.org/manual/Get_sample_number_from_time___.html).
