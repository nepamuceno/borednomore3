import customtkinter as ctk
import tkinter as tk

class TextEditor(ctk.CTkTextbox):
    def __init__(self, master):
        super().__init__(master, wrap="word", undo=True)
        self.bind("<Button-3>", self.menu)

    def menu(self, e):
        m = tk.Menu(self, tearoff=0)
        m.add_command(label="Undo", command=self.edit_undo)
        m.add_command(label="Redo", command=self.edit_redo)
        m.add_separator()
        m.add_command(label="Copy", command=lambda:self.event_generate("<<Copy>>"))
        m.add_command(label="Paste", command=lambda:self.event_generate("<<Paste>>"))
        m.add_command(label="Select All", command=lambda:self.tag_add("sel","1.0","end"))
        m.tk_popup(e.x_root, e.y_root)

