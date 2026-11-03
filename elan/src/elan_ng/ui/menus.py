"""The menu tree from REIMPLEMENTATION.md §5.2 with ELAN's default shortcuts from §2.9.

The tree is plain data so tests can compare it with the spec and later milestones can
enable items by attaching handlers to their ``id``. Shortcuts use Qt's portable notation:
"Ctrl" becomes Cmd on macOS, which matches ELAN for most menu shortcuts (see §2.9).
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Item:
    id: str
    text: str
    phase: str
    shortcut: str = ""


@dataclass(frozen=True)
class Separator:
    pass


@dataclass(frozen=True)
class Menu:
    text: str
    entries: tuple[Item | Separator | Menu, ...] = field(default_factory=tuple)
    phase: str = ""


SEP = Separator()

MENU_BAR: tuple[Menu, ...] = (
    Menu(
        "&File",
        (
            Item("file.new", "&New...", "M4", "Ctrl+N"),
            Item("file.open", "&Open...", "M4", "Ctrl+O"),
            Menu("Open &Recent", phase="M4"),
            Item("file.close", "&Close", "M4", "Ctrl+W"),
            SEP,
            Item("file.save", "&Save", "M4", "Ctrl+S"),
            Item("file.save_as", "Save &As...", "M4", "Ctrl+Shift+S"),
            Item("file.save_as_template", "Save as &Template...", "v1", "Ctrl+Shift+Alt+S"),
            Item("file.save_selection", "Save Selection as EAF...", "P2"),
            Item("file.merge", "Merge Transcriptions...", "P2"),
            SEP,
            Item("file.properties", "Properties...", "v1"),
            Menu("Multiple File Processing", phase="P2"),
            Menu("Export Multiple Files As", phase="P2"),
            SEP,
            Menu(
                "&Import",
                (
                    Item("import.textgrid", "Praat TextGrid...", "v1"),
                    Item("import.tabtext", "CSV / Tab-delimited Text...", "v1"),
                    Item("import.subtitles", "Subtitles (SRT/WebVTT)...", "v1"),
                    SEP,
                    Item("import.chat", "CHAT...", "P2"),
                    Item("import.toolbox", "Toolbox...", "P2"),
                    Item("import.flex", "FLEx...", "P2"),
                    Item("import.transcriber", "Transcriber...", "P2"),
                ),
            ),
            Menu(
                "&Export As",
                (
                    Item("export.tabtext", "Tab-delimited Text...", "v1"),
                    Item("export.transcript", "Traditional Transcript...", "v1"),
                    Item("export.interlinear", "Interlinear Text...", "v1"),
                    Item("export.textgrid", "Praat TextGrid...", "v1"),
                    Item("export.subtitles", "Subtitles Text (SRT/WebVTT)...", "v1"),
                    SEP,
                    Item("export.chat", "CHAT...", "P2"),
                    Item("export.toolbox", "Toolbox...", "P2"),
                    Item("export.flex", "FLEx...", "P2"),
                ),
            ),
            SEP,
            Item("file.exit", "E&xit", "M0", "Ctrl+Q"),
        ),
    ),
    Menu(
        "&Edit",
        (
            Item("edit.undo", "&Undo", "M4", "Ctrl+Z"),
            Item("edit.redo", "&Redo", "M4", "Ctrl+Y"),
            SEP,
            Item("edit.copy_annotation", "Copy Annotation", "M4", "Ctrl+C"),
            Item("edit.copy_group", "Copy Annotation Group", "v1", "Ctrl+Alt+C"),
            Item("edit.duplicate", "Duplicate Annotation", "v1", "Ctrl+D"),
            Item("edit.paste", "Paste Annotation", "v1", "Ctrl+V"),
            Item("edit.paste_group", "Paste Annotation Group", "v1", "Ctrl+Alt+V"),
            Item("edit.paste_here", "Paste Annotation Here", "v1", "Ctrl+Shift+V"),
            Item("edit.paste_group_here", "Paste Annotation Group Here", "v1", "Ctrl+Alt+Shift+V"),
            Item("edit.copy_time", "Copy Current Time", "v1", "Ctrl+Alt+G"),
            SEP,
            Item("edit.linked_files", "Edit Linked Files...", "M3", "Ctrl+Alt+L"),
            SEP,
            Menu(
                "&Preferences",
                (
                    Item("prefs.edit", "Edit Preferences...", "M4"),
                    Item("prefs.shortcuts", "Shortcuts...", "v1"),
                    Item("prefs.import_export", "Import / Export Preferences...", "v1"),
                ),
            ),
        ),
    ),
    Menu(
        "&Annotation",
        (
            Item("annotation.new_here", "New Annotation Here", "M4", "Ctrl+Alt+N"),
            Item("annotation.new_before", "New Annotation Before", "M4"),
            Item("annotation.new_after", "New Annotation After", "M4", "Ctrl+Shift+N"),
            Item(
                "annotation.new_from_times",
                "New Annotation from Begin-End Time...",
                "v1",
                "Ctrl+Alt+Shift+N",
            ),
            SEP,
            Item("annotation.modify", "Modify Annotation", "M4", "Ctrl+Alt+M"),
            Item("annotation.modify_time", "Modify Annotation Time...", "v1"),
            Item("annotation.clear_value", "Remove Annotation Value", "M4", "Ctrl+Del"),
            Item("annotation.delete", "Delete Annotation", "M4", "Ctrl+Alt+D"),
            SEP,
            Item("annotation.split", "Split Annotation", "v1"),
            Item("annotation.merge_next", "Merge with Next", "v1"),
            Item("annotation.merge_previous", "Merge with Previous", "v1"),
            Menu("Shift Annotations", phase="v1"),
            Item("annotation.delete_in_selection", "Delete Annotations in Selection", "v1"),
            SEP,
            Item("annotation.from_overlaps", "Create Annotations from Overlaps...", "P2"),
            Item("annotation.from_gaps", "Create Annotations from Gaps...", "P2"),
            Item("annotation.from_subtraction", "Create Annotations from Subtraction...", "P2"),
            Item("annotation.label_number", "Label and Number Annotations...", "P2"),
        ),
    ),
    Menu(
        "&Tier",
        (
            Item("tier.add", "Add New Tier...", "M4", "Ctrl+T"),
            Item("tier.change", "Change Tier Attributes...", "M4"),
            Item("tier.delete", "Delete Tier...", "M4", "Ctrl+Alt+T"),
            SEP,
            Item("tier.add_participant", "Add Participant...", "v1"),
            Item("tier.import", "Import Tiers...", "v1"),
            Item("tier.reparent", "Change Parent of Tier...", "v1"),
            Item("tier.copy", "Copy Tier...", "v1"),
            Item("tier.merge", "Merge Tiers...", "v1"),
            Item("tier.tokenize", "Tokenize Tier...", "v1"),
        ),
    ),
    Menu(
        "T&ype",
        (
            Item("type.add", "Add New Tier Type...", "M4", "Ctrl+Shift+T"),
            Item("type.change", "Change Tier Type...", "M4"),
            Item("type.delete", "Delete Tier Type...", "M4"),
            Item("type.import", "Import Tier Types...", "v1"),
            SEP,
            Item("type.edit_cv", "Edit Controlled Vocabularies...", "M4", "Ctrl+Shift+C"),
            Item("type.edit_languages", "Edit Languages...", "v1"),
            Item("type.edit_lexicon_links", "Edit Lexicon Service Links...", "P2"),
        ),
    ),
    Menu(
        "&Search",
        (
            Item("search.find", "Find...", "M4", "Ctrl+F"),
            Item("search.replace", "Find and Replace...", "v1"),
            Item("search.goto", "Go To...", "M3", "Ctrl+G"),
            SEP,
            Item("search.multiple", "Search Multiple EAF...", "P2", "Ctrl+Shift+F"),
            Item("search.structured", "Structured Search Multiple EAF...", "P2"),
            Item("search.replace_multiple", "Find and Replace in Multiple Files...", "P2"),
        ),
    ),
    Menu(
        "&View",
        (
            Item("view.media", "Media Player", "M3"),
            Item("view.waveform", "Waveform", "M3"),
            Item("view.timeline", "Timeline Viewer", "M3"),
            Item("view.interlinear", "Interlinear Viewer", "v1"),
            Item("view.grid", "Grid Viewer", "M4"),
            Item("view.text", "Text Viewer", "v1"),
            Item("view.subtitles", "Subtitle Viewer", "v1"),
            Item("view.density", "Annotation Density Viewer", "v1"),
            Item("view.spectrogram", "Spectrogram", "P2"),
            SEP,
            Item("view.lexicon", "Lexicon", "P2"),
            Item("view.comments", "Comments", "P2"),
            Item("view.recognizers", "Recognizers", "P2"),
            SEP,
            Menu("Font Size", phase="M3"),
            Menu("Zoom", phase="M3"),
        ),
    ),
    Menu(
        "&Options",
        (
            Item("mode.annotation", "Annotation Mode", "M4"),
            Item("mode.synchronization", "Synchronization Mode", "v1"),
            Item("mode.transcription", "Transcription Mode", "v1"),
            Item("mode.segmentation", "Segmentation Mode", "v1"),
            Item("mode.interlinearization", "Interlinearization Mode", "P2"),
            SEP,
            Menu(
                "Time Propagation Mode",
                (
                    Item("propagation.normal", "Normal", "M5"),
                    Item("propagation.bulldozer", "Bulldozer", "v1"),
                    Item("propagation.shift", "Shift", "v1"),
                ),
            ),
            Item("options.selection_mode", "Selection Mode", "M3", "Ctrl+K"),
            Item("options.loop_mode", "Loop Mode", "M3", "Ctrl+L"),
            SEP,
            Menu("Frame Length", phase="M3"),
            Menu("Playback Rate", phase="M3"),
            Menu("Volume", phase="M3"),
            Menu("Media Player", phase="v1"),
        ),
    ),
    Menu(
        "&Window",
        (
            Item("window.previous", "Previous Window", "M4"),
            Item("window.next", "Next Window", "M4"),
        ),
    ),
    Menu(
        "&Help",
        (
            Item("help.contents", "Contents", "v1"),
            Item("help.shortcuts", "Shortcuts", "M4"),
            SEP,
            Item("help.about", "&About elan-ng", "M0"),
        ),
    ),
)


def iter_items(entries: tuple[Item | Separator | Menu, ...] = MENU_BAR) -> list[Item]:
    """All items in the tree, depth first."""
    found: list[Item] = []
    for entry in entries:
        if isinstance(entry, Item):
            found.append(entry)
        elif isinstance(entry, Menu):
            found.extend(iter_items(entry.entries))
    return found
