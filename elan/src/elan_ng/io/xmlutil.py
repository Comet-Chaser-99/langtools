"""Shared XML helpers for EAF-family files: residue capture and ELAN-style output."""

from __future__ import annotations

import copy
from collections.abc import Callable, Iterable, Mapping

from lxml import etree

from elan_ng.core.model import Residue

XSI = "http://www.w3.org/2001/XMLSchema-instance"
XML_DECLARATION = b'<?xml version="1.0" encoding="UTF-8"?>\n'

Element = etree._Element


def is_element(node: object) -> bool:
    return isinstance(node, etree._Element) and isinstance(node.tag, str)


def split_attrs(el: Element, known: Iterable[str]) -> tuple[dict[str, str], Residue]:
    """Known attributes as a dict; everything else goes into a Residue."""
    known_set = set(known)
    values: dict[str, str] = {}
    residue = Residue()
    for name, value in el.attrib.items():
        key = str(name)
        if key in known_set:
            values[key] = str(value)
        else:
            residue.attrs[key] = str(value)
    return values, residue


def walk_children(
    el: Element,
    residue: Residue,
    handlers: Mapping[str, Callable[[Element], object]],
) -> None:
    """Call the handler for each known child; keep unknown children and comments as residue.

    The anchor of a residue node is the number of known children before it, so the writer
    can put it back in the same place relative to the known content.
    """
    known_count = 0
    for child in el:
        handler = handlers.get(child.tag) if isinstance(child.tag, str) else None
        if handler is not None:
            handler(child)
            known_count += 1
        else:
            node = copy.deepcopy(child)
            node.tail = None
            residue.children.append((known_count, node))


def make(tag: str, attrs: dict[str, str | None], residue: Residue | None = None) -> Element:
    """Create an element with ELAN's attribute order: alphabetical, namespaced ones last."""
    merged: dict[str, str] = {k: v for k, v in attrs.items() if v is not None}
    if residue is not None:
        merged.update(residue.attrs)
    el = etree.Element(tag)
    for key in sorted(merged, key=lambda k: (k.startswith("{"), k)):
        el.set(key, merged[key])
    return el


def append_children(parent: Element, known: list[Element], residue: Residue) -> None:
    """Append known children, re-inserting residue nodes at their anchors."""
    pending = sorted(residue.children, key=lambda item: item[0])
    position = 0
    for index, child in enumerate(known):
        while position < len(pending) and pending[position][0] <= index:
            parent.append(copy.deepcopy(_as_element(pending[position][1])))
            position += 1
        parent.append(child)
    for _, node in pending[position:]:
        parent.append(copy.deepcopy(_as_element(node)))


def _as_element(node: object) -> Element:
    if not isinstance(node, etree._Element):
        raise TypeError(f"residue node is not an lxml element: {node!r}")
    return node


def text_element(
    tag: str,
    attrs: dict[str, str | None],
    text: str,
    residue: Residue | None = None,
    *,
    always_open: bool = False,
) -> Element:
    """An element with text content. Residue children keep their tails (mixed content)."""
    el = make(tag, attrs, residue)
    if text or always_open:
        el.text = text
    if residue is not None:
        for _, node in residue.children:
            el.append(copy.deepcopy(_as_element(node)))
    return el


def keep_text_residue(el: Element, residue: Residue) -> None:
    """For text-content elements: keep child nodes (comments etc.) with their tails."""
    for child in el:
        residue.children.append((0, copy.deepcopy(child)))


def serialize(root: Element, prolog: Iterable[object] = (), epilog: Iterable[object] = ()) -> bytes:
    """ELAN-style output: double-quoted UTF-8 declaration, 4-space indentation.

    ``prolog``/``epilog`` are comments or processing instructions outside the root element.
    """
    etree.indent(root, space="    ")
    parts = [XML_DECLARATION]
    for node in prolog:
        parts.append(_node_bytes(node) + b"\n")
    parts.append(etree.tostring(root, encoding="UTF-8", xml_declaration=False) + b"\n")
    for node in epilog:
        parts.append(_node_bytes(node) + b"\n")
    return b"".join(parts)


def _node_bytes(node: object) -> bytes:
    el = copy.deepcopy(_as_element(node))
    el.tail = None
    return etree.tostring(el, encoding="UTF-8", xml_declaration=False)


def parse(data: bytes) -> Element:
    parser = etree.XMLParser(remove_blank_text=False, resolve_entities=False, no_network=True)
    root: Element = etree.fromstring(data, parser)
    return root
