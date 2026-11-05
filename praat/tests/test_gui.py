import pytest

pytest.importorskip("PySide6")
pytest.importorskip("pyqtgraph")

from PySide6.QtCore import Qt

from langtools_praat.gui.app import MainWindow
from langtools_praat.io.textgrid import read, write
from langtools_praat.model.textgrid import TextGrid


def test_gui_open_waveform_edit_save_reopen(qtbot, wav, tmp_path):
    grid_path = tmp_path / "phones.TextGrid"
    write(grid_path, TextGrid.create("phones", 0, 1, (("phones", "interval"), ("events", "point"))))
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    window.open_path(wav)
    window.open_path(grid_path)
    qtbot.waitUntil(
        lambda: window.curve.getData()[0] is not None and len(window.curve.getData()[0]) > 0,
        timeout=10000,
    )
    assert window.source.channels == 2
    assert window.table_model.rowCount() == 2  # empty point tier is selectable
    assert window.table_model.setData(window.table_model.index(0, 4), "ɲe\u0301")
    assert window.session.dirty
    assert window.session.document.tiers[0].intervals[0].label == "ɲe\u0301"
    assert window.undo_action.isEnabled()
    window.undo()
    assert not window.session.dirty
    window.redo()
    assert window.session.dirty
    tier = window.session.document.tiers[0]
    window.edit("annotation.split_interval", tier_id=tier.id, time=0.5, text_offset=1)
    window.select_annotation(0)
    assert window.region.getRegion() == (0, 0.5)
    output = tmp_path / "saved.TextGrid"
    window.workspace.save(window.session.document.id, output)
    assert [e.label for e in read(output).tiers[0].intervals] == ["ɲ", "e\u0301"]
    window.close()


def test_failed_file_open_keeps_workspace_and_revision(qtbot, wav, tmp_path):
    window = MainWindow()
    qtbot.addWidget(window)
    window.open_path(wav)
    original = tuple(window.workspace.objects)
    path = tmp_path / "invalid.TextGrid"
    path.write_text("invalid text", encoding="utf-8")
    with pytest.raises(ValueError):
        window.open_path(path)
    assert tuple(window.workspace.objects) == original
    window.close()


def test_stale_waveform_response_is_ignored(qtbot):
    import numpy as np

    from langtools_praat.media.waveform import Waveform

    window = MainWindow()
    qtbot.addWidget(window)
    window._token = 7
    window.wave_ready(6, Waveform(np.array([0.5]), np.array([-1]), np.array([1])))
    assert window.curve.getData()[0] is None
    window.close()


def test_dirty_close_can_cancel_and_preserves_labels(qtbot, tmp_path, monkeypatch):
    from PySide6.QtWidgets import QMessageBox

    path = tmp_path / "original.TextGrid"
    write(path, TextGrid.create("words", 0, 1, (("words", "interval"),)))
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    window.open_path(path)
    window.table_model.setData(window.table_model.index(0, 4), "edited", Qt.ItemDataRole.EditRole)
    monkeypatch.setattr(QMessageBox, "question", lambda *args: QMessageBox.StandardButton.Cancel)
    assert not window.close()
    assert window.session.document.tiers[0].intervals[0].label == "edited"
    assert read(path).tiers[0].intervals[0].label == ""
    monkeypatch.setattr(QMessageBox, "question", lambda *args: QMessageBox.StandardButton.Discard)
    window.close()


def test_native_label_editor_commits_and_keeps_selection(qtbot, tmp_path, monkeypatch):
    from PySide6.QtWidgets import QLineEdit

    path = tmp_path / "labels.TextGrid"
    write(path, TextGrid.create("words", 0, 1, (("words", "interval"),)))
    window = MainWindow()
    monkeypatch.setattr(window, "confirm_saved", lambda value: True)
    qtbot.addWidget(window)
    window.show()
    window.open_path(path)
    index = window.table_model.index(0, 4)
    window.table.setCurrentIndex(index)
    window.table.edit(index)
    editor = window.table.findChild(QLineEdit)
    assert editor is not None
    editor.setText("ɲe\u0301 😀")
    qtbot.keyClick(editor, Qt.Key.Key_Return)
    qtbot.waitUntil(lambda: window.session.document.tiers[0].intervals[0].label == "ɲe\u0301 😀")
    assert window.table.currentIndex().row() == 0
    window.workspace.save(window.session.document.id, path, overwrite=True)
    window.close()
