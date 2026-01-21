def enable_autoscroll(textbox):
    def on_change(event):
        textbox.see("end")
        textbox.edit_modified(False)
    textbox.bind("<<Modified>>", on_change)

