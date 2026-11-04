from PySide6.QtCore import QAbstractTableModel, Qt, Signal

from ..annotation.session import AnnotationSession
from ..application.workspace import Workspace
from ..model.textgrid import IntervalTier


class AnnotationTable(QAbstractTableModel):
    content_changed = Signal()
    HEADERS = ("Tier", "Type", "Start (s)", "End (s)", "Label")

    def __init__(self, workspace: Workspace, parent=None):
        super().__init__(parent)
        self.workspace = workspace
        self.session: AnnotationSession | None = None
        self.rows = []

    def set_session(self, session: AnnotationSession | None):
        self.beginResetModel()
        self.session = session
        self.rows = []
        if session:
            for tier in session.document.tiers:
                entities = tier.intervals if isinstance(tier, IntervalTier) else tier.points
                # Keep empty point tiers visible/selectable for their first insertion.
                self.rows.extend((tier, item) for item in entities)
                if not entities:
                    self.rows.append((tier, None))
        self.endResetModel()

    def rowCount(self, parent=None):
        return 0 if parent is not None and parent.isValid() else len(self.rows)

    def columnCount(self, parent=None):
        return 0 if parent is not None and parent.isValid() else len(self.HEADERS)

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return self.HEADERS[section]
        return None

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or role not in (
            Qt.ItemDataRole.DisplayRole,
            Qt.ItemDataRole.EditRole,
        ):
            return None
        tier, item = self.rows[index.row()]
        interval = isinstance(tier, IntervalTier)
        if item is None:
            return (tier.name, "point (empty)", "", "", "")[index.column()]
        start = item.xmin if interval else item.time
        end = item.xmax if interval else item.time
        values = (
            tier.name,
            "interval" if interval else "point",
            repr(start),
            repr(end),
            item.label,
        )
        return values[index.column()]

    def flags(self, index):
        flags = super().flags(index)
        if index.isValid() and index.column() == 4 and self.rows[index.row()][1] is not None:
            flags |= Qt.ItemFlag.ItemIsEditable
        return flags

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        if (
            not index.isValid()
            or index.column() != 4
            or self.session is None
            or role != Qt.ItemDataRole.EditRole
        ):
            return False
        tier, entity = self.rows[index.row()]
        if entity is None:
            return False
        self.workspace.execute(
            self.session.document.id,
            "annotation.set_label",
            expected_revision=self.session.document.revision,
            tier_id=tier.id,
            entity_id=entity.id,
            label=str(value),
        )
        # Preserve table selection and the native editor during label-only changes.
        # Geometry edits use a model reset; label edits do not change row structure.
        updated_tier = next(t for t in self.session.document.tiers if t.id == tier.id)
        updated_entities = (
            updated_tier.intervals
            if isinstance(updated_tier, IntervalTier)
            else updated_tier.points
        )
        updated_by_id = {item.id: item for item in updated_entities}
        self.rows = [
            (updated_tier, updated_by_id[item.id])
            if old_tier.id == tier.id and item
            else (old_tier, item)
            for old_tier, item in self.rows
        ]
        self.dataChanged.emit(index, index)
        self.content_changed.emit()
        return True
