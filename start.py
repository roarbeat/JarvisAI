"""
start.py  –  Jarvis Launcher
=============================
Startet die grafische Benutzeroberflaeche.
Alternativ direkt:  python gui.py

Verwendung:
    python start.py          -> GUI (Standard)
    python start.py --cli    -> Terminal (wie bisher jarvis.py)
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def start_gui():
    try:
        import customtkinter  # noqa: F401
    except ImportError:
        print()
        print("  ╔══════════════════════════════════════════════╗")
        print("  ║  customtkinter fehlt – bitte installieren:   ║")
        print("  ║                                              ║")
        print("  ║    pip install customtkinter                 ║")
        print("  ╚══════════════════════════════════════════════╝")
        print()
        input("  Enter zum Beenden...")
        sys.exit(1)

    from gui import JarvisApp
    print("\n  J A R V I S  –  Starte GUI...\n")
    app = JarvisApp()
    app.protocol("WM_DELETE_WINDOW", app._on_close)
    app.mainloop()


def start_cli():
    import jarvis
    jarvis.main()


if __name__ == "__main__":
    if "--cli" in sys.argv:
        start_cli()
    else:
        start_gui()
