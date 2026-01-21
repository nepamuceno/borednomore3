from tkinter import filedialog

class ContextManager:
    def __init__(self, state):
        self.state = state

    def add(self):
        f = filedialog.askopenfilename()
        if f:
            self.state.append("context_files", f)

    def pin(self, f):
        self.state.append("pinned_context_files", f)

