#!/usr/bin/env python3
"""
BoredNoMore3 Downloader
Advanced wallpaper downloader from multiple sources

Downloads high-quality wallpapers from:
- Pexels (https://pexels.com)
- Lorem Picsum (https://picsum.photos)

Author: Nepamuceno Bartolo
GitHub: https://github.com/nepamuceno/borednomore3
Version: 0.5.2 (Modified)
"""

import os
import sys
import time
import random
import hashlib
import argparse
import requests
import re
import glob

VERSION = "0.5.2"
AUTHOR = "Nepamuceno Bartolo"
GITHUB = "https://github.com/nepamuceno/borednomore3"

class BoredNoMore3Downloader:
    """Advanced wallpaper downloader with smart numbering and duplicate detection"""

    def __init__(self, directory="./wallpapers", search="wallpaper", count=10,
                 deep_search=False, sources=None, start_from=None, randomize_source=False):
        self.directory = os.path.abspath(os.path.expanduser(directory))
        self.search = search
        self.total_target = count
        self.deep_search = deep_search
        self.randomize_source = randomize_source
        self.downloaded = []
        self.downloaded_hashes = set()
        self.next_number = 1
        self.start_from = start_from
        
        # Available sources
        self.available_sources = {
            'pexels': self.download_from_pexels,
            'picsum': self.download_from_picsum,
        }
        
        if randomize_source:
            random_source = random.choice(list(self.available_sources.keys()))
            self.sources = [random_source]
            print(f"Random source selected: {random_source}")
        elif sources:
            self.sources = sources
        else:
            self.sources = ['all']
        
        if not os.path.isdir(self.directory):
            try:
                os.makedirs(self.directory, exist_ok=True)
                print(f"Created directory: {self.directory}")
            except Exception as e:
                print(f"Error: Cannot create directory '{self.directory}': {e}")
                sys.exit(1)
        
        self._scan_existing_files()

    def _scan_existing_files(self):
        print(f"Scanning directory: {self.directory}")
        existing_files = glob.glob(os.path.join(self.directory, "*.jpg"))
        
        if not existing_files:
            print("No existing wallpapers found. Starting from 1.")
            self.next_number = self.start_from if self.start_from else 1
            return
        
        max_number = 0
        number_pattern = re.compile(r'(\d+)')
        
        for filepath in existing_files:
            filename = os.path.basename(filepath)
            numbers = number_pattern.findall(filename)
            if numbers:
                num = int(numbers[-1])
                max_number = max(max_number, num)
            if self.start_from is None:
                try:
                    file_hash = self._get_file_hash(filepath)
                    self.downloaded_hashes.add(file_hash)
                except:
                    pass
        
        if self.start_from is not None:
            self.next_number = self.start_from
            print(f"Override mode: Starting from wallpaper number {self.next_number}")
        else:
            self.next_number = max_number + 1
            print(f"Next wallpaper will be numbered: {self.next_number}")

    def _get_file_hash(self, filepath):
        sha256_hash = hashlib.sha256()
        try:
            with open(filepath, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except:
            return None

    def _is_duplicate(self, image_data):
        sha256_hash = hashlib.sha256()
        sha256_hash.update(image_data)
        file_hash = sha256_hash.hexdigest()
        if file_hash in self.downloaded_hashes:
            return True
        self.downloaded_hashes.add(file_hash)
        return False

    def _save_image(self, image_data, source_name):
        if self.start_from is None:
            if self._is_duplicate(image_data):
                print(f"  Skipped duplicate from {source_name}")
                return False
        else:
            sha256_hash = hashlib.sha256()
            sha256_hash.update(image_data)
            self.downloaded_hashes.add(sha256_hash.hexdigest())
        
        filename = f"wallpaper_{self.next_number:05d}.jpg"
        save_path = os.path.join(self.directory, filename)
        overwrite_msg = " (OVERWRITTEN)" if os.path.exists(save_path) else ""
        
        try:
            with open(save_path, "wb") as f:
                f.write(image_data)
            self.downloaded.append(save_path)
            print(f"  Downloaded: {filename} from {source_name}{overwrite_msg}")
            self.next_number += 1
            return True
        except Exception as e:
            print(f"  Error saving {filename}: {e}")
            return False

    def download_from_pexels(self, limit):
        print(f"\n[Pexels] Searching for '{self.search}' (Limit: {limit})...")
        downloaded_count = 0
        pages = 5 if self.deep_search else 2
        photo_ranges = [(1000000, 5000000), (100000, 999999), (10000, 99999)]
        
        for start, end in photo_ranges[:pages]:
            if downloaded_count >= limit:
                break
            # Try a reasonable number of random IDs to hit the target
            for _ in range(limit * 3):
                if downloaded_count >= limit:
                    break
                photo_id = random.randint(start, end)
                url = f"https://images.pexels.com/photos/{photo_id}/pexels-photo-{photo_id}.jpeg?auto=compress&cs=tinysrgb&w=1920"
                try:
                    response = requests.get(url, timeout=10)
                    if response.status_code == 200 and len(response.content) > 50000:
                        if self._save_image(response.content, "Pexels"):
                            downloaded_count += 1
                    time.sleep(0.2)
                except:
                    continue
        print(f"[Pexels] Downloaded {downloaded_count} images")
        return downloaded_count

    def download_from_picsum(self, limit):
        print(f"\n[Lorem Picsum] Downloading random wallpapers (Limit: {limit})...")
        downloaded_count = 0
        for i in range(limit):
            url = f"https://picsum.photos/1920/1080?random={random.randint(1, 100000)}"
            try:
                response = requests.get(url, timeout=10, allow_redirects=True)
                if response.status_code == 200:
                    if self._save_image(response.content, "Picsum"):
                        downloaded_count += 1
                time.sleep(0.2)
            except Exception as e:
                print(f"  Error downloading from Picsum: {e}")
                continue
        print(f"[Picsum] Downloaded {downloaded_count} images")
        return downloaded_count

    def fetch_all_sources(self):
        print("\n" + "=" * 80)
        print("BoredNoMore3 Downloader - Starting Download Process")
        print("=" * 80)
        print(f"Search query: '{self.search}'")
        print(f"Total target: {self.total_target} wallpapers")
        print(f"Save directory: {self.directory}")
        
        active_keys = list(self.available_sources.keys()) if 'all' in self.sources else self.sources
        print(f"Sources: {', '.join(active_keys)}")
        print("=" * 80)
        
        initial_count = len(self.downloaded)
        num_sources = len(active_keys)
        
        # Calculate distribution
        count_per_source = self.total_target // num_sources
        remainder = self.total_target % num_sources

        for i, source_key in enumerate(active_keys):
            # Add remainder to the last source
            quota = count_per_source + (remainder if i == num_sources - 1 else 0)
            if quota > 0:
                self.available_sources[source_key](limit=quota)
        
        print("\n" + "=" * 80)
        print("Download Process Completed")
        print("=" * 80)
        total_new = len(self.downloaded) - initial_count
        print(f"Total new wallpapers downloaded: {total_new}")
        print(f"Total wallpapers in directory: {self.next_number - 1}")
        print(f"Saved to: {self.directory}")
        print("=" * 80)

def print_help():
    help_text = f"""
BoredNoMore3 Downloader v{VERSION}

USAGE:
    borednomore3_downloader.py [OPTIONS]

OPTIONS:
    -h, --help      Show this help
    -d <path>       Save directory (Default: ./wallpapers)
    -s <query>      Search query (Default: "wallpaper")
    -n <count>      TOTAL wallpapers to download (Default: 10)
    -D, --deep      Enable deep search (Pexels)
    -w <sources>    Sources (pexels, picsum, all)
    -o <number>     Overwrite starting from specific number
    -R              Randomly pick ONE source
"""
    print(help_text)

def main():
    try:
        parser = argparse.ArgumentParser(add_help=False)
        parser.add_argument('-h', '--help', action='store_true')
        parser.add_argument('-v', '--version', action='store_true')
        parser.add_argument('-d', '--directory', type=str, default='./wallpapers')
        parser.add_argument('-s', '--search', type=str, default='wallpaper')
        parser.add_argument('-n', '--number', type=int, default=10)
        parser.add_argument('-D', '--deep', action='store_true')
        parser.add_argument('-w', '--websites', type=str, default=None)
        parser.add_argument('-o', '--overwrite', type=int, default=None)
        parser.add_argument('-R', '--random-source', action='store_true')
        args = parser.parse_args()

        if args.help:
            print_help(); sys.exit(0)
        
        sources = None
        if args.websites:
            if args.websites.lower() != 'all':
                sources = [s.strip().lower() for s in args.websites.split(',')]

        downloader = BoredNoMore3Downloader(
            directory=args.directory,
            search=args.search,
            count=args.number,
            deep_search=args.deep,
            sources=sources,
            start_from=args.overwrite,
            randomize_source=args.random_source
        )
        downloader.fetch_all_sources()

    except KeyboardInterrupt:
        print("\nDownload interrupted by user."); sys.exit(0)
    except Exception as e:
        print(f"\nAn error occurred: {str(e)}")

if __name__ == "__main__":
    main()
