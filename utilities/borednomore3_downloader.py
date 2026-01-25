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
Version: 0.6.0
"""

import os
import sys
import time
import random
import hashlib
import argparse
import glob
import re
from pathlib import Path

# Import download engines
try:
    from borednomore3_downloader_engines import DownloadEngines
except ImportError:
    print("ERROR: borednomore3_downloader_engines.py not found!")
    print("Please ensure both files are in the same directory.")
    sys.exit(1)

VERSION = "0.6.0"
AUTHOR = "Nepamuceno Bartolo"
EMAIL = "(hidden)"
GITHUB = "https://github.com/nepamuceno/borednomore3"


class BoredNoMore3Downloader:
    """Advanced wallpaper downloader with smart numbering and duplicate detection"""

    def __init__(self, directory=".", search="dark wallpaper", count=10, deep_search=False, 
                 sources=None, start_from=None, randomize_source=False):
        self.directory = os.path.abspath(os.path.expanduser(directory))
        self.search = search
        self.count = count  # Use 'count' for consistency with engines
        self.deep_search = deep_search  # Use 'deep_search' for consistency with engines
        self.randomize_source = randomize_source
        self.downloaded = []
        self.downloaded_hashes = set()
        self.next_number = 1
        self.start_from = start_from
        
        # Initialize download engines
        self.engines = DownloadEngines(self)
        
        # Available sources mapping
        self.available_sources = {
            'unsplash': self.engines.download_from_unsplash,
            'pexels': self.engines.download_from_pexels,
            'pixabay': self.engines.download_from_pixabay,
            'picsum': self.engines.download_from_picsum,
            'wallhaven': self.engines.download_from_wallhaven,
            'google': self.engines.download_from_google,
            'bing': self.engines.download_from_bing,
        }
        
        # Handle source selection with randomization
        if randomize_source:
            random_source = random.choice(list(self.available_sources.keys()))
            self.sources = [random_source]
            print(f"🎲 Random source selected: {random_source}")
        elif sources:
            self.sources = sources
        else:
            self.sources = ['bing']
        
        # Create directory if it doesn't exist
        self._create_directory()
        
        # Scan existing files and determine next number
        self._scan_existing_files()

    def _create_directory(self):
        """Create output directory if it doesn't exist"""
        if not os.path.isdir(self.directory):
            try:
                os.makedirs(self.directory, exist_ok=True)
                print(f"📁 Created directory: {self.directory}")
            except Exception as e:
                print(f"❌ Error: Cannot create directory '{self.directory}': {e}")
                sys.exit(1)

    def _scan_existing_files(self):
        """Scan directory for existing wallpapers and find next number"""
        print(f"🔍 Scanning directory: {self.directory}")
        
        pattern = os.path.join(self.directory, "wallpaper_*.jpg")
        existing_files = glob.glob(pattern)
        
        if not existing_files:
            print("📝 No existing wallpapers found. Starting from 1.")
            self.next_number = 1
            if self.start_from is not None:
                self.next_number = self.start_from
                print(f"⚠️  Override: Starting from specified number {self.next_number}")
            return
        
        # Extract numbers from filenames
        max_number = 0
        number_pattern = re.compile(r'wallpaper_(\d+)\.jpg')
        
        for filepath in existing_files:
            filename = os.path.basename(filepath)
            match = number_pattern.match(filename)
            if match:
                num = int(match.group(1))
                max_number = max(max_number, num)
            
            # Calculate hash to avoid duplicates (only if not overwriting)
            if self.start_from is None:
                try:
                    file_hash = self._get_file_hash(filepath)
                    if file_hash:
                        self.downloaded_hashes.add(file_hash)
                except Exception:
                    pass
        
        # Determine starting number
        if self.start_from is not None:
            self.next_number = self.start_from
            print(f"📊 Found {len(existing_files)} existing wallpapers.")
            print(f"⚠️  Override mode: Starting from wallpaper number {self.next_number}")
            print(f"⚠️  WARNING: Existing wallpapers from {self.next_number} onwards will be overwritten!")
        else:
            self.next_number = max_number + 1
            print(f"📊 Found {len(existing_files)} existing wallpapers.")
            print(f"➡️  Next wallpaper will be numbered: {self.next_number}")

    def _get_file_hash(self, filepath):
        """Calculate SHA256 hash of a file"""
        sha256_hash = hashlib.sha256()
        try:
            with open(filepath, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception:
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

    def save_image(self, image_data, source_name):
        """Save image with smart numbering (public method for engines)"""
        # Skip duplicate check if in overwrite mode
        if self.start_from is None:
            if self._is_duplicate(image_data):
                print(f"  ⏭️  Skipped duplicate from {source_name}")
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
            overwrite_msg = " 🔄 (OVERWRITTEN)"
        
        try:
            with open(save_path, "wb") as f:
                f.write(image_data)
            
            file_size_kb = len(image_data) / 1024
            self.downloaded.append(save_path)
            print(f"  ✅ Downloaded: {filename} from {source_name} ({file_size_kb:.1f} KB){overwrite_msg}")
            self.next_number += 1
            return True
        except Exception as e:
            print(f"  ❌ Error saving {filename}: {e}")
            return False

    def fetch_all_sources(self):
        """Download wallpapers from selected sources"""
        print("\n" + "=" * 80)
        print("🚀 BoredNoMore3 Downloader - Starting Download Process")
        print("=" * 80)
        print(f"🔍 Search query: '{self.search}'")
        print(f"🎯 Target count: {self.count} wallpapers")
        print(f"🔬 Deep search: {'✅ Enabled' if self.deep_search else '❌ Disabled'}")
        print(f"📁 Save directory: {self.directory}")
        
        # Determine which sources to use
        if 'all' in self.sources:
            active_sources = list(self.available_sources.keys())
            print(f"🌐 Sources: All ({', '.join(active_sources)})")
        else:
            active_sources = self.sources
            print(f"🌐 Sources: {', '.join(active_sources)}")
        
        if self.start_from is not None:
            print(f"⚠️  Mode: OVERWRITE from number {self.start_from}")
        else:
            print(f"➕ Mode: APPEND (continue from last)")
        
        print("=" * 80)
        
        initial_count = len(self.downloaded)
        
        # Download from selected sources
        for source in active_sources:
            if source in self.available_sources:
                try:
                    self.available_sources[source]()
                except KeyboardInterrupt:
                    raise
                except Exception as e:
                    print(f"❌ [{source}] Fatal error: {e}")
            else:
                print(f"⚠️  Unknown source: {source}")
        
        print("\n" + "=" * 80)
        print("✅ Download Process Completed")
        print("=" * 80)
        
        total_downloaded = len(self.downloaded) - initial_count
        print(f"📥 Total new wallpapers downloaded: {total_downloaded}")
        print(f"📊 Total wallpapers in directory: {self.next_number - 1}")
        print(f"💾 Saved to: {self.directory}")
        print("=" * 80)


def print_help():
    """Print comprehensive help information"""
    help_text = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                  BoredNoMore3 Downloader - Wallpaper Fetcher                 ║
║                              Version {VERSION}                                ║
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
        Example: -d ~/Pictures/Wallpapers
    -s, --search <query>
        Search query for finding wallpapers.
        Default: "dark wallpaper"
        Example: -s "nature landscape"
        Example: -s "abstract art"
    -n, --number <count>
        Number of wallpapers to download.
        Default: 10
        Range: 1-500
        Example: -n 20
    -D, --deep
        Enable deep search mode for more variety.
    -w, --websites <sources>
        Specify which websites/sources to use.
        Default: bing
        Available: unsplash, pexels, pixabay, picsum, wallhaven, google, bing, all
        
        Example: -w unsplash,pexels
        Example: -w all
    -o, --overwrite <number>
        Start overwriting from specified number.
        Example: -o 50
    -R, --random-source
        Randomly select one source.
SOURCES:
    • unsplash  - High-quality curated photography
    • pexels    - Professional stock photos (API key recommended)
    • pixabay   - Free images (API key recommended)
    • picsum    - Random quality photos
    • wallhaven - Community wallpapers (API key recommended)
    • google    - Google Images scraping
    • bing      - Bing Images scraping
    • all       - All available sources
FEATURES:
    ✅ Smart sequential numbering
    ✅ SHA256 duplicate detection
    ✅ Multiple source support
    ✅ Deep search mode
    ✅ Automatic directory creation
    ✅ Overwrite mode
AUTHOR:
    {AUTHOR}
    GitHub: {GITHUB}
NOTES:
    - For best results with Pexels, Pixabay, and Wallhaven, use their API keys
    - Edit borednomore3_downloader_engines.py to add API keys
    - Bing and Google work via scraping (no API key needed)
"""
    print(help_text)


def print_version():
    """Print version information"""
    print(f"BoredNoMore3 Downloader v{VERSION}")


def print_credits():
    """Print credits and author information"""
    credits_text = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                  BoredNoMore3 Downloader - Wallpaper Fetcher                 ║
╚══════════════════════════════════════════════════════════════════════════════╝
Version:    {VERSION}
Author:     {AUTHOR}
Email:      {EMAIL}
GitHub:     {GITHUB}
Credits:
    • Unsplash.com - Beautiful free photos
    • Pexels.com - Free stock photos & videos
    • Pixabay.com - Free images & videos
    • Wallhaven.cc - Community wallpapers
    • Picsum.photos - Lorem Picsum random images
    
Thank you to all content creators and communities!
"""
    print(credits_text)


def main():
    """Main entry point"""
    try:
        parser = argparse.ArgumentParser(
            description='BoredNoMore3 Downloader - Wallpaper Fetcher',
            add_help=False
        )
        
        parser.add_argument('-h', '--help', action='store_true')
        parser.add_argument('-v', '--version', action='store_true')
        parser.add_argument('-c', '--credits', action='store_true')
        parser.add_argument('-d', '--directory', type=str, default='.')
        parser.add_argument('-s', '--search', type=str, default='dark wallpaper')
        parser.add_argument('-n', '--number', type=int, default=10)
        parser.add_argument('-D', '--deep', action='store_true')
        parser.add_argument('-w', '--websites', type=str, default=None)
        parser.add_argument('-o', '--overwrite', type=int, default=None)
        parser.add_argument('-R', '--random-source', action='store_true')
        
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
        
        # Validate number
        if args.number < 1 or args.number > 500:
            print("❌ Error: Number must be between 1 and 500")
            sys.exit(1)
        
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
                    print(f"❌ Error: Invalid source(s): {', '.join(invalid_sources)}")
                    print(f"Available sources: {', '.join(available)}")
                    sys.exit(1)
        
        # Create and run downloader
        print(f"🎨 BoredNoMore3 Downloader v{VERSION}")
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
        print("\n\n⚠️  Download interrupted by user. Exiting gracefully...")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ An error occurred: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
