from elan_ng.core.ids import IdAllocator, last_used_annotation_id
from elan_ng.io.eaf_reader import read_eaf

from support import DATA


def test_last_used_id_is_never_below_the_highest_existing_id() -> None:
    doc = read_eaf(DATA / "minimal.eaf")
    doc.header.set_property("lastUsedAnnotationId", "2")
    assert last_used_annotation_id(doc) == 5


def test_allocator_hands_out_fresh_ids_and_updates_the_property() -> None:
    doc = read_eaf(DATA / "minimal.eaf")
    allocator = IdAllocator(doc)
    assert [allocator.next_id(), allocator.next_id()] == ["a6", "a7"]
    assert doc.header.get_property("lastUsedAnnotationId") == "7"
