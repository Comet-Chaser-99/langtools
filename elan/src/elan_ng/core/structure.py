"""Derived structure: display times and parent/child links (REIMPLEMENTATION.md §2.1.2, §2.1.5).

EAF does not store everything the editor needs. Unaligned time slots have no value, the
parent of an alignable annotation on a dependent tier is implicit, and reference
annotations have no times at all. :func:`analyze` derives all of this from a
:class:`Document` in one pass.
"""

from __future__ import annotations

import bisect
from dataclasses import dataclass, field

from elan_ng.core.model import (
    AlignableAnnotation,
    Annotation,
    Document,
    RefAnnotation,
    Stereotype,
    Tier,
    TimeSlot,
)


@dataclass
class Structure:
    # Display time (ms, may be fractional) of every slot that could be resolved.
    slot_times: dict[TimeSlot, float] = field(default_factory=dict)
    # Display interval of every annotation that could be resolved.
    times: dict[Annotation, tuple[float, float]] = field(default_factory=dict)
    parent: dict[Annotation, Annotation] = field(default_factory=dict)
    children: dict[Annotation, list[Annotation]] = field(default_factory=dict)
    tier_of: dict[Annotation, Tier] = field(default_factory=dict)


def _chains(tier: Tier) -> list[list[TimeSlot]]:
    """Maximal chains of slots on one tier, linking annotations where end == next begin."""
    alignable = [a for a in tier.annotations if isinstance(a, AlignableAnnotation)]
    by_begin = {a.begin: a for a in alignable}
    ends = {a.end for a in alignable}
    chains: list[list[TimeSlot]] = []
    for start in alignable:
        if start.begin in ends:
            continue  # not the first annotation of a chain
        chain = [start.begin]
        current: AlignableAnnotation | None = start
        visited: set[TimeSlot] = set()
        while current is not None and current.end not in visited:
            visited.add(current.end)
            chain.append(current.end)
            current = by_begin.get(current.end)
        chains.append(chain)
    return chains


def _interpolate(chain: list[TimeSlot], times: dict[TimeSlot, float]) -> None:
    """Spread unresolved slots in a chain evenly between their resolved neighbors."""
    last_known: int | None = None
    for index, slot in enumerate(chain):
        if slot not in times:
            continue
        if last_known is not None and index - last_known > 1:
            start, end = times[chain[last_known]], times[slot]
            steps = index - last_known
            for k in range(1, steps):
                times.setdefault(chain[last_known + k], start + (end - start) * k / steps)
        last_known = index


def resolve_slot_times(doc: Document) -> dict[TimeSlot, float]:
    times: dict[TimeSlot, float] = {
        s: float(s.value) for s in doc.time_order if s.value is not None
    }
    # Parents first, so a nested subdivision can use the interpolated slots of its parent.
    for tier in doc.tiers_in_hierarchy_order():
        for chain in _chains(tier):
            _interpolate(chain, times)
    # Fallback for anything still unresolved (malformed files): use the global slot order.
    _interpolate(doc.time_order, times)
    return times


def analyze(doc: Document) -> Structure:
    result = Structure(slot_times=resolve_slot_times(doc))
    index: dict[str, Annotation] = {}
    for tier in doc.tiers:
        for annotation in tier.annotations:
            index[annotation.id] = annotation
            result.tier_of[annotation] = tier
            if isinstance(annotation, AlignableAnnotation):
                begin = result.slot_times.get(annotation.begin)
                end = result.slot_times.get(annotation.end)
                if begin is not None and end is not None:
                    result.times[annotation] = (begin, end)

    for tier in doc.tiers_in_hierarchy_order():
        parent_tier = doc.tier(tier.parent_ref) if tier.parent_ref else None
        if parent_tier is None:
            continue
        candidates = sorted(
            (result.times[a][0], result.times[a][1], i, a)
            for i, a in enumerate(parent_tier.annotations)
            if a in result.times
        )
        begins = [c[0] for c in candidates]
        for annotation in tier.annotations:
            parent: Annotation | None = None
            if isinstance(annotation, RefAnnotation):
                parent = index.get(annotation.ref)
            elif annotation in result.times:
                begin, end = result.times[annotation]
                position = bisect.bisect_right(begins, begin) - 1
                if position >= 0 and candidates[position][1] >= end:
                    parent = candidates[position][3]
            if parent is not None:
                result.parent[annotation] = parent
                result.children.setdefault(parent, []).append(annotation)

    # Reference annotations take their times from the parent, in hierarchy order.
    for tier in doc.tiers_in_hierarchy_order():
        stereotype = doc.stereotype_of(tier)
        if stereotype is Stereotype.SYMBOLIC_ASSOCIATION:
            for annotation in tier.annotations:
                parent = result.parent.get(annotation)
                if parent is not None and parent in result.times:
                    result.times[annotation] = result.times[parent]
        elif stereotype is Stereotype.SYMBOLIC_SUBDIVISION:
            for parent, siblings in symbolic_order(tier, result).items():
                if parent not in result.times:
                    continue
                begin, end = result.times[parent]
                step = (end - begin) / len(siblings)
                for k, child in enumerate(siblings):
                    result.times[child] = (begin + k * step, begin + (k + 1) * step)
    return result


def symbolic_order(tier: Tier, structure: Structure) -> dict[Annotation, list[Annotation]]:
    """Children of each parent on a Symbolic Subdivision tier, in PREVIOUS_ANNOTATION order."""
    groups: dict[Annotation, list[RefAnnotation]] = {}
    for annotation in tier.annotations:
        parent = structure.parent.get(annotation)
        if parent is not None and isinstance(annotation, RefAnnotation):
            groups.setdefault(parent, []).append(annotation)
    ordered: dict[Annotation, list[Annotation]] = {}
    for parent, siblings in groups.items():
        next_of: dict[str | None, RefAnnotation] = {a.previous: a for a in siblings}
        chain: list[Annotation] = []
        current = next_of.get(None)
        while current is not None and current not in chain:
            chain.append(current)
            current = next_of.get(current.id)
        # Siblings not reachable from the head (broken chains) keep document order.
        chain.extend(a for a in siblings if a not in chain)
        ordered[parent] = chain
    return ordered
