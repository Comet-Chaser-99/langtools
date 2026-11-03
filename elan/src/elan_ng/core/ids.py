"""Annotation id allocation (REIMPLEMENTATION.md §3.1.3).

Existing ids are kept. New ids are ``a<n>`` above ``lastUsedAnnotationId`` (or above the
highest ``a<n>`` in the document when the property is missing or too low), and an id is
never handed out twice in a session, even if the annotation that had it was deleted.
"""

from __future__ import annotations

import re

from elan_ng.core.model import Document

_NUMBERED = re.compile(r"a(\d+)")
LAST_USED_PROPERTY = "lastUsedAnnotationId"


def highest_numbered_id(doc: Document) -> int:
    highest = 0
    for annotation in doc.annotations():
        match = _NUMBERED.fullmatch(annotation.id)
        if match:
            highest = max(highest, int(match.group(1)))
    return highest


def last_used_annotation_id(doc: Document) -> int:
    stored = doc.header.get_property(LAST_USED_PROPERTY)
    stored_value = int(stored) if stored is not None and stored.isdigit() else 0
    return max(stored_value, highest_numbered_id(doc))


class IdAllocator:
    def __init__(self, doc: Document) -> None:
        self._doc = doc
        self._last = last_used_annotation_id(doc)
        self._taken = {a.id for a in doc.annotations()}

    def next_id(self) -> str:
        while True:
            self._last += 1
            candidate = f"a{self._last}"
            if candidate not in self._taken:
                self._taken.add(candidate)
                self._doc.header.set_property(LAST_USED_PROPERTY, str(self._last))
                return candidate
