"""Semantic comparison of EAF files for round-trip tests (REIMPLEMENTATION.md §6.2).

Two files are "the same" when their canonical forms are equal. The canonical form
ignores what the writer is allowed to change: attribute order, indentation, DATE,
VERSION/FORMAT, the schema location, lastUsedAnnotationId, time slot ids (slots are
renamed by their position among the used slots), and unused time slots.
"""

from __future__ import annotations

from typing import Any

from lxml import etree

IGNORED_ROOT_ATTRS = {
    "DATE",
    "VERSION",
    "FORMAT",
    "{http://www.w3.org/2001/XMLSchema-instance}noNamespaceSchemaLocation",
}

Canonical = tuple[Any, ...]


def canonical(data: bytes, *, skip: frozenset[str] = frozenset()) -> Canonical:
    root = etree.fromstring(data)
    used: set[str] = set()
    for el in root.iter("ALIGNABLE_ANNOTATION"):
        used.update({el.get("TIME_SLOT_REF1", ""), el.get("TIME_SLOT_REF2", "")})
    slot_names: dict[str, str] = {}
    for el in root.iter("TIME_SLOT"):
        slot_id = el.get("TIME_SLOT_ID", "")
        if slot_id in used:
            slot_names[slot_id] = f"T{len(slot_names) + 1}"
    return _node(root, slot_names, skip, is_root=True)


def _node(el: Any, slots: dict[str, str], skip: frozenset[str], *, is_root: bool = False) -> Any:
    if not isinstance(el.tag, str):  # comment or processing instruction
        return ("#comment", (el.text or "").strip())
    attrs = {}
    for key, value in el.attrib.items():
        if is_root and key in IGNORED_ROOT_ATTRS:
            continue
        if key in ("TIME_SLOT_ID", "TIME_SLOT_REF1", "TIME_SLOT_REF2"):
            value = slots.get(value, f"?{value}")
        attrs[key] = value
    if el.tag == "PROPERTY" and el.get("NAME") == "lastUsedAnnotationId":
        return ("PROPERTY", (("NAME", "lastUsedAnnotationId"),), "*", ())
    children = []
    for child in el:
        if isinstance(child.tag, str) and child.tag in skip:
            continue
        if child.tag == "TIME_SLOT" and child.get("TIME_SLOT_ID") not in slots:
            continue
        children.append(_node(child, slots, skip))
    text = el.text or ""
    if len(el) > 0 and not text.strip():
        text = ""
    return (el.tag, tuple(sorted(attrs.items())), text, tuple(children))


def first_difference(a: Any, b: Any, path: str = "") -> str | None:
    """A readable pointer to the first difference between two canonical trees."""
    if a == b:
        return None
    if not (isinstance(a, tuple) and isinstance(b, tuple) and len(a) == 4 and len(b) == 4):
        return f"{path}: {a!r} != {b!r}"
    here = f"{path}/{a[0]}"
    if a[0] != b[0] or a[1] != b[1] or a[2] != b[2]:
        return f"{here}: {a[:3]!r} != {b[:3]!r}"
    for index, (x, y) in enumerate(zip(a[3], b[3], strict=False)):
        found = first_difference(x, y, f"{here}[{index}]")
        if found:
            return found
    return f"{here}: {len(a[3])} children != {len(b[3])}"
