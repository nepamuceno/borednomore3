import customtkinter as ctk
from tkinter import filedialog

class EditorToolbar(ctk.CTkFrame):
    def __init__(self, master, editor):
        super().__init__(master)

        ctk.CTkButton(self,text="Load",command=lambda:self.load(editor)).pack(side="left")
        ctk.CTkButton(self,text="Save As",command=lambda:self.save(editor)).pack(side="left")
        ctk.CTkButton(self,text="Undo",command=editor.edit_undo).pack(side="left")
        ctk.CTkButton(self,text="Redo",command=editor.edit_redo).pack(side="left")
        ctk.CTkButton(self,text="Clear",command=lambda:editor.delete("1.0","end")).pack(side="left")

    def load(self, editor):
        p = filedialog.askopenfilename()
        if p:
            editor.delete("1.0","end")
            editor.insert("1.0", open(p).read())

    def save(self, editor):
        p = filedialog.asksaveasfilename()
        if p:
            open(p,"w").write(editor.get("1.0","end"))

