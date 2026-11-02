# Praat Reimplementation: Design Document

**Status:** Draft, generated 2026-11-02 from twelve section reports. Not reviewed by the project owner.
**Reference:** Praat source and manual in `praat-source/` (this workspace).
**Target:** Cross-platform (Windows, macOS, Linux), modern libraries, behaviour replicated from Praat.

## Open decisions (read first)

These conflicts were found while writing the sections. They are not resolved here.

1. **Stack:** Section 2 recommends Python (NumPy/SciPy, Qt via PySide6). The earlier draft `REIMPLEMENTATION.md` recommends TypeScript with Web Audio. One of these must be chosen.
2. **Licensing:** Praat's source is GPL-3.0-or-later. Clean-room versus derived code needs the owner's decision (Section 12).
3. **Sound class:** `fon/Sound.h` declares Sound as a Vector, but `Sound_create` builds a Matrix (Section 3).
4. **Shorten:** The manual lists it as readable, but the source rejects it (Section 3).
5. **TextGrid boundary removal:** The manual and source disagree on merging text (Section 5).
6. **Spectrogram dynamic range:** The manual says 50 dB, the editor preferences say 70 dB (Section 4).
7. **Pitch ceiling:** The manual says candidates above the ceiling are ignored, but the code does not enforce this (Section 6).
8. **Schedule:** The earlier draft totals 20 weeks in one place and 22 in another (Section 12 uses 22).

Every section marks what it could not verify. Nothing has been compiled or run against the reference binary.

---

## 1. Scope and feature inventory

**Sources.** All feature claims come from the Praat manual web copy in `praat-source/docs/`. The top-level list is `praat.html` (identical to `index.html`), which gives the "Functionality" summary. Area detail comes from the files under `docs/manual/`, cited by file name below. Paths are relative to `docs/manual/` unless shown otherwise.

**Priority scale.** These labels are my recommendation for a first reimplementation. They are not claims made by the manual.

- **Core**: the basic record, view, analyse, annotate loop does not work without it.
- **Important**: needed before the tool can replace Praat for ordinary phonetics work. It can follow the first release.
- **Optional**: specialised, depends on external models or hardware, or is outside Praat's core acoustic toolkit. Defer.

Anything I could not check in the manual is marked *unverified*.

### 1.1 Feature inventory

| Area | What the manual says it does | Priority | Why |
|---|---|---|---|
| Objects | Objects live in memory, not in files. They are made from New/Open, listed in the Objects window, and written with Save (`objects.html`). Types include Sound, LongSound, TextGrid, Pitch, Formant, Intensity, Spectrogram, Ltas, Manipulation, Matrix, Table (`Types_of_objects.html`). | Core | Every other area operates on these typed, named objects. The object model is the user model. |
| Objects window | Left: List of Objects. Right: Dynamic menu, whose commands depend on selected types. Fixed buttons: Rename, Info, Copy, Remove, Inspect. Menus: Praat, New, Open, Save, Help (`Objects_window.html`, `Dynamic_menu.html`). | Core | This is the main window. Selection-driven commands are the central interaction pattern. |
| Sound: model and queries | Sampled waveforms. Queries cover structure (sample count, sampling period), content (value at time), shape (min, max, zero crossing), statistics (mean, RMS, SD), and energy (`Sound.html`). | Core | Basic analysis and the base for all other objects. |
| Sound: file I/O | Reads WAV, AIFF/AIFC, NeXT/Sun .au and NIST as standard types, plus proprietary types (`Sound_files_3__Files_that_Praat_can_read.html`). Writes WAV, AIFF, AIFC, NeXT/Sun, NIST and FLAC, all 16-bit (`Sound_files_4__Files_that_Praat_can_write.html`). Also text and binary object formats (`Sound.html`). | Core (WAV, 16-bit linear); Important (rest) | Files come first. WAV covers most use. The other formats are needed for compatibility. Read support for MP3, Ogg Vorbis and Opus is listed in `Sound_files.html`; I did not verify the full read list. |
| Sound: editing | Formula (`Sound__Formula___.html`), extract part, resample, scale peak and intensity, fade, set value, pre- and de-emphasis, remove noise, trim silences. | Important | Simple DSP. Most is not needed to view and annotate a recording. |
| Playback and recording | Sound: Play; Record mono and stereo Sound through the SoundRecorder window (`Sound__Play.html`, `Record_mono_Sound___.html`, `Record_stereo_Sound___.html`, `SoundRecorder.html`). | Core (playback); Important (recording) | The editor is unusable without playback. Recording can wait, since files can be read. |
| LongSound | File-based sound for long recordings, opened with Open long sound file (`LongSound.html`, `Sound_files_3...`). `praat.html` states sound files up to 2 GB (about 3 hours). | Important | Needed for real corpora. Not needed for first demos. |
| SoundEditor and TextGridEditor | Each object type has its own editor window. Edits take effect immediately (`Editors.html`). The SoundEditor overlays analyses on the waveform (`Intro_2_2__Viewing_and_editing_a_sound.html`). | Core | This is the working view for the core loop. |
| Other editors | PitchEditor, PointEditor, PitchTierEditor, IntensityTierEditor, DurationTierEditor, SpectrumEditor, ArtwordEditor, OTGrammarEditor, and Inspect for any type (`Editors.html`). | Optional (most) | Each editor follows the matching feature. Build them with those features. |
| Spectrogram and spectrum | Spectrogram is PSD in Pa^2/Hz on a time-frequency grid, with the attributes listed in `Spectrogram.html`. Spectral slices give a Spectrum object (`Intro_3_6...`, `Intro_3_8...`). Analysis: `Sound__To_Spectrogram___.html`. Pitch-dependent variant: `Sound__To_Spectrogram__pitch-dependent____.html`. | Core (spectrogram, slice); Optional (pitch-dependent) | The main visual analysis. The pitch-dependent variant is a refinement. |
| Ltas | Long-term average spectrum in dB/Hz, with bin and statistics queries (`Ltas.html`, `Sound__To_Ltas__pitch-corrected____.html`). | Optional | Not in the `praat.html` functionality list. |
| Filtering | Frequency-domain band filters (pass and stop Hann band, formula). Time-domain IIR one-formant, pre-emphasis and de-emphasis, plus in-place variants. Convolution (`Filtering.html`, `Sounds__Convolve___.html`). | Important | Easy DSP that users reach for often. In-place variants need care with object state. |
| Pitch | A Pitch object is periodicity candidates per frame. Methods: filtered autocorrelation (for intonation), raw autocorrelation, raw cross-correlation (for voice analysis), filtered cross-correlation, and SHS (`Pitch.html`, `Sound__To_Pitch__shs____.html`). Default floor 75 Hz and ceiling 600 Hz (`Voice.html`, `Sound__To_Pitch__ac____.html`). Path finding selects a smooth track. Settings: `Pitch_settings___.html`. | Core (filtered autocorrelation, with PitchEditor and Draw); Important (other methods) | Pitch is central to intonation work and feeds Manipulation and Voice. Other methods are needed for voice work. |
| Pitch derived objects | PitchTier, Smooth, Interpolate, To PointProcess, To PitchTier (`Pitch.html`, `Pitch__Smooth___.html`, `Pitch__Interpolate.html`, `PitchTier.html`). | Important | Needed for Manipulation and for pulse-based analysis. |
| Formant | A Formant object gives frequency and bandwidth per formant, per frame (`Formant.html`). Burg method with time step, maximum formants (5 is typical for speech), formant ceiling, window length and pre-emphasis (`Sound__To_Formant__burg____.html`). Variants: keep all, sl, robust (`Formant.html` links). Tracking and drawing: `Formant__Track___.html`, `Formant__Draw_tracks___.html`. | Core (Burg, tracks, draw); Important (keep all, sl, robust) | Formant analysis is one of the main functions. Burg is the standard path. The variants are refinements. |
| FormantPath, FormantGrid | Formant path and time-stamped FormantGrid (`FormantPath.html`, `FormantGrid.html`). | Optional | Specialised follow-on to the formant tracker. |
| LPC | Autocorrelation, covariance, Burg and Marple methods. Conversion to Formant and spectrum, and LPC filtering (`LPC.html`, `Sound__To_LPC__burg____.html`, `Formants___LPC_menu.html`). | Important (Burg first) | LPC is the basis of the formant tracker and of LPC resynthesis. |
| Intensity | Intensity contour in dB SPL (re 2e-5 Pa), at linearly spaced times, with statistics, IntensityTier, and To TextGrid (silences) (`Intensity.html`, `Sound__To_Intensity___.html`, `Intensity__To_TextGrid__silences____.html`). | Important | Listed under the analysis functions in `praat.html`. Silence detection depends on it. |
| TextGrid and annotation | Interval and point tiers. Created from Sound or LongSound (To TextGrid), Create TextGrid, or merged (`TextGrid.html`, `Intro_7__Annotation.html`). Edited in TextGridEditor. Saved as text or short text, or binary (`TextGrid_file_formats.html`, `Intro_7...`). Labels on several tiers, plus the phonetic alphabet (`praat.html`). | Core | `praat.html` names labelling and segmentation as a main function. The text TextGrid format is the main interchange with users' existing data. |
| TextGridNavigator | Search tiers across TextGrids (`TextGridNavigator.html`). | Optional | Described only by its page title. Detail *unverified*. |
| Transcription and diarisation | Whisper.cpp transcription needs an external ggml model. Diarisation uses an adapted pyannote.audio pipeline. Silero VAD for speech activity (`Speech_recognition.html`, `speech_activity_detection_with_Silero_VAD.html`, `TextGrid___Sound__Transcribe_interval___.html`). | Optional | Depends on large external ML models. The newest area. Defer. |
| Manipulation | Bundles the original Sound, glottal pulses (PointProcess), a PitchTier and a DurationTier. Resynthesis by overlap-add, by LPC, or as a pulse train or hum (`Manipulation.html`, `Intro_8__Manipulation.html`). | Important | Pitch and duration change are in `praat.html`. Overlap-add first. LPC resynthesis later. |
| Source-filter and generators | Create Sound from formula, tone complex, gammatone and Shepard tone (`Sound.html`). Source-filter tutorials (`Source-filter_synthesis.html`). | Important | Generators are easy to build and useful for stimuli. |
| Formula language | Numeric and string expressions, arrays, control structures, attributes of objects (`Formulas.html`, `Formulas_1_1...` to `Formulas_9...`). | Core | Formulas drive Create Sound from formula, Formula commands, and scripts. It is the first thing to build. |
| Scripting language | Variables, jumps, loops, procedures, arrays, vectors, forms, file I/O, system calls, object selection, and query commands (`Scripting.html`, `Scripting_5__Language_elements_reference.html`, `Scripting_6...`, `Scripting_4...`). | Core (interpreter, object selection, queries, forms); Important (the rest) | Many users work only by script. Full compatibility with older scripts is a later goal. `Scripting_10__Old_functions.html` covers legacy names. |
| Scripting: editors and IPC | Editor blocks (`Scripting_7...`), sendpraat and `praat --send` (`Scripting_8...`, `Scripting_6_9...`), stand-alone programs (`Scripting_9...`). | Optional | Inter-process and standalone builds need a stable core first. |
| Picture window | Drawing commands write to the Picture window: margins, marks, axes, text, pens, fonts (`Picture_window.html`, `Draw_menu.html`). | Important | Drawing is how results reach papers. On-screen drawing can start the work. |
| Picture export | Save as PDF, PNG, EPS, Windows metafile, plus a Praat picture format (`Picture_window.html`). `praat.html` lists PDF, PNG and EPS. | Important | Output quality matters for the target users. Start with PDF and PNG. |
| Voice analysis | Pulses from the waveform. Voice report: voice breaks, five jitter measures, shimmer, and harmonicity (`Voice.html`, `Voice_report.html`, `Voice_1...` to `Voice_4...`). | Important | Listed in `praat.html` under speech analysis. Depends on Pitch and PointProcess. Not in the user's original list. |
| Articulatory synthesis | Speaker and Artword objects produce a Sound (`Articulatory_synthesis.html`, `Artword.html`, `Speaker.html`). Math is in Boersma (1998), cited there. | Optional | Separate physical model with its own editor. Heavy computation. The manual's timing claims (5 minutes on a 1997 machine, about 1 s on 2019) are *unverified* on current hardware. |
| Klatt synthesis | KlattGrid: source-filter model with separate tiers for pitch, flutter, voicing, formants and nasal terms (`KlattGrid.html`, `Create_KlattGrid___.html`). | Optional | Listed in `praat.html` ("Klatt acoustic synthesis"). Not in the user's list. Large parameter set. |
| Speech synthesis (TTS) | SpeechSynthesizer wraps eSpeak NG (`SpeechSynthesizer.html`). | Optional | External dependency. |
| Cochleagram and Excitation | Bark-based excitation patterns over time (`Cochleagram.html`, `Excitation.html`). | Optional | Listed in `praat.html`. Specialised. |
| Matrix, Table, statistics | Matrix, Table, TableOfReal, Configuration and similar. Multidimensional scaling, PCA, discriminant analysis (`Types_of_objects.html`, `praat.html`). | Important (Matrix, Table as substrate); Optional (statistics) | Matrix is the substrate for formulas. The statistical methods are a separate family. |
| Learning algorithms | Feedforward neural networks, stochastic Optimality Theory (`praat.html`, `OTGrammarEditor` in `Editors.html`). | Optional | Separate subsystem. |
| Listening experiments | Identification and discrimination experiments (`ExperimentMFC.html`). | Optional | Listed in `praat.html`. Self-contained. |
| Preferences and settings | Settings submenu for audio I/O. Saved preferences for fonts, views, sound devices (`praat.html`, `Objects_window.html`, `preferences_file.html`). | Important | Needed for a usable tool. Keep it simple at first. |

### 1.2 Recommended first-release cut

From the table, a first release would cover:

- Objects, Objects window, and the formula language.
- Sound I/O (WAV at least), queries, playback, and the SoundEditor.
- TextGrid and TextGridEditor, with text save and read.
- Spectrogram and spectral slices.
- Pitch (filtered autocorrelation) with PitchEditor and drawing.
- Formant (Burg) with tracks.
- The scripting interpreter, with object selection, queries and forms.
- Basic Picture window drawing with PDF and PNG export.

Everything marked Important follows next. Optional items come last or are dropped.

### 1.3 Gaps and open points

- The user's list omitted Voice analysis, Klatt synthesis, Cochleagram, Ltas, and the statistics and learning families. These appear in `praat.html` and are included above.
- The manual is a web copy. I did not check it against the Praat source or a specific release. Version-specific details, such as the `ac` to `raw autocorrelation` rename (`Sound__To_Pitch__ac____.html`), need confirming against the target release.
- Not read in detail: `History_mechanism.html`, `plugins.html`, `TextGrid_file_formats.html`, `Intro_8_3...`, `Intro_8_4...`. Claims resting on them are *unverified*.

---

## 2. Architecture and technology stack

### 2.1 Requirements that drive the choice

- **Cross-platform:** Windows 10/11, macOS (Intel and Apple Silicon), and mainstream Linux distributions, from one codebase.
- **Modern, maintained libraries:** no dependency on Motif, Xt, or hand-vendored codecs. Each dependency should have an active upstream and a stable license.
- **Replicate existing behavior:** the reference is Praat's output, not Praat's source code. Numerical results (pitch, formants, intensity, spectrograms) must agree with Praat within stated tolerances, and file formats (Sound, TextGrid, Pitch, Formant, Matrix, Table) must read and write Praat's own text and binary formats.
- **Testable against the reference:** the stack must make differential testing against real Praat cheap.

A licensing constraint shapes the whole design. The Praat source tree is GPL-3.0 (`praat-source/main/gpl-3.0.txt`). If this project does not want to be GPL-3.0, it should not port Praat's C++ code. The specification should come from the Praat manual, the published algorithm papers (Boersma 1993 for autocorrelation pitch, Burg's method for LPC, and so on), and observed Praat output. The Praat source should be used as a behavior oracle only. Whether that policy is acceptable is a question for the project owner and, if needed, a licensing review.

### 2.2 What the reference source shows

The source tree is organized in layers, which the new architecture should mirror where it helps:

| Praat directory | Role | Reimplementation counterpart |
|---|---|---|
| `melder/` | Utilities: file handling, text I/O, `VEC`/`MAT` math, audio I/O (`melder_audio*`, `melder_audiofiles*`) | I/O and platform adapters, numeric utilities |
| `dwsys/` | Numerics (`NUMFourier`, `NUM2`, `Eigen`, `NMF`), `Collection`, `Graphics_extensions` | Algorithm kernels |
| `fon/`, `dwtools/`, `LPC/`, `stat/` | Object types and algorithms: `Sound`, `TextGrid`, `Pitch`, `Formant`, `Intensity`, `Matrix`, `Spectrogram`, `Table`, and so on | Core domain model and analysis modules |
| `sys/` | Graphics abstraction (`Graphics*.cpp` with Screen and PostScript backends), GUI toolkit wrappers (`Gui*.cpp`), `Editor`, `Data`/`DataEditor` | Rendering layer, UI |
| `main/`, `Formula` in `sys/` | Entry point, `praat_*_init` command registration, expression evaluation | Command registry, script host |
| `external/` | Vendored codecs and libraries: portaudio, flac, vorbis, opusfile, lame, mp3, gsl, clapack, glpk, zlib, espeak, whispercpp | Replaced by maintained dependencies (section 2.3) |

Two observations follow. First, `sys/` mixes GUI, graphics, and editor logic, which is the coupling the new design should avoid. Second, the Praat object types are mostly "data plus algorithm" pairs, which map cleanly onto a domain model with separate analysis functions.

### 2.3 Options compared

**Option A: TypeScript, React, Web Audio, and Electron or Tauri.** This is the direction in the existing feasibility report (`REIMPLEMENTATION.md`, section 3.1). Strengths: canvas rendering, a web-first UI, and easy distribution. Weaknesses: the core DSP runs in JavaScript with no mature equivalent of SciPy for signal work, so pitch and LPC code must be written from scratch; Web Audio offers no direct access to AIFF, FLAC, or NIST files; and differential testing needs a Node bridge to Praat or a separate harness.

**Option B: Rust core with Tauri 2 (web UI) or egui (native UI).** Strengths: fast, memory-safe, single binary, and excellent cross-platform packaging. Weaknesses: the Rust DSP ecosystem is thinner for speech-specific work (`rustfft` and `realfft` cover the FFT, but there is no equivalent of Praat's pitch or formant code), and the learning curve is steep for a contributor team that is mostly students.

**Option C: Python core with a Qt GUI.** Core is NumPy and SciPy, the GUI is PySide6 (Qt for Python), and the scripting language is Python. Strengths: the strongest scientific ecosystem, direct access to libsndfile and PortAudio, mature Qt widgets for editor-style UIs, and the option to use Parselmouth (Python bindings to Praat) as a reference oracle in tests. Weaknesses: DSP loops must be vectorized or compiled (numba is an option), and Qt has licensing terms that need to be read (PySide6 is LGPL-3.0; verify current terms).

**Recommendation: Option C.** Praat's users are phoneticians who script in Praat or Python, and the reference-testing requirement favors a stack where Praat itself can be called from tests. The core is pure Python with NumPy and SciPy, which keeps the algorithms readable and easy to check against the papers. The GUI sits behind a thin interface, so a future web front end (Option A) can reuse the core without rewriting it.

### 2.4 Concrete stack

Each version must be checked before use. Versions are not stated here.

| Concern | Choice | Notes | Version |
|---|---|---|---|
| Language | Python 3.11+ (type hints throughout) | | verify current version |
| UI toolkit | PySide6 (Qt 6) | Editors, dialogs, menus, and the Praat-style command palette | verify current version |
| Waveform and spectrogram display | pyqtgraph (`ImageItem`, `PlotItem`) | Fast interactive plots inside Qt | verify current version |
| Publication graphics | Qt painter for on-screen drawing; matplotlib for SVG, PDF, and EPS export | Replaces Praat's Postscript path (`GraphicsPostscript.cpp`) | verify current version |
| Audio playback and recording | sounddevice (PortAudio wrapper) | Replaces `external/portaudio`. Qt Multimedia is the fallback if device control must stay inside Qt | verify current version |
| FFT, filters, linear algebra | NumPy (`numpy.fft`, `numpy.linalg`), SciPy (`scipy.signal`, `scipy.fft`, `scipy.linalg`) | Replaces `NUMFourier`, `Eigen`, `clapack`, and `gsl` use. Praat's windows and Gaussian kernels must be matched explicitly | verify current version |
| Accelerated loops | numba, optional | Only for hot paths such as Burg LPC over long files | verify current version |
| WAV, AIFF/AIFC, FLAC, Ogg Vorbis, Opus, MP3 | soundfile (libsndfile bindings) | libsndfile covers the common formats. Check NIST and Sun/NeXT support, and check Praat's Kay format separately | verify current version |
| Praat text and binary formats | Custom readers and writers in the core | Specified from the Praat manual and checked against sample files | n/a |
| Scripting host | Python for the API. A Praat-script interpreter is a later compatibility layer | Praat's script grammar is documented in the manual | n/a |
| Tests | pytest, hypothesis for property tests, Parselmouth for differential tests | Parselmouth is a Python interface to Praat | verify current version |
| Packaging | briefcase (BeeWare) or PyInstaller for binaries; pip for development | Signing and notarization for macOS; MSIX or installer for Windows | verify current version |
| CI | GitHub Actions matrix over Windows, macOS, and Linux | Runs unit and differential tests on each platform | n/a |

### 2.5 Layers

```
+--------------------------------------------------------------+
| UI layer (PySide6)                                           |
|   Editors: Sound, TextGrid, Spectrogram, Pitch, Table        |
|   Dialogs, menus, command palette, preferences               |
+--------------------------------------------------------------+
| Command layer                                                |
|   Command registry (one entry per Praat menu action)         |
|   Undo/redo, selections, object list                         |
+--------------------------------------------------------------+
| Script host                                                  |
|   Python API (primary)  |  Praat-script interpreter (later)  |
+--------------------------------------------------------------+
| Domain model                                                 |
|   Sound, TextGrid, Pitch, Formant, Intensity, Spectrogram,   |
|   Matrix, Table   (immutable-by-default data + metadata)     |
+--------------------------------------------------------------+
| Analysis modules (pure functions, no UI imports)             |
|   pitch, formant, intensity, spectrogram, manipulation,      |
|   statistics                                                 |
+--------------------------------------------------------------+
| Kernels: NumPy, SciPy, optional numba                        |
+--------------------------------------------------------------+
| I/O and platform adapters                                    |
|   soundfile (audio files) | sounddevice (audio devices)      |
|   Praat text/binary codecs | graphics backends (Qt, SVG, PDF)|
+--------------------------------------------------------------+
```

Rules that make the layering enforceable:

1. The domain model and analysis modules never import Qt, sounddevice, or the script host.
2. The UI never calls kernels directly. It goes through the command layer, so every menu action has one code path that scripts also use.
3. Graphics is an interface (`draw_line`, `draw_text`, `draw_image`, `set_viewport`, and so on) with backends for Qt, SVG, and PDF. This mirrors `sys/Graphics.h`, which Praat uses to get identical output on screen and on paper.

### 2.6 Core object model

Praat's object types map onto a small set of Python classes. Each class is a dataclass-style container with metadata (name, time domain or frequency grid) and numeric arrays. The analysis that creates each object lives in an analysis module, not in the class.

- **`PraatObject`** (base): `name`, `kind` (the Praat class name, used for the object list and file headers), `write(path)`, and `read(path)` classmethod. This replaces `Data`/`Thing` in `sys/Data.h` and `melder/`.
- **`Sound`** (from `fon/Sound.h`): `samples` as a float64 array with shape `(channels, n)`, `sampling_frequency`, and `start_time`. Its time grid is implied: sample `i` is at `start_time + i / sampling_frequency`. Praat's Sound is a 1-D-per-channel `Matrix`, so this matches Praat's layout.
- **`TextGrid`** (from `fon/TextGrid.h`): `start_time`, `end_time`, and an ordered list of tiers. An `IntervalTier` holds sorted intervals `(xmin, xmax, text)`, and a `TextTier` holds points `(time, text)`. Both enforce non-overlap and contiguity when edited, as Praat does.
- **`Pitch`** (from `fon/Pitch.h`): a regular time grid (`dt`, `t1`, `n_frames`) and, per frame, a list of candidate `(frequency, strength)` pairs. Keeping candidates is needed to match Praat's Viterbi path and its unvoiced decisions.
- **`Formant`** (from `fon/Formant.h`): a regular time grid and, per frame, a list of `(frequency, bandwidth)` pairs, with the number of formants per frame stored.
- **`Intensity`** (from `fon/Intensity.h`): a regular time grid and an array of dB values, with the reference level stored.
- **`Spectrogram`** (from `fon/Spectrogram.h`): a time-by-frequency array of power values with both grids. Used for display and for `ComplexSpectrogram` workflows.
- **`Matrix`** (from `fon/Matrix.h`): a 2-D float64 array with `x1, dx, nx` and `y1, dy, ny` grids. `Sound`, `Spectrogram`, and the generic matrix type all reuse it internally.
- **`Table`** (from `stat/Table.h`): named columns with a declared type (`numeric` or `string`) and a row count. `TableOfReal` is a subset that holds only numeric values and row/column labels.

Every object type follows one contract: analysis functions take objects and return new objects. They never mutate their inputs. This matches Praat's "To X" convention (for example, `To Pitch (ac)` returns a new `Pitch`) and makes undo a matter of keeping references.

### 2.7 Open questions for this section

- Whether Python's performance is acceptable for Burg LPC and long-file spectrograms, or whether numba or a small C extension is needed on the critical path. A spike should measure this before the stack is committed.
- Whether Qt's LGPL terms work for the project's distribution plan.
- How much of Praat's script language to support at first. The Python API covers the research use case, and a Praat-script layer can follow once the object model is stable.

---

## 3. Sound objects, audio I/O and file formats

Sources read: `docs/manual/Sound_files*.html`, `docs/manual/TextGrid_file_formats.html`, `docs/manual/Save_as_*.html`, `docs/manual/Read_from_file___.html`, `docs/manual/Sound.html`; `fon/Sound.cpp`, `fon/Sound.h`, `fon/Sound_files.cpp`, `fon/Sampled_def.h`, `fon/Matrix_def.h`, `fon/Pitch_def.h`, `fon/Formant_def.h`, `fon/Sampled.h`, `fon/praat_Sound.cpp`, `foned/SoundArea.cpp`, `fon/TextGrid_files.cpp`; `melder/melder_audiofiles.cpp`, `melder/melder_audiofiles.h`, `melder/melder_ftoa.cpp`, `melder/abcio.cpp`; `sys/Data.cpp`, `sys/oo_WRITE_BINARY.h`.

Claims are marked **[verified]** when I read the cited code or page, and **[unverified]** otherwise.

### 3.1 Audio formats

**Read (manual, `Sound_files_3__Files_that_Praat_can_read.html`).** The manual lists these standard formats for Read from file and Open long sound file:

| Format | Encodings listed |
|---|---|
| WAV | linear 16-bit LE; 8-bit mu-law; 8-bit A-law; 8-bit unsigned |
| AIFF / AIFC | linear 16-bit BE; 8-bit signed |
| NeXT/Sun (.au) | linear 16-bit BE; 8-bit mu-law; 8-bit A-law; 8-bit signed |
| NIST | linear 16-bit LE; 16-bit BE; 8-bit mu-law; 8-bit A-law; 8-bit signed |
| FLAC | 8, 16, 24, 32-bit; all sample rates |
| MP3 | all CBR and VBR bitrates (decode only) |
| Shorten | 8-bit A-law (listed in the manual) |

The manual's own prose and the per-format pages widen this:

- AIFF: 8, 16, 24 or 32-bit, any sample rate, any channel count; compressed AIFC is not supported (`Sound_files_2_2__AIFF_files.html`, `Sound_files_2_3__AIFC_files.html`). **[verified, manual]**
- NIST: "several kinds" including Polyphone; NIST files compressed with shorten are no longer supported (`Sound_files_2_5__NIST_files.html`). **[verified, manual]**
- Ogg Vorbis and Ogg Opus decoding are documented (`Sound_files_2_8`, `Sound_files_2_9`). **[unverified]**: I found no Ogg decoder in `melder/`, `fon/` or `sys/`. The only hits for "vorbis/opus/ogg" were in `external/espeak`, `dwtools` and `artsynth`. The Ogg claim may depend on code outside these directories.
- Shorten is listed as readable in `Sound_files_3`, but `fon/Sound_files.cpp:86-87` throws "Cannot unshorten" for `Melder_SHORTEN`. **[verified, source]** The reimplementation should treat Shorten as unsupported and fix the manual.
- The manual says "five types of standard sound files" and then lists six. **[verified, manual]**

**Write (manual `Sound_files_4__Files_that_Praat_can_write.html`; source `fon/praat_Sound.cpp:2055-2090`).** Save as WAV, AIFF, AIFC, NeXT/Sun, NIST and FLAC, all at 16 bits. The Save menu also exposes 24-bit and 32-bit WAV (`fon/praat_Sound.cpp:1318-1325`, `foned/SoundArea.cpp:362-378`). The manual does not mention these. **[verified]**

MP3 is decode-only. `melder/melder_audiofiles.cpp` has a `Melder_MP3` type and a default-encoding table entry, but the header writer's `switch` has no MP3 case and falls through to `Unknown audio file type` (line 209). **[verified]**

**Internal type table.** `melder/melder_audiofiles.h` defines the file types (AIFF=1, AIFC=2, WAV=3, NeXT/Sun=4, NIST=5, FLAC=6, MP3=7) and the encodings (8/16/24/32-bit linear in both endiannesses, mu-law, A-law, Shorten=11, Polyphone=12, IEEE float 32/64 in both endiannesses, FLAC 16/24/32). The reimplementation can use this as the enum of codecs. **[verified]**

**Compression.** The manual says compressed formats cannot be created, only read, except FLAC which is "fully supported" (`Sound_files_1_6__Compression.html`). **[verified, manual]**

### 3.2 Sample rate and bit depth

**Sampling.** A Sound stores its samples at a uniform sampling period `dx = 1/fs`. Sample index `i` (1-based) lies at time `x1 + (i-1)*dx`. **[verified]** (`fon/Sampled.h:33`, `Sampled_xToIndex`; `fon/Sampled_def.h` fields `nx`, `dx`, `x1`.)

**Quantization on read.** Integer samples are divided by the full-scale value so that full scale maps to ±1.0 (interpreted as pascal, see `sound_pressure_calibration`):

- 16-bit: divide by 32768 (`melder/melder_audiofiles.cpp`, e.g. line 1665). **[verified]**
- 24-bit: divide by 8388608 (line 1836). **[verified]**
- 32-bit: divide by 2^31 (`1.0/32768/65536`, line 1772). **[verified]**
- 8-bit mu-law and A-law: table lookup to 16-bit, then divide by 32768 (lines 2024, 2034). **[verified]**
- 8-bit unsigned: `(b/128) - 1.0` (line 1714). **[verified]**

**Quantization on write.** `MelderFile_writeFloatToAudio` (`melder/melder_audiofiles.cpp:2218`) multiplies, rounds to nearest, and clips to the integer range. For 16-bit: `round(x*32768)` clipped to [-32768, 32767]. For 24-bit the multiplier is 8388608. Clipped samples are counted and reported when `warnIfClipped` is set. **[verified]** The manual gives the same rule (`Sound_files_1_2__Quantization.html`).

**Floating-point output.** The reader and writer also contain IEEE float 32/64 branches (`bingetr32`, `binputr32`, lines 2116-2128 and 2187-2190). These are not listed in the manual. The float write path divides by 32768. **[verified in code; the GUI exposure is unverified]**

**Known source defect.** The float-to-short reads at lines 2116-2128 are marked `// BUG: truncation; not ideal`. The reimplementation should not copy the truncation. **[verified]**

**Sample rate in the header.** On save, Praat writes the sample rate as `Melder_iround_tieDown(1.0/dx)` (`fon/Sound_files.cpp:440`), an integer. A Sound whose `dx` is not `1/integer` will not round-trip its sampling period exactly. **[verified]**

**Channels.** The manual says "most file types" support mono and stereo (`Sound_files_1_3`). The source lets a Sound have any `ny` (`Sound_create(numberOfChannels, ...)`, `fon/Sound.cpp:126-129`), and the AIFF reader accepts any channel count per the manual. Channel handling beyond two is **[unverified]**.

**File size.** Header plus samples times bytes per sample times channels. The manual gives 28 bytes for a NeXT/Sun header (`Sound_files_1_5__Size.html`). **[verified, manual]**

### 3.3 The Sound object

**Class structure.** `Sound` is a `Matrix` with `ny` channel rows and `nx` sample columns, inheriting the `Sampled` fields `xmin`, `xmax`, `nx`, `dx`, `x1` (`fon/Sampled_def.h`, `fon/Matrix_def.h`). `Sound_create` calls `Matrix_init` with `ny = numberOfChannels` (`fon/Sound.cpp:126-129`). **[verified]**

**Inconsistency.** `fon/Sound.h` declares `Thing_define (Sound, Vector)`, which conflicts with the Matrix-based runtime. **[unverified]** which one is authoritative for on-disk layout. The reimplementation should decide this explicitly before writing a binary format.

**Time origin.** A new Sound from `Sound_createSimple(ch, duration, fs)` has:

- `nx = round(duration * fs)` (`fon/Sound.cpp:136-143`)
- `dx = 1/fs`
- `x1 = 0.5/fs`
- `xmin = 0`, `xmax = duration`

So the first sample is centred at `dx/2`, and the domain covers `[0, nx*dx]`. `Sound_shiftTimesToBetweenZeroAndPhysicalDuration` (`fon/Sound.cpp:275-279`) enforces the same convention. **[verified]** Note that the manual's Sound page does not state this; it is a source-level convention.

**Sample count from a file.** A read computes `duration = numberOfSamples / sampleRate` and then calls `Sound_createSimple` (`fon/Sound_files.cpp:68-94`). The sampling rate is a double in the reader but an integer on write (see 3.2), so a read-then-write cycle can change `dx`. **[verified]**

**Resampling and concatenation** change `dx` and `x1` (e.g. `fon/Sound.cpp:362-373`). The reimplementation's time-origin rule must be preserved through these operations.

**LongSound.** Files too large for memory open as `LongSound`, which reads only what is needed (`docs/manual/Open_long_sound_file___.html`, `fon/LongSound.cpp`). **[verified, manual and file list]**

### 3.4 Praat text and binary object formats

**Text header.** Every text object begins:

```
File type = "ooTextFile"
Object class = "<ClassName>"
```

The class version is appended after the class name when nonzero (`sys/Data.cpp:85-90`). **[verified]**

**Text body.** Fields are written in declaration order via the `oo_*` macros in each `*_def.h`. The reader ignores comments. Only free-standing numbers, double-quoted strings and `<flag>` tokens count as data, and `!` starts a comment (`TextGrid_file_formats.html`; `Save_as_text_file___.html`). **[verified, manual]**

**Number formatting.** Doubles are written with `%.15g`, with escalation to `%.16g` and `%.17g` (`melder/melder_ftoa.cpp:147-151`). The escalation is presumably there to guarantee an exact round-trip for doubles. **[verified that escalation exists; the round-trip guarantee is unverified.]**

**Encoding.** On Windows the text writer uses CRLF (`sys/Data.cpp:66-67`). A UTF-16 output mode writes a BOM `0xFEFF` (`sys/Data.cpp:73`). **[verified]**

**Short text format.** One datum per line, with most comments removed. It is read by the same parser (`Save_as_short_text_file___.html`). **[verified, manual]**

**Binary format.** Files start with the ASCII bytes `ooBinaryFile`, then the class name (written with `binputw8`), then fields in binary (`sys/Data.cpp:131-150`) **[class-name encoding detail unverified]**. Doubles are read with `bingetr64` (`melder/abcio.cpp:1122`), which uses the host's native representation when it is IEEE-754 double and byte-swaps otherwise. The byte order is therefore decided by macros in `abcio.cpp:641-658`. **[verified for structure; byte order per platform is unverified and should be checked against a real file before the reimplementation fixes it.]**

**Magic-number detection.** `Data_readFromFile` reads the first 512 bytes. A gzip magic `1F 8B` is treated as a text file (`sys/Data.cpp:292-296`). The text and binary headers are recognized by searching for `TextFile` and `ooBinaryFile` (`sys/Data.cpp:281-343`). **[verified]**

**Pitch, Formant.** Both derive from `Sampled` (`fon/Pitch_def.h:79`, `fon/Formant_def.h:57`). Pitch has `ceiling` and per-frame candidates with `frequency` and `strength`. Formant has per-frame formants with `frequency` and `bandwidth`, and `numberOfFormants` as a 16-bit integer. The exact field order for the text and binary layouts should be taken from the `*_def.h` files, not from this summary. **[verified field names; order unverified]**

**Generic Save/Read.** Save as text file and Save as binary file accept any object type, and Read from file recognizes both (`docs/manual/Read_from_file___.html`). Collections are written with `Object class = "Collection"` (`Save_as_text_file___.html`). **[verified, manual]**

### 3.5 TextGrid file formats

**Long text format.** The manual gives a full example of a TextGrid with two interval tiers and one point tier. Structure: `File type`, `Object class = "TextGrid"`, `xmin`, `xmax`, `tiers? <exists>`, `size = N`, then `item [i]:` blocks, each with `class = "IntervalTier"` or `"TextTier"`, `name`, `xmin`, `xmax`, and either `intervals: size = K` with `intervals [j]:` blocks (`xmin`, `xmax`, `text`) or `points: size = K` with `points [j]:` blocks. The manual example shows only `points: size = 0`, so the point field names are **[unverified]**. **[verified, manual]**

**Short text format.** The same data, one value per line, with comments dropped (`TextGrid_file_formats.html`, section 2). **[verified, manual]**

**Round-trip rule for TextGrids.** Because the parser ignores whitespace-separated labels (`item [2]`, `xmin =`, etc.), the long and short forms should read to the same object. A test should load the manual's minimal example in both forms and compare the object.

**Legacy and import formats.** `fon/TextGrid_files.cpp` also contains:

- A "Praat chronological TextGrid text file" writer and reader (`TextGrid_writeToChronologicalTextFile`, line 479; `TextGrid_readFromChronologicalTextFile`, line 408). This is a separate, older format. **[verified]**
- Readers for ESPS label files (line 91), CGN syntax files (line 563), TIMIT label files (line 1030) and Kiel label files (line 1134). These are import-only in the sense that no matching writer was checked. **[verified existence; writer absence unverified]**

### 3.6 Round-trip compatibility

I propose three distinct tiers. They have different guarantees and should not be merged.

1. **Object round-trip (exact).** Text and binary save/read of any Sampled-derived object (Sound, Pitch, Formant, TextGrid) should reproduce the same field values. The text format relies on `%.15g`-to-`%.17g` escalation, and the binary format on IEEE doubles. The test is equality of every field after a write and read. Subject to the byte-order check in 3.4.
2. **TextGrid round-trip (exact, modulo comments).** Long and short forms must parse to equal objects. Quoting rules for label text should follow `writeQuotedString` (`TextGrid_files.cpp:466`), which was not read in detail **[unverified]**.
3. **Audio round-trip (lossy).** A Sound saved as a 16-bit file and read back equals the original only after quantization: each sample becomes `round(x*32768)/32768` with clipping. A 24-bit or 32-bit save is closer. FLAC at 16 bits is lossless relative to the 16-bit integers. Sampling rate round-trips only when `1/dx` is an integer (3.2). **[verified from code]**

**What the reimplementation must match.** The manual is the behavioral target for reading. For writing, the byte-level output of the 16-bit WAV, AIFF and NIST headers (`melder/melder_audiofiles.cpp:37-210`) should match, and the reimplementation should check its files against Praat's own output on the same Sound, because the manual's description of headers is not complete.

**Open questions (not checked).**
- Whether the Ogg claims in the manual are implemented in this tree (3.1).
- The on-disk byte order for binary objects (3.4).
- Whether Sound's on-disk layout is Matrix-based or Vector-based (3.3).
- The exact field order for Pitch and Formant (3.4).
- Channel counts above two in each format (3.2).

---

## 4. Spectrogram and waveform display: visual parity

Status: draft as of 2026-11-02. Sources: the manual pages and the reference source under `praat-source/`. Where the manual and the source disagree, this section follows the source (what the reference does) and records the conflict in 4.7.

Manual pages used: `docs/manual/Intro_3_1__Viewing_a_spectrogram.html`, `Intro_3_2__Configuring_the_spectrogram.html`, `Intro_3_3__Querying_the_spectrogram.html`, `Intro_3_7__Configuring_the_spectral_slice.html`, `Intro_2_2__Viewing_and_editing_a_sound.html`, `Advanced_spectrogram_settings___.html`, `Sound__To_Spectrogram___.html`, `Spectrogram.html`, `Spectrum.html`, `SoundEditor.html`, `Keyboard_shortcuts.html`.
Screenshot used: `docs/pictures/screenshot-1.png` (Sound editor). `screenshot-2.png` (script window) and `screenshot-3.png` (Objects window) are not display references.

### 4.1 Spectrogram algorithm

The spectrogram is a short-time Fourier analysis. The manual lists Fourier as the only method.

**Window.** The default is Gaussian. It is the only shape with no sidelobes: a 1000 Hz sine shows one line, not a comb of grey lines (`Advanced_spectrogram_settings___.html`). The source (`fon/Sound_and_Spectrogram.cpp`, `Sound_to_Spectrogram_e`) uses

    w(i) = (exp(-48 p^2) - e) / (1 - e),   e = exp(-12),   p = (i - mid) / N_phys,  p in [-0.5, 0.5]

The physical window is twice the effective length (`physicalAnalysisWidth = 2 * effectiveAnalysisWidth`). At the default 5 ms, the physical span is 10 ms (`Intro_3_7__Configuring_the_spectral_slice.html`). Square, Hamming, Bartlett, Welch and Hanning are kept for teaching. They are about twice as fast, and they must be implemented, but only Gaussian must match numerically.

**Window length and bandwidth.** The default is 0.005 s. The Gaussian -3 dB bandwidth is `1.2982804 / L`: about 260 Hz at 5 ms, about 43 Hz at 30 ms (`Intro_3_2__Configuring_the_spectrogram.html`). The manual's sine tests are regression tests. A 1000 Hz sine should give one band at 5 ms. A 1000 + 1200 Hz pair should resolve into two bands at 30 ms.

**Frequency range.** The default view is 0 to 5000 Hz (`spectrogram_viewFrom` 0.0, `spectrogram_viewTo` 5000.0, `foned/SoundAnalysisArea_prefs.h`). Analysis stops at Nyquist, and bins above it are white.

**Sampling.** The grid follows the view. Per redraw, `timeStep = (endWindow - startWindow) / spectrogram_timeSteps` and `freqStep = viewTo / spectrogram_frequencySteps`. Both steps are clamped:

- time step floor = `(L / sqrt(pi)) / 8`;
- frequency step floor = `(1 / (L / sqrt(pi))) / 8`.

Both use oversampling 8.0 (passed by `foned/SoundAnalysisArea.cpp`). For L = 5 ms the floors are 0.353 ms and 44.31 Hz, matching `Sound__To_Spectrogram___.html`. The frequency grid then snaps to FFT bin width. Frames are centred, so there is a white stripe about one physical window wide at each sound edge (`Intro_3_1__Viewing_a_spectrogram.html`).

**Pre-emphasis.** Default +6 dB/octave. Each row gets `preemph / ln2 * ln(f / 1000 + 1e-308)` dB. 1000 Hz stays at 0 dB, bands above it darken and bands below lighten (`fon/Spectrogram.cpp`, ~line 93).

**Power to dB.** `psd_db = 10 log10(psd / 4e-10)`, with psd in Pa^2/Hz (`Spectrogram.cpp`, ~line 102). The 1e-308 floor puts silence near -3080 dB.

**Dynamic compression.** Default 0. Each frame gets `c * (max - frame_max)` added to every bin (`Spectrogram.cpp`, line 134). The manual's worked example (c = 0.4, global max 80 dB, frame max 20 dB gives +24 dB) checks out against this formula.

### 4.2 Dynamic range, autoscaling, colour

| Setting | Default | Source key |
|---|---|---|
| Maximum | 100 dB/Hz | `spectrogram_maximum` |
| Autoscaling | on | `spectrogram_autoscaling` |
| Dynamic range | see 4.7 | `spectrogram_dynamicRange` |
| Pre-emphasis | +6 dB/oct | `spectrogram_preemphasis` |
| Dynamic compression | 0 | `spectrogram_dynamicCompression` |
| Colour map | Grey | `spectrogram_colourMap` |

**Autoscaling.** When on, `maximum` is the largest post-pre-emphasis value in the visible part, not the fixed 100 dB/Hz. Loud material scrolling off screen therefore darkens the rest. The manual describes this as intended (`Intro_3_1__Viewing_a_spectrogram.html`), so it must be reproduced exactly.

**Grey mapping.** Values from `maximum - dynamicRange` (white) to `maximum` (black) map linearly to grey. Values above the top are black, and values below the bottom are white (`Intro_3_2__Configuring_the_spectrogram.html`; `fon/Spectrogram.cpp` ~line 151 calls `Graphics_image` with `min_val`, `max_val`).

**Colour maps.** `fon/Spectrogram_enums.h` lists Grey, Viridis, Jet, Hot, Cool, Spring, Summer, Autumn, Winter, Bone, Copper, Pink, Parula and Turbo, plus invert and RGB options. These are later additions that the manual does not cover. Only Grey must match. The others are extension points and need not be pixel-identical.

### 4.3 Editor layout

From `screenshot-1.png` and `Intro_2_2__Viewing_and_editing_a_sound.html`:

- The waveform fills the upper pane, with amplitude labels at left (max, zero, min). A cyan frame marks the modifiable sound.
- The spectrogram fills the lower pane, with 0 Hz at the bottom and the view top (`5000 Hz` by default) at the top, and the frequency axis at left.
- A red time cursor runs through both panes. Its time is shown above the waveform. Clicking the spectrogram shows a cross with frequency at left and time at top (`Intro_3_3__Querying_the_spectrogram.html`).
- Below the panes is a time ruler: selection start and end, then "Visible part" and "Total duration" rows.
- The bottom row has the buttons `all`, `in`, `out`, `sel`, `bak`, a scroll bar, and a `Group` check box that synchronises zoom and scroll (`SoundEditor.html`).
- The screenshot also shows pitch (blue, right axis, 50 to 800 Hz) and formant (red dots) overlays. Both are on by default (`pitch_show`, `SoundAnalysisArea_prefs.h`). They are separate features and are outside this section.

The waveform draws one vertical span per pixel column from that column's min to max sample (`Intro_3_1__Viewing_a_spectrogram.html`). The spectrogram does not do this. It samples one frame per column.

### 4.4 Zoom and scroll

From `Keyboard_shortcuts.html` and `foned/FunctionEditor.cpp`:

- **Zoom in** halves the visible span, keeping the centre fixed. Shortcut Command-I, which is Ctrl-I on Windows.
- **Zoom out** doubles it. Command-O.
- **Zoom to selection** is Command-N. It pushes the previous window onto a history. **Zoom back** pops it. **Zoom all** is Command-A.
- **Ctrl plus mouse wheel** zooms by 2 % per step: `exp(-0.02 * sign * sqrt(|delta|))`.
- **Page-up and Page-down** scroll by a page. Shift-wheel and horizontal swipe scroll horizontally (`What_was_new_*`).
- Scrolling by arrow keys uses `arrowScrollStep` = 0.05. The manual says 5 % of the visible window (`Intro_3_1__Viewing_a_spectrogram.html`). See 4.7.
- The window clamps to the sound extent (1e-12 tolerance). When a shift hits an edge, the window length is kept.
- The spectrogram recomputes on every window change. The time-step rule keeps about one frame per pixel column (`Advanced_spectrogram_settings___.html`).

Because frames are point samples at pixel centres, scrolling changes the image slightly, and the darkness changes under autoscaling (`Intro_3_1__Viewing_a_spectrogram.html`). This is the reference behaviour and is not a bug to fix.

### 4.5 What must match and what may differ

**Must match numerically:**

1. The Gaussian window, physical length (2x effective), and the edge clamp.
2. Time and frequency step rules, including the 8x oversampling floors and FFT-bin snapping.
3. The dB transform, pre-emphasis row term, and 1e-308 floor.
4. Autoscaling, dynamic-range and compression formulae, with the defaults from 4.7.
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

- Fonts, anti-aliasing, widget toolkit, window decoration, menu bar, buttons, scroll bar. The screenshot is a Linux desktop capture, so pixel-exact match across toolkits is not a goal.
- Colour maps other than Grey.
- Pixel positions of overlays, provided the data is the same.

A real pixel comparison should use a spectrogram-only raster from a fixed test sound, rendered by the reference on the same platform. Screenshots are not a valid pixel baseline.

### 4.6 Verification plan

- Regenerate the manual's worked examples (1000 Hz sine, 1000 + 1200 Hz pair at 30 ms, the click-and-tone formula) and check band positions and widths.
- Compare spectrogram cell values against the reference's `Spectrogram` object, using `Spectrogram: Get value` queries on both sides.
- Read the defaults from the reference's Spectrogram settings form in a running build.

### 4.7 Conflicts and unverified items

- **Dynamic range default.** The manual (`Intro_3_2__Configuring_the_spectrogram.html`) says 50 dB. The Sound editor source (`spectrogram_dynamicRange`) says 70 dB. `Spectrogram: Paint...` (`fon/praat_uvafon_init.cpp`) uses 50 dB. The editor's 70 dB is what a user sees on first open, so this section recommends 70 dB. This is a decision for the design owner.
- **Time and frequency step defaults.** The manual's `Advanced_spectrogram_settings___.html` says 1000 and 250. The source says 1500 and 500. The source is used here.
- **Scroll step units.** The manual says 5 % of the window. The code declares 0.05 with no explicit unit. Not verified which the Sound editor uses.
- **Grey ramp shape.** Linear in dB is inferred from the `Graphics_image` call. `sys/Graphics_image.cpp` was not read, so gamma or quantisation is unverified.
- **Screenshot measurements.** `screenshot-1.png` is a single desktop capture at unknown DPI. No pixel measurements were taken, so proportions and label positions are approximate.
- **Gaussian width.** The `exp(-48 p^2)` form was read from source. The bandwidth was taken from the manual's `1.2982804 / L`, not derived from the source.
- **Colour maps and RGB.** These were read from the enum and switch statements, not checked against rendered output.

---

## 5. TextGrid and annotation editing

Sources: manual pages `docs/manual/TextGrid.html`, `docs/manual/TextGridEditor.html`, `docs/manual/TextGrid_file_formats.html` (praat-source). Implementation: `fon/TextGrid_def.h`, `fon/TextGrid.cpp`, `fon/TextGrid_files.cpp`, `foned/TextGridArea.cpp`, `foned/TextGridEditor.cpp`, `melder/abcio.cpp`. Items marked **[unverified]** were not checked against running Praat.

### 5.1 Data model

A TextGrid is a container of tiers over one time domain (seconds). Two tier kinds exist:

- **IntervalTier** (`fon/TextGrid_def.h`): a collection of `TextInterval` objects (`xmin`, `xmax`, `text`). Intervals must be contiguous and non-overlapping, with positive duration.
- **TextTier** (point tier): a sorted collection of `TextPoint` objects (`number` = time, `mark` = label).

Invariants, from `docs/manual/TextGrid_file_formats.html` section 6:

1. Strong (interval tiers): each interval has `xmax > xmin`; each interval's `xmin` equals the previous interval's `xmax`.
2. Strong (point tiers): point times are strictly increasing. Praat refuses to insert a point at an existing point's time.
3. Weak: the first interval starts at the tier's `xmin`, and the last ends at the tier's `xmax`.
4. Weak: each tier's time domain equals the TextGrid's time domain. Merging TextGrids can violate this; Praat still displays such grids.

An interval tier always has at least one interval. A newly created interval tier is one empty interval spanning the domain. Praat reads files that break the weak invariants but may read files that break the strong ones incorrectly, and the manual says so explicitly. A reimplementation should reject strong-invariant violations with an error and repair or accept weak ones.

Creation paths (manual `TextGrid.html`): `Sound/LongSound/PointProcess: To TextGrid...`, `Create TextGrid...`, `TextGrids: Merge...`, `Intensity: To TextGrid (silences)...`, and the other `To TextGrid` variants. `TextGrid: Extend time...` and `TextGrid: Count labels...` are also documented. `TextGrids_concatenate` exists in `fon/TextGrid.cpp` (line ~1392), but its menu entry was not checked.

### 5.2 Text file formats

Praat's generic text object format (`melder/abcio.cpp`) is used for TextGrid. The manual (`TextGrid_file_formats.html`) documents three layouts that all express the same data.

**Long form ("Save as text file")**, abbreviated:

```
File type = "ooTextFile"
Object class = "TextGrid"
xmin = 0
xmax = 2.3
tiers? <exists>
size = 3
item []:
    item [1]:
        class = "IntervalTier"
        name = "Mary"
        xmin = 0
        xmax = 2.3
        intervals: size = 1
        intervals [1]:
            xmin = 0
            xmax = 2.3
            text = ""
    item [3]:
        class = "TextTier"
        name = "bell"
        xmin = 0
        xmax = 2.3
        points: size = 0
```

Point entries use `points [n]:` with `number = <t>` and `mark = "<text>"`. In text, a double quote is written as `""`.

**Short form ("Save as short text file")**: the same data, one free-standing token per line, with no labels:

```
"ooTextFile"
"TextGrid"
0
2.3
<exists>
3
"IntervalTier"
"Mary"
0
2.3
1
0
2.3
""
```

**Free-form**: any layout is accepted as long as data tokens are free-standing. Tokens are free-standing when preceded and followed by start/end of file, line, or space. Comments are:
- anything between `[` `]` labels such as `[2]`, `xmin =`, `size =`, `item []:` (ignored by the reader, per the manual),
- anything after `!` on a line.

The first line must be exactly `"ooTextFile"`. The second token is the object class, `"TextGrid"`. Then follow `xmin`, `xmax`, the flag `<exists>` (or `<absent>`, which ends the file), the tier count, and for each tier: class, name, `xmin`, `xmax`, the element count, then each element.

**Encoding and line endings** (manual section 7): reader accepts UTF-8 without BOM, UTF-16 with BOM (either endianness), and legacy Latin-1 or MacRoman. Writer uses UTF-8 without BOM or UTF-16 with BOM. Never write Latin-1 or MacRoman. Line endings: LF, CR, or CRLF, all accepted on read.

**Trigraphs** (manual section 8): labels may contain backslash trigraphs such as `\ct` for U+0254. The reimplementation must accept them on input. Whether it writes Unicode or trigraphs is a user preference; the TextGrid window offers "Convert entire TextGrid to backslash trigraphs" and "to Unicode" (`foned/TextGridArea.cpp` around line 1936).

**Praat chronological text file** (source only, `fon/TextGrid_files.cpp` lines 408-560): header `"Praat chronological TextGrid text file"`, then time domain, tier count, and all elements sorted by time and then tier number, one per line. It is not described in the TextGrid manual pages. **[unverified]** whether any current Praat build still produces it from the GUI.

### 5.3 Editor interactions

Source: `foned/TextGridArea.cpp`. Pixel thresholds are in millimetres:

- `clickingVicinityRadius_mm = 1.0` (line 567), used for click-near-boundary.
- A click within 1.5 mm of a boundary or point is a boundary/point hit (`nearBoundaryOrPoint`).
- `draggingVicinityRadius_mm = clickingVicinityRadius_mm + 0.2`, so a drag must leave the 1.2 mm radius before it moves anything.

**Cursor and selection.** Clicking in the Sound area or inside an interval positions the cursor hair. Clicking in a tier snaps a time selection to the nearest boundary or point (manual `TextGridEditor.html`; code around lines 600-660).

**Tier selection.** Clicking anywhere in a tier selects it; its name is drawn in red with a pointing hand.

**Interval selection.** Clicking inside an interval selects it (yellow). The cursor moves to its start and the selection becomes the interval. Clicking left or right of an interval's midpoint anchors to its `xmin` or `xmax` respectively (code around line 620).

**Add boundary (interval tier) or point (point tier).** Click inside the cursor circle in the tier, or use the Boundary menu:

- "Add on selected tier": Enter.
- "Add on tier N" for N = 1..8, and "Add on all tiers": Command plus digit (macOS modifiers; see the unverified note below).

The text of the split interval is divided between the two results according to the text cursor position in the text window (manual).

**Remove boundary.** Option+Backspace (`foned/TextGridArea.cpp` line 2052). It calls `IntervalTier_removeLeftBoundary` (`fon/TextGrid.cpp` around line 1072), which merges the two intervals and concatenates their texts left then right. Points: "Remove" in the Point menu removes the selected point. Removing a whole tier is in the Tier menu.

**Move boundary or point.** Drag it. Shift-drag moves all boundaries and points at the same time, on every tier. The Shift behaviour follows a preference (`shiftDragMultiple`, around line 1154).

- Dragging a boundary is blocked by its neighbours on the same tier (line ~702). Point tiers may pass neighbours.
- Dropping onto another tier snaps to the nearest boundary or point there (lines ~772-790).
- Dropping near the cursor circle snaps to the cursor time (line ~798).
- If the user wiggles inside the anchor vicinity without leaving it, nothing moves (line ~806).
- The first and last boundaries of a tier cannot be moved (`isLeftEdgeOfFirstInterval`, `isRightEdgeOfLastInterval`, around line 660).

**Text entry.** Select an interval or point (click), then type. Text appears in the text window and in the interval or point at once. Navigation uses the mouse and arrow keys. Special symbols and Unicode are accepted (manual).

**Clipboard and search.** Cut/Copy/Paste on text: X, C, V (`foned/TextGridArea.cpp` line 1050). Find: F, Find again: G. Check spelling in tier: L (only when the SpellingChecker is attached).

**Playback.** Tab plays the selected interval; Tab during playback halts it and moves the cursor to the stop point (manual `TextGridEditor.html`). Clicking a rectangle around the drawing area plays a stretch of sound.

**Tier navigation.** Option+Up/Down selects previous/next tier. Option+Left/Right selects previous/next interval. Shift+Option+Left/Right extends the selection (menu definitions lines 1943-1953).

**Linked Sound.** Selecting a TextGrid and a Sound (or LongSound) before View & Edit creates a TextGridEditor with the Sound in the top area and the tiers below (`foned/TextGridEditor.cpp` lines 45-53). All tiers are shown; boundaries and labels are hidden when zoomed out. Extract sound selection (File menu) copies the selected time range as a new Sound, either keeping the original times or shifting to zero.

### 5.4 Compatibility test list

Round-trip and parsing:
1. Read and write the long form example from the manual; output must equal input up to whitespace and comments.
2. Read the short form; read the free-form example with `!` comments and `3 tiers`-style counts.
3. Doubled quote `""` round-trips inside a label.
4. Reads UTF-8, UTF-8 BOM-less, UTF-16 LE and BE with BOM, Latin-1, and MacRoman files; writes UTF-8 or UTF-16 only.
5. Reads LF, CR, and CRLF line endings.
6. Trigraph `\ct` reads as U+0254 in a label.
7. Reject an interval whose `xmax <= xmin`, and an interval gap or overlap, with an error.
8. Accept a tier whose domain differs from the TextGrid's (weak invariant), and display it.
9. Reject an out-of-order point sequence.
10. Chronological text file reads and writes (source-only format).

Editing:
11. Add boundary inside an interval: two intervals, text split by cursor position.
12. Remove boundary: merged interval; text concatenated, left then right.
13. Remove boundary where both texts are equal: **see discrepancy below**.
14. Drag boundary: blocked by neighbours; not movable at the tier edges.
15. Shift-drag moves coincident boundaries on all tiers.
16. Drop onto another tier snaps to that tier's boundary within the vicinity.
17. Point add/remove; point duplicate time is refused.
18. Tab playback of the selected interval.

Linking:
19. Creating an editor from TextGrid + Sound shows both; Extract sound selection preserves times in one mode and shifts to zero in the other.

### 5.5 Unverified items and discrepancies

- **Remove boundary text merge.** The manual (`TextGridEditor.html`) says that if the two texts are equal, the result keeps that text once. The source (`fon/TextGrid.cpp` `IntervalTier_removeLeftBoundary`) always concatenates with `Melder_cat`. The source does not implement the manual's equal-text rule. The reimplementation must choose one. Flagged for a decision; I have not verified which behaviour users rely on.
- **Key bindings.** The source uses `GuiMenu_COMMAND`, `GuiMenu_COMMAND_EXTRA`, `GuiMenu_OPTION` and `GuiMenu_ENTER`. The manual gives Command-F1..F9 for "Add on tier N". The source menu entries use digit keys with `GuiMenu_COMMAND_EXTRA` (`foned/TextGridArea.cpp` lines 2029-2045), and the F-key mapping is not confirmed in the code I read. **[unverified]** how these map on Windows and Linux.
- **Mouse thresholds.** The 1.0 mm and 1.5 mm values were read from source, not measured on screen. They depend on display DPI in an unverified way.
- **Tab playback and selection behaviour** are taken from the manual; the playback code was not read.
- **File reader tolerance.** The rules for accepting variant layouts come from the manual. The generic reader in `melder/abcio.cpp` was not traced end to end. **[unverified]** whether it tolerates arbitrary whitespace between comment and data.

---

## 6. Pitch analysis

Source root used for all citations: `praat-source\` (abbreviated `PS\` below). The pitch code was found under `praat-reimplementation\praat-source`.

### 6.1 Methods

Praat offers four candidate-finding methods, all feeding one shared path finder:

| Command (manual) | Method | Source entry point |
|---|---|---|
| Sound: To Pitch... / (raw autocorrelation) | AC, Hanning window | `Sound_to_Pitch_rawAc` (`PS\fon\Sound_to_Pitch.cpp`:499) |
| (raw autocorrelation, very accurate) | AC, Gaussian window | same, `veryAccurate = true` |
| (raw cross-correlation) | forward CC, unwindowed | `Sound_to_Pitch_rawCc` (:512) |
| (filtered autocorrelation) | low-pass, then AC | `Sound_to_Pitch_filteredAc` (:525) |
| (filtered cross-correlation) | low-pass, then CC | `Sound_to_Pitch_filteredCc` (:569) |

The manual (`PS\docs\manual\pitch_analysis_by_raw_autocorrelation.html`) describes the AC method as Boersma (1993): the windowed autocorrelation is divided by the normalized autocorrelation of the window, so that peaks of a periodic signal come out at the same height. The CC method (`pitch_analysis_by_raw_cross-correlation.html`) is a forward cross-correlation over a window of one longest period. The manual recommends filtered AC for speech intonation and CC for jitter/shimmer-type voice work. The filtered variant applies a Gaussian-in-frequency low-pass to the whole sound before analysis (`Sound_to_Pitch_filteredAc`, cutoff `pitchTop / sqrt(-2 ln attenuationAtTop)`), so that the amplitude factor at `pitchTop` equals `attenuationAtTop` (the manual's table at `pitch_analysis_by_filtered_autocorrelation.html` agrees: 0.03 at 800 Hz, 0.42 at 400 Hz).

### 6.2 Algorithm

1. **Frame grid.** Frames are centred so that as many as fit symmetrically are placed (`Sampled_shortTermAnalysis`, `PS\fon\Sampled.cpp`:71). Frame count is `floor((duration - windowDuration)/timeStep) + 1`.
2. **Per frame (`Sound_into_PitchFrame`, `PS\fon\Sound_to_Pitch.cpp`, starting near line 30).** Subtract a local mean (one longest period either side); window (AC only); compute local intensity as the peak of the windowed, mean-subtracted frame divided by the global peak (`globalPeak`, computed on the whole sound at :370). Compute r(lag) by FFT (AC) or direct sums (CC).
3. **Candidate recruitment.** Candidate 1 is always the unvoiced candidate (frequency 0, strength 0). Local maxima of r with `r > 0.5 * voicingThreshold` are candidates (line 186); frequency comes from parabolic interpolation, strength from sinc interpolation, then a second sinc-based maximization. Up to `maxnCandidates` are kept; when full, a new peak replaces the weakest one if it scores higher after the octave penalty (lines 227, 237). `maxnCandidates` is raised to `floor(ceiling/floor)` if smaller (line 287).
4. **Path finding (`Pitch_pathFinder`, `PS\fon\Pitch.cpp`:524-670).** Viterbi over frames. Per-candidate score `delta`: unvoiced candidates get `unvoicedStrength = voicingThreshold + max(0, 2 - intensity*(1+voicingThreshold)/silenceThreshold)` (line 553-555); voiced candidates get `strength - octaveCost * log2(ceiling/f)` (line 560). Transition costs: voiced to voiced `octaveJumpCost * |log2(f1/f2)|`; any voicing change `voicedUnvoicedCost`; both unvoiced 0. Before the search both jump and V/UV costs are multiplied by `0.01 / dx` (lines 543-545), which is the time-step correction the manual mentions. Voiced means `0 < f < ceiling` (`PS\fon\Pitch.h`:66). The backtrack swaps the chosen candidate into slot 1.

### 6.3 Parameters and defaults

Defaults below are from the GUI forms in `PS\fon\praat_Sound.cpp` (lines 1615-1800) and the manual pages. The `Sound_to_Pitch` convenience function (`Sound_to_Pitch.cpp`:494-496) hard-codes the same values as the "To Pitch..." form.

| Parameter | "To Pitch..." (AC) | Filtered AC/CC | Notes |
|---|---|---|---|
| Time step | 0 (auto) | 0 (auto) | auto = `periodsPerWindow / floor / 4`: 0.75/floor for AC, 0.25/floor for CC (`Sound_to_Pitch.cpp`:291) |
| Pitch floor | 75 Hz | 50 Hz | sets window length: 3/floor (AC), 1/floor (CC); analysis fails if floor < periodsPerWindow / duration (:314) |
| Ceiling / top | 600 Hz | 800 Hz | ceiling does not limit recruitment (see 6.4) |
| Max candidates | 15 | 15 | "Very accurate" off |
| Very accurate | off | off | AC Gaussian window, length 6/floor (:299) |
| Silence threshold | 0.03 | 0.09 | relative to global peak |
| Voicing threshold | 0.45 | 0.50 | strength of unvoiced candidate; also gates recruitment at 0.5x |
| Octave cost | 0.01 /oct | 0.055 /oct | favours high candidates |
| Octave-jump cost | 0.35 | 0.35 | scaled by 0.01/dt |
| Voiced/unvoiced cost | 0.14 | 0.14 | scaled by 0.01/dt |
| Attenuation at top | n/a | 0.03 | filtered variants only |

### 6.4 Where the manual and source disagree or are silent

These were checked against the code and are not in the manual's text:

- **Ceiling.** The manual says candidates above the ceiling are "ignored". In the code, the ceiling does not restrict recruitment: the lag loop starts at 2 (`Sound_to_Pitch.cpp`:185), and `minimumLag` (:339) is computed but never used (grep confirms one occurrence). Above-ceiling candidates survive into the path finder and are simply treated as voiceless there (`Pitch.h`:66). The header comment (`Sound_to_Pitch.h`) says the same thing.
- **Octave-cost reference.** Recruitment penalises with `log2(pitchFloor/f)` (:227, :237), but the path finder uses `log2(ceiling/f)` (`Pitch.cpp`:560). The manual does not say which reference applies. Replication has to use both.
- **Window length.** The manual gives the Hanning window length as exactly 3/floor. The code takes `floor(dt_window/dx)`, then rounds to an even count minus 2 (`Sound_to_Pitch.cpp`:330-332). The difference is a few samples.
- **Pull formants.** `Pitch_pathFinder` has a formant-pulling branch (`Pitch.cpp`:654), enabled by passing `Melder_debug == 31` as its last argument (`Sound_to_Pitch.cpp`:485). With the flag off it is inactive; the manual does not mention it.
- **Debug switches.** `Melder_debug == 30` enables a frequency-jump term across unvoiced stretches (`Pitch.cpp`:591); it is off by default. Any port must leave it out.

### 6.5 What "replicating Praat numerically" means

The target is a function from (Sound, settings) to a Pitch object with the same frame grid, the same candidate lists (frequency and strength per frame), and the same path. Several things limit exact equality:

- **Floating point.** The AC path uses Praat's own FFT (`NUMfft_forward/backward`) and `sqrt`, `exp`, `log`, which differ across libm builds. A port in double precision with a different FFT will differ at roughly 1e-12 relative in r, which is usually below any decision boundary but not always.
- **Long double.** Cross-correlation accumulates in `longdouble` (`Sound_to_Pitch.cpp`:116-127). `PS\melder\melder_real.h`:20-40 maps this to 80-bit on x86-64 gcc/clang and to 64-bit on ARM64 and (per the comment) on Clang for Windows. CC results therefore depend on the compiler, and Praat itself is not bit-identical across platforms. This is verified from the comment; the MSVC behaviour is from general knowledge and unverified here.
- **Threading.** Frames are computed in parallel (`MelderThread_PARALLEL`), but each frame writes only its own slot, so results should not depend on thread count. Not tested.
- **Decision ties.** The Viterbi uses strict `>` with an `==` tie branch (`Pitch.cpp`:613). Near-ties in path cost can flip with tiny numeric changes; these are the main source of path mismatch.

So "match" needs tiers, not one tolerance.

### 6.6 Differential test plan

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

### 6.7 Unverified

- Exact `Get value` / candidate query commands in this source tree; the test script above names them only generically.
- That the filtered variants' manual pages match their GUI forms beyond what is listed here (I read the filtered AC page and the GUI; the filtered CC manual page was checked only for its absence of a "standard value" line).
- The sinc-depth constants (`NUM_PEAK_INTERPOLATE_SINC70`/`700`, `PS\melder\NUMinterpol.h`:35-36) and their meaning in `NUMinterpol.cpp`, which I did not open.
- MSVC `long double` width (see 6.5).
- No oracle has been run; all tolerances above are proposals, not measured values.

---

## 7. Formant analysis (Burg LPC)

Source root used for all citations: `praat-source\` (the sources are under `praat-reimplementation\praat-source`). All line numbers were read on the working tree as of 2026-11-02.

### 7.1 Pipeline

The user-facing command is `Sound: To Formant (burg)...`. Its GUI form is in `fon/praat_Sound.cpp` (lines 1448-1460), and it calls `Sound_to_Formant_burg` in `fon/Sound_to_Formant.cpp`. The steps, in order:

1. **Resampling.** `Sound_to_Formant_any` (line 377) resamples to `2 * maximumFrequency` with `Sound_resample(..., 50)` unless the ceiling is <= 0 or equal to the existing Nyquist (in which case the Sound is copied). The manual (`fon/manual_formant.cpp`, lines 566-567) states the same.
2. **Pre-emphasis, in place.** `Sound_preEmphasize_inplace` (`fon/Sound.cpp`, line 1241) applies `s[i] -= a * s[i-1]` for i from N down to 2, with `a = exp(-2*pi*f*dx)` (`Sound_computeEmphasisFactor`, line 1237). The first sample is unchanged. The manual describes this as a +6 dB/octave inverted low-pass with the +3 dB point at the "Pre-emphasis from" value.
3. **Frame grid.** `dt` defaults to `halfdt_window / 4` when the time step is 0 (line 293), which is 25% of the window length as the manual says. `numberOfFrames = 1 + floor((duration - 2*halfdt_window)/dt)`, and frame 1 is centred at `x1 + 0.5*(duration - dx - (n-1)*dt)` (lines 294-301).
4. **Window.** Gaussian with `N = floor(2*halfdt_window/dx)` samples (line 297). Weights are `w(i) = (exp(-48*((i - (N+1)/2)/(N+1))^2) - e^-12) / (1 - e^-12)` (lines 317-320), so the window is zero at both edges. The manual calls this "sidelobes below -120 dB" with an effective duration of twice the Window length parameter.
5. **Intensity.** The frame intensity is the maximum squared sample in the window region of the pre-emphasised Sound (lines 333-341). It is a peak, not an RMS. A frame whose maximum is zero is left empty, because Burg cannot process all zeros (line 342-343).
6. **Burg.** `burg()` (lines 36-89) takes `numberOfPoles = Melder_iround(2 * nFormants)` (line 392) and calls `VECburg` (`dwsys/NUM2.cpp`, lines 1430-1496), the Burg recursion (reflection coefficients `2*num/denum`, error update `xms *= 1 - a_i^2`). The prediction polynomial is `z^m - a_1 z^(m-1) - ... - a_m` (lines 44-47), and its roots are folded into the unit circle with `Roots_fixIntoUnitCircle` (`dwsys/Roots.cpp`, lines 72-77; roots with |z| > 1 are replaced by `1/conj(z)`).
7. **Root selection.** Only roots with `imag >= 0` are used (conjugate pairs). The frequency is `|atan2(im, re)| * Nyquist / pi`, kept only if it lies in `[safetyMargin, Nyquist - safetyMargin]` (lines 61-87). For the Burg command `safetyMargin = 50 Hz` (line 392); for "keep all" it is 0 (line 400).
8. **Sorting.** `Formant_sort` (`fon/Sound_to_Formant.cpp`, line 267) sorts each frame by frequency, carrying bandwidths with it.

Split-Levinson (`Sound_to_Formant_willems`, line 406, command "sl") is a separate code path (`splitLevinson`, lines 169-265). It always sets bandwidth to 50 Hz (line 261), which the manual confirms (`manual_formant.cpp`, lines 609-610).

### 7.2 Parameters and defaults

| Parameter | GUI label and default (`praat_Sound.cpp` 1449-1453) | Manual | Code meaning |
|---|---|---|---|
| Time step | 0.0 (= auto) | 25% of window length | `dt`; 0 means `halfdt/4` |
| Max. number of formants | 5.0 | any multiple of 0.5 | `numberOfPoles = round(2*nFormants)`; `maxnFormants = (poles+1)/2` |
| Formant ceiling | 5500.0 Hz | 5500 (female), 5000 (male), 8000 (child) | resample target `2 * ceiling`; also sets Nyquist for frequencies |
| Window length | 0.025 s | effective; actual Gaussian is 2x | `halfdt_window`; Gaussian length `2 * halfdt_window` |
| Pre-emphasis from | 50.0 Hz | +3 dB point | `preemphasisFrequency` |

Notes on the table:
- The GUI default and the manual agree. The `FORM` strings are the authoritative defaults in this tree.
- `Sound_to_Formant_burg` requires `nsamp_window >= numberOfPoles + 1`, otherwise it throws `Window too short.` (line 299). The Burg LPC command has a different error message (`dwtest/test_LPC.praat` line 94); a reimplementation should not conflate them.
- If `numberOfFrames < 1`, the code falls back to one frame centred on the whole Sound (lines 302-307). This is undocumented in the manual (unverified as a user-visible behaviour).

### 7.3 The Formant object

Declared in `fon/Formant_def.h` (class `Formant`, parent `Sampled`) and `fon/Formant.h`:
- Sampled axis: `xmin, xmax, nx, dx, x1`; `dx` is the frame step, and the manual calls frame duration equal to frame step (`manual_formant.cpp`, lines 65-66).
- `maxnFormants` (INT16) is the capacity, set to `(numberOfPoles+1)/2` by `Formant_create` (`fon/Formant.cpp`, lines 80-92).
- Each frame: `intensity` (double), `numberOfFormants` (INT16), and a vector `formant[]` of `Formant_Formant` (`frequency`, `bandwidth`, both double, in Hz). Frames can have fewer formants than `maxnFormants`, so the number of formants is per frame (`Formant_getMinNumFormants`/`MaxNumFormants`, lines 94-107).

Stale comments: `fon/Formant.h` lines 35-46 (the `Formant_create` postconditions) still refer to `maximumNumberOfPairs`, `numberOfPairs`, `formants[]` and `bandwidths[]`, which do not exist in `Formant_def.h`. The implementation is the authority; a reimplementation should not copy those comments.

### 7.4 Bandwidth reporting

The bandwidth of a Burg pole is `-ln(|z|^2) * Nyquist / pi` (`fon/Sound_to_Formant.cpp`, lines 84-85), where `Nyquist = 0.5 / dx` of the resampled Sound. Equivalently, with pole radius r, `B = -ln(r^2) * fs / (2*pi)`. The manual states bandwidth in Hz (`manual_formant.cpp`, line 87) and does not give this formula, so the formula is taken from source only.

Two bandwidth conventions to be aware of:
- Burg and "keep all" use the pole formula above, so bandwidths are frame-dependent.
- Split-Levinson sets all bandwidths to a constant 50 Hz (line 261). A reimplementation that reports bandwidths for "sl" must reproduce that constant, not estimate it.

### 7.5 Replicating numerically: differential test plan

Reference generation needs a Praat binary, which is not in this tree (unverified whether one exists on this machine). The plan:

1. **Fixtures.** Use `dwtest/sa1.wav` (92 KB, 16 kHz speech) and the synthetic cases in `test/fon/Sound_to_Formant.praat` (sinusoid plus Gaussian noise, random sample rates 16-96 kHz). `dwtest/sa1_10020_burg_20220616.Formant` is a binary (`ooBinaryFile`) Formant object, presumably from `sa1.wav`, but its generating parameters are not recorded in the repo (unverified). Use it only as a sanity reference after its parameters are confirmed.
2. **Reference output.** A Praat script that runs `To Formant (burg)` with an explicit grid of parameters and writes, per frame, `intensity`, `numberOfFormants`, and each formant's frequency and bandwidth (e.g. `Down to Table` with bandwidths, or `Save as text file`). Record the Praat version and the build used.
3. **Parameter grid.** Vary `maximumNumberOfFormants` over {4, 4.5, 5, 5.5, 6}, ceiling over {5000, 5500, 8000}, window over {0.005, 0.025}, pre-emphasis over {0, 50, 200}, and time step over {0, 0.01}. Include the 0-ceiling and ceiling-equals-Nyquist branches.
4. **Comparison.** Exact match on frame count, frame times (to 1e-9 s), and `numberOfFormants`. For frequencies and bandwidths, a tolerance is needed; a value of 0.01 Hz is a starting guess (unverified, not derived from any measured Praat noise floor). Compare sorted formants, since `Formant_sort` is applied.
5. **Known sensitivities.** Root finding and the Burg recursion use `longdouble` accumulators (`dwsys/NUM2.cpp`, lines 1443-1447), so the reimplementation should use at least double precision in the sums. Resampling (`Sound_resample`, precision 50) is a separate source of mismatch; test the resampler on its own first.

### 7.6 Unverified claims

- The sa1 `.Formant` reference parameters (above).
- The 0.01 Hz tolerance.
- Whether a Praat binary is available for reference generation.
- That "keep all" and Burg differ only in the safety margin. This is what the code shows, but I did not run it.
- The odd-window framing quirk: `halfnsamp_window = N/2` and the frame spans `2*halfnsamp` samples (lines 297, 331-332, 346), so for odd N the frame is one sample shorter than N and its window indexing starts at its own first sample. I read this but did not test whether it changes results.

---

## 8. Intensity, pulses, and voice measures

Sources: `praat-source/docs/manual/` (Intensity, Sound__To_Intensity, Intro_6_2, PointProcess, Voice, Voice_1..3, Voice_6, Voice_report, PointProcess__Get_jitter__*, Advanced_pulses_settings) and `praat-source/fon/` (Sound_to_Intensity.cpp, Intensity.cpp, praat_Sound.cpp, Sound_to_PointProcess.cpp, Pitch_to_PointProcess.cpp, VoiceAnalysis.cpp, AmplitudeTier.cpp, PointProcess.cpp). Where the manual and the source disagree, the source is what the reimplementation should match, and the disagreement is listed in the last subsection.

### 1. Intensity

### 1.1 Definition and units

An Intensity object is a Matrix with one row and linearly spaced frames `t_i = t_1 + (i-1) dt`, with values in dB SPL, meaning dB relative to 2e-5 Pa (manual: `Intensity.html`). In `fon/Sound_to_Intensity.cpp` the reference is `hearingThreshold_in_Pa = 2.0e-5`, and a frame value below 1e-30 relative power is clamped to -300 dB. The object is created by `fon/Intensity.cpp` (`Intensity_create`, `Intensity_init` via `Matrix_init` with dy = 1, one row).

### 1.2 Computation (Sound: To Intensity...)

Form defaults (`fon/praat_Sound.cpp`, `CONVERT_EACH_TO_ONE__Sound_to_Intensity`): Pitch floor = 100 Hz, Time step = 0 (auto), Subtract mean = true. The old form (`CONVERT_EACH_TO_ONE__old_Sound_to_Intensity`) passes `subtractMean = false`.

Parameters in `Sound_to_Intensity_` (source comment and manual agree):

- `logicalWindowDuration = 3.2 / pitchFloor`. This is the "effective" window length the manual refers to.
- `physicalWindowDuration = 6.4 / pitchFloor`; the window is spanned by `halfWindowSamples = floor((physicalWindowDuration/2) / dx)` on each side of the frame centre.
- Default time step (timeStep = 0) is `logicalWindowDuration / 4 = 0.8 / pitchFloor`.
- Window shape: `x = (i - centre) dx / halfWindowDuration`, `w = I0((2 pi^2 + 0.5) * sqrt(1 - x^2))`, i.e. a Kaiser window with beta ~ 20.2. The manual calls this "Kaiser-20" (`Sound__To_Intensity___.html`) and, in Intro 6.2, "Gaussian ('double Kaiser')". Treat the source formula as authoritative.
- Sound is squared, then averaged with the window. With `subtractMeanPressure`, the mean of each windowed segment is removed (`centre_VEC_inout`) before squaring. This is a local mean over the window, not a global DC removal.
- For each frame, `P = sum_channels sum_samples(x^2 w) / sum_channels sum_samples(w)`, and the value is `10 log10(P / (2e-5)^2)`.
- The frame centre is the nearest sample to the frame time (time accuracy half a sample). Stereo input is handled by pooling channel energies.
- `veryAccurate` is `false` in code; if enabled, the Sound is upsampled first to avoid super-Nyquist content from squaring.

Minimum length: the physical duration must be at least `6.4 / pitchFloor` (about 64 ms at 100 Hz); otherwise an error is thrown.

Unverified: the manual describes the intensity as ripple-free to 0.00001 dB for a periodic signal; I have not checked this numerically.

### 1.3 Averaging (Intensity: Get mean...)

Settings: time range (t1, t2) with t1 >= t2 meaning the whole object; averaging method energy, dB, or sones. Per `fon/Intensity.cpp`, these map to unit codes through `v_convertStandardToSpecialUnit`: energy `10^(0.1 x)`, sones `2^(0.1 x)`, dB identity. The mean is taken in that domain and converted back. The manual formulas are:

- dB: `(1/(t2-t1)) integral x(t) dt` (implemented as a sampled mean, `Sampled_getMean_standardUnit`; the integral wording is the manual's, the sampled form is what the code does)
- energy: `10 log10{ (1/(t2-t1)) integral 10^(x(t)/10) dt }`
- sones: `10 log2{ (1/(t2-t1)) integral 2^(x(t)/10) dt }`

The median (`Intensity_averaging_MEDIAN`) is a separate path via `Sampled_getQuantile` at 0.5. Maximum, minimum, standard deviation and time-of-extremum queries are in the manual pages `Intensity__Get_*.html`; I have not read their implementations.

Behaviour stated in the manual: energy-averaged mean of an Intensity made from a Sound should be close to that Sound's mean SPL.

Default averaging method in the query form: unverified (not read).

### 1.4 Display settings

View range default 50-100 dB (manual Intro 6.2). Visual only; it does not affect values.

### 2. Pulses (PointProcess)

A PointProcess is a sorted sequence of times `t_i` in `[tmin, tmax]`, with `t_{i+1} > t_i` (manual `PointProcess.html`; `fon/PointProcess.cpp`). Pulses are the glottal-closure estimates used by voice analysis. Two generators are used by the periodic commands:

### 2.1 Sound & Pitch: To PointProcess (cc)

Implemented in `fon/Pitch_to_PointProcess.cpp`, function `Sound_Pitch_to_PointProcess_cc`. The algorithm, as read from the code:

1. Iterate over voiced intervals of the Pitch (`Pitch_getVoicedIntervalAfter`).
2. In each voiced interval, start at its midpoint, where F0 is `f0middle`. Find the extremum (maximum) within `+-0.5/f0middle` of that midpoint via `Sound_findExtremum`. This is the first pulse.
3. Walk right, then left, from the anchor. At each step, search for the best cross-correlated period in the window `[tmax + 0.8/f0, tmax + 1.25/f0]` (or the mirror interval to the left) with `Sound_findMaximumCorrelation`. Add a pulse when correlation > 0.3 and peak > 0.01 times the global absolute peak, and the new pulse is more than `0.8/f0` after the last added pulse on that side (`addedRight`).
4. Boundary points at the voicing edges require correlation > 0.7 and peak > 0.023333 times the global peak.
5. If correlation is -1 (no candidate), the search steps by one period and continues.

Constants 0.8, 1.25, 0.3, 0.7, 0.01 and 0.023333 are from the code. The manual does not state them; treat them as the reference behaviour, with the code as source.

`Sound_findMaximumCorrelation` is a static helper in `fon/Pitch_to_PointProcess.cpp` (line 163); its internals were not read in full. Unverified: exact correlation normalisation.

### 2.2 Sound & Pitch: To PointProcess (peaks)

Same walk and pitch-based anchoring, but each step uses `Sound_findExtremum` in the window `[tmax - 1.25/f0, tmax - 0.8/f0]` (or the mirror). No correlation test. Includes maxima, minima, or both, as selected. It is the choice the manual documents as "peaks".

### 2.3 Sound: To PointProcess (periodic, cc / peaks)

Defined in `fon/Sound_to_PointProcess.cpp`. Each is a composition: `Sound_to_Pitch(me, 0.0, fmin, fmax)` (autocorrelation, time step auto), then the pitch-based finder above. The manual (`Voice_6...`) says the one-step periodic cc uses the AC pitch, which is suboptimal for voice work. For voice analysis, use a two-step path: `Sound: To Pitch (raw cc)` followed by `Sound & Pitch: To PointProcess (cc)`. The "optimize for voice analysis" setting in the Sound window does this.

Other PointProcess generators (`Sound_to_PointProcess_extrema`, `_zeroes`) are simple local-extremum and zero-crossing finders in `fon/Sound_to_PointProcess.cpp`. Zero crossings are interpolated linearly.

### 3. Jitter and shimmer

Notation: `T_i` is the i-th interval (period) between consecutive points; `N` is the number of intervals. Two range settings always apply: a period range `[pmin, pmax]` and a `maximumPeriodFactor` on the ratio of consecutive intervals. The manual's defaults (`Voice_2__Jitter.html`) are `pmin = 0.8 / pitchCeiling`, `pmax = 1.25 / pitchFloor`, and and a maximum period factor of 1.3 (the value used in the voice-report examples; the form that holds the voice-report default was not located, so this is unverified). The voice report itself is in `fon/VoiceAnalysis.cpp`. Setting `pmin == pmax` disables the range filter (code convention in `fon/VoiceAnalysis.cpp`).

A term is skipped when any of its intervals falls outside `[pmin, pmax]` or when a consecutive ratio exceeds `maximumPeriodFactor`. `N` is decremented accordingly. The denominator uses the adjusted `N`. Results are `undefined` if too few terms remain.

### 3.1 Jitter (`PointProcess: Get jitter ...`, `fon/VoiceAnalysis.cpp`)

Let `meanPeriod = (sum of valid T_i) / N_valid`, computed by `PointProcess_getMeanPeriod` with the same filter rules.

- **local**: `jitter = [ sum_{i=2}^{N} |T_i - T_{i-1}| / (N-1) ] / meanPeriod`. Result is a fraction (printed as %).
- **local, absolute**: the same sum without division by meanPeriod, in seconds.
- **rap** (relative average perturbation): `absAP = sum_{i=2}^{N-1} |T_i - (T_{i-1}+T_i+T_{i+1})/3| / (N-2)`; `RAP = absAP / meanPeriod`. Range 0 to 2.
- **ppq5**: `absPPQ5 = sum_{i=3}^{N-2} |T_i - (T_{i-2}+...+T_{i+2})/5| / (N-4)`; `PPQ5 = absPPQ5 / meanPeriod`. Range 0 to 4.
- **ddp**: code returns `3 * RAP` (`PointProcess_getJitter_ddp`). The manual gives `absDDP = sum |(T_{i+1}-T_i) - (T_i-T_{i-1})| / (N-2)`, then `DDP = absDDP / meanPeriod`, and states the result is exactly 3 times RAP. See section 4 on the internal wording.

The voice-report jitter values are the five of these in the order local, local absolute, rap, ppq5, ddp, printed with 3 decimals as percent (or seconds for absolute).

### 3.2 Shimmer (`fon/AmplitudeTier.cpp`, `fon/VoiceAnalysis.cpp`)

Amplitudes are taken at the pulses through `PointProcess_Sound_to_AmplitudeTier` (called from `fon/VoiceAnalysis.cpp`; its sampling method, peak-search or nearest-sample, is unverified). Amplitude values `A_i` then go through `AmplitudeTier_getShimmer_*_u` with the same period filter (`pmin`, `pmax` on the pulse-to-pulse distances) and a `maximumAmplitudeFactor` (default 1.6, `fon/praat_Tiers.cpp`) on the ratio of consecutive amplitudes. The denominator in all linear measures is the mean of `A_1 ... A_{size-1}` over the whole tier (not only the valid terms, per the code).

- **local**: `mean_valid |A_i - A_{i-1}| / mean(A)`. Manual: "average absolute difference between amplitudes of consecutive periods, divided by the average amplitude."
- **local, dB**: `20 * mean_valid | log10(A_{i-1}/A_i) |`. Code uses the ratio. The manual's wording "log of the difference" is wrong; see section 4.
- **apq3**: `mean_valid |A_i - (A_{i-1}+A_i+A_{i+1})/3| / mean(A)`.
- **apq5**: five-point neighbourhood, same form.
- **apq11**: eleven-point neighbourhood (`i-5 .. i+5`), 10 neighbours plus the point.
- **dda**: `3 * apq3` (`PointProcess_Sound_getShimmer_dda`). Manual: "Praat's original Get shimmer ... three times APQ3."

Shimmer is meaningful only on sustained vowels (manual). The voice report prints shimmer local (%), local dB (dB, 3 decimals), apq3, apq5, apq11, and dda (%).

### 4. Voice report

Command: Pulses > Voice report in the Sound window, or `Voice report: tmin, tmax, floor, ceiling, maxPeriodFactor, maxAmplitudeFactor, silenceThreshold, voicingThreshold` in a script (manual Voice_6 example: `0, 0, 75, 500, 1.3, 1.6, 0.03, 0.45`). The function `VoiceAnalysis.cpp` writes these sections, in order:

1. Time domain (tmin, tmax, duration; the window is selection-driven).
2. Pitch: median, mean, standard deviation, minimum, maximum (Hz).
3. Pulses: number of pulses, number of periods, mean period and its standard deviation (seconds).
4. Voicing: fraction of locally unvoiced frames (with counts), number of voice breaks, degree of voice breaks (fraction, with break seconds and total seconds). Breaks are inter-pulse intervals longer than `1.25/floor` (manual `Voice_1__Voice_breaks.html`; code uses `pmax` = `1.25/floor`). Unvoiced frames use the voicing and silence thresholds (defaults 0.45 and 0.03 per the manual).
5. Jitter: local, local absolute, rap, ppq5, ddp.
6. Shimmer: local, local dB, apq3, apq5, apq11, dda.
7. Harmonicity of voiced parts: mean autocorrelation, mean NHR, mean HNR (dB).
8. H1-minus-H2: mean of points and mean of curve (dB) via `PointProcess_Sound_to_H1minusH2Tier_u`.

The manual's pages describe only jitter, shimmer, voice breaks, and the HNR (Voice 4, not read here). Sections 1, 2, 3 and 8 are present in code but are not described in the voice pages I read. The reimplementation should include them.

The period floor and ceiling used for the report are `pmin = 0.8 / ceiling` and `pmax = 1.25 / floor` (`VoiceAnalysis.cpp`, consistent with `Voice_2__Jitter.html`).

### 5. Discrepancies and unverified items

- **DDP wording.** `PointProcess__Get_jitter__ddp____.html` says absDDP is "one third of the mean absolute difference of differences", but the formula given has no 1/3, and the same page says DDP is exactly 3 times RAP. Code returns `3 * RAP`. Implement `3 * RAP`. The `N` decrement rule for DDP in the manual (three-term validity) also differs from the code, which uses the RAP filter; the code is the reference.
- **Shimmer dB.** Manual says "log of the difference"; code uses `log10(A_{i-1}/A_i)`. Implement the ratio.
- **Shimmer denominator.** Code averages the amplitudes of all points except the last, not only valid terms. The manual says "average amplitude". Implement as code.
- **Intensity window.** Manual says both "Kaiser-20" and "Gaussian (double Kaiser)". Code is `I0(beta sqrt(1-x^2))` with beta = 2 pi^2 + 0.5. Implement as code.
- **Mean intensity integral.** Manual writes an integral; code uses a sampled mean. Confirm `Sampled_getMean_standardUnit` before relying on either.
- **Unverified:** the internals of `Sound_findMaximumCorrelation`; `Sound_findExtremum`; `PointProcess_Sound_to_AmplitudeTier` sampling method (interpolated or nearest; not read); default averaging method of Intensity Get mean; voice-report default values beyond those cited; the `PointProcess.cpp` report function near lines 47-59 (appears to be a separate PointProcess-level report with the same jitter lines; not read); the intensity ripple claim (0.00001 dB).

---

## 9. Praat scripting language compatibility

Praat scripts (`.praat` files and text typed into a Script window) are the main automation interface for users, and many lab workflows depend on them. This section says what the language contains, how much of it to match, how to build the interpreter, and which commands to implement first.

Sources: the scripting tutorial under `praat-reimplementation/praat-source/docs/manual/Scripting_*.html` (chapters 3 to 8 and 10), the formula pages `Formulas_3`, `Formulas_6`, `Formulas_7` in the same folder, and the sendpraat pages `praat-source/docs/sendpraat.html` and `manual/Scripting_8_1`/`8_2`. The interpreter source in `praat-source/sys/` was consulted only to confirm the parser style (see 9.4). Frequencies below come from a grep of the 336 `.praat` files in the source tree; those are mostly test scripts, so the counts show what the test suite uses, not what users run.

### 9.1 Language features the manual documents

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

### 9.2 How much to target

Recommend a tiered plan, measured against the repo's own script corpus as an acceptance test.

- **Tier 0 (first release).** Lexical rules; numeric and string variables; all of `Scripting_5_1` to `5_5` and `5_9`; the `writeInfo*`/`appendInfo*` family; `assert` and `exitScript`; formulas with the `Formulas_3` precedence; `length`, `left$`, `right$`, `mid$`, `index`, `rindex`, `fixed$`, `percent$`; `selectObject`/`plusObject`/`minusObject`/`removeObject`/`selected$`; `form`/`endform` with the seven basic field types; calls to whichever menu commands the reimplementation has implemented.
- **Tier 1.** Arrays and dictionaries; vectors and matrices (`#`, `##`, and the `Scripting_5_7` functions); `beginPause`/`endPause` with the full field set; query-to-variable assignment; file I/O; `include`; `runScript`; `variableExists`; predefined platform and version variables.
- **Tier 2.** sendpraat and `praat --send` (see 9.3); `runSystem`; `stopwatch`; `nocheck`/`nowarn`; `...` continuation lines; the remaining form types.
- **Tier 3 (defer or decline).** Old-syntax forms (`'var'` interpolation, `Draw...` names) can be implemented as a translation pass later, not in the core parser. `sendsocket` is documented as removed in Praat 7 (`Scripting_6_7`), so do not implement it. Exact byte-for-byte output formatting is Tier 3 unless the corpus tests require it.

The main cost is not the grammar. It is the size of the menu-command surface, since every command is reachable from a script. Build the command registry from the same table that drives the GUI, so that a menu item and its script form are one entry. Then the long tail of commands can be added without touching the parser.

### 9.3 sendpraat and inter-process control

Praat has three ways to be controlled from outside: the `sendpraat` subroutine and program (`docs/sendpraat.html`, `Scripting_8_1`, `8_2`), `praat --send` (`Scripting_6_9`, recommended in the docs because it starts Praat if needed), and `praat --run`/`--open` for script and file arguments (`Scripting_6_9`). Sendpraat takes a `timeOut` (ignored on Windows), a `fullTrust` flag that gates file writes and system calls (`Scripting_8_1`), a program name, and one or more script lines. The reimplementation should keep the same CLI surface, the same `fullTrust` gating, and `runScript:` for long scripts. The transport is platform-specific. `sys/praat.cpp` near line 109 mentions a message file that sendpraat writes; the mechanism on each platform is unverified beyond that comment.

### 9.4 Interpreter design options

**A. Hand-written parser in the host language.** Praat's grammar is line-oriented: one statement per line, keyword-led blocks, `@` calls, and `.`-prefixed locals. The repo's own formula parser is hand-written recursive descent (`sys/Formula.cpp`, `Formula_parseExpression` near line 1913). A hand-written parser can match the quirks exactly (the `-2^6` rejection, right-associative `^`, `fi`/`endif`, the `;` terminator, dollar-suffix typing, `#`/`##` literals, query-assignment rules) and can report errors by line number, which the manual relies on (`exitScript` and `assert` messages include line numbers). It adds no dependency. Cost: we write and test the parser ourselves.

**B. Embed a general-purpose language and translate.** Lua, Python, Tcl or JavaScript would supply expressions, control flow and debugging. The problems are: Praat statements are commands with colon-separated arguments and no assignment (`Draw line: 0, 50, length, 50`), which do not map onto host syntax; query results change type based on the target variable; line-number error reporting must be rebuilt; and the `fullTrust` gate from sendpraat would have to be enforced around an runtime that has full OS access by default. Rejected as the core interpreter. It could be reconsidered later as an optional extension language.

**C. Hybrid (recommended).** A hand-written, line-based statement parser builds a small AST and runs it directly. The same expression evaluator serves formulas inside command arguments and statement-level assignments. Command dispatch goes through the shared command registry (9.2). `include` and `form` are handled in a pre-pass, because the manual says `include` happens before the rest of the script is considered and that a form's values are needed by the body (`Scripting_5_8`, `6_1`).

Recommendation: option C.

### 9.5 Most-used script commands to support first

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

### 9.6 Unverified and open items

- Whether the interpreter accepts curly-quoted strings as used in the manual examples.
- Whether `elif` and `fi` are accepted as statements, or only `elsif`/`endif` (the manual documents `fi` only for formulas).
- The exact numeric-to-text formatting. The manual shows values such as `1.4142135623730951`, which look like shortest round-trip output, but the algorithm was not checked.
- How menu commands are dispatched inside `sys/Interpreter.cpp`. Only the file layout and the presence of the parser were confirmed.
- The frequency counts come from test scripts and may not reflect user scripts.
- Whether `nocheck` and `nowarn` change behaviour beyond suppressing errors or warnings was not checked in the manual.

---

## 10. Manipulation, resynthesis, and articulatory synthesis

Sources read: `praat-reimplementation/praat-source/docs/manual/Manipulation.html`, `Intro_8_1__Manipulation_of_pitch.html`, `Intro_8_2__Manipulation_of_duration.html`, `Manipulation__Get_resynthesis__overlap-add_.html`, `Sound.html`, `Sound__Resample___.html`, `Sound__Filter__pre-emphasis____.html`, `Sound__Filter__de-emphasis____.html`, `Sound__Lengthen__overlap-add____.html`, `Articulatory_synthesis.html`; source `fon/Manipulation.cpp`, `fon/Sound.h`, `artsynth/*`. Nothing was compiled or run.

### 10.1 The Manipulation object

A Manipulation holds four parts (manual `Manipulation.html`): the original Sound; a PointProcess of glottal pulses; a PitchTier (the pitch targets); and a DurationTier (initially empty). Its attributes are `timeStep` (common value 0.010 s), `pitchFloor` (common 75 Hz) and `pitchCeiling` (common 600 Hz).

Creation (`Sound_to_Manipulation`, `fon/Manipulation.cpp` line ~114) runs the Sound: To Pitch analysis, places pulses where the sound has energy, converts the pitch contour to a dense PitchTier, and adds an empty DurationTier. Two variants take a precomputed Pitch or PointProcess (`Sound_Pitch_to_Manipulation`, `Sound_PointProcess_to_Manipulation`).

Resynthesis is a switch in `Manipulation_to_Sound` (`fon/Manipulation.cpp` ~line 669). The manual lists overlap-add (original sound + pulses + pitch tier + duration tier), LPC-based (LPC + pulses + pitch tier), and pulse-train or hummed output from pulses alone or the pitch tier alone. The manual calls the first method overlap-add. The usual name for this family is PSOLA; that the two are the same algorithm is **unverified**. The overlap-add functions copy pulse-centred windows (`copyRise`, `copyFall`, `copyBell`, `copyBell2`, `copyFlat`, ~lines 209-285) into a new Sound.

Two modes are stubs. `Manipulation_PULSES_FORMANT`, `..._FORMANT_INTENSITY`, `..._LPC_INTENSITY` and `..._PITCH_LPC_INTENSITY` return an empty `autoSound` in the source. The manual does not list them, so the reimplementation should not port them as-is.

Editing is through ManipulationEditor (`foned/ManipulationEditor.cpp`), which is GUI work and belongs in the editor section. The manual's workflow is: drag pitch points (with Stylize pitch to thin them), add duration points, shift-click to hear the original, and Publish resynthesis to get a new Sound. Scripted control is through Replace/Extract commands (`Manipulation__Replace_pitch_tier.html` and siblings). Precise scripted manipulation (Create PitchTier, Add point, Replace pitch tier) is documented in `Intro_8_1`, and the duration example in `Intro_8_2` makes a step change by placing two points 0.000002 s apart (0.084999 and 0.085001). That is a usable regression case.

Test coverage: the listing of `test/fon/` shows no Manipulation test. Resampling has eight (`resample*_8.praat`), and `Sound_concatenate.praat` exists. The Manipulation path needs tests written from scratch.

### 10.2 Sound filters and transforms

The Sound menu in `Sound.html` lists many commands. The table covers the ones that matter for a v1 decision. "Read" means the manual page or source was opened for this section. Items marked "listed" were seen only in `Sound.html`.

| Command | What it does (source) | Phase |
|---|---|---|
| Sound: Resample... | Sinc interpolation with depth `Precision` (default 50); precision 1 is linear; anti-alias low-pass when downsampling. Declared `fon/Sound.h:113`. Read. | v1 |
| Filter (pre-emphasis) / (de-emphasis) | alpha = exp(-2 pi F dt); pre: y_i = x_i - alpha x_(i-1); de: recursive y_i = x_i + alpha y_(i-1). Declared `fon/Sound.h:189-191`. Read. | v1 |
| Filter (one formant) in-place | `Sound_filterWithOneFormantInplace`, `fon/Sound.h:187`. Listed. | v1 |
| Scale peak / Scale intensity, Fade in / out, Multiply by window, Set value, Extract part, Combine to stereo | Simple per-sample or windowing operations. Listed. | v1 |
| Sounds: Concatenate | Joins sounds; `test/fon/Sound_concatenate.praat` exists. Listed. | v1 |
| Filter (pass/stop Hann band), Filter (formula) | Spectral or formula filters. Listed; source location not checked. | v1 (verify) |
| Lengthen (overlap-add) | `Sound_lengthen_overlapAdd`, `fon/Sound.h:344`. Factor 1.5 standard; manual says values over 3 do not work. Read. | v2 |
| Deepen band modulation | `fon/Sound.h:345`. Listed. | v2 |
| Change gender / Change speaker | `dwtools/Sound_extensions.h:151`. Depends on formant and pitch tools. Listed. | v2 |
| Sound & Formant: Filter; Sound & FormantGrid: Filter; LPC & Sound: Filter | Filters driven by formant or LPC objects. Listed. | v2 (with Formant and LPC) |

Resampling and pre/de-emphasis are both short, well-specified, and used in the analysis pipeline (pitch and formant analysis also resample internally: `dwtools/Sound_to_Pitch2.cpp:113`, `dwtools/Sound_extensions.cpp:2800`). They should be in v1 with the resampling tests carried over as acceptance tests. The exact numerical output of the sinc resampler must be compared against the old binary, because Praat users compare numbers across versions.

### 10.3 Articulatory synthesis (`praat-source\artsynth`)

What is there. The folder has 34 files and about 3,450 lines of C/C++ and headers (counted with `wc`). The pieces are:

- **Speaker**: kind is "Female", "Male" or "Child"; 1 or 2 vocal-cord masses (`artsynth/Speaker.h`).
- **Articulation (Art)**: 29 named muscle activities, each 0 to 1 (`artsynth/Articulation_enums.h`; 30 enum lines including the placeholder at index 0).
- **Artword**: a time-indexed track of targets for each muscle (`artsynth/Artword.h`, `Artword_setTarget`).
- **Vocal tract model**: `Speaker_to_Delta.cpp` (366 lines) and `Delta.h`, a tube model where each tube segment has coupled mass and spring terms and left/right neighbours. Source comments cite equation numbers from Boersma (1998).
- **Synthesis**: `Artword_Speaker_to_Sound.cpp` (436 lines) steps the model with `oversampling` substeps per sample (`Dt = 1/fsamp/oversampling`). It can also output three width, pressure and velocity Sounds.
- **Editing and display**: `ArtwordEditor.cpp`, plus drawing and a "Play movie" command in `praat_Artsynth.cpp`.

Build wiring. It is a separate static library (`artsynth/Makefile`, `artsynth/meson.build`). The meson file passes `gtk_dep` as a dependency of the library, so the synthesis core is linked to GTK. The reimplementation would have to separate that before porting.

Cost and evidence. The manual says the example utterance takes about five minutes on a 1997 computer and about one second on a 2019 computer (`Articulatory_synthesis.html`, step 11). Neither figure was measured here. The test folder contains an example file `test/fon/examples/hallo.Artword` and a manual movie script `test/manually/movies.praat`. There are no automated tests for the synthesis output.

Recommendation: out of scope for v1, and a v3 candidate at best. Reasons: it is a self-contained physics model with about 3,400 lines and no automated tests; and it depends on a drawing layer and an editor that the reimplementation has not designed yet. Whether any of the owner's projects needs it was not checked. Keep `hallo.Artword` as a file-format fixture so a later port can read the existing format.

### 10.4 Recommended phasing

- **v1:** Resample (with the eight resampling tests as acceptance tests); pre-emphasis and de-emphasis; the simple DSP transforms in the table (scale, fade, window, extract, set value, concatenate, stereo combine); one-formant and Hann-band filters. Manipulation object creation and overlap-add resynthesis with pitch and duration tiers, scripted only (no editor), with the pulse-only and pitch-only outputs. Those reuse the Pitch and PointProcess code that v1 must have anyway, so the marginal cost is the overlap-add routine and its tests.
- **v2:** ManipulationEditor and Publish resynthesis. Lengthen, deepen band modulation, change gender and speaker. Formant- and LPC-driven filters. The LPC resynthesis path for Manipulation.
- **Out of scope (v3 or later, unless the owner decides otherwise):** Articulatory synthesis (Art, Artword, Speaker, Delta), including its editor and movie playback. Also the empty stub modes in `Manipulation_to_Sound`; do not port them.

### 10.5 Open items

- Whether the Manipulation overlap-add here equals the PSOLA of the literature: **unverified**. Compare outputs on a reference sound before claiming equality.
- Filter (pass/stop Hann band) and Filter (formula): source location not checked.
- Speed figures for articulatory synthesis: from the manual, **not measured**.
- No code was compiled or run, so no output was compared with the existing binary.
- Whether the owner's own projects need articulatory synthesis: not established. This is the owner's decision.

---

## 11. User interface: windows, menus, dialogs, shortcuts

Base path for citations: `praat-reimplementation\praat-source\docs\` (abbreviated `docs/`). Manual pages are `docs/manual/<Name>.html`; screenshots are `docs/pictures/` or `docs/manual/<Name>_N.png`. Claims marked **[unverified]** were not checked against Praat's C/C++ source, which this section did not read.

### 11.1 Window model

- **Objects window** (`docs/manual/Objects_window.html`). Left: the List of Objects, numbered ("1. Sound 1"). Right: the Dynamic menu, a column of buttons that depends on the selected object's class. Bottom-left fixed buttons: Rename..., Info, Copy..., Remove, Inspect. Top menus: Praat, New, Open, Save (dynamic; empty when nothing is selected), Help. `docs/pictures/screenshot-3.png` shows a Sound selected: View & Edit first, then Play, Draw >, Query >, Modify >, Annotate >, Analyse periodicity >, Analyse spectrum >, To Intensity..., Manipulate >, Convert >, Filter >, Combine >, with "Sound help" above them. The "Sound help" button and the Analyse-periodicity/spectrum groupings are not described in `docs/manual/Dynamic_menu.html`; this is version drift **[unverified which version is newer]**.
- **Picture window** (`docs/manual/Picture_window.html`). Menus: File, Edit, Margins, World, Select, Pen, Font, Help. The manual has no screenshot of it; its layout is **[unverified]**.
- **Editors** (`docs/manual/Editors.html`). One window per object or view, titled with the object name. Edits apply immediately, there is no save-before-close step, the window disappears when its object is removed, and renaming changes the title.
- **Settings (dialog) windows** (`docs/manual/Scripting_2__How_to_script_settings_windows.html`). Any command whose name ends in "..." opens a form. File commands open a platform file selector instead.
- **ScriptEditor** (`docs/manual/ScriptEditor.html`; `docs/pictures/screenshot-2.png`). A text editor with Run and history paste.

### 11.2 Menu tree (mirrors the reference)

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

### 11.3 Keyboard shortcuts

`docs/manual/Keyboard_shortcuts.html` (footer dated 2022-07-01). On Windows and Linux, "Command" is Ctrl, "Option" is Alt, and "Extra-Command" is Ctrl+Shift. Context-dependent meanings are in parentheses. The table below keeps the entries a reimplementation needs first. Mac-only F-key entries are omitted; on Windows and Linux, pitch is F5 and on the Mac it is F10.

| Key (Win/Linux) | Context | Action |
|---|---|---|
| Ctrl-A | all | Zoom all |
| Ctrl-C / Ctrl-V / Ctrl-X | all | Copy / Paste / Cut (Sound: paste after selection; Ctrl-Shift-V paste over) |
| Ctrl-Z / Ctrl-Y | all | Undo / Redo |
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

### 11.4 Dialog anatomy

`docs/manual/Scripting_2__How_to_script_settings_windows_1.png` shows the "Sound: Draw" form. Layout: a title bar with a close button; right-aligned labels; text fields in pairs (value and a "(= all)" or "(= auto)" hint); a checkbox ("Garnish"); an option menu ("Drawing method"); a bottom row with Help and Standards on the left and Cancel, Apply and OK on the right, with OK as the default button.

The manual defines the dialog as a script contract:

- A script line is the command name, then the arguments top to bottom and left to right, in the same order as the form.
- Argument types are numeric, boolean (yes/no or 1/0), multiple-choice (option menu and radio box are equivalent in scripts), text, formula (with `~`), file, and colour (a name, a grey value, or an `{r,g,b}` vector).
- The "(= all)" and "(= auto)" hints are display text; zero is the value.
- The ScriptEditor's `#form` / `#endform` header generates a form from a script (`docs/manual/ScriptEditor.html`).
- The history mechanism records each OK as a replayable line (`docs/manual/ScriptEditor.html`, Example 1).

### 11.5 What must match closely and what can be modernized

**Must match closely (compatibility or user expectations):**

1. Command names, menu hierarchy, the "..." suffix (opens a form) and the ">" submenu convention. Scripts, `sendpraat`, Add to fixed menu, Add to dynamic menu and history paste all address commands by name (`fixed_menu_commands.html`; `Scripting_8__Controlling_Praat_from_another_program.html`).
2. Argument order, types, defaults and zero-means-all/auto semantics of every form. This is the scripting API.
3. Each OK emits one replayable command line (history).
4. Objects window semantics: numbered list, click replaces selection, Shift-click adds to it (`Shift-click.html`), fixed buttons, and View & Edit as the first dynamic button.
5. Editor pointer semantics: click sets the cursor, drag selects time, Shift-click and Shift-drag act on several marks, Command-click (Ctrl-click) mutes a channel, and the Group button synchronizes windows (`SoundEditor.html`, `Click.html`, `Shift-drag.html`).
6. The keyboard table in 11.3, with Command mapped to Ctrl on Windows.
7. Picture window drawing model: world coordinates, margins derived from font size (`Font_menu.html`), the 16 named colours, the four fonts and five preset sizes, and backslash-digraph special characters. Pixel-identical output is not required; the same drawing commands must produce equivalent pictures.
8. Object lifecycle: Remove closes the object's editor, rename updates titles, and editors are independent windows.

**Can be modernized (presentation):**

1. Native file selectors, message boxes and menus. Use the OS dialogs; keep the command names.
2. Dark mode. The Objects and ScriptEditor screenshots are dark, while the SoundEditor screenshot is light. Whether this is an OS theme or a Praat theme is **[unverified]**. Use theme tokens so both modes work.
3. HiDPI and font scaling. Keep layout in logical units; the Picture window's margins already depend on font size.
4. Window chrome. The screenshots' title bars and buttons are not identical; whether they are the OS's own is **[unverified]**.
5. Font families. The manual names Times, Helvetica, Palatino and Courier (PostScript names). Map them to bundled equivalents. The IPA and Symbol glyphs need the SIL fonts shipped in the docs folder (`docs/Charis-7.000.zip`, `docs/DoulosSIL-7.000.zip`, `docs/CharisSIL-6.200.zip`).
6. Menu bar placement. On macOS the Praat menu sits in the system menu bar (`Praat_menu.html`); on Windows and Linux, in-window menus are acceptable.
7. Export formats. Keep PDF, PNG and EPS; add SVG, and treat "Windows metafile" as a platform-specific item.
8. Pixel layout, button sizes and the checkbox glyph style.

**Unverified or open:**

- The Picture window layout has no screenshot in the manual.
- Screenshot-1 and screenshot-3 show menus and buttons (Time, Intensity, Pulses, Sound help) that the manual pages read here do not describe. The manual pages carry footers from 2014 to 2023, so the screenshots are probably from a newer build **[unverified]**.
- The platform of the screenshots is not stated; the chrome looks like a GTK-style Linux window **[unverified]**.
- The menu definitions in Praat's source were not read; all menu contents above come from the manual and screenshots.

---

## 12. Testing, validation, milestones, licensing, and risks

Status: draft for owner review. Reference state: Praat source at commit `56ed24e` (master, committed 2026-11-01), as found in `praat-source`. Nothing in this section has been built or run yet; claims marked **(unverified)** are not checked against the tree.

### 12.1 Differential testing against reference Praat

**Oracle.** Two reference sources, used for different purposes:

1. **Pinned source build (primary).** Build `praat_barren` from the pinned commit with `make PRAAT_GRAPHICS=barren PRAAT_AUDIO=none`, the same target the existing CI uses (`praat-source/.github/workflows/build-and-test.yml`). This is headless and scriptable with `praat --run script.praat`.
2. **Released binaries (drift check).** The Windows, macOS and Linux downloads linked from `praat-source/docs/download_win.html`, `download_mac.html` and `download_linux.html` (release tag `v7.0.02` per the Windows page). These are used once per oracle bump to confirm that the source build and the shipped binary agree. Their exact version against the pinned commit is **(unverified)**.

**Corpus.** A fixed, versioned set of files with SHA-256 hashes recorded in the repo:

- *Synthetic:* pure tones (440 Hz, 1 kHz, 10 kHz, 100 kHz at 192 kHz sample rate), a 100 Hz to 20 kHz linear chirp, white noise with a fixed seed. Generate these inside Praat (`Create Sound from formula`) so the oracle and the reimplementation start from identical sample values, and store the generating script alongside.
- *Speech:* a small set of vowels and sentences. `praat-source/dwtest/` already contains `sa1.wav` and a TIMIT-derived `.phn`/`.TextGrid` pair. Their licence status is **(unverified)** and must be checked before any of them enters a public repo (see 12.4).
- *Edge cases:* silence, clipping, DC offset, very short files (below one analysis window), 8-bit and 24-bit WAV, mono and stereo.

**Procedure.** For each corpus item and each parameter set in a matrix (for example, pitch floor and ceiling, time step, voicing threshold, octave-jump cost):

1. Run the oracle script, which writes its result object to a text file and an export table.
2. Run the reimplementation headlessly (Node CLI or a test harness; the browser UI is not involved) on the same input.
3. Compare with a comparator script that reads both outputs and emits a per-item JSON report.

**Tolerances (proposed, to be validated).** These extend the thresholds in Sections 7.3 and 10 of the main report. They are targets, not measured results.

| Quantity | Comparison | Proposed tolerance |
|---|---|---|
| Pitch (F0), pure tones | Per-frame absolute error, Hz | < 1 Hz |
| Pitch (F0), speech | Per-frame error on voiced frames | < 5% relative |
| Voicing decision | Per-frame agreement | >= 99% of frames |
| Formants F1 to F3, vowels | Per-frame absolute error, Hz | < 50 Hz |
| Intensity | Per-frame absolute error, dB | < 0.1 dB |
| Spectrogram | Power in dB per bin | < 0.1 dB, plus < 1% pixels differing in rendered PNG |
| FFT / windowing primitives | Relative error vs. oracle | < 1e-9 in float64 |

Frame alignment must be checked first. A time-offset error of one frame can look like a large pitch error, so the comparator reports the frame-time vector before any error metric. Discrete decisions (voicing, octave jumps, formant count) are compared by agreement rate, not by numeric tolerance. Praat's text-output precision is **(unverified)** and sets the floor for any byte-level comparison.

### 12.2 Golden-file tests

- Golden files are the oracle's outputs, stored under `test/golden/<oracle-version>/`, with a `MANIFEST` recording the Praat commit, build flags, corpus hashes and generation date.
- Format-level files (TextGrid, Pitch and Formant short text, WAV headers) are compared byte-for-byte, because they are text and must round-trip exactly (Section 7.2 of the main report).
- Numeric outputs are compared with the tolerances in 12.1, never byte-for-byte.
- Golden files are regenerated only by an explicit oracle bump, reviewed as a diff of the manifest and the numeric deltas. Silent regeneration is not allowed.
- The Praat suites in `praat-source/test/` and `praat-source/dwtest/` (entry points `runAllTests_batch.praat`) test Praat itself with internal assertions. They can seed additional golden cases where they print values, but they are not a validation of the reimplementation by themselves.

### 12.3 Cross-platform CI matrix

Existing CI (verified): a single workflow, `praat-source/.github/workflows/build-and-test.yml`, runs on `ubuntu-latest` only, on pushes and pull requests to `master`. It builds `praat_barren` and runs Praat's own `test` and `dwtest` batch scripts. It has no Windows or macOS job. That is relevant because the reimplementation targets all three platforms, and the Windows and macOS reference builds are not exercised by any CI in this tree.

Proposed CI for the reimplementation (new repository):

| Job | Runner | Contents | Gate |
|---|---|---|---|
| unit | ubuntu, windows, macos (latest) | Unit tests (FFT, LPC, TextGrid parser, coordinate transforms) | Every PR |
| format round-trip | ubuntu, windows, macos | Byte-level golden tests for TextGrid, Pitch, Formant | Every PR |
| differential-quick | ubuntu | Small corpus (about 10 items), pinned oracle built from source | Every PR |
| differential-full | ubuntu (self-hosted or scheduled) | Full corpus and parameter matrix | Nightly and before each release |
| browser | ubuntu and windows; Chromium, Firefox, WebKit | Playwright integration tests, audio playback smoke test | Every PR |
| oracle-check | windows, macos | Released Praat binary against the source-build golden set | Per oracle bump |

Open items **(unverified)**: whether the Praat source builds cleanly on GitHub-hosted Windows and macOS runners (the authors describe MSYS2 and macOS builds in `praat-source/HOW_TO_BUILD_ALL.md`, but CI has not been run for those here). If it does not, the fallback is to pin SHA-256 hashes of the released binaries and fetch them.

### 12.4 Licensing

**What the tree says (verified in files):**

- `praat-source/README.md` section 2.1: most source is under the GPL, version 2 or later, or version 3 or later; "the whole of Praat is distributed under the General Public License, version 3 or later."
- Source headers, for example `praat-source/fon/AmplitudeTier.cpp` lines 6 to 16: GPL v3 "or (at your option) any later version." A grep found the GPL notice in 463 files under `fon/`, `sys/` and `dwsys/`.
- `praat-source/docs/LICENSE.txt`: the website is CC BY-SA 4.0. The manual pages in `docs/manual/` are GPL-3.0-or-later. Several third-party items are excluded (SIL fonts under OFL 1.1; Microsoft Windows screenshots in `docs/pictures/`, claimed as fair use by the authors).
- `praat-source/org.praat.Praat.metainfo.xml` lines 4, 12 and 13: `project_license` is GPL-3.0-or-later and `metadata_license` is MIT. The MIT line applies to the metadata file itself.
- No top-level `LICENSE` file exists in the repository root (verified by directory listing).
- `praat-source/external/` vendors third-party libraries (whispercpp, opusfile, flac, lame, espeak and others), each with its own licence. These were not audited.

**What it implies (analysis, not legal advice):**

1. **Derived code.** If any implementer reads Praat's C/C++ source and ports its logic, the result is plausibly a derivative work. A GPL-3.0-or-later Praat would then impose GPL terms on the reimplementation if it is distributed. A web app served to users is still distribution under the GPL's terms, so this is not avoided by moving to the browser.
2. **Clean-room route.** Implementers work from the manual pages, published papers and black-box oracle outputs, and do not read `praat-source/fon/` or `sys/` for algorithms. This needs a written provenance rule and a log of sources consulted. Copyright generally protects expression rather than algorithms, but patent status of published methods is **(unverified)** and needs separate review.
3. **Running Praat as an oracle** (executing the binary or the source build, and comparing its output files) is a different activity from copying code. Whether oracle outputs carry any licence obligation is **(unverified)**.
4. **Documentation reuse.** Copying manual text into the reimplementation's docs triggers GPL obligations; copying website text triggers CC BY-SA 4.0 ShareAlike.
5. **Corpus redistribution.** Files derived from TIMIT and other third-party speech data may carry licence restrictions. Check each file before committing it to a public repository.
6. **Name.** Whether "Praat" may appear in the product name is **(unverified)**; treat it as a trademark question for the owner.

**Owner decision required:** the reimplementation's licence, clean-room versus derived-code policy, corpus licensing, and product naming. These should be reviewed by someone qualified to give legal advice before any code is written against the Praat source.

### 12.5 Milestones and acceptance criteria

These map onto the nine phases in Section 5 of the main report. Week counts follow that plan.

| Milestone | Weeks | Acceptance criteria |
|---|---:|---|
| M0 Oracle and CI | 1 | Pinned oracle builds from source on Linux; corpus v0.1 hashed; golden manifest written; CI green on ubuntu, windows and macos for the empty project |
| M1 Audio I/O and waveform | 2-3 | WAV read matches oracle sample values exactly for 16/24/32-bit PCM; playback smoke test passes in all three browsers |
| M2 Spectrogram | 4-6 | Power in dB within 0.1 dB on the synthetic corpus; rendered PNG differs in < 1% of pixels |
| M3 TextGrid | 7-9 | Byte-identical round trip on the golden set; round trip on 100 real user files with zero diffs (the 100-file source is **(unverified)** and needs to be obtained) |
| M4 Pitch | 10-12 | Tolerances in 12.1 met on the full pitch matrix; voicing agreement >= 99% |
| M5 Formants | 13-15 | F1 to F3 within 50 Hz on vowel corpus; formant export byte-identical in format |
| M6 Intensity and measurements | 16-17 | Intensity within 0.1 dB; measurement queries match oracle to displayed precision |
| M7 Release candidate | 20-22 | All differential tests pass; three-OS CI green; signed installers or web deployment verified; licence review closed |

M1 to M6 are gated on the differential-quick job passing. M7 is gated on the nightly full run passing for two consecutive weeks.

### 12.6 Risk table

| Risk | Likelihood | Impact | Mitigation | Owner |
|---|---|---|---|---|
| Implementation derives from GPL source without a licence decision | Medium | Critical | Clean-room rule and source log from M0; owner review of 12.4 | Owner |
| Oracle drift: source build and release binary disagree | Medium | High | Pin commit and binary version; oracle-check job; manifest in golden set | Lead dev |
| Reimplementation reproduces Praat's bugs, or "correct" behaviour is undefined | Medium | High | Decide explicitly bit-compatibility versus documented behaviour per feature (open decision, Section 11) | Owner, DSP |
| Pitch algorithm differs from the reference | High | Critical | Differential tests from M4; frame-alignment check first | DSP specialist |
| Formant tracking unstable on real speech | High | High | Burg LPC per manual; vowel corpus; expert review | DSP specialist |
| CI cannot build Praat on Windows or macOS runners | Medium | Medium | Fallback: pinned released binaries by SHA-256 | Lead dev |
| Corpus contains licence-restricted audio | Medium | High | Per-file licence check; keep restricted files out of the public repo | Owner |
| Browser audio limits (sample rate, latency, Safari behaviour) | Medium | Medium | Browser CI matrix; document supported sample rates | UI dev |
| Timeline inconsistency: main report says "20-week timeline" in 9.1 and totals 22 weeks in 9.2 | Certain (already in text) | Low | Fix in main report; this section uses 22 weeks | Author |
| Solo or small-team capacity below the 2-3 contributors assumed | High | High | Scope cut per Section 9.1 (defer intensity, filtering) | Owner |
| Patent status of published methods | Unknown | Unknown | Legal review, as in 12.4 | Owner |

### 12.7 Open items for this section

- Confirm the licence position in 12.4 with the owner and a qualified reviewer before M0.
- Verify whether the pinned source builds on Windows and macOS runners.
- Decide the bit-compatibility policy for each feature.
- Obtain or decide on the 100-file TextGrid set for M3.

---

