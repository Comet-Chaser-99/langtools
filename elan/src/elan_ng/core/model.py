"""The EAF data model (REIMPLEMENTATION.md §2.1, §3.1).

Plain mutable dataclasses. Fields mirror EAF elements and attributes one to one, so the
reader and writer stay simple and nothing is lost. Optional attributes that are absent in
the file are ``None`` (not ""), so "absent" and "empty" round-trip differently.

Every element class carries a :class:`Residue` with the XML the model does not understand
(unknown attributes, unknown child elements, comments); the io layer fills and writes it.
The core never looks inside it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


@dataclass
class Residue:
    """Unknown content of one element, kept for lossless round-trips (§3.2).

    ``attrs`` holds unknown attributes in document order. ``children`` holds
    ``(anchor, node)`` pairs: ``anchor`` is the number of known child elements that
    precede the node, ``node`` is an opaque object owned by the io layer.
    """

    attrs: dict[str, str] = field(default_factory=dict)
    children: list[tuple[int, object]] = field(default_factory=list)

    def __bool__(self) -> bool:
        return bool(self.attrs or self.children)


class Stereotype(StrEnum):
    TIME_SUBDIVISION = "Time_Subdivision"
    SYMBOLIC_SUBDIVISION = "Symbolic_Subdivision"
    SYMBOLIC_ASSOCIATION = "Symbolic_Association"
    INCLUDED_IN = "Included_In"

    @property
    def alignable(self) -> bool:
        return self in (Stereotype.TIME_SUBDIVISION, Stereotype.INCLUDED_IN)


# The descriptions ELAN writes, byte for byte (including its spelling "refering", §2.1.4).
CONSTRAINT_DESCRIPTIONS: dict[Stereotype, str] = {
    Stereotype.TIME_SUBDIVISION: (
        "Time subdivision of parent annotation's time interval, "
        "no time gaps allowed within this interval"
    ),
    Stereotype.SYMBOLIC_SUBDIVISION: (
        "Symbolic subdivision of a parent annotation. "
        "Annotations refering to the same parent are ordered"
    ),
    Stereotype.SYMBOLIC_ASSOCIATION: "1-1 association with a parent annotation",
    Stereotype.INCLUDED_IN: (
        "Time alignable annotations within the parent annotation's time interval, gaps are allowed"
    ),
}


@dataclass(eq=False)
class TimeSlot:
    """A point on the time axis. ``value`` is ms, or ``None`` for an unaligned slot.

    Compared by identity: two slots with the same value are still different slots.
    ``id`` is the id read from the file; the writer renumbers slots (§3.1.3).
    """

    id: str
    value: int | None = None
    residue: Residue = field(default_factory=Residue)

    @property
    def aligned(self) -> bool:
        return self.value is not None

    def __repr__(self) -> str:
        return f"TimeSlot({self.id!r}, {self.value!r})"


@dataclass(eq=False)
class Annotation:
    id: str
    value: str = ""
    ext_ref: str | None = None
    lang_ref: str | None = None
    cve_ref: str | None = None
    residue: Residue = field(default_factory=Residue)
    # Residue of the wrapping <ANNOTATION> element.
    wrapper_residue: Residue = field(default_factory=Residue)
    value_residue: Residue = field(default_factory=Residue)


@dataclass(eq=False)
class AlignableAnnotation(Annotation):
    begin: TimeSlot = field(default_factory=lambda: TimeSlot(""))
    end: TimeSlot = field(default_factory=lambda: TimeSlot(""))
    svg_ref: str | None = None

    def __repr__(self) -> str:
        return f"AlignableAnnotation({self.id!r}, {self.value!r}, {self.begin}, {self.end})"


@dataclass(eq=False)
class RefAnnotation(Annotation):
    ref: str = ""  # ANNOTATION_REF: id of the parent annotation
    previous: str | None = None  # PREVIOUS_ANNOTATION (Symbolic Subdivision chains)

    def __repr__(self) -> str:
        return f"RefAnnotation({self.id!r}, {self.value!r}, ref={self.ref!r})"


@dataclass(eq=False)
class Tier:
    id: str
    type_ref: str
    parent_ref: str | None = None
    participant: str | None = None
    annotator: str | None = None
    default_locale: str | None = None
    lang_ref: str | None = None
    ext_ref: str | None = None
    annotations: list[AlignableAnnotation | RefAnnotation] = field(default_factory=list)
    residue: Residue = field(default_factory=Residue)


@dataclass
class TierType:
    """A LINGUISTIC_TYPE. Boolean attributes keep their raw text ("true"/"false")."""

    id: str
    time_alignable: str | None = None
    constraint: Stereotype | None = None
    graphic_references: str | None = None
    cv_ref: str | None = None
    ext_ref: str | None = None
    lexicon_ref: str | None = None
    residue: Residue = field(default_factory=Residue)


@dataclass
class MediaDescriptor:
    media_url: str
    mime_type: str
    relative_media_url: str | None = None
    time_origin: int | None = None
    extracted_from: str | None = None
    residue: Residue = field(default_factory=Residue)


@dataclass
class LinkedFileDescriptor:
    link_url: str
    mime_type: str
    relative_link_url: str | None = None
    time_origin: int | None = None
    associated_with: str | None = None
    residue: Residue = field(default_factory=Residue)


@dataclass
class Property:
    name: str | None
    value: str
    residue: Residue = field(default_factory=Residue)


@dataclass
class Header:
    media_file: str | None = None
    time_units: str | None = None
    media: list[MediaDescriptor] = field(default_factory=list)
    linked_files: list[LinkedFileDescriptor] = field(default_factory=list)
    properties: list[Property] = field(default_factory=list)
    residue: Residue = field(default_factory=Residue)

    def get_property(self, name: str) -> str | None:
        for prop in self.properties:
            if prop.name == name:
                return prop.value
        return None

    def set_property(self, name: str, value: str) -> None:
        for prop in self.properties:
            if prop.name == name:
                prop.value = value
                return
        self.properties.append(Property(name, value))


@dataclass
class License:
    text: str
    url: str | None = None
    residue: Residue = field(default_factory=Residue)


@dataclass
class Locale:
    language_code: str
    country_code: str | None = None
    variant: str | None = None
    residue: Residue = field(default_factory=Residue)


@dataclass
class Language:
    id: str
    definition: str | None = None
    label: str | None = None
    residue: Residue = field(default_factory=Residue)


@dataclass
class Constraint:
    stereotype: str
    description: str | None = None
    residue: Residue = field(default_factory=Residue)


@dataclass
class LangText:
    """A text with a language: CV DESCRIPTION elements."""

    lang_ref: str
    text: str
    residue: Residue = field(default_factory=Residue)


@dataclass
class CVEValue:
    lang_ref: str
    value: str
    description: str | None = None
    residue: Residue = field(default_factory=Residue)


@dataclass
class CVEntry:
    id: str
    values: list[CVEValue] = field(default_factory=list)
    ext_ref: str | None = None
    residue: Residue = field(default_factory=Residue)

    def value_in(self, lang_ref: str | None) -> str:
        for value in self.values:
            if value.lang_ref == lang_ref:
                return value.value
        return self.values[0].value if self.values else ""


@dataclass
class ControlledVocabulary:
    id: str
    descriptions: list[LangText] = field(default_factory=list)
    entries: list[CVEntry] = field(default_factory=list)
    ext_ref: str | None = None
    residue: Residue = field(default_factory=Residue)


@dataclass
class LexiconRef:
    id: str
    name: str
    type: str
    url: str
    lexicon_id: str
    lexicon_name: str
    datcat_id: str | None = None
    datcat_name: str | None = None
    residue: Residue = field(default_factory=Residue)


@dataclass
class ExternalRef:
    id: str
    type: str
    value: str
    residue: Residue = field(default_factory=Residue)


@dataclass
class RefLink:
    """A CROSS_REF_LINK (``kind == "cross"``) or GROUP_REF_LINK (``kind == "group"``).

    Attributes are kept as an ordered dict because links are not editable before P2;
    the engine only needs ``refs()`` to keep them consistent when annotations are deleted.
    """

    kind: str
    attrs: dict[str, str]
    text: str = ""
    residue: Residue = field(default_factory=Residue)

    def refs(self) -> list[str]:
        if self.kind == "cross":
            return [self.attrs.get("REF1", ""), self.attrs.get("REF2", "")]
        return self.attrs.get("REFS", "").split()


@dataclass
class RefLinkSet:
    attrs: dict[str, str]
    links: list[RefLink] = field(default_factory=list)
    residue: Residue = field(default_factory=Residue)


@dataclass(eq=False)
class Document:
    author: str = ""
    date: str = ""
    version: str = "3.0"
    format: str | None = "3.0"
    licenses: list[License] = field(default_factory=list)
    header: Header = field(default_factory=Header)
    time_order: list[TimeSlot] = field(default_factory=list)
    tiers: list[Tier] = field(default_factory=list)
    tier_types: list[TierType] = field(default_factory=list)
    locales: list[Locale] = field(default_factory=list)
    languages: list[Language] = field(default_factory=list)
    constraints: list[Constraint] = field(default_factory=list)
    vocabularies: list[ControlledVocabulary] = field(default_factory=list)
    lexicon_refs: list[LexiconRef] = field(default_factory=list)
    ref_link_sets: list[RefLinkSet] = field(default_factory=list)
    external_refs: list[ExternalRef] = field(default_factory=list)
    residue: Residue = field(default_factory=Residue)
    # Residue of TIME_ORDER itself (its unknown attributes, comments between slots).
    time_order_residue: Residue = field(default_factory=Residue)
    # Root attributes such as xsi:noNamespaceSchemaLocation, kept verbatim.
    root_extra: dict[str, str] = field(default_factory=dict)
    # Comments and processing instructions before / after the root element (opaque).
    prolog: list[object] = field(default_factory=list)
    epilog: list[object] = field(default_factory=list)
    source_version: str | None = None

    # -- lookups ---------------------------------------------------------------------

    def tier(self, tier_id: str) -> Tier | None:
        return next((t for t in self.tiers if t.id == tier_id), None)

    def tier_type(self, type_id: str) -> TierType | None:
        return next((t for t in self.tier_types if t.id == type_id), None)

    def vocabulary(self, cv_id: str) -> ControlledVocabulary | None:
        return next((v for v in self.vocabularies if v.id == cv_id), None)

    def stereotype_of(self, tier: Tier) -> Stereotype | None:
        tier_type = self.tier_type(tier.type_ref)
        return tier_type.constraint if tier_type else None

    def children_of(self, tier: Tier) -> list[Tier]:
        return [t for t in self.tiers if t.parent_ref == tier.id]

    def annotations(self) -> list[AlignableAnnotation | RefAnnotation]:
        return [a for tier in self.tiers for a in tier.annotations]

    def annotation_index(self) -> dict[str, tuple[Tier, AlignableAnnotation | RefAnnotation]]:
        return {a.id: (tier, a) for tier in self.tiers for a in tier.annotations}

    def tiers_in_hierarchy_order(self) -> list[Tier]:
        """Parents before children; document order among siblings. Orphans come last."""
        ordered: list[Tier] = []
        seen: set[str] = set()

        def visit(tier: Tier) -> None:
            if tier.id in seen:
                return
            seen.add(tier.id)
            ordered.append(tier)
            for child in self.children_of(tier):
                visit(child)

        for tier in self.tiers:
            if tier.parent_ref is None:
                visit(tier)
        ordered.extend(t for t in self.tiers if t.id not in seen)
        return ordered
