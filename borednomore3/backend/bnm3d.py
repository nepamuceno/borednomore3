#!/usr/bin/env python3
"""
Borednomore3 Wallpaper Downloader
Backend v0.0.9 - Full Feature Set
- Real-time flushing for GUI
- Exclusive Mode Logic (env, conf, keys)
- Storage Audit (Statistics)
- Restored Verbose & Debug Flags
"""
import os, sys, argparse, requests, random, hashlib, time, re
from pathlib import Path
from datetime import datetime
from collections import Counter
import functools

# Force every print in the backend to flush immediately
print = functools.partial(print, flush=True)


VERSION = "0.0.9"
SCRIPTNAME = "bnm3d.py"

# Global tracking
site_stats = {"pexels": 0, "unsplash": 0, "pixabay": 0}
error_count = 0

def log(level, message, timestamp=True):
    """Standard plaintext logger with forced flush for real-time GUI updates."""
    time_str = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] " if timestamp else ""
    print(f"{time_str}[{level:8}] {message}")
    sys.stdout.flush()

def load_config(config_path):
    config_data = {}
    if config_path and os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'): continue
                    if '=' in line:
                        k, v = line.split('=', 1)
                        config_data[k.strip().upper()] = v.strip().strip('"').strip("'")
        except Exception as e:
            log("ERROR", f"Failed to read config {config_path}: {e}")
    return config_data

def get_exclusive_config(args):
    """
    Priority Modes:
    - env: Only PWD .env
    - conf: Only explicit -c file
    - keys: Only CLI/GUI passed keys
    """
    conf = {}
    mode = args.mode.lower() if args.mode else "env"

    if mode == "env":
        env_path = Path(os.getcwd()) / ".env"
        if env_path.exists():
            if args.debug: log("DEBUG", f"MODE: ENV. Loading from {env_path}")
            conf = load_config(env_path)
        else:
            log("CRITICAL", "MODE: ENV selected but no .env found in PWD.")
            sys.exit(1)

    elif mode == "conf":
        if args.config and os.path.exists(args.config):
            if args.debug: log("DEBUG", f"MODE: CONF. Loading from {args.config}")
            conf = load_config(args.config)
        else:
            log("CRITICAL", "MODE: CONF selected but no valid config (-c) provided.")
            sys.exit(1)

    elif mode == "keys":
        if args.debug: log("DEBUG", "MODE: KEYS. Using GUI-passed parameters.")
        if args.pexels: conf["PEXELS_API"] = args.pexels
        if args.unsplash: conf["UNSPLASH_API"] = args.unsplash
        if args.pixabay: conf["PIXABAY_API"] = args.pixabay
    
    # Non-API Defaults
    conf.setdefault("SEARCH", "wallpaper")
    conf.setdefault("NUMBER", "5")
    conf.setdefault("OUTPUT", "./wallpapers")
    return conf

def get_storage_stats(outdir):
    """Scan folder and count file extensions (Statistics)."""
    path = Path(outdir)
    if not path.exists(): return {}
    # Count every file extension in the folder
    files = [f.suffix.lower() for f in path.iterdir() if f.is_file()]
    return Counter(files)

def get_existing_hashes(outdir, debug=False):
    hashes = set()
    files = list(Path(outdir).glob("*.jpg"))
    if debug: log("DEBUG", f"Scanning {len(files)} files for duplicates.")
    for file in files:
        try:
            with open(file, "rb") as f:
                hashes.add(hashlib.sha256(f.read()).hexdigest())
        except: continue
    return hashes

def get_next_index(outdir):
    highest = 0
    if not os.path.exists(outdir): return 1
    for f in os.listdir(outdir):
        match = re.search(r"wallpaper(\d+)\.jpg", f)
        if match: highest = max(highest, int(match.group(1)))
    return highest + 1

# --- API Fetchers ---

def fetch_pexels(query, n, api_key, base_url, deep=False, debug=False):
    if not api_key or n <= 0: return []
    headers = {"Authorization": api_key}
    page = random.randint(2, 20) if deep else 1
    url = f"{base_url}?query={query}&per_page={n}&page={page}"
    if debug: log("DEBUG", f"PEXELS: Fetching {n} items from {url}")
    try:
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        return [p["src"]["original"] for p in r.json().get("photos", [])]
    except Exception as e:
        log("ERROR", f"PEXELS: {e}")
        return []

def fetch_unsplash(query, n, api_key, base_url, deep=False, debug=False):
    if not api_key or n <= 0: return []
    page = random.randint(2, 10) if deep else 1
    url = f"{base_url}?query={query}&per_page={n}&page={page}&client_id={api_key}"
    if debug: log("DEBUG", f"UNSPLASH: Fetching {n} items from {url}")
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return [p["urls"]["full"] for p in r.json().get("results", [])]
    except Exception as e:
        log("ERROR", f"UNSPLASH: {e}")
        return []

def fetch_pixabay(query, n, api_key, base_url, deep=False, debug=False):
    if not api_key or n <= 0: return []
    page = random.randint(2, 10) if deep else 1
    url = f"{base_url}?key={api_key}&q={query}&per_page={max(3, n)}&page={page}"
    if debug: log("DEBUG", f"PIXABAY: Fetching {n} items from {url}")
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return [p["largeImageURL"] for p in r.json().get("hits", [])]
    except Exception as e:
        log("ERROR", f"PIXABAY: {e}")
        return []

def download_batch(urls, outdir, start_index, existing_hashes, site_name, verbose=False, debug=False):
    global error_count
    saved_count = 0
    curr_idx = start_index
    for u in urls:
        try:
            res = requests.get(u, timeout=15)
            res.raise_for_status()
            data = res.content
            file_h = hashlib.sha256(data).hexdigest()
            if file_h in existing_hashes:
                if verbose: log("SKIP", f"Duplicate found on {site_name}.")
                continue
            fn = os.path.join(outdir, f"wallpaper{curr_idx:05d}.jpg")
            with open(fn, "wb") as f: f.write(data)
            existing_hashes.add(file_h)
            site_stats[site_name] += 1
            if verbose: log("INFO", f"Saved: {fn} ({site_name})")
            curr_idx += 1
            saved_count += 1
        except Exception as e:
            log("ERROR", f"FILE: {e}")
            error_count += 1
    return saved_count

def main():
    parser = argparse.ArgumentParser(description=f"{SCRIPTNAME} v{VERSION}")
    # Configuration Mode
    parser.add_argument("-m", "--mode", choices=['env', 'conf', 'keys'], default='env', help="Config priority mode")
    
    # Standard Options
    parser.add_argument("-s", "--search", help="Search query")
    parser.add_argument("-n", "--number", type=int, help="Number of images")
    parser.add_argument("-w", "--website", help="Specific site (pexels, unsplash, pixabay, all)")
    parser.add_argument("-c", "--config", help="Path to .conf file")
    
    # API Keys
    parser.add_argument("--pexels", help="Pexels Key")
    parser.add_argument("--unsplash", help="Unsplash Key")
    parser.add_argument("--pixabay", help="Pixabay Key")
    
    # Flags
    parser.add_argument("-D", "--deep", action="store_true", help="Deep search (random page)")
    parser.add_argument("-r", "--randomize", action="store_true", help="Randomize site selection")
    parser.add_argument("--overwrite", type=int, help="Start index for filename")
    parser.add_argument("-v", "--verbose", action="store_true", help="Show saving details")
    parser.add_argument("-d", "--debug", action="store_true", help="Show technical debug info")
    
    args = parser.parse_args()

    cfg = get_exclusive_config(args)
    
    # Merge Argparse and Config
    search = args.search or cfg.get("SEARCH", "wallpaper")
    target_n = args.number or int(cfg.get("NUMBER", 5))
    output = cfg.get("OUTPUT", "./wallpapers")
    deep_mode = args.deep or cfg.get("DEEP", "false").lower() == "true"
    debug_mode = args.debug
    verbose_mode = args.verbose

    sources = {
        "pexels": {"key": cfg.get("PEXELS_API"), "url": cfg.get("PEXELS_URL", "https://api.pexels.com/v1/search")},
        "unsplash": {"key": cfg.get("UNSPLASH_API"), "url": cfg.get("UNSPLASH_URL", "https://api.unsplash.com/search/photos")},
        "pixabay": {"key": cfg.get("PIXABAY_API"), "url": cfg.get("PIXABAY_URL", "https://pixabay.com/api/")}
    }
    
    active_sites = [k for k, v in sources.items() if v["key"]]
    if args.website and args.website != "all":
        active_sites = [args.website] if args.website in active_sites else []

    if not active_sites:
        log("CRITICAL", f"No API keys found in mode: {args.mode}")
        sys.exit(1)

    os.makedirs(output, exist_ok=True)
    start_idx = args.overwrite if args.overwrite is not None else get_next_index(output)
    existing_hashes = get_existing_hashes(output, debug_mode)

    total_saved = 0
    
    # Distribution Logic
    if args.randomize:
        if debug_mode: log("DEBUG", "Randomization flag (-r) is active.")
        site_distribution = [random.choice(active_sites) for _ in range(target_n)]
    else:
        per_site = target_n // len(active_sites)
        rem = target_n % len(active_sites)
        site_distribution = []
        for site in active_sites:
            count = per_site + (1 if rem > 0 else 0)
            site_distribution.extend([site] * count)
            rem -= 1

    log("STATUS", f"Starting in {args.mode.upper()} mode. Query: '{search}' | Target: {target_n}")

    for site in active_sites:
        needed = site_distribution.count(site)
        if needed <= 0: continue
        func = getattr(sys.modules[__name__], f"fetch_{site}")
        urls = func(search, needed, sources[site]["key"], sources[site]["url"], deep_mode, debug_mode)
        saved = download_batch(urls, output, start_idx + total_saved, existing_hashes, site, verbose_mode, debug_mode)
        total_saved += saved

    # --- FINAL REPORT & STORAGE AUDIT ---
    storage_stats = get_storage_stats(output)
    
    print("\n" + "="*50); sys.stdout.flush()
    log("REPORT", f"BNM3D {VERSION} SUMMARY (Mode: {args.mode})", timestamp=False)
    print("="*50); sys.stdout.flush()
    print(f"Actually Saved    : {total_saved}"); sys.stdout.flush()
    print(f"System Errors     : {error_count}"); sys.stdout.flush()
    print("-" * 50); sys.stdout.flush()
    print(f"STORAGE DIRECTORY : {os.path.abspath(output)}"); sys.stdout.flush()
    for ext, count in sorted(storage_stats.items()):
        ext_label = ext.upper() if ext else "NO EXT"
        print(f" {ext_label:<12}: {count} files")
    print("="*50); sys.stdout.flush()
    
    return total_saved

if __name__ == "__main__":
    main()
