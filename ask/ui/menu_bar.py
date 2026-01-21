import tkinter as tk
import customtkinter as ctk

def build_menu(root, state):
    menu = tk.Menu(root)

    app = tk.Menu(menu, tearoff=0)
    app.add_command(label="Exit", command=root.destroy)
    menu.add_cascade(label="App", menu=app)

    theme = tk.Menu(menu, tearoff=0)
    for t in ("Light", "Dark", "System"):
        theme.add_command(
            label=t,
            command=lambda x=t.lower(): (
                ctk.set_appearance_mode(x),
                state.set("theme", x)
            )
        )
    menu.add_cascade(label="Theme", menu=theme)

    root.config(menu=menu)

