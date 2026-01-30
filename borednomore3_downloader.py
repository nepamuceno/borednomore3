#!/usr/bin/env python3
import os, sys, argparse, requests, random, hashlib, time
from dotenv import load_dotenv

VERSION = "0.0.1"
SCRIPTNAME = "borednomore3_downloader.py"
CREDITS = "Author: Nepamuceno\nEmail: (hidden)\nGitHub: https://github.com/nepamuceno/borednomore3"

load_dotenv()

PEXELS_API = os.getenv("PEXELS_API")
UNSPLASH_API = os.getenv("UNSPLASH_API")
PIXABAY_API = os.getenv("PIXABAY_API")

downloaded_hashes = set()
site_counts = {"pexels":0, "unsplash":0, "pixabay":0}
error_count = 0

def file_hash(data):
    h = hashlib.sha256()
    h.update(data)
    return h.hexdigest()

def fetch_pexels(query, n, debug=False):
    if not PEXELS_API or n <= 0: return []
    print(f"[INFO] Fetching {n} images from Pexels...")
    headers = {"Authorization": PEXELS_API}
    url = f"https://api.pexels.com/v1/search?query={query}&per_page={n}"
    if debug: print("[DEBUG] Pexels URL:", url)
    r = requests.get(url, headers=headers)
    results = [p["src"]["original"].replace("\\u0026","&") for p in r.json().get("photos", [])]
    site_counts["pexels"] += len(results)
    return results

def fetch_unsplash(query, n, debug=False):
    if not UNSPLASH_API or n <= 0: return []
    print(f"[INFO] Fetching {n} images from Unsplash...")
    url = f"https://api.unsplash.com/search/photos?query={query}&per_page={n}&client_id={UNSPLASH_API}"
    if debug: print("[DEBUG] Unsplash URL:", url)
    r = requests.get(url)
    results = [p["urls"]["full"] for p in r.json().get("results", [])]
    site_counts["unsplash"] += len(results)
    return results

def fetch_pixabay(query, n, debug=False):
    if not PIXABAY_API or n <= 0: return []
    print(f"[INFO] Fetching {n} images from Pixabay...")
    n = max(3, min(n, 200))  # enforce valid range
    url = f"https://pixabay.com/api/?key={PIXABAY_API}&q={query}&per_page={n}&orientation=horizontal"
    if debug: print("[DEBUG] Pixabay URL:", url)
    r = requests.get(url)
    results = [p["largeImageURL"] for p in r.json().get("hits", [])]
    site_counts["pixabay"] += len(results)
    return results

def download_images(urls, outdir, verbose=False):
    global error_count
    total = len(urls)
    print(f"[INFO] Downloading {total} images into '{outdir}'...")
    count = 0
    for idx, u in enumerate(urls, 1):
        try:
            img = requests.get(u, timeout=15).content
            h = file_hash(img)
            if h in downloaded_hashes:
                if verbose: print(f"[VERBOSE] Skipping duplicate {u}")
                continue
            downloaded_hashes.add(h)
            fn = os.path.join(outdir, f"wallpaper_{len(downloaded_hashes):05d}.jpg")
            print(f"[INFO] Downloading image {idx}/{total} -> {fn}")
            if verbose: print(f"[VERBOSE] Source URL: {u}")
            with open(fn, "wb") as f: f.write(img)
            count += 1
        except Exception as e:
            error_count += 1
            print(f"[ERROR] Failed to download {u}: {e}")
    return count

def main():
    parser = argparse.ArgumentParser(description="Download wallpapers from multiple sources")
    parser.add_argument("-s", "--search", help="Search string")
    parser.add_argument("-n", "--number", type=int, default=5, help="Total number of new images to download")
    parser.add_argument("-w", "--website", choices=["pexels","unsplash","pixabay","all"], default="pexels")
    parser.add_argument("--balanced", action="store_true", help="Balanced distribution across all sites (only with -w all)")
    parser.add_argument("-o", "--output", default="./wallpapers", help="Directory to store downloaded wallpapers (default: ./wallpapers)")
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug information")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument("-V", "--version", action="store_true", help="Show version and exit")
    parser.add_argument("-c", "--credits", action="store_true", help="Show credits and exit")
    args = parser.parse_args()

    # Early exits
    if args.credits:
        print(CREDITS)
        sys.exit(0)
    if args.version:
        print(f"{SCRIPTNAME} version {VERSION}")
        sys.exit(0)

    if not args.search:
        parser.error("the following arguments are required: -s/--search")

    # Ensure output directory exists or can be created
    try:
        os.makedirs(args.output, exist_ok=True)
    except Exception as e:
        print(f"[ERROR] cannot create output directory '{args.output}': {e}")
        sys.exit(1)

    start_time = time.time()

    urls = []
    if args.website == "all":
        if args.balanced:
            per_site = args.number // 3
            remainder = args.number % 3
            counts = [per_site, per_site, per_site]
            for i in range(remainder):
                counts[i] += 1
            print(f"[INFO] Balanced distribution: {counts}")
        else:
            counts = [0,0,0]
            for i in range(args.number):
                counts[random.randint(0,2)] += 1
            print(f"[INFO] Random distribution: {counts}")
        urls.extend(fetch_pexels(args.search, counts[0], args.debug))
        urls.extend(fetch_unsplash(args.search, counts[1], args.debug))
        urls.extend(fetch_pixabay(args.search, counts[2], args.debug))

        shortfall = args.number - len(urls)
        if shortfall > 0:
            print(f"[INFO] Shortfall detected: {shortfall}, backfilling...")
            while shortfall > 0:
                for site in ["pexels","unsplash","pixabay"]:
                    if shortfall <= 0: break
                    if site == "pexels":
                        extra = fetch_pexels(args.search, shortfall, args.debug)
                    elif site == "unsplash":
                        extra = fetch_unsplash(args.search, shortfall, args.debug)
                    else:
                        extra = fetch_pixabay(args.search, shortfall, args.debug)
                    urls.extend(extra)
                    shortfall = args.number - len(urls)
    elif args.website == "pexels":
        urls = fetch_pexels(args.search, args.number, args.debug)
    elif args.website == "unsplash":
        urls = fetch_unsplash(args.search, args.number, args.debug)
    elif args.website == "pixabay":
        urls = fetch_pixabay(args.search, args.number, args.debug)

    print(f"[INFO] Found {len(urls)} URLs")
    if args.debug:
        for u in urls: print("[DEBUG] URL:", u)

    count = download_images(urls, args.output, args.verbose)

    elapsed = time.time() - start_time
    print("\n[SUMMARY]")
    print(f"  Total requested: {args.number}")
    print(f"  Total downloaded: {count}")
    print(f"  Errors: {error_count}")
    print(f"  From Pexels: {site_counts['pexels']}")
    print(f"  From Unsplash: {site_counts['unsplash']}")
    print(f"  From Pixabay: {site_counts['pixabay']}")
    print(f"  Output directory: {args.output}")
    print(f"  Elapsed time: {elapsed:.2f} seconds")
    print("\n[INFO] All done — enjoy your new wallpapers!")

if __name__ == "__main__":
    main()
