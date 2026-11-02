"""Application entry point: ``elan-ng [--version] [--self-test]``."""

from __future__ import annotations

import argparse
import os
import sys

from elan_ng import APP_NAME, __version__


def self_test() -> int:
    """Start Qt, build the main window and check it, without user interaction.

    Used by CI to check that a packaged build can load Qt and its plugins. Runs on the
    offscreen platform unless QT_QPA_PLATFORM is already set.
    """
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication

    from elan_ng.ui.mainwindow import MainWindow
    from elan_ng.ui.menus import MENU_BAR, iter_items

    app = QApplication.instance() or QApplication([APP_NAME])
    window = MainWindow()
    window.show()
    app.processEvents()
    menus = [action.text() for action in window.menuBar().actions()]
    expected = [menu.text for menu in MENU_BAR]
    if menus != expected:
        print(f"self-test FAILED: menus {menus!r} != {expected!r}", file=sys.stderr)
        return 1
    missing = [item.id for item in iter_items() if item.id not in window.actions_by_id]
    if missing:
        print(f"self-test FAILED: missing actions {missing!r}", file=sys.stderr)
        return 1
    window.close()
    print(f"{APP_NAME} {__version__} self-test OK ({len(window.actions_by_id)} actions)")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog=APP_NAME)
    parser.add_argument("--version", action="version", version=f"{APP_NAME} {__version__}")
    parser.add_argument("--self-test", action="store_true", help="start, check the UI, and exit")
    args = parser.parse_args(argv)
    if args.self_test:
        return self_test()

    from PySide6.QtWidgets import QApplication

    from elan_ng.ui.mainwindow import MainWindow

    app = QApplication(sys.argv[:1])
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(__version__)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
