"""PyInstaller entry script (PyInstaller needs a file, not a console-script name)."""

import sys

from elan_ng.app import main

sys.exit(main())
