import os
import sys
import random
import hashlib
import requests
import glob
import re
import threading
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
from urllib.parse import quote

# --- LOG REDIRECTION ---
class RedirectText:
    def __init__(self, text_widget):
        self.text_widget = text_widget
    def write(self, string):
        self.text_widget.configure(state="normal")
        self.text_widget.insert("end", string)
        self.text_widget.see("end")
        self.text_widget.configure(state="disabled")
    def flush(self): pass

# --- CORE DOWNLOADER ENGINE ---
class BoredNoMore3Downloader:
    def __init__(self, directory=".", search="dark wallpaper", count=10, sources=None, start_from=None, deep=False, random_src=False):
        self.directory = os.path.abspath(os.path.expanduser(directory))
        self.search = search
        self.target_count = count
        self.deep = deep
        self.downloaded_hashes = set()
        self.start_from = start_from
        
        # 1. THE GLOBAL COUNTER
        self.total_saved = 0 
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.google.com/'
        }

        self.available_sources = {
            'unsplash': self.download_from_unsplash,
            'pexels': self.download_from_pexels,
            'pixabay': self.download_from_pixabay,
            'picsum': self.download_from_picsum,
            'wallhaven': self.download_from_wallhaven,
            'google': self.download_from_google,
            'bing': self.download_from_bing,
        }

        if random_src:
            self.sources = [random.choice(list(self.available_sources.keys()))]
        elif not sources:
            self.sources = list(self.available_sources.keys())
        else:
            self.sources = sources
        
        if not os.path.isdir(self.directory):
            os.makedirs(self.directory, exist_ok=True)
        self._initialize_numbering()

    def _initialize_numbering(self):
        existing_files = glob.glob(os.path.join(self.directory, "*.jpg"))
        max_number = 0
        number_pattern = re.compile(r'(\d+)')
        for filepath in existing_files:
            numbers = number_pattern.findall(os.path.basename(filepath))
            if numbers: max_number = max(max_number, int(numbers[-1]))
            if self.start_from is None:
                h = self._get_file_hash(filepath)
                if h: self.downloaded_hashes.add(h)
        self.next_number = self.start_from if self.start_from is not None else max_number + 1

    def _get_file_hash(self, filepath):
        sha256_hash = hashlib.sha256()
        try:
            with open(filepath, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except: return None

    def _save_image(self, image_data, source_name):
        # 2. STOP IF GLOBAL LIMIT REACHED
        if self.total_saved >= self.target_count: return "STOP"
        
        if not image_data or len(image_data) < 10000: return False 
        if self.start_from is None:
            file_hash = hashlib.sha256(image_data).hexdigest()
            if file_hash in self.downloaded_hashes: return False
            self.downloaded_hashes.add(file_hash)
        
        filename = f"wallpaper_{self.next_number:05d}.jpg"
        try:
            with open(os.path.join(self.directory, filename), "wb") as f: f.write(image_data)
            print(f"  [OK] {filename} ({source_name})")
            self.next_number += 1
            # INCREMENT GLOBAL COUNTER
            self.total_saved += 1
            return True
        except: return False

    # --- ENGINES (Now all checking self.total_saved) ---

    def download_from_unsplash(self):
        print("\n--- Unsplash ---")
        for _ in range(self.target_count * 3):
            if self.total_saved >= self.target_count: break
            try:
                url = f"https://source.unsplash.com/featured/1920x1080/?{quote(self.search)}&sig={random.random()}"
                r = requests.get(url, headers=self.headers, timeout=15)
                if r.status_code == 200:
                    if self._save_image(r.content, "Unsplash") == "STOP": break
            except: continue

    def download_from_pexels(self):
        print("\n--- Pexels ---")
        pages = range(1, 10) if self.deep else [1]
        for page in pages:
            if self.total_saved >= self.target_count: break
            try:
                r = requests.get(f"https://www.pexels.com/search/{quote(self.search)}/?page={page}", headers=self.headers, timeout=15)
                urls = re.findall(r'https://images\.pexels\.com/photos/\d+/pexels-photo-\d+\.jpeg\?auto=compress&cs=tinysrgb&w=1260', r.text)
                for u in list(set(urls)):
                    if self.total_saved >= self.target_count: return
                    img = requests.get(u, headers=self.headers, timeout=15).content
                    if self._save_image(img, "Pexels") == "STOP": return
            except: continue

    def download_from_pixabay(self):
        print("\n--- Pixabay ---")
        pages = range(1, 10) if self.deep else [1]
        for page in pages:
            if self.total_saved >= self.target_count: break
            try:
                r = requests.get(f"https://pixabay.com/images/search/{quote(self.search)}/?pagi={page}", headers=self.headers, timeout=15)
                urls = re.findall(r'https://cdn\.pixabay\.com/photo/[^"]+__340\.jpg', r.text)
                for u in list(set(urls)):
                    if self.total_saved >= self.target_count: return
                    high_res = u.replace("__340", "_1280")
                    img = requests.get(high_res, headers=self.headers, timeout=15).content
                    if self._save_image(img, "Pixabay") == "STOP": return
            except: continue

    def download_from_google(self):
        print("\n--- Google ---")
        try:
            r = requests.get(f"https://www.google.com/search?q={quote(self.search)}&tbm=isch&asearch=ichunk&async=_id:rg_s,_pms:s", headers=self.headers, timeout=15)
            urls = re.findall(r'https://[^"]+?\.(?:jpg|jpeg|png)', r.text)
            for u in list(set(urls)):
                if self.total_saved >= self.target_count: break
                if "gstatic" in u: continue
                try:
                    img = requests.get(u, headers=self.headers, timeout=10).content
                    if self._save_image(img, "Google") == "STOP": break
                except: continue
        except: pass

    def download_from_bing(self):
        print("\n--- Bing ---")
        offsets = range(0, 300, 30) if self.deep else [0]
        for offset in offsets:
            if self.total_saved >= self.target_count: break
            try:
                r = requests.get(f"https://www.bing.com/images/search?q={quote(self.search)}&first={offset}", headers=self.headers, timeout=15)
                urls = re.findall(r'murl&quot;:&quot;(https?://[^&]+?\.(?:jpg|jpeg|png))', r.text)
                for u in urls:
                    if self.total_saved >= self.target_count: break
                    try:
                        img = requests.get(u, headers=self.headers, timeout=10).content
                        if self._save_image(img, "Bing") == "STOP": break
                    except: continue
            except: break

    def download_from_picsum(self):
        print("\n--- Picsum ---")
        # Loop based on target remaining
        for _ in range(self.target_count):
            if self.total_saved >= self.target_count: break
            try:
                r = requests.get(f"https://picsum.photos/1920/1080?random={random.random()}", timeout=15)
                if self._save_image(r.content, "Picsum") == "STOP": break
            except: continue

    def download_from_wallhaven(self):
        print("\n--- Wallhaven ---")
        pages = range(1, 10) if self.deep else [1]
        for page in pages:
            if self.total_saved >= self.target_count: break
            try:
                api_url = f"https://wallhaven.cc/api/v1/search?q={quote(self.search)}&page={page}"
                data = requests.get(api_url, headers=self.headers, timeout=15).json()
                for item in data.get('data', []):
                    if self.total_saved >= self.target_count: break
                    img = requests.get(item['path'], headers=self.headers, timeout=15).content
                    if self._save_image(img, "Wallhaven") == "STOP": return
            except: break

    def fetch_all_sources(self):
        for s in self.sources:
            if self.total_saved >= self.target_count: break
            if s in self.available_sources: self.available_sources[s]()
        print(f"\n[DONE] Total images saved: {self.total_saved}")

# --- GUI LAYER ---
class BoredNoMoreGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("BoredNoMore3")
        self.geometry("1100x900")
        ctk.set_appearance_mode("Dark")
        
        # --- FIX: Row 1 (Console) gets the weight, not Row 0 ---
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=0) # Inputs stay fixed size
        self.grid_rowconfigure(1, weight=1) # Console expands to fill space
        self.grid_rowconfigure(2, weight=0) # Button stays at bottom

        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, rowspan=3, sticky="nsew")
        ctk.CTkLabel(self.sidebar, text="BNM3", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=30)
        
        ctk.CTkButton(self.sidebar, text="Help", fg_color="transparent", border_width=1, command=lambda: self.run_cli("-h")).pack(pady=5, padx=20, fill="x")
        ctk.CTkButton(self.sidebar, text="Credits", fg_color="transparent", border_width=1, command=lambda: self.run_cli("-c")).pack(pady=5, padx=20, fill="x")
        ctk.CTkButton(self.sidebar, text="Version", fg_color="transparent", border_width=1, command=lambda: self.run_cli("-v")).pack(pady=5, padx=20, fill="x")
        self.exit_btn = ctk.CTkButton(self.sidebar, text="Exit Program", fg_color="#721c24", hover_color="#af233a", command=self.destroy)
        self.exit_btn.pack(side="bottom", pady=20, padx=20, fill="x")

        # Main Layout (Inputs)
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, padx=20, pady=10, sticky="nsew")

        ctk.CTkLabel(self.main_frame, text="Search Keywords", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10)
        self.search_entry = ctk.CTkEntry(self.main_frame, width=600); self.search_entry.pack(pady=(0, 15), padx=10, anchor="w")
        self.search_entry.insert(0, "dark wallpaper")

        self.path_var = tk.StringVar(value=os.getcwd())
        self.dir_btn = ctk.CTkButton(self.main_frame, text="Select Folder", command=self.select_dir); self.dir_btn.pack(anchor="w", padx=10)
        ctk.CTkLabel(self.main_frame, textvariable=self.path_var, font=("Courier", 11), text_color="gray").pack(anchor="w", padx=10, pady=(0,15))

        self.source_frame = ctk.CTkFrame(self.main_frame); self.source_frame.pack(fill="x", padx=10, pady=5)
        self.sources_vars = {}
        srcs = ['unsplash', 'pexels', 'pixabay', 'picsum', 'wallhaven', 'google', 'bing']
        for i, s in enumerate(srcs):
            v = tk.BooleanVar(value=False)
            cb = ctk.CTkCheckBox(self.source_frame, text=s.capitalize(), variable=v)
            cb.grid(row=0, column=i, padx=10, pady=10)
            self.sources_vars[s] = v

        self.ctrl_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent"); self.ctrl_frame.pack(fill="x", padx=10, pady=10)
        self.deep_var = tk.BooleanVar(value=False); self.rand_var = tk.BooleanVar(value=False)
        self.deep_cb = ctk.CTkCheckBox(self.ctrl_frame, text="Deep Search", variable=self.deep_var); self.deep_cb.pack(side="left", padx=10)
        self.rand_cb = ctk.CTkCheckBox(self.ctrl_frame, text="Random Engines", variable=self.rand_var); self.rand_cb.pack(side="left", padx=10)

        self.count_slider = ctk.CTkSlider(self.main_frame, from_=1, to=100, command=lambda v: self.count_lbl.configure(text=f"Global Download Limit: {int(v)} total images"))
        self.count_slider.set(10); self.count_slider.pack(fill="x", padx=10)
        self.count_lbl = ctk.CTkLabel(self.main_frame, text="Global Download Limit: 10 total images"); self.count_lbl.pack(anchor="w", padx=15)

        self.ow_entry = ctk.CTkEntry(self.main_frame, placeholder_text="Overwrite ID", width=120); self.ow_entry.pack(anchor="w", padx=10)

        # --- Console Box (Now properly stretching) ---
        self.console_box = ctk.CTkTextbox(self, font=("Courier New", 12), fg_color="#000000", text_color="#00ff00", state="disabled")
        self.console_box.grid(row=1, column=1, padx=20, pady=(0, 20), sticky="nsew")
        sys.stdout = RedirectText(self.console_box)

        # --- Launch Button (Stays at the bottom) ---
        self.launch_btn = ctk.CTkButton(self, text="START MISSION", height=50, fg_color="#28a745", command=self.start)
        self.launch_btn.grid(row=2, column=1, padx=20, pady=(0, 20), sticky="ew")

        self.input_widgets = [self.search_entry, self.dir_btn, self.deep_cb, self.rand_cb, self.count_slider, self.ow_entry, self.launch_btn]

    def run_cli(self, flag):
        try:
            res = subprocess.run([sys.executable, "borednomore3_downloader.py", flag], capture_output=True, text=True)
            print(res.stdout)
        except: print("[ERROR] CLI failure.")

    def select_dir(self):
        d = filedialog.askdirectory()
        if d: self.path_var.set(d)

    def start(self):
        for w in self.input_widgets: w.configure(state="disabled")
        threading.Thread(target=self.run_logic, daemon=True).start()

    def run_logic(self):
        try:
            ow = self.ow_entry.get()
            downloader = BoredNoMore3Downloader(
                directory=self.path_var.get(),
                search=self.search_entry.get(),
                count=int(self.count_slider.get()),
                sources=[s for s,v in self.sources_vars.items() if v.get()],
                start_from=int(ow) if ow.isdigit() else None,
                deep=self.deep_var.get(),
                random_src=self.rand_var.get()
            )
            downloader.fetch_all_sources()
        except Exception as e: print(f"\n[ERROR] {e}")
        finally:
            for w in self.input_widgets: w.configure(state="normal")
            self.launch_btn.configure(text="START MISSION")

if __name__ == "__main__":
    app = BoredNoMoreGUI()
    app.mainloop()
