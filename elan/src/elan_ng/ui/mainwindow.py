"""The document window (REIMPLEMENTATION.md §5.1). In M0 it only shows the menu bar."""

from __future__ import annotations

from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import QLabel, QMainWindow, QMenu, QMessageBox, QWidget

from elan_ng import APP_NAME, __version__
from elan_ng.ui.menus import MENU_BAR, Item, Menu, Separator

# Phases whose items have handlers in this build. Everything else is shown disabled,
# with its phase in the tooltip, so the full ELAN menu layout is visible from the start.
IMPLEMENTED_PHASES = frozenset({"M0"})


class MainWindow(QMainWindow):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(APP_NAME)
        self.resize(1200, 800)
        self.actions_by_id: dict[str, QAction] = {}
        self._build_menus()
        placeholder = QLabel("No document open")
        placeholder.setObjectName("placeholder")
        placeholder.setEnabled(False)
        placeholder.setMargin(24)
        self.setCentralWidget(placeholder)

        self.actions_by_id["file.exit"].triggered.connect(self.close)
        self.actions_by_id["help.about"].triggered.connect(self.show_about)

    def _build_menus(self) -> None:
        bar = self.menuBar()
        for menu in MENU_BAR:
            self._add_menu(bar.addMenu(menu.text), menu)

    def _add_menu(self, qmenu: QMenu, menu: Menu) -> None:
        if menu.phase and not menu.entries:
            qmenu.setEnabled(menu.phase in IMPLEMENTED_PHASES)
            qmenu.setToolTip(f"Planned: {menu.phase}")
        qmenu.setToolTipsVisible(True)
        for entry in menu.entries:
            if isinstance(entry, Separator):
                qmenu.addSeparator()
            elif isinstance(entry, Menu):
                self._add_menu(qmenu.addMenu(entry.text), entry)
            else:
                qmenu.addAction(self._make_action(entry))

    def _make_action(self, item: Item) -> QAction:
        action = QAction(item.text, self)
        action.setObjectName(item.id)
        if item.shortcut:
            action.setShortcut(QKeySequence(item.shortcut))
        enabled = item.phase in IMPLEMENTED_PHASES
        action.setEnabled(enabled)
        if not enabled:
            action.setToolTip(f"Planned: {item.phase}")
        if item.id == "file.exit":
            action.setMenuRole(QAction.MenuRole.QuitRole)
        elif item.id == "help.about":
            action.setMenuRole(QAction.MenuRole.AboutRole)
        else:
            action.setMenuRole(QAction.MenuRole.NoRole)
        self.actions_by_id[item.id] = action
        return action

    def show_about(self) -> None:
        QMessageBox.about(
            self,
            f"About {APP_NAME}",
            f"<b>{APP_NAME}</b> {__version__}<br>"
            "A cross-platform reimplementation of ELAN (working name).<br>"
            "Not affiliated with the Max Planck Institute for Psycholinguistics.",
        )
