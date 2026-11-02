"""Write the core model as EAF 3.0 (REIMPLEMENTATION.md §3.1.3, §3.2).

Output follows what ELAN itself writes, so diffs stay small: attributes in alphabetical
order, 4-space indentation, time slots renumbered ts1..tsN in time order, unused slots
dropped, and the four CONSTRAINT elements with ELAN's descriptions.
"""

from __future__ import annotations

import os
import tempfile
import uuid
from datetime import datetime
from pathlib import Path

from lxml import etree

from elan_ng.core.ids import last_used_annotation_id
from elan_ng.core.model import (
    CONSTRAINT_DESCRIPTIONS,
    AlignableAnnotation,
    ControlledVocabulary,
    Document,
    Header,
    Property,
    RefAnnotation,
    Residue,
    Stereotype,
    Tier,
    TimeSlot,
)
from elan_ng.io.xmlutil import (
    XSI,
    Element,
    append_children,
    make,
    serialize,
    text_element,
)

SCHEMA_LOCATION = "http://www.mpi.nl/tools/elan/EAFv3.0.xsd"
SCHEMA_LOCATION_ATTR = f"{{{XSI}}}noNamespaceSchemaLocation"


def write_eaf(doc: Document) -> bytes:
    """Serialize without changing the document."""
    root = _Writer(doc).document()
    return _move_namespace_declaration(serialize(root, doc.prolog, doc.epilog))


def _move_namespace_declaration(data: bytes) -> bytes:
    """lxml writes xmlns:xsi first; ELAN writes it after the plain attributes."""
    declaration = f' xmlns:xsi="{XSI}"'.encode()
    start = data.index(b"<ANNOTATION_DOCUMENT")
    end = data.index(b">", start)
    tag = data[start:end]
    if declaration not in tag:
        return data
    tag = tag.replace(declaration, b"", 1)
    position = tag.find(b" xsi:")
    tag = tag + declaration if position < 0 else tag[:position] + declaration + tag[position:]
    return data[:start] + tag + data[end:]


def save_eaf(doc: Document, path: str | Path, *, now: datetime | None = None) -> None:
    """Prepare the document for saving (date, ids, URN) and write it atomically."""
    prepare_for_save(doc, now=now)
    data = write_eaf(doc)
    target = Path(path)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{target.name}.", dir=target.parent)
    try:
        with os.fdopen(fd, "wb") as tmp:
            tmp.write(data)
            tmp.flush()
            os.fsync(tmp.fileno())
        os.replace(tmp_name, target)
    except BaseException:
        Path(tmp_name).unlink(missing_ok=True)
        raise


def prepare_for_save(doc: Document, *, now: datetime | None = None) -> None:
    moment = (now or datetime.now()).astimezone()
    doc.date = moment.isoformat(timespec="seconds")
    doc.version = "3.0"
    doc.format = "3.0"
    if doc.header.get_property("URN") is None:
        doc.header.properties.insert(
            0, Property("URN", f"urn:nl-mpi-tools-elan-eaf:{uuid.uuid4()}")
        )
    doc.header.set_property("lastUsedAnnotationId", str(last_used_annotation_id(doc)))


class _Writer:
    def __init__(self, doc: Document) -> None:
        self.doc = doc
        self.slot_ids = self._number_slots()

    def _number_slots(self) -> dict[TimeSlot, str]:
        used: set[TimeSlot] = set()
        for tier in self.doc.tiers:
            for annotation in tier.annotations:
                if isinstance(annotation, AlignableAnnotation):
                    used.add(annotation.begin)
                    used.add(annotation.end)
        ordered = [slot for slot in self.doc.time_order if slot in used]
        # Slots referenced by annotations but missing from TIME_ORDER (malformed input)
        # are written at the end so references still resolve.
        listed = set(ordered)
        for tier in self.doc.tiers:
            for annotation in tier.annotations:
                if isinstance(annotation, AlignableAnnotation):
                    for slot in (annotation.begin, annotation.end):
                        if slot not in listed:
                            listed.add(slot)
                            ordered.append(slot)
        return {slot: f"ts{index}" for index, slot in enumerate(ordered, start=1)}

    def document(self) -> Element:
        doc = self.doc
        attrs: dict[str, str | None] = {
            "AUTHOR": doc.author,
            "DATE": doc.date,
            "FORMAT": "3.0",
            "VERSION": "3.0",
        }
        extra = dict(doc.root_extra)
        if doc.source_version not in (None, "3.0") or SCHEMA_LOCATION_ATTR not in extra:
            extra[SCHEMA_LOCATION_ATTR] = SCHEMA_LOCATION
        attrs.update(extra)
        root = etree.Element("ANNOTATION_DOCUMENT", nsmap={"xsi": XSI})
        for key in sorted(attrs, key=lambda k: (k.startswith("{"), k)):
            value = attrs[key]
            if value is not None:
                root.set(key, value)

        known: list[Element] = []
        known += [
            text_element("LICENSE", {"LICENSE_URL": lic.url}, lic.text, lic.residue)
            for lic in doc.licenses
        ]
        known.append(self.header(doc.header))
        known.append(self.time_order())
        known += [self.tier(tier) for tier in doc.tiers]
        known += [
            self.leaf(
                "LINGUISTIC_TYPE",
                {
                    "LINGUISTIC_TYPE_ID": t.id,
                    "TIME_ALIGNABLE": t.time_alignable,
                    "CONSTRAINTS": t.constraint.value if t.constraint else None,
                    "GRAPHIC_REFERENCES": t.graphic_references,
                    "CONTROLLED_VOCABULARY_REF": t.cv_ref,
                    "EXT_REF": t.ext_ref,
                    "LEXICON_REF": t.lexicon_ref,
                },
                t.residue,
            )
            for t in doc.tier_types
        ]
        known += [
            self.leaf(
                "LOCALE",
                {
                    "LANGUAGE_CODE": loc.language_code,
                    "COUNTRY_CODE": loc.country_code,
                    "VARIANT": loc.variant,
                },
                loc.residue,
            )
            for loc in doc.locales
        ]
        known += [
            self.leaf(
                "LANGUAGE",
                {
                    "LANG_ID": lang.id,
                    "LANG_DEF": lang.definition,
                    "LANG_LABEL": lang.label,
                },
                lang.residue,
            )
            for lang in doc.languages
        ]
        known += self.constraints()
        known += [self.vocabulary(cv) for cv in doc.vocabularies]
        known += [
            self.leaf(
                "LEXICON_REF",
                {
                    "LEX_REF_ID": lex.id,
                    "NAME": lex.name,
                    "TYPE": lex.type,
                    "URL": lex.url,
                    "LEXICON_ID": lex.lexicon_id,
                    "LEXICON_NAME": lex.lexicon_name,
                    "DATCAT_ID": lex.datcat_id,
                    "DATCAT_NAME": lex.datcat_name,
                },
                lex.residue,
            )
            for lex in doc.lexicon_refs
        ]
        for link_set in doc.ref_link_sets:
            set_el = make("REF_LINK_SET", dict(link_set.attrs))
            links = [
                text_element(
                    "CROSS_REF_LINK" if link.kind == "cross" else "GROUP_REF_LINK",
                    dict(link.attrs),
                    link.text,
                    link.residue,
                )
                for link in link_set.links
            ]
            append_children(set_el, links, link_set.residue)
            known.append(set_el)
        known += [
            self.leaf(
                "EXTERNAL_REF",
                {
                    "EXT_REF_ID": ref.id,
                    "TYPE": ref.type,
                    "VALUE": ref.value,
                },
                ref.residue,
            )
            for ref in doc.external_refs
        ]
        append_children(root, known, doc.residue)
        return root

    def leaf(self, tag: str, attrs: dict[str, str | None], residue: Residue) -> Element:
        el = make(tag, attrs, residue)
        append_children(el, [], residue)
        return el

    def header(self, header: Header) -> Element:
        el = make(
            "HEADER",
            {"MEDIA_FILE": header.media_file, "TIME_UNITS": header.time_units},
            header.residue,
        )
        children: list[Element] = []
        for media in header.media:
            children.append(
                self.leaf(
                    "MEDIA_DESCRIPTOR",
                    {
                        "MEDIA_URL": media.media_url,
                        "RELATIVE_MEDIA_URL": media.relative_media_url,
                        "MIME_TYPE": media.mime_type,
                        "TIME_ORIGIN": _str(media.time_origin),
                        "EXTRACTED_FROM": media.extracted_from,
                    },
                    media.residue,
                )
            )
        for linked in header.linked_files:
            children.append(
                self.leaf(
                    "LINKED_FILE_DESCRIPTOR",
                    {
                        "LINK_URL": linked.link_url,
                        "RELATIVE_LINK_URL": linked.relative_link_url,
                        "MIME_TYPE": linked.mime_type,
                        "TIME_ORIGIN": _str(linked.time_origin),
                        "ASSOCIATED_WITH": linked.associated_with,
                    },
                    linked.residue,
                )
            )
        for prop in header.properties:
            children.append(text_element("PROPERTY", {"NAME": prop.name}, prop.value, prop.residue))
        append_children(el, children, header.residue)
        return el

    def time_order(self) -> Element:
        el = make("TIME_ORDER", {}, self.doc.time_order_residue)
        slots = [
            self.leaf(
                "TIME_SLOT", {"TIME_SLOT_ID": slot_id, "TIME_VALUE": _str(slot.value)}, slot.residue
            )
            for slot, slot_id in self.slot_ids.items()
        ]
        append_children(el, slots, self.doc.time_order_residue)
        return el

    def tier(self, tier: Tier) -> Element:
        el = make(
            "TIER",
            {
                "TIER_ID": tier.id,
                "PARTICIPANT": tier.participant,
                "ANNOTATOR": tier.annotator,
                "LINGUISTIC_TYPE_REF": tier.type_ref,
                "DEFAULT_LOCALE": tier.default_locale,
                "PARENT_REF": tier.parent_ref,
                "EXT_REF": tier.ext_ref,
                "LANG_REF": tier.lang_ref,
            },
            tier.residue,
        )
        children = [self.annotation(a) for a in tier.annotations]
        append_children(el, children, tier.residue)
        return el

    def annotation(self, annotation: AlignableAnnotation | RefAnnotation) -> Element:
        wrapper = make("ANNOTATION", {}, annotation.wrapper_residue)
        common: dict[str, str | None] = {
            "ANNOTATION_ID": annotation.id,
            "EXT_REF": annotation.ext_ref,
            "LANG_REF": annotation.lang_ref,
            "CVE_REF": annotation.cve_ref,
        }
        if isinstance(annotation, AlignableAnnotation):
            inner = make(
                "ALIGNABLE_ANNOTATION",
                {
                    **common,
                    "TIME_SLOT_REF1": self.slot_ids[annotation.begin],
                    "TIME_SLOT_REF2": self.slot_ids[annotation.end],
                    "SVG_REF": annotation.svg_ref,
                },
                annotation.residue,
            )
        else:
            inner = make(
                "REF_ANNOTATION",
                {
                    **common,
                    "ANNOTATION_REF": annotation.ref,
                    "PREVIOUS_ANNOTATION": annotation.previous,
                },
                annotation.residue,
            )
        value = text_element(
            "ANNOTATION_VALUE", {}, annotation.value, annotation.value_residue, always_open=True
        )
        append_children(inner, [value], annotation.residue)
        append_children(wrapper, [inner], annotation.wrapper_residue)
        return wrapper

    def constraints(self) -> list[Element]:
        """The CONSTRAINT elements: the file's own, else ELAN's standard four."""
        if self.doc.constraints:
            return [
                self.leaf(
                    "CONSTRAINT",
                    {"STEREOTYPE": c.stereotype, "DESCRIPTION": c.description},
                    c.residue,
                )
                for c in self.doc.constraints
            ]
        return [
            make("CONSTRAINT", {"STEREOTYPE": s.value, "DESCRIPTION": CONSTRAINT_DESCRIPTIONS[s]})
            for s in (
                Stereotype.TIME_SUBDIVISION,
                Stereotype.SYMBOLIC_SUBDIVISION,
                Stereotype.SYMBOLIC_ASSOCIATION,
                Stereotype.INCLUDED_IN,
            )
        ]

    def vocabulary(self, cv: ControlledVocabulary) -> Element:
        el = make("CONTROLLED_VOCABULARY", {"CV_ID": cv.id, "EXT_REF": cv.ext_ref}, cv.residue)
        children = [
            text_element("DESCRIPTION", {"LANG_REF": d.lang_ref}, d.text, d.residue)
            for d in cv.descriptions
        ]
        for entry in cv.entries:
            entry_el = make(
                "CV_ENTRY_ML", {"CVE_ID": entry.id, "EXT_REF": entry.ext_ref}, entry.residue
            )
            values = [
                text_element(
                    "CVE_VALUE",
                    {"LANG_REF": v.lang_ref, "DESCRIPTION": v.description},
                    v.value,
                    v.residue,
                )
                for v in entry.values
            ]
            append_children(entry_el, values, entry.residue)
            children.append(entry_el)
        append_children(el, children, cv.residue)
        return el


def _str(value: int | None) -> str | None:
    return None if value is None else str(value)
