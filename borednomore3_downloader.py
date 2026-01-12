#!/usr/bin/env python3
"""
BoredNoMore3 Downloader
Advanced wallpaper downloader from multiple sources

Downloads high-quality wallpapers from:
- Unsplash (https://unsplash.com)
- Pexels (https://pexels.com)
- Pixabay (https://pixabay.com)
- Wallhaven (https://wallhaven.cc)
- Lorem Picsum (https://picsum.photos)
- Google Images (via scraping)
- Bing Images (via scraping)

Author: Nepamuceno Bartolo
Email: (hidden)
GitHub: https://github.com/nepamuceno/borednomore3
Version: 0.5.0
"""

import os
import sys
import time
import random
import hashlib
import argparse
import requests
import glob
from pathlib import Path
from urllib.parse import quote, urlparse
import re

VERSION = "0.5.0"
AUTHOR = "Nepamuceno Bartolo"
EMAIL = "(hidden)"
GITHUB = "https://github.com/nepamuceno/borednomore3"


class BoredNoMore3Downloader:
    """Advanced wallpaper downloader with smart numbering and duplicate detection"""

    def __init__(self, directory=".", search="dark wallpaper", count=10, deep_search=False, sources=None, start_from=None, randomize_source=False):
        self.directory = os.path.abspath(os.path.expanduser(directory))
        self.search = search
        self.count = count
        self.deep_search = deep_search
        self.randomize_source = randomize_source
        self.downloaded = []
        self.downloaded_hashes = set()
        self.next_number = 1
        self.start_from = start_from
        
        # Available sources
        self.available_sources = {
            'unsplash': self.download_from_unsplash,
            'pexels': self.download_from_pexels,
            'pixabay': self.download_from_pixabay,
            'picsum': self.download_from_picsum,
            'wallhaven': self.download_from_wallhaven,
            'google': self.download_from_google,
            'bing': self.download_from_bing,
        }
        
        # Handle source selection with randomization
        if randomize_source:
            # Pick a random source if random flag is set
            random_source = random.choice(list(self.available_sources.keys()))
            self.sources = [random_source]
            print(f"Random source selected: {random_source}")
        elif sources:
            self.sources = sources
        else:
            # Default logic: Default to Bing if not specified
            self.sources = ['bing']
        
        # Create directory if it doesn't exist
        if not os.path.isdir(self.directory):
            try:
                os.makedirs(self.directory, exist_ok=True)
                print(f"Created directory: {self.directory}")
            except Exception as e:
                print(f"Error: Cannot create directory '{self.directory}': {e}")
                sys.exit(1)
        
        # Scan existing files and determine next number
        self._scan_existing_files()

    def _scan_existing_files(self):
        """Scan directory for existing wallpapers and find next number"""
        print(f"Scanning directory: {self.directory}")
        
        existing_files = []
        pattern = os.path.join(self.directory, "*.jpg")
        existing_files = glob.glob(pattern)
        
        if not existing_files:
            print("No existing wallpapers found. Starting from 1.")
            self.next_number = 1
            if self.start_from is not None:
                self.next_number = self.start_from
                print(f"Override: Starting from specified number {self.next_number}")
            return
        
        # Extract numbers from filenames
        max_number = 0
        number_pattern = re.compile(r'(\d+)')
        
        for filepath in existing_files:
            filename = os.path.basename(filepath)
            numbers = number_pattern.findall(filename)
            if numbers:
                # Get the last number in the filename
                num = int(numbers[-1])
                max_number = max(max_number, num)
            
            # Calculate hash to avoid duplicates (only if not overwriting)
            if self.start_from is None:
                try:
                    file_hash = self._get_file_hash(filepath)
                    self.downloaded_hashes.add(file_hash)
                except:
                    pass
        
        # Determine starting number
        if self.start_from is not None:
            self.next_number = self.start_from
            print(f"Found {len(existing_files)} existing wallpapers.")
            print(f"Override mode: Starting from wallpaper number {self.next_number}")
            print(f"WARNING: Existing wallpapers from {self.next_number} onwards will be overwritten!")
        else:
            self.next_number = max_number + 1
            print(f"Found {len(existing_files)} existing wallpapers.")
            print(f"Next wallpaper will be numbered: {self.next_number}")

    def _get_file_hash(self, filepath):
        """Calculate SHA256 hash of a file"""
        sha256_hash = hashlib.sha256()
        try:
            with open(filepath, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except:
            return None

    def _is_duplicate(self, image_data):
        """Check if image data is a duplicate"""
        sha256_hash = hashlib.sha256()
        sha256_hash.update(image_data)
        file_hash = sha256_hash.hexdigest()
        
        if file_hash in self.downloaded_hashes:
            return True
        
        self.downloaded_hashes.add(file_hash)
        return False

    def _save_image(self, image_data, source_name):
        """Save image with smart numbering"""
        # Skip duplicate check if in overwrite mode
        if self.start_from is None:
            if self._is_duplicate(image_data):
                print(f"  Skipped duplicate from {source_name}")
                return False
        else:
            # In overwrite mode, still add hash to track new downloads
            sha256_hash = hashlib.sha256()
            sha256_hash.update(image_data)
            file_hash = sha256_hash.hexdigest()
            self.downloaded_hashes.add(file_hash)
        
        filename = f"wallpaper_{self.next_number:05d}.jpg"
        save_path = os.path.join(self.directory, filename)
        
        # Check if we're overwriting
        overwrite_msg = ""
        if os.path.exists(save_path):
            overwrite_msg = " (OVERWRITTEN)"
        
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

    def download_from_unsplash(self):
        """Download wallpapers from Unsplash"""
        print(f"\n[Unsplash] Searching for '{self.search}'...")
        
        try:
            pages = 3 if self.deep_search else 1
            downloaded_count = 0
            
            for page in range(1, pages + 1):
                if downloaded_count >= self.count:
                    break
                
                # Use Unsplash API-like endpoint
                search_encoded = quote(self.search)
                url = f"https://source.unsplash.com/1920x1080/?{search_encoded}&sig={random.randint(1, 10000)}"
                
                for attempt in range(self.count // pages + 2):
                    if downloaded_count >= self.count:
                        break
                    
                    try:
                        # Add random seed to get different images
                        unique_url = f"{url}&t={time.time()}"
                        response = requests.get(unique_url, timeout=15, allow_redirects=True)
                        
                        if response.status_code == 200:
                            if self._save_image(response.content, "Unsplash"):
                                downloaded_count += 1
                        
                        time.sleep(0.5)  # Rate limiting
                    except Exception as e:
                        print(f"  Error downloading from Unsplash: {e}")
                        continue
            
            print(f"[Unsplash] Downloaded {downloaded_count} images")
        except Exception as e:
            print(f"[Unsplash] Error: {e}")

    def download_from_pexels(self):
        """Download wallpapers from Pexels"""
        print(f"\n[Pexels] Searching for '{self.search}'...")
        
        try:
            downloaded_count = 0
            pages = 5 if self.deep_search else 2
            
            # Pexels has IDs, try random ranges
            photo_ranges = [
                (1000000, 5000000),    # Modern photos
                (100000, 999999),      # Mid-range
                (10000, 99999),        # Older photos
            ]
            
            for start, end in photo_ranges[:pages]:
                if downloaded_count >= self.count:
                    break
                
                for _ in range(self.count // len(photo_ranges) + 2):
                    if downloaded_count >= self.count:
                        break
                    
                    photo_id = random.randint(start, end)
                    url = f"https://images.pexels.com/photos/{photo_id}/pexels-photo-{photo_id}.jpeg?auto=compress&cs=tinysrgb&w=1920"
                    
                    try:
                        response = requests.get(url, timeout=15)
                        if response.status_code == 200 and len(response.content) > 50000:
                            if self._save_image(response.content, "Pexels"):
                                downloaded_count += 1
                        time.sleep(0.3)
                    except Exception as e:
                        continue
            
            print(f"[Pexels] Downloaded {downloaded_count} images")
        except Exception as e:
            print(f"[Pexels] Error: {e}")

    def download_from_pixabay(self):
        """Download wallpapers from Pixabay"""
        print(f"\n[Pixabay] Searching for '{self.search}'...")
        
        try:
            downloaded_count = 0
            
            # Pixabay image IDs - try random ranges
            for _ in range(self.count):
                photo_id = random.randint(100000, 8000000)
                
                # Try different image sizes
                sizes = ["1920", "1280"]
                
                for size in sizes:
                    if downloaded_count >= self.count:
                        break
                    
                    url = f"https://pixabay.com/get/g{str(photo_id)[:2]}/{photo_id}_1920.jpg"
                    
                    try:
                        response = requests.get(url, timeout=15)
                        if response.status_code == 200 and len(response.content) > 50000:
                            if self._save_image(response.content, "Pixabay"):
                                downloaded_count += 1
                                break
                        time.sleep(0.3)
                    except Exception as e:
                        continue
            
            print(f"[Pixabay] Downloaded {downloaded_count} images")
        except Exception as e:
            print(f"[Pixabay] Error: {e}")

    def download_from_picsum(self):
        """Download wallpapers from Lorem Picsum"""
        print(f"\n[Lorem Picsum] Downloading random wallpapers...")
        
        try:
            downloaded_count = 0
            
            for i in range(self.count):
                # Use random seed for variety
                url = f"https://picsum.photos/1920/1080?random={random.randint(1, 100000)}"
                
                try:
                    response = requests.get(url, timeout=15, allow_redirects=True)
                    if response.status_code == 200:
                        if self._save_image(response.content, "Picsum"):
                            downloaded_count += 1
                    time.sleep(0.3)
                except Exception as e:
                    print(f"  Error downloading from Picsum: {e}")
                    continue
            
            print(f"[Picsum] Downloaded {downloaded_count} images")
        except Exception as e:
            print(f"[Picsum] Error: {e}")

    def download_from_wallhaven(self):
        """Download wallpapers from Wallhaven"""
        print(f"\n[Wallhaven] Searching for '{self.search}'...")
        
        try:
            downloaded_count = 0
            pages = 3 if self.deep_search else 1
            
            for page in range(1, pages + 1):
                if downloaded_count >= self.count:
                    break
                
                # Wallhaven search URL
                search_encoded = quote(self.search)
                url = f"https://wallhaven.cc/api/v1/search?q={search_encoded}&page={page}"
                
                try:
                    response = requests.get(url, timeout=15)
                    if response.status_code == 200:
                        data = response.json()
                        
                        if 'data' in data:
                            for item in data['data']:
                                if downloaded_count >= self.count:
                                    break
                                
                                if 'path' in item:
                                    img_url = item['path']
                                    try:
                                        img_response = requests.get(img_url, timeout=15)
                                        if img_response.status_code == 200:
                                            if self._save_image(img_response.content, "Wallhaven"):
                                                downloaded_count += 1
                                        time.sleep(0.5)
                                    except:
                                        continue
                    
                    time.sleep(1)  # Rate limiting between pages
                except Exception as e:
                    print(f"  Error with Wallhaven API: {e}")
                    continue
            
            print(f"[Wallhaven] Downloaded {downloaded_count} images")
        except Exception as e:
            print(f"[Wallhaven] Error: {e}")

    def download_from_google(self):
        """Download wallpapers from Google Images"""
        print(f"\n[Google] Searching for '{self.search}'...")
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        downloaded_count = 0
        try:
            url = f"https://www.google.com/search?q={quote(self.search)}&tbm=isch"
            response = requests.get(url, headers=headers, timeout=15)
            # Simple regex to find direct image URLs
            img_urls = re.findall(r'https://[^"]+\.(?:jpg|jpeg|png)', response.text)
            
            for img_url in list(set(img_urls)):
                if downloaded_count >= self.count: break
                try:
                    img_data = requests.get(img_url, headers=headers, timeout=10).content
                    if len(img_data) > 10000: # filter out tiny thumbnails
                        if self._save_image(img_data, "Google"):
                            downloaded_count += 1
                    time.sleep(0.5)
                except: continue
            print(f"[Google] Downloaded {downloaded_count} images")
        except Exception as e:
            print(f"[Google] Error: {e}")

    def download_from_bing(self):
        """Download wallpapers from Bing Images"""
        print(f"\n[Bing] Searching for '{self.search}'...")
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        downloaded_count = 0
        try:
            url = f"https://www.bing.com/images/search?q={quote(self.search)}"
            response = requests.get(url, headers=headers, timeout=15)
            # Find images in media content attributes
            img_urls = re.findall(r'murl&quot;:&quot;(https?://[^&]+?\.(?:jpg|jpeg|png))', response.text)
            
            for img_url in list(set(img_urls)):
                if downloaded_count >= self.count: break
                try:
                    img_data = requests.get(img_url, headers=headers, timeout=10).content
                    if self._save_image(img_data, "Bing"):
                        downloaded_count += 1
                    time.sleep(0.5)
                except: continue
            print(f"[Bing] Downloaded {downloaded_count} images")
        except Exception as e:
            print(f"[Bing] Error: {e}")

    def fetch_all_sources(self):
        """Download wallpapers from selected sources"""
        print("\n" + "=" * 80)
        print("BoredNoMore3 Downloader - Starting Download Process")
        print("=" * 80)
        print(f"Search query: '{self.search}'")
        print(f"Target count: {self.count} wallpapers")
        print(f"Deep search: {'Enabled' if self.deep_search else 'Disabled'}")
        print(f"Save directory: {self.directory}")
        
        # Determine which sources to use
        if 'all' in self.sources:
            active_sources = list(self.available_sources.keys())
            print(f"Sources: All ({', '.join(active_sources)})")
        else:
            active_sources = self.sources
            print(f"Sources: {', '.join(active_sources)}")
        
        if self.start_from is not None:
            print(f"Mode: OVERWRITE from number {self.start_from}")
        else:
            print(f"Mode: APPEND (continue from last)")
        
        print("=" * 80)
        
        initial_count = len(self.downloaded)
        
        # Download from selected sources
        for source in active_sources:
            if source in self.available_sources:
                self.available_sources[source]()
            else:
                print(f"[Warning] Unknown source: {source}")
        
        print("\n" + "=" * 80)
        print("Download Process Completed")
        print("=" * 80)
        
        total_downloaded = len(self.downloaded) - initial_count
        print(f"Total new wallpapers downloaded: {total_downloaded}")
        print(f"Total wallpapers in directory: {self.next_number - 1}")
        print(f"Saved to: {self.directory}")
        print("=" * 80)


def print_help():
    """Print comprehensive help information"""
    help_text = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    BoredNoMore3 Downloader - Wallpaper Fetcher                ║
║                                Version {VERSION}                               ║
╚══════════════════════════════════════════════════════════════════════════════╝

DESCRIPTION:
    BoredNoMore3 Downloader is an advanced wallpaper downloading tool that fetches
    high-quality images from multiple sources with smart duplicate detection and
    sequential numbering.

USAGE:
    borednomore3_downloader.py [OPTIONS]

OPTIONS:
    -h, --help
        Display this comprehensive help message and exit.

    -v, --version
        Display version information and exit.

    -c, --credits
        Display credits and author information.

    -d, --directory <path>
        Directory where wallpapers will be saved.
        Default: current directory
        The script will scan existing files and continue numbering from the last
        wallpaper to avoid conflicts.
        Example: -d ~/Pictures/Wallpapers

    -s, --search <query>
        Search query for finding wallpapers.
        Default: "dark wallpaper"
        The search query is used across multiple sources to find relevant images.
        Example: -s "nature landscape"
        Example: -s "abstract art"

    -n, --number <count>
        Number of wallpapers to download.
        Default: 10
        Range: 1-100
        Example: -n 20

    -D, --deep
        Enable deep search mode.
        When enabled, the downloader explores multiple pages and deeper into
        each source to find more unique wallpapers. This increases download time
        but provides more variety.

    -w, --websites <sources>
        Specify which websites/sources to use for downloading.
        Default: bing (unless -R is used, then random source)
        Available sources: unsplash, pexels, pixabay, picsum, wallhaven, google, bing, all
        
        Use comma-separated list for multiple sources:
        Example: -w unsplash,pexels
        Example: -w bing
        Example: -w all (uses all available sources)
        
        Source descriptions:
        • unsplash  - High-quality curated photography
        • pexels    - Professional stock photos
        • pixabay   - Large variety of free images
        • picsum    - Random quality photos
        • wallhaven - Community wallpaper collection
        • google    - Google Images search results
        • bing      - Bing Images search results
        • all       - Use all available sources

    -o, --overwrite <number>
        Start overwriting wallpapers from the specified number.
        Default: None (append mode - continue from last wallpaper)
        
        When specified, existing wallpapers from this number onwards will be
        replaced with new downloads. Use with caution!
        
        Example: -o 50 (start overwriting from wallpaper_00050.jpg)
        Example: -o 1 (replace all wallpapers starting from the first)
        
        Note: In overwrite mode, duplicate detection is disabled to allow
        replacing existing files.

    -R, --random-source
        Randomly select one source/website to download from.
        When this flag is set and -w is not specified, a random source will
        be chosen automatically. Useful for variety.
        
        Example: -R (randomly picks one of: unsplash, pexels, pixabay, etc.)
        
        Note: If -w is explicitly specified, it takes precedence over -R.

FEATURES:
    ✓ Smart Sequential Numbering
        Automatically scans existing wallpapers and continues numbering from the
        last file (e.g., if you have wallpaper_00042.jpg, new downloads start at
        wallpaper_00043.jpg).

    ✓ Duplicate Detection
        Uses SHA256 hashing to detect and skip duplicate images, even if they
        have different filenames or come from different sources.

    ✓ Multiple Sources
        Downloads from 7 major sources:
        • Unsplash - High-quality free stock photos
        • Pexels - Professional stock photography
        • Pixabay - Free images and videos
        • Wallhaven - Community wallpaper collection
        • Lorem Picsum - Random placeholder images
        • Google/Bing - General search engine images

    ✓ Deep Search Mode
        Explores multiple pages and deeper results from each source to find
        unique wallpapers not commonly downloaded.

    ✓ Automatic Directory Creation
        If the specified directory doesn't exist, it will be created automatically.

AUTHOR:
    {AUTHOR}
    Email: {EMAIL}
    GitHub: {GITHUB}
"""
    print(help_text)


def print_version():
    """Print version information"""
    print(f"BoredNoMore3 Downloader v{VERSION}")


def print_credits():
    """Print credits and author information"""
    credits_text = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    BoredNoMore3 Downloader - Wallpaper Fetcher                ║
╚══════════════════════════════════════════════════════════════════════════════╝

Version:    {VERSION}
Author:     {AUTHOR}
Email:      {EMAIL}
GitHub:     {GITHUB}
"""
    print(credits_text)


def main():
    """Main entry point"""
    try:
        parser = argparse.ArgumentParser(
            description='BoredNoMore3 Downloader - Wallpaper Fetcher',
            add_help=False
        )
        
        parser.add_argument('-h', '--help', action='store_true', help='Show help message')
        parser.add_argument('-v', '--version', action='store_true', help='Show version information')
        parser.add_argument('-c', '--credits', action='store_true', help='Show credits')
        parser.add_argument('-d', '--directory', type=str, default='.', help='Directory to save wallpapers')
        parser.add_argument('-s', '--search', type=str, default='dark wallpaper', help='Search query')
        parser.add_argument('-n', '--number', type=int, default=10, help='Number of wallpapers to download')
        parser.add_argument('-D', '--deep', action='store_true', help='Enable deep search mode')
        parser.add_argument('-w', '--websites', type=str, default=None, help='Websites to use')
        parser.add_argument('-o', '--overwrite', type=int, default=None, help='Start overwriting from this number')
        parser.add_argument('-R', '--random-source', action='store_true', help='Randomly select one source')
        
        args = parser.parse_args()
        
        if args.help:
            print_help()
            sys.exit(0)
        
        if args.version:
            print_version()
            sys.exit(0)
        
        if args.credits:
            print_credits()
            sys.exit(0)
        
        # Parse websites
        available = ['unsplash', 'pexels', 'pixabay', 'picsum', 'wallhaven', 'google', 'bing', 'all']
        sources = None
        
        if args.websites:
            if args.websites.lower() == 'all':
                sources = ['all']
            else:
                sources = [s.strip().lower() for s in args.websites.split(',')]
                invalid_sources = [s for s in sources if s not in available]
                if invalid_sources:
                    print(f"Error: Invalid source(s): {', '.join(invalid_sources)}")
                    sys.exit(1)
        
        # Create and run downloader
        print(f"BoredNoMore3 Downloader v{VERSION}")
        print("=" * 80)
        
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
        print("\n\nDownload interrupted by user. Exiting gracefully...")
        sys.exit(0)
    except Exception as e:
        print(f"\nAn error occurred: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
