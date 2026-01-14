#!/usr/bin/env python3
"""
BoredNoMore3 Downloader Engines
Search engine implementations for wallpaper downloading

This module contains all the download engine implementations for various
wallpaper sources. Each engine is responsible for fetching images from
a specific source.

Author: Nepamuceno Bartolo
Version: 0.6.0
"""

import time
import random
import requests
import re
from urllib.parse import quote, unquote
import json
from bs4 import BeautifulSoup

# ============================================================================
# API KEYS CONFIGURATION
# ============================================================================
# Add your API keys here for better results and higher rate limits

PEXELS_API_KEY = ""  # Get from: https://www.pexels.com/api/
PIXABAY_API_KEY = ""  # Get from: https://pixabay.com/api/docs/
WALLHAVEN_API_KEY = ""  # Get from: https://wallhaven.cc/settings/account

# ============================================================================
# USER AGENT
# ============================================================================
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'


class DownloadEngines:
    """Collection of download engines for various wallpaper sources"""
    
    def __init__(self, downloader):
        """Initialize with reference to main downloader instance"""
        self.downloader = downloader
        self.headers = {
            'User-Agent': USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
    
    @property
    def count(self):
        """Get download count from downloader (handles different attribute names)."""
        return getattr(self.downloader, 'count', getattr(self.downloader, 'target_count', 10))
    
    @property
    def deep_search(self):
        """Get deep search flag from downloader (handles different attribute names)."""
        return getattr(self.downloader, 'deep_search', getattr(self.downloader, 'deep', False))
    
    # ========================================================================
    # UNSPLASH
    # ========================================================================
    
    def download_from_unsplash(self):
        """Download wallpapers from Unsplash"""
        print(f"\n[Unsplash] Searching for '{self.downloader.search}'...")
        
        try:
            downloaded_count = 0
            attempts = self.count * 3  # Try more to account for failures
            
            # Use the source.unsplash.com endpoint which doesn't require API key
            search_encoded = quote(self.downloader.search)
            
            for i in range(attempts):
                if downloaded_count >= self.count:
                    break
                
                # Add random parameters to get different images
                random_seed = random.randint(1, 999999)
                url = f"https://source.unsplash.com/1920x1080/?{search_encoded}"
                
                # Add cache-busting parameters
                params = {
                    'sig': random_seed,
                    't': int(time.time() * 1000)
                }
                
                try:
                    response = requests.get(url, params=params, headers=self.headers, 
                                          timeout=15, allow_redirects=True)
                    
                    if response.status_code == 200 and len(response.content) > 50000:
                        # Check if it's actually an image
                        if response.headers.get('content-type', '').startswith('image/'):
                            if self.downloader.save_image(response.content, "Unsplash"):
                                downloaded_count += 1
                    
                    time.sleep(0.8)  # Rate limiting
                except Exception as e:
                    print(f"  ⚠️  Attempt {i+1} failed: {str(e)[:50]}")
                    time.sleep(1)
                    continue
            
            print(f"[Unsplash] Downloaded {downloaded_count} images")
        except Exception as e:
            print(f"[Unsplash] Error: {e}")
    
    # ========================================================================
    # PEXELS
    # ========================================================================
    
    def download_from_pexels(self):
        """Download wallpapers from Pexels"""
        print(f"\n[Pexels] Searching for '{self.downloader.search}'...")
        
        try:
            downloaded_count = 0
            
            if PEXELS_API_KEY:
                # Use official API
                pages = 5 if self.deep_search else 2
                
                for page in range(1, pages + 1):
                    if downloaded_count >= self.count:
                        break
                    
                    url = "https://api.pexels.com/v1/search"
                    headers = {**self.headers, 'Authorization': PEXELS_API_KEY}
                    params = {
                        'query': self.downloader.search,
                        'per_page': 80,
                        'page': page
                    }
                    
                    try:
                        response = requests.get(url, headers=headers, params=params, timeout=15)
                        if response.status_code == 200:
                            data = response.json()
                            if 'photos' in data:
                                for photo in data['photos']:
                                    if downloaded_count >= self.count:
                                        break
                                    
                                    img_url = photo.get('src', {}).get('original')
                                    if img_url:
                                        try:
                                            img_response = requests.get(img_url, timeout=15)
                                            if img_response.status_code == 200:
                                                if self.downloader.save_image(img_response.content, "Pexels"):
                                                    downloaded_count += 1
                                            time.sleep(0.3)
                                        except Exception:
                                            continue
                        time.sleep(1)
                    except Exception as e:
                        print(f"  ⚠️  Error with Pexels API: {e}")
                        continue
            else:
                # Scraping method - search Pexels website
                print("  ℹ️  No API key - using web scraping (add API key for better results)")
                
                search_encoded = quote(self.downloader.search)
                page = 1
                attempts = 0
                max_attempts = self.count * 3
                
                while downloaded_count < self.count and attempts < max_attempts:
                    attempts += 1
                    url = f"https://www.pexels.com/search/{search_encoded}/?page={page}"
                    
                    try:
                        response = requests.get(url, headers=self.headers, timeout=15)
                        if response.status_code == 200:
                            # Find image URLs in the page
                            # Pexels uses specific patterns for image URLs
                            img_patterns = [
                                r'https://images\.pexels\.com/photos/\d+/[^"]+\.jpeg\?[^"]*w=1920',
                                r'data-big-src="(https://images\.pexels\.com/photos/[^"]+)"',
                                r'srcset="([^"]*images\.pexels\.com/photos/[^"]*\d+w)"'
                            ]
                            
                            img_urls = []
                            for pattern in img_patterns:
                                matches = re.findall(pattern, response.text)
                                img_urls.extend(matches)
                            
                            # Get unique URLs and filter for large images
                            img_urls = list(set(img_urls))
                            img_urls = [url for url in img_urls if '1920' in url or '1280' in url]
                            
                            if img_urls:
                                for img_url in img_urls:
                                    if downloaded_count >= self.count:
                                        break
                                    
                                    try:
                                        # Clean URL
                                        img_url = img_url.split()[0] if ' ' in img_url else img_url
                                        
                                        img_response = requests.get(img_url, headers=self.headers, timeout=15)
                                        if img_response.status_code == 200 and len(img_response.content) > 50000:
                                            if self.downloader.save_image(img_response.content, "Pexels"):
                                                downloaded_count += 1
                                        time.sleep(0.5)
                                    except Exception as e:
                                        continue
                            
                            page += 1
                            time.sleep(2)  # Rate limiting for scraping
                        else:
                            break
                    except Exception as e:
                        print(f"  ⚠️  Scraping error: {str(e)[:50]}")
                        break
            
            print(f"[Pexels] Downloaded {downloaded_count} images")
        except Exception as e:
            print(f"[Pexels] Error: {e}")
    
    # ========================================================================
    # PIXABAY
    # ========================================================================
    
    def download_from_pixabay(self):
        """Download wallpapers from Pixabay"""
        print(f"\n[Pixabay] Searching for '{self.downloader.search}'...")
        
        try:
            downloaded_count = 0
            
            if PIXABAY_API_KEY:
                # Use official API
                pages = 5 if self.deep_search else 2
                
                for page in range(1, pages + 1):
                    if downloaded_count >= self.count:
                        break
                    
                    url = "https://pixabay.com/api/"
                    params = {
                        'key': PIXABAY_API_KEY,
                        'q': self.downloader.search,
                        'image_type': 'photo',
                        'per_page': 200,
                        'page': page
                    }
                    
                    try:
                        response = requests.get(url, params=params, timeout=15)
                        if response.status_code == 200:
                            data = response.json()
                            if 'hits' in data:
                                for hit in data['hits']:
                                    if downloaded_count >= self.count:
                                        break
                                    
                                    img_url = hit.get('largeImageURL') or hit.get('webformatURL')
                                    if img_url:
                                        try:
                                            img_response = requests.get(img_url, timeout=15)
                                            if img_response.status_code == 200:
                                                if self.downloader.save_image(img_response.content, "Pixabay"):
                                                    downloaded_count += 1
                                            time.sleep(0.3)
                                        except Exception:
                                            continue
                        time.sleep(1)
                    except Exception as e:
                        print(f"  ⚠️  Error with Pixabay API: {e}")
                        continue
            else:
                # Scraping method
                print("  ℹ️  No API key - using web scraping (add API key for better results)")
                
                search_encoded = quote(self.downloader.search)
                page = 1
                attempts = 0
                max_attempts = self.count * 3
                
                while downloaded_count < self.count and attempts < max_attempts:
                    attempts += 1
                    url = f"https://pixabay.com/images/search/{search_encoded}/?pagi={page}"
                    
                    try:
                        response = requests.get(url, headers=self.headers, timeout=15)
                        if response.status_code == 200:
                            # Find image URLs
                            img_patterns = [
                                r'https://pixabay\.com/get/[^"]+_1280\.jpg',
                                r'https://pixabay\.com/get/[^"]+_1920\.jpg',
                                r'data-lazy="(https://cdn\.pixabay\.com/[^"]+)"'
                            ]
                            
                            img_urls = []
                            for pattern in img_patterns:
                                matches = re.findall(pattern, response.text)
                                img_urls.extend(matches)
                            
                            img_urls = list(set(img_urls))
                            
                            if img_urls:
                                for img_url in img_urls:
                                    if downloaded_count >= self.count:
                                        break
                                    
                                    try:
                                        img_response = requests.get(img_url, headers=self.headers, timeout=15)
                                        if img_response.status_code == 200 and len(img_response.content) > 50000:
                                            if self.downloader.save_image(img_response.content, "Pixabay"):
                                                downloaded_count += 1
                                        time.sleep(0.5)
                                    except Exception:
                                        continue
                            
                            page += 1
                            time.sleep(2)
                        else:
                            break
                    except Exception as e:
                        print(f"  ⚠️  Scraping error: {str(e)[:50]}")
                        break
            
            print(f"[Pixabay] Downloaded {downloaded_count} images")
        except Exception as e:
            print(f"[Pixabay] Error: {e}")
    
    # ========================================================================
    # LOREM PICSUM
    # ========================================================================
    
    def download_from_picsum(self):
        """Download wallpapers from Lorem Picsum"""
        print(f"\n[Lorem Picsum] Downloading random wallpapers...")
        
        try:
            downloaded_count = 0
            
            for i in range(self.count * 2):
                if downloaded_count >= self.count:
                    break
                
                photo_id = random.randint(1, 1084)  # Picsum has ~1084 photos
                url = f"https://picsum.photos/id/{photo_id}/1920/1080.jpg"
                
                try:
                    response = requests.get(url, timeout=15, allow_redirects=True)
                    if response.status_code == 200 and len(response.content) > 50000:
                        if self.downloader.save_image(response.content, "Picsum"):
                            downloaded_count += 1
                    time.sleep(0.3)
                except Exception:
                    continue
            
            print(f"[Picsum] Downloaded {downloaded_count} images")
        except Exception as e:
            print(f"[Picsum] Error: {e}")
    
    # ========================================================================
    # WALLHAVEN
    # ========================================================================
    
    def download_from_wallhaven(self):
        """Download wallpapers from Wallhaven"""
        print(f"\n[Wallhaven] Searching for '{self.downloader.search}'...")
        
        try:
            downloaded_count = 0
            pages = 3 if self.deep_search else 2
            
            for page in range(1, pages + 1):
                if downloaded_count >= self.count:
                    break
                
                url = "https://wallhaven.cc/api/v1/search"
                
                params = {
                    'q': self.downloader.search,
                    'page': page,
                    'sorting': 'relevance',
                    'atleast': '1920x1080',
                    'purity': '100'  # SFW only
                }
                
                if WALLHAVEN_API_KEY:
                    params['apikey'] = WALLHAVEN_API_KEY
                
                try:
                    response = requests.get(url, params=params, headers=self.headers, timeout=15)
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        if 'data' in data and len(data['data']) > 0:
                            for item in data['data']:
                                if downloaded_count >= self.count:
                                    break
                                
                                img_url = item.get('path')
                                if img_url:
                                    try:
                                        img_response = requests.get(img_url, headers=self.headers, timeout=15)
                                        if img_response.status_code == 200 and len(img_response.content) > 50000:
                                            if self.downloader.save_image(img_response.content, "Wallhaven"):
                                                downloaded_count += 1
                                        time.sleep(0.5)
                                    except Exception as e:
                                        continue
                        else:
                            print(f"  ℹ️  No results found for '{self.downloader.search}'")
                            break
                    
                    time.sleep(1.5)  # Rate limiting
                except Exception as e:
                    print(f"  ⚠️  Error with Wallhaven API: {str(e)[:50]}")
                    continue
            
            print(f"[Wallhaven] Downloaded {downloaded_count} images")
        except Exception as e:
            print(f"[Wallhaven] Error: {e}")
    
    # ========================================================================
    # GOOGLE IMAGES
    # ========================================================================
    
    def download_from_google(self):
        """Download wallpapers from Google Images via scraping"""
        print(f"\n[Google Images] Searching for '{self.downloader.search}'...")
        
        try:
            downloaded_count = 0
            search_encoded = quote(self.downloader.search + ' wallpaper')
            
            # Google Images search with size filter
            url = f"https://www.google.com/search?q={search_encoded}&tbm=isch&tbs=isz:l"
            
            try:
                response = requests.get(url, headers=self.headers, timeout=15)
                
                if response.status_code == 200:
                    # Multiple patterns to find images
                    patterns = [
                        r'"(https?://[^"]+\.(?:jpg|jpeg|png))"',
                        r'https?://[^\s"<>]+\.(?:jpg|jpeg|png)',
                        r'"ou":"(https?://[^"]+)"'
                    ]
                    
                    all_urls = []
                    for pattern in patterns:
                        matches = re.findall(pattern, response.text)
                        all_urls.extend(matches)
                    
                    # Deduplicate and filter
                    all_urls = list(set(all_urls))
                    filtered_urls = [
                        url for url in all_urls 
                        if 'gstatic' not in url.lower() 
                        and 'google' not in url.lower()
                        and 'encrypted' not in url.lower()
                        and len(url) < 500  # Skip data URIs
                    ]
                    
                    print(f"  Found {len(filtered_urls)} potential images")
                    
                    for img_url in filtered_urls:
                        if downloaded_count >= self.count:
                            break
                        
                        try:
                            # Decode URL if needed
                            img_url = unquote(img_url)
                            
                            img_response = requests.get(img_url, headers=self.headers, timeout=10)
                            if (img_response.status_code == 200 and 
                                len(img_response.content) > 50000 and
                                img_response.headers.get('content-type', '').startswith('image/')):
                                
                                if self.downloader.save_image(img_response.content, "Google"):
                                    downloaded_count += 1
                            
                            time.sleep(0.7)
                        except Exception:
                            continue
                
            except Exception as e:
                print(f"  ⚠️  Error scraping Google: {str(e)[:50]}")
            
            print(f"[Google Images] Downloaded {downloaded_count} images")
        except Exception as e:
            print(f"[Google Images] Error: {e}")
    
    # ========================================================================
    # BING IMAGES
    # ========================================================================
    
    def download_from_bing(self):
        """Download wallpapers from Bing Images via scraping"""
        print(f"\n[Bing Images] Searching for '{self.downloader.search}'...")
        
        try:
            downloaded_count = 0
            search_encoded = quote(self.downloader.search + ' wallpaper')
            
            # Bing Images search with size filter
            url = f"https://www.bing.com/images/search?q={search_encoded}&qft=+filterui:imagesize-large&FORM=IRFLTR"
            
            try:
                response = requests.get(url, headers=self.headers, timeout=15)
                
                if response.status_code == 200:
                    # Bing-specific patterns
                    patterns = [
                        r'murl&quot;:&quot;(https?://[^&]+?\.(?:jpg|jpeg|png))',
                        r'"murl":"(https?://[^"]+\.(?:jpg|jpeg|png))"',
                        r'mediaurl=([^&]+\.(?:jpg|jpeg|png))'
                    ]
                    
                    all_urls = []
                    for pattern in patterns:
                        matches = re.findall(pattern, response.text)
                        all_urls.extend(matches)
                    
                    # Deduplicate
                    all_urls = list(set(all_urls))
                    
                    # Filter out thumbnails
                    filtered_urls = [
                        url for url in all_urls 
                        if 'th?id' not in url.lower() 
                        and 'thumbnail' not in url.lower()
                    ]
                    
                    print(f"  Found {len(filtered_urls)} potential images")
                    
                    for img_url in filtered_urls:
                        if downloaded_count >= self.count:
                            break
                        
                        try:
                            # Decode HTML entities
                            img_url = img_url.replace('&amp;', '&')
                            img_url = unquote(img_url)
                            
                            img_response = requests.get(img_url, headers=self.headers, timeout=10)
                            if (img_response.status_code == 200 and 
                                len(img_response.content) > 30000 and
                                img_response.headers.get('content-type', '').startswith('image/')):
                                
                                if self.downloader.save_image(img_response.content, "Bing"):
                                    downloaded_count += 1
                            
                            time.sleep(0.5)
                        except Exception:
                            continue
                
            except Exception as e:
                print(f"  ⚠️  Error scraping Bing: {str(e)[:50]}")
            
            print(f"[Bing Images] Downloaded {downloaded_count} images")
        except Exception as e:
            print(f"[Bing Images] Error: {e}")
