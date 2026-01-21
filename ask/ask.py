#!/usr/bin/env python3
import os
import customtkinter as ctk
from core.state_manager import StateManager
from core.history_manager import HistoryManager
from ui.main_window import MainWindow

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def main():
    state = StateManager(BASE_DIR)
    history = HistoryManager(BASE_DIR)

    ctk.set_appearance_mode(state.get("theme", "system"))
    app = MainWindow(state, history)
    app.mainloop()

    state.save()
    history.save()

if __name__ == "__main__":
    main()

