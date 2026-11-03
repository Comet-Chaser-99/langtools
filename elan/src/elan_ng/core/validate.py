"""Document checks (REIMPLEMENTATION.md §2.1.2 invariants I1-I3, §2.1.4 stereotype rules).

:func:`validate` never changes the document. The reader loads files with problems as
they are (§3.2 point 5); this report is what the UI shows as the "repair report", and
what the constraint engine (M2) asserts is empty after every edit.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from enum import StrEnum
from itertools import pairwise

from elan_ng.core.model import (
    AlignableAnnotation,
    Annotation,
    Document,
    RefAnnotation,
    Stereotype,
    Tier,
)
from elan_ng.core.structure import Structure, analyze, symbolic_order


class Severity(StrEnum):
    ERROR = "error"  # breaks the data model or the schema
    WARNING = "warning"  # ELAN tolerates it, but it violates a rule


@dataclass(frozen=True)
class Problem:
    code: str
    severity: Severity
    message: str
    ids: tuple[str, ...] = ()


def validate(doc: Document, structure: Structure | None = None) -> list[Problem]:
    structure = structure or analyze(doc)
    problems: list[Problem] = []
    problems += _references(doc)
    problems += _time_order(doc)
    problems += _tiers(doc, structure)
    return problems


def _err(code: str, message: str, *ids: str) -> Problem:
    return Problem(code, Severity.ERROR, message, ids)


def _warn(code: str, message: str, *ids: str) -> Problem:
    return Problem(code, Severity.WARNING, message, ids)


def _references(doc: Document) -> list[Problem]:
    problems: list[Problem] = []
    for name, counts in (
        ("tier", Counter(t.id for t in doc.tiers)),
        ("tier type", Counter(t.id for t in doc.tier_types)),
        ("controlled vocabulary", Counter(v.id for v in doc.vocabularies)),
        ("annotation", Counter(a.id for a in doc.annotations())),
    ):
        for key, count in counts.items():
            if count > 1:
                problems.append(_err("duplicate-id", f"{count} {name}s have the id {key!r}", key))

    type_ids = {t.id for t in doc.tier_types}
    tier_ids = {t.id for t in doc.tiers}
    cv_ids = {v.id for v in doc.vocabularies}
    lang_ids = {lang.id for lang in doc.languages}
    for tier in doc.tiers:
        if tier.type_ref not in type_ids:
            problems.append(
                _err(
                    "unknown-type",
                    f"tier {tier.id!r} uses unknown tier type {tier.type_ref!r}",
                    tier.id,
                )
            )
        if tier.parent_ref is not None and tier.parent_ref not in tier_ids:
            problems.append(
                _err(
                    "unknown-parent",
                    f"tier {tier.id!r} has unknown parent {tier.parent_ref!r}",
                    tier.id,
                )
            )
        if tier.lang_ref is not None and tier.lang_ref not in lang_ids:
            problems.append(
                _err(
                    "unknown-language",
                    f"tier {tier.id!r} refers to unknown language {tier.lang_ref!r}",
                    tier.id,
                )
            )
    for tier_type in doc.tier_types:
        if tier_type.cv_ref is not None and tier_type.cv_ref not in cv_ids:
            problems.append(
                _err(
                    "unknown-cv",
                    f"tier type {tier_type.id!r} refers to unknown "
                    f"controlled vocabulary {tier_type.cv_ref!r}",
                    tier_type.id,
                )
            )

    slots = set(doc.time_order)
    annotation_ids = {a.id for a in doc.annotations()}
    for annotation in doc.annotations():
        if isinstance(annotation, AlignableAnnotation):
            for slot in (annotation.begin, annotation.end):
                if slot not in slots:
                    problems.append(
                        _err(
                            "unknown-slot",
                            f"annotation {annotation.id!r} refers to unknown time slot {slot.id!r}",
                            annotation.id,
                        )
                    )
        else:
            if annotation.ref not in annotation_ids:
                problems.append(
                    _err(
                        "unknown-annotation",
                        f"annotation {annotation.id!r} refers to unknown parent {annotation.ref!r}",
                        annotation.id,
                    )
                )
            if annotation.previous is not None and annotation.previous not in annotation_ids:
                problems.append(
                    _err(
                        "unknown-annotation",
                        f"annotation {annotation.id!r} refers "
                        f"to unknown previous annotation {annotation.previous!r}",
                        annotation.id,
                    )
                )
    return problems


def _time_order(doc: Document) -> list[Problem]:
    problems: list[Problem] = []
    # I2: aligned values never decrease along TIME_ORDER.
    previous = None
    for slot in doc.time_order:
        if slot.value is None:
            continue
        if previous is not None and previous.value is not None and slot.value < previous.value:
            problems.append(
                _warn(
                    "time-order",
                    f"time slot {slot.id!r} ({slot.value} ms) comes "
                    f"after {previous.id!r} ({previous.value} ms)",
                    slot.id,
                )
            )
        previous = slot
    # I3: every slot is used.
    used = {
        s for a in doc.annotations() if isinstance(a, AlignableAnnotation) for s in (a.begin, a.end)
    }
    for slot in doc.time_order:
        if slot not in used:
            problems.append(_warn("unused-slot", f"time slot {slot.id!r} is not used", slot.id))
    # I1: begin before end.
    position = {slot: index for index, slot in enumerate(doc.time_order)}
    for annotation in doc.annotations():
        if not isinstance(annotation, AlignableAnnotation):
            continue
        begin, end = annotation.begin, annotation.end
        if begin.value is not None and end.value is not None:
            bad = begin.value >= end.value
        else:
            bad = position.get(begin, -1) >= position.get(end, -1)
        if bad:
            problems.append(
                _warn(
                    "empty-interval",
                    f"annotation {annotation.id!r} does not end after it begins",
                    annotation.id,
                )
            )
    return problems


def _tiers(doc: Document, structure: Structure) -> list[Problem]:
    problems: list[Problem] = []
    for tier in doc.tiers:
        stereotype = doc.stereotype_of(tier)
        is_root = tier.parent_ref is None
        if doc.tier_type(tier.type_ref) is None:
            continue  # already reported
        if is_root and stereotype is not None:
            problems.append(
                _err(
                    "stereotype",
                    f"independent tier {tier.id!r} uses a type with constraint {stereotype.value}",
                    tier.id,
                )
            )
            continue
        if not is_root and stereotype is None:
            problems.append(
                _err(
                    "stereotype",
                    f"dependent tier {tier.id!r} uses a type without a constraint",
                    tier.id,
                )
            )
            continue
        alignable = stereotype is None or stereotype.alignable
        for annotation in tier.annotations:
            if alignable != isinstance(annotation, AlignableAnnotation):
                kind = "time-alignable" if alignable else "symbolic"
                problems.append(
                    _err(
                        "annotation-kind",
                        f"annotation {annotation.id!r} does not match {kind} tier {tier.id!r}",
                        annotation.id,
                    )
                )
        if not is_root:
            problems += _parents(tier, structure)
        if stereotype in (None, Stereotype.INCLUDED_IN):
            problems += _overlaps(tier, structure)
        if stereotype is Stereotype.TIME_SUBDIVISION:
            problems += _subdivision_coverage(tier, structure)
        if stereotype is Stereotype.SYMBOLIC_ASSOCIATION:
            counts = Counter(structure.parent.get(a) for a in tier.annotations)
            for parent, count in counts.items():
                if parent is not None and count > 1:
                    problems.append(
                        _err(
                            "association",
                            f"{count} annotations on {tier.id!r} refer to {parent.id!r}",
                            parent.id,
                        )
                    )
        if stereotype is Stereotype.SYMBOLIC_SUBDIVISION:
            for parent, chain in symbolic_order(tier, structure).items():
                heads = [a for a in chain if isinstance(a, RefAnnotation) and a.previous is None]
                if len(heads) != 1:
                    problems.append(
                        _warn(
                            "chain",
                            f"children of {parent.id!r} on {tier.id!r} do not form one chain",
                            parent.id,
                        )
                    )
    return problems


def _parents(tier: Tier, structure: Structure) -> list[Problem]:
    return [
        _err("no-parent", f"annotation {a.id!r} on {tier.id!r} has no parent annotation", a.id)
        for a in tier.annotations
        if a not in structure.parent
    ]


def _overlaps(tier: Tier, structure: Structure) -> list[Problem]:
    timed = sorted((structure.times[a], a.id) for a in tier.annotations if a in structure.times)
    problems: list[Problem] = []
    for (first, first_id), (second, second_id) in pairwise(timed):
        if second[0] < first[1]:
            problems.append(
                _warn(
                    "overlap",
                    f"annotations {first_id!r} and {second_id!r} on {tier.id!r} overlap",
                    first_id,
                    second_id,
                )
            )
    return problems


def _subdivision_coverage(tier: Tier, structure: Structure) -> list[Problem]:
    problems: list[Problem] = []
    groups: dict[Annotation, list[AlignableAnnotation]] = {}
    for annotation in tier.annotations:
        parent = structure.parent.get(annotation)
        if parent is not None and isinstance(annotation, AlignableAnnotation):
            groups.setdefault(parent, []).append(annotation)
    for parent, children in groups.items():
        if not isinstance(parent, AlignableAnnotation):
            continue
        # Compare times, not slot identity: ELAN shares slots, other tools may not.
        times = structure.times
        if parent not in times or any(child not in times for child in children):
            continue
        children.sort(key=lambda a: times[a])
        contiguous = all(times[a][1] == times[b][0] for a, b in pairwise(children))
        if (
            times[children[0]][0] != times[parent][0]
            or times[children[-1]][1] != times[parent][1]
            or not contiguous
        ):
            problems.append(
                _warn(
                    "subdivision-gap",
                    f"children of {parent.id!r} on {tier.id!r} do not cover it without gaps",
                    parent.id,
                )
            )
    return problems
