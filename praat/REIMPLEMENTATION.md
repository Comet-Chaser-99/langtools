# Praat / LangTools — Master Reimplementation Specification

**Consolidated:** 2026-11-04. **Canonical location:** `praat/REIMPLEMENTATION.md`. **Status:** integrated design and research specification; implementation and runtime parity remain to be demonstrated.

This is the single master plan for a modern, offline-capable, cross-platform phonetics application in [mhulden/langtools](https://github.com/mhulden/langtools). It merges the broad workflow and numerical plan, the detailed annotation plan, and the comprehensive design contribution into one topic-based specification. LangTool is a provisional application name, unrelated to the LanguageTool grammar checker.

## Contents

- [1. Provenance, evidence and design authority](#1-provenance-evidence-and-design-authority)
- [2. Product goal, workflow and phased coverage](#2-product-goal-workflow-and-phased-coverage)
- [3. Architecture, stack and ownership](#3-architecture-stack-and-ownership)
- [4. Domain objects, Sound and time coordinates](#4-domain-objects-sound-and-time-coordinates)
- [5. Audio I/O, codecs and long recordings](#5-audio-io-codecs-and-long-recordings)
- [6. Spectrogram, waveform and visual analysis](#6-spectrogram-waveform-and-visual-analysis)
- [7. Pitch analysis and candidate/path compatibility](#7-pitch-analysis-and-candidatepath-compatibility)
- [8. Burg formants and numerical sensitivities](#8-burg-formants-and-numerical-sensitivities)
- [9. Intensity, pulses and voice-measure research](#9-intensity-pulses-and-voice-measure-research)
- [10. TextGrid annotation commands and editor state](#10-textgrid-annotation-commands-and-editor-state)
- [11. Annotation domain invariants, TextGrid codec and safe persistence](#11-annotation-domain-invariants-textgrid-codec-and-safe-persistence)
- [12. Automation, formulas and staged Praat scripting](#12-automation-formulas-and-staged-praat-scripting)
- [13. Manipulation, transforms and synthesis roadmap](#13-manipulation-transforms-and-synthesis-roadmap)
- [14. Workspace UI, menus, dialogs and keyboard routing](#14-workspace-ui-menus-dialogs-and-keyboard-routing)
- [15. Screenshot fidelity, typography and accessible rendering](#15-screenshot-fidelity-typography-and-accessible-rendering)
- [16. Shared service contracts and asynchronous integration](#16-shared-service-contracts-and-asynchronous-integration)
- [17. Cross-platform deployment, validation and release gates](#17-cross-platform-deployment-validation-and-release-gates)
- [18. Delivery milestones, unresolved discrepancies and maintenance](#18-delivery-milestones-unresolved-discrepancies-and-maintenance)
- [19. Primary references and research navigation](#19-primary-references-and-research-navigation)

## 1. Provenance, evidence and design authority

The three inputs are preserved by Git history rather than maintained as competing active plans:

| Input | Immutable provenance | Main contribution retained |
|---|---|---|
| General reimplementation plan | [REIMPLEMENTATION.md blob db9f197](https://api.github.com/repos/mhulden/langtools/git/blobs/db9f197487264357a74ecc110242c75ba6cbf112) | Research workflow, Python scientific stack, staged scope, sample-center timing, scientific acceptance gates |
| Annotation plan | [Annotation blob](https://api.github.com/repos/mhulden/langtools/git/blobs/13732a773a6922397bbadbea2678629e93180084) | Transactional editing, Unicode/IME, codec invariants, transport interfaces, visual evidence and recovery |
| Comprehensive design | [PR #5 document at c496105](https://github.com/Comet-Chaser-99/langtools/blob/c496105718eac746b8a0d3789c8d5a15fd30b690/praat/reimplementation.md) | Feature inventory, DSP detail, scripting, manipulation, UI/menu/dialog research, differential testing and risks |

The general plan's immutable blob is also available through the [GitHub blob API](https://api.github.com/repos/mhulden/langtools/git/blobs/db9f197487264357a74ecc110242c75ba6cbf112). The third input was retrieved from an open PR; its inclusion does not imply that PR has already been merged. Do not merge its lowercase `praat/reimplementation.md` separately after adopting this master: case-only filename variants collide on common macOS/Windows filesystems.

### Evidence vocabulary

- **Documented:** behavior described in an official manual, whose version must be bound to the reference release.
- **Source-observed / source reported:** implementation detail inspected by a contributor. This is not a successful runtime test or proof that a GUI command takes that path.
- **Proposed:** architecture, scope, policy or acceptance budget adopted for this master; it is not a claim about existing Praat behavior.
- **Unresolved:** reference capture, measurement or a product decision is still needed.

The two original reports dated November 2 and the third contribution did not run a reference executable. This consolidation inspected their complete contents and rechecked selected source/manual discrepancies; it did not compile Praat or measure output parity. Detailed algorithm sections retain source-derived research with this qualification. Local paths such as `praat-source/`, `PS\` and `docs/manual/` describe the contributors' research trees, not folders shipped in LangTools. The reproducible source root is [Praat commit 56ed24ef](https://github.com/praat/praat.github.io/tree/56ed24ef5efedffd06112a2bc1c0530bddc3a55e); append the cited relative file path there. Contributor line numbers are historical hints, not stable API identifiers.

### Reference baseline and conflict policy

Research source snapshot: `56ed24ef5efedffd06112a2bc1c0530bddc3a55e` (2026-11-01), whose version header reports `7.0.03beta`. Select one obtainable executable/build for acceptance, record version, checksum, build flags, OS/CPU, acquisition URL and matching manual snapshot. This master does not silently substitute a stable release for that beta snapshot.

Use the chosen release's manual and published methods to specify intent, then black-box input/output experiments to establish observed compatibility. Source observations explain discrepancies but do not automatically override documentation. If intent and runtime differ, publish the chosen behavior and its known deviation. Never silently change scientific results to make a UI prettier or a test easier.

### Consolidated design decisions

| Issue in the inputs | Master decision |
|---|---|
| C++/Qt Quick versus Python/Qt versus a referenced web draft | Python + NumPy/SciPy + PySide6/Qt Widgets + PyQtGraph is the baseline. Native acceleration is a measured optimization behind the same interfaces. Browser/Rust/C++ application rewrites are deferred alternatives. |
| Broad first-release claims versus a deliverable research workflow | R1 is audio/view/annotate/analyze/export with Python automation. Native Praat scripting, voice measures, synthesis and publication graphics are retained in the plan as R2/R3 work. |
| Conflicting sample origin descriptions | Preserve `xmin`, `xmax`, `nx`, `dx`, `x1` independently. Sample centers do not generally coincide with `xmin`. |
| TextGrid semantic equality versus byte-identical files | Semantic round-trip equality is the interchange gate. Test deterministic writer bytes separately; do not reject valid whitespace, line-ending or comment differences. |
| Equal-label boundary removal | Manual and pinned source differ. Capture the selected runtime; document the chosen rule. No unconditional claim of deduplication or concatenation is accepted yet. |
| 20 versus 22 week promises | Use milestone exit criteria. A 22-week planning envelope is illustrative only; no delivery date is promised without estimates and team availability. |
| Clean-room claims versus prior source inspection | This is source-informed independent reimplementation research, not certified clean-room work. Keep a provenance/reuse ledger and avoid copying implementation by default. |

## 2. Product goal, workflow and phased coverage

Reproduce observable research behavior with maintained libraries: preserve units, precision, time alignment, annotation content, supported commands and file interchange. The project is an independent implementation, not a wrapper around Praat. A licensed reference executable belongs only in the test/oracle environment.

The user workflow is: import recording → select named object → open editor → inspect waveform/analyses → select and audition → create/edit tiers → query/export measurements → save and reopen annotations → repeat headlessly through the same core.

### Release map (authoritative for all later chapters)

| Area | R1: first useful release | R2: expanded compatibility | R3: specialized/future |
|---|---|---|---|
| Workspace | Typed objects; selection-driven actions; rename/copy/remove/info; independent editor lifecycle | More object classes and generic inspection | Specialized editors |
| Sound | Mono/stereo WAV PCM16/24/32 I/O; sample/time queries; waveform and selected playback | AIFF/AIFC, FLAC, NIST, AU; recording; additional validated codecs | Proprietary formats and unusual channel layouts |
| Long recordings | Bounded waveform summaries and adapter interfaces; no full-file decode requirement in the interface | Complete LongSound workflow and long-file streaming acceptance | Very large corpus indexing |
| Spectrum | Gaussian spectrogram, settings, cursor queries | Spectral slices; additional windows; Spectrum/Ltas objects | Pitch-dependent spectra, cochleagrams/excitation |
| Pitch | Filtered autocorrelation, explicit parameters, F0/voicing queries and contour | Raw AC/CC and filtered CC, PitchEditor, derived tiers and pulses | SHS and additional variants |
| Formants | Burg, explicit parameters, frequency/bandwidth/count and missing values | Tracking, LPC objects, keep-all/SL/robust, FormantPath/Grid | Further model families |
| Intensity | Windowed contour and documented queries, distinct averaging methods | Silence annotation and intensity tiers | Additional transformations |
| Annotation | Interval/point tiers, Unicode, split/merge/move/search, undo/redo; full/short text TextGrid I/O | Binary/chronological TextGrid; label importers; spelling and advanced commands | Recognition, alignment, diarization, navigator |
| Automation | Typed Python API and headless CLI with shared command registry | Formula evaluator and staged native Praat interpreter | IPC/sendpraat, editor blocks, old syntax |
| Export/graphics | Measurement CSV + settings/provenance JSON; annotation export | Picture command model, PDF/PNG then SVG/EPS | Legacy picture/metafile compatibility |
| Audio transforms | Analysis-internal resampling/pre-emphasis tested as primitives | User transforms/filters, concatenate/extract, scripted manipulation and overlap-add | ManipulationEditor, LPC resynthesis, speaker/gender transforms |
| Voice | Retain explicit gaps in compatibility report | Pulses, jitter/shimmer/harmonicity and Voice report after dependencies | Advanced voice models |
| Synthesis/other | Not advertised | Simple original signal generators and source-filter tools | Art/Artword/Speaker, KlattGrid, TTS, grammar/learning/statistics, experiments |

Every R1 row must pass its gate before calling R1 complete. A partial milestone remains useful but must be labeled accurately. Feature descriptions in later research chapters do not promote R2/R3 features into R1. Keep unsupported operations absent or clearly unavailable; never ship placeholder results.

## 3. Architecture, stack and ownership

### Baseline dependencies

| Concern | Baseline | Constraint |
|---|---|---|
| Host | Python 3.12 or a newer mutually supported baseline selected at M0 | Typed interfaces; reproducible dependency lock |
| Numerical primitives | NumPy + SciPy, float64 initially | Implement Praat-specific framing/scaling/path decisions explicitly |
| Desktop | PySide6 / Qt 6 Widgets | Shared command registry; native text/IME widgets |
| Plots | PyQtGraph plus custom batched tier/waveform items | Visible-range rendering; avoid an item per sample |
| Audio files | SoundFile / libsndfile | Test actual installed build/subtype support; no inferred codec guarantees |
| Playback | sounddevice / PortAudio behind a transport adapter | Source clock and device-latency semantics tested per OS |
| Graphics | Backend-neutral drawing model; Qt display and a verified vector export backend | Matplotlib is a candidate exporter, not an automatic substitute for Picture semantics |
| Tests | pytest, Hypothesis, pytest-qt | Pure numerical/codec tests run without devices or display |
| Distribution | Python package + PyInstaller bundles per target OS | Native dependency inventory, fresh-machine smoke tests |
| Optimization | Optional Numba or a small native module | Add only after profiling; same precision and interfaces |

Use [official Qt for Python documentation](https://doc.qt.io/qtforpython-6/) and the primary sources at the end to choose concrete supported releases. These are architecture choices, not current version guarantees. Parselmouth may assist isolated reference experiments only if its embedded version is explicitly recorded; it must never become LangTool's runtime engine or silently replace the chosen oracle.

### Layer rules

```text
Qt UI / Python API / CLI / later Praat interpreter
                    ↓
Shared command registry + transactions + object workspace
                    ↓
Domain snapshots + pure scientific analysis
                    ↓
Numerical primitives / codecs / transport / graphics adapters
```

The domain and analysis layers cannot import Qt or open devices/dialogs. Commands contain IDs, typed parameters and expected revisions. Functions that create analyses return new objects and do not mutate source audio. Annotation updates return a new revision plus an inverse/change set; do not pretend keeping an old reference is sufficient undo for mutable arrays.

One registry entry defines command ID, supported selection signature, ordered parameters, types/defaults/units, enablement, result type, documentation and error schema. Dialogs, menus, Python API, CLI, history and future scripts use this entry. Object IDs are stable and distinct from names; duplicate names remain representable. Removing an object closes or detaches its editors; renaming refreshes their titles. Document memory state and explicit disk save are separate concepts.

### Suggested three-person implementation boundaries

| Contributor | Primary ownership | Shared review |
|---|---|---|
| A | TextGrid model/codec, annotation commands, tier rendering, Unicode and editor state | Domain invariants and transport integration |
| B | Decoding, streaming, playback, waveform summaries, numerical analyses and scientific fixtures | Timing, channel rules, precision and result units |
| C | Workspace, command registry, project/recovery, CLI/interpreter, packaging and graphics | Lifecycle, command schema and platform CI |

These roles combine the three reports; actual people must agree ownership at kickoff. A owns the authoritative TextGrid codec while C owns project storage, preventing duplicate serializers. Build fake adapters first so contributors can work independently.

### Proposed repository layout

```text
praat/
  REIMPLEMENTATION.md             # this single master
  pyproject.toml
  dependency lock
  src/langtools_praat/
    model/                       # domain objects and time grids
    analysis/                    # spectrogram, pitch, formant, intensity
    annotation/                  # commands and invariant validation
    io/                          # audio, TextGrid, measurement exports
    application/                 # registry, workspace, transactions, recovery
    media/                       # bounded source and transport adapters
    graphics/                    # backend-neutral drawing operations
    gui/                         # Qt workspace and editor views
    scripting/                   # future formula/Praat compatibility layer
    cli.py
  tests/
    unit/ interoperability/ gui/ fixtures/ golden/
```

This consolidation changes documentation only; listed modules and test artifacts are future implementation outputs. Additional usage/decision records may be created when code exists; do not keep competing reimplementation specifications.

## 4. Domain objects, Sound and time coordinates

All domain objects carry stable ID, kind, name, revision and relevant domain metadata; persistence is implemented by codecs rather than UI-bound `read`/`write` methods. Arrays are immutable snapshots or protected against uncontrolled mutation.

| Object | Required content |
|---|---|
| Sound | Float64 `(channels, nx)` samples; `xmin,xmax,nx,dx,x1`; source identity/revision |
| TextGrid | Ordered tier objects with their own domains and stable entity IDs |
| Pitch | Regular time grid, frame intensity, all candidate frequencies/strengths, chosen path and voicing mask |
| Formant | Regular grid, frame intensity/count, frequency/bandwidth pairs; no fabricated candidates |
| Intensity | Regular grid, dB values, reference definition and explicit undefined state |
| Spectrogram | Power matrix, axis orientation, physical units, time/frequency grids and validity |
| Matrix/Table | Coordinate-aware numeric arrays or typed named columns; labels preserved |
| PointProcess/tiers (R2) | Strictly ordered times with model-specific values and domains |
| Manipulation (R2) | Original Sound reference/snapshot, pulses, PitchTier and DurationTier |

### Canonical time rules

`time(i) = x1 + (i - 1)*dx` for public one-based sample number i; internal zero-based j maps to `x1 + j*dx`. Inverse indexing is fractional until an operation explicitly rounds. Preserve `xmin` and `xmax` separately from the sample-center grid.

For a typical imported N-frame recording at sample rate fs: `xmin=0`, `xmax=N/fs`, `dx=1/fs`, `x1=dx/2`. One second at 16 kHz has centers 0.00003125…0.99996875 s. Generated/extracted objects may have different origins or declared durations. Carry those values, not a guessed `start_time + j/fs` interpretation.

The apparent Sound inheritance conflict in the third report is resolved: the pinned `fon/Vector.h` declares `Vector` as deriving from `Matrix`. Sound deriving from Vector and initialization using Matrix are consistent. This does not establish binary field layout; binary codecs still require explicit fixtures.

Keep original audio unchanged during analysis. No implicit normalization, downmix, resampling or sample-time quantization. Specify channel handling for each method. Use finite double seconds for annotation interchange; frame indices are integers inside audio adapters. Boundary times may lie between samples.

Queries must specify interpolation method, endpoints, rounding, empty ranges, out-of-domain behavior and undefined values. Preserve units in outputs; 0 Hz is not a substitute for undefined/unvoiced pitch. A common time transform positions waveform, overlays, tiers and cursor; subtract the visible origin before converting to screen floats.

## 5. Audio I/O, codecs and long recordings

### Required I/O contract

R1 reads/writes mono/stereo WAV PCM16/24/32 and reports rate, channels, frame count and subtype. Test source decoding and export scaling explicitly. Signed integer decoding commonly divides by 2^(bits-1); unsigned PCM8 requires its own offset rule when added. Integer writing rounds/clips according to a declared policy and reports clipping; dither, float output and unusual rates are separate explicit modes.

The research reports identify WAV, AIFF/AIFC, AU/NeXT/Sun, NIST, FLAC and decode-only MP3 in Praat, with documentation/source uncertainty for Ogg/Opus and Shorten. Retain a per-format/per-subtype capability table backed by fixtures. A libsndfile binding does not guarantee all codec support in every binary package. Shorten is unsupported unless a dedicated verified implementation is added; do not promise it because an old manual lists it.

Candidate reference integer rules are PCM16 scale 32768, PCM24 scale 8388608 and PCM32 scale 2^31; clipping ranges are asymmetric. Confirm tie handling at half-integers and endpoints. Compare decoded values/metadata rather than imposing identical WAV header chunk ordering. Lossless FLAC is lossless relative to its integer representation, not arbitrary floating-point source data. File-rate fields may quantize noninteger sampling rates; export must disclose that loss.

Float32/64 WAV, compressed formats, multichannel beyond stereo and proprietary data need separate acceptance fixtures. Do not inherit the third report's unverified floating-writer scaling as a product rule.

### Generic Praat object codecs

Detect known text/binary signatures before parsing and report unsupported object classes. Full/short text layouts share a token-based representation; comments and formatting are not domain content. Numeric output must preserve stored doubles and use locale-independent formatting. Collections and versioned classes need explicit support; do not claim a generic reader handles every class.

Binary `ooBinaryFile` structure, string encoding, field order and endianness remain research work, not inferred from host memory layout or C++ inheritance. Binary Sound/Pitch/Formant/Matrix/Table and legacy chronological/ESPS/CGN/TIMIT/Kiel importers belong to R2/R3. Keep fixtures and unsupported-format errors now.

### Long recordings and device resilience

Read requested source-frame ranges with bounded caches. Waveform summaries are min/max buckets, not a full decoded copy or decimation that hides peaks. R1's interfaces support streaming even if complete LongSound feature parity ships in R2. A one-hour recording benchmark is a stress target, not a measured capability.

Device loss stops transport cleanly and preserves edits. Source revision changes invalidate summaries/analyses. Audio threads do not call UI code or mutate annotations. Cancellation, progress and errors carry operation/session IDs so stale callbacks cannot update a new session.


## 6. Spectrogram, waveform and visual analysis

Status: draft as of 2026-11-02. Sources: the manual pages and the reference source under `praat-source/`. Manual/source differences are research leads; the compatibility policy and discrepancy register in this master determine acceptance.

Manual pages used: `docs/manual/Intro_3_1__Viewing_a_spectrogram.html`, `Intro_3_2__Configuring_the_spectrogram.html`, `Intro_3_3__Querying_the_spectrogram.html`, `Intro_3_7__Configuring_the_spectral_slice.html`, `Intro_2_2__Viewing_and_editing_a_sound.html`, `Advanced_spectrogram_settings___.html`, `Sound__To_Spectrogram___.html`, `Spectrogram.html`, `Spectrum.html`, `SoundEditor.html`, `Keyboard_shortcuts.html`.
Screenshot used: `docs/pictures/screenshot-1.png` (Sound editor). `screenshot-2.png` (script window) and `screenshot-3.png` (Objects window) are not display references.

### Spectrogram algorithm

The spectrogram is a short-time Fourier analysis. The manual lists Fourier as the only method.

**Window.** The default is Gaussian. The manual emphasizes its strong sidelobe suppression: a 1000 Hz sine shows one line, not a comb of grey lines (`Advanced_spectrogram_settings___.html`). The source (`fon/Sound_and_Spectrogram.cpp`, `Sound_to_Spectrogram_e`) uses

    w(i) = (exp(-48 p^2) - e) / (1 - e),   e = exp(-12),   p = (i - mid) / N_phys,  p in [-0.5, 0.5]

The physical window is twice the effective length (`physicalAnalysisWidth = 2 * effectiveAnalysisWidth`). At the default 5 ms, the physical span is 10 ms (`Intro_3_7__Configuring_the_spectral_slice.html`). Square, Hamming, Bartlett, Welch and Hanning are kept for teaching. Other shapes belong to R2; their speed and numerical behavior need independent measurement.

**Window length and bandwidth.** The default is 0.005 s. The Gaussian -3 dB bandwidth is `1.2982804 / L`: about 260 Hz at 5 ms, about 43 Hz at 30 ms (`Intro_3_2__Configuring_the_spectrogram.html`). The manual's sine tests are regression tests. A 1000 Hz sine should give one band at 5 ms. A 1000 + 1200 Hz pair should resolve into two bands at 30 ms.

**Frequency range.** The default view is 0 to 5000 Hz (`spectrogram_viewFrom` 0.0, `spectrogram_viewTo` 5000.0, `foned/SoundAnalysisArea_prefs.h`). Analysis stops at Nyquist, and bins above it are white.

**Sampling.** The grid follows the view. Per redraw, `timeStep = (endWindow - startWindow) / spectrogram_timeSteps` and `freqStep = viewTo / spectrogram_frequencySteps`. Both steps are clamped:

- time step floor = `(L / sqrt(pi)) / 8`;
- frequency step floor = `(1 / (L / sqrt(pi))) / 8`.

Both use oversampling 8.0 (passed by `foned/SoundAnalysisArea.cpp`). For L = 5 ms the floors are 0.353 ms and 44.31 Hz, matching `Sound__To_Spectrogram___.html`. The frequency grid then snaps to FFT bin width. Frames are centred, so there is a white stripe about one physical window wide at each sound edge (`Intro_3_1__Viewing_a_spectrogram.html`).

**Pre-emphasis.** Default +6 dB/octave. Each row gets `preemph / ln2 * ln(f / 1000 + 1e-308)` dB. 1000 Hz stays at 0 dB, bands above it darken and bands below lighten (`fon/Spectrogram.cpp`, ~line 93).

**Power to dB.** `psd_db = 10 log10(psd / 4e-10)`, with psd in Pa^2/Hz (`Spectrogram.cpp`, ~line 102). The 1e-308 floor puts silence near -3080 dB.

**Dynamic compression.** Default 0. Each frame gets `c * (max - frame_max)` added to every bin (`Spectrogram.cpp`, line 134). The manual's worked example (c = 0.4, global max 80 dB, frame max 20 dB gives +24 dB) checks out against this formula.

### Dynamic range, autoscaling, colour

| Setting | Default | Source key |
|---|---|---|
| Maximum | 100 dB/Hz | `spectrogram_maximum` |
| Autoscaling | on | `spectrogram_autoscaling` |
| Dynamic range | see D04 / context-specific defaults | `spectrogram_dynamicRange` |
| Pre-emphasis | +6 dB/oct | `spectrogram_preemphasis` |
| Dynamic compression | 0 | `spectrogram_dynamicCompression` |
| Colour map | Grey | `spectrogram_colourMap` |

**Autoscaling.** When on, `maximum` is the largest post-pre-emphasis value in the visible part, not the fixed 100 dB/Hz. Loud material scrolling off screen therefore darkens the rest. The manual describes this as intended (`Intro_3_1__Viewing_a_spectrogram.html`), so it must be reproduced exactly.

**Grey mapping.** Values from `maximum - dynamicRange` (white) to `maximum` (black) map linearly to grey. Values above the top are black, and values below the bottom are white (`Intro_3_2__Configuring_the_spectrogram.html`; `fon/Spectrogram.cpp` ~line 151 calls `Graphics_image` with `min_val`, `max_val`).

**Colour maps.** `fon/Spectrogram_enums.h` lists Grey, Viridis, Jet, Hot, Cool, Spring, Summer, Autumn, Winter, Bone, Copper, Pink, Parula and Turbo, plus invert and RGB options. These are later additions that the manual does not cover. Only Grey must match. The others are extension points and need not be pixel-identical.

### Editor layout

From `screenshot-1.png` and `Intro_2_2__Viewing_and_editing_a_sound.html`:

- The waveform fills the upper pane, with amplitude labels at left (max, zero, min). A cyan frame marks the modifiable sound.
- The spectrogram fills the lower pane, with 0 Hz at the bottom and the view top (`5000 Hz` by default) at the top, and the frequency axis at left.
- A red time cursor runs through both panes. Its time is shown above the waveform. Clicking the spectrogram shows a cross with frequency at left and time at top (`Intro_3_3__Querying_the_spectrogram.html`).
- Below the panes is a time ruler: selection start and end, then "Visible part" and "Total duration" rows.
- The bottom row has the buttons `all`, `in`, `out`, `sel`, `bak`, a scroll bar, and a `Group` check box that synchronises zoom and scroll (`SoundEditor.html`).
- The screenshot also shows pitch (blue, right axis, 50 to 800 Hz) and formant (red dots) overlays. The report identifies preference flags for these overlays; first-open defaults remain subject to reference capture. They are separate features and are outside this section.

For zoomed-out views, a peak-preserving waveform representation draws a vertical min/max span per pixel column (`Intro_3_1__Viewing_a_spectrogram.html`). Spectrogram display uses time-frequency samples and interpolation rather than waveform min/max aggregation; validate its viewport sampling separately.

### Zoom and scroll

From `Keyboard_shortcuts.html` and `foned/FunctionEditor.cpp`:

- **Zoom in** halves the visible span, keeping the centre fixed. Shortcut Command-I, which is Ctrl-I on Windows.
- **Zoom out** doubles it. Command-O.
- **Zoom to selection** is Command-N. It pushes the previous window onto a history. **Zoom back** pops it. **Zoom all** is Command-A.
- **Ctrl plus mouse wheel** zooms by 2 % per step: `exp(-0.02 * sign * sqrt(|delta|))`.
- **Page-up and Page-down** scroll by a page. Shift-wheel and horizontal swipe scroll horizontally (`What_was_new_*`).
- Scrolling by arrow keys uses `arrowScrollStep` = 0.05. The manual says 5 % of the visible window (`Intro_3_1__Viewing_a_spectrogram.html`). See the discrepancy notes below.
- The window clamps to the sound extent (1e-12 tolerance). When a shift hits an edge, the window length is kept.
- The spectrogram recomputes on every window change. The time-step rule keeps about one frame per pixel column (`Advanced_spectrogram_settings___.html`).

Because frames are point samples at pixel centres, scrolling changes the image slightly, and the darkness changes under autoscaling (`Intro_3_1__Viewing_a_spectrogram.html`). This is a candidate observable behavior to capture; do not change it silently.

### What must match and what may differ

**Must match numerically:**

1. The Gaussian window, physical length (2x effective), and the edge clamp.
2. Time and frequency step rules, including the 8x oversampling floors and FFT-bin snapping.
3. The dB transform, pre-emphasis row term, and 1e-308 floor.
4. Autoscaling, dynamic-range and compression formulae, with the defaults from the discrepancy register.
5. Grey endpoints: `maximum - dynamicRange` is white, `maximum` is black.
6. Default view 0 to 5000 Hz, and the edge stripes.
7. Zoom factors (x0.5 and x2 per step), zoom-to-selection and zoom-back, and clamping.
8. The bandwidth formula, so that the manual's sine tests pass.

**Should match visually:**

- Layout: waveform above, spectrogram below, frequency axis at left, time ruler at bottom, cursor crossing both panes.
- Layer order: waveform, spectrogram, overlays, cursor.
- Grey direction: quiet is white, loud is black.
- Pane proportions. In `screenshot-1.png` the two panes are roughly equal in height. The reference does not fix this.

**May differ freely:**

- Font rasterization, widget toolkit and native chrome may differ; meaningful menu actions and focus behavior still follow the command and accessibility contracts. The screenshot platform is unverified; capture it explicitly for new evidence.
- Colour maps other than Grey.
- Pixel positions of overlays, provided the data is the same.

A numerical/raster comparison should use a spectrogram-only export from a fixed test sound, rendered under recorded settings. Whole-window screenshots separately validate layout and interaction states; do not use unknown-DPI website screenshots as quantitative raster baselines.

### Verification plan

- Regenerate the manual's worked examples (1000 Hz sine, 1000 + 1200 Hz pair at 30 ms, the click-and-tone formula) and check band positions and widths.
- Compare spectrogram cell values against the reference's `Spectrogram` object, using `Spectrogram: Get value` queries on both sides.
- Read the defaults from the reference's Spectrogram settings form in a running build.

### Conflicts and unverified items

- **Dynamic range default.** The manual (`Intro_3_2__Configuring_the_spectrogram.html`) says 50 dB. The Sound editor source (`spectrogram_dynamicRange`) says 70 dB. `Spectrogram: Paint...` (`fon/praat_uvafon_init.cpp`) uses 50 dB. Treat 70 dB for the editor and 50 dB for Paint as separate candidate defaults; capture both forms in the chosen executable before freezing them.
- **Time and frequency step defaults.** The manual's `Advanced_spectrogram_settings___.html` says 1000 and 250. The source says 1500 and 500. Both values remain context-specific reference candidates until runtime capture.
- **Scroll step units.** The manual says 5 % of the window. The code declares 0.05 with no explicit unit. Not verified which the Sound editor uses.
- **Grey ramp shape.** Linear in dB is inferred from the `Graphics_image` call. `sys/Graphics_image.cpp` was not read, so gamma or quantisation is unverified.
- **Screenshot measurements.** `screenshot-1.png` is a single desktop capture at unknown DPI. No pixel measurements were taken, so proportions and label positions are approximate.
- **Gaussian width.** The `exp(-48 p^2)` form was read from source. The bandwidth was taken from the manual's `1.2982804 / L`, not derived from the source.
- **Colour maps and RGB.** These were read from the enum and switch statements, not checked against rendered output.


## 7. Pitch analysis and candidate/path compatibility

Source root used for all citations: `praat-source\` (abbreviated `PS\` below). The pitch code was found under `praat-reimplementation\praat-source`.

### Methods

Praat offers four candidate-finding methods, all feeding one shared path finder:

| Command (manual) | Method | Source entry point |
|---|---|---|
| Sound: To Pitch... / (raw autocorrelation) | AC, Hanning window | `Sound_to_Pitch_rawAc` (`PS\fon\Sound_to_Pitch.cpp`:499) |
| (raw autocorrelation, very accurate) | AC, Gaussian window | same, `veryAccurate = true` |
| (raw cross-correlation) | forward CC, unwindowed | `Sound_to_Pitch_rawCc` (:512) |
| (filtered autocorrelation) | low-pass, then AC | `Sound_to_Pitch_filteredAc` (:525) |
| (filtered cross-correlation) | low-pass, then CC | `Sound_to_Pitch_filteredCc` (:569) |

The manual (`PS\docs\manual\pitch_analysis_by_raw_autocorrelation.html`) describes the AC method as Boersma (1993): the windowed autocorrelation is divided by the normalized autocorrelation of the window, so that peaks of a periodic signal come out at the same height. The CC method (`pitch_analysis_by_raw_cross-correlation.html`) is a forward cross-correlation over a window of one longest period. The manual recommends filtered AC for speech intonation and CC for jitter/shimmer-type voice work. The filtered variant applies a Gaussian-in-frequency low-pass to the whole sound before analysis (`Sound_to_Pitch_filteredAc`, cutoff `pitchTop / sqrt(-2 ln attenuationAtTop)`), so that the amplitude factor at `pitchTop` equals `attenuationAtTop` (the manual's table at `pitch_analysis_by_filtered_autocorrelation.html` agrees: 0.03 at 800 Hz, 0.42 at 400 Hz).

### Algorithm

1. **Frame grid.** Frames are centred so that as many as fit symmetrically are placed (`Sampled_shortTermAnalysis`, `PS\fon\Sampled.cpp`:71). Frame count is `floor((duration - windowDuration)/timeStep) + 1`.
2. **Per frame (`Sound_into_PitchFrame`, `PS\fon\Sound_to_Pitch.cpp`, starting near line 30).** Subtract a local mean (one longest period either side); window (AC only); compute local intensity as the peak of the windowed, mean-subtracted frame divided by the global peak (`globalPeak`, computed on the whole sound at :370). Compute r(lag) by FFT (AC) or direct sums (CC).
3. **Candidate recruitment.** Candidate 1 is always the unvoiced candidate (frequency 0, strength 0). Local maxima of r with `r > 0.5 * voicingThreshold` are candidates (line 186); frequency comes from parabolic interpolation, strength from sinc interpolation, then a second sinc-based maximization. Up to `maxnCandidates` are kept; when full, a new peak replaces the weakest one if it scores higher after the octave penalty (lines 227, 237). `maxnCandidates` is raised to `floor(ceiling/floor)` if smaller (line 287).
4. **Path finding (`Pitch_pathFinder`, `PS\fon\Pitch.cpp`:524-670).** Viterbi over frames. Per-candidate score `delta`: unvoiced candidates get `unvoicedStrength = voicingThreshold + max(0, 2 - intensity*(1+voicingThreshold)/silenceThreshold)` (line 553-555); voiced candidates get `strength - octaveCost * log2(ceiling/f)` (line 560). Transition costs: voiced to voiced `octaveJumpCost * |log2(f1/f2)|`; any voicing change `voicedUnvoicedCost`; both unvoiced 0. Before the search both jump and V/UV costs are multiplied by `0.01 / dx` (lines 543-545), which is the time-step correction the manual mentions. Voiced means `0 < f < ceiling` (`PS\fon\Pitch.h`:66). The backtrack swaps the chosen candidate into slot 1.

### Parameters and defaults

Defaults below are from the GUI forms in `PS\fon\praat_Sound.cpp` (lines 1615-1800) and the manual pages. The `Sound_to_Pitch` convenience function (`Sound_to_Pitch.cpp`:494-496) hard-codes the same values as the "To Pitch..." form.

| Parameter | "To Pitch..." (AC) | Filtered AC/CC | Notes |
|---|---|---|---|
| Time step | 0 (auto) | 0 (auto) | auto = `periodsPerWindow / floor / 4`: 0.75/floor for AC, 0.25/floor for CC (`Sound_to_Pitch.cpp`:291) |
| Pitch floor | 75 Hz | 50 Hz | sets window length: 3/floor (AC), 1/floor (CC); analysis fails if floor < periodsPerWindow / duration (:314) |
| Ceiling / top | 600 Hz | 800 Hz | ceiling does not limit recruitment (see the discrepancy notes below) |
| Max candidates | 15 | 15 | "Very accurate" off |
| Very accurate | off | off | AC Gaussian window, length 6/floor (:299) |
| Silence threshold | 0.03 | 0.09 | relative to global peak |
| Voicing threshold | 0.45 | 0.50 | strength of unvoiced candidate; also gates recruitment at 0.5x |
| Octave cost | 0.01 /oct | 0.055 /oct | favours high candidates |
| Octave-jump cost | 0.35 | 0.35 | scaled by 0.01/dt |
| Voiced/unvoiced cost | 0.14 | 0.14 | scaled by 0.01/dt |
| Attenuation at top | n/a | 0.03 | filtered variants only |

### Where the manual and source disagree or are silent

These were checked against the code and are not in the manual's text:

- **Ceiling.** The manual says candidates above the ceiling are "ignored". In the code, the ceiling does not restrict recruitment: the lag loop starts at 2 (`Sound_to_Pitch.cpp`:185), and `minimumLag` (:339) is computed but never used (grep confirms one occurrence). Above-ceiling candidates survive into the path finder and are simply treated as voiceless there (`Pitch.h`:66). The header comment (`Sound_to_Pitch.h`) says the same thing.
- **Octave-cost reference.** Recruitment penalises with `log2(pitchFloor/f)` (:227, :237), but the path finder uses `log2(ceiling/f)` (`Pitch.cpp`:560). The manual does not say which reference applies. Test both scoring stages against the oracle before claiming parity.
- **Window length.** The manual gives the Hanning window length as exactly 3/floor. The code takes `floor(dt_window/dx)`, then rounds to an even count minus 2 (`Sound_to_Pitch.cpp`:330-332). The difference is a few samples.
- **Pull formants.** `Pitch_pathFinder` has a formant-pulling branch (`Pitch.cpp`:654), enabled by passing `Melder_debug == 31` as its last argument (`Sound_to_Pitch.cpp`:485). With the flag off it is inactive; the manual does not mention it.
- **Debug switches.** `Melder_debug == 30` enables a frequency-jump term across unvoiced stretches (`Pitch.cpp`:591); it is off by default. Do not expose debug-only branches as normal product features.

### What "replicating Praat numerically" means

The target is a function from (Sound, settings) to a Pitch object with the same frame grid, the same candidate lists (frequency and strength per frame), and the same path. Several things limit exact equality:

- **Floating point.** The AC path uses Praat's own FFT (`NUMfft_forward/backward`) and `sqrt`, `exp`, `log`, which differ across libm builds. A port in double precision with a different FFT will differ at roughly 1e-12 relative in r, which is usually below any decision boundary but not always.
- **Long double.** Cross-correlation accumulates in `longdouble` (`Sound_to_Pitch.cpp`:116-127). `PS\melder\melder_real.h`:20-40 maps this to 80-bit on x86-64 gcc/clang and to 64-bit on ARM64 and (per the comment) on Clang for Windows. CC results therefore depend on the compiler, and Praat itself is not bit-identical across platforms. This is verified from the comment; the MSVC behaviour is from general knowledge and unverified here.
- **Threading.** Frames are computed in parallel (`MelderThread_PARALLEL`), but each frame writes only its own slot, so results should not depend on thread count. Not tested.
- **Decision ties.** The Viterbi uses strict `>` with an `==` tie branch (`Pitch.cpp`:613). Near-ties in path cost can flip with tiny numeric changes; these are the main source of path mismatch.

So "match" needs tiers, not one tolerance.

### Differential test plan

Oracle: a Praat build from this source tree, run through a Praat script that writes, for each frame, the time, intensity, and each candidate's frequency and strength, plus the final path (`Get value in frame` / candidate queries; exact command names unverified against this tree). Inputs:

- Synthetic: pure sines at 100, 220, 377 Hz; sine plus white noise at 0, 10, 20 dB SNR; impulse trains at 90 Hz; a linear chirp 80 to 400 Hz; silence; a sine with an 0.2 s gap; the sound in `PS\test\fon\Sound_to_Pitch.praat`.
- Real speech: at least five short clips (male, female, creak, high child voice, noisy recording), chosen by the project owner. Not yet selected.

Parameter grid: the default setting of each of the five methods, plus pitch floors 50, 75, 100 and ceilings 300, 600, 800, with silence/voicing thresholds at 0.03/0.09 and 0.25/0.5.

Tolerances:

| Quantity | Tier A (same algorithm, same double arithmetic) | Tier B (independent FFT) | Tier C (cross-compiler / acceptance) |
|---|---|---|---|
| Frame count, times (x1, dx) | exact | exact | exact |
| Intensity per frame | rel. 1e-10 | rel. 1e-8 | rel. 1e-6 |
| Candidate frequency, voiced both | rel. 1e-7 | rel. 1e-5 | rel. 0.5% in 99% of frames |
| Candidate strength | abs. 1e-8 | abs. 1e-6 | abs. 1e-3 |
| Voiced/unvoiced decision | 0 mismatches | <= 0.2% of frames, each checked as a near-tie | <= 1% of frames |
| Final path, voiced frames | 0 frame mismatches | >= 99.5% agreement | >= 98% agreement |
| Octave-jump count | equal | within 1 | within 2% of frames |

Rules:

- Every path mismatch must be classified: a score tie (|delta_path_1 - delta_path_2| < 1e-9 at the decision point) is acceptable in Tiers A and B; anything else is a failure.
- Gross errors (frequency off by more than 5% in a voiced frame where both agree on voicing) fail every tier.
- Determinism: run the oracle twice and compare; identical output is required before any port is compared against it.
- Edge cases, exact: all-zero sound returns all-unvoiced; floor below `periodsPerWindow/duration` raises the documented error; ceiling above Nyquist is clipped (`Sound_to_Pitch.cpp`:324); time step 0 gives `periodsPerWindow/floor/4`.
- Long-double check: run CC on one platform with gcc and one with MSVC; the difference is reported, not failed, and recorded as the platform noise floor.

### Unverified

- Exact `Get value` / candidate query commands in this source tree; the test script above names them only generically.
- That the filtered variants' manual pages match their GUI forms beyond what is listed here (I read the filtered AC page and the GUI; the filtered CC manual page was checked only for its absence of a "standard value" line).
- The sinc-depth constants (`NUM_PEAK_INTERPOLATE_SINC70`/`700`, `PS\melder\NUMinterpol.h`:35-36) and their meaning in `NUMinterpol.cpp`, which I did not open.
- MSVC `long double` width (see the numerical-replication notes below).
- No oracle has been run; all tolerances above are proposals, not measured values.


## 8. Burg formants and numerical sensitivities

Source root used for all citations: `praat-source\` (the sources are under `praat-reimplementation\praat-source`). All line numbers were read on the working tree as of 2026-11-02.

### Pipeline

The user-facing command is `Sound: To Formant (burg)...`. Its GUI form is in `fon/praat_Sound.cpp` (lines 1448-1460), and it calls `Sound_to_Formant_burg` in `fon/Sound_to_Formant.cpp`. The steps, in order:

1. **Resampling.** `Sound_to_Formant_any` (line 377) resamples to `2 * maximumFrequency` with `Sound_resample(..., 50)` unless the ceiling is <= 0 or equal to the existing Nyquist (in which case the Sound is copied). The manual (`fon/manual_formant.cpp`, lines 566-567) states the same.
2. **Pre-emphasis, in place.** `Sound_preEmphasize_inplace` (`fon/Sound.cpp`, line 1241) applies `s[i] -= a * s[i-1]` for i from N down to 2, with `a = exp(-2*pi*f*dx)` (`Sound_computeEmphasisFactor`, line 1237). The first sample is unchanged in this reported code path; preserve channel-local state in any independent implementation. The manual describes this as a +6 dB/octave inverted low-pass with the +3 dB point at the "Pre-emphasis from" value.
3. **Frame grid.** `dt` defaults to `halfdt_window / 4` when the time step is 0 (line 293), which is 25% of the window length as the manual says. `numberOfFrames = 1 + floor((duration - 2*halfdt_window)/dt)`, and frame 1 is centred at `x1 + 0.5*(duration - dx - (n-1)*dt)` (lines 294-301).
4. **Window.** Gaussian with `N = floor(2*halfdt_window/dx)` samples (line 297). Weights are `w(i) = (exp(-48*((i - (N+1)/2)/(N+1))^2) - e^-12) / (1 - e^-12)` (lines 317-320), so the window is zero at both edges. The manual describes a Gaussian-like window; distinguish the effective Window length parameter from the approximately doubled physical span. Validate sidelobe claims and exact sample weights numerically.
5. **Intensity.** The frame intensity is the maximum squared sample in the window region of the pre-emphasised Sound (lines 333-341). It is a peak, not an RMS. A frame whose maximum is zero is left empty, because Burg cannot process all zeros (line 342-343).
6. **Burg.** `burg()` (lines 36-89) takes `numberOfPoles = Melder_iround(2 * nFormants)` (line 392) and calls `VECburg` (`dwsys/NUM2.cpp`, lines 1430-1496), the Burg recursion (reflection coefficients `2*num/denum`, error update `xms *= 1 - a_i^2`). The prediction polynomial is `z^m - a_1 z^(m-1) - ... - a_m` (lines 44-47), and its roots are folded into the unit circle with `Roots_fixIntoUnitCircle` (`dwsys/Roots.cpp`, lines 72-77; roots with |z| > 1 are replaced by `1/conj(z)`).
7. **Root selection.** Only roots with `imag >= 0` are used (conjugate pairs). The frequency is `|atan2(im, re)| * Nyquist / pi`, kept only if it lies in `[safetyMargin, Nyquist - safetyMargin]` (lines 61-87). For the Burg command `safetyMargin = 50 Hz` (line 392); for "keep all" it is 0 (line 400).
8. **Sorting.** `Formant_sort` (`fon/Sound_to_Formant.cpp`, line 267) sorts each frame by frequency, carrying bandwidths with it.

Split-Levinson (`Sound_to_Formant_willems`, line 406, command "sl") is a separate code path (`splitLevinson`, lines 169-265). It always sets bandwidth to 50 Hz (line 261), which the manual confirms (`manual_formant.cpp`, lines 609-610).

### Parameters and defaults

| Parameter | GUI label and default (`praat_Sound.cpp` 1449-1453) | Manual | Code meaning |
|---|---|---|---|
| Time step | 0.0 (= auto) | 25% of window length | `dt`; 0 means `halfdt/4` |
| Max. number of formants | 5.0 | any multiple of 0.5 | `numberOfPoles = round(2*nFormants)`; `maxnFormants = (poles+1)/2` |
| Formant ceiling | 5500.0 Hz | 5500 (female), 5000 (male), 8000 (child) | resample target `2 * ceiling`; also sets Nyquist for frequencies |
| Window length | 0.025 s | effective; actual Gaussian is 2x | `halfdt_window`; Gaussian length `2 * halfdt_window` |
| Pre-emphasis from | 50.0 Hz | +3 dB point | `preemphasisFrequency` |

Notes on the table:
- The contributor reports agreement between these GUI forms and the manual. Capture reset defaults in the pinned executable before treating them as release requirements.
- `Sound_to_Formant_burg` requires `nsamp_window >= numberOfPoles + 1`, otherwise it throws `Window too short.` (line 299). The Burg LPC command has a different error message (`dwtest/test_LPC.praat` line 94); a reimplementation should not conflate them.
- If `numberOfFrames < 1`, the code falls back to one frame centred on the whole Sound (lines 302-307). This is undocumented in the manual (unverified as a user-visible behaviour).

### The Formant object

Declared in `fon/Formant_def.h` (class `Formant`, parent `Sampled`) and `fon/Formant.h`:
- Sampled axis: `xmin, xmax, nx, dx, x1`; `dx` is the frame step, and the manual calls frame duration equal to frame step (`manual_formant.cpp`, lines 65-66).
- `maxnFormants` (INT16) is the capacity, set to `(numberOfPoles+1)/2` by `Formant_create` (`fon/Formant.cpp`, lines 80-92).
- Each frame: `intensity` (double), `numberOfFormants` (INT16), and a vector `formant[]` of `Formant_Formant` (`frequency`, `bandwidth`, both double, in Hz). Frames can have fewer formants than `maxnFormants`, so the number of formants is per frame (`Formant_getMinNumFormants`/`MaxNumFormants`, lines 94-107).

Stale comments: `fon/Formant.h` lines 35-46 (the `Formant_create` postconditions) still refer to `maximumNumberOfPairs`, `numberOfPairs`, `formants[]` and `bandwidths[]`, which do not exist in `Formant_def.h`. The implementation is the authority; a reimplementation should not copy those comments.

### Bandwidth reporting

The bandwidth of a Burg pole is `-ln(|z|^2) * Nyquist / pi` (`fon/Sound_to_Formant.cpp`, lines 84-85), where `Nyquist = 0.5 / dx` of the resampled Sound. Equivalently, with pole radius r, `B = -ln(r^2) * fs / (2*pi)`. The manual states bandwidth in Hz (`manual_formant.cpp`, line 87) and does not give this formula, so the formula is taken from source only.

Two bandwidth conventions to be aware of:
- Burg and "keep all" use the pole formula above, so bandwidths are frame-dependent.
- Split-Levinson sets all bandwidths to a constant 50 Hz (line 261). A reimplementation that reports bandwidths for "sl" must reproduce that constant, not estimate it.

### Replicating numerically: differential test plan

Reference generation needs the pinned oracle. The original contributor did not run a binary. The plan:

1. **Fixtures.** Subject to provenance and redistribution checks, consider `dwtest/sa1.wav` (92 KB, 16 kHz speech) and the synthetic cases in `test/fon/Sound_to_Formant.praat` (sinusoid plus Gaussian noise, random sample rates 16-96 kHz). `dwtest/sa1_10020_burg_20220616.Formant` is a binary (`ooBinaryFile`) Formant object, presumably from `sa1.wav`, but its generating parameters are not recorded in the repo (unverified). Use it only as a sanity reference after its parameters are confirmed.
2. **Reference output.** A Praat script that runs `To Formant (burg)` with an explicit grid of parameters and writes, per frame, `intensity`, `numberOfFormants`, and each formant's frequency and bandwidth (e.g. `Down to Table` with bandwidths, or `Save as text file`). Record the Praat version and the build used.
3. **Parameter grid.** Vary `maximumNumberOfFormants` over {4, 4.5, 5, 5.5, 6}, ceiling over {5000, 5500, 8000}, window over {0.005, 0.025}, pre-emphasis over {0, 50, 200}, and time step over {0, 0.01}. Include the 0-ceiling and ceiling-equals-Nyquist branches.
4. **Comparison.** Exact match on frame count, frame times (to 1e-9 s), and `numberOfFormants`. For frequencies and bandwidths, a tolerance is needed; a value of 0.01 Hz is a starting guess (unverified, not derived from any measured Praat noise floor). Compare sorted formants, since `Formant_sort` is applied.
5. **Known sensitivities.** Root finding and the Burg recursion use `longdouble` accumulators (`dwsys/NUM2.cpp`, lines 1443-1447), so the reimplementation should use at least double precision in the sums. Resampling (`Sound_resample`, precision 50) is a separate source of mismatch; test the resampler on its own first.

### Unverified claims

- The sa1 `.Formant` reference parameters (above).
- The 0.01 Hz tolerance.
- Whether a Praat binary is available for reference generation.
- That "keep all" and Burg differ only in the safety margin. This is what the code shows, but I did not run it.
- The odd-window framing quirk: `halfnsamp_window = N/2` and the frame spans `2*halfnsamp` samples (lines 297, 331-332, 346), so for odd N the frame is one sample shorter than N and its window indexing starts at its own first sample. I read this but did not test whether it changes results.


## 9. Intensity, pulses and voice-measure research

**Scope:** intensity is R1; pulse, jitter/shimmer and voice-report implementation is R2. The detailed report below retains definitions and candidate oracle cases for both stages.

Sources: `praat-source/docs/manual/` (Intensity, Sound__To_Intensity, Intro_6_2, PointProcess, Voice, Voice_1..3, Voice_6, Voice_report, PointProcess__Get_jitter__*, Advanced_pulses_settings) and `praat-source/fon/` (Sound_to_Intensity.cpp, Intensity.cpp, praat_Sound.cpp, Sound_to_PointProcess.cpp, Pitch_to_PointProcess.cpp, VoiceAnalysis.cpp, AmplitudeTier.cpp, PointProcess.cpp). Source-derived details below are research leads; resolve disagreements using the pinned runtime and the discrepancy register in this master.

### Intensity

### Definition and units

An Intensity object is a Matrix with one row and linearly spaced frames `t_i = t_1 + (i-1) dt`, with values in dB SPL, meaning dB relative to 2e-5 Pa (manual: `Intensity.html`). In `fon/Sound_to_Intensity.cpp` the reference is `hearingThreshold_in_Pa = 2.0e-5`, and a frame value below 1e-30 relative power is clamped to -300 dB. The object is created by `fon/Intensity.cpp` (`Intensity_create`, `Intensity_init` via `Matrix_init` with dy = 1, one row).

### Computation (Sound: To Intensity...)

Form defaults (`fon/praat_Sound.cpp`, `CONVERT_EACH_TO_ONE__Sound_to_Intensity`): Pitch floor = 100 Hz, Time step = 0 (auto), Subtract mean = true. The old form (`CONVERT_EACH_TO_ONE__old_Sound_to_Intensity`) passes `subtractMean = false`.

Parameters in `Sound_to_Intensity_` (source comment and manual agree):

- `logicalWindowDuration = 3.2 / pitchFloor`. This is the "effective" window length the manual refers to.
- `physicalWindowDuration = 6.4 / pitchFloor`; the window is spanned by `halfWindowSamples = floor((physicalWindowDuration/2) / dx)` on each side of the frame centre.
- Default time step (timeStep = 0) is `logicalWindowDuration / 4 = 0.8 / pitchFloor`.
- Window shape: `x = (i - centre) dx / halfWindowDuration`, `w = I0((2 pi^2 + 0.5) * sqrt(1 - x^2))`, i.e. a Kaiser window with beta ~ 20.2. The manual calls this "Kaiser-20" (`Sound__To_Intensity___.html`) and, in Intro 6.2, "Gaussian ('double Kaiser')". Treat the source formula as a candidate reference kernel and verify it with the pinned runtime.
- Sound is squared, then averaged with the window. With `subtractMeanPressure`, the mean of each windowed segment is removed (`centre_VEC_inout`) before squaring. This is a local mean over the window, not a global DC removal.
- For each frame, `P = sum_channels sum_samples(x^2 w) / sum_channels sum_samples(w)`, and the value is `10 log10(P / (2e-5)^2)`.
- The frame centre is the nearest sample to the frame time (time accuracy half a sample). Stereo input is handled by pooling channel energies.
- `veryAccurate` is `false` in code; if enabled, the Sound is upsampled first to avoid super-Nyquist content from squaring.

Minimum length: the physical duration must be at least `6.4 / pitchFloor` (about 64 ms at 100 Hz); otherwise an error is thrown.

Unverified: the manual describes the intensity as ripple-free to 0.00001 dB for a periodic signal; I have not checked this numerically.

### Averaging (Intensity: Get mean...)

Settings: time range (t1, t2) with t1 >= t2 meaning the whole object; averaging method energy, dB, or sones. Per `fon/Intensity.cpp`, these map to unit codes through `v_convertStandardToSpecialUnit`: energy `10^(0.1 x)`, sones `2^(0.1 x)`, dB identity. The mean is taken in that domain and converted back. The manual formulas are:

- dB: `(1/(t2-t1)) integral x(t) dt` (implemented as a sampled mean, `Sampled_getMean_standardUnit`; the integral wording is the manual's, the sampled form is what the code does)
- energy: `10 log10{ (1/(t2-t1)) integral 10^(x(t)/10) dt }`
- sones: `10 log2{ (1/(t2-t1)) integral 2^(x(t)/10) dt }`

The median (`Intensity_averaging_MEDIAN`) is a separate path via `Sampled_getQuantile` at 0.5. Maximum, minimum, standard deviation and time-of-extremum queries are in the manual pages `Intensity__Get_*.html`; I have not read their implementations.

Behaviour stated in the manual: energy-averaged mean of an Intensity made from a Sound should be close to that Sound's mean SPL.

Default averaging method in the query form: unverified (not read).

### Display settings

View range default 50-100 dB (manual Intro 6.2). Visual only; it does not affect values.

### Pulses (PointProcess)

A PointProcess is a sorted sequence of times `t_i` in `[tmin, tmax]`, with `t_{i+1} > t_i` (manual `PointProcess.html`; `fon/PointProcess.cpp`). Pulses are the glottal-closure estimates used by voice analysis. Two generators are used by the periodic commands:

### Sound & Pitch: To PointProcess (cc)

Implemented in `fon/Pitch_to_PointProcess.cpp`, function `Sound_Pitch_to_PointProcess_cc`. The algorithm, as read from the code:

1. Iterate over voiced intervals of the Pitch (`Pitch_getVoicedIntervalAfter`).
2. In each voiced interval, start at its midpoint, where F0 is `f0middle`. Find the extremum (maximum) within `+-0.5/f0middle` of that midpoint via `Sound_findExtremum`. This is the first pulse.
3. Walk right, then left, from the anchor. At each step, search for the best cross-correlated period in the window `[tmax + 0.8/f0, tmax + 1.25/f0]` (or the mirror interval to the left) with `Sound_findMaximumCorrelation`. Add a pulse when correlation > 0.3 and peak > 0.01 times the global absolute peak, and the new pulse is more than `0.8/f0` after the last added pulse on that side (`addedRight`).
4. Boundary points at the voicing edges require correlation > 0.7 and peak > 0.023333 times the global peak.
5. If correlation is -1 (no candidate), the search steps by one period and continues.

Constants 0.8, 1.25, 0.3, 0.7, 0.01 and 0.023333 are from the code. The manual does not state them; treat them as the reference behaviour, with the code as source.

`Sound_findMaximumCorrelation` is a static helper in `fon/Pitch_to_PointProcess.cpp` (line 163); its internals were not read in full. Unverified: exact correlation normalisation.

### Sound & Pitch: To PointProcess (peaks)

Same walk and pitch-based anchoring, but each step uses `Sound_findExtremum` in the window `[tmax - 1.25/f0, tmax - 0.8/f0]` (or the mirror). No correlation test. Includes maxima, minima, or both, as selected. It is the choice the manual documents as "peaks".

### Sound: To PointProcess (periodic, cc / peaks)

Defined in `fon/Sound_to_PointProcess.cpp`. Each is a composition: `Sound_to_Pitch(me, 0.0, fmin, fmax)` (autocorrelation, time step auto), then the pitch-based finder above. The manual (`Voice_6...`) says the one-step periodic cc uses the AC pitch, which is suboptimal for voice work. For voice analysis, use a two-step path: `Sound: To Pitch (raw cc)` followed by `Sound & Pitch: To PointProcess (cc)`. The "optimize for voice analysis" setting in the Sound window does this.

Other PointProcess generators (`Sound_to_PointProcess_extrema`, `_zeroes`) are simple local-extremum and zero-crossing finders in `fon/Sound_to_PointProcess.cpp`. Zero crossings are interpolated linearly.

### Jitter and shimmer

Notation: `T_i` is the i-th interval (period) between consecutive points; `N` is the number of intervals. Two range settings always apply: a period range `[pmin, pmax]` and a `maximumPeriodFactor` on the ratio of consecutive intervals. The manual's defaults (`Voice_2__Jitter.html`) are `pmin = 0.8 / pitchCeiling`, `pmax = 1.25 / pitchFloor`, and a maximum period factor of 1.3 (the value used in the voice-report examples; the form that holds the voice-report default was not located, so this is unverified). The voice report itself is in `fon/VoiceAnalysis.cpp`. Setting `pmin == pmax` disables the range filter (code convention in `fon/VoiceAnalysis.cpp`).

A term is skipped when any of its intervals falls outside `[pmin, pmax]` or when a consecutive ratio exceeds `maximumPeriodFactor`. `N` is decremented accordingly. The denominator uses the adjusted `N`. Results are `undefined` if too few terms remain.

### Jitter (`PointProcess: Get jitter ...`, `fon/VoiceAnalysis.cpp`)

Let `meanPeriod = (sum of valid T_i) / N_valid`, computed by `PointProcess_getMeanPeriod` with the same filter rules.

- **local**: `jitter = [ sum_{i=2}^{N} |T_i - T_{i-1}| / (N-1) ] / meanPeriod`. Result is a fraction (printed as %).
- **local, absolute**: the same sum without division by meanPeriod, in seconds.
- **rap** (relative average perturbation): `absAP = sum_{i=2}^{N-1} |T_i - (T_{i-1}+T_i+T_{i+1})/3| / (N-2)`; `RAP = absAP / meanPeriod`. Range 0 to 2.
- **ppq5**: `absPPQ5 = sum_{i=3}^{N-2} |T_i - (T_{i-2}+...+T_{i+2})/5| / (N-4)`; `PPQ5 = absPPQ5 / meanPeriod`. Range 0 to 4.
- **ddp**: code returns `3 * RAP` (`PointProcess_getJitter_ddp`). The manual gives `absDDP = sum |(T_{i+1}-T_i) - (T_i-T_{i-1})| / (N-2)`, then `DDP = absDDP / meanPeriod`, and states the result is exactly 3 times RAP. See the discrepancy notes below.

The voice-report jitter values are the five of these in the order local, local absolute, rap, ppq5, ddp, printed with 3 decimals as percent (or seconds for absolute).

### Shimmer (`fon/AmplitudeTier.cpp`, `fon/VoiceAnalysis.cpp`)

Amplitudes are taken at the pulses through `PointProcess_Sound_to_AmplitudeTier` (called from `fon/VoiceAnalysis.cpp`; its sampling method, peak-search or nearest-sample, is unverified). Amplitude values `A_i` then go through `AmplitudeTier_getShimmer_*_u` with the same period filter (`pmin`, `pmax` on the pulse-to-pulse distances) and a `maximumAmplitudeFactor` (default 1.6, `fon/praat_Tiers.cpp`) on the ratio of consecutive amplitudes. The denominator in all linear measures is the mean of `A_1 ... A_{size-1}` over the whole tier (not only the valid terms, per the code).

- **local**: `mean_valid |A_i - A_{i-1}| / mean(A)`. Manual: "average absolute difference between amplitudes of consecutive periods, divided by the average amplitude."
- **local, dB**: `20 * mean_valid | log10(A_{i-1}/A_i) |`. Code uses the ratio. The manual's wording "log of the difference" is wrong; see the voice-measure discrepancy notes below.
- **apq3**: `mean_valid |A_i - (A_{i-1}+A_i+A_{i+1})/3| / mean(A)`.
- **apq5**: five-point neighbourhood, same form.
- **apq11**: eleven-point neighbourhood (`i-5 .. i+5`), 10 neighbours plus the point.
- **dda**: `3 * apq3` (`PointProcess_Sound_getShimmer_dda`). Manual: "Praat's original Get shimmer ... three times APQ3."

Shimmer is meaningful only on sustained vowels (manual). The voice report prints shimmer local (%), local dB (dB, 3 decimals), apq3, apq5, apq11, and dda (%).

### Voice report

Command: Pulses > Voice report in the Sound window, or `Voice report: tmin, tmax, floor, ceiling, maxPeriodFactor, maxAmplitudeFactor, silenceThreshold, voicingThreshold` in a script (manual Voice_6 example: `0, 0, 75, 500, 1.3, 1.6, 0.03, 0.45`). The function `VoiceAnalysis.cpp` writes these sections, in order:

1. Time domain (tmin, tmax, duration; the window is selection-driven).
2. Pitch: median, mean, standard deviation, minimum, maximum (Hz).
3. Pulses: number of pulses, number of periods, mean period and its standard deviation (seconds).
4. Voicing: fraction of locally unvoiced frames (with counts), number of voice breaks, degree of voice breaks (fraction, with break seconds and total seconds). Breaks are inter-pulse intervals longer than `1.25/floor` (manual `Voice_1__Voice_breaks.html`; code uses `pmax` = `1.25/floor`). Unvoiced frames use the voicing and silence thresholds (defaults 0.45 and 0.03 per the manual).
5. Jitter: local, local absolute, rap, ppq5, ddp.
6. Shimmer: local, local dB, apq3, apq5, apq11, dda.
7. Harmonicity of voiced parts: mean autocorrelation, mean NHR, mean HNR (dB).
8. H1-minus-H2: mean of points and mean of curve (dB) via `PointProcess_Sound_to_H1minusH2Tier_u`.

The manual's pages describe only jitter, shimmer, voice breaks, and the HNR (Voice 4, not read here). Sections 1, 2, 3 and 8 are present in code but are not described in the voice pages I read. Include these in the R2 voice-report inventory, not the R1 release gate.

The period floor and ceiling used for the report are `pmin = 0.8 / ceiling` and `pmax = 1.25 / floor` (`VoiceAnalysis.cpp`, consistent with `Voice_2__Jitter.html`).

### Discrepancies and unverified items

- **DDP wording.** `PointProcess__Get_jitter__ddp____.html` says absDDP is "one third of the mean absolute difference of differences", but the formula given has no 1/3, and the same page says DDP is exactly 3 times RAP. Code returns `3 * RAP`. Use `3 * RAP` as the candidate definition, subject to reference validation. The `N` decrement rule for DDP in the manual (three-term validity) also differs from the code, which uses the RAP filter; the code observation must be confirmed by the selected runtime.
- **Shimmer dB.** Manual says "log of the difference"; code uses `log10(A_{i-1}/A_i)`. Use the ratio as the candidate definition, subject to reference validation.
- **Shimmer denominator.** Code averages the amplitudes of all points except the last, not only valid terms. The manual says "average amplitude". Verify this candidate behavior against the selected runtime.
- **Intensity window.** Manual says both "Kaiser-20" and "Gaussian (double Kaiser)". Code is `I0(beta sqrt(1-x^2))` with beta = 2 pi^2 + 0.5. Verify this candidate behavior against the selected runtime.
- **Mean intensity integral.** Manual writes an integral; code uses a sampled mean. Confirm `Sampled_getMean_standardUnit` before relying on either.
- **Unverified:** the internals of `Sound_findMaximumCorrelation`; `Sound_findExtremum`; `PointProcess_Sound_to_AmplitudeTier` sampling method (interpolated or nearest; not read); default averaging method of Intensity Get mean; voice-report default values beyond those cited; the `PointProcess.cpp` report function near lines 47-59 (appears to be a separate PointProcess-level report with the same jitter lines; not read); the intensity ripple claim (0.00001 dB).


## 10. TextGrid annotation commands and editor state

### 10.1 Opening and creating annotations

**Documented:** a TextGrid contains interval tiers and point tiers. It can be edited alone or alongside Sound/LongSound. See the [TextGrid object manual](https://praat.org/manual/TextGrid.html).

Proposed flow:

1. Import a recording into the object list.
2. Run `To TextGrid…`, entering ordered tier names and identifying point tiers.
3. Create a distinct annotation object linked to the recording, inheriting its time domain.
4. Select the recording and annotation and run `View & Edit`.
5. Edit, save a TextGrid, close, and reopen in both applications.

Also support opening an annotation without audio. Keep editing enabled; disable playback with an explanation. A missing recording must never make the annotation unrecoverable.

Do not assume the first time is zero. Store source time origins explicitly. Define how mismatched audio and annotation domains are displayed without shifting either silently. Duplicate names must not be used as object or tier identity.

### 10.2 State model

The editor state separates:

- document: ordered tiers, labels, times, revision and dirty state;
- view: visible time span, pane sizes, analysis visibility and vertical scroll;
- selection: active tier, selected entity, cursor and ordered time range;
- text editing: caret, selected text, composition state and edit transaction;
- transport: requested playback range, actual source position and status;
- transient gesture: drag anchor, candidate time, affected IDs and preview.

A selection or zoom change is not a document edit. Playback cannot modify labels. A redraw cannot push undo history. Stale analysis responses cannot change the current selection.

### 10.3 Interaction contract

The following condensed behaviors are **documented** in the [editor manual](https://praat.org/manual/TextGridEditor.html): selecting an interval selects its time range; Enter inserts a boundary/point; label splitting depends on text selection; dragging moves marks, Shift-drag moves coincident marks across tiers; Tab auditions a selection and stops playback at its current position. The manual describes an equal-label exception to merging; D03 records conflicting source behavior and the required runtime check. The editor includes tier-scoped Find and Find again.

Translate those into independently testable commands:

| Command | Preconditions | LangTool requirement |
|---|---|---|
| Select interval | Valid tier/entity | Set active tier, range and text target together |
| Insert boundary | Interior time in interval tier | Split geometry and text as one undoable transaction |
| Insert point | Valid point-tier time | Insert ordered event with an editable label |
| Move boundary | Internal boundary and valid target | Change shared endpoint of both adjacent intervals |
| Move aligned marks | Explicit affected IDs | Validate all proposed positions, then commit atomically |
| Remove boundary | Internal boundary | Merge geometry and apply verified label merge rule |
| Set label | Valid target and completed text composition | Preserve Unicode content and update both views |
| Add/rename/reorder/remove tier | Valid operation | Preserve stable identity; record complete inverse operation |
| Find / Find again | Active tier and query | Return match entity and text range; reveal result |
| Play/stop selection | Audio service available | Use source-clock time and keep annotation content unchanged |
| Export TextGrid | Valid document | Produce interoperable output through the single codec |

This table is a proposed implementation contract; exact post-command focus and selection need reference fixtures.

### 10.4 Split semantics: high-priority reference cases

**Source-observed:** `insertBoundaryOrPoint` in the pinned `TextGridArea.cpp` considers both time selection and text selection, rejects duplicates and selections crossing existing boundaries, and treats inactive tiers differently. Its collapsed-caret behavior can divide text around the caret; selecting all text has a special branch. A generic “split and copy label” operation would miss these distinctions.

Build a decision table from reference runs before implementing the complete command:

| Time selection | Text selection | Fixture to capture |
|---|---|---|
| Collapsed inside one interval | Caret at beginning, middle, end | Resulting labels, selection and caret |
| Collapsed | Entire label selected | Special-case label placement |
| Collapsed | Partial text selected | Whether selected substring is retained or removed |
| Range within one interval | Partial or complete selection | Left, middle and right results |
| Range meeting an existing boundary | Any | Endpoint handling and interval count |
| Range crossing an internal boundary | Any | Error and absence of partial mutation |
| Target is inactive tier | Unrelated active text | Label allocation without stealing active text |

Do not infer all rows from the ordinary middle-caret case. Tests must include combining marks and supplementary Unicode characters; toolkit UTF-16 positions and core UTF-8 byte offsets are different coordinate systems.

### 10.5 Proposed drag transaction

On press, resolve a stable entity ID and take a before-image. During movement, update a preview only. Determine a proposed target using the visible time transform and snapping policy. On release, validate every affected tier and commit one command. Escape cancels the gesture without dirtying the document.

For aligned multi-tier moves, collect exact coincident times from the original model; do not identify unrelated marks by a wide floating-point epsilon. Snapping is an interaction tolerance measured in screen units and converted to time at the current zoom. It is separate from domain equality.

Preserve interval adjacency and strict event order. Illegal moves must not cause crossed boundaries, duplicate points, or partially moved tiers. **Unresolved:** reference behavior for invalid drops, tie-breaking between snap targets, drag thresholds, auto-scroll and the modifier's interaction with editor preferences. Capture these rather than claiming this proposed transaction design exactly describes Praat.

### 10.6 Text, search and focus

Support IPA, combining diacritics, multilingual input, paste, bidirectional labels and platform input methods. Store literal label content. Avoid silent Unicode normalization or trimming. Distinguish raw Praat trigraph text from a display representation; define any conversion as an explicit operation.

Coalesce ordinary typing into sensible undo groups. Commit or cancel input-method composition before changing the target interval; test that Enter during composition does not unexpectedly insert a boundary.

Keep text shortcuts and annotation shortcuts in separate routing contexts. Verify the reference mapping for Command/Ctrl variants and function keys. Provide menu alternatives for operating-system shortcut collisions. Retain keyboard focus visibility and expose boundaries and intervals through an accessible list/navigation interface in addition to the drawing surface.

**Unresolved search details:** wraparound, case sensitivity, empty query, normalization, matches spanning composition, and end-of-tier messages. Do not substitute regular expressions for literal search without an explicit mode.


## 11. Annotation domain invariants, TextGrid codec and safe persistence

Proposed model, independent of serialization and UI:

```text
TextGridDocument { id, revision, xmin, xmax, orderedTiers }
Tier = IntervalTier | PointTier
IntervalTier { id, name, xmin, xmax, intervals[] }
Interval { id, xmin, xmax, label }
PointTier { id, name, xmin, xmax, points[] }
Point { id, time, label }
```

Use finite IEEE-754 double seconds for interchange times and retain their full precision. Audio services use integer frame indices internally. An annotation boundary may fall between audio samples; do not quantize annotation times just because playback uses frames. UI formatting must never become the stored value.

Every mutation must preserve positive interval duration, exact adjacency of neighboring intervals, and strictly increasing point times. Newly created documents should span each tier's declared domain. Persist IDs in project data; TextGrid export does not need invented ID fields.

**Compatibility distinction:** the [format specification](https://praat.org/manual/TextGrid_file_formats.html) distinguishes strong ordering/adjacency restrictions from weaker domain-coverage assumptions. Imported files can violate the latter. Preserve representable domain differences and flag them; do not silently extend, crop, reorder, or relabel imports to fit the new-document policy. Reject impossible geometry transactionally. Optional repair creates a separate, reviewable result and reports each change.

Tier removal and reordering must repair editor selection by stable ID. Commands should carry a revision precondition and return typed errors. No GUI item may hold a raw pointer into a container that can move during editing.


### 11.1 Required compatibility

Initial interoperability is full and short text TextGrid import/export. Unknown classes and binary signatures produce clear unsupported-format errors. Do not treat a binary file as corrupt text.

Implement a token scanner and structural parser, with source locations and typed diagnostics. Avoid one regular expression per line. The [format manual](https://praat.org/manual/TextGrid_file_formats.html) describes free-standing data tokens, doubled embedded quotes, comments, text encodings and line endings. Preserve precision and literal strings through decoding and writing; semantic round-trip equality is the objective, not identical whitespace.

Proposed import pipeline:

```text
bytes → identify format/encoding → decode → scan tokens
      → parse declared structures → validate → publish document
```

Set explicit byte, tier, entity and string-size limits. Check counts before allocating. Never publish half a parsed document. Preserve file path, detected encoding and diagnostics separately from annotation content.

### 11.2 Codec verification checklist

- Full, short and mixed-layout token arrangements.
- Comments and decorative indices without interpreting those indices as payload.
- Empty labels, quoted labels, exclamation marks inside strings and multiline strings.
- UTF-8 and both byte orders of BOM-marked UTF-16; LF, CRLF and CR.
- Explicit handling for legacy encodings; ambiguous input requires a user-selected encoding rather than lossy replacement.
- Nonzero time origin, unequal declared domains and scientific notation.
- Count mismatches, truncation, malformed quotes and unexpected class names.
- NaN/infinity, duplicate point times, overlapping intervals and invalid duration.
- Backslash sequences preserved as raw content through import/export.

The scanner's exact whitespace, number and comment grammar must be derived from pinned fixtures before declaring support for arbitrary valid Praat files. Well-formed output from one happy-path writer is insufficient coverage.

### 11.3 Proposed save behavior

Default to UTF-8 text with deterministic numeric formatting and enough digits to round-trip doubles. Offer full and short text export. Never rewrite annotation times using the display's decimal precision.

Write a temporary sibling file, flush it, then replace the destination using the platform's safe replacement facility. Failure must leave the previous file usable and the document dirty. Only a successful explicit save establishes a new clean revision.

Project metadata and crash recovery belong to C. Store source-audio links and view state there; keep TextGrid export interoperable. Recovery snapshots never overwrite an explicit export automatically. Detect external file changes before replacement and provide a conflict flow.


## 12. Automation, formulas and staged Praat scripting

### R1 Python API and CLI

Proposed CLI: `langtools-praat analyze INPUT.wav --config settings.json --output measurements.csv`. Settings are typed, versioned, locale-independent and complete enough to reproduce GUI results. Export a sidecar JSON with source hash, algorithm/version, settings, units and validity policy. Exit codes: 0 success, 2 invalid input/configuration, 1 execution failure; diagnostics go to stderr. The CLI is a LangTool interface, not Praat syntax compatibility. Python exposes the same command/application layer without launching a window or opening a device.

The remaining subsections specify the retained R2/R3 native Praat-language roadmap. S0/S1/S2/S3 are interpreter stages, independent of the R1/R2/R3 product releases. A Python API is not a Praat-language interpreter, and implementing a parser does not imply support for every menu command.

Praat scripts (`.praat` files and text typed into a Script window) are the main automation interface for users, and many lab workflows depend on them. This section says what the language contains, how much of it to match, how to build the interpreter, and which commands to implement first.

Sources: the scripting tutorial under `praat-reimplementation/praat-source/docs/manual/Scripting_*.html` (chapters 3 to 8 and 10), the formula pages `Formulas_3`, `Formulas_6`, `Formulas_7` in the same folder, and the sendpraat pages `praat-source/docs/sendpraat.html` and `manual/Scripting_8_1`/`8_2`. The interpreter source in `praat-source/sys/` was consulted only to confirm the parser style (see interpreter design options below). Frequencies below come from a grep of the 336 `.praat` files in the source tree; those are mostly test scripts, so the counts show what the test suite uses, not what users run.

### Language features the manual documents

- **Lexical rules.** Comments start with `#` or `;`. Leading whitespace and blank lines are ignored. A statement may continue with `...` at the start of the next line (`Scripting_3_7`). The manual's examples use curly quotes for strings; whether the interpreter also accepts them is unverified (check `sys/Interpreter.cpp`).
- **Variables** (`Scripting_5_1`, `5_6`, `5_7`). Numeric names start with a lowercase letter. String names end in `$`. Vectors end in `#` and matrices in `##`. Arrays use `x[i]` and dictionaries use `x["key"]`. Predefined variables include `windows`, `macintosh`, `unix`, `praat_intel64` and related platform flags, `praatVersion`, `praatVersion$`, `newline$`, `tab$`, `shellDirectory$`, `homeDirectory$`, `preferencesDirectory$`, `temporaryDirectory$` and `defaultDirectory$`. The manual notes that predefined variables can be overwritten and recommends `appVersion()` and `appVersion$()` instead. `variableExists()` tests for a name.
- **Expressions** (`Scripting_5_2`, `Formulas_3`, `Formulas_6`, `Formulas_7`). Numeric and string formulas, with the operator precedence described in `Formulas_3`. Some points from that page: `^` is right-associative (`4^3^2` is `4^9`), and `-2^6` is rejected as ambiguous. The page also documents `if ... then ... else ... fi` (or `endif`) and a trailing `;` that ends a formula. The string functions include `length`, `left$`, `right$`, `mid$`, `index`, `rindex` and `startsWith`. Also `fixed$` and `percent$` for formatted output (`Scripting_5_1`).
- **Control flow** (`Scripting_5_3`, `5_4`, `5_9`). `if`/`elsif` (`elif` is a documented variant)/`else`/`endif`; `for`/`endfor` with an optional `from`, where the stop value is re-evaluated each pass; `while`/`endwhile`; `repeat`/`until`; `exitScript` with or without a message. `assert` (`Scripting_6_8`) is described as equivalent to an `if` that calls `exitScript`.
- **Include** (`Scripting_5_8`). `include file.praat` must start at column 0, takes a literal filename, and is spliced in before the rest of the script is considered. There is no separate namespace. Relative paths resolve against the outermost script's folder.
- **Procedures** (`Scripting_5_5`). `procedure name: .arg$, .arg2` ... `endproc`, called as `@name: args`. Variables prefixed with `.` are local to the procedure. Unprefixed names are global, and the manual's own example depends on a procedure reading a global.
- **Output and queries** (`Scripting_6_2`, `6_3`). `writeInfo`, `writeInfoLine`, `appendInfo`, `appendInfoLine`, and `clearinfo`. Any command that writes to the Info window can be assigned instead: a numeric target takes the leading number, and a string target (`mean$ = Get mean: ...`) takes the whole text.
- **Object model** (`Scripting_4_1` to `4_3`). `selectObject`, `plusObject`, `minusObject`, `removeObject`, `selected()`, `selected$()`, and `numberOfSelected()`. Objects are addressed by numeric ID or by "Type name" string.
- **Menu commands as statements.** Most of the language's surface is the menu command set: `Create Sound as pure tone: "name", ...`, `Draw line: ...`, `Get mean: ...`. Argument lists are colon-separated and comma-delimited. The commands are not a fixed keyword list in the manual.
- **Forms and pauses** (`Scripting_6_1`, `6_6`). `form`/`endform` with field types `real`, `positive`, `integer`, `natural`, `word`, `sentence`, `text`. `beginPause`/`endPause` adds `comment`, `boolean`, `infile`, `outfile`, `choice`, `optionMenu` and `realvector`. `pauseScript` gives a simple stop/continue prompt. Form variable names are derived from the field labels (spaces become underscores, the first letter is lowercased, parenthetical units are dropped).
- **Files and system** (`Scripting_6_4`, `6_5`). `fileReadable`, `readFile$`/`readFile`, `writeFile`, `appendFile`, `createFolder`, `deleteFile`, `runSystem`, `runSystem_nocheck`. The manual warns that `runSystem` is platform-specific and dangerous.
- **Other.** `stopwatch`, `runScript`, `runNotebook` (listed among the reserved words in `sys/Formula.cpp`), `nocheck` and `nowarn` prefixes, and the vector functions of `Scripting_5_7` (`zero#`, `to#`, `from_to#`, `sort#`, `shuffle#`, `sum`, `mean`, `stdev`, `inner`).
- **Old syntax** (`Scripting_10`). Old scripts used `echo`, single-quote interpolation (`'name$'`), and command names with a trailing ellipsis such as `Draw... 0 0 0 0 yes Curve`. The manual says old scripts "should continue to work", which means the interpreter has to accept these forms too.

### How much to target

Continuations belong with the lexical stage S0; their appearance again in the inherited S2 inventory is superseded by this rule. Optional filesystem/system/IPC features require their own explicit support and trust policy.

Recommend a tiered plan, measured against the repo's own script corpus as a research corpus; only scripts whose commands are implemented become acceptance tests.

- **Compatibility stage S0 (after R1).** Lexical rules; numeric and string variables; all of `Scripting_5_1` to `5_5` and `5_9`; the `writeInfo*`/`appendInfo*` family; `assert` and `exitScript`; formulas with the `Formulas_3` precedence; `length`, `left$`, `right$`, `mid$`, `index`, `rindex`, `fixed$`, `percent$`; `selectObject`/`plusObject`/`minusObject`/`removeObject`/`selected$`; `form`/`endform` with the seven basic field types; calls to whichever menu commands the reimplementation has implemented.
- **Compatibility stage S1.** Arrays and dictionaries; vectors and matrices (`#`, `##`, and the `Scripting_5_7` functions); `beginPause`/`endPause` with the full field set; query-to-variable assignment; file I/O; `include`; `runScript`; `variableExists`; predefined platform and version variables.
- **Compatibility stage S2.** sendpraat and `praat --send` (see inter-process control below); `runSystem`; `stopwatch`; `nocheck`/`nowarn`; the remaining form types (continuation lines are already S0).
- **Compatibility stage S3 (defer or decline).** Old-syntax forms (`'var'` interpolation, `Draw...` names) can be implemented as a translation pass later, not in the core parser. `sendsocket` is documented as removed in Praat 7 (`Scripting_6_7`), so do not implement it. Exact byte-for-byte output formatting is Tier 3 unless the corpus tests require it.

The main cost is not the grammar. It is the size of the menu-command surface, since every command is reachable from a script. Build the command registry from the same table that drives the GUI, so that a menu item and its script form are one entry. Then the long tail of commands can be added without touching the parser.

### sendpraat and inter-process control

Praat has three ways to be controlled from outside: the `sendpraat` subroutine and program (`docs/sendpraat.html`, `Scripting_8_1`, `8_2`), `praat --send` (`Scripting_6_9`, recommended in the docs because it starts Praat if needed), and `praat --run`/`--open` for script and file arguments (`Scripting_6_9`). Sendpraat takes a `timeOut` (ignored on Windows), a `fullTrust` flag that gates file writes and system calls (`Scripting_8_1`), a program name, and one or more script lines. If IPC compatibility is implemented in R3, specify the CLI surface and trust semantics explicitly; R1 provides a separate Python API/CLI and does not claim sendpraat compatibility. The transport is platform-specific. `sys/praat.cpp` near line 109 mentions a message file that sendpraat writes; the mechanism on each platform is unverified beyond that comment.

### Interpreter design options

**A. Hand-written parser in the host language.** Praat's grammar is line-oriented: one statement per line, keyword-led blocks, `@` calls, and `.`-prefixed locals. The repo's own formula parser is hand-written recursive descent (`sys/Formula.cpp`, `Formula_parseExpression` near line 1913). A hand-written parser can match the quirks exactly (the `-2^6` rejection, right-associative `^`, `fi`/`endif`, the `;` terminator, dollar-suffix typing, `#`/`##` literals, query-assignment rules) and can report errors by line number, which the manual relies on (`exitScript` and `assert` messages include line numbers). It adds no dependency. Cost: we write and test the parser ourselves.

**B. Embed a general-purpose language and translate.** Lua, Python, Tcl or JavaScript would supply expressions, control flow and debugging. The problems are: Praat statements are commands with colon-separated arguments and no assignment (`Draw line: 0, 50, length, 50`), which do not map onto host syntax; query results change type based on the target variable; line-number error reporting must be rebuilt; and the `fullTrust` gate from sendpraat would have to be enforced around an runtime that has full OS access by default. Rejected as the core interpreter. It could be reconsidered later as an optional extension language.

**C. Hybrid (recommended).** A hand-written, line-based statement parser builds a small AST and runs it directly. The same expression evaluator serves formulas inside command arguments and statement-level assignments. Command dispatch goes through the shared command registry (the scope table above). `include` and `form` are handled in a pre-pass, because the manual says `include` happens before the rest of the script is considered and that a form's values are needed by the body (`Scripting_5_8`, `6_1`).

Recommendation: option C.

### Most-used script commands to support first

Ordered by manual emphasis and by line-leading frequency in the repo's 336 scripts (counts approximate):

1. `writeInfoLine:`, `appendInfoLine:` (about 400 lines), `appendInfo:` (about 120), `writeInfo:`, `clearinfo`
2. `for`/`endfor` (about 260), `if`/`elsif`/`else`/`endif`, `while`/`endwhile`, `repeat`/`until`
3. `procedure`/`endproc` (about 160) and `@call`, including `.local` names
4. `assert` (about 385), `exitScript`
5. `selectObject:` (about 180), `removeObject:` (about 175), `plusObject:`, `minusObject:`, `selected()`, `selected$()`, `numberOfSelected()`
6. Object-creating commands with ID assignment (`sound = Create Sound as pure tone: ...`), and the action commands `Remove` and `Draw` (about 40 each), `Play`, `Save as ...`
7. `form`/`endform`, `beginPause`/`endPause`, `pauseScript:`
8. String functions `fixed$`, `percent$`, `length`, `left$`, `right$`, `mid$`, `index`, `rindex`
9. File and system: `readFile$`, `writeFile`, `appendFile`, `fileReadable`, `createFolder`, `deleteFile` (about 5 to 15 each)
10. `runScript:`, `include`, `variableExists`, `praatVersion$`/`appVersion$`, `windows`/`macintosh`/`unix`
11. Vector constructors and reducers: `zero#`, `sum`, `mean`, `stdev`, `sort#`, `size`

### Unverified and open items

- Whether the interpreter accepts curly-quoted strings as used in the manual examples.
- Whether `elif` and `fi` are accepted as statements, or only `elsif`/`endif` (the manual documents `fi` only for formulas).
- The exact numeric-to-text formatting. The manual shows values such as `1.4142135623730951`, which look like shortest round-trip output, but the algorithm was not checked.
- How menu commands are dispatched inside `sys/Interpreter.cpp`. Only the file layout and the presence of the parser were confirmed.
- The frequency counts come from test scripts and may not reflect user scripts.
- Whether `nocheck` and `nowarn` change behaviour beyond suppressing errors or warnings was not checked in the manual.


## 13. Manipulation, transforms and synthesis roadmap

Sources read: `praat-reimplementation/praat-source/docs/manual/Manipulation.html`, `Intro_8_1__Manipulation_of_pitch.html`, `Intro_8_2__Manipulation_of_duration.html`, `Manipulation__Get_resynthesis__overlap-add_.html`, `Sound.html`, `Sound__Resample___.html`, `Sound__Filter__pre-emphasis____.html`, `Sound__Filter__de-emphasis____.html`, `Sound__Lengthen__overlap-add____.html`, `Articulatory_synthesis.html`; source `fon/Manipulation.cpp`, `fon/Sound.h`, `artsynth/*`. Nothing was compiled or run.

### The Manipulation object

A Manipulation holds four parts (manual `Manipulation.html`): the original Sound; a PointProcess of glottal pulses; a PitchTier (the pitch targets); and a DurationTier (initially empty). Its attributes are `timeStep` (common value 0.010 s), `pitchFloor` (common 75 Hz) and `pitchCeiling` (common 600 Hz).

Creation (`Sound_to_Manipulation`, `fon/Manipulation.cpp` line ~114) runs the Sound: To Pitch analysis, places pulses where the sound has energy, converts the pitch contour to a dense PitchTier, and adds an empty DurationTier. Two variants take a precomputed Pitch or PointProcess (`Sound_Pitch_to_Manipulation`, `Sound_PointProcess_to_Manipulation`).

Resynthesis is a switch in `Manipulation_to_Sound` (`fon/Manipulation.cpp` ~line 669). The manual lists overlap-add (original sound + pulses + pitch tier + duration tier), LPC-based (LPC + pulses + pitch tier), and pulse-train or hummed output from pulses alone or the pitch tier alone. The manual calls the first method overlap-add. The usual name for this family is PSOLA; that the two are the same algorithm is **unverified**. The overlap-add functions copy pulse-centred windows (`copyRise`, `copyFall`, `copyBell`, `copyBell2`, `copyFlat`, ~lines 209-285) into a new Sound.

Several enumerated modes are stubs. `Manipulation_PULSES_FORMANT`, `..._FORMANT_INTENSITY`, `..._LPC_INTENSITY` and `..._PITCH_LPC_INTENSITY` return an empty `autoSound` in the source. The manual does not list them, so the reimplementation should not port them as-is.

Editing is through ManipulationEditor (`foned/ManipulationEditor.cpp`), which is GUI work and belongs in the editor section. The manual's workflow is: drag pitch points (with Stylize pitch to thin them), add duration points, shift-click to hear the original, and Publish resynthesis to get a new Sound. Scripted control is through Replace/Extract commands (`Manipulation__Replace_pitch_tier.html` and siblings). Precise scripted manipulation (Create PitchTier, Add point, Replace pitch tier) is documented in `Intro_8_1`, and the duration example in `Intro_8_2` makes a step change by placing two points 0.000002 s apart (0.084999 and 0.085001). That is a usable regression case.

Test coverage: the listing of `test/fon/` shows no Manipulation test. Resampling has eight (`resample*_8.praat`), and `Sound_concatenate.praat` exists. The Manipulation path needs tests written from scratch.

### Sound filters and transforms

The Sound menu in `Sound.html` lists many commands. The table covers the ones that matter for the expanded R2/R3 roadmap. "Read" means the manual page or source was opened for this section. Items marked "listed" were seen only in `Sound.html`.

| Command | What it does (source) | Phase |
|---|---|---|
| Sound: Resample... | Sinc interpolation with depth `Precision` (default 50); precision 1 is linear; anti-alias low-pass when downsampling. Declared `fon/Sound.h:113`. Read. | R2 |
| Filter (pre-emphasis) / (de-emphasis) | alpha = exp(-2 pi F dt); pre: y_i = x_i - alpha x_(i-1); de: recursive y_i = x_i + alpha y_(i-1). Declared `fon/Sound.h:189-191`. Read. | R2 |
| Filter (one formant) in-place | `Sound_filterWithOneFormantInplace`, `fon/Sound.h:187`. Listed. | R2 |
| Scale peak / Scale intensity, Fade in / out, Multiply by window, Set value, Extract part, Combine to stereo | Simple per-sample or windowing operations. Listed. | R2 |
| Sounds: Concatenate | Joins sounds; `test/fon/Sound_concatenate.praat` exists. Listed. | R2 |
| Filter (pass/stop Hann band), Filter (formula) | Spectral or formula filters. Listed; source location not checked. | R2 (verify) |
| Lengthen (overlap-add) | `Sound_lengthen_overlapAdd`, `fon/Sound.h:344`. Factor 1.5 standard; manual says values over 3 do not work. Read. | R3 |
| Deepen band modulation | `fon/Sound.h:345`. Listed. | R3 |
| Change gender / Change speaker | `dwtools/Sound_extensions.h:151`. Depends on formant and pitch tools. Listed. | R3 |
| Sound & Formant: Filter; Sound & FormantGrid: Filter; LPC & Sound: Filter | Filters driven by formant or LPC objects. Listed. | R3 (with Formant and LPC) |

Resampling and pre/de-emphasis are both short, well-specified, and used in the analysis pipeline (pitch and formant analysis also resample internally: `dwtools/Sound_to_Pitch2.cpp:113`, `dwtools/Sound_extensions.cpp:2800`). Use independently generated acceptance fixtures for these primitives; record attribution/licensing for any reused reference tests. The exact numerical output of the sinc resampler must be compared against the old binary, because Praat users compare numbers across versions.

### Articulatory synthesis (`praat-source\artsynth`)

What is there. The folder has 34 files and about 3,450 lines of C/C++ and headers (counted with `wc`). The pieces are:

- **Speaker**: kind is "Female", "Male" or "Child"; 1 or 2 vocal-cord masses (`artsynth/Speaker.h`).
- **Articulation (Art)**: 29 named muscle activities, each 0 to 1 (`artsynth/Articulation_enums.h`; 30 enum lines including the placeholder at index 0).
- **Artword**: a time-indexed track of targets for each muscle (`artsynth/Artword.h`, `Artword_setTarget`).
- **Vocal tract model**: `Speaker_to_Delta.cpp` (366 lines) and `Delta.h`, a tube model where each tube segment has coupled mass and spring terms and left/right neighbours. Source comments cite equation numbers from Boersma (1998).
- **Synthesis**: `Artword_Speaker_to_Sound.cpp` (436 lines) steps the model with `oversampling` substeps per sample (`Dt = 1/fsamp/oversampling`). It can also output three width, pressure and velocity Sounds.
- **Editing and display**: `ArtwordEditor.cpp`, plus drawing and a "Play movie" command in `praat_Artsynth.cpp`.

Build wiring. It is a separate static library (`artsynth/Makefile`, `artsynth/meson.build`). The meson file passes `gtk_dep` as a dependency of the library, so the synthesis core is linked to GTK. The reimplementation would have to separate that before porting.

Cost and evidence. The manual says the example utterance takes about five minutes on a 1997 computer and about one second on a 2019 computer (`Articulatory_synthesis.html`, step 11). Neither figure was measured here. The test folder contains an example file `test/fon/examples/hallo.Artword` and a manual movie script `test/manually/movies.praat`. There are no automated tests for the synthesis output.

Recommendation: articulatory synthesis is an R3 candidate. Reasons: it is a self-contained physics model with about 3,400 lines and no automated tests; and it depends on a drawing layer and an editor that the reimplementation has not designed yet. Whether any of the owner's projects needs it was not checked. Consider an appropriately licensed Artword fixture for future format tests; verify redistribution rights before committing any upstream example.

### Consolidated phasing

R1 tests analysis-internal resampling/pre-emphasis as scientific primitives. R2 adds user-facing transforms, filters, scripted Manipulation and overlap-add only after Pitch/PointProcess/tier tests pass. R3 covers the ManipulationEditor and additional resynthesis modes, articulatory synthesis, movies and specialized models. Historical v1/v2 recommendations in the contributor report are superseded by the release map in this master. Empty modes must return an explicit unsupported-operation error; never an apparently successful empty Sound.

### Open items

- Whether the Manipulation overlap-add here equals the PSOLA of the literature: **unverified**. Compare outputs on a reference sound before claiming equality.
- Filter (pass/stop Hann band) and Filter (formula): source location not checked.
- Speed figures for articulatory synthesis: from the manual, **not measured**.
- No code was compiled or run, so no output was compared with the existing binary.
- Whether the owner's own projects need articulatory synthesis: not established. This is the owner's decision.


## 14. Workspace UI, menus, dialogs and keyboard routing

Base path for citations: `praat-reimplementation\praat-source\docs\` (abbreviated `docs/`). Manual pages are `docs/manual/<Name>.html`; screenshots are `docs/pictures/` or `docs/manual/<Name>_N.png`. Claims marked **[unverified]** were not checked against Praat's C/C++ source, which this section did not read.

### Window model

- **Objects window** (`docs/manual/Objects_window.html`). Left: the List of Objects, numbered ("1. Sound 1"). Right: the Dynamic menu, a column of buttons that depends on the selected object's class. Bottom-left fixed buttons: Rename..., Info, Copy..., Remove, Inspect. Top menus: Praat, New, Open, Save (dynamic; empty when nothing is selected), Help. `docs/pictures/screenshot-3.png` shows a Sound selected: View & Edit first, then Play, Draw >, Query >, Modify >, Annotate >, Analyse periodicity >, Analyse spectrum >, To Intensity..., Manipulate >, Convert >, Filter >, Combine >, with "Sound help" above them. The "Sound help" button and the Analyse-periodicity/spectrum groupings are not described in `docs/manual/Dynamic_menu.html`; this is version drift **[unverified which version is newer]**.
- **Picture window** (`docs/manual/Picture_window.html`). Menus: File, Edit, Margins, World, Select, Pen, Font, Help. The manual has no screenshot of it; its layout is **[unverified]**.
- **Editors** (`docs/manual/Editors.html`). One window per object or view, titled with the object name. Edits update the in-memory object immediately; persistence is separate. Preserve LangTool unsaved-change protection at object/application close. Removing the object closes its editors; renaming changes titles.
- **Settings (dialog) windows** (`docs/manual/Scripting_2__How_to_script_settings_windows.html`). Any command whose name ends in "..." opens a form. File commands open a platform file selector instead.
- **ScriptEditor** (`docs/manual/ScriptEditor.html`; `docs/pictures/screenshot-2.png`). A text editor with Run and history paste.

### Menu tree (mirrors the reference)

```
Objects window
  Praat      New Praat script / New Praat notebook
             Open Praat script... / Open Praat notebook...
             Goodies >  Calculator..., Difference of two proportions, Formulas, Statistics
             Settings >  program-wide preferences (audio I/O, LongSound settings...)
             Technical >  [contents not read]
             Buttons..., Add menu command..., Add action command..., Quit
  New        Record mono Sound..., Record stereo Sound...
             Sound >  pure tone, from formula, tone complex, gammatone, Shepard tone
             Create TextGrid..., Tiers >, Create Corpus..., Tables >, Stats >, Generics >
  Open       Read from file..., Open long sound file...,
             Read separate channels from sound file...,
             Read Table from comma/semicolon/tab/whitespace-separated file...,
             Read TableOfReal from headerless spreadsheet file...
  Save       (fixed, when selected) Save as text file..., Save as short text file...,
             Save as binary file...; plus dynamic entries (e.g. Table: Save as ...-separated file...)
  Help       manual
  Dynamic    View & Edit, Play, Draw >, Query >, Modify >, ... (class-dependent)

Picture window
  File       Save as PDF / PNG / EPS file..., Save as Windows metafile...,
             Read / Save as Praat picture file..., PostScript settings..., Print...
  Edit       Undo, Copy to clipboard, Erase all
  Margins    Draw inner box, Text left/right/top/bottom..., Marks ... (incl. logarithmic),
             One mark ..., Axes...
  World      Text..., Axes..., Draw line / rectangle / rounded rectangle...,
             Paint rectangle / rounded rectangle...
  Select     Select inner viewport..., Select outer viewport..., Viewport text...
  Pen        Black, Blue, Cyan, Green, Grey, Lime, Magenta, Maroon, Navy, Olive,
             Pink, Purple, Red, Silver, Teal, Yellow, Colour...
  Font       Times, Helvetica, Palatino, Courier; sizes 10, 12, 14, 18, 24; Font size...
  Help

SoundEditor (screenshot-1): File, Edit, Time, Play, Sound, Analyses, Spectrogram,
             Pitch, Intensity, Formants, Pulses, Help
ScriptEditor (screenshot-2): File, Edit, Search, Convert, Font, Run, Help
```

Sources: `Picture_window.html`, `Pen_menu.html`, `Font_menu.html`, `World_menu.html`, `Save_menu.html`, `New_menu.html`, `Open_menu.html`, `Praat_menu.html`, `Goodies.html`, `SoundEditor.html`. The SoundEditor manual page names Analyses, Formants, Pitch, Spectrogram and Play menus but not Time, Sound, Intensity or Pulses, which appear in the screenshot. The manual's ScriptEditor page confirms File, Edit (Clear history, Paste history) and Run; Search, Convert and Font are visible in the screenshot but not described in the text read **[unverified]**. The manual says the Pen and Font menus are text-level choices, and that the "Windows metafile" entry is Windows-specific.

### Keyboard shortcuts

This is a candidate reference inventory, not global key routing. In a focused text field Ctrl/Command-A selects text; timeline Zoom all is active only in its canvas/menu context. Recheck Ctrl versus Ctrl+Shift digit shortcuts, function keys and macOS conventions against D07 before declaring parity. Commands outside the implemented release remain unavailable.

`docs/manual/Keyboard_shortcuts.html` (footer dated 2022-07-01). On Windows and Linux, "Command" is Ctrl, "Option" is Alt, and "Extra-Command" is Ctrl+Shift. Context-dependent meanings are in parentheses. The table below keeps the entries a reimplementation needs first. Mac-only F-key entries are omitted; on Windows and Linux, pitch is F5 and on the Mac it is F10.

| Key (Win/Linux) | Context | Action |
|---|---|---|
| Ctrl-A | Timeline/editor canvas | Zoom all |
| Ctrl-C / Ctrl-V / Ctrl-X | all | Copy / Paste / Cut (Sound: paste after selection; Ctrl-Shift-V paste over) |
| Ctrl-Z / Ctrl-Y | Editable contexts; verify platform convention | Undo / Redo |
| Ctrl-E | Picture | Erase all |
| Ctrl-F / Ctrl-Shift-F | all | Find / Replace (destructive) |
| Ctrl-G / Ctrl-Shift-G | all | Find again / Replace again |
| Ctrl-H | ScriptEditor | Paste history |
| Ctrl-R / Ctrl-T | ScriptEditor | Run / Run selection |
| Ctrl-R | Sound | Reverse selection |
| Ctrl-T | TextGrid | Transcribe interval |
| Ctrl-I / Ctrl-O | Sound | Zoom in / zoom out |
| Ctrl-N | Sound | Zoom to selection |
| Ctrl-L | Objects | Open long sound file... |
| Ctrl-L | Sound | View spectral slice |
| Ctrl-O | Objects | Read from file... |
| Ctrl-P | Picture | Print |
| Ctrl-S / Ctrl-W / Ctrl-Q | all | Save / Close window / Quit |
| Ctrl-U | all | Calculator... |
| Ctrl-M | all | Search Praat manual... |
| Ctrl-1 ... Ctrl-8 | TextGrid | Add interval on tier 1-8 |
| Ctrl-0 | Sound | Move cursor to nearest zero crossing |
| F1 - F4 | all | Get first - fourth formant |
| F5 / Ctrl-F5 / Alt-F5 / Shift-F5 | all | Get pitch / pitch listing / minimum / maximum |
| F6 / F7 / F8 | all | Get cursor / spectral power at cursor cross / get intensity |
| Ctrl-F8 / Alt-F8 / Shift-F8 | all | Intensity listing / minimum / maximum |
| Ctrl-F9 | all | Pulse listing |
| F11 | all | Voice report |
| F12 / Shift-F12 / Alt-F12 / Ctrl-F12 | all | Log 1 / Log 2 / Log script 3 / Log script 4 (Ctrl-F12 may be unavailable) |
| Tab / Shift-Tab | Sound | Play selection / play window |
| Up / Down | Sound | Select earlier / later |
| Shift-Up / Shift-Down | Sound | Move start of selection left / right |
| Ctrl-Up / Ctrl-Down | Sound | Move end of selection left / right |
| PgUp / PgDn | Sound | Scroll page back / forward |
| Esc | all | Interrupt playing |

The manual's "Command-Arrow" and "Extra-Command" entries are translated by the Ctrl and Ctrl-Shift mapping above; that translation is my reading of the convention on the manual page, not a tested mapping **[unverified]**.

### Dialog anatomy

`docs/manual/Scripting_2__How_to_script_settings_windows_1.png` shows the "Sound: Draw" form. Layout: a title bar with a close button; right-aligned labels; text fields in pairs (value and a "(= all)" or "(= auto)" hint); a checkbox ("Garnish"); an option menu ("Drawing method"); a bottom row with Help and Standards on the left and Cancel, Apply and OK on the right, with OK as the default button.

The manual defines the dialog as a script contract:

- A script line is the command name, then the arguments top to bottom and left to right, in the same order as the form.
- Argument types are numeric, boolean (yes/no or 1/0), multiple-choice (option menu and radio box are equivalent in scripts), text, formula (with `~`), file, and colour (a name, a grey value, or an `{r,g,b}` vector).
- The "(= all)" and "(= auto)" hints are display text; zero is the value.
- The ScriptEditor's `#form` / `#endform` header generates a form from a script (`docs/manual/ScriptEditor.html`).
- The history mechanism records each OK as a replayable line (`docs/manual/ScriptEditor.html`, Example 1).

### What must match closely and what can be modernized

**Must match closely (compatibility or user expectations):**

1. For implemented compatibility commands, preserve command names, argument identity and dialog affordances. Scripts, `sendpraat`, Add to fixed menu, Add to dynamic menu and history paste address commands by name (`fixed_menu_commands.html`; `Scripting_8__Controlling_Praat_from_another_program.html`).
2. Argument order, types, defaults and zero-means-all/auto semantics of every form. This is the scripting API.
3. Each accepted command emits one structured history record; native Praat text replay becomes a compatibility gate when its interpreter stage ships.
4. Objects window semantics: numbered list, click replaces selection, Shift-click adds to it (`Shift-click.html`), fixed buttons, and View & Edit as the first dynamic button.
5. Editor pointer semantics: click sets the cursor, drag selects time, Shift-click and Shift-drag act on several marks, Command-click (Ctrl-click) mutes a channel, and the Group button synchronizes windows (`SoundEditor.html`, `Click.html`, `Shift-drag.html`).
6. The context-scoped keyboard table below, after verification on each target platform.
7. Picture window drawing model: world coordinates, margins derived from font size (`Font_menu.html`), the 16 named colours, the four fonts and five preset sizes, and backslash-digraph special characters. Pixel-identical output is not required; the same drawing commands must produce equivalent pictures.
8. Object lifecycle: Remove closes the object's editor, rename updates titles, and editors are independent windows.

**Can be modernized (presentation):**

1. Native file selectors, message boxes and menus. Use the OS dialogs; keep the command names.
2. Dark mode. The Objects and ScriptEditor screenshots are dark, while the SoundEditor screenshot is light. Whether this is an OS theme or a Praat theme is **[unverified]**. Use theme tokens so both modes work.
3. HiDPI and font scaling. Keep layout in logical units; the Picture window's margins already depend on font size.
4. Window chrome. The screenshots' title bars and buttons are not identical; whether they are the OS's own is **[unverified]**.
5. Font families. The manual names Times, Helvetica, Palatino and Courier (PostScript names). Map them to bundled equivalents. Use a tested IPA-capable font and record its license; candidate SIL font archives reported in the reference docs folder include (`docs/Charis-7.000.zip`, `docs/DoulosSIL-7.000.zip`, `docs/CharisSIL-6.200.zip`).
6. Menu bar placement. On macOS the Praat menu sits in the system menu bar (`Praat_menu.html`); on Windows and Linux, in-window menus are acceptable.
7. Graphics export roadmap: PDF/PNG first, SVG/EPS after backend fidelity tests; Windows metafile remains a separate platform-specific capability.
8. Pixel layout, button sizes and the checkbox glyph style.

**Unverified or open:**

- The Picture window layout has no screenshot in the manual.
- Screenshot-1 and screenshot-3 show menus and buttons (Time, Intensity, Pulses, Sound help) that the manual pages read here do not describe. The manual pages carry footers from 2014 to 2023, so the screenshots are probably from a newer build **[unverified]**.
- The platform of the screenshots is not stated; the chrome looks like a GTK-style Linux window **[unverified]**.
- The menu definitions in Praat's source were not read; all menu contents above come from the manual and screenshots.


## 15. Screenshot fidelity, typography and accessible rendering

### 15.1 Inspected visual evidence

The official [TextGrid illustration](https://praat.org/manual/TextGrid_file_formats_1.png) was inspected. It shows a common 0–2.3 second axis, sentence and phoneme interval tiers, an event tier, aligned vertical marks, centered labels, and phonetic glyphs. **It is a publication-style diagram, not an editor screenshot.** It establishes relationships and typography examples, not toolbar positions, active selection colors, or exact editor dimensions.

Use its geometry to create an original fixture: a 2.3-second synthetic recording, two interval tiers and one event tier. Choose original short labels and publish their exact expected times. Reproduce label alignment without copying the manual's entire example.

### 15.2 Proposed editor layout

```text
Menus and document title / unsaved indicator
Label text editor for active interval or event
Waveform pane, optional analysis pane, common cursor
Ordered annotation tiers with tier names and marks
Shared time ruler, playback regions, zoom/navigation controls
Status: selection start/end/duration, active tier, audio status
```

A single affine time transform must position the waveform, analysis overlays, tier marks, selection and ruler. Keep time precision in the core; convert to float scene coordinates only after subtracting the visible origin. This avoids jitter when viewing a narrow span far into a long recording.

At extreme zoom-out, clip labels predictably and reveal full content in the text editor or tooltip. Render visible entities plus a small margin, with binary-search lookup. Maintain high-contrast selection and a non-color cue for the active tier. Support reduced motion and explicit focus states.

### 15.3 Required reference capture set

Capture the same reference executable on each supported platform, recording version, OS, scale, window dimensions, fonts, fixture hash and action sequence:

| Capture | Required state |
|---|---|
| V01 | Annotation alone, all tiers visible |
| V02 | Audio plus annotation, selected interval and populated text field |
| V03 | Zoomed boundary, cursor and selected time range |
| V04 | Point tier with selected event |
| V05 | IPA/combining-mark label at 100% and 200% scale |
| V06 | Boundary drag preview and invalid drop result |
| V07 | Find result, save dialog and unsupported-file error |
| V08 | Large document with vertical scrolling and narrow intervals |

Store reference captures and LangTool captures separately. Annotate differences as behavioral, visual or platform-native. Set quantitative visual tolerances after the reference captures exist.

Proposed acceptance separates geometry from rasterization: assert time alignment numerically, check labels and selection state structurally, and use masked screenshot comparisons for stable canvas regions. Allow OS-specific text rasterization and native window chrome. A deliberate visual modernization must preserve recognizable selection and editing affordances and be recorded as a product decision.


## 16. Shared service contracts and asynchronous integration

These are proposed language-neutral contracts, not existing Praat APIs. Implement fake adapters before integrating.

```text
AudioSource.describe()
  → { sourceId, revision, xmin, sampleRate, frameCount, channels }
AudioSource.readFrames(firstFrame, count, cancellation)
  → { sourceId, revision, firstFrame, frames }
Waveform.request(sourceId, revision, timeRange, channel, pixelWidth, token)
  → { token, coveredRange, minMaxBuckets }
Transport.play(sourceId, revision, startTime, endTime)
  → playbackSessionId
Transport.stop(playbackSessionId)
Transport.position(playbackSessionId)
  → { sourceTime, state, timingQuality }
Analysis.request(sourceId, revision, kind, parameters, range, token)
  → { token, timestamps, valuesOrTiles, units, validity, metadata }
Workspace.openAnnotation(documentId, optionalSourceId)
Workspace.publishCommand(documentId, expectedRevision, command)
  → { revision, changeSet } | typedError
```

Contributors A and B agree on source-time mapping, exclusive/inclusive playback endpoints, frame rounding, multichannel display, cancellation and latency compensation. Represent absent or unvoiced analysis results explicitly; zero is a valid measurement in some domains. Commands and results carry units.

B's playback clock, not a GUI timer, supplies the stopped cursor position. Progress events identify their playback session so an old callback cannot move the cursor during a new session. A source revision change invalidates waveform and analysis caches. Out-of-order results are discarded by token and revision.

C owns command IDs and application-wide shortcut registration. A supplies supported commands, enablement predicates and typed parameters. GUI actions, future scripting and automated fixtures should call the same commands. Headless annotation operations must not require a window or audio device.

A emits content revisions and changed entity IDs. C handles project autosave, object lifecycle and recovery. B receives immutable snapshots or explicit ranges, never mutable UI objects.


### Contract refinements for this master

Audio descriptions also carry `dx,x1,xmin,xmax` rather than assuming `sampleRate` determines the domain. Define whether ranges are closed/half-open and how sample-center rounding works per command. Transport progress includes latency/timing quality; use the source/audio clock to place a stopped cursor, not elapsed GUI timer ticks.

Analysis results include algorithm/version, exact settings, axis units, validity masks and provenance. Cache keys include audio identity/revision, channel policy and every parameter. Cancel stale jobs and ignore out-of-order results by revision/token. A zoom change invalidates viewport-specific spectrogram tiles without silently replacing a persistent analysis object. GUI and CLI scientific results must be identical for identical snapshots/settings.

One affine time transform and shared selection model serve all panes. Preview drag state is transient; release commits one transaction. A grouped move is atomic across all affected tiers. A command rejected for stale revision changes nothing. Recovery writes and expensive analyses run outside the GUI thread without bypassing the command layer.

## 17. Cross-platform deployment, validation and release gates

### Platform baseline

| Target | First release | Verification |
|---|---|---|
| Windows 11 x64 | Required | Scaling, paths, Qt/native libraries, devices, shortcut contexts |
| macOS 14+ Apple Silicon | Required | Retina, menu conventions, Unicode/IME, bundle and audio |
| Ubuntu 24.04 x64 | Required | Wayland/X11, platform plugins/fonts, audio and packaging |
| Intel macOS / Windows ARM64 / Linux ARM64 | Follow-up | Advertise only after build and behavior coverage |
| Browser/mobile | Deferred | Separate filesystem, input, timing and deployment design |

These are proposed verification baselines, not results. Package on the target OS; test from a clean environment. Record signing/notarization status and bundled native dependencies. Do not use browser/Playwright jobs as desktop Qt acceptance tests. Real audio-device smoke checks supplement deterministic fake-sink tests; headless CI alone cannot validate playback latency.

### Oracle and fixtures

Pin one source build or binary as primary oracle. A headless source build is useful for numerical jobs; released binaries serve drift checks, not an interchangeable second baseline. Verify actual build commands and executable names at M0; inherited `praat_barren` instructions are not an executed build here. Record executable checksum, source commit, build flags, compiler, OS/CPU and precision differences.

Each manifest includes fixture ID, input hash/license, generator/seed, oracle metadata, complete settings, command, output schema, comparison rule, observations, evidence paths and known deviations. Keep original generated inputs common to both applications so different synthesis routines cannot mask analysis differences.

Use silence, impulses, DC, clipping, sine/harmonic complexes, chirps, seeded noise, gaps, very short files, stereo differences and original/licensed speech. Respect Nyquist: a 192 kHz fixture cannot represent an unaliased 100 kHz sine; either raise the rate or mark that case explicitly as aliasing. Restricted TIMIT-derived examples and unlicensed upstream audio must not enter a public corpus.

### One comparison policy

1. Verify object type, frame/entity counts, time/frequency coordinates, units and undefined masks before numeric error.
2. Compare numeric values with predeclared fixture-specific tolerances; compare discrete candidates, voicing and path decisions separately.
3. Compare interchange semantics, not comments, whitespace or arbitrary container headers. Reserve byte equality for LangTool's own deterministic-writer regression tests.
4. Compare stable canvas geometry and data overlays separately from OS font rasterization and chrome.
5. Freeze expected outputs and tolerances before evaluating an implementation; oracle bumps require an explicit manifest/output review.

The inputs proposed conflicting pitch/formant/spectrogram tolerances. No single number below is a measured accuracy guarantee. Use these as an initial R1 budget to ratify at M0; stricter primitive and diagnostic budgets remain useful research targets, not competing release gates.

| Quantity | Proposed R1 budget | Additional required checks |
|---|---|---|
| Sample/frame coordinates | 1e-9 s after identical grid construction | Exact counts, origins and step definitions |
| PCM export | Half quantization step away from clipping, with declared rounding/no dither | Endpoint clipping and half-integer ties |
| Stable synthetic voiced F0 | 1% relative | Octave errors separately; voicing/path masks explicitly |
| Speech F0 | Publish per-frame and distribution errors; ratify corpus gate | No average-only pass, classify near-ties |
| Synthetic vowel formants | max(20 Hz, 2%) starting budget | Bandwidths, counts, ordering and root matching |
| Intensity | 0.1 dB nonsilent interior frames | Silence convention, channels, local mean and averaging |
| Spectrogram power | 0.5 dB defined valid nonsilent bins | Physical/effective window, PSD units, edges, floor and coordinates |
| TextGrid | Exact decoded labels/entity order and round-trip doubles | Full/short/encoding/comment variations |
| Playback | Threshold set by deterministic/loopback measurement | Source-clock stop, latency, session identity |

Detailed pitch tiered budgets, 0.01 Hz formant guesses and 0.1 dB spectrogram proposals in research notes are diagnostic hypotheses. They do not override this table or establish achieved parity. Near-decision cases require explanations; failing structural/undefined-state checks cannot be excused by a broad numeric tolerance.

### Scientific acceptance cases

- Waveform/time: preserve samples, rate, channels and centers at 16/44.1/48 kHz; test nonzero origin and extraction with preserved/zeroed times.
- Spectrogram: single tone, two nearby tones at different window lengths, impulse, chirp and silence; compare grids and PSD before grayscale.
- Pitch: tones, harmonic complexes, noisy vowels, creak, octave transitions and gaps; vary floor/top/step/thresholds and report candidates as well as F0.
- Formants: known source-filter vowels and licensed speech; vary ceiling, half-integer formant count, window, pre-emphasis and auto/explicit step. Test resampling independently.
- Intensity: DC offset, silence, amplitude doubling (about +6.0206 dB), unequal stereo channels and distinct dB/energy/sones means.
- Annotation: full/short text imports, quotes/multiline/IPA/trigraph preservation, mixed domains, malformed input, point duplicates, split decision table, group drags and undo atomicity.
- Workspace: rename/remove/copy lifecycle, stale result rejection, save failures/conflicts/recovery, close during playback/analysis and absent devices.
- Automation: identical core outputs/settings through GUI, Python and CLI. Native script fixtures run only after their supported command/language subset is declared.


### Annotation end-to-end acceptance scenarios

| ID | Action | Pass condition |
|---|---|---|
| A01 | Create annotation from nonzero-origin audio | Correct domains, ordered tier types, independent object |
| A02 | Select interval, type IPA and switch tier | Correct text target; no composition or text loss |
| A03 | Insert at caret and undo | Reference label split; exact original restored |
| A04 | Split with time and text selections | Every decision-table case matches captured reference |
| A05 | Drag boundary, then group-drag | Correct geometry and one undo step per gesture |
| A06 | Attempt duplicate or crossing edit | No corrupt or partial mutation |
| A07 | Remove boundary between equal/different labels | Pinned-runtime merge rule, including D03, and no invented whitespace |
| A08 | Play selection and stop halfway | Audible range and stopped cursor meet agreed timing tolerance |
| A09 | Import, edit, export and reopen in Praat | Semantic content and time precision retained |
| A10 | Find across active tier | Correct entity, highlighted substring and verified wrap behavior |
| A11 | Open without audio, save, recover | Annotation remains fully usable |
| A12 | Close during analysis or device change | No crash, stale callback or missing committed edits |

Measure playback timing tolerance using loopback or a deterministic fake sink before setting a release threshold. A passing UI timer test cannot establish audio timing parity.


The following are proposed targets to validate, not measured results:

| Scenario | Initial target | Measurement |
|---|---|---|
| Cursor/drag on ordinary desktop | p95 interaction response below 50 ms | Timestamp input, state update and next frame |
| Active gesture rendering | Aim for 60 Hz | Profile frame time with dense visible tiers |
| One-hour recording | Bounded audio memory | No full decoded recording required for navigation |
| 100,000 annotation entities | Smooth viewport navigation | Load, pan and edit with most entities offscreen |
| Analysis during editing | No GUI blocking | Cancel stale jobs; profile worker saturation |

Declare benchmark hardware, file formats, cache state and memory budgets when measuring. Profile import separately from drawing. Annotation commands should use sorted lookup and localized change sets; do not serialize the full project on every pointer move.

Device loss must stop transport cleanly without dropping edits. Missing analysis support must leave annotation usable. A worker error should appear once with useful context and preserve the current document. Avoid network dependencies for opening, editing and exporting local files.


### CI and release gate

Run domain/numerical/codec tests on Linux, Windows and macOS on every PR, without a device dependency. Run Qt GUI smoke and artifact comparisons per platform; run a quick pinned-oracle subset on PRs and a full corpus/parameter matrix before release. Cache immutable oracle artifacts by checksum. Perform a reference drift check on Windows/macOS at every oracle bump. Test packaged launch on clean hosts and record manual device checks.

A release report must state the supported workflow/format/command matrix, passed fixture manifest, numerical error distributions, measured performance, per-platform results and known deviations. No “Praat compatible” claim extends beyond that matrix. Two weeks of green nightly runs can be useful soak evidence but are not a substitute for explicit gates or an unconditional schedule commitment.

## 18. Delivery milestones, unresolved discrepancies and maintenance

### Milestones and responsibilities

| Milestone | Work and handoff | Exit condition |
|---|---|---|
| M0 — reference and contracts | Pin oracle/manuals/dependencies; ratify R1; agree source-time/selection/channel rules and budgets; capture initial UI states | Reproducible manifests, adapter contracts and resolved release-blocking semantics |
| M1 — headless foundation | Domain/registry, WAV I/O, TextGrid codec/commands, fake transport and original fixtures | Time/codec gates and rejected-operation atomicity pass on three systems |
| M2 — usable annotation | Workspace and editor, native text/IME, selection, drag, search/undo and actual transport | Annotation A01–A12 plus cross-platform interaction checks |
| M3 — validated analysis | Spectrogram, filtered AC pitch, Burg and intensity with cancellation/caches; Python API and CLI | All R1 numerical/structural gates, shared GUI/CLI outputs |
| M4 — release | Recovery/conflicts, screenshots/accessibility, performance and clean packages | Published compatibility report and every R1 row complete |
| M5 — expanded compatibility | R2 scripting stages, voice/graphics/transforms/codecs, then R3 | Separate scoped acceptance matrix per addition |

These are dependency gates, not fixed sequential weeks; A/B/C can work against fake adapters in parallel. Retain a rough 22-week envelope only for capacity discussion after M0 estimates. Do not retain incompatible 20/22-week promises or skip weeks without assigning integration work.

### Discrepancy register

| ID | Observation | Master treatment / next evidence | Owner |
|---|---|---|---|
| D01 | Sound/Vector/Matrix described as inconsistent | Resolved by pinned `Vector : Matrix`; still fixture-test every serialized class | B |
| D02 | Sound origins differ between reports | Use explicit sampled axes and sample-center mapping; no implied origin | B + A |
| D03 | Equal-label boundary deletion differs in manual/source | Pinned source helper concatenates non-null labels; manual says equal labels retained once. Capture actual editor/command paths for chosen build and freeze chosen rule | A |
| D04 | Spectrogram 50 versus 70 dB and 1000/250 versus 1500/500 grid steps | Separate Paint/editor contexts and saved preferences; capture reset forms at pinned runtime | B + A |
| D05 | Pitch top/ceiling and above-ceiling candidate handling | Distinguish raw and filtered methods, recruitment versus selected voicing; test near thresholds | B |
| D06 | Point movement said to cross neighbors versus proposed rejection | Preserve sorted point times after any reorder, reject duplicates; reference-run crossing selection/ID behavior | A |
| D07 | Annotation hit/drag millimeter thresholds and tier shortcuts | Candidate 1.0/1.5/1.2 mm thresholds and modifier/digit/function-key variants require DPI/platform capture | A |
| D08 | Strict `ooTextFile` first-line claim contradicts full header example | Accept documented header/token forms through codec fixtures; never require only a bare quoted line | A |
| D09 | Legacy text encodings and trigraph conversion | Raw literal storage/round trip; explicit display/conversion and encoding selection, no silent normalization | A |
| D10 | Shorten/Ogg/Opus and float-WAV behavior | Capability table per actual decoder build; unsupported until verified; no inherited unverified float scaling | B |
| D11 | Binary order/string encoding and legacy chronological files | Deferred codecs, not inferred from host representation | A + B |
| D12 | Formula/native scripting called R1 in one input and deferred in others | R1 Python API/CLI; native syntax in staged R2/R3, shared registry from M1 | C |
| D13 | Contradictory tolerance tables and byte-equality gates | Authoritative comparison policy in section 17; retain research numbers only as diagnostic proposals | All |
| D14 | Live UI screenshots absent from consolidation | Capture V01–V08 with exact platform, dimensions, fonts and fixture hashes; inherited screenshot notes remain reported evidence | A + C |
| D15 | Source-informed research called clean-room | Do not make that claim; maintain provenance/reuse ledger and review copied materials explicitly | All |

The D03 source behavior was rechecked during consolidation in the pinned `IntervalTier_removeLeftBoundary` helper: equal nonempty labels follow the concatenation branch. This is not a runtime observation. Preserve the counterexample fixture (equal labels on adjacent intervals) as a release-blocking test instead of erasing the discrepancy.

### Licensing, reuse and data provenance

Default to independently implementing behavior from manuals, published methods and recorded experiments; no direct code reuse is selected by this master. If a legacy component is excellent enough to propose reuse, document exact file/revision, reason, changes, test evidence, license and notices before inclusion. General scientific libraries still require their own dependency/notice inventory.

The Praat README describes mixed file-level GPL terms and an overall GPL-3-or-later distribution; documentation, fonts, screenshots and vendored libraries have their own terms. Consult the actual notices for each reused item. Do not infer the new project's license from a metadata file, and do not make blanket legal claims about all browser delivery or all generated outputs. Choose and record the project's distribution/license policy with the maintainers; this document is not a legal determination.

Do not describe source-informed research as a verified clean-room process. Keep logs of sources consulted and isolate oracle experiments from shipped application dependencies. Generated/original fixtures are preferred; redistributable speech needs per-file license/consent records. Product naming and any copied font/image/manual material need explicit provenance. These are release tasks for materials actually used, not a reason to stop independent documentation or implementation work.

### Risks and mitigations

| Risk | Effect | Mitigation |
|---|---|---|
| Scope expands into all of Praat | Unfinishable initial release | Keep authoritative R1/R2/R3 matrix and milestone gates |
| Wrong frame or sample origins | Every plot/query appears plausible but is shifted | Axis fixtures before numerical comparisons |
| DSP near-ties and precision differ by platform | Candidate/path flips | Oracle noise-floor measurement, classified mismatches and no blanket bit-equality claim |
| Invalid or non-atomic annotation edit | Research labels lost or geometry corrupted | Invariant validation, stable IDs, command inverse and grouped transaction tests |
| Codec assumptions lose content | Files reopen incorrectly in Praat | Bidirectional semantic fixtures, precision-safe writing, explicit unsupported cases |
| Qt/input methods/fonts differ | Lost text or illegible IPA | Native text controls, IME and high-DPI fixtures on all systems |
| Python hot loops block interaction | Unresponsive editor | Worker isolation, profiling, localized updates, measured acceleration |
| Oracle/manual drift | Contradictory defaults/behavior | Immutable manifests and explicit reference bumps |
| Permission or package failures | Export/install unusable | Atomic save, clean-machine bundles and failure fixtures |
| Three plans diverge again | Duplicate/conflicting work | This file is the single specification; update topic sections and discrepancy register together |


## 19. Primary references and research navigation

Original research accessed 2026-11-02; consolidated 2026-11-04. Manuals are living pages; implementation work must bind them to the selected reference release. Library links justify proposed roles, not proven compatibility of this unbuilt application.

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


Additional primary references for the integrated detailed chapters:

- [Pinned Praat tree](https://github.com/praat/praat.github.io/tree/56ed24ef5efedffd06112a2bc1c0530bddc3a55e): contributor source-relative paths above resolve here, including `fon/`, `foned/`, `melder/`, `sys/`, `dwsys/`, `artsynth/` and `docs/`.
- [Pinned Vector inheritance](https://github.com/praat/praat.github.io/blob/56ed24ef5efedffd06112a2bc1c0530bddc3a55e/fon/Vector.h) and [TextGrid domain operations](https://github.com/praat/praat.github.io/blob/56ed24ef5efedffd06112a2bc1c0530bddc3a55e/fon/TextGrid.cpp).
- [TextGrid annotation area](https://github.com/praat/praat.github.io/blob/56ed24ef5efedffd06112a2bc1c0530bddc3a55e/foned/TextGridArea.cpp) and [editor composition](https://github.com/praat/praat.github.io/blob/56ed24ef5efedffd06112a2bc1c0530bddc3a55e/foned/TextGridEditor.cpp).
- [Objects window](https://praat.org/manual/Objects_window.html), [SoundEditor](https://praat.org/manual/SoundEditor.html), [keyboard shortcuts](https://praat.org/manual/Keyboard_shortcuts.html), [Picture window](https://praat.org/manual/Picture_window.html), [ScriptEditor](https://praat.org/manual/ScriptEditor.html).
- [Manipulation](https://praat.org/manual/Manipulation.html), [articulatory synthesis](https://praat.org/manual/Articulatory_synthesis.html), [Voice](https://praat.org/manual/Voice.html), [PointProcess](https://praat.org/manual/PointProcess.html).
- [Official SoundEditor image](https://praat.org/pictures/screenshot-1.png), [ScriptEditor image](https://praat.org/pictures/screenshot-2.png), [Objects image](https://praat.org/pictures/screenshot-3.png), [annotation illustration](https://praat.org/manual/TextGrid_file_formats_1.png). The comprehensive contributor reported inspecting the first three; this consolidation does not claim new live UI captures.

Keep these sources bound to the chosen release when implementing. A source link, source-reading claim or proposed test is not a passing compatibility result.
