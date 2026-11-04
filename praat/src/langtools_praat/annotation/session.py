from dataclasses import replace

from ..errors import InvalidInput, StaleRevision
from ..model.textgrid import TextGrid
from .commands import Edit


class AnnotationSession:
    """Immutable snapshots make undo real; revisions stay monotonic through undo/redo."""

    def __init__(self, document: TextGrid):
        self._document = document
        self._saved = document
        self._undo: list[TextGrid] = []
        self._redo: list[TextGrid] = []

    @property
    def document(self) -> TextGrid:
        return self._document

    @property
    def dirty(self) -> bool:
        if self._saved is None:
            return True
        return replace(self.document, revision=self._saved.revision) != self._saved

    @property
    def can_undo(self) -> bool:
        return bool(self._undo)

    @property
    def can_redo(self) -> bool:
        return bool(self._redo)

    def mark_saved(self) -> None:
        self._saved = self.document

    def mark_unsaved(self) -> None:
        self._saved = None

    def rename(self, name: str) -> None:
        """Workspace name changes do not alter document content or undo history."""
        self._document = replace(self.document, name=name)
        if self._saved is not None:
            self._saved = replace(self._saved, name=name)
        self._undo = [replace(d, name=name) for d in self._undo]
        self._redo = [replace(d, name=name) for d in self._redo]

    def apply(self, edit: Edit, *, expected_revision: int) -> TextGrid:
        if expected_revision != self.document.revision:
            raise StaleRevision("Document changed; refresh before applying this edit.")
        updated = edit.apply(self.document)
        if updated == self.document:
            return self.document
        self._undo.append(self.document)
        self._redo.clear()
        self._document = replace(updated, revision=self.document.revision + 1)
        return self.document

    def undo(self) -> TextGrid:
        if not self._undo:
            raise InvalidInput("Nothing to undo.")
        self._redo.append(self.document)
        self._document = replace(self._undo.pop(), revision=self.document.revision + 1)
        return self.document

    def redo(self) -> TextGrid:
        if not self._redo:
            raise InvalidInput("Nothing to redo.")
        self._undo.append(self.document)
        self._document = replace(self._redo.pop(), revision=self.document.revision + 1)
        return self.document
