# LangTool reimplementation plan: Praat annotation workspace

Prepared 2026-11-02. Primary target: [praat/praat.github.io](https://github.com/praat/praat.github.io).

## 1. Purpose and scope

Build a modern, offline-capable, cross-platform phonetics application, provisionally called **LangTool**, that preserves the research workflows and observable behavior of Praat. “LangTool” here means a speech analysis and annotation application; it does not mean the LanguageTool grammar checker.

This is one contributor's detailed specification for **TextGrid annotation and its synchronized audio workspace**. It deliberately concentrates implementation depth here. It supplies integration contracts for two complementary contributors rather than claiming to specify every Praat feature.

The linked repository contains the application implementation and documentation, despite its website-like name. Its [README](https://github.com/praat/praat.github.io/blob/56ed24ef5efedffd06112a2bc1c0530bddc3a55e/README.md) describes speech analysis, synthesis, manipulation, annotation, grammar models, statistics, and publication graphics. Those broader capabilities need separate workstreams.

Success means a researcher can open an existing recording and TextGrid, inspect the signal, annotate intervals and events, audition selections, and return a usable TextGrid to Praat. A polished waveform demonstration without reliable editing and interchange does not meet this goal.

### Three-person ownership proposal

| Contributor | Owns | Deliverable and boundary |
|---|---|---|
| A — this specification | TextGrid domain model, parser/writer, annotation commands, editor interaction, tier rendering, annotation acceptance fixtures | A usable annotation workspace with fake audio/analysis adapters first, then integrated services |
| B | Audio decoding, bounded streaming, playback timing, waveform summaries, numerical analyses | Headless services returning timestamped samples and results; owns DSP accuracy and device adapters |
| C | Application shell, object registry, command routing and scripting, project persistence, packaging, publication graphics | Object selection and editor lifecycle; owns installers and application-wide policy |

These are proposed assignments for the three people, not a claim that other contributors have accepted them. Agree on section 8 contracts before coding independently. Person A owns TextGrid serialization even though Person C owns generic project storage; there must be one authoritative codec.

### Explicit exclusions from this contributor's first delivery

Full Praat script compatibility; pitch/formant algorithms; synthesis and manipulation editors; statistical and grammar tools; EEG; speech recognition, forced alignment and diarization; spelling dictionaries; publication drawing commands; binary TextGrid support. Track these as named compatibility gaps. Do not expose working-looking commands backed by placeholders.

## 2. Evidence and compatibility baseline

### Pinned reference

Repository HEAD inspected: [`56ed24ef5efedffd06112a2bc1c0530bddc3a55e`](https://github.com/praat/praat.github.io/commit/56ed24ef5efedffd06112a2bc1c0530bddc3a55e), dated 2026-11-01. Its [version header](https://github.com/praat/praat.github.io/blob/56ed24ef5efedffd06112a2bc1c0530bddc3a55e/main/main_Praat.h) identifies `7.0.03beta`. This is a research snapshot, not an endorsement of a beta as the shipping compatibility target. Before reference recordings, choose and record one obtainable reference executable and its checksum. Do not combine its behavior with another version silently.

Evidence was gathered by reading repository metadata, selected source files, official manual pages, and one manual illustration. No Praat executable was run, no numerical parity experiment was performed, and no live editor screenshot was captured. Runtime-sensitive details below remain explicit verification tasks.

### Evidence vocabulary

- **Documented:** the linked official manual describes the behavior.
- **Source-observed:** selected pinned implementation code was inspected; this is supporting evidence, not a runtime result.
- **Proposed:** a LangTool architecture, usability choice, or acceptance requirement.
- **Unresolved:** requires a reference run, screenshot, or team decision before claiming parity.

### Source map

| Reference | Use |
|---|---|
| [Annotation tutorial](https://praat.org/manual/Intro_7__Annotation.html) | Overall create, edit, save, reopen workflow |
| [TextGrid object](https://praat.org/manual/TextGrid.html) | Tier types and opening with optional audio |
| [TextGridEditor manual](https://praat.org/manual/TextGridEditor.html) | User interaction reference |
| [TextGrid formats](https://praat.org/manual/TextGrid_file_formats.html) | Interchange specification and restrictions |
| [Pinned TextGridEditor.cpp](https://github.com/praat/praat.github.io/blob/56ed24ef5efedffd06112a2bc1c0530bddc3a55e/foned/TextGridEditor.cpp) | Editor composition and lifecycle |
| [Pinned TextGridArea.cpp](https://github.com/praat/praat.github.io/blob/56ed24ef5efedffd06112a2bc1c0530bddc3a55e/foned/TextGridArea.cpp) | Annotation interaction edge cases |
| [Pinned TextGrid.cpp](https://github.com/praat/praat.github.io/blob/56ed24ef5efedffd06112a2bc1c0530bddc3a55e/fon/TextGrid.cpp) | Domain operations and validation reference |
| [Pinned TextGrid_def.h](https://github.com/praat/praat.github.io/blob/56ed24ef5efedffd06112a2bc1c0530bddc3a55e/fon/TextGrid_def.h) | Serialized object structure |
| [Pinned TextGridArea preferences](https://github.com/praat/praat.github.io/blob/56ed24ef5efedffd06112a2bc1c0530bddc3a55e/foned/TextGridArea_prefs.h) | Settings inventory for later verification |
| [Official annotation illustration](https://praat.org/manual/TextGrid_file_formats_1.png) | Inspected tier and time geometry example |

The online manual can change independently of the pinned repository. Archive the equivalent pinned `docs/manual/` pages and reference capture metadata with the fixture suite before freezing release acceptance.

## 3. Product and technology decisions

**Proposed default: C++20 domain/services, Qt 6 Quick/QML desktop UI, and CMake builds.** Keep the annotation core free of UI toolkit types. The [Qt Quick documentation](https://doc.qt.io/qt-6/qtquick-index.html) supports the intended arrangement: QML user interfaces with C++ extension points. This choice provides one desktop UI implementation and direct integration with audio and scientific services.

Use Qt Quick Controls for dialogs and accessible controls; implement waveform and tier surfaces as batched custom scene-graph items. Do not create one QML control per audio sample or boundary. Keep text input in a native toolkit text component for input methods and selection support.

Use a low-level PCM playback adapter, provisionally Qt Multimedia `QAudioSink`, supplied by B. [Qt Multimedia](https://doc.qt.io/qt-6/qtmultimedia-index.html) provides raw audio output and cross-platform device interfaces. Its documentation also identifies platform differences: the existence of an API is not proof of identical timing or format behavior.

Select and pin a supported Qt minor version and dependency lock on implementation kickoff. The documentation links are rolling references, not a dependency lock. Choose additional codecs or DSP libraries in B's specification after format, precision, distribution, and maintenance requirements are settled. Do not add an entire second runtime just for annotation.

### Supported platform proposal

| Target | First release | Required checks |
|---|---|---|
| Windows 11 x64 | Required | DPI scaling, paths, audio device changes, shortcuts |
| macOS Apple Silicon | Required | Retina rendering, menu conventions, input methods, audio output |
| Ubuntu 24.04 x64 | Required | Wayland and X11, font availability, audio output |
| macOS Intel / Windows ARM64 / Linux ARM64 | Follow-up | Build and behavior coverage before advertising support |
| Browser and mobile | Out of initial scope | Separate latency, filesystem and input specification |

Cross-platform means installable packages tested on each declared system. It does not mean reproducing every obsolete platform in Praat's distribution history.

### Code reuse policy

Implement against documented behavior and fixtures. Existing class hierarchies, allocation macros, widget infrastructure, and historical platform wrappers are not the proposed architecture. Consult legacy implementation when documentation is ambiguous and record what that consultation resolves.

Reuse a component only when measured correctness, a clear interface, tests, maintenance quality, and compatible licensing justify it. Keep a reuse ledger with source revision, component, modifications, rationale, license, and notices. Praat's README describes GPL licensing for the overall distribution; copying code requires an explicit distribution decision. An independent implementation must still preserve attribution and licensing for any copied assets or documentation. This document grants no license to those materials.

## 4. Core workflow and behavior contract

### 4.1 Opening and creating annotations

**Documented:** a TextGrid contains interval tiers and point tiers. It can be edited alone or alongside Sound/LongSound. See the [TextGrid object manual](https://praat.org/manual/TextGrid.html).

Proposed flow:

1. Import a recording into the object list.
2. Run `To TextGrid…`, entering ordered tier names and identifying point tiers.
3. Create a distinct annotation object linked to the recording, inheriting its time domain.
4. Select the recording and annotation and run `View & Edit`.
5. Edit, save a TextGrid, close, and reopen in both applications.

Also support opening an annotation without audio. Keep editing enabled; disable playback with an explanation. A missing recording must never make the annotation unrecoverable.

Do not assume the first time is zero. Store source time origins explicitly. Define how mismatched audio and annotation domains are displayed without shifting either silently. Duplicate names must not be used as object or tier identity.

### 4.2 State model

Proposed editor state separates:

- document: ordered tiers, labels, times, revision and dirty state;
- view: visible time span, pane sizes, analysis visibility and vertical scroll;
- selection: active tier, selected entity, cursor and ordered time range;
- text editing: caret, selected text, composition state and edit transaction;
- transport: requested playback range, actual source position and status;
- transient gesture: drag anchor, candidate time, affected IDs and preview.

A selection or zoom change is not a document edit. Playback cannot modify labels. A redraw cannot push undo history. Stale analysis responses cannot change the current selection.

### 4.3 Interaction contract

The following condensed behaviors are **documented** in the [editor manual](https://praat.org/manual/TextGridEditor.html): selecting an interval selects its time range; Enter inserts a boundary/point; label splitting depends on text selection; dragging moves marks, Shift-drag moves coincident marks across tiers; Tab auditions a selection and stops playback at its current position. Removing an internal boundary combines adjacent labels, retaining a single copy when equal. The editor includes tier-scoped Find and Find again.

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

### 4.4 Split semantics: high-priority reference cases

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

### 4.5 Proposed drag transaction

On press, resolve a stable entity ID and take a before-image. During movement, update a preview only. Determine a proposed target using the visible time transform and snapping policy. On release, validate every affected tier and commit one command. Escape cancels the gesture without dirtying the document.

For aligned multi-tier moves, collect exact coincident times from the original model; do not identify unrelated marks by a wide floating-point epsilon. Snapping is an interaction tolerance measured in screen units and converted to time at the current zoom. It is separate from domain equality.

Preserve interval adjacency and strict event order. Illegal moves must not cause crossed boundaries, duplicate points, or partially moved tiers. **Unresolved:** reference behavior for invalid drops, tie-breaking between snap targets, drag thresholds, auto-scroll and the modifier's interaction with editor preferences. Capture these rather than claiming this proposed transaction design exactly describes Praat.

### 4.6 Text, search and focus

Support IPA, combining diacritics, multilingual input, paste, bidirectional labels and platform input methods. Store literal label content. Avoid silent Unicode normalization or trimming. Distinguish raw Praat trigraph text from a display representation; define any conversion as an explicit operation.

Coalesce ordinary typing into sensible undo groups. Commit or cancel input-method composition before changing the target interval; test that Enter during composition does not unexpectedly insert a boundary.

Keep text shortcuts and annotation shortcuts in separate routing contexts. Verify the reference mapping for Command/Ctrl variants and function keys. Provide menu alternatives for operating-system shortcut collisions. Retain keyboard focus visibility and expose boundaries and intervals through an accessible list/navigation interface in addition to the drawing surface.

**Unresolved search details:** wraparound, case sensitivity, empty query, normalization, matches spanning composition, and end-of-tier messages. Do not substitute regular expressions for literal search without an explicit mode.

## 5. Data model and invariant policy

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

## 6. TextGrid codec and persistence

### 6.1 Required compatibility

Initial interoperability is full and short text TextGrid import/export. Unknown classes and binary signatures produce clear unsupported-format errors. Do not treat a binary file as corrupt text.

Implement a token scanner and structural parser, with source locations and typed diagnostics. Avoid one regular expression per line. The [format manual](https://praat.org/manual/TextGrid_file_formats.html) describes free-standing data tokens, doubled embedded quotes, comments, text encodings and line endings. Preserve precision and literal strings through decoding and writing; semantic round-trip equality is the objective, not identical whitespace.

Proposed import pipeline:

```text
bytes → identify format/encoding → decode → scan tokens
      → parse declared structures → validate → publish document
```

Set explicit byte, tier, entity and string-size limits. Check counts before allocating. Never publish half a parsed document. Preserve file path, detected encoding and diagnostics separately from annotation content.

### 6.2 Codec verification checklist

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

### 6.3 Proposed save behavior

Default to UTF-8 text with deterministic numeric formatting and enough digits to round-trip doubles. Offer full and short text export. Never rewrite annotation times using the display's decimal precision.

Write a temporary sibling file, flush it, then replace the destination using the platform's safe replacement facility. Failure must leave the previous file usable and the document dirty. Only a successful explicit save establishes a new clean revision.

Project metadata and crash recovery belong to C. Store source-audio links and view state there; keep TextGrid export interoperable. Recovery snapshots never overwrite an explicit export automatically. Detect external file changes before replacement and provide a conflict flow.

## 7. Rendering and screenshot fidelity

### 7.1 Inspected visual evidence

The official [TextGrid illustration](https://praat.org/manual/TextGrid_file_formats_1.png) was inspected. It shows a common 0–2.3 second axis, sentence and phoneme interval tiers, an event tier, aligned vertical marks, centered labels, and phonetic glyphs. **It is a publication-style diagram, not an editor screenshot.** It establishes relationships and typography examples, not toolbar positions, active selection colors, or exact editor dimensions.

Use its geometry to create an original fixture: a 2.3-second synthetic recording, two interval tiers and one event tier. Choose original short labels and publish their exact expected times. Reproduce label alignment without copying the manual's entire example.

### 7.2 Proposed editor layout

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

### 7.3 Required reference capture set

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

Store reference captures and LangTool captures separately. Annotate differences as behavioral, visual or platform-native. No exact pixel tolerances can honestly be fixed until these captures exist.

Proposed acceptance separates geometry from rasterization: assert time alignment numerically, check labels and selection state structurally, and use masked screenshot comparisons for stable canvas regions. Allow OS-specific text rasterization and native window chrome. A deliberate visual modernization must preserve recognizable selection and editing affordances and be recorded as a product decision.

## 8. Contracts between contributors

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

A and B agree on source-time mapping, exclusive/inclusive playback endpoints, frame rounding, multichannel display, cancellation and latency compensation. Represent absent or unvoiced analysis results explicitly; zero is a valid measurement in some domains. Commands and results carry units.

B's playback clock, not a GUI timer, supplies the stopped cursor position. Progress events identify their playback session so an old callback cannot move the cursor during a new session. A source revision change invalidates waveform and analysis caches. Out-of-order results are discarded by token and revision.

C owns command IDs and application-wide shortcut registration. A supplies supported commands, enablement predicates and typed parameters. GUI actions, future scripting and automated fixtures should call the same commands. Headless annotation operations must not require a window or audio device.

A emits content revisions and changed entity IDs. C handles project autosave, object lifecycle and recovery. B receives immutable snapshots or explicit ranges, never mutable UI objects.

## 9. Performance and operational requirements

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

## 10. Validation strategy

### 10.1 Reference fixtures

Maintain a manifest for every compatibility claim:

```text
fixtureId, source/reference revision, executable checksum,
input hashes, platform, action sequence, observed state,
expected output, comparison rule, evidence paths, known differences
```

Generate original recordings: silence, impulses, short tones, stereo channel differences and a nonzero-origin annotation. Use short original spoken fixtures only when required. Avoid redistributing unlicensed recordings.

### 10.2 Domain and codec tests

Use meaningful invariant and interoperability tests:

- command followed by undo restores labels, geometry and stable identities;
- redo restores the same post-command state;
- rejected commands leave revision, content and dirty state unchanged;
- randomized legal edits retain ordering and adjacency;
- a grouped move either updates every participant or none;
- writing and rereading preserve times and literal label strings;
- files exported by LangTool open in the pinned Praat executable;
- reference-exported files import in LangTool without losing entities;
- malformed imports cannot replace an open document.

### 10.3 End-to-end acceptance scenarios

| ID | Action | Pass condition |
|---|---|---|
| A01 | Create annotation from nonzero-origin audio | Correct domains, ordered tier types, independent object |
| A02 | Select interval, type IPA and switch tier | Correct text target; no composition or text loss |
| A03 | Insert at caret and undo | Reference label split; exact original restored |
| A04 | Split with time and text selections | Every decision-table case matches captured reference |
| A05 | Drag boundary, then group-drag | Correct geometry and one undo step per gesture |
| A06 | Attempt duplicate or crossing edit | No corrupt or partial mutation |
| A07 | Remove boundary between equal/different labels | Reference merge rule and no invented whitespace |
| A08 | Play selection and stop halfway | Audible range and stopped cursor meet agreed timing tolerance |
| A09 | Import, edit, export and reopen in Praat | Semantic content and time precision retained |
| A10 | Find across active tier | Correct entity, highlighted substring and verified wrap behavior |
| A11 | Open without audio, save, recover | Annotation remains fully usable |
| A12 | Close during analysis or device change | No crash, stale callback or missing committed edits |

Measure playback timing tolerance using loopback or a deterministic fake sink before setting a release threshold. A passing UI timer test cannot establish audio timing parity.

### 10.4 Release gate

Run domain and codec tests headlessly on all three systems. Run UI, font and real playback smoke checks on each system. Record supported file variants and unresolved differences in a compatibility report. Do not label the application “Praat compatible” without a scoped matrix stating which workflows and formats were verified.

## 11. Implementation sequence and handoffs

### Milestone 0 — Freeze the contract

Agree ownership, platform baseline, reference executable, source-time conventions, shortcut policy and library versions. Capture V01–V05 and resolve split cases. Deliver an evidence manifest and signed-off interface definitions. Reference capture is outstanding work, not completed research.

### Milestone 1 — Headless annotation core

Implement domain entities, invariant validation, commands, inverses and full/short text codecs. Deliver fixtures, diagnostics and a small headless runner. Exit when valid files round-trip and failed operations are demonstrably atomic.

### Milestone 2 — Annotation-only editor

Implement common time transform, tier surface, text binding, selection, insert/remove, drag, undo/redo and search using fake adapters. Exit when editing does not depend on DSP or playback and screenshot geometry checks pass.

### Milestone 3 — Integrated audio workspace

Integrate B's bounded waveform and transport services and C's object lifecycle. Add time-range audition, stopped cursor positioning and optional asynchronous analysis overlays. Exit when A01–A12 pass for the supported scope.

### Milestone 4 — Cross-platform hardening

Complete input methods, keyboard navigation, accessible entity navigation, high DPI, long-document profiling, export conflicts, crash recovery integration and packages. Exit with a per-platform compatibility report and reproducible fixture results.

### Milestone 5 — Expand explicitly

Add reference-verified advanced boundary commands, spelling support, binary files or scripting only as separate scoped additions. Aligners and transcription services must output ordinary validated annotation commands or importable documents; they must not bypass the invariant layer.

## 12. Open decisions and risks

| Item | Owner | Required resolution |
|---|---|---|
| Beta HEAD versus stable reference | All | Pin obtainable executable and never silently change baseline |
| Actual editor screenshots absent | A | Capture V01–V08; distinguish diagram from UI evidence |
| Complete split and focus behavior | A | Fill decision table with reference outputs |
| Invalid drag and snap tie-breaks | A | Capture behavior at multiple zoom and DPI levels |
| Playback stop accuracy and time origin | B + A | Specify mapping and measure physical/deterministic timing |
| Unicode caret coordinate mapping | A | Test graphemes, scalar values and toolkit offsets |
| Weak-domain imports | A | Preserve with diagnostics; agree edit restrictions |
| Script compatibility expectations | C | Publish supported command/language subset before marketing |
| Codec and toolkit distribution | B + C | Pin dependencies, notices and distribution requirements |
| Publication graphics | C | Separate specification using actual graphics references |

The deliverable from this workstream is a reproducible annotation workflow with explicit evidence. Modern libraries supply the platform foundation; domain invariants, reference fixtures, file interchange and documented editing semantics determine compatibility.
