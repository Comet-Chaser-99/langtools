"""ELAN per-document preferences, ``.pfsx`` (REIMPLEMENTATION.md §3.3).

The file is kept as an XML tree, so every key elan-ng does not know survives a save
untouched. :meth:`Preferences.get` and :meth:`Preferences.set` convert between the typed
value elements (String, Boolean, Int, Long, Float, Double, Object, prefList, prefGroup)
and Python values.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from lxml import etree

from elan_ng.io.xmlutil import XSI, Element, parse, serialize

PfsxValue = str | bool | int | float | list[Any] | dict[str, Any] | None

_SCALARS = {"String", "Boolean", "Int", "Long", "Float", "Double", "Object"}


class Preferences:
    def __init__(self, root: Element | None = None) -> None:
        if root is None:
            root = etree.Element("preferences", nsmap={"xsi": XSI})
            root.set("version", "1.1")
            root.set(
                f"{{{XSI}}}noNamespaceSchemaLocation", "http://www.mpi.nl/tools/elan/Prefs_v1.1.xsd"
            )
        self.root = root

    @classmethod
    def read(cls, path: str | Path) -> Preferences:
        return cls.parse(Path(path).read_bytes())

    @classmethod
    def parse(cls, data: bytes) -> Preferences:
        root = parse(data)
        if root.tag != "preferences":
            raise ValueError(f"root element is {root.tag!r}, expected 'preferences'")
        return cls(root)

    def to_bytes(self) -> bytes:
        return serialize(self.root)

    def keys(self) -> list[str]:
        return [str(el.get("key")) for el in self._entries()]

    def get(self, key: str) -> PfsxValue:
        el = self._find(key)
        return None if el is None else _decode(el)

    def set(self, key: str, value: PfsxValue) -> None:
        new = _encode(key, value)
        old = self._find(key)
        if old is None:
            self.root.append(new)
        else:
            old.getparent().replace(old, new)  # type: ignore[union-attr]

    def _entries(self) -> list[Element]:
        return [el for el in self.root if isinstance(el.tag, str) and el.get("key") is not None]

    def _find(self, key: str) -> Element | None:
        return next((el for el in self._entries() if el.get("key") == key), None)


def _decode_scalar(el: Element) -> PfsxValue:
    text = el.text or ""
    match el.tag:
        case "Boolean":
            return text.strip() == "true"
        case "Int" | "Long":
            return int(text)
        case "Float" | "Double":
            return float(text)
        case _:
            return text


def _decode(el: Element) -> PfsxValue:
    if el.tag == "prefGroup":
        return {str(child.get("key")): _decode(child) for child in el if isinstance(child.tag, str)}
    values = [child for child in el if isinstance(child.tag, str) and child.tag in _SCALARS]
    if el.tag == "prefList":
        return [_decode_scalar(child) for child in values]
    return _decode_scalar(values[0]) if values else None


def _scalar(value: PfsxValue) -> Element:
    if isinstance(value, bool):
        el = etree.Element("Boolean")
        el.text = "true" if value else "false"
    elif isinstance(value, int):
        el = etree.Element("Int")
        el.text = str(value)
    elif isinstance(value, float):
        el = etree.Element("Float")
        el.text = repr(value)
    else:
        el = etree.Element("String")
        el.text = "" if value is None else str(value)
    return el


def _encode(key: str, value: PfsxValue) -> Element:
    if isinstance(value, dict):
        el = etree.Element("prefGroup", key=key)
        for child_key, child_value in value.items():
            el.append(_encode(child_key, child_value))
    elif isinstance(value, list):
        el = etree.Element("prefList", key=key)
        for item in value:
            el.append(_scalar(item))
    else:
        el = etree.Element("pref", key=key)
        el.append(_scalar(value))
    return el
