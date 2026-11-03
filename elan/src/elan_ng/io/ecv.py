"""Read external controlled vocabulary files, ``.ecv`` (REIMPLEMENTATION.md §3.4).

An .ecv file has the root element CV_RESOURCE and the same CONTROLLED_VOCABULARY, LANGUAGE
and EXTERNAL_REF elements as an EAF file, so it reuses the EAF reader's element parsers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from elan_ng.core.model import ControlledVocabulary, ExternalRef, Language, Residue
from elan_ng.io.eaf_reader import EAFError, _Reader
from elan_ng.io.xmlutil import parse, split_attrs, walk_children


@dataclass
class VocabularyResource:
    author: str | None = None
    date: str | None = None
    version: str | None = None
    languages: list[Language] = field(default_factory=list)
    vocabularies: list[ControlledVocabulary] = field(default_factory=list)
    external_refs: list[ExternalRef] = field(default_factory=list)
    residue: Residue = field(default_factory=Residue)


def read_ecv(path: str | Path) -> VocabularyResource:
    return parse_ecv(Path(path).read_bytes())


def parse_ecv(data: bytes) -> VocabularyResource:
    try:
        root = parse(data)
    except Exception as exc:
        raise EAFError(f"not well-formed XML: {exc}") from exc
    if root.tag != "CV_RESOURCE":
        raise EAFError(f"root element is {root.tag!r}, expected 'CV_RESOURCE'")
    values, residue = split_attrs(root, ["AUTHOR", "DATE", "VERSION"])
    resource = VocabularyResource(
        author=values.get("AUTHOR"),
        date=values.get("DATE"),
        version=values.get("VERSION"),
        residue=residue,
    )
    reader = _Reader()
    walk_children(
        root,
        residue,
        {
            "LANGUAGE": lambda el: resource.languages.append(reader.language(el)),
            "CONTROLLED_VOCABULARY": lambda el: resource.vocabularies.append(reader.vocabulary(el)),
            "EXTERNAL_REF": lambda el: resource.external_refs.append(reader.external_ref(el)),
        },
    )
    return resource
