import customtkinter as ctk
import json
import webbrowser
from pathlib import Path

ENGINES_FILE = Path("ai_engines.json")

class EngineEditor(ctk.CTkScrollableFrame):
    def __init__(self, master):
        super().__init__(master)
        self.load()

    def load(self):
        self.engines = json.loads(ENGINES_FILE.read_text())
        self.render()

    def render(self):
        for w in self.winfo_children():
            w.destroy()

        for idx, engine in enumerate(self.engines):
            url = ctk.CTkEntry(self)
            url.insert(0, engine["url"])
            url.pack(fill="x")

            desc = ctk.CTkEntry(self)
            desc.insert(0, engine["description"])
            desc.pack(fill="x")

            url.bind("<KeyRelease>", lambda e,i=idx: self.update(i))
            desc.bind("<KeyRelease>", lambda e,i=idx: self.update(i))

            ctk.CTkButton(
                self, text="Open",
                command=lambda u=engine["url"]: webbrowser.open(u)
            ).pack(pady=2)

    def update(self, idx):
        children = self.winfo_children()
        self.engines[idx]["url"] = children[idx*3].get()
        self.engines[idx]["description"] = children[idx*3+1].get()
        ENGINES_FILE.write_text(json.dumps(self.engines, indent=2))

