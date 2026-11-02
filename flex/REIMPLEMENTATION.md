# FieldWorks / FLEx Reimplementation Feasibility Report

**Status:** Initial technical assessment and implementation plan  
**Prepared:** 2026-11-02  
**Target:** A clean, modern, cross-platform reimplementation for Windows, macOS, and Linux  
**Reference product:** SIL FieldWorks Language Explorer (FLEx)

## Executive summary

A modern cross-platform reimplementation is technically feasible, but it is not a conventional UI port. FieldWorks is a mature linguistic platform built around a large, versioned object model, specialized multilingual text behavior, configurable views, import/export pipelines, morphological analysis, publishing, and collaborative merge semantics. Reproducing its essential behavior is a multi-year product program.

The recommended approach is a **clean reimplementation with compatibility at documented boundaries**, rather than a line-by-line translation:

1. Treat current FieldWorks behavior and public file formats as the compatibility specification.
2. Build a new domain model and application architecture without copying implementation code.
3. Make lossless `.fwdata` and `.fwbackup` interchange the first major compatibility milestone.
4. Deliver vertical slices, starting with writing systems, lists, and lexicon editing; then interlinear text; then publishing, grammar, notebook, collaboration, and integrations.
5. Maintain a permanent differential test suite that runs the same fixtures and operations through FieldWorks and the new application where automation permits.

For the primary implementation, **modern .NET with C# and Avalonia is the lowest-risk choice**. TypeScript is viable, especially with Electron, but advanced input methods, bidirectional text, desktop integration, large-project performance, and native linguistic dependencies increase the risk. The final stack choice should be made after a short, evidence-based prototype comparing C#/Avalonia and TypeScript/Electron on the hardest text-editing scenarios.

Directional delivery expectations:

- A credible lexicography MVP: **12–18 months with 5–7 experienced contributors**.
- A broadly useful release including interlinear analysis and publication: **24–36 months with 7–10 contributors**.
- Essential-feature parity, migrations, collaboration, integrations, and production hardening: **36–60 months with 8–12 contributors**.
- A team of two or three should expect **five to eight years**, with significant scope prioritization.

These ranges are not commitments. Phase 0 should replace them with estimates based on an agreed compatibility matrix and representative user projects.

## 1. Scope and interpretation of “essential functionality”

FieldWorks presents five main work areas: Lexicon, Grammar, Texts & Words, Notebook, and Lists. The official feature overview also emphasizes writing systems, consistency across linked data, customization, import/export, dictionary production, interlinear analysis, and concordance. For this report, “essential” means the following capabilities.

### 1.1 Project and data lifecycle

- Create, open, lock, save, copy, rename, and delete language projects.
- Import current supported FieldWorks projects and migrate older model versions.
- Create and restore `.fwbackup` archives, including writing systems, configuration, linked media, and supporting files.
- Autosave, crash recovery, atomic writes, integrity checks, repair diagnostics, and user-visible migration reports.
- Stable object identity and references across import, editing, export, and collaboration.

### 1.2 Writing systems and multilingual text

- BCP-47-based writing-system definitions and project-specific LDML data.
- Vernacular, analysis, pronunciation, and user-interface writing-system roles.
- Multiple alternatives for the same field, plus mixed-writing-system runs inside formatted text.
- Unicode normalization policy, grapheme-aware navigation, bidirectional layout, right-to-left editing, font fallback, complex-script shaping, and IME composition.
- Writing-system-specific fonts, keyboards/input methods, collation, valid characters, punctuation, spell checking, number formatting, and quotation conventions.
- Correct copy/paste, selection, search, sort, filtering, and export of multilingual rich text.

### 1.3 Core linguistic model

- Owned and referenced objects, sequences, collections, GUID identity, and referential integrity.
- Undoable transactions and consistent cascading behavior.
- Lexical entries, senses, forms, allomorphs, pronunciations, examples, etymologies, semantic domains, lexical relations, reversals, and grammatical information.
- Wordforms, analyses, glosses, morpheme bundles, text segments, translations, structured text, annotations, and discourse charts.
- Parts of speech, inflectional features, phonemes, phonological features, environments, natural classes, and rules.
- Notebook records, participants, locations, dates, record types, and linked text/media.
- Possibility lists, custom list items, custom fields, styles, publications, and project configuration.

### 1.4 User workflows

- Configurable browse/detail/document views.
- Create, edit, delete, merge, move, reorder, and link records.
- Search, filtering, sorting, concordance, record navigation, and history.
- Configurable columns and field visibility.
- Bulk edit with preview, validation, undo, and auditability.
- Cross-area navigation, such as jumping from a word occurrence to its lexical entry.

### 1.5 Lexicon and publication

- Lexicon editing, rapid data entry, semantic-domain workflows, reversal indexes, and lexical relations.
- Configurable dictionary and reversal layouts, including publications and writing-system selection.
- Preview and export to practical publication formats such as XHTML/HTML, PDF through a documented pipeline, DOCX or ODT, and interchange formats used by downstream tools.
- Media handling and stable relative links.

### 1.6 Text and linguistic analysis

- Text entry/import, paragraph and segment management, tokenization, punctuation handling, and re-tokenization.
- Word glossing and morphological analysis with reusable suggestions.
- Configurable interlinear lines and print/export views.
- Word, morpheme, gloss, and complex concordances; corpus statistics; text metadata and filtering.
- Discourse/text chart editing.
- Morphological parser integration and trace/debug workflows where users depend on them.

### 1.7 Interchange and integration

- LIFT lexicon import/export.
- SFM/MDF import with mapping and encoding conversion.
- FlexText interlinear import/export.
- FieldWorks XML project import/export and version migrations.
- Paratext interoperability, dictionary publishing services, FLExTools-style automation, and other integrations selected by the compatibility matrix.
- A documented extension API that does not expose internal UI classes.

### 1.8 Collaboration

- A safe replacement for Send/Receive, including object-aware merge, deletions, conflicts, reports, and recovery.
- Offline-first use, because many target users cannot assume continuous or high-bandwidth connectivity.
- Compatibility with FLEx Bridge should be treated as a separate decision from providing equivalent collaboration. Exact FLEx Bridge compatibility may be disproportionately expensive.

## 2. What the reference codebase shows

This assessment inspected the FieldWorks repository at commit `936ae91fe7bb2d5b9759e47eb5e95fc9bd8b388d` (2026-10-29) and liblcm at `da7140f07b92dfcc1762cbd2492ccaf667d0fb02` (2026-10-13). Counts are snapshots, not permanent properties of upstream.

### 2.1 Size and technology

The FieldWorks checkout contains approximately:

- 146 C# projects and 8 C++ projects.
- 2,538 C# source files and 140 C++ source files.
- 142 projects targeting .NET Framework 4.8 and three targeting .NET 8.
- 655 test source files and more than 6,100 NUnit-style test declarations.
- 102 runtime XML configuration files for Language Explorer, 86 XSLT files, and 438 `.resx` files.
- Extensive managed/native and COM boundaries: native Views/FwKernel rendering, generated interfaces, and registration-free COM deployment.

The build and tests are explicitly Windows-only, despite parts of the dependency ecosystem supporting Linux. The main application is a .NET Framework 4.8 WinForms host.

This explains why incremental cross-platform compilation is not a practical modernization strategy. Too many assumptions are distributed across UI, rendering, native code, COM, build tooling, and platform-specific integrations.

### 2.2 Upstream is already migrating UI, but not yet the product platform

Current upstream contains a substantial WinForms-to-Avalonia migration. Avalonia controls are hosted inside the existing WinForms process and continue to use LCModel, native/legacy services, and the Windows host. This work is valuable as a behavioral reference, particularly for multilingual editing, view composition, undo boundaries, and UI parity.

It does **not** currently make FieldWorks cross-platform: the repository documentation explicitly says runnable builds and tests are Windows-only, and the migration design is a coexistence architecture inside the legacy application.

The upstream migration strengthens the case for Avalonia as a UI candidate, but it does not remove the need for a new application boundary, portable persistence, portable integrations, and elimination of COM/native-Views dependencies.

### 2.3 The true center is LCModel

FieldWorks depends on the separate `liblcm` repository for its language-and-culture object model, persistence, migrations, writing-system integration, repositories, factories, services, undo, and backup/restore.

The current master model has:

- Model version `7000072`.
- 193 classes, of which 171 are concrete.
- 898 declared properties.
- 57 numbered migration implementation files in the current tree.

Even a test project demonstrates the scale of real data: `TestLangProj.fwdata` is approximately 42 MB and contains about 129,000 serialized objects across 89 classes. Large production projects may be substantially bigger and contain linked media.

This model is not just a schema. Application behavior depends on ownership, generated accessors, reference semantics, virtual/computed properties, validation, side effects, undo units, writing-system-aware strings, and domain services. A schema-only translation would appear to work and then corrupt or semantically alter projects.

### 2.4 XML configuration is an application language

Many tools, layouts, fields, menus, commands, columns, dictionary views, and exports are described through XML and XSLT. The current five areas are assembled from configuration, not only hard-coded screens.

A new implementation should not copy this mechanism wholesale. It should preserve user-visible configurability through typed, versioned configuration models with schemas and migrations. Importers can translate supported legacy configurations into the new representation.

### 2.5 High-risk subsystems

The following are the most difficult parts to reproduce faithfully:

1. **Multilingual rich text:** run-level writing systems, styles, grapheme clusters, bidi selection, IME state, clipboard behavior, and font/keyboard switching.
2. **Lossless LCModel compatibility:** object ownership, reference order, custom fields, unknown future data, migrations, and rich-string serialization.
3. **Interlinear editing:** tokenization, analysis reuse, cascading updates, parser suggestions, and synchronized views.
4. **Dictionary configuration and publication:** deeply nested configurable content, styles, writing-system alternatives, filtering, and multiple output formats.
5. **Collaboration:** semantic merge of identity-based XML objects, conflict behavior, deletes-versus-edits, configuration, writing-system files, and linked media.
6. **Search, filtering, and bulk edit:** these cross nearly every class and must remain responsive and undoable on large projects.
7. **Integrations:** Paratext, keyboards, spelling, encodings, media, Webonary, Pathway, FLEx Bridge, and scripting each have independent version and platform constraints.

## 3. Feasibility verdict

### 3.1 Technical feasibility: yes

There is no single algorithmic blocker. The formats are inspectable, the reference application is open source, core standards are available, and modern cross-platform frameworks can support the required desktop workflows. The new application can be substantially simpler by enforcing modular boundaries and avoiding legacy UI/native abstractions.

### 3.2 Schedule feasibility: conditional

Full essential parity is feasible only if the work is funded and managed as a product program. A one-year “port” is not credible. A small prototype could look convincing while lacking migrations, edge-case text behavior, publication fidelity, collaboration, and safe round trips—the exact areas where users can lose work.

### 3.3 Clean reimplementation feasibility: yes, with discipline

The stated preference not to reuse code is workable. The project can reference the original for observable behavior and compatibility facts while writing new code and documentation. Recommended safeguards are:

- Maintain a written compatibility specification independent of source structure.
- Record the provenance of every format and behavior requirement.
- Do not copy source files, comments, resources, layouts, icons, generated model code, or tests into the new repository without an explicit license and design review.
- Create new fixtures or use projects users have expressly licensed for testing.
- Derive tests from documented behavior and black-box observations where practical.
- Have counsel review LGPL obligations, third-party assets, trademarks, bundled fonts, localization data, and any linked/reused library before distribution.

FieldWorks and liblcm are LGPL-2.1-or-later, which permits significant reuse under its terms, but “permitted” and “consistent with this project’s clean-reimplementation goal” are different questions. This document is a technical assessment, not legal advice.

## 4. Recommended product architecture

### 4.1 Architectural style

Use a modular monolith with strict dependency rules. A distributed service architecture would add failure modes and operational complexity without helping an offline desktop application.

```text
Desktop UI
    |
Application use cases / commands / queries
    |
Domain model and domain services
    |
Persistence ports, search index, file formats, integrations
    |
SQLite / project package / external tools and services
```

Key rules:

- Domain assemblies do not reference UI frameworks, filesystems, databases, or network clients.
- Every mutation is a named command executed in a transaction and represented in undo/redo.
- Queries use purpose-built read models rather than walking an entire object graph from UI code.
- File-format implementations are adapters behind explicit versioned interfaces.
- Integrations run out of process when their stability or licensing could compromise the editor.
- UI configuration is typed and validated; no stringly typed command bus or reflection-loaded screen classes.
- Platform-specific services—keyboards, spell checking, file associations, and credential storage—sit behind narrow interfaces with three-platform contract tests.

### 4.2 Proposed modules

- `Flex.Domain`: identifiers, entities, value objects, invariants, and domain events.
- `Flex.Application`: commands, queries, transactions, undo/redo, validation, and permissions.
- `Flex.WritingSystems`: BCP-47/LDML, typography, keyboards, collation, normalization, and valid-character policy.
- `Flex.Storage`: SQLite persistence, migrations, project locking, recovery, and indexing.
- `Flex.Interop.FieldWorks`: lossless `.fwdata` and `.fwbackup` handling.
- `Flex.Interop.Lift`, `Flex.Interop.Sfm`, `Flex.Interop.FlexText`: public interchange formats.
- `Flex.Lexicon`, `Flex.Texts`, `Flex.Grammar`, `Flex.Notebook`, `Flex.Lists`: bounded feature modules.
- `Flex.Analysis`: tokenization, suggestions, parser contracts, concordance, and statistics.
- `Flex.Publishing`: dictionary/reversal configuration and renderer-neutral document model.
- `Flex.Collaboration`: operation log, merge, conflicts, transport adapters, and audit history.
- `Flex.Integrations`: Paratext, publishing services, scripting, and external processors.
- `Flex.Desktop`: application shell, navigation, accessibility, localization, and platform adapters.

The exact names may change, but the boundaries should remain enforceable in the build.

### 4.3 Persistence recommendation

Use **SQLite as the new application’s transactional working store**, with WAL mode, foreign keys, explicit schema migrations, and a separately rebuildable full-text/search index. Store linked media as files in a project package, referenced by stable logical IDs rather than absolute paths.

Do not make SQLite itself the interchange contract. Define a versioned project package manifest and support:

- Atomic package backup and restore.
- Lossless import from supported `.fwdata` model versions.
- Semantic export back to a declared FieldWorks model version.
- Preservation of unknown extension data where safe.
- A compatibility report listing every transformed, unsupported, or discarded item before commit.

During early releases, default to importing a copy rather than editing a user’s only FieldWorks project. Round-trip export should remain opt-in until differential tests prove it safe.

### 4.4 Rich text representation

Define a framework-neutral attributed-string model early. At minimum it needs:

- Unicode scalar text with stable run boundaries.
- Writing-system tag per run.
- Named style and supported inline properties.
- Object replacement/embedded data policy.
- Grapheme and bidi utilities that operate independently of controls.
- Deterministic serialization to and from FieldWorks rich-string XML.

Do not use HTML as the canonical rich-text model. HTML can be an export or clipboard representation, but browser editing normalization and DOM mutation are unsuitable as the linguistic source of truth.

### 4.5 Publishing architecture

Compile dictionary and reversal configurations into a renderer-neutral document tree. Separate:

1. Selection and ordering of linguistic content.
2. Labels and writing-system alternatives.
3. Semantic document structure.
4. Styling.
5. Rendering to interactive preview, HTML/XHTML, print/PDF, and word-processing formats.

This avoids reproducing the current mixture of layouts, generated fragments, CSS, XML, and XSLT as a single opaque pipeline.

### 4.6 Extension architecture

Offer two levels:

- A stable command/query API for trusted in-process extensions only after the core model stabilizes.
- A preferred out-of-process API using versioned JSON-RPC or local HTTP over authenticated local transport, with capability permissions and timeouts.

For user automation, a Python SDK is likely more valuable to the current community than JavaScript-only scripting. The protocol should be language-neutral so Python and TypeScript clients can coexist.

## 5. Technology choice

### 5.1 Recommended: C# on current LTS .NET with Avalonia

Advantages:

- Strong static modeling for a large domain with many invariants.
- Mature XML, SQLite, async, testing, packaging, and diagnostics ecosystems.
- One language across domain, persistence, and UI.
- Avalonia targets Windows, macOS, and Linux and already has upstream FieldWorks experimentation around difficult UI behavior.
- Easier comparison with the reference domain terminology without reusing its implementation.
- Better fit for CPU-heavy import, indexing, publication, and analysis than a browser-only runtime.

Risks:

- Avalonia text controls still require explicit testing for complex scripts, IMEs, accessibility, and platform-native behavior.
- Linux keyboard/input-method integration varies by desktop environment.
- The team must avoid importing legacy architectural patterns merely because both systems use C#.

### 5.2 Viable alternative: TypeScript + React in Electron

Advantages:

- Productive UI ecosystem and a large hiring pool.
- Consistent rendering across platforms because Electron ships Chromium.
- Strong developer tooling, component testing, and accessible UI primitives.
- TypeScript can cover UI, application services, import/export, and Node-based desktop services.

Risks:

- Contenteditable-based rich text is difficult to make deterministic for run-level writing systems, bidi selection, IME composition, and lossless undo.
- Memory overhead is material for large projects and document views.
- ICU, keyboard, spelling, media, SQLite, and file-watching requirements introduce native Node modules and packaging complexity.
- Security requires strict process separation, context isolation, no renderer Node access, validated IPC, and a narrow preload API.

If TypeScript is chosen, use a custom editor state model with controlled rendering; never make the DOM the authoritative document. Put persistence and file operations in the Electron main process or a dedicated worker process. Use generated runtime validators for every IPC contract.

### 5.3 Tauri or a browser/PWA

Tauri can reduce bundle size, but it introduces Rust plus TypeScript and relies on different system webviews across platforms. That combination increases validation cost for precisely the complex text behaviors that matter most.

A browser/PWA should not be the primary target for full parity. Sandboxed filesystem access, offline project packages, large imports, local integrations, fonts, keyboards, and external processes all become harder. A web client could be added later against a shared application protocol.

### 5.4 Required technology spike

Before making the final choice, build the same prototype in C#/Avalonia and TypeScript/Electron. The prototype must not be a generic form. It must demonstrate:

- A 100,000-record synthetic project with instant browse, filter, and record switching.
- Mixed LTR/RTL text and at least Arabic, Devanagari, Latin with combining marks, and an East Asian IME.
- Per-run writing systems and fonts in one field.
- Grapheme-safe selection, arrow movement, deletion, copy/paste, undo/redo, and IME cancellation.
- Virtualized browse and detail views.
- Import of a representative `.fwdata` subset and deterministic re-export.
- Automated UI tests on Windows, macOS, Ubuntu/X11, and Ubuntu/Wayland.
- Accessibility inspection and screen-reader smoke tests.
- Signed/packageable application artifacts on all three platforms.

Use a written scorecard. If neither stack passes the text criteria, stop and solve the editor architecture before building product screens.

## 6. Compatibility strategy

### 6.1 Define levels instead of claiming “compatible”

For each feature and format, track one of these levels:

1. **Read:** accepted without crashing and reported accurately.
2. **Represent:** all meaningful data can exist in the new model.
3. **Edit:** data can be changed with equivalent validation and side effects.
4. **Write:** export is accepted by the reference application.
5. **Round trip:** import/export preserves supported semantics.
6. **Workflow parity:** users can complete the same end-to-end task.

A public compatibility page should be generated from the same machine-readable matrix used by tests.

### 6.2 Version policy

- Select a bounded initial source range, for example FieldWorks 9.x/current model `7000072`, after validating actual user demand.
- Import older projects through explicit migration stages, never heuristic mutation.
- Never silently open a model version newer than the application understands.
- Preserve an untouched source copy and produce an import manifest with hashes.
- Make exports reproducible and identify the target model/version in metadata.

### 6.3 Differential and metamorphic tests

For every supported format:

- Parse, validate, serialize, reload, and compare semantic graphs.
- Randomize safe object order where the format declares order irrelevant.
- Test unknown elements, dangling references, duplicate IDs, corrupt archives, missing media, path traversal, zip bombs, and interrupted writes.
- Compare sorts against ICU reference results for configured collations.
- Run generated Unicode and bidi cases, not only English fixtures.
- Validate exported projects by opening them in an isolated copy of supported FieldWorks versions when licensing and automation allow.

### 6.4 Golden corpus

Build a consented, anonymized project corpus covering:

- Tiny, medium, large, and pathological object counts.
- Multiple model versions and migrations.
- RTL, complex scripts, combining marks, audio writing systems, and mixed-run strings.
- Custom fields and user-created lists.
- Lexicon-only, text-heavy, parser-heavy, notebook-heavy, and publication-heavy projects.
- Linked pictures, audio, video, missing files, non-ASCII filenames, and long paths.
- Real dictionary configurations, reversals, interlinear exports, and collaboration conflicts.

No release should ship based only on synthetic fixtures.

## 7. Point-by-point implementation plan

Each phase has a deliverable and an exit gate. Phases may overlap only after their boundary contracts are stable.

### Phase 0 — Product definition and compatibility inventory (6–10 weeks)

1. Interview lexicographers, linguists, support staff, trainers, and integration maintainers.
2. Inventory every visible tool, command, dialog, import/export option, project artifact, and supported integration.
3. Rank workflows as release-critical, important, specialist, legacy-only, or intentionally retired.
4. Select the initial supported FieldWorks versions and operating-system baselines.
5. Define performance budgets using real projects.
6. Establish the clean-reimplementation and licensing process.
7. Create the compatibility matrix and golden-corpus governance.
8. Write product principles: offline-first, never lose data, multilingual correctness, transparent transformations, accessible by default.

**Exit gate:** stakeholders sign off on a bounded definition of essential parity and the first two release slices.

### Phase 1 — Technology and text prototype (8–12 weeks)

1. Implement the C#/Avalonia and TypeScript/Electron spikes described above.
2. Test all three platforms, including X11 and Wayland on Linux.
3. Benchmark startup, memory, browse/filter latency, large XML import, and save.
4. Exercise IMEs, RTL, grapheme navigation, clipboard, accessibility, and font fallback with native speakers or qualified testers.
5. Record the choice in an architecture decision record.

**Exit gate:** one stack meets agreed text, accessibility, performance, and packaging thresholds.

### Phase 2 — Repository, quality, and delivery foundation (6–10 weeks)

1. Establish module dependency rules and architecture tests.
2. Add formatting, analyzers, warnings-as-errors, API compatibility checks, and documentation linting.
3. Configure unit, property, integration, UI, migration, and cross-platform test lanes.
4. Produce unsigned development packages for all platforms on every main-branch build.
5. Add structured logging, crash reports with opt-in privacy controls, and local diagnostic bundles.
6. Establish threat modeling, dependency scanning, secret scanning, and release signing.
7. Create ADR, compatibility, file-format, extension, and contributor documentation templates.

**Exit gate:** a trivial vertical slice ships reproducibly on all target platforms.

### Phase 3 — Domain kernel and transactional storage (4–6 months)

1. Implement stable IDs, ownership, references, ordered collections, multilingual values, rich strings, and custom-field definitions.
2. Implement command transactions, validation, undo/redo, and domain events.
3. Implement SQLite schema migrations, project locking, WAL recovery, backups, and integrity verification.
4. Build read models and indexes for browse, search, sort, and concordance.
5. Add deterministic serialization contracts and property-based invariant tests.
6. Implement project creation and a minimal project package.

**Exit gate:** a large synthetic project survives randomized create/edit/delete/undo/save/reopen operations with invariant checks and crash injection.

### Phase 4 — Writing-system platform (4–6 months, overlaps Phase 3)

1. Implement BCP-47 and LDML import/export with explicit supported subsets.
2. Implement project writing-system roles, defaults, and per-field alternatives.
3. Implement ICU-backed collation, normalization, segmentation, and character properties.
4. Implement rich-text runs, bidi/grapheme editing, font fallback, and writing-system-aware clipboard formats.
5. Implement platform keyboard/input-method adapters and spell-check contracts.
6. Add a writing-system editor and diagnostic preview.

**Exit gate:** the multilingual test matrix passes on all supported operating systems with no known data-loss issue.

### Phase 5 — FieldWorks project import and backup compatibility (4–8 months)

1. Write a streaming `.fwdata` reader that first records unknown classes/properties rather than dropping them.
2. Implement the selected LCModel classes in dependency order.
3. Resolve ownership and references in validated stages with actionable diagnostics.
4. Implement supported model migrations as independently testable transformations.
5. Import writing-system stores, configuration settings, supporting files, and linked media.
6. Read `.fwbackup` safely with archive limits and path-traversal protection.
7. Implement semantic export and compare normalized graphs.
8. Publish a per-version compatibility report.

**Exit gate:** the golden corpus imports without unreported loss; exported supported projects open in the reference FieldWorks versions and pass semantic comparison.

### Phase 6 — Lists and lexicon MVP (6–9 months)

1. Implement the Lists area and generic possibility-list editor first; many later workflows depend on it.
2. Implement lexicon browse/detail editing, entries, senses, forms, grammatical information, examples, notes, media, and custom fields.
3. Add semantic domains, lexical relations, variants, complex forms, and reversals.
4. Add configurable columns, search, filter, sort, record navigation, merge, and safe delete.
5. Add rapid data entry and bulk edit with preview and a single undo transaction.
6. Implement LIFT and SFM/MDF import/export.
7. Implement backup/restore and user-facing project integrity tools.

**Exit gate:** pilot users can create and maintain a real multilingual dictionary without returning to FieldWorks for ordinary lexicon work.

### Phase 7 — Dictionary configuration and publishing (5–8 months)

1. Define the typed publication configuration model and legacy configuration importer.
2. Implement nested field selection, ordering, labels, writing systems, grouping, numbering, and styles.
3. Implement dictionary, reversal, and classified-dictionary previews.
4. Produce accessible HTML/XHTML and print-quality PDF through a reproducible renderer.
5. Add DOCX/ODT or a well-documented downstream workflow based on user priority.
6. Add publication regression tests at semantic-tree and rendered-layout levels.

**Exit gate:** selected real dictionaries can be regenerated with accepted content and layout fidelity.

### Phase 8 — Text corpus and interlinear analysis (9–15 months)

1. Implement text metadata, paragraph editing, segmentation, tokenization, and punctuation models.
2. Implement wordforms, analyses, glosses, morpheme bundles, and links to lexical entries/senses.
3. Implement analysis suggestion/reuse and controlled propagation of changes.
4. Implement configurable interlinear lines, analysis/gloss workflows, and print view.
5. Implement concordances, filters, corpus statistics, and occurrence navigation.
6. Implement FlexText and prioritized interlinear exports.
7. Implement discourse charts after core interlinear editing is stable.
8. Add re-tokenization previews and strong undo/recovery because tokenization changes can affect many objects.

**Exit gate:** pilot linguists can import, analyze, gloss, search, and export representative corpora with accepted correctness and speed.

### Phase 9 — Grammar, phonology, and morphology (6–12 months)

1. Implement category, feature, phoneme, natural-class, environment, and rule editors.
2. Implement grammar-sketch generation from an explicit intermediate model.
3. Define a parser service protocol independent of any specific engine.
4. Integrate HermitCrab or another approved engine as an out-of-process adapter, subject to licensing and platform validation.
5. Decide whether XAmple compatibility is essential; isolate it if retained.
6. Implement Try a Word, trace, status, and parser-result lifecycle based on actual user priorities.

**Exit gate:** agreed grammar workflows and at least one production parser path work on all platforms.

### Phase 10 — Notebook (3–5 months)

1. Implement notebook record types, hierarchical records, dates, people, locations, restrictions, structured text, and media.
2. Link records to texts and other domain objects.
3. Implement browse, document, filter, sort, custom fields, and export.
4. Validate cultural-data privacy and redaction workflows.

**Exit gate:** representative notebook projects round-trip and daily notebook workflows are complete.

### Phase 11 — Collaboration (6–12 months)

1. Decide between exact FLEx Bridge compatibility and a new protocol after measuring demand.
2. Define an append-only local operation log with actor, object, field, base revision, and transaction identity.
3. Implement three-way semantic merge for scalar, multilingual, rich-text, ordered, owning, and reference properties.
4. Specify deletes-versus-edits, duplicate logical records, list changes, configuration, writing systems, and linked-media conflicts.
5. Build a comprehensible conflict UI and immutable merge report.
6. Add encrypted transports, authentication, retry, resumability, and offline queues.
7. Fuzz merges and run multi-client convergence tests.

**Exit gate:** concurrent randomized edits converge without silent loss, and pilot teams can diagnose every surfaced conflict.

### Phase 12 — Integrations and automation (ongoing, prioritized)

1. Paratext lexicon/scripture exchange.
2. Web publishing targets and Pathway-equivalent workflows.
3. Encoding conversion and legacy-import assistance.
4. FLExTools-compatible concepts through the new language-neutral API, not binary compatibility unless explicitly required.
5. Media metadata and processing.
6. Extension SDKs, sample plugins, version negotiation, permissions, and compatibility tests.

**Exit gate:** each integration has a named owner, supported versions, contract tests, failure isolation, and deprecation policy.

### Phase 13 — Localization, accessibility, documentation, and training (starts early; completes before 1.0)

1. Externalize all user-facing text from the beginning.
2. Support runtime locale selection, plural rules, bidi UI, and translation updates.
3. Meet WCAG 2.2 AA where applicable and test keyboard-only operation and major screen readers.
4. Write task-oriented user documentation and an embedded searchable help system.
5. Maintain architecture, domain glossary, file-format, troubleshooting, and extension documentation.
6. Produce migration guides and explain intentional differences from FieldWorks.

**Exit gate:** documentation and accessibility checks are release criteria, not post-release tasks.

### Phase 14 — Production hardening and 1.0 release (6–9 months)

1. Run long-duration, low-disk, interrupted-I/O, corrupt-input, and large-project tests.
2. Complete privacy, security, accessibility, localization, and legal reviews.
3. Validate install, update, rollback, signing, notarization, and uninstall on supported OS versions.
4. Conduct staged migrations with support staff and real projects.
5. Publish a support lifecycle, backup guidance, compatibility matrix, known limitations, and recovery procedures.
6. Keep the source project untouched and make rollback possible throughout the pilot.

**Exit gate:** zero unresolved known data-loss defects, recovery drills pass, and pilot organizations approve migration.

## 8. Suggested release slices

### Release A — Read-only explorer

- Open copies of supported `.fwdata` and `.fwbackup` projects.
- Inspect writing systems, lists, lexicon, texts, and object diagnostics.
- Search and export reports without mutation.

This validates parsing and provides immediate utility without risking user data.

### Release B — Lexicography preview

- New native projects, writing systems, lists, lexicon editing, search/filter/sort, undo, backup, LIFT, and SFM.
- No promise of FieldWorks round-trip editing until the export gate passes.

### Release C — Lexicography production

- Proven FieldWorks import/export, dictionary/reversal configuration, publication, bulk edit, and pilot support.

### Release D — Linguistic analysis

- Text corpus, interlinear editing, concordance, FlexText, and selected morphology/parser workflows.

### Release E — Complete fieldwork suite

- Grammar, notebook, collaboration, prioritized integrations, mature extensions, migration tooling, and full production support.

## 9. Testing and quality strategy

### 9.1 Test pyramid

- Domain unit tests for every invariant and calculated behavior.
- Property-based tests for object graphs, Unicode strings, serializers, migrations, undo, and merge.
- Contract tests for databases, formats, platform services, and integrations.
- Golden-corpus migration and round-trip tests.
- Headless component tests for most UI behavior.
- Small, high-value end-to-end suites on every supported OS/display server.
- Manual linguistic and accessibility sessions for behaviors automation cannot judge.

### 9.2 Non-negotiable performance budgets

Phase 0 should set exact values. Suggested starting targets on reference hardware are:

- Warm project open under 5 seconds for a representative medium project.
- Browse/filter feedback under 100 ms for indexed operations.
- Record switch under 150 ms at the 95th percentile.
- Typing latency under 16 ms for ordinary edits and under 50 ms during expensive analysis invalidation.
- Background save without blocking text input.
- Crash-safe commit with no partially written project package.

### 9.3 Data safety rules

- Never mutate the sole copy of an imported project.
- Every migration is forward-only internally but starts from an automatic recoverable snapshot.
- Every bulk operation previews its scope and is one undoable transaction where feasible.
- Every destructive import/export reports omissions and warnings before replacing a destination.
- Unknown data is preserved or explicitly rejected; it is never silently discarded.
- Recovery and restore are continuously tested, not merely documented.

## 10. Team and governance

A balanced full-parity team should include:

- Product lead with field linguistics/lexicography experience.
- Technical lead/architect.
- Two to four domain and persistence engineers.
- Two to three desktop/UI engineers.
- One interoperability/data-migration engineer.
- One test/quality engineer with automation depth.
- Shared UX research/design, accessibility, documentation, localization, release engineering, security, and community support.

At least one team member must own multilingual text correctness, and at least one must own compatibility/migrations. These cannot be occasional side responsibilities.

Use public architecture decisions, a domain glossary, format specifications, and generated compatibility reports. Require two-person review for migrations, serializers, merge logic, and destructive operations.

## 11. Principal risks and mitigations

| Risk | Impact | Mitigation |
|---|---:|---|
| Scope is defined as “everything users might use” | Critical | Signed compatibility matrix and staged releases |
| Silent loss during `.fwdata` conversion | Critical | Unknown-data accounting, semantic diff, golden corpus, source-copy preservation |
| Complex-script editor defects | Critical | Hard text spike first, native-speaker testing, Unicode/property tests, three-platform matrix |
| Recreating LCModel behavior incompletely | Critical | Specify invariants, vertical slices, differential behavior tests, no schema-only shortcut |
| Collaboration conflict loss | Critical | Append-only audit log, formal merge rules, convergence/fuzz tests, delayed rollout |
| Publication output is “almost” correct | High | Renderer-neutral document model and real-dictionary regression corpus |
| External integration churn | High | Versioned out-of-process adapters and explicit support policy |
| Electron memory/security issues if TypeScript is chosen | High | Process isolation, strict IPC, virtualization, performance budgets, security review |
| Avalonia platform text/accessibility gaps | High | Prototype gate and platform-specific adapters; do not commit before evidence |
| Linux distribution/IME variance | High | Supported distro/display matrix, packaged runtimes, X11 and Wayland CI/manual tests |
| Clean-room intent drifts into copied implementation | High | Provenance records, review checklist, legal review, independently written specifications/tests |
| Project loses maintainability over time | High | Module boundaries, architecture tests, ADRs, API policy, documentation as release criteria |
| Understaffed migration/support effort | High | Dedicated compatibility owner, staged pilots, diagnostic bundles, rollback support |

## 12. Decisions required before implementation

1. Which FieldWorks versions and model versions must be supported initially?
2. Is opening/exporting `.fwdata` enough, or must the new application share the same project alternately with FieldWorks?
3. Which five workflows define the first useful release for actual users?
4. Is exact FLEx Bridge interoperability required, or is equivalent collaboration acceptable?
5. Which integrations are contractual: Paratext, Webonary, Pathway, FLExTools, Dictionary App Builder, or others?
6. Must existing dictionary configurations reproduce visual output exactly, or is semantic equivalence with migration assistance acceptable?
7. Which parser engines are essential?
8. What is the project’s license, governance model, and relationship to SIL/upstream maintainers?
9. Can representative real-world projects be obtained under suitable test/data agreements?
10. What team and multi-year maintenance budget is available?

## 13. Recommended immediate next steps

1. Contact FieldWorks and liblcm maintainers to validate assumptions, avoid duplicating undocumented work, and discuss format compatibility.
2. Create `flex/COMPATIBILITY.md` as a machine-linked feature/format matrix.
3. Recruit five to ten representative users and collect workflow narratives plus consented test projects.
4. Specify the `.fwdata` subset and rich-string behavior needed for the first lexicon slice.
5. Run the C#/Avalonia versus TypeScript/Electron spike.
6. Build a read-only `.fwdata` inspector as the first end-to-end artifact.
7. Re-estimate after the inspector reports actual unsupported classes, fields, writing systems, configurations, and media across the corpus.

## 14. Reference material

Primary sources used for this assessment:

- [FieldWorks source repository](https://github.com/sillsdev/FieldWorks)
- [FieldWorks developer README](https://github.com/sillsdev/FieldWorks/blob/main/ReadMe.md)
- [FieldWorks product features](https://software.sil.org/fieldworks/features/)
- [FieldWorks technical documents](https://software.sil.org/fieldworks/help/technical-documents/)
- [FieldWorks developer resources](https://software.sil.org/fieldworks/developer/)
- [Using Send/Receive](https://software.sil.org/fieldworks/help/using-sendreceive/)
- [liblcm source repository](https://github.com/sillsdev/liblcm)
- [LCModel master model](https://github.com/sillsdev/liblcm/blob/master/src/SIL.LCModel/MasterLCModel.xml)
- [FLEx Bridge source repository](https://github.com/sillsdev/flexbridge)

Important upstream files inspected in the source snapshots include:

- `FieldWorks/CONTEXT.md`
- `FieldWorks/Docs/migration/avalonia-migration-overview.md`
- `FieldWorks/Docs/architecture/dependencies.md`
- `FieldWorks/Docs/architecture/data-migrations.md`
- `FieldWorks/Directory.Packages.props`
- `FieldWorks/DistFiles/Language Explorer/Configuration/**`
- `FieldWorks/TestLangProj/TestLangProj.fwdata`
- `liblcm/src/SIL.LCModel/MasterLCModel.xml`
- `liblcm/src/SIL.LCModel/Infrastructure/Impl/XMLBackendProvider.cs`
- `liblcm/src/SIL.LCModel/DomainServices/DataMigration/**`
- `liblcm/src/SIL.LCModel/DomainServices/BackupRestore/**`

## Conclusion

The reimplementation should proceed if the goal is a maintained, cross-platform linguistic workbench and the project can support a staged multi-year effort. The strongest route is not to imitate the current class structure. It is to preserve the data and workflows users depend on while replacing the implementation with a smaller modular core, explicit compatibility adapters, a modern UI, and unusually strong migration and multilingual-text tests.

The first proof point is not a redesigned lexicon screen. It is a trustworthy read-only importer and a text editor that handles the project’s hardest scripts correctly on Windows, macOS, and Linux. If those foundations pass, the rest is large but tractable. If they do not, expanding feature scope would only hide the core risk.
