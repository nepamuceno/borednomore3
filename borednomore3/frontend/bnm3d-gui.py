#!/usr/bin/env python3
"""
Borednomore3 Downloader GUI - Professional Edition
Frontend v0.1.7 - "Curating Your Digital Horizon"
Features: Dynamic Icon Generation, Persistent Console, Standard Favicon
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog
import os, sys, subprocess, threading, queue
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageTk

# Appearance
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

def create_dynamic_logo():
    """Generates the BNM3 logo in memory using PIL"""
    size = 128
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Gradient background circle
    for i in range(size//2, 0, -2):
        alpha = int(255 * (i / (size//2)))
        draw.ellipse([size//2 - i, size//2 - i, size//2 + i, size//2 + i], 
                     fill=(30, 144, 255, alpha))
    
    try:
        # Adjusted font size for "BNM3"
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
    except:
        font = ImageFont.load_default()
    
    text = "BNM3d"
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    pos = ((size - tw) // 2, (size - th) // 2 - 5)
    
    draw.text((pos[0] + 2, pos[1] + 2), text, fill=(0, 0, 0, 180), font=font)
    draw.text(pos, text, fill=(255, 255, 255, 255), font=font)
    
    return img

class ScrolledConsole(ctk.CTkTextbox):
    def __init__(self, master, max_lines=1000, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(state="disabled", wrap="none", font=("Consolas", 12))
        self.auto_scroll = True
        self.max_lines = max_lines
        
    def write(self, text):
        self.configure(state="normal")
        self.insert("end", text)
        current_lines = int(self.index('end-1c').split('.')[0])
        if current_lines > self.max_lines:
            cutoff = current_lines - self.max_lines
            self.delete("1.0", f"{cutoff}.0")
        if self.auto_scroll: self.see("end")
        self.configure(state="disabled")

    def clear(self):
        self.configure(state="normal")
        self.delete("1.0", "end")
        self.configure(state="disabled")

class BNM3DownloaderGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- Path Logic ---
        self.frontend_dir = Path(__file__).parent.resolve()
        self.project_root = self.frontend_dir.parent
        self.backend_dir = self.project_root / "backend"
        self.downloader_script = self.backend_dir / "bnm3d.py"
        self.config_dir = self.project_root / "conf"
        self.gui_state_file = self.config_dir / "gui_state.conf"

        # --- Window Setup ---
        self.title("BNM3D Pro")
        self.geometry("1200x850")
        
        # Apply the Dynamic Logo to the Window Icon
        self.logo_pil = create_dynamic_logo()
        self.logo_tk = ImageTk.PhotoImage(self.logo_pil)
        try:
            self.wm_iconphoto(True, self.logo_tk)
        except: pass

        # --- App State ---
        self.download_process = None
        self.output_queue = queue.Queue()
        self.is_running = False

        self.setup_grid()
        self.create_sidebar()
        self.create_main_view()
        self.create_console_area()
        self.load_gui_state()
        self.monitor_output()

    def setup_grid(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

    def create_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=300, corner_radius=0)
        self.sidebar.grid(row=0, column=0, rowspan=2, sticky="nsew")
        
        # Display the generated logo in the sidebar
        sidebar_logo_img = ctk.CTkImage(light_image=self.logo_pil, dark_image=self.logo_pil, size=(80, 80))
        self.logo_label = ctk.CTkLabel(self.sidebar, image=sidebar_logo_img, text="")
        self.logo_label.pack(pady=(20, 5))

        self.title_label = ctk.CTkLabel(self.sidebar, text="BNM3D PRO", font=ctk.CTkFont(size=20, weight="bold"))
        self.title_label.pack()
        self.slogan_label = ctk.CTkLabel(self.sidebar, text="Curating Your Digital Horizon", font=ctk.CTkFont(size=11, slant="italic"), text_color="#3498db")
        self.slogan_label.pack(pady=(0, 10))
        
        self.add_sidebar_label("SEARCH QUERY")
        self.search_var = ctk.StringVar(value="minimalist 4k")
        self.search_entry = ctk.CTkEntry(self.sidebar, textvariable=self.search_var)
        self.search_entry.pack(fill="x", padx=20, pady=5)

        self.add_sidebar_label("IMAGE COUNT")
        self.number_var = ctk.StringVar(value="10")
        self.number_entry = ctk.CTkEntry(self.sidebar, textvariable=self.number_var)
        self.number_entry.pack(fill="x", padx=20, pady=5)

        self.add_sidebar_label("SOURCE SELECTION")
        self.website_var = ctk.StringVar(value="all")
        self.source_menu = ctk.CTkOptionMenu(self.sidebar, values=["all", "pexels", "unsplash", "pixabay"], variable=self.website_var)
        self.source_menu.pack(fill="x", padx=20, pady=5)

        self.add_sidebar_label("CONFIG MODE (-m)")
        self.mode_var = ctk.StringVar(value="env")
        self.mode_menu = ctk.CTkOptionMenu(self.sidebar, values=["env", "conf", "keys"], variable=self.mode_var, command=lambda x: self.update_api_visibility())
        self.mode_menu.pack(fill="x", padx=20, pady=5)

        self.add_sidebar_label("MANUAL KEYS (Mode: keys)")
        self.pex_var = ctk.StringVar()
        self.pex_entry = ctk.CTkEntry(self.sidebar, textvariable=self.pex_var, placeholder_text="Pexels API Key", show="*")
        self.pex_entry.pack(fill="x", padx=20, pady=2)

        self.uns_var = ctk.StringVar()
        self.uns_entry = ctk.CTkEntry(self.sidebar, textvariable=self.uns_var, placeholder_text="Unsplash API Key", show="*")
        self.uns_entry.pack(fill="x", padx=20, pady=2)

        self.pix_var = ctk.StringVar()
        self.pix_entry = ctk.CTkEntry(self.sidebar, textvariable=self.pix_var, placeholder_text="Pixabay API Key", show="*")
        self.pix_entry.pack(fill="x", padx=20, pady=2)

        self.add_sidebar_label("CUSTOM CONFIG (-c)")
        self.config_path_var = ctk.StringVar(value=str(self.config_dir / "bnm3d.conf"))
        conf_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        conf_frame.pack(fill="x", padx=20, pady=5)
        self.conf_path_entry = ctk.CTkEntry(conf_frame, textvariable=self.config_path_var, font=("Consolas", 10))
        self.conf_path_entry.pack(side="left", fill="x", expand=True)
        self.conf_btn = ctk.CTkButton(conf_frame, text="...", width=30, command=self.browse_config)
        self.conf_btn.pack(side="right", padx=(5, 0))

        # Toggles
        self.deep_var = ctk.BooleanVar(value=False)
        self.deep_sw = ctk.CTkSwitch(self.sidebar, text="Deep Search (-D)", variable=self.deep_var)
        self.deep_sw.pack(anchor="w", padx=30, pady=8)
        self.rand_var = ctk.BooleanVar(value=False)
        self.rand_sw = ctk.CTkSwitch(self.sidebar, text="Randomize (-r)", variable=self.rand_var)
        self.rand_sw.pack(anchor="w", padx=30, pady=8)
        self.verb_var = ctk.BooleanVar(value=True)
        self.verb_sw = ctk.CTkSwitch(self.sidebar, text="Verbose (-v)", variable=self.verb_var)
        self.verb_sw.pack(anchor="w", padx=30, pady=8)
        self.debug_var = ctk.BooleanVar(value=True)
        self.debug_sw = ctk.CTkSwitch(self.sidebar, text="Debug (-d)", variable=self.debug_var)
        self.debug_sw.pack(anchor="w", padx=30, pady=8)

    def create_main_view(self):
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_container.grid_rowconfigure(1, weight=1)
        self.main_container.grid_columnconfigure(0, weight=1)

        self.ctrl_frame = ctk.CTkFrame(self.main_container, height=60)
        self.ctrl_frame.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        
        self.run_btn = ctk.CTkButton(self.ctrl_frame, text="START DOWNLOAD", fg_color="#2ecc71", hover_color="#27ae60", command=self.start_task)
        self.run_btn.pack(side="left", padx=15, pady=10, expand=True, fill="x")

        self.stop_btn = ctk.CTkButton(self.ctrl_frame, text="STOP", fg_color="#e67e22", state="disabled", command=self.stop_task)
        self.stop_btn.pack(side="left", padx=5, pady=10)

        self.kill_btn = ctk.CTkButton(self.ctrl_frame, text="KILL", fg_color="#e74c3c", state="disabled", command=self.kill_task)
        self.kill_btn.pack(side="left", padx=5, pady=10)

        self.clear_btn = ctk.CTkButton(self.ctrl_frame, text="CLEAR CONSOLE", fg_color="#7f8c8d", command=lambda: self.console.clear())
        self.clear_btn.pack(side="left", padx=5, pady=10)

        ctk.CTkButton(self.ctrl_frame, text="EXIT", fg_color="#34495e", command=self.quit).pack(side="left", padx=15, pady=10)

    def create_console_area(self):
        self.console_frame = ctk.CTkFrame(self.main_container)
        self.console_frame.grid(row=1, column=0, sticky="nsew")
        self.console_frame.grid_rowconfigure(1, weight=1)
        self.console_frame.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(self.console_frame, fg_color="#1a1a1a", height=40)
        header.grid(row=0, column=0, sticky="ew")
        ctk.CTkLabel(header, text="TERMINAL OUTPUT", font=ctk.CTkFont(size=11, weight="bold")).pack(side="left", padx=15)
        self.scroll_switch = ctk.CTkSwitch(header, text="Auto-scroll", font=ctk.CTkFont(size=10))
        self.scroll_switch.pack(side="right", padx=10)
        self.scroll_switch.select()

        self.console = ScrolledConsole(self.console_frame, max_lines=1000, border_width=1)
        self.console.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

    def add_sidebar_label(self, text):
        lbl = ctk.CTkLabel(self.sidebar, text=text, font=ctk.CTkFont(size=10, weight="bold"), text_color="gray70")
        lbl.pack(anchor="w", padx=20, pady=(15, 0))

    def update_api_visibility(self):
        state = "normal" if self.mode_var.get() == "keys" else "disabled"
        for entry in [self.pex_entry, self.uns_entry, self.pix_entry]:
            entry.configure(state=state)

    def save_gui_state(self):
        try:
            with open(self.gui_state_file, "w") as f:
                f.write(f"mode={self.mode_var.get()}\n")
                f.write(f"search={self.search_var.get()}\n")
                f.write(f"number={self.number_var.get()}\n")
                f.write(f"website={self.website_var.get()}\n")
                f.write(f"pex={self.pex_var.get()}\n")
                f.write(f"uns={self.uns_var.get()}\n")
                f.write(f"pix={self.pix_var.get()}\n")
                f.write(f"deep={int(self.deep_var.get())}\n")
                f.write(f"rand={int(self.rand_var.get())}\n")
                f.write(f"verb={int(self.verb_var.get())}\n")
                f.write(f"debug={int(self.debug_var.get())}\n")
                f.write(f"config={self.config_path_var.get()}\n")
        except: pass

    def load_gui_state(self):
        if not self.gui_state_file.exists(): return
        try:
            with open(self.gui_state_file, "r") as f:
                for line in f:
                    if "=" not in line: continue
                    k, v = line.strip().split("=", 1)
                    if k == "mode": self.mode_var.set(v)
                    elif k == "search": self.search_var.set(v)
                    elif k == "number": self.number_var.set(v)
                    elif k == "website": self.website_var.set(v)
                    elif k == "pex": self.pex_var.set(v)
                    elif k == "uns": self.uns_var.set(v)
                    elif k == "pix": self.pix_var.set(v)
                    elif k == "deep": self.deep_var.set(bool(int(v)))
                    elif k == "rand": self.rand_var.set(bool(int(v)))
                    elif k == "verb": self.verb_var.set(bool(int(v)))
                    elif k == "debug": self.debug_var.set(bool(int(v)))
                    elif k == "config": self.config_path_var.set(v)
            self.update_api_visibility()
        except: pass

    def browse_config(self):
        file = filedialog.askopenfilename(filetypes=[("Config files", "*.conf"), ("All files", "*.*")])
        if file: self.config_path_var.set(file)

    def start_task(self):
        if self.is_running: return
        self.save_gui_state()
        cmd = [sys.executable, "-u", str(self.downloader_script)]
        cmd += ["-m", self.mode_var.get()]
        cmd += ["-s", self.search_var.get()]
        cmd += ["-n", self.number_var.get()]
        cmd += ["-w", self.website_var.get()]
        if self.mode_var.get() == "conf": cmd += ["-c", self.config_path_var.get()]
        elif self.mode_var.get() == "keys":
            if self.pex_var.get().strip(): cmd += ["--pexels", self.pex_var.get().strip()]
            if self.uns_var.get().strip(): cmd += ["--unsplash", self.uns_var.get().strip()]
            if self.pix_var.get().strip(): cmd += ["--pixabay", self.pix_var.get().strip()]
        if self.deep_var.get(): cmd.append("-D")
        if self.rand_var.get(): cmd.append("-r")
        if self.verb_var.get(): cmd.append("-v")
        if self.debug_var.get(): cmd.append("-d")

        self.console.write(f"\n--- SESSION START: {' '.join(cmd)} ---\n\n")
        self.is_running = True
        self.toggle_ui(True)
        threading.Thread(target=self.execute_subprocess, args=(cmd,), daemon=True).start()

    def execute_subprocess(self, cmd):
        try:
            env = os.environ.copy()
            env["PYTHONUNBUFFERED"] = "1"
            self.download_process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
                text=True, bufsize=1, env=env, universal_newlines=True
            )
            while True:
                line = self.download_process.stdout.readline()
                if not line:
                    if self.download_process.poll() is not None: break
                    continue
                self.output_queue.put(line)
        except Exception as e:
            self.output_queue.put(f"[GUI ERROR] {str(e)}\n")
        finally:
            if self.download_process and self.download_process.stdout:
                self.download_process.stdout.close()
            self.is_running = False
            self.output_queue.put("PROCESS_EXITED")

    def monitor_output(self):
        self.console.auto_scroll = self.scroll_switch.get()
        try:
            while not self.output_queue.empty():
                line = self.output_queue.get_nowait()
                if line == "PROCESS_EXITED":
                    self.toggle_ui(False)
                    self.console.write("\n>>> [FINISHED] Session Ended.\n")
                else: 
                    self.console.write(line)
        except: pass
        self.after(20, self.monitor_output)

    def stop_task(self):
        if self.download_process: self.download_process.terminate()

    def kill_task(self):
        if self.download_process: self.download_process.kill()

    def toggle_ui(self, running):
        state = "disabled" if running else "normal"
        ctrls = [
            self.run_btn, self.search_entry, self.number_entry, 
            self.source_menu, self.mode_menu, self.conf_btn,
            self.deep_sw, self.rand_sw, self.verb_sw, self.debug_sw, self.clear_btn
        ]
        for w in ctrls:
            try: w.configure(state=state)
            except: pass
        self.stop_btn.configure(state="normal" if running else "disabled")
        self.kill_btn.configure(state="normal" if running else "disabled")
        if not running: self.update_api_visibility()

if __name__ == "__main__":
    app = BNM3DownloaderGUI()
    app.mainloop()
