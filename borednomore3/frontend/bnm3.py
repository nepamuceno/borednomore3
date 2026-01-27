#!/usr/bin/env python3
"""
BNM3 GUI - BoredNoMore3 Dynamic Wallpaper Manager
Professional interface with REAL command execution output

Author: Nepamuceno
Version: 1.0.3
Slogan: "Never Stare At The Same Wall Twice"
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageDraw, ImageFont
import os, sys, json, subprocess, signal, threading, time
from datetime import datetime

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Determine if we're installed or running from source
if '/usr/' in SCRIPT_DIR or '/usr/local/' in SCRIPT_DIR:
    # Installed system-wide
    STATE_FILE = os.path.join(os.path.expanduser('~'), '.config', 'borednomore3', '.bnm3_gui_state.json')
    DEFAULT_SCRIPT = os.path.join(SCRIPT_DIR, 'borednomore3.py')
    CONF_DIR = '/etc/borednomore3'
    DEFAULT_CONF = os.path.join(CONF_DIR, 'borednomore3.conf')
    DEFAULT_LIST = os.path.join(CONF_DIR, 'borednomore3.list')
    WALLPAPERS_DIR = os.path.join(os.path.expanduser('~'), 'Pictures', 'Wallpapers')
else:
    # Running from source
    STATE_FILE = os.path.join(SCRIPT_DIR, '.bnm3_gui_state.json')
    DEFAULT_SCRIPT = os.path.join(SCRIPT_DIR, '..', 'backend', 'borednomore3.py')
    CONF_DIR = os.path.join(SCRIPT_DIR, '..', 'conf')
    DEFAULT_CONF = os.path.join(CONF_DIR, 'borednomore3.conf')
    DEFAULT_LIST = os.path.join(CONF_DIR, 'borednomore3.list')
    WALLPAPERS_DIR = os.path.join(SCRIPT_DIR, '..', 'wallpapers')

def create_logo():
    size = 128
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Gradient background circle
    for i in range(size//2, 0, -2):
        alpha = int(255 * (i / (size//2)))
        draw.ellipse([size//2 - i, size//2 - i, size//2 + i, size//2 + i], 
                     fill=(30, 144, 255, alpha))
    
    # Draw "BNM3" instead of "B3"
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
    except:
        font = ImageFont.load_default()
    
    text = "BNM3"
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    pos = ((size - tw) // 2, (size - th) // 2 - 5)
    
    # Text shadow
    draw.text((pos[0] + 2, pos[1] + 2), text, fill=(0, 0, 0, 180), font=font)
    # Main text
    draw.text(pos, text, fill=(255, 255, 255, 255), font=font)
    
    return img

class ProcessManager:
    def __init__(self):
        self.process = None
        self.pid = None
        self.is_running = False
        
    def start_process(self, command, callback=None):
        try:
            self.process = subprocess.Popen(
                command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                universal_newlines=True, bufsize=1,
                preexec_fn=os.setsid if os.name != 'nt' else None
            )
            self.pid = self.process.pid
            self.is_running = True
            threading.Thread(target=self._read_output, args=(callback,), daemon=True).start()
            return True, self.pid
        except Exception as e:
            return False, str(e)
    
    def _read_output(self, callback):
        try:
            while self.is_running and self.process and self.process.poll() is None:
                line = self.process.stdout.readline()
                if line and callback:
                    callback(line)
                time.sleep(0.001)
        except:
            pass
        finally:
            if self.process and self.process.stdout:
                try:
                    remaining = self.process.stdout.read()
                    if remaining and callback:
                        callback(remaining)
                except:
                    pass
    
    def stop_process(self, force=False):
        if not self.process or not self.pid:
            return True, "No process running"
        try:
            self.is_running = False
            if os.name == 'nt':
                self.process.kill() if force else self.process.terminate()
                msg = f"Process {self.pid} {'killed' if force else 'stopped'}"
            else:
                os.killpg(os.getpgid(self.pid), signal.SIGKILL if force else signal.SIGHUP)
                if not force:
                    try:
                        self.process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        os.killpg(os.getpgid(self.pid), signal.SIGKILL)
                msg = f"Process {self.pid} {'killed (SIGKILL)' if force else 'stopped (SIGHUP)'}"
            self._cleanup_zombies()
            self.process, self.pid = None, None
            return True, msg
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def _cleanup_zombies(self):
        if os.name != 'nt':
            try:
                result = subprocess.run(['pgrep', '-f', 'borednomore3.py'], capture_output=True, text=True)
                if result.returncode == 0:
                    for pid in result.stdout.strip().split('\n'):
                        if pid and pid.isdigit():
                            try:
                                os.kill(int(pid), signal.SIGKILL)
                            except:
                                pass
            except:
                pass
    
    def is_process_running(self):
        if not self.pid:
            return False
        try:
            return (self.process and self.process.poll() is None) if os.name == 'nt' else (os.kill(self.pid, 0) or True)
        except:
            return False


class BNM3GUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Ensure state file directory exists
        state_dir = os.path.dirname(STATE_FILE)
        if state_dir and not os.path.exists(state_dir):
            try:
                os.makedirs(state_dir, exist_ok=True)
            except:
                pass  # Fallback to current directory if can't create
        
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        ww, wh = min(int(sw * 0.9), 1600), min(int(sh * 0.9), 1000)
        x, y = (sw - ww) // 2, (sh - wh) // 2
        
        self.title("BNM3 - BoredNoMore3 Wallpaper Manager")
        self.geometry(f"{ww}x{wh}+{x}+{y}")
        self.minsize(1400, 900)
        
        try:
            logo = create_logo()
            import io
            with io.BytesIO() as output:
                logo.save(output, format="PNG")
                output.seek(0)
                self.iconphoto(True, tk.PhotoImage(data=output.read()))
        except:
            pass
        
        self.process_manager = ProcessManager()
        self.state = self.load_state()
        self.create_ui()
        self.restore_state()
        self.after(1000, self.update_status)
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def create_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.create_sidebar()
        self.create_main_content()
    
    def create_sidebar(self):
        sidebar = ctk.CTkFrame(self, width=300, corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_rowconfigure(15, weight=1)
        
        try:
            logo_img = create_logo().resize((80, 80), Image.Resampling.LANCZOS)
            logo_photo = ctk.CTkImage(light_image=logo_img, dark_image=logo_img, size=(80, 80))
            ctk.CTkLabel(sidebar, image=logo_photo, text="").grid(row=0, column=0, padx=20, pady=(20, 10))
        except:
            pass
        
        ctk.CTkLabel(sidebar, text="BNM3", font=ctk.CTkFont(size=32, weight="bold")).grid(row=1, column=0, padx=20, pady=(5, 0))
        ctk.CTkLabel(sidebar, text="BoredNoMore3", font=ctk.CTkFont(size=14)).grid(row=2, column=0, padx=20, pady=0)
        ctk.CTkLabel(sidebar, text='"Never Stare At The Same Wall Twice"', font=ctk.CTkFont(size=10, slant="italic"), text_color="gray").grid(row=3, column=0, padx=20, pady=(0, 5))
        ctk.CTkLabel(sidebar, text="v1.0.3", font=ctk.CTkFont(size=9), text_color="gray50").grid(row=4, column=0, padx=20, pady=(0, 15))
        
        quick_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        quick_frame.grid(row=5, column=0, padx=20, pady=(5, 10), sticky="ew")
        quick_frame.grid_columnconfigure((0, 1, 2), weight=1)
        
        ctk.CTkButton(quick_frame, text="❓", command=self.show_help, width=60, height=30).grid(row=0, column=0, padx=2)
        ctk.CTkButton(quick_frame, text="ℹ️", command=self.show_version, width=60, height=30).grid(row=0, column=1, padx=2)
        ctk.CTkButton(quick_frame, text="👤", command=self.show_credits, width=60, height=30).grid(row=0, column=2, padx=2)
        
        self.debug_var = tk.BooleanVar(value=self.state.get('debug', False))
        ctk.CTkCheckBox(sidebar, text="Enable Debug Mode (-D)", variable=self.debug_var, font=ctk.CTkFont(size=10), height=20).grid(row=6, column=0, padx=20, pady=(0, 8), sticky="w")
        
        self.start_button = ctk.CTkButton(sidebar, text="▶ START", command=self.start_wallpapers, height=45, font=ctk.CTkFont(size=15, weight="bold"), fg_color="#28a745", hover_color="#218838")
        self.start_button.grid(row=7, column=0, padx=20, pady=8, sticky="ew")
        
        self.stop_button = ctk.CTkButton(sidebar, text="■ STOP", command=lambda: self.stop_wallpapers(False), height=38, font=ctk.CTkFont(size=13), fg_color="#fd7e14", hover_color="#e67700", state="disabled")
        self.stop_button.grid(row=8, column=0, padx=20, pady=8, sticky="ew")
        
        self.kill_button = ctk.CTkButton(sidebar, text="⚠ FORCE KILL", command=lambda: self.stop_wallpapers(True), height=38, font=ctk.CTkFont(size=13), fg_color="#dc3545", hover_color="#c82333", state="disabled")
        self.kill_button.grid(row=9, column=0, padx=20, pady=8, sticky="ew")
        
        status_frame = ctk.CTkFrame(sidebar)
        status_frame.grid(row=10, column=0, padx=20, pady=15, sticky="ew")
        status_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(status_frame, text="Status:", font=ctk.CTkFont(size=11, weight="bold")).grid(row=0, column=0, padx=8, pady=6, sticky="w")
        self.status_indicator = ctk.CTkLabel(status_frame, text="● Stopped", text_color="gray", font=ctk.CTkFont(size=11))
        self.status_indicator.grid(row=0, column=1, padx=8, pady=6, sticky="e")
        
        ctk.CTkLabel(status_frame, text="PID:", font=ctk.CTkFont(size=11, weight="bold")).grid(row=1, column=0, padx=8, pady=6, sticky="w")
        self.pid_label = ctk.CTkLabel(status_frame, text="N/A", font=ctk.CTkFont(size=11))
        self.pid_label.grid(row=1, column=1, padx=8, pady=6, sticky="e")
        
        ctk.CTkLabel(sidebar, text="Theme:", font=ctk.CTkFont(size=11, weight="bold")).grid(row=11, column=0, padx=20, pady=(15, 3))
        self.theme_var = tk.StringVar(value=self.state.get('theme', 'System'))
        ctk.CTkOptionMenu(sidebar, values=["Light", "Dark", "System"], variable=self.theme_var, command=self.change_theme, height=32).grid(row=12, column=0, padx=20, pady=3, sticky="ew")
        
        ctk.CTkFrame(sidebar, height=2, fg_color="gray30").grid(row=13, column=0, padx=20, pady=15, sticky="ew")
        
        ctk.CTkButton(sidebar, text="💾 Save Log", command=self.save_log, height=32).grid(row=14, column=0, padx=20, pady=4, sticky="ew")
        ctk.CTkButton(sidebar, text="🗑 Clear Console", command=self.clear_log, height=32, fg_color="gray40", hover_color="gray30").grid(row=15, column=0, padx=20, pady=4, sticky="ew")
        ctk.CTkButton(sidebar, text="🧹 Cleanup Processes", command=self.cleanup_zombies_manual, height=32, fg_color="gray40", hover_color="gray30").grid(row=16, column=0, padx=20, pady=4, sticky="ew")
        
        ctk.CTkButton(sidebar, text="🚪 EXIT PROGRAM", command=self.exit_program, height=40, font=ctk.CTkFont(size=13, weight="bold"), fg_color="#dc3545", hover_color="#c82333").grid(row=18, column=0, padx=20, pady=(10, 20), sticky="ew")
    
    def create_main_content(self):
        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=0, column=1, padx=15, pady=15, sticky="nsew")
        
        self.tab_settings = self.tabview.add("⚙ Settings")
        self.tab_console = self.tabview.add("🖥 Console")
        self.tab_advanced = self.tabview.add("🔧 Advanced")
        
        self.tab_settings.grid_columnconfigure(0, weight=1)
        self.tab_console.grid_columnconfigure(0, weight=1)
        self.tab_console.grid_rowconfigure(1, weight=1)
        self.tab_advanced.grid_columnconfigure(0, weight=1)
        
        self.create_settings_tab()
        self.create_console_tab()
        self.create_advanced_tab()
    
    def create_settings_tab(self):
        main_frame = ctk.CTkFrame(self.tab_settings, fg_color="transparent")
        main_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)
        
        left_col = ctk.CTkFrame(main_frame, fg_color="transparent")
        left_col.grid(row=0, column=0, sticky="nsew", padx=5)
        left_col.grid_columnconfigure(1, weight=1)
        
        row = 0
        ctk.CTkLabel(left_col, text="📁 FILE PATHS", font=ctk.CTkFont(size=13, weight="bold")).grid(row=row, column=0, columnspan=3, padx=5, pady=(5, 8), sticky="w")
        row += 1
        
        ctk.CTkLabel(left_col, text="Script Path:", font=ctk.CTkFont(size=10)).grid(row=row, column=0, padx=5, pady=3, sticky="w")
        self.script_path_var = tk.StringVar(value=self.state.get('script_path', DEFAULT_SCRIPT))
        ctk.CTkEntry(left_col, textvariable=self.script_path_var, height=26, font=ctk.CTkFont(size=10)).grid(row=row, column=1, padx=3, pady=3, sticky="ew")
        ctk.CTkButton(left_col, text="...", width=35, height=26, command=lambda: self.browse_file(self.script_path_var, "Python", "*.py")).grid(row=row, column=2, padx=3, pady=3)
        row += 1
        
        self.use_config_var = tk.BooleanVar(value=self.state.get('use_config', False))
        self.use_config_cb = ctk.CTkCheckBox(left_col, text="Use custom configuration file", variable=self.use_config_var, font=ctk.CTkFont(size=10, weight="bold"), height=22, command=self.toggle_config_state)
        self.use_config_cb.grid(row=row, column=0, columnspan=3, padx=5, pady=3, sticky="w")
        row += 1
        
        ctk.CTkLabel(left_col, text="Config File:", font=ctk.CTkFont(size=10)).grid(row=row, column=0, padx=5, pady=3, sticky="w")
        self.config_path_var = tk.StringVar(value=self.state.get('config_path', DEFAULT_CONF))
        self.config_entry = ctk.CTkEntry(left_col, textvariable=self.config_path_var, height=26, font=ctk.CTkFont(size=10))
        self.config_entry.grid(row=row, column=1, padx=3, pady=3, sticky="ew")
        self.config_browse = ctk.CTkButton(left_col, text="...", width=35, height=26, command=lambda: self.browse_file(self.config_path_var, "Config", "*.conf"))
        self.config_browse.grid(row=row, column=2, padx=3, pady=3)
        row += 1
        
        self.use_directory_var = tk.BooleanVar(value=self.state.get('use_directory', False))
        self.use_directory_cb = ctk.CTkCheckBox(left_col, text="Use custom wallpaper folder", variable=self.use_directory_var, font=ctk.CTkFont(size=10), height=22, command=self.toggle_directory_state)
        self.use_directory_cb.grid(row=row, column=0, columnspan=3, padx=5, pady=3, sticky="w")
        row += 1
        
        ctk.CTkLabel(left_col, text="Folder:", font=ctk.CTkFont(size=10)).grid(row=row, column=0, padx=5, pady=3, sticky="w")
        self.directory_var = tk.StringVar(value=self.state.get('directory', WALLPAPERS_DIR))
        self.directory_entry = ctk.CTkEntry(left_col, textvariable=self.directory_var, height=26, font=ctk.CTkFont(size=10))
        self.directory_entry.grid(row=row, column=1, padx=3, pady=3, sticky="ew")
        self.directory_browse = ctk.CTkButton(left_col, text="...", width=35, height=26, command=self.browse_directory)
        self.directory_browse.grid(row=row, column=2, padx=3, pady=3)
        row += 1
        
        self.use_wallpaper_list_var = tk.BooleanVar(value=self.state.get('use_wallpaper_list', False))
        self.use_list_cb = ctk.CTkCheckBox(left_col, text="Use patterns file (file with wallpaper patterns)", variable=self.use_wallpaper_list_var, font=ctk.CTkFont(size=10), height=22, command=self.toggle_list_state)
        self.use_list_cb.grid(row=row, column=0, columnspan=3, padx=5, pady=3, sticky="w")
        row += 1
        
        ctk.CTkLabel(left_col, text="Patterns File:", font=ctk.CTkFont(size=10)).grid(row=row, column=0, padx=5, pady=3, sticky="w")
        self.list_path_var = tk.StringVar(value=self.state.get('list_path', DEFAULT_LIST))
        self.list_entry = ctk.CTkEntry(left_col, textvariable=self.list_path_var, height=26, font=ctk.CTkFont(size=10))
        self.list_entry.grid(row=row, column=1, padx=3, pady=3, sticky="ew")
        self.list_browse = ctk.CTkButton(left_col, text="...", width=35, height=26, command=lambda: self.browse_file(self.list_path_var, "List", "*.list"))
        self.list_browse.grid(row=row, column=2, padx=3, pady=3)
        row += 1
        
        ctk.CTkLabel(left_col, text="⏱ TIMING", font=ctk.CTkFont(size=13, weight="bold")).grid(row=row, column=0, columnspan=3, padx=5, pady=(12, 8), sticky="w")
        row += 1
        
        # Change every (with slider)
        ctk.CTkLabel(left_col, text="Change every (seconds):", font=ctk.CTkFont(size=10)).grid(row=row, column=0, padx=5, pady=3, sticky="w")
        self.interval_var = tk.IntVar(value=int(self.state.get('interval', 300)))
        self.interval_entry = ctk.CTkEntry(left_col, textvariable=self.interval_var, width=80, height=26, font=ctk.CTkFont(size=10))
        self.interval_entry.grid(row=row, column=1, padx=3, pady=3, sticky="w")
        row += 1
        
        self.interval_slider = ctk.CTkSlider(left_col, from_=1, to=3600, variable=self.interval_var, width=300, command=lambda v: self.interval_var.set(int(v)))
        self.interval_slider.grid(row=row, column=0, columnspan=3, padx=5, pady=(0, 8), sticky="ew")
        row += 1
        
        # Animation frames (with slider)
        ctk.CTkLabel(left_col, text="Animation frames (5-100):", font=ctk.CTkFont(size=10)).grid(row=row, column=0, padx=5, pady=3, sticky="w")
        self.frames_var = tk.IntVar(value=int(self.state.get('frames', 10)))
        self.frames_entry = ctk.CTkEntry(left_col, textvariable=self.frames_var, width=80, height=26, font=ctk.CTkFont(size=10))
        self.frames_entry.grid(row=row, column=1, padx=3, pady=3, sticky="w")
        row += 1
        
        self.frames_slider = ctk.CTkSlider(left_col, from_=5, to=100, variable=self.frames_var, width=300, command=lambda v: self.frames_var.set(int(v)))
        self.frames_slider.grid(row=row, column=0, columnspan=3, padx=5, pady=(0, 8), sticky="ew")
        row += 1
        
        # Delay per frame (with slider)
        ctk.CTkLabel(left_col, text="Delay per frame (seconds):", font=ctk.CTkFont(size=10)).grid(row=row, column=0, padx=5, pady=3, sticky="w")
        self.speed_var = tk.DoubleVar(value=float(self.state.get('speed', 0.001)))
        self.speed_entry = ctk.CTkEntry(left_col, textvariable=self.speed_var, width=80, height=26, font=ctk.CTkFont(size=10))
        self.speed_entry.grid(row=row, column=1, padx=3, pady=3, sticky="w")
        row += 1
        
        self.speed_slider = ctk.CTkSlider(left_col, from_=0.0001, to=1.0, variable=self.speed_var, width=300, command=lambda v: self.speed_var.set(round(float(v), 4)))
        self.speed_slider.grid(row=row, column=0, columnspan=3, padx=5, pady=(0, 8), sticky="ew")
        row += 1
        
        ctk.CTkLabel(left_col, text="🎬 TRANSITIONS", font=ctk.CTkFont(size=13, weight="bold")).grid(row=row, column=0, columnspan=3, padx=5, pady=(12, 8), sticky="w")
        row += 1
        
        ctk.CTkLabel(left_col, text="Effect IDs (e.g. 1,5,10-15):", font=ctk.CTkFont(size=10)).grid(row=row, column=0, padx=5, pady=3, sticky="w")
        self.transitions_var = tk.StringVar(value=self.state.get('transitions', ''))
        ctk.CTkEntry(left_col, textvariable=self.transitions_var, height=26, font=ctk.CTkFont(size=10)).grid(row=row, column=1, columnspan=2, padx=3, pady=3, sticky="ew")
        row += 1
        
        right_col = ctk.CTkFrame(main_frame, fg_color="transparent")
        right_col.grid(row=0, column=1, sticky="nsew", padx=5)
        
        rrow = 0
        ctk.CTkLabel(right_col, text="⚡ OPTIONS", font=ctk.CTkFont(size=13, weight="bold")).grid(row=rrow, column=0, padx=5, pady=(5, 8), sticky="w")
        rrow += 1
        
        self.randomize_var = tk.BooleanVar(value=self.state.get('randomize', False))
        self.randomize_cb = ctk.CTkCheckBox(right_col, text="Randomize transitions", variable=self.randomize_var, font=ctk.CTkFont(size=11), height=24)
        self.randomize_cb.grid(row=rrow, column=0, padx=5, pady=4, sticky="w")
        rrow += 1
        
        self.randomize_wallpapers_var = tk.BooleanVar(value=self.state.get('randomize_wallpapers', False))
        self.randomize_wp_cb = ctk.CTkCheckBox(right_col, text="Randomize wallpapers", variable=self.randomize_wallpapers_var, font=ctk.CTkFont(size=11), height=24)
        self.randomize_wp_cb.grid(row=rrow, column=0, padx=5, pady=4, sticky="w")
        rrow += 1
        
        self.keep_image_var = tk.BooleanVar(value=self.state.get('keep_image', False))
        self.keep_image_cb = ctk.CTkCheckBox(right_col, text="Keep previous image", variable=self.keep_image_var, font=ctk.CTkFont(size=11), height=24)
        self.keep_image_cb.grid(row=rrow, column=0, padx=5, pady=4, sticky="w")
        rrow += 1
        
        ctk.CTkLabel(right_col, text="ℹ️ INFO", font=ctk.CTkFont(size=13, weight="bold")).grid(row=rrow, column=0, padx=5, pady=(12, 8), sticky="w")
        rrow += 1
        
        info_frame = ctk.CTkFrame(right_col, fg_color=("gray85", "gray20"))
        info_frame.grid(row=rrow, column=0, padx=5, pady=5, sticky="nsew")
        
        info_text = """PRIORITY (highest → lowest):
1. Custom Config File
2. GUI Settings
3. Default borednomore3.conf
4. Script Defaults

When "Use custom configuration" is
checked, ALL other GUI settings
are IGNORED.

Transitions: Leave empty for all,
or specify IDs like: 1,5,10-15

Use sliders for easy adjustment
of timing values."""
        
        ctk.CTkLabel(info_frame, text=info_text, justify="left", font=ctk.CTkFont(size=9)).pack(padx=10, pady=10, anchor="w")
    
    def create_console_tab(self):
        header = ctk.CTkFrame(self.tab_console, fg_color="transparent", height=35)
        header.grid(row=0, column=0, sticky="ew", padx=5, pady=(5, 0))
        header.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(header, text="🖥 Live Terminal Output (Real-time from script)", font=ctk.CTkFont(size=14, weight="bold")).grid(row=0, column=0, sticky="w", padx=10)
        
        self.autoscroll_var = tk.BooleanVar(value=True)
        ctk.CTkCheckBox(header, text="Auto-scroll", variable=self.autoscroll_var, font=ctk.CTkFont(size=10), width=100).grid(row=0, column=1, padx=10)
        
        self.console_text = ctk.CTkTextbox(self.tab_console, wrap="none", font=ctk.CTkFont(family="Courier New", size=10), border_width=2)
        self.console_text.grid(row=1, column=0, sticky="nsew", padx=5, pady=(5, 5))
    
    def create_advanced_tab(self):
        main_frame = ctk.CTkFrame(self.tab_advanced, fg_color="transparent")
        main_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        main_frame.grid_columnconfigure(0, weight=1)
        
        row = 0
        ctk.CTkLabel(main_frame, text="🔧 ADVANCED OPTIONS", font=ctk.CTkFont(size=14, weight="bold")).grid(row=row, column=0, padx=5, pady=(5, 10), sticky="w")
        row += 1
        
        opt_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        opt_frame.grid(row=row, column=0, sticky="ew", padx=5, pady=5)
        opt_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(opt_frame, text="Python Interpreter:", font=ctk.CTkFont(size=11)).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.python_var = tk.StringVar(value=self.state.get('python_path', sys.executable))
        ctk.CTkEntry(opt_frame, textvariable=self.python_var, height=28, font=ctk.CTkFont(size=10)).grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        ctk.CTkLabel(opt_frame, text="Extra Arguments:", font=ctk.CTkFont(size=11)).grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.extra_args_var = tk.StringVar(value=self.state.get('extra_args', ''))
        ctk.CTkEntry(opt_frame, textvariable=self.extra_args_var, height=28, font=ctk.CTkFont(size=10)).grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        
        row += 1
        ctk.CTkLabel(main_frame, text="📋 COMMAND PREVIEW", font=ctk.CTkFont(size=14, weight="bold")).grid(row=row, column=0, padx=5, pady=(15, 10), sticky="w")
        row += 1
        
        self.command_preview = ctk.CTkTextbox(main_frame, height=100, font=ctk.CTkFont(family="Courier New", size=9), wrap="word")
        self.command_preview.grid(row=row, column=0, padx=5, pady=5, sticky="ew")
        row += 1
        
        ctk.CTkButton(main_frame, text="🔄 Update Preview", command=self.update_command_preview, height=32, font=ctk.CTkFont(size=11)).grid(row=row, column=0, padx=5, pady=5)
    
    def run_command_and_show_output(self, command, title):
        self.tabview.set("🖥 Console")
        self.log_message(f"\n{'='*80}\n{title}\n{'='*80}\n")
        self.log_message(f"Executing: {' '.join(command)}\n\n")
        
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=10)
            output = result.stdout if result.stdout else result.stderr
            if output:
                self.log_message(output)
            else:
                self.log_message("[No output received]\n")
            if result.returncode != 0:
                self.log_message(f"\n[Exit code: {result.returncode}]\n")
        except subprocess.TimeoutExpired:
            self.log_message("[Command timed out]\n")
        except Exception as e:
            self.log_message(f"[ERROR] {str(e)}\n")
        self.log_message(f"\n{'='*80}\n\n")
    
    def show_help(self):
        script = self.script_path_var.get()
        if os.path.exists(script):
            self.run_command_and_show_output([self.python_var.get(), script, '-h'], "HELP OUTPUT")
        else:
            messagebox.showerror("Error", f"Script not found:\n{script}")
    
    def show_version(self):
        script = self.script_path_var.get()
        if os.path.exists(script):
            self.run_command_and_show_output([self.python_var.get(), script, '--version'], "VERSION INFO")
        else:
            messagebox.showerror("Error", f"Script not found:\n{script}")
    
    def show_credits(self):
        script = self.script_path_var.get()
        if os.path.exists(script):
            self.run_command_and_show_output([self.python_var.get(), script, '-c'], "CREDITS")
        else:
            messagebox.showerror("Error", f"Script not found:\n{script}")
    
    def toggle_config_state(self):
        state = "normal" if self.use_config_var.get() else "disabled"
        self.config_entry.configure(state=state)
        self.config_browse.configure(state=state)
    
    def toggle_directory_state(self):
        state = "normal" if self.use_directory_var.get() else "disabled"
        self.directory_entry.configure(state=state)
        self.directory_browse.configure(state=state)
    
    def toggle_list_state(self):
        state = "normal" if self.use_wallpaper_list_var.get() else "disabled"
        self.list_entry.configure(state=state)
        self.list_browse.configure(state=state)
    
    def update_command_preview(self):
        try:
            cmd = self.build_command()
            cmd_str = ' '.join([f'"{arg}"' if ' ' in arg else arg for arg in cmd])
            self.command_preview.configure(state="normal")
            self.command_preview.delete("1.0", "end")
            self.command_preview.insert("1.0", cmd_str)
            self.command_preview.configure(state="disabled")
        except Exception as e:
            self.command_preview.configure(state="normal")
            self.command_preview.delete("1.0", "end")
            self.command_preview.insert("1.0", f"Error: {str(e)}")
            self.command_preview.configure(state="disabled")
    
    def browse_file(self, var, title, filetypes):
        filename = filedialog.askopenfilename(title=f"Select {title}", filetypes=[(title, filetypes), ("All Files", "*.*")])
        if filename:
            var.set(filename)
    
    def browse_directory(self):
        directory = filedialog.askdirectory(title="Select Wallpaper Directory")
        if directory:
            self.directory_var.set(directory)
    
    def build_command(self):
        cmd = [self.python_var.get(), self.script_path_var.get()]
        if self.debug_var.get():
            cmd.append('-D')
        if self.use_config_var.get():
            cmd.extend(['--config', self.config_path_var.get()])
        else:
            if self.interval_var.get():
                cmd.extend(['-i', str(self.interval_var.get())])
            if self.use_directory_var.get() and self.directory_var.get():
                cmd.extend(['-d', self.directory_var.get()])
            if self.frames_var.get():
                cmd.extend(['-f', str(self.frames_var.get())])
            if self.speed_var.get():
                cmd.extend(['-s', str(self.speed_var.get())])
            if self.transitions_var.get():
                cmd.extend(['-t', self.transitions_var.get()])
            if self.randomize_var.get():
                cmd.append('-r')
            if self.randomize_wallpapers_var.get():
                cmd.append('-w')
            if self.keep_image_var.get():
                cmd.append('-k')
            if self.use_wallpaper_list_var.get():
                cmd.extend(['-l', self.list_path_var.get()])
        if self.extra_args_var.get().strip():
            cmd.extend(self.extra_args_var.get().split())
        return cmd
    
    def disable_settings_controls(self):
        #Disable ONLY Settings tab controls
        for ctrl in [self.randomize_cb, self.randomize_wp_cb, self.keep_image_cb, self.use_list_cb, self.use_config_cb, self.use_directory_cb]:
               ctrl.configure(state="disabled")
    
        self.interval_entry.configure(state="disabled")
        self.interval_slider.configure(state="disabled")
        self.frames_entry.configure(state="disabled")
        self.frames_slider.configure(state="disabled")
        self.speed_entry.configure(state="disabled")
        self.speed_slider.configure(state="disabled")
    
        for widget in [self.config_entry, self.config_browse, self.directory_entry, self.directory_browse, self.list_entry, self.list_browse]:
              widget.configure(state="disabled")

    def enable_settings_controls(self):
        # Enable Settings tab controls
        for ctrl in [self.randomize_cb, self.randomize_wp_cb, self.keep_image_cb, self.use_list_cb, self.use_config_cb, self.use_directory_cb]:
            ctrl.configure(state="normal")
    
        self.interval_entry.configure(state="normal")
        self.interval_slider.configure(state="normal")
        self.frames_entry.configure(state="normal")
        self.frames_slider.configure(state="normal")
        self.speed_entry.configure(state="normal")
        self.speed_slider.configure(state="normal")
    
        self.toggle_config_state()
        self.toggle_directory_state()
        self.toggle_list_state()
    
    def start_wallpapers(self):
        if self.process_manager.is_process_running():
            messagebox.showwarning("Already Running", "Wallpaper changer is already running!")
            return
        
        if not os.path.exists(self.script_path_var.get()):
            messagebox.showerror("Error", f"Script file not found:\n{self.script_path_var.get()}")
            return
        
        try:
            cmd = self.build_command()
            cmd_str = ' '.join([f'"{a}"' if ' ' in a else a for a in cmd])
            self.log_message("=" * 80 + "\nSTARTING WALLPAPER CHANGER\n" + "=" * 80 + "\n")
            self.log_message(f"Command: {cmd_str}\n" + "=" * 80 + "\n\n")
            
            success, result = self.process_manager.start_process(cmd, callback=lambda line: self.after(0, lambda l=line: self.log_message(l)))
            
            if success:
                self.log_message(f"[Process started with PID: {result}]\n\n")
                self.start_button.configure(state="disabled")
                self.stop_button.configure(state="normal")
                self.kill_button.configure(state="normal")
                self.disable_settings_controls()
                self.save_state()
            else:
                self.log_message(f"[FAILED] {result}\n")
                messagebox.showerror("Error", f"Failed to start process:\n{result}")
        except Exception as e:
            self.log_message(f"[ERROR] {str(e)}\n")
            messagebox.showerror("Error", f"Failed to start:\n{str(e)}")
    
    def stop_wallpapers(self, force=False):
        if not self.process_manager.is_process_running():
            self.process_manager._cleanup_zombies()
            messagebox.showinfo("Not Running", "No process found. Attempted cleanup.")
            return
        
        action = "FORCE KILLING (SIGKILL)" if force else "STOPPING (SIGHUP)"
        self.log_message("\n" + "=" * 80 + f"\n{action} process PID {self.process_manager.pid}\n" + "=" * 80 + "\n")
        
        success, message = self.process_manager.stop_process(force=force)
        self.log_message(f"{message}\n" + "=" * 80 + "\n\n")
        
        if success:
            self.start_button.configure(state="normal")
            self.stop_button.configure(state="disabled")
            self.kill_button.configure(state="disabled")
            self.enable_settings_controls()
    
    def cleanup_zombies_manual(self):
        self.log_message("\n[Scanning for background processes...]\n")
        self.process_manager._cleanup_zombies()
        self.log_message("[Cleanup complete]\n\n")
        messagebox.showinfo("Cleanup", "Background processes cleaned")
    
    def log_message(self, message):
        self.console_text.configure(state="normal")
        self.console_text.insert("end", message)
        if self.autoscroll_var.get():
            self.console_text.see("end")
        self.console_text.configure(state="disabled")
    
    def clear_log(self):
        if messagebox.askyesno("Clear Console", "Clear all console output?"):
            self.console_text.configure(state="normal")
            self.console_text.delete("1.0", "end")
            self.console_text.configure(state="disabled")
            self.log_message("[Console cleared]\n\n")
    
    def save_log(self):
        filename = filedialog.asksaveasfilename(defaultextension=".log",
            filetypes=[("Log Files", "*.log"), ("Text Files", "*.txt"), ("All Files", "*.*")],
            initialfile=f"bnm3_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        if filename:
            try:
                with open(filename, 'w') as f:
                    f.write(self.console_text.get("1.0", "end-1c"))
                messagebox.showinfo("Success", f"Log saved to:\n{filename}")
                self.log_message(f"\n[Log saved to: {filename}]\n\n")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save log:\n{str(e)}")
    
    def change_theme(self, theme):
        ctk.set_appearance_mode(theme)
        self.save_state()
    
    def update_status(self):
        if self.process_manager.is_process_running():
            self.status_indicator.configure(text="● Running", text_color="#28a745")
            self.pid_label.configure(text=str(self.process_manager.pid))
        else:
            self.status_indicator.configure(text="● Stopped", text_color="gray")
            self.pid_label.configure(text="N/A")
            if self.stop_button.cget("state") == "normal":
                self.start_button.configure(state="normal")
                self.stop_button.configure(state="disabled")
                self.kill_button.configure(state="disabled")
                self.enable_settings_controls()
                self.log_message("\n[Process ended]\n\n")
        self.after(1000, self.update_status)
    
    def save_state(self):
        state = {
            'theme': self.theme_var.get(),
            'script_path': self.script_path_var.get(),
            'config_path': self.config_path_var.get(),
            'list_path': self.list_path_var.get(),
            'interval': self.interval_var.get(),
            'directory': self.directory_var.get(),
            'frames': self.frames_var.get(),
            'speed': self.speed_var.get(),
            'transitions': self.transitions_var.get(),
            'randomize': self.randomize_var.get(),
            'randomize_wallpapers': self.randomize_wallpapers_var.get(),
            'keep_image': self.keep_image_var.get(),
            'use_wallpaper_list': self.use_wallpaper_list_var.get(),
            'use_config': self.use_config_var.get(),
            'use_directory': self.use_directory_var.get(),
            'debug': self.debug_var.get(),
            'python_path': self.python_var.get(),
            'extra_args': self.extra_args_var.get(),
            'running_pid': self.process_manager.pid,
            'window_geometry': self.geometry()
        }
        try:
            with open(STATE_FILE, 'w') as f:
                json.dump(state, f, indent=2)
        except:
            pass
    
    def load_state(self):
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    def restore_state(self):
        if 'window_geometry' in self.state:
            try:
                self.geometry(self.state['window_geometry'])
            except:
                pass
        
        if 'running_pid' in self.state and self.state['running_pid']:
            pid = self.state['running_pid']
            try:
                if os.name != 'nt':
                    os.kill(pid, 0)
                    if messagebox.askyesno("Orphaned Process", f"Found process from previous session (PID: {pid})\n\nKill it?"):
                        try:
                            os.killpg(os.getpgid(pid), signal.SIGKILL)
                            self.log_message(f"[Killed orphaned process {pid}]\n\n")
                        except Exception as e:
                            self.log_message(f"[ERROR killing {pid}: {e}]\n\n")
            except:
                pass
        
        self.toggle_config_state()
        self.toggle_directory_state()
        self.toggle_list_state()
    
    def exit_program(self):
        if self.process_manager.is_process_running():
            response = messagebox.askyesnocancel("Process Running",
                f"Wallpaper changer is running (PID: {self.process_manager.pid})\n\n"
                "Yes = Stop process and exit\nNo = Leave running and exit\nCancel = Don't exit")
            if response is None:
                return
            elif response:
                self.stop_wallpapers(force=True)
                time.sleep(0.5)
        
        self.log_message("\n[Saving state...]\n")
        self.save_state()
        self.log_message("[Exiting]\n\n")
        self.process_manager.is_running = False
        self.destroy()
    
    def on_closing(self):
        self.exit_program()


if __name__ == "__main__":
    try:
        import customtkinter
    except ImportError:
        print("\nERROR: CustomTkinter required\nInstall: pip install customtkinter\n")
        sys.exit(1)
    
    BNM3GUI().mainloop()
