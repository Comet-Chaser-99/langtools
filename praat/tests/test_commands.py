import pytest

from langtools_praat.annotation.commands import InsertPoint, MoveBoundary, SetLabel, SplitInterval
from langtools_praat.annotation.session import AnnotationSession
from langtools_praat.application.workspace import Workspace
from langtools_praat.errors import InvalidInput, StaleRevision
from langtools_praat.model.textgrid import TextGrid


def session():
    return AnnotationSession(
        TextGrid.create("test", 3, 5, (("phones", "interval"), ("events", "point")))
    )


def test_unicode_split_undo_redo_and_monotonic_revision():
    target = session()
    tier = target.document.tiers[0]
    target.apply(SetLabel(tier.id, tier.intervals[0].id, "aɲ😀e\u0301"), expected_revision=0)
    target.mark_saved()
    before = target.document
    target.apply(SplitInterval(tier.id, 4, 3), expected_revision=1)
    assert [e.label for e in target.document.tiers[0].intervals] == ["aɲ😀", "e\u0301"]
    assert before.tiers[0].intervals[0].label == "aɲ😀e\u0301"
    assert target.dirty
    target.undo()
    assert target.document.revision == 3
    assert not target.dirty
    target.redo()
    assert target.document.revision == 4
    assert target.dirty


def test_failed_and_stale_commands_are_atomic():
    target = session()
    tier = target.document.tiers[0]
    original = target.document
    for edit in (SplitInterval(tier.id, 3), SplitInterval(tier.id, 4, 99)):
        with pytest.raises(InvalidInput):
            target.apply(edit, expected_revision=0)
        assert target.document is original
        assert not target.can_undo
    with pytest.raises(StaleRevision):
        target.apply(SplitInterval(tier.id, 4), expected_revision=10)
    assert target.document is original


def test_boundary_adjacency_and_duplicate_point_rejection():
    target = session()
    interval_id, point_id = (t.id for t in target.document.tiers)
    target.apply(SplitInterval(interval_id, 4), expected_revision=0)
    right = target.document.tiers[0].intervals[1]
    target.apply(MoveBoundary(interval_id, right.id, 4.25), expected_revision=1)
    left, right = target.document.tiers[0].intervals
    assert left.xmax == right.xmin == 4.25
    target.apply(InsertPoint(point_id, 4, "bell"), expected_revision=2)
    before = target.document
    with pytest.raises(InvalidInput):
        target.apply(InsertPoint(point_id, 4), expected_revision=3)
    assert target.document is before
    with pytest.raises(InvalidInput):
        target.apply(MoveBoundary(interval_id, right.id, 5), expected_revision=3)
    assert target.document is before


def test_edit_after_undo_discards_redo_without_renaming_back():
    target = session()
    tier = target.document.tiers[0]
    target.apply(SplitInterval(tier.id, 4), expected_revision=0)
    target.rename("renamed")
    target.undo()
    assert target.document.name == "renamed"
    target.apply(SetLabel(tier.id, tier.intervals[0].id, "new"), expected_revision=2)
    assert not target.can_redo


def test_workspace_duplicate_names_copy_lifecycle_and_save_failure(tmp_path):
    workspace = Workspace()
    first = workspace.add_annotation(session().document)
    second = workspace.add_annotation(session().document)
    assert first != second
    copied = workspace.copy(first)
    assert workspace.get(copied).dirty
    first_session = workspace.get(first)
    tier = first_session.document.tiers[0]
    workspace.execute(
        first,
        "annotation.set_label",
        expected_revision=0,
        tier_id=tier.id,
        entity_id=tier.intervals[0].id,
        label="hello",
    )
    assert workspace.get(second).document.tiers[0].intervals[0].label == ""
    assert workspace.get(copied).document.tiers[0].intervals[0].label == ""
    with pytest.raises(FileNotFoundError):
        workspace.save(first, tmp_path / "absent" / "x.TextGrid")
    assert first_session.dirty
    workspace.save(first, tmp_path / "ok.TextGrid")
    assert not first_session.dirty
    workspace.remove(first)
    with pytest.raises(InvalidInput):
        workspace.get(first)


def test_external_disk_change_does_not_overwrite_or_clear_dirty(tmp_path):
    from langtools_praat.io.textgrid import write

    path = tmp_path / "original.TextGrid"
    write(path, session().document)
    workspace = Workspace()
    object_id = workspace.open(path)
    target = workspace.get(object_id)
    tier = target.document.tiers[0]
    workspace.execute(
        object_id,
        "annotation.set_label",
        expected_revision=0,
        tier_id=tier.id,
        entity_id=tier.intervals[0].id,
        label="local edit",
    )
    path.write_text("someone else's version", encoding="utf-8")
    with pytest.raises(InvalidInput, match="changed on disk"):
        workspace.save(object_id, path, overwrite=True)
    assert path.read_text() == "someone else's version"
    assert target.dirty
    workspace.save(object_id, tmp_path / "recovered.TextGrid")
    assert not target.dirty
