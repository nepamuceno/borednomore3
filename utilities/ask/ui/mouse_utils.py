def enable_scroll(widget):
    widget.bind("<MouseWheel>", lambda e: widget.yview_scroll(-1*(e.delta//120), "units"))
    widget.bind("<Button-4>", lambda e: widget.yview_scroll(-1,"units"))
    widget.bind("<Button-5>", lambda e: widget.yview_scroll(1,"units"))

