import re
from pathlib import Path

from elan_ng.ui.menus import MENU_BAR, Item, Menu, iter_items

SPEC = Path(__file__).resolve().parents[1] / "REIMPLEMENTATION.md"
PHASES = {"M0", "M3", "M4", "M5", "v1", "P2"}


def test_top_level_menus_match_spec_section_5_2() -> None:
    names = [menu.text.replace("&", "") for menu in MENU_BAR]
    assert names == [
        "File",
        "Edit",
        "Annotation",
        "Tier",
        "Type",
        "Search",
        "View",
        "Options",
        "Window",
        "Help",
    ]
    spec = SPEC.read_text(encoding="utf-8")
    block = spec.split("### 5.2 Menus", 1)[1].split("### 5.3", 1)[0]
    top_level = re.findall(r"^([A-Z][a-z]+)$", block, flags=re.MULTILINE)
    assert top_level == names


def test_item_ids_are_unique() -> None:
    ids = [item.id for item in iter_items()]
    assert len(ids) == len(set(ids))


def test_every_item_has_a_known_phase() -> None:
    def phases(entries: tuple[object, ...]) -> list[str]:
        found: list[str] = []
        for entry in entries:
            if isinstance(entry, Item):
                found.append(entry.phase)
            elif isinstance(entry, Menu):
                if entry.phase:
                    found.append(entry.phase)
                found.extend(phases(entry.entries))
        return found

    assert set(phases(MENU_BAR)) <= PHASES


def test_shortcuts_are_unique() -> None:
    shortcuts = [item.shortcut for item in iter_items() if item.shortcut]
    assert len(shortcuts) == len(set(shortcuts))


def test_elan_default_shortcuts_from_spec_section_2_9() -> None:
    by_id = {item.id: item.shortcut for item in iter_items()}
    assert by_id["file.save"] == "Ctrl+S"
    assert by_id["file.save_as_template"] == "Ctrl+Shift+Alt+S"
    assert by_id["edit.undo"] == "Ctrl+Z"
    assert by_id["edit.redo"] == "Ctrl+Y"
    assert by_id["annotation.new_here"] == "Ctrl+Alt+N"
    assert by_id["annotation.delete"] == "Ctrl+Alt+D"
    assert by_id["tier.add"] == "Ctrl+T"
    assert by_id["search.find"] == "Ctrl+F"
