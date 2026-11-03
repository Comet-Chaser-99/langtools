"""Reader and writer details (REIMPLEMENTATION.md §3.1-§3.2)."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from elan_ng.core.model import AlignableAnnotation, RefAnnotation, Stereotype
from elan_ng.io.eaf_reader import EAFError, parse_eaf, read_eaf
from elan_ng.io.eaf_writer import save_eaf, write_eaf

from support import DATA


def test_minimal_example_fields() -> None:
    doc = read_eaf(DATA / "minimal.eaf")
    assert [t.id for t in doc.tiers] == ["tx@A", "wd@A", "gl@A"]
    assert doc.header.media[0].relative_media_url == "./story.wav"
    assert doc.header.get_property("lastUsedAnnotationId") == "5"
    assert [s.value for s in doc.time_order] == [1000, None, 2500]
    words = doc.tier("wd@A")
    assert words is not None
    first, second = words.annotations
    assert isinstance(first, AlignableAnnotation) and isinstance(second, AlignableAnnotation)
    assert first.end is second.begin  # shared slot
    gloss = doc.tier("gl@A")
    assert gloss is not None
    assert isinstance(gloss.annotations[1], RefAnnotation)
    assert gloss.annotations[1].cve_ref == "cveid1"
    gloss_type = doc.tier_type("gloss")
    assert gloss_type is not None
    assert gloss_type.constraint is Stereotype.SYMBOLIC_ASSOCIATION
    pos = doc.vocabulary("pos")
    assert pos is not None
    assert pos.entries[0].value_in("eng") == "N"


def test_unknown_content_and_comments_are_kept_in_place() -> None:
    out = write_eaf(read_eaf(DATA / "edge_cases.eaf")).decode()
    assert out.index("<!-- A comment before the root element. -->") < out.index(
        "<ANNOTATION_DOCUMENT"
    )
    assert 'FUTURE_ROOT_ATTR="kept"' in out
    assert '<FUTURE_HEADER_ELEMENT VALUE="kept">with text</FUTURE_HEADER_ELEMENT>' in out
    assert out.index("FUTURE_HEADER_ELEMENT") > out.index('NAME="custom"')
    assert 'FUTURE_ANNOTATION_ATTR="kept"' in out
    assert out.index("<!-- comment between annotations -->") > out.index('ANNOTATION_ID="a2"')
    assert out.rstrip().endswith(
        "<FUTURE_TOP_LEVEL_ELEMENT>kept at the end</FUTURE_TOP_LEVEL_ELEMENT>\n"
        "</ANNOTATION_DOCUMENT>"
    )


def test_values_survive_exactly() -> None:
    doc = parse_eaf(write_eaf(read_eaf(DATA / "edge_cases.eaf")))
    a1 = doc.annotation_index()["a1"][1]
    assert a1.value == "first line\nsecond line with ünïcödé, emoji 🎙️ and RTL שלום"
    assert doc.annotation_index()["a2"][1].value == ""
    assert doc.header.get_property("custom") == 'multi\nline & "quoted"'


def test_empty_value_is_written_like_elan() -> None:
    out = write_eaf(read_eaf(DATA / "edge_cases.eaf")).decode()
    assert "<ANNOTATION_VALUE></ANNOTATION_VALUE>" in out
    assert "<ANNOTATION_VALUE/>" not in out


def test_attributes_are_alphabetical_like_elan() -> None:
    out = write_eaf(read_eaf(DATA / "edge_cases.eaf")).decode()
    assert (
        '<TIER ANNOTATOR="HF" DEFAULT_LOCALE="en" LANG_REF="eng" '
        'LINGUISTIC_TYPE_REF="utterance" PARTICIPANT="Speaker A" TIER_ID="utterance A">'
    ) in out


def test_time_slots_are_renumbered_and_unused_ones_dropped() -> None:
    doc = read_eaf(DATA / "problems.eaf")
    out = write_eaf(doc).decode()
    assert 'TIME_VALUE="9000"' not in out  # ts7 is unused
    assert 'TIME_SLOT_ID="ts6"' in out and 'TIME_SLOT_ID="ts7"' not in out


def test_old_controlled_vocabularies_become_multilingual() -> None:
    doc = read_eaf(DATA / "old_cv_2_7.eaf")
    und = [lang for lang in doc.languages if lang.id == "und"]
    assert und and und[0].label == "undetermined (und)"
    gesture = doc.vocabulary("Gesture")
    assert gesture is not None
    assert [(d.lang_ref, d.text) for d in gesture.descriptions] == [("und", "Gesture phases")]
    assert [e.values[0].value for e in gesture.entries] == ["prep", "stroke"]
    assert gesture.entries[1].ext_ref == "er1"
    assert gesture.entries[0].values[0].description == "preparation"
    assert all(e.id.startswith("cveid_") for e in gesture.entries)
    empty = doc.vocabulary("Empty description")
    assert empty is not None and empty.descriptions == []
    out = write_eaf(doc).decode()
    assert 'VERSION="3.0"' in out and "EAFv3.0.xsd" in out and "CV_ENTRY " not in out


def test_save_updates_header_and_writes_atomically(tmp_path: Path) -> None:
    doc = read_eaf(DATA / "minimal.eaf")
    doc.header.properties = [p for p in doc.header.properties if p.name != "URN"]
    target = tmp_path / "saved.eaf"
    save_eaf(doc, target, now=datetime(2026, 11, 2, 12, 0, tzinfo=UTC))
    saved = read_eaf(target)
    assert saved.date.startswith("2026-11-02T")
    urn = saved.header.get_property("URN")
    assert urn is not None and urn.startswith("urn:nl-mpi-tools-elan-eaf:")
    assert saved.header.get_property("lastUsedAnnotationId") == "5"
    assert [p.name for p in tmp_path.iterdir()] == ["saved.eaf"]


@pytest.mark.parametrize(
    ("data", "message"),
    [(b"<not-xml", "well-formed"), (b"<TIER/>", "ANNOTATION_DOCUMENT")],
)
def test_bad_input_raises_eaf_error(data: bytes, message: str) -> None:
    with pytest.raises(EAFError, match=message):
        parse_eaf(data)
