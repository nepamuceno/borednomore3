#!/usr/bin/env python3
"""
Ask Prompt Engine
Entry point
Python 3.12 compatible
"""

import sys
from datetime import datetime

from ui.main_window import MainWindow


def main() -> None:
    print(f"[{datetime.now()}] Ask starting...")
    print(f"[DEBUG] Python version: {sys.version}")

    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
