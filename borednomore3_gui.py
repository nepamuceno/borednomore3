#!/usr/bin/env python3
import customtkinter as ctk
import threading
import os
import sys
import subprocess
import time
import signal
import configparser
from tkinter import filedialog, Text
from pathlib import Path
# --- VERSION METADATA ---
VERSION = "3.3.0"
AUTHOR = "Deb"
# --- DEFAULT CONFIGURATION ---
DEFAULT_CONFIG = {
    'interval': 300,
    'directory': os.getcwd(),
    'frames': 10,
    'speed': 0.001,
    'transitions': '',
    'randomize': True,
    'keep_image': False,
    'borednomore3_binary': 'borednomore3',
    'config_file': 'borednomore3.conf'
}
# --- PID MANAGEMENT ---
PID_FILE = "/tmp/borednomore3.pid"
def save_pid(pid):
    """Save process PID to file."""
    try:
        with open(PID_FILE, "w") as f:
            f.write(str(pid))
        return True
    except Exception as e:
        print(f"[ERROR] Failed to save PID: {e}")
        return False
def get_saved_pid():
    """Retrieve saved PID from file."""
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE, "r") as f:
                return int(f.read().strip())
        except Exception as e:
            print(f"[WARNING] Could not read PID file: {e}")
            return None
    return None
def is_pid_running(pid):
    """Check if a process with the given PID is running."""
    if pid is None:
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False
def kill_process(pid):
    """Terminate a process by PID."""
    if pid is None:
        return False
    try:
        os.kill(pid, signal.SIGTERM)
        time.sleep(0.5)
      
        if is_pid_running(pid):
            os.kill(pid, signal.SIGKILL)
            time.sleep(0.3)
      
        return not is_pid_running(pid)
    except Exception as e:
        print(f"[ERROR] Failed to kill process {pid}: {e}")
        return False
def cleanup_pid_file():
    """Remove PID file."""
    try:
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
    except Exception as e:
        print(f"[WARNING] Could not remove PID file: {e}")
# --- CONFIG FILE MANAGEMENT ---
def load_config_file(config_path):
    """Load configuration from file"""
    config = {}
    if not os.path.exists(config_path):
        return config
  
    try:
        parser = configparser.ConfigParser()
        parser.read(config_path)
      
        if 'settings' in parser:
            settings = parser['settings']
          
            if 'interval' in settings:
                config['interval'] = int(settings['interval'])
            if 'directory' in settings:
                config['directory'] = settings['directory']
            if 'frames' in settings:
                config['frames'] = int(settings['frames'])
            if 'speed' in settings:
                config['speed'] = float(settings['speed'])
            if 'transitions' in settings:
                config['transitions'] = settings['transitions']
            if 'randomize' in settings:
                config['randomize'] = settings.getboolean('randomize')
            if 'keep_image' in settings:
                config['keep_image'] = settings.getboolean('keep_image')
            if 'borednomore3_binary' in settings:
                config['borednomore3_binary'] = settings['borednomore3_binary']
      
        return config
    except Exception as e:
        print(f"[WARNING] Error loading config file: {e}")
        return config
def save_config_file(config_path, config):
    """Save configuration to file"""
    try:
        parser = configparser.ConfigParser()
        parser['settings'] = {
            'interval': str(config['interval']),
            'directory': config['directory'],
            'frames': str(config['frames']),
            'speed': str(config['speed']),
            'transitions': config['transitions'],
            'randomize': str(config['randomize']),
            'keep_image': str(config['keep_image']),
            'borednomore3_binary': config['borednomore3_binary']
        }
      
        with open(config_path, 'w') as f:
            parser.write(f)
      
        print(f"[*] Configuration saved to: {config_path}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to save config: {e}")
        return False
# --- LOG REDIRECTION ---
class ConsoleRedirector:
    """Redirect stdout/stderr to GUI console."""
    def __init__(self, textbox):
        self.textbox = textbox
        self.buffer = []
    def write(self, text):
        if text.strip():
            try:
                self.textbox.configure(state="normal")
                self.textbox.insert("end", text + "\n")
                self.textbox.see("end")
                self.textbox.configure(state="disabled")
            except Exception:
                pass
    def flush(self):
        pass
# --- CUSTOM WIDGETS ---
class NumberInput(ctk.CTkFrame):
    """Custom numeric input with increment/decrement buttons."""
    def __init__(self, master, label, default=5, step=1, min_val=1, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.step = step
        self.min_val = min_val
      
        self.lbl = ctk.CTkLabel(
            self, text=label,
            font=ctk.CTkFont(size=8, weight="bold"),
            text_color="#64748B"
        )
        self.lbl.pack(side="top", anchor="w", pady=(0, 1))
      
        self.container = ctk.CTkFrame(
            self, fg_color="#1E293B",
            height=28, corner_radius=5
        )
        self.container.pack(fill="x")
      
        self.entry = ctk.CTkEntry(
            self.container, width=50,
            border_width=0, fg_color="transparent",
            font=ctk.CTkFont(size=10, weight="bold"),
            justify="center"
        )
        self.entry.insert(0, str(default))
        self.entry.pack(side="left", expand=True, fill="both", padx=3)
      
        self.btn_f = ctk.CTkFrame(self.container, fg_color="transparent")
        self.btn_f.pack(side="right", padx=1)
      
        self.b1 = ctk.CTkButton(
            self.btn_f, text="+", width=18, height=12,
            fg_color="#334155", hover_color="#3B82F6",
            command=lambda: self.update_val(self.step)
        )
        self.b1.pack(pady=1)
      
        self.b2 = ctk.CTkButton(
            self.btn_f, text="-", width=18, height=12,
            fg_color="#334155", hover_color="#3B82F6",
            command=lambda: self.update_val(-self.step)
        )
        self.b2.pack(pady=1)
    def update_val(self, n):
        try:
            curr = float(self.entry.get())
            new_val = max(self.min_val, curr + n)
            self.entry.delete(0, "end")
            if self.step < 1:
                formatted = f"{new_val:.4f}".rstrip('0').rstrip('.')
            else:
                formatted = str(int(new_val))
            self.entry.insert(0, formatted)
        except ValueError:
            self.entry.delete(0, "end")
            self.entry.insert(0, str(self.min_val))
    def get(self):
        return self.entry.get()
    def set(self, value):
        self.entry.delete(0, "end")
        self.entry.insert(0, str(value))
    def set_state(self, state):
        self.entry.configure(state=state)
        self.b1.configure(state=state)
        self.b2.configure(state=state)
# --- MAIN GUI ---
class BoredMissionControl(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(f"BoredNoMore3 Mission Control v{VERSION}")
        self.configure(fg_color="#090E1A")
      
        # Dynamic responsive geometry based on screen size
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        width = int(screen_width * 0.8)  # 80% of screen width
        height = int(screen_height * 0.8)  # 80% of screen height
        width = max(1000, min(width, 1400))  # Clamp between 1000-1400
        height = max(600, min(height, 950))  # Clamp between 600-950
        self.geometry(f"{width}x{height}")
      
        # Center the window
        self.update_idletasks()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
      
        # Process Management
        self.bg_process_pid = None
        self.log_monitor_thread = None
        self.monitoring = False
        self.start_time = None
        self.log_file = "/tmp/borednomore3.log"
      
        # Configuration
        self.config = DEFAULT_CONFIG.copy()
        self.config_file_path = 'borednomore3.conf'
      
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        # Setup UI
        self.setup_ui()
      
        # Load configuration if exists
        self.load_configuration()
      
        # Check if engine is already running from previous session
        self.check_existing_engine()
      
        # Handle window close event
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
    def setup_ui(self):
        """Build the complete GUI."""
        # --- Sidebar ---
        self.side = ctk.CTkFrame(self, width=280, corner_radius=0, fg_color="#111827")
        self.side.grid(row=0, column=0, rowspan=1, sticky="nsew")
      
        ctk.CTkLabel(
            self.side, text="BoredNoMore3",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#3B82F6"
        ).pack(pady=(15, 2))
      
        self.status_lbl = ctk.CTkLabel(
            self.side, text="STATUS: STANDBY",
            font=ctk.CTkFont(size=9, weight="bold"),
            text_color="#3B82F6"
        )
        self.status_lbl.pack(pady=(0, 2))
        self.pid_lbl = ctk.CTkLabel(
            self.side, text="PID: N/A",
            font=ctk.CTkFont(family="monospace", size=8),
            text_color="#475569"
        )
        self.pid_lbl.pack(pady=(0, 2))
        self.timer_lbl = ctk.CTkLabel(
            self.side, text="UPTIME: 00:00:00",
            font=ctk.CTkFont(family="monospace", size=9),
            text_color="#475569"
        )
        self.timer_lbl.pack(pady=(0, 4))
        # Configuration File Selection
        config_f = ctk.CTkFrame(self.side, fg_color="transparent")
        config_f.pack(fill="x", padx=15, pady=(2, 3))
      
        ctk.CTkLabel(
            config_f, text="CONFIG FILE",
            font=ctk.CTkFont(size=8, weight="bold"),
            text_color="#64748B"
        ).pack(side="top", anchor="w", pady=(0, 1))
      
        config_input_f = ctk.CTkFrame(config_f, fg_color="transparent")
        config_input_f.pack(fill="x")
      
        self.config_var = ctk.StringVar(value=self.config_file_path)
        self.config_entry = ctk.CTkEntry(
            config_input_f, textvariable=self.config_var,
            height=26, font=ctk.CTkFont(size=8),
            fg_color="#1F2937", border_width=0
        )
        self.config_entry.pack(side="left", expand=True, fill="x", padx=(0, 3))
      
        self.config_browse_btn = ctk.CTkButton(
            config_input_f, text="📁", width=26, height=26,
            fg_color="#374151", hover_color="#3B82F6",
            command=self.browse_config
        )
        self.config_browse_btn.pack(side="right")
        # Load/Save Config Buttons
        config_btn_f = ctk.CTkFrame(self.side, fg_color="transparent")
        config_btn_f.pack(fill="x", padx=15, pady=(0, 4))
      
        self.load_config_btn = ctk.CTkButton(
            config_btn_f, text="LOAD CONFIG",
            height=22, fg_color="#1E293B",
            hover_color="#3B82F6",
            font=ctk.CTkFont(size=8),
            command=self.load_configuration
        )
        self.load_config_btn.pack(side="left", expand=True, fill="x", padx=(0, 2))
      
        self.save_config_btn = ctk.CTkButton(
            config_btn_f, text="SAVE CONFIG",
            height=22, fg_color="#1E293B",
            hover_color="#10B981",
            font=ctk.CTkFont(size=8),
            command=self.save_configuration
        )
        self.save_config_btn.pack(side="right", expand=True, fill="x", padx=(2, 0))
        # Directory Selection
        self.path_var = ctk.StringVar(value=self.config['directory'])
        dir_f = ctk.CTkFrame(self.side, fg_color="transparent")
        dir_f.pack(fill="x", padx=15, pady=(2, 3))
      
        ctk.CTkLabel(
            dir_f, text="WALLPAPER DIRECTORY",
            font=ctk.CTkFont(size=8, weight="bold"),
            text_color="#64748B"
        ).pack(side="top", anchor="w", pady=(0, 1))
      
        folder_input_f = ctk.CTkFrame(dir_f, fg_color="transparent")
        folder_input_f.pack(fill="x")
      
        self.path_entry = ctk.CTkEntry(
            folder_input_f, textvariable=self.path_var,
            height=28, font=ctk.CTkFont(size=9),
            fg_color="#1F2937", border_width=0
        )
        self.path_entry.pack(side="left", expand=True, fill="x", padx=(0, 3))
      
        self.browse_btn = ctk.CTkButton(
            folder_input_f, text="📂", width=28, height=28,
            fg_color="#374151", hover_color="#3B82F6",
            command=self.browse
        )
        self.browse_btn.pack(side="right")
        # Control Inputs
        self.interval_ctrl = NumberInput(
            self.side, "INTERVAL (SEC)", self.config['interval'], step=10, min_val=1
        )
        self.interval_ctrl.pack(padx=15, pady=3, fill="x")
        self.frames_ctrl = NumberInput(
            self.side, "ANIMATION DENSITY", self.config['frames'], step=1, min_val=5
        )
        self.frames_ctrl.pack(padx=15, pady=3, fill="x")
        self.speed_ctrl = NumberInput(
            self.side, "TRANSITION SPEED", self.config['speed'], step=0.001, min_val=0.0001
        )
        self.speed_ctrl.pack(padx=15, pady=3, fill="x")
        # Binary Path Selection
        binary_f = ctk.CTkFrame(self.side, fg_color="transparent")
        binary_f.pack(fill="x", padx=15, pady=(3, 3))
      
        ctk.CTkLabel(
            binary_f, text="BACKEND BINARY",
            font=ctk.CTkFont(size=8, weight="bold"),
            text_color="#64748B"
        ).pack(side="top", anchor="w", pady=(0, 1))
      
        self.binary_var = ctk.StringVar(value=self.config['borednomore3_binary'])
        self.binary_entry = ctk.CTkEntry(
            binary_f, textvariable=self.binary_var,
            height=26, font=ctk.CTkFont(size=9),
            fg_color="#1F2937", border_width=0
        )
        self.binary_entry.pack(fill="x")
        # Switches
        self.rand_switch = ctk.CTkSwitch(
            self.side, text="Randomize Sequence",
            progress_color="#3B82F6",
            font=ctk.CTkFont(size=9)
        )
        self.rand_switch.pack(pady=3)
        if self.config['randomize']:
            self.rand_switch.select()
        self.keep_image_switch = ctk.CTkSwitch(
            self.side, text="Keep Image Mode",
            progress_color="#10B981",
            font=ctk.CTkFont(size=9)
        )
        self.keep_image_switch.pack(pady=2)
        if self.config['keep_image']:
            self.keep_image_switch.select()
        # Action Buttons
        self.start_btn = ctk.CTkButton(
            self.side, text="INITIALIZE ENGINE",
            height=36, fg_color="#3B82F6",
            hover_color="#2563EB",
            font=ctk.CTkFont(weight="bold", size=11),
            command=self.start_engine
        )
        self.start_btn.pack(padx=15, pady=2, fill="x")
        self.stop_btn = ctk.CTkButton(
            self.side, text="STOP ENGINE",
            height=36, fg_color="transparent",
            border_width=2, border_color="#334155",
            text_color="#94A3B8", hover_color="#DC2626",
            state="disabled", command=self.stop_engine,
            font=ctk.CTkFont(size=11)
        )
        self.stop_btn.pack(padx=15, pady=2, fill="x")
        # Red "End Program" button - now below STOP ENGINE, kills backend and exits
        self.end_program_btn = ctk.CTkButton(
            self.side, text="End Program",
            height=36, fg_color="#EF4444",
            hover_color="#B91C1C",
            font=ctk.CTkFont(weight="bold", size=11),
            command=self.end_program
        )
        self.end_program_btn.pack(padx=15, pady=2, fill="x")
        # --- Main View ---
        self.main = ctk.CTkFrame(self, fg_color="transparent")
        self.main.grid(row=0, column=1, sticky="nsew", padx=15, pady=5)
        # Command Bar
        self.cmd_bar = ctk.CTkFrame(self.main, fg_color="#111827", height=36, corner_radius=6)
        self.cmd_bar.pack(fill="x", pady=(0, 5))
      
        ctk.CTkLabel(
            self.cmd_bar, text="SYSTEM TOOLS",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="#3B82F6"
        ).pack(side="left", padx=10)
      
        self.cmd_btns = []
        for label, flag in [("VERSION", "-v"), ("CREDITS", "-c"), ("HELP", "-h")]:
            b = ctk.CTkButton(
                self.cmd_bar, text=label, width=70, height=22,
                fg_color="#1E293B", hover_color="#3B82F6",
                text_color="#94A3B8",
                font=ctk.CTkFont(size=9, weight="bold"),
                command=lambda f=flag: self.run_external_cmd(f)
            )
            b.pack(side="right", padx=3)
            self.cmd_btns.append(b)
        # Transition Matrix Header
        header_f = ctk.CTkFrame(self.main, fg_color="transparent")
        header_f.pack(fill="x", pady=(0, 3))
      
        ctk.CTkLabel(
            header_f, text="TRANSITION MATRIX",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#E2E8F0"
        ).pack(side="left")
        self.util_f = ctk.CTkFrame(header_f, fg_color="transparent")
        self.util_f.pack(side="right")
      
        self.all_btn = ctk.CTkButton(
            self.util_f, text="SELECT ALL",
            width=60, height=18, fg_color="#1E293B",
            hover_color="#3B82F6",
            font=ctk.CTkFont(size=8),
            command=lambda: self.bulk_matrix(True)
        )
        self.all_btn.pack(side="left", padx=3)
      
        self.none_btn = ctk.CTkButton(
            self.util_f, text="UNSELECT ALL",
            width=70, height=18, fg_color="#1E293B",
            hover_color="#EF4444",
            font=ctk.CTkFont(size=8),
            command=lambda: self.bulk_matrix(False)
        )
        self.none_btn.pack(side="left", padx=3)
        # Transition Grid
        self.grid_frame = ctk.CTkScrollableFrame(
            self.main, fg_color="#111827",
            corner_radius=8, border_width=1,
            border_color="#1F2937",
            height=180,
            scrollbar_button_color="#3B82F6",
            scrollbar_button_hover_color="#2563EB"
        )
        self.grid_frame.pack(fill="both", expand=False, padx=1, pady=1)
      
        for c in range(5):
            self.grid_frame.grid_columnconfigure(c, weight=1)
        self.trans_vars = {}
        self.check_boxes = []
      
        # Using 100 transitions with real names
        transition_names = {
            1: "instant-cut",
            2: "fade",
            3: "fade-in",
            4: "fade-out",
            5: "slide-left",
            6: "slide-right",
            7: "slide-up",
            8: "slide-down",
            9: "zoom-in",
            10: "zoom-out",
            11: "focus-in",
            12: "focus-out",
            13: "wipe-left-to-right",
            14: "wipe-right-to-left",
            15: "wipe-top-to-bottom",
            16: "wipe-bottom-to-top",
            17: "diagonal-top-left-to-bottom-right",
            18: "diagonal-bottom-right-to-top-left",
            19: "diagonal-top-right-to-bottom-left",
            20: "diagonal-bottom-left-to-top-right",
            21: "iris-in",
            22: "iris-out",
            23: "clock-wipe-clockwise",
            24: "clock-wipe-counterclockwise",
            25: "barn-door-open",
            26: "barn-door-close",
            27: "split-vertical-open",
            28: "split-vertical-close",
            29: "split-horizontal-open",
            30: "split-horizontal-close",
            31: "checker-dissolve",
            32: "pixelate-transition",
            33: "spiral-clockwise",
            34: "spiral-counterclockwise",
            35: "dissolve-white",
            36: "dissolve-black",
            37: "whip-pan-left",
            38: "whip-pan-right",
            39: "whip-pan-up",
            40: "whip-pan-down",
            41: "push-left",
            42: "push-right",
            43: "push-up",
            44: "push-down",
            45: "reveal-left",
            46: "reveal-right",
            47: "reveal-up",
            48: "reveal-down",
            49: "box-in",
            50: "box-out",
            51: "diamond-in",
            52: "diamond-out",
            53: "venetian-blinds-horizontal",
            54: "venetian-blinds-vertical",
            55: "checkerboard-inward",
            56: "checkerboard-outward",
            57: "radial-wipe-in",
            58: "radial-wipe-out",
            59: "crossfade",
            60: "glitch-transition",
            61: "light-leak",
            62: "film-burn",
            63: "corner-pin-top-left",
            64: "corner-pin-top-right",
            65: "corner-pin-bottom-left",
            66: "corner-pin-bottom-right",
            67: "center-expand",
            68: "center-collapse",
            69: "wave-left-to-right",
            70: "wave-right-to-left",
            71: "wave-top-to-bottom",
            72: "wave-bottom-to-top",
            73: "twist-clockwise",
            74: "twist-counterclockwise",
            75: "ripple-center",
            76: "ripple-edges",
            77: "mosaic-transition",
            78: "mirror-flip-horizontal",
            79: "mirror-flip-vertical",
            80: "shatter-from-center",
            81: "shatter-from-edges",
            82: "fold-left",
            83: "fold-right",
            84: "fold-up",
            85: "fold-down",
            86: "cube-rotate-left",
            87: "cube-rotate-right",
            88: "cube-rotate-up",
            89: "cube-rotate-down",
            90: "page-curl-top-right",
            91: "page-curl-bottom-left",
            92: "linear-blur-left-to-right",
            93: "linear-blur-right-to-left",
            94: "radial-blur-in",
            95: "radial-blur-out",
            96: "squares-random",
            97: "strips-left-to-right",
            98: "strips-right-to-left",
            99: "strips-top-to-bottom",
            100: "strips-bottom-to-top",
        }
      
        for i in range(1, 101):
            var = ctk.BooleanVar(value=True)
            name = transition_names.get(i, f"Unknown-{i}")
            display_text = f"{i}: {name}"
            cb = ctk.CTkCheckBox(
                self.grid_frame,
                text=display_text,
                variable=var,
                font=ctk.CTkFont(family="Consolas", size=7),
                checkbox_width=10, checkbox_height=10,
                hover_color="#3B82F6"
            )
            cb.grid(row=(i-1) // 5, column=(i-1) % 5, padx=4, pady=2, sticky="w")
            self.trans_vars[i] = var
            self.check_boxes.append(cb)
        # Console Section
        console_header = ctk.CTkFrame(self.main, fg_color="transparent")
        console_header.pack(fill="x", pady=(5, 2))
      
        ctk.CTkLabel(
            console_header, text="ENGINE CONSOLE",
            font=ctk.CTkFont(size=9, weight="bold"),
            text_color="#E2E8F0"
        ).pack(side="left")
      
        self.clear_btn = ctk.CTkButton(
            console_header, text="CLEAR",
            width=60, height=16, fg_color="transparent",
            text_color="#F59E0B", hover_color="#EF4444",
            font=ctk.CTkFont(size=8),
            command=self.clear_console
        )
        self.clear_btn.pack(side="right", padx=3)
      
        self.export_btn = ctk.CTkButton(
            console_header, text="EXPORT LOG",
            width=60, height=16, fg_color="transparent",
            text_color="#3B82F6", hover_color="#10B981",
            font=ctk.CTkFont(size=8),
            command=self.export_log
        )
        self.export_btn.pack(side="right")
        self.console = ctk.CTkTextbox(
            self.main, fg_color="#05070A",
            border_width=1, border_color="#1F2937",
            text_color="#10B981",
            font=ctk.CTkFont(family="monospace", size=9),
            wrap="word"
        )
        self.console.pack(fill="both", expand=True)
        self.console.configure(state="disabled")
      
        # Redirect stdout to console
        sys.stdout = ConsoleRedirector(self.console)
        sys.stderr = ConsoleRedirector(self.console)
      
        # Start clock update
        self.update_clock()
      
        print(f"[*] BoredNoMore3 Mission Control v{VERSION} initialized")
        print(f"[*] Ready to launch background engine")
    # --- CONFIGURATION MANAGEMENT ---
    def load_configuration(self):
        """Load configuration from file"""
        config_file = self.config_var.get()
        if os.path.exists(config_file):
            loaded_config = load_config_file(config_file)
            if loaded_config:
                self.config.update(loaded_config)
                self.apply_config_to_ui()
                print(f"[*] Configuration loaded from: {config_file}")
            else:
                print(f"[WARNING] Could not load configuration from: {config_file}")
        else:
            print(f"[INFO] Config file not found: {config_file}, using defaults")
    def save_configuration(self):
        """Save current UI settings to configuration file"""
        self.config['directory'] = self.path_var.get()
        self.config['interval'] = int(self.interval_ctrl.get())
        self.config['frames'] = int(self.frames_ctrl.get())
        self.config['speed'] = float(self.speed_ctrl.get())
        self.config['randomize'] = self.rand_switch.get()
        self.config['keep_image'] = self.keep_image_switch.get()
        self.config['borednomore3_binary'] = self.binary_var.get()
      
        # Get selected transitions
        selected = [str(n) for n, v in self.trans_vars.items() if v.get()]
        self.config['transitions'] = ','.join(selected)
      
        config_file = self.config_var.get()
        if save_config_file(config_file, self.config):
            print(f"[+] Configuration saved successfully")
        else:
            print(f"[ERROR] Failed to save configuration")
    def apply_config_to_ui(self):
        """Apply loaded configuration to UI elements"""
        self.path_var.set(self.config['directory'])
        self.interval_ctrl.set(self.config['interval'])
        self.frames_ctrl.set(self.config['frames'])
        self.speed_ctrl.set(self.config['speed'])
        self.binary_var.set(self.config['borednomore3_binary'])
      
        if self.config['randomize']:
            self.rand_switch.select()
        else:
            self.rand_switch.deselect()
      
        if self.config['keep_image']:
            self.keep_image_switch.select()
        else:
            self.keep_image_switch.deselect()
      
        # Apply transition selection
        if self.config['transitions']:
            # First deselect all
            for cb in self.check_boxes:
                cb.deselect()
          
            # Then select specified ones
            try:
                transitions = [int(t.strip()) for t in self.config['transitions'].split(',') if t.strip()]
                for t in transitions:
                    if t in self.trans_vars:
                        self.trans_vars[t].set(True)
            except:
                pass
    def browse_config(self):
        """Browse for configuration file"""
        path = filedialog.askopenfilename(
            initialdir=os.getcwd(),
            title="Select Configuration File",
            filetypes=(("Config files", "*.conf"), ("All files", "*.*"))
        )
        if path:
            self.config_var.set(path)
            self.load_configuration()
    # --- PROCESS MANAGEMENT ---
    def get_backend_command(self, use_unbuffered=False):
        """Get the backend command from config or detect binary
      
        Args:
            use_unbuffered: If True, add -u flag for unbuffered output (only for background processes)
        """
        binary = self.binary_var.get().strip()
      
        if not binary:
            binary = 'borednomore3'
      
        # Check if running from source or as binary
        if getattr(sys, 'frozen', False):
            # GUI is compiled, use configured binary name
            return [binary]
      
        # GUI is running as script, check if backend is .py or binary
        if os.path.exists(f"{binary}.py"):
            if use_unbuffered:
                return [sys.executable, "-u", f"{binary}.py"]
            else:
                return [sys.executable, f"{binary}.py"]
        elif os.path.exists(binary):
            return [f"./{binary}"]
        else:
            return [binary]
    def check_existing_engine(self):
        """Check if engine is already running from previous session."""
        pid = get_saved_pid()
        if pid and is_pid_running(pid):
            self.bg_process_pid = pid
            print(f"[*] Detected existing engine running (PID: {pid})")
            print(f"[*] Resuming monitoring of background process")
            print(f"[*] Output log: /tmp/borednomore3.log")
            self.set_running_state(True)
          
            # Try to load existing log content
            log_file = "/tmp/borednomore3.log"
            try:
                if os.path.exists(log_file):
                    with open(log_file, 'r') as f:
                        content = f.read()
                        if content:
                            print("=" * 80)
                            print("--- Previous Engine Output (last 30 lines) ---")
                            print("=" * 80)
                            lines = content.splitlines()
                            for line in lines[-30:]:
                                print(line)
                            print("=" * 80)
                            print("--- Continuing live output ---")
            except Exception as e:
                print(f"[WARNING] Could not read previous log: {e}")
          
            self.start_log_monitoring(log_file)
        else:
            if pid:
                print(f"[*] Stale PID file detected, cleaning up")
                cleanup_pid_file()
            self.set_running_state(False)
    def start_engine(self):
        """Launch the background engine process."""
        selected_t = [int(n) for n, v in self.trans_vars.items() if v.get()]
        if not selected_t:
            print("[ERROR] No transitions selected! Select at least one.")
            return
      
        base_cmd = self.get_backend_command(use_unbuffered=True)
        flags = [
            "-d", self.path_var.get(),
            "-i", str(self.interval_ctrl.get()),
            "-f", str(self.frames_ctrl.get()),
            "-s", str(self.speed_ctrl.get()),
            "-t", ",".join(map(str, selected_t))
        ]
        if self.rand_switch.get():
            flags.append("-r")
        if self.keep_image_switch.get():
            flags.append("-k")
        print(f"[*] Launching background engine...")
        print(f"[*] Command: {' '.join(base_cmd + flags)}")
        try:
            log_file = "/tmp/borednomore3.log"
          
            with open(log_file, "w") as log:
                process = subprocess.Popen(
                    base_cmd + flags,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    stdin=subprocess.DEVNULL,
                    start_new_session=True,
                    bufsize=0,
                    env={**os.environ, 'PYTHONUNBUFFERED': '1'}
                )
          
            self.bg_process_pid = process.pid
            save_pid(process.pid)
          
            print(f"[+] Engine started successfully (PID: {process.pid})")
            print(f"[+] Process is now running in background")
            print(f"[*] Output is being logged to: {log_file}")
            print(f"[*] Streaming engine output below:")
            print("=" * 80)
          
            self.start_time = time.time()
            self.set_running_state(True)
          
            self.start_log_monitoring(log_file)
          
        except Exception as e:
            print(f"[ERROR] Failed to start engine: {e}")
            self.set_running_state(False)
    def stop_engine(self):
        """Stop the background engine process."""
        if not self.bg_process_pid:
            print("[WARNING] No active process to stop")
            return
      
        print(f"[!] Terminating engine (PID: {self.bg_process_pid})...")
      
        if kill_process(self.bg_process_pid):
            print(f"[OK] Engine process {self.bg_process_pid} terminated")
            cleanup_pid_file()
            self.bg_process_pid = None
            self.start_time = None
            self.set_running_state(False)
        else:
            print(f"[ERROR] Failed to terminate process {self.bg_process_pid}")
            print(f"[*] You may need to kill it manually: kill {self.bg_process_pid}")
    def start_log_monitoring(self, log_file=None):
        """Monitor if background process is still running and tail log file."""
        if self.monitoring:
            return
      
        self.monitoring = True
        self.log_file = log_file or "/tmp/borednomore3.log"
      
        def monitor():
            last_position = 0
            time.sleep(0.2)
          
            while self.monitoring and self.bg_process_pid:
                if not is_pid_running(self.bg_process_pid):
                    print("=" * 80)
                    print(f"[!] Background process {self.bg_process_pid} has terminated")
                    cleanup_pid_file()
                    self.after(0, lambda: self.set_running_state(False))
                    self.bg_process_pid = None
                    break
              
                try:
                    if os.path.exists(self.log_file):
                        with open(self.log_file, 'r') as f:
                            f.seek(last_position)
                            new_content = f.read()
                            if new_content:
                                for line in new_content.splitlines():
                                    print(line)
                                last_position = f.tell()
                except Exception:
                    pass
              
                time.sleep(0.3)
      
        self.log_monitor_thread = threading.Thread(target=monitor, daemon=True)
        self.log_monitor_thread.start()
    # --- UI STATE MANAGEMENT ---
    def set_running_state(self, running):
        """Update GUI to reflect engine state."""
        if running:
            self.status_lbl.configure(
                text="STATUS: ACTIVE (BACKGROUND)",
                text_color="#10B981"
            )
            self.pid_lbl.configure(
                text=f"PID: {self.bg_process_pid or 'N/A'}",
                text_color="#10B981"
            )
            self.start_btn.configure(
                state="disabled",
                text="ENGINE ACTIVE",
                fg_color="#334155"
            )
            self.stop_btn.configure(
                state="normal",
                text_color="#EF4444",
                border_color="#EF4444"
            )
            self.set_controls_state(False)
          
            if not self.monitoring:
                self.start_log_monitoring()
              
        else:
            self.status_lbl.configure(
                text="STATUS: STANDBY",
                text_color="#3B82F6"
            )
            self.pid_lbl.configure(
                text="PID: N/A",
                text_color="#475569"
            )
            self.start_btn.configure(
                state="normal",
                text="INITIALIZE ENGINE",
                fg_color="#3B82F6"
            )
            self.stop_btn.configure(
                state="disabled",
                text_color="#94A3B8",
                border_color="#334155"
            )
            self.set_controls_state(True)
            self.monitoring = False
    def set_controls_state(self, enabled):
        """Enable/disable control inputs."""
        state = "normal" if enabled else "disabled"
      
        self.path_entry.configure(state=state)
        self.browse_btn.configure(state=state)
        self.config_entry.configure(state=state)
        self.config_browse_btn.configure(state=state)
        self.load_config_btn.configure(state=state)
        self.save_config_btn.configure(state=state)
        self.interval_ctrl.set_state(state)
        self.frames_ctrl.set_state(state)
        self.speed_ctrl.set_state(state)
        self.binary_entry.configure(state=state)
        self.rand_switch.configure(state=state)
        self.keep_image_switch.configure(state=state)
        self.all_btn.configure(state=state)
        self.none_btn.configure(state=state)
      
        for cb in self.check_boxes:
            cb.configure(state=state)
      
        for b in self.cmd_btns:
            b.configure(state=state)
    # --- UI UTILITIES ---
    def update_clock(self):
        """Update uptime display."""
        if self.start_time and self.bg_process_pid and is_pid_running(self.bg_process_pid):
            elapsed = int(time.time() - self.start_time)
            self.timer_lbl.configure(
                text=f"UPTIME: {time.strftime('%H:%M:%S', time.gmtime(elapsed))}",
                text_color="#10B981"
            )
        else:
            self.timer_lbl.configure(
                text="UPTIME: 00:00:00",
                text_color="#475569"
            )
      
        self.after(1000, self.update_clock)
    def bulk_matrix(self, state):
        """Select/deselect all transitions."""
        for cb in self.check_boxes:
            if state:
                cb.select()
            else:
                cb.deselect()
    def run_external_cmd(self, flag):
        """Run backend command and capture output."""
        def execute():
            cmd = self.get_backend_command(use_unbuffered=False) + [flag]
            print(f"[*] Executing: {' '.join(cmd)}")
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.stdout:
                    for line in result.stdout.splitlines():
                        print(line)
                if result.stderr:
                    for line in result.stderr.splitlines():
                        print(f"[ERROR] {line}")
            except subprocess.TimeoutExpired:
                print("[ERROR] Command timed out")
            except Exception as e:
                print(f"[ERROR] Command failed: {e}")
      
        threading.Thread(target=execute, daemon=True).start()
    def clear_console(self):
        """Clear console output."""
        self.console.configure(state="normal")
        self.console.delete("1.0", "end")
        self.console.configure(state="disabled")
        print(f"[*] Console cleared at {time.strftime('%H:%M:%S')}")
    def export_log(self):
        """Export console log to file."""
        try:
            content = self.console.get("1.0", "end-1c")
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"borednomore_log_{timestamp}.txt"
          
            with open(filename, "w") as f:
                f.write(content)
          
            print(f"[*] Log exported to {filename}")
        except Exception as e:
            print(f"[ERROR] Failed to export log: {e}")
    def browse(self):
        """Open directory browser."""
        path = filedialog.askdirectory(initialdir=self.path_var.get())
        if path:
            self.path_var.set(path)
            print(f"[*] Directory changed to: {path}")
    def on_closing(self):
        """Handle window close - keep engine running."""
        if self.bg_process_pid and is_pid_running(self.bg_process_pid):
            print(f"[*] Closing GUI - engine will continue running (PID: {self.bg_process_pid})")
            print(f"[*] To stop engine, restart GUI and click STOP ENGINE")
      
        self.monitoring = False
        self.destroy()
    def end_program(self):
        """End Program - stop backend if running and close GUI"""
        if self.bg_process_pid and is_pid_running(self.bg_process_pid):
            self.stop_engine()
        self.destroy()
# --- MAIN ENTRY POINT ---
if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
  
    app = BoredMissionControl()
    app.mainloop()
