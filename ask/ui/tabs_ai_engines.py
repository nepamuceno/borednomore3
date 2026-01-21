import customtkinter as ctk
from tkinter import Listbox, END, SINGLE, messagebox
import webbrowser


class AITab(ctk.CTkFrame):
    """
    AI Engines manager tab.
    """

    def __init__(self, parent, state):
        super().__init__(parent)
        self.state = state

        # tkinter Listbox (CTk has no Listbox)
        self.listbox = Listbox(
            self,
            selectmode=SINGLE,
            activestyle="dotbox"
        )
        self.listbox.pack(fill="both", expand=True, padx=5, pady=5)

        buttons = ctk.CTkFrame(self)
        buttons.pack(fill="x", padx=5, pady=5)

        ctk.CTkButton(buttons, text="Add", command=self.add).pack(side="left", padx=2)
        ctk.CTkButton(buttons, text="Edit", command=self.edit).pack(side="left", padx=2)
        ctk.CTkButton(buttons, text="Delete", command=self.delete).pack(side="left", padx=2)
        ctk.CTkButton(buttons, text="Open", command=self.open).pack(side="left", padx=2)
        ctk.CTkButton(buttons, text="Copy URL", command=self.copy_url).pack(side="left", padx=2)

        self.refresh()

    def refresh(self):
        self.listbox.delete(0, END)
        for e in self.state.state.get("ai_engines", []):
            self.listbox.insert(END, f"{e['description']} | {e['url']}")

    def _get_index(self):
        sel = self.listbox.curselection()
        if not sel:
            return None
        return sel[0]

    def add(self):
        dialog = ctk.CTkInputDialog(
            title="Add AI Engine",
            text="Description | URL"
        )
        val = dialog.get_input()
        if not val or "|" not in val:
            return

        desc, url = [v.strip() for v in val.split("|", 1)]
        self.state.state["ai_engines"].append({
            "description": desc,
            "url": url
        })
        self.state.save()
        self.refresh()

    def edit(self):
        idx = self._get_index()
        if idx is None:
            messagebox.showwarning("AI Engines", "Select an engine first")
            return

        e = self.state.state["ai_engines"][idx]
        dialog = ctk.CTkInputDialog(
            title="Edit AI Engine",
            text="Description | URL",
            initialvalue=f"{e['description']} | {e['url']}"
        )
        val = dialog.get_input()
        if not val or "|" not in val:
            return

        desc, url = [v.strip() for v in val.split("|", 1)]
        e["description"] = desc
        e["url"] = url

        self.state.save()
        self.refresh()

    def delete(self):
        idx = self._get_index()
        if idx is None:
            return
        del self.state.state["ai_engines"][idx]
        self.state.save()
        self.refresh()

    def open(self):
        idx = self._get_index()
        if idx is None:
            return
        url = self.state.state["ai_engines"][idx]["url"]
        webbrowser.open(url)

    def copy_url(self):
        idx = self._get_index()
        if idx is None:
            return
        url = self.state.state["ai_engines"][idx]["url"]
        self.clipboard_clear()
        self.clipboard_append(url)
