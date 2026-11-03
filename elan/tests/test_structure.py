"""Derived times and parents (REIMPLEMENTATION.md §2.1.2, §2.1.5)."""

from __future__ import annotations

from elan_ng.core.model import Document
from elan_ng.core.structure import analyze
from elan_ng.io.eaf_reader import read_eaf

from support import DATA, external


def _times(doc: Document) -> dict[str, tuple[float, float]]:
    structure = analyze(doc)
    return {a.id: structure.times[a] for a in doc.annotations() if a in structure.times}


def test_unaligned_slots_are_interpolated_along_the_chain() -> None:
    times = _times(read_eaf(DATA / "minimal.eaf"))
    assert times["a2"] == (1000, 1750)
    assert times["a3"] == (1750, 2500)


def test_symbolic_association_takes_parent_times() -> None:
    times = _times(read_eaf(DATA / "minimal.eaf"))
    assert times["a4"] == times["a2"]
    assert times["a5"] == times["a3"]


def test_two_unaligned_slots_split_evenly() -> None:
    times = _times(read_eaf(DATA / "edge_cases.eaf"))
    # words A under a1 (0-3000): w1 0-1000, then w2..w4 share 1000-3000 via two unaligned slots
    assert times["a3"] == (0, 1000)
    assert times["a4"][0] == 1000
    assert round(times["a4"][1], 3) == round(1000 + 2000 / 3, 3)
    assert round(times["a5"][1], 3) == round(1000 + 4000 / 3, 3)
    assert times["a6"][1] == 3000


def test_nested_subdivision_uses_parent_slots() -> None:
    times = _times(read_eaf(DATA / "edge_cases.eaf"))
    assert times["a8"] == (4000, 4500)
    assert times["a9"] == (4500, 5000)


def test_symbolic_subdivision_splits_parent_evenly_in_chain_order() -> None:
    times = _times(read_eaf(DATA / "edge_cases.eaf"))
    assert times["a12"] == (4000, 4000 + 1000 / 3)
    assert times["a14"][1] == 5000


def test_parents_are_derived() -> None:
    doc = read_eaf(DATA / "edge_cases.eaf")
    structure = analyze(doc)
    index = {a.id: a for a in doc.annotations()}
    assert structure.parent[index["a4"]] is index["a1"]
    assert structure.parent[index["a9"]] is index["a7"]
    assert structure.parent[index["a15"]] is index["a1"]  # Included In
    assert structure.parent[index["a16"]] is index["a2"]
    assert structure.parent[index["a10"]] is index["a3"]
    assert [c.id for c in structure.children[index["a2"]]] == ["a7", "a12", "a13", "a14", "a16"]


def test_every_annotation_in_elan_sample_is_resolved() -> None:
    doc = read_eaf(external("pympi_sample_3.0.eaf"))
    structure = analyze(doc)
    assert all(a in structure.times for a in doc.annotations())
    assert all(a in structure.parent for t in doc.tiers if t.parent_ref for a in t.annotations)
