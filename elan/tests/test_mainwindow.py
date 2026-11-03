from pytestqt.qtbot import QtBot

from elan_ng.ui.mainwindow import MainWindow
from elan_ng.ui.menus import iter_items


def test_window_builds_full_menu_tree(qtbot: QtBot) -> None:
    window = MainWindow()
    qtbot.addWidget(window)
    assert set(window.actions_by_id) == {item.id for item in iter_items()}


def test_only_m0_items_are_enabled(qtbot: QtBot) -> None:
    window = MainWindow()
    qtbot.addWidget(window)
    enabled = {id_ for id_, action in window.actions_by_id.items() if action.isEnabled()}
    assert enabled == {"file.exit", "help.about"}


def test_shortcut_is_attached(qtbot: QtBot) -> None:
    window = MainWindow()
    qtbot.addWidget(window)
    assert window.actions_by_id["file.save"].shortcut().toString() == "Ctrl+S"


def test_exit_closes_window(qtbot: QtBot) -> None:
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    window.actions_by_id["file.exit"].trigger()
    assert not window.isVisible()
