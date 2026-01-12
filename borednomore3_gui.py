#!/usr/bin/env python3
import customtkinter as ctk
import threading
import os
import sys
import datetime
import subprocess
import time
from tkinter import filedialog

# Import backend logic
try:
    from borednomore3 import BoredNoMore3, VERSION, AUTHOR
    from borednomore3_transitions import TRANSITIONS
except ImportError:
    VERSION = "3.1.5"
    AUTHOR = "Deb"
    TRANSITIONS = {i: f"trans-{i}" for i in range(1, 41)}

class ConsoleRedirector:
    def __init__(self, textbox):
        self.textbox = textbox

    def write(self, text):
        self.textbox.configure(state="normal")
        self.textbox.insert("end", text)
        self.textbox.see("end")
        self.textbox.configure(state="disabled")

    def flush(self):
        pass

class NumberInput(ctk.CTkFrame):
    def __init__(self, master, label, default=5, step=1, min_val=1, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.step = step
        self.min_val = min_val
        self.lbl = ctk.CTkLabel(self, text=label, font=ctk.CTkFont(size=10, weight="bold"), text_color="#64748B")
        self.lbl.pack(side="top", anchor="w", pady=(0, 2))
        self.container = ctk.CTkFrame(self, fg_color="#1E293B", height=38, corner_radius=6)
        self.container.pack(fill="x")
        self.entry = ctk.CTkEntry(self.container, width=60, border_width=0, fg_color="transparent", 
                                  font=ctk.CTkFont(size=13, weight="bold"), justify="center")
        self.entry.insert(0, str(default))
        self.entry.pack(side="left", expand=True, fill="both")
        self.btn_f = ctk.CTkFrame(self.container, fg_color="transparent")
        self.btn_f.pack(side="right", padx=2)
        self.b1 = ctk.CTkButton(self.btn_f, text="+", width=22, height=16, fg_color="#334155", hover_color="#3B82F6", command=lambda: self.update_val(self.step))
        self.b1.pack(pady=1)
        self.b2 = ctk.CTkButton(self.btn_f, text="-", width=22, height=16, fg_color="#334155", hover_color="#3B82F6", command=lambda: self.update_val(-self.step))
        self.b2.pack(pady=1)

    def update_val(self, n):
        try:
            curr = float(self.entry.get())
            new_val = max(self.min_val, curr + n)
            self.entry.delete(0, "end")
            formatted = f"{new_val:.4f}".rstrip('0').rstrip('.') if n < 1 else str(int(new_val))
            self.entry.insert(0, formatted)
        except: self.entry.insert(0, str(self.min_val))

    def get(self):
        """Restored missing method to fix Critical Error"""
        return self.entry.get()

    def set_state(self, state):
        self.entry.configure(state=state)
        self.b1.configure(state=state)
        self.b2.configure(state=state)

class BoredMissionControl(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(f"BoredNoMore3 v{VERSION}")
        self.geometry("1400x950")
        self.configure(fg_color="#090E1A")
        self.app_instance = None
        self.start_time = None
        
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- Sidebar ---
        self.side = ctk.CTkFrame(self, width=320, corner_radius=0, fg_color="#111827")
        self.side.grid(row=0, column=0, sticky="nsew")
        
        ctk.CTkLabel(self.side, text="BoredNoMore3", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(30, 5))
        self.status_lbl = ctk.CTkLabel(self.side, text=f"SYSTEM READY", font=ctk.CTkFont(size=11, weight="bold"), text_color="#3B82F6")
        self.status_lbl.pack(pady=(0, 10))

        self.timer_lbl = ctk.CTkLabel(self.side, text="UPTIME: 00:00:00", font=ctk.CTkFont(family="monospace", size=12), text_color="#475569")
        self.timer_lbl.pack(pady=(0, 20))

        # Config Inputs
        self.path_var = ctk.StringVar(value=os.getcwd())
        self.folder_f = ctk.CTkFrame(self.side, fg_color="transparent")
        self.folder_f.pack(fill="x", padx=25, pady=(5, 15))
        self.path_entry = ctk.CTkEntry(self.folder_f, textvariable=self.path_var, height=35, font=ctk.CTkFont(size=11), fg_color="#1F2937", border_width=0)
        self.path_entry.pack(side="left", expand=True, fill="x", padx=(0, 5))
        self.browse_btn = ctk.CTkButton(self.folder_f, text="📂", width=35, height=35, fg_color="#374151", hover_color="#3B82F6", command=self.browse)
        self.browse_btn.pack(side="right")

        self.interval_ctrl = NumberInput(self.side, "INTERVAL (SEC)", 300, step=10, min_val=1)
        self.interval_ctrl.pack(padx=25, pady=8, fill="x")

        self.frames_ctrl = NumberInput(self.side, "ANIMATION DENSITY", 10, step=1, min_val=5)
        self.frames_ctrl.pack(padx=25, pady=8, fill="x")

        self.speed_ctrl = NumberInput(self.side, "TRANSITION SPEED", 0.001, step=0.001, min_val=0.0001)
        self.speed_ctrl.pack(padx=25, pady=8, fill="x")

        self.rand_switch = ctk.CTkSwitch(self.side, text="Randomize Sequence", progress_color="#3B82F6")
        self.rand_switch.pack(pady=15); self.rand_switch.select()

        self.start_btn = ctk.CTkButton(self.side, text="INITIALIZE ENGINE", height=50, fg_color="#3B82F6", font=ctk.CTkFont(weight="bold"), command=self.start)
        self.start_btn.pack(padx=25, pady=5, fill="x")

        self.stop_btn = ctk.CTkButton(self.side, text="STOP ENGINE", height=50, fg_color="transparent", border_width=1, border_color="#334155", text_color="#94A3B8", state="disabled", command=self.stop)
        self.stop_btn.pack(padx=25, pady=5, fill="x")

        ctk.CTkButton(self.side, text="EXIT PROGRAM", height=45, fg_color="#EF4444", hover_color="#B91C1C", font=ctk.CTkFont(weight="bold"), command=self.quit_app).pack(side="bottom", padx=25, pady=20, fill="x")

        # --- Main View ---
        self.main = ctk.CTkFrame(self, fg_color="transparent")
        self.main.grid(row=0, column=1, sticky="nsew", padx=30, pady=20)

        # Help / Credits / Version Bar
        self.cmd_bar = ctk.CTkFrame(self.main, fg_color="#111827", height=50, corner_radius=10)
        self.cmd_bar.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(self.cmd_bar, text="SYSTEM TOOLS", font=ctk.CTkFont(size=12, weight="bold"), text_color="#3B82F6").pack(side="left", padx=20)
        
        self.cmd_btns = []
        for label, flag in [("HELP", "-h"), ("CREDITS", "-c"), ("VERSION", "-v")]:
            b = ctk.CTkButton(self.cmd_bar, text=label, width=90, height=30, fg_color="#1E293B", text_color="#94A3B8", font=ctk.CTkFont(size=11, weight="bold"), command=lambda f=flag: self.run_external_cmd(f))
            b.pack(side="right", padx=10)
            self.cmd_btns.append(b)

        header_f = ctk.CTkFrame(self.main, fg_color="transparent")
        header_f.pack(fill="x", pady=(0, 10))
        self.matrix_lbl = ctk.CTkLabel(header_f, text="TRANSITION MATRIX", font=ctk.CTkFont(size=14, weight="bold"), text_color="#475569")
        self.matrix_lbl.pack(side="left")

        # Matrix Utilities
        self.util_f = ctk.CTkFrame(header_f, fg_color="transparent")
        self.util_f.pack(side="right")
        self.all_btn = ctk.CTkButton(self.util_f, text="SELECT ALL", width=80, height=24, fg_color="#1E293B", font=ctk.CTkFont(size=10), command=lambda: self.bulk_matrix(True))
        self.all_btn.pack(side="left", padx=5)
        self.none_btn = ctk.CTkButton(self.util_f, text="CLEAR", width=60, height=24, fg_color="#1E293B", font=ctk.CTkFont(size=10), command=lambda: self.bulk_matrix(False))
        self.none_btn.pack(side="left", padx=5)

        self.grid_frame = ctk.CTkFrame(self.main, fg_color="#111827", corner_radius=12, border_width=1, border_color="#1F2937")
        self.grid_frame.pack(fill="both", expand=False, padx=2, pady=2)
        for c in range(5): self.grid_frame.grid_columnconfigure(c, weight=1)

        self.trans_vars = {}
        self.check_boxes = []
        for i, (num, name) in enumerate(TRANSITIONS.items()):
            var = ctk.BooleanVar(value=True)
            cb = ctk.CTkCheckBox(self.grid_frame, text=f"{num}: {name.upper()}", variable=var, 
                                 font=ctk.CTkFont(family="Consolas", size=9), checkbox_width=14, checkbox_height=14)
            cb.grid(row=i // 5, column=i % 5, padx=8, pady=8, sticky="w")
            self.trans_vars[num] = var
            self.check_boxes.append(cb)

        # Output Console
        console_header = ctk.CTkFrame(self.main, fg_color="transparent")
        console_header.pack(fill="x", pady=(20, 5))
        ctk.CTkLabel(console_header, text="ENGINE CONSOLE", font=ctk.CTkFont(size=11, weight="bold"), text_color="#475569").pack(side="left")
        
        self.export_btn = ctk.CTkButton(console_header, text="EXPORT LOG", width=80, height=20, fg_color="transparent", text_color="#3B82F6", font=ctk.CTkFont(size=10), command=self.export_log)
        self.export_btn.pack(side="right")

        self.console = ctk.CTkTextbox(self.main, fg_color="#05070A", border_width=1, border_color="#1F2937", text_color="#10B981", font=ctk.CTkFont(family="monospace", size=12))
        self.console.pack(fill="both", expand=True)
        self.console.configure(state="disabled")
        
        sys.stdout = ConsoleRedirector(self.console)
        self.update_clock()

    def update_clock(self):
        if self.start_time:
            elapsed = int(time.time() - self.start_time)
            self.timer_lbl.configure(text=f"UPTIME: {time.strftime('%H:%M:%S', time.gmtime(elapsed))}")
        self.after(1000, self.update_clock)

    def bulk_matrix(self, state):
        for cb in self.check_boxes:
            if state: cb.select()
            else: cb.deselect()

    def set_gui_state(self, state):
        s = "normal" if state else "disabled"
        self.path_entry.configure(state=s)
        self.browse_btn.configure(state=s)
        self.interval_ctrl.set_state(s)
        self.frames_ctrl.set_state(s)
        self.speed_ctrl.set_state(s)
        self.rand_switch.configure(state=s)
        self.start_btn.configure(state=s)
        self.all_btn.configure(state=s)
        self.none_btn.configure(state=s)
        for cb in self.check_boxes: cb.configure(state=s)
        for b in self.cmd_btns: b.configure(state=s)

    def run_external_cmd(self, flag):
        def execute():
            # EXACT MODIFICATION: Captured output to print it to the ConsoleRedirector
            cmd = [sys.executable, "borednomore3.py", flag] if os.path.exists("borednomore3.py") else ["borednomore3", flag]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.stdout: print(result.stdout)
            if result.stderr: print(result.stderr)
        threading.Thread(target=execute, daemon=True).start()

    def export_log(self):
        content = self.console.get("1.0", "end")
        with open("engine_log.txt", "w") as f:
            f.write(content)
        print("[*] Log exported to engine_log.txt")

    def browse(self):
        path = filedialog.askdirectory()
        if path: self.path_var.set(path)

    def quit_app(self):
        if self.app_instance: self.app_instance.should_exit = True
        self.destroy(); sys.exit(0)

    def start(self):
        self.set_gui_state(False)
        self.start_time = time.time()
        self.status_lbl.configure(text="ENGINE STATUS: ACTIVE", text_color="#10B981")
        self.stop_btn.configure(state="normal", text_color="#EF4444", border_color="#EF4444")
        
        selected_t = [int(n) for n, v in self.trans_vars.items() if v.get()]
        self.thread = threading.Thread(target=self.logic, args=(selected_t,), daemon=True)
        self.thread.start()

    def stop(self):
        if self.app_instance: self.app_instance.should_exit = True
        self.set_gui_state(True)
        self.start_time = None
        self.status_lbl.configure(text="ENGINE STATUS: STANDBY", text_color="#3B82F6")
        self.stop_btn.configure(state="disabled", text_color="#94A3B8", border_color="#334155")
        print("\n[!] Engine service terminated.")

    def logic(self, t_list):
        try:
            self.app_instance = BoredNoMore3(
                interval=int(self.interval_ctrl.get()),
                directory=self.path_var.get(),
                frames=int(self.frames_ctrl.get()),
                fade_speed=float(self.speed_ctrl.get()),
                transitions=t_list,
                randomize=self.rand_switch.get()
            )
            self.app_instance.run()
        except Exception as e: print(f"CRITICAL ERROR: {e}")
        finally: self.stop()

if __name__ == "__main__":
    app = BoredMissionControl()
    app.mainloop()
