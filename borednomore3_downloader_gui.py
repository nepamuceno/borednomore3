#!/usr/bin/env python3
import os
import sys
import hashlib
import glob
import re
import threading
import subprocess
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import customtkinter as ctk

VERSION = "0.7.0"

# Import the engines module
try:
    from borednomore3_downloader_engines import DownloadEngines
except ImportError:
    print("ERROR: borednomore3_downloader_engines.py not found!")
    print("Please ensure the engines file is in the same directory.")
    sys.exit(1)

# --- LOG REDIRECTION ---
class RedirectText:
    """Thread-safe text redirection to GUI console."""
    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.queue = []
        self.lock = threading.Lock()

    def write(self, string):
        """Write to buffer (called from any thread)."""
        if string.strip():
            with self.lock:
                self.queue.append(string)

    def flush_to_widget(self):
        """Flush buffer to widget (must be called from main thread)."""
        with self.lock:
            if self.queue:
                self.text_widget.configure(state="normal")
                for text in self.queue:
                    self.text_widget.insert("end", text)
                self.text_widget.see("end")
                self.text_widget.configure(state="disabled")
                self.queue.clear()

    def flush(self):
        pass

# --- CORE DOWNLOADER ENGINE ---
class BoredNoMore3Downloader:
    """Main downloader class that uses the engines module."""

    def __init__(self, directory=".", search="dark wallpaper", count=10, sources=None,
                 start_from=None, deep=False, random_src=False):
        self.directory = os.path.abspath(os.path.expanduser(directory))
        self.search = search
        self.target_count = count
        self.deep = deep
        self.downloaded_hashes = set()
        self.start_from = start_from
        self.total_saved = 0

        # Initialize download engines
        self.engines = DownloadEngines(self)

        # Available sources mapping to engine methods
        self.available_sources = {
            'unsplash': self.engines.download_from_unsplash,
            'pexels': self.engines.download_from_pexels,
            'pixabay': self.engines.download_from_pixabay,
            'picsum': self.engines.download_from_picsum,
            'wallhaven': self.engines.download_from_wallhaven,
            'google': self.engines.download_from_google,
            'bing': self.engines.download_from_bing,
        }

        # Handle source selection
        if random_src:
            import random
            self.sources = [random.choice(list(self.available_sources.keys()))]
            print(f"Random source selected: {self.sources[0]}")
        elif not sources:
            self.sources = list(self.available_sources.keys())
        else:
            self.sources = sources

        # Create directory if needed
        if not os.path.isdir(self.directory):
            os.makedirs(self.directory, exist_ok=True)
            print(f"Created directory: {self.directory}")

        self._initialize_numbering()

    def _initialize_numbering(self):
        """Scan existing files and determine next number."""
        existing_files = glob.glob(os.path.join(self.directory, "wallpaper*.jpg"))
        max_number = 0
        number_pattern = re.compile(r'wallpaper_(\d+)\.jpg')

        for filepath in existing_files:
            filename = os.path.basename(filepath)
            match = number_pattern.match(filename)
            if match:
                num = int(match.group(1))
                max_number = max(max_number, num)

            # Load hashes for duplicate detection
            if self.start_from is None:
                h = self._get_file_hash(filepath)
                if h:
                    self.downloaded_hashes.add(h)

        self.next_number = self.start_from if self.start_from is not None else max_number + 1

        if existing_files:
            print(f"Found {len(existing_files)} existing wallpapers")
            print(f"Starting from number: {self.next_number}")

    def _get_file_hash(self, filepath):
        """Calculate SHA256 hash of a file."""
        sha256_hash = hashlib.sha256()
        try:
            with open(filepath, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except:
            return None

    def save_image(self, image_data, source_name):
        """Save image with smart numbering."""
        if self.total_saved >= self.target_count:
            return "STOP"

        if not image_data or len(image_data) < 10000:
            return False

        # Check for duplicates (unless in overwrite mode)
        if self.start_from is None:
            file_hash = hashlib.sha256(image_data).hexdigest()
            if file_hash in self.downloaded_hashes:
                return False
            self.downloaded_hashes.add(file_hash)

        filename = f"wallpaper_{self.next_number:05d}.jpg"
        try:
            with open(os.path.join(self.directory, filename), "wb") as f:
                f.write(image_data)

            file_size_kb = len(image_data) / 1024
            print(f" {filename} ({source_name}) - {file_size_kb:.1f} KB")
            self.next_number += 1
            self.total_saved += 1
            return True
        except Exception as e:
            print(f" Error saving {filename}: {e}")
            return False

    def fetch_all_sources(self):
        """Download wallpapers from selected sources."""
        print(f"\n{'='*80}")
        print(f" BoredNoMore3 Downloader v{VERSION}")
        print(f"{'='*80}")
        print(f" Search: '{self.search}'")
        print(f" Target: {self.target_count} images")
        print(f" Sources: {', '.join(self.sources)}")
        print(f" Directory: {self.directory}")
        print(f"{'='*80}\n")

        for s in self.sources:
            if self.total_saved >= self.target_count:
                break
            if s in self.available_sources:
                try:
                    self.available_sources[s]()
                except Exception as e:
                    print(f"[{s}] Error: {e}")

        print(f"\n{'='*80}")
        print(f" Download Complete!")
        print(f" Total images saved: {self.total_saved}")
        print(f" Location: {self.directory}")
        print(f"{'='*80}")

# --- TRANSITION DESCRIPTIONS ---
TRANSITION_DESCRIPTIONS = {
    "instant-cut": "Instantly switches to the new wallpaper. No animation.",
    "fade": "Smooth crossfade between old and new wallpaper.",
    "fade-in": "Fades from black to the new wallpaper.",
    "fade-out": "Fades to black, then reveals the new wallpaper.",
    "slide-left": "New wallpaper slides in from the right over the old one.",
    "slide-right": "New wallpaper slides in from the left.",
    "slide-up": "New wallpaper slides in from the bottom.",
    "slide-down": "New wallpaper slides in from the top.",
    "zoom-in": "New wallpaper zooms in from the center.",
    "zoom-out": "Old wallpaper zooms out, revealing the new one underneath.",
    "focus-in": "Blur shifts from old to new wallpaper.",
    "focus-out": "Blur shifts from new to old (reverse focus).",
    "wipe-left-to-right": "Wipe reveal from left to right.",
    "wipe-right-to-left": "Wipe reveal from right to left.",
    "wipe-top-to-bottom": "Wipe reveal from top to bottom.",
    "wipe-bottom-to-top": "Wipe reveal from bottom to top.",
    "diagonal-top-left-to-bottom-right": "Diagonal wipe from top-left corner.",
    "diagonal-bottom-right-to-top-left": "Diagonal wipe from bottom-right.",
    "diagonal-top-right-to-bottom-left": "Diagonal wipe from top-right.",
    "diagonal-bottom-left-to-top-right": "Diagonal wipe from bottom-left.",
    "iris-in": "Circular iris expands from center revealing new wallpaper.",
    "iris-out": "Circular iris closes to center showing new underneath.",
    "clock-wipe-clockwise": "Clock hand wipe rotating clockwise.",
    "clock-wipe-counterclockwise": "Clock hand wipe rotating counterclockwise.",
    "box-in": "Square expands from center revealing new wallpaper.",
    "box-out": "Square collapses to center.",
    "diamond-in": "Diamond shape expands from center.",
    "diamond-out": "Diamond shape collapses to center.",
    "page-curl-top-right": "Realistic page curl effect from top-right corner.",
    "page-curl-bottom-left": "Page curl from bottom-left corner.",
    "cube-rotate-left": "3D cube rotation to the left.",
    "cube-rotate-right": "3D cube rotation to the right.",
    "cube-rotate-up": "3D cube rotation upward.",
    "cube-rotate-down": "3D cube rotation downward.",
    "glitch-transition": "Digital glitch effect with RGB separation.",
    "checker-dissolve": "Checkerboard pattern dissolve.",
    "pixelate-transition": "Gradual pixelation dissolve.",
    "wave-left-to-right": "Sinusoidal wave distortion moving left to right.",
    "venetian-blinds-horizontal": "Horizontal blind slats opening.",
    "venetian-blinds-vertical": "Vertical blind slats opening.",
}

# --- GUI LAYER ---
class BoredNoMoreGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(f"BoredNoMore3 Downloader v{VERSION}")
        self.geometry("1200x950")
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        self.bg_process = None
        self.is_running = False
        self.redirector = None

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)

        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color="#111827")
        self.sidebar.grid(row=0, column=0, rowspan=3, sticky="nsew")

        ctk.CTkLabel(
            self.sidebar, text="BNM3\nDownloader",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="#3B82F6"
        ).pack(pady=40)

        ctk.CTkButton(
            self.sidebar, text="Help",
            fg_color="transparent", border_width=1,
            hover_color="#3B82F6",
            command=lambda: self.run_cli("-h")
        ).pack(pady=5, padx=20, fill="x")

        ctk.CTkButton(
            self.sidebar, text="Credits",
            fg_color="transparent", border_width=1,
            hover_color="#3B82F6",
            command=lambda: self.run_cli("-c")
        ).pack(pady=5, padx=20, fill="x")

        ctk.CTkButton(
            self.sidebar, text="Version",
            fg_color="transparent", border_width=1,
            hover_color="#3B82F6",
            command=lambda: self.run_cli("-v")
        ).pack(pady=5, padx=20, fill="x")

        # Transition Info Button
        ctk.CTkButton(
            self.sidebar, text="Transition Info",
            fg_color="#6366F1", hover_color="#4F46E5",
            command=self.show_transition_info
        ).pack(pady=15, padx=20, fill="x")

        # End Program Button
        self.exit_btn = ctk.CTkButton(
            self.sidebar, text="End Program",
            fg_color="#EF4444", hover_color="#B91C1C",
            font=ctk.CTkFont(weight="bold"),
            command=self.quit_app
        )
        self.exit_btn.pack(side="bottom", pady=30, padx=20, fill="x")

        # Main Layout
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, padx=20, pady=10, sticky="nsew")

        ctk.CTkLabel(
            self.main_frame, text="Search Keywords",
            font=ctk.CTkFont(weight="bold", size=12)
        ).pack(anchor="w", padx=10, pady=(10, 5))

        self.search_entry = ctk.CTkEntry(
            self.main_frame, width=600, height=35,
            placeholder_text="Enter search keywords..."
        )
        self.search_entry.pack(pady=(0, 15), padx=10, anchor="w", fill="x")
        self.search_entry.insert(0, "dark wallpaper")

        # Directory selection
        dir_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        dir_frame.pack(fill="x", padx=10, pady=(0, 15))

        self.path_var = tk.StringVar(value=os.getcwd())
        self.dir_btn = ctk.CTkButton(
            dir_frame, text="Select Folder",
            width=150, command=self.select_dir
        )
        self.dir_btn.pack(side="left")

        ctk.CTkLabel(
            dir_frame, textvariable=self.path_var,
            font=("Courier", 10), text_color="#64748B"
        ).pack(side="left", padx=10, fill="x", expand=True)

        # Source selection
        ctk.CTkLabel(
            self.main_frame, text="Download Sources",
            font=ctk.CTkFont(weight="bold", size=12)
        ).pack(anchor="w", padx=10, pady=(10, 5))

        self.source_frame = ctk.CTkFrame(self.main_frame, fg_color="#1E293B", corner_radius=8)
        self.source_frame.pack(fill="x", padx=10, pady=5)

        self.sources_vars = {}
        srcs = ['unsplash', 'pexels', 'pixabay', 'picsum', 'wallhaven', 'google', 'bing']
        for i, s in enumerate(srcs):
            v = tk.BooleanVar(value=True)
            cb = ctk.CTkCheckBox(
                self.source_frame, text=s.capitalize(),
                variable=v, hover_color="#3B82F6"
            )
            cb.grid(row=0, column=i, padx=10, pady=10)
            self.sources_vars[s] = v

        # Control options
        self.ctrl_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.ctrl_frame.pack(fill="x", padx=10, pady=10)

        self.deep_var = tk.BooleanVar(value=False)
        self.rand_var = tk.BooleanVar(value=False)

        self.deep_cb = ctk.CTkCheckBox(
            self.ctrl_frame, text="Deep Search (More Pages)",
            variable=self.deep_var
        )
        self.deep_cb.pack(side="left", padx=10)

        self.rand_cb = ctk.CTkCheckBox(
            self.ctrl_frame, text="Random Source Selection",
            variable=self.rand_var
        )
        self.rand_cb.pack(side="left", padx=10)

        # Count slider
        ctk.CTkLabel(
            self.main_frame, text="Download Count",
            font=ctk.CTkFont(weight="bold", size=12)
        ).pack(anchor="w", padx=10, pady=(10, 5))

        self.count_slider = ctk.CTkSlider(
            self.main_frame, from_=1, to=100,
            command=lambda v: self.count_lbl.configure(
                text=f"Total images to download: {int(v)}"
            )
        )
        self.count_slider.set(10)
        self.count_slider.pack(fill="x", padx=10)

        self.count_lbl = ctk.CTkLabel(
            self.main_frame, text="Total images to download: 10",
            font=("Courier", 11), text_color="#64748B"
        )
        self.count_lbl.pack(anchor="w", padx=15, pady=(5, 10))

        # Overwrite option
        ow_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        ow_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(
            ow_frame, text="Overwrite from number:",
            font=ctk.CTkFont(size=11)
        ).pack(side="left")

        self.ow_entry = ctk.CTkEntry(
            ow_frame, placeholder_text="Leave empty for append mode",
            width=200
        )
        self.ow_entry.pack(side="left", padx=10)

        # Console
        console_label = ctk.CTkLabel(
            self, text="Console Output",
            font=ctk.CTkFont(weight="bold", size=12)
        )
        console_label.grid(row=1, column=1, padx=20, pady=(10, 5), sticky="w")

        self.console_box = ctk.CTkTextbox(
            self, font=("Courier New", 11),
            fg_color="#000000", text_color="#10B981",
            state="disabled", wrap="word"
        )
        self.console_box.grid(row=1, column=1, padx=20, pady=(0, 10), sticky="nsew")

        # Setup redirector and start periodic update
        self.redirector = RedirectText(self.console_box)
        sys.stdout = self.redirector
        sys.stderr = self.redirector
        self.update_console()

        # Action Buttons
        self.btn_f = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_f.grid(row=2, column=1, padx=20, pady=(0, 20), sticky="ew")

        self.launch_btn = ctk.CTkButton(
            self.btn_f, text="START DOWNLOAD",
            height=50, fg_color="#10B981",
            hover_color="#059669",
            font=ctk.CTkFont(weight="bold", size=14),
            command=self.start
        )
        self.launch_btn.pack(side="left", expand=True, fill="x", padx=(0, 5))

        self.stop_btn = ctk.CTkButton(
            self.btn_f, text="STOP",
            height=50, width=150,
            fg_color="#EF4444", hover_color="#DC2626",
            font=ctk.CTkFont(weight="bold", size=14),
            state="disabled", command=self.stop_mission
        )
        self.stop_btn.pack(side="right")

        self.input_widgets = [
            self.search_entry, self.dir_btn, self.deep_cb,
            self.rand_cb, self.count_slider, self.ow_entry,
            self.launch_btn
        ]

        print(f" BoredNoMore3 Downloader GUI v{VERSION}")
        print("Ready to download wallpapers!")

    def update_console(self):
        """Periodically update console from buffer."""
        if self.redirector:
            self.redirector.flush_to_widget()
        self.after(100, self.update_console)

    def show_transition_info(self):
        """Show a window with all transition names and descriptions."""
        info_win = ctk.CTkToplevel(self)
        info_win.title("Wallpaper Transition Effects")
        info_win.geometry("900x700")
        info_win.transient(self)
        info_win.grab_set()

        ctk.CTkLabel(
            info_win, text="Available Transition Effects",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=15)

        # Scrollable frame
        canvas = tk.Canvas(info_win, bg="#1E293B")
        scrollbar = ttk.Scrollbar(info_win, orient="vertical", command=canvas.yview)
        scrollable_frame = ctk.CTkFrame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        scrollbar.pack(side="right", fill="y")

        # Populate transitions
        sorted_trans = sorted(TRANSITION_DESCRIPTIONS.items(), key=lambda x: x[0])

        for name, desc in sorted_trans:
            frame = ctk.CTkFrame(scrollable_frame, fg_color="transparent")
            frame.pack(fill="x", padx=15, pady=5)

            ctk.CTkLabel(
                frame, text=name.replace("-", " ").title(),
                font=ctk.CTkFont(weight="bold", size=13),
                anchor="w"
            ).pack(anchor="w")

            ctk.CTkLabel(
                frame, text=desc,
                font=ctk.CTkFont(size=11),
                text_color="#94A3B8", anchor="w", wraplength=800, justify="left"
            ).pack(anchor="w", pady=(0, 10))

    def get_backend_command(self):
        """Detect if running from source or as binary."""
        if getattr(sys, 'frozen', False):
            return ["borednomore3-downloader"]
        if os.path.exists("borednomore3_downloader.py"):
            return [sys.executable, "borednomore3_downloader.py"]
        return ["borednomore3-downloader"]

    def run_cli(self, flag):
        """Run CLI command and show output."""
        def exec_cli():
            cmd = self.get_backend_command() + [flag]
            print(f"\n[*] Executing: {' '.join(cmd)}\n")
            try:
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                if res.stdout:
                    print(res.stdout)
                if res.stderr:
                    print(f"[ERROR] {res.stderr}")
            except subprocess.TimeoutExpired:
                print("[ERROR] Command timed out")
            except Exception as e:
                print(f"[ERROR] {e}")
        threading.Thread(target=exec_cli, daemon=True).start()

    def select_dir(self):
        """Open directory selection dialog."""
        d = filedialog.askdirectory(initialdir=self.path_var.get())
        if d:
            self.path_var.set(d)
            print(f" Directory set to: {d}")

    def stop_mission(self):
        """Signal to stop the download."""
        self.is_running = False
        print("\n Stopping download... (finishing current image)")

    def start(self):
        """Start the download process."""
        self.is_running = True
        for w in self.input_widgets:
            w.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        threading.Thread(target=self.run_logic, daemon=True).start()

    def run_logic(self):
        """Main download logic running in thread."""
        try:
            ow = self.ow_entry.get()
            selected_sources = [s for s, v in self.sources_vars.items() if v.get()]

            if not selected_sources:
                print(" Error: No sources selected! Please select at least one source.")
                self.after(0, self.reset_ui)
                return

            downloader = BoredNoMore3Downloader(
                directory=self.path_var.get(),
                search=self.search_entry.get(),
                count=int(self.count_slider.get()),
                sources=selected_sources,
                start_from=int(ow) if ow.isdigit() else None,
                deep=self.deep_var.get(),
                random_src=self.rand_var.get()
            )

            # Run source by source, checking stop signal
            for s in downloader.sources:
                if not self.is_running or downloader.total_saved >= downloader.target_count:
                    break
                if s in downloader.available_sources:
                    downloader.available_sources[s]()

            if not self.is_running:
                print("\n Download stopped by user")

            print(f"\n{'='*80}")
            print(f" Session Complete!")
            print(f" Images saved: {downloader.total_saved}")
            print(f"{'='*80}")

        except Exception as e:
            print(f"\n Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.after(0, self.reset_ui)

    def reset_ui(self):
        """Reset UI to initial state."""
        for w in self.input_widgets:
            w.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self.is_running = False

    def quit_app(self):
        """Safely exit the application."""
        if messagebox.askokcancel("Quit", "Do you really want to exit BoredNoMore3?"):
            self.is_running = False
            self.destroy()
            sys.exit(0)

if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    app = BoredNoMoreGUI()
    app.mainloop()
