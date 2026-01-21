# /home/deb/borednomore3/borednomore3/debian/src/lxqt/backend/wallpaper_adapter.py
"""
Wallpaper Adapter Module for borednomore3
Provides unified interface for different wallpaper setting methods
"""

import os
import sys
import subprocess
import ctypes
import ctypes.util
from pathlib import Path

class WallpaperAdapter:
    """Unified wallpaper setting adapter with fallback mechanisms"""
    
    def __init__(self, debug=False):
        self.debug = debug
        self.custom_binary_path = self._find_custom_binary()
        self.custom_library_path = self._find_custom_library()
        self.custom_library = None
        
        # Try to load custom library if available
        if self.custom_library_path:
            try:
                self.custom_library = ctypes.CDLL(self.custom_library_path)
                self.custom_library.set_wallpaper_universal.argtypes = [ctypes.c_char_p]
                self.custom_library.set_wallpaper_universal.restype = ctypes.c_int
                if self.debug:
                    print(f"[DEBUG] Loaded custom wallpaper library: {self.custom_library_path}")
            except Exception as e:
                if self.debug:
                    print(f"[DEBUG] Failed to load custom library: {e}")
        
        # Fallback methods in order of preference
        self.fallback_methods = [
            self._try_feh,
            self._try_nitrogen,
            self._try_pcmanfm,
            self._try_xwallpaper,
            self._try_hsetroot,
            self._try_xloadimage,
            self._try_gsettings,
            self._try_qdbus
        ]
    
    def _find_custom_binary(self):
        """Find custom binary in standard locations"""
        search_paths = [
            "./setwallpaper",
            "/usr/local/bin/setwallpaper-bnm3",
            "/usr/bin/setwallpaper-bnm3",
            os.path.join(os.path.dirname(__file__), "setwallpaper"),
            os.path.join(os.path.dirname(__file__), "..", "..", "setwallpaper", "setwallpaper")
        ]
        
        for path in search_paths:
            if os.path.isfile(path) and os.access(path, os.X_OK):
                return path
        return None
    
    def _find_custom_library(self):
        """Find custom shared library"""
        search_paths = [
            "./setwallpaper.so",
            "/usr/local/lib/setwallpaper-bnm3.so",
            "/usr/lib/setwallpaper-bnm3.so",
            os.path.join(os.path.dirname(__file__), "setwallpaper.so"),
            os.path.join(os.path.dirname(__file__), "..", "..", "setwallpaper", "setwallpaper.so")
        ]
        
        for path in search_paths:
            if os.path.isfile(path):
                return path
        return None
    
    def set_wallpaper(self, image_path):
        """Set wallpaper using best available method"""
        if not os.path.exists(image_path):
            if self.debug:
                print(f"[DEBUG] Image not found: {image_path}")
            return False
        
        # Try custom library first (fastest)
        if self.custom_library:
            try:
                result = self.custom_library.set_wallpaper_universal(image_path.encode('utf-8'))
                if result == 0:
                    if self.debug:
                        print(f"[DEBUG] Set wallpaper using custom library: {image_path}")
                    return True
            except Exception as e:
                if self.debug:
                    print(f"[DEBUG] Custom library failed: {e}")
        
        # Try custom binary second
        if self.custom_binary_path:
            try:
                result = subprocess.run(
                    [self.custom_binary_path, image_path],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=0.5
                )
                if result.returncode == 0:
                    if self.debug:
                        print(f"[DEBUG] Set wallpaper using custom binary: {image_path}")
                    return True
            except Exception as e:
                if self.debug:
                    print(f"[DEBUG] Custom binary failed: {e}")
        
        # Try fallback methods
        for method in self.fallback_methods:
            try:
                if method(image_path):
                    if self.debug:
                        print(f"[DEBUG] Set wallpaper using {method.__name__}: {image_path}")
                    return True
            except Exception as e:
                if self.debug:
                    print(f"[DEBUG] {method.__name__} failed: {e}")
                continue
        
        if self.debug:
            print(f"[DEBUG] All wallpaper methods failed for: {image_path}")
        return False
    
    def _try_feh(self, image_path):
        """Try feh wallpaper setter"""
        subprocess.run(["feh", "--bg-fill", image_path], 
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=0.5)
        return True
    
    def _try_nitrogen(self, image_path):
        """Try nitrogen wallpaper setter"""
        subprocess.run(["nitrogen", "--set-zoom-fill", image_path], 
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=0.5)
        return True
    
    def _try_pcmanfm(self, image_path):
        """Try pcmanfm-qt wallpaper setter"""
        subprocess.run(["pcmanfm-qt", "--set-wallpaper", image_path, 
                       "--wallpaper-mode=stretch", "--desktop"], 
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=0.5)
        return True
    
    def _try_xwallpaper(self, image_path):
        """Try xwallpaper setter"""
        subprocess.run(["xwallpaper", "--zoom", image_path], 
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=0.5)
        return True
    
    def _try_hsetroot(self, image_path):
        """Try hsetroot wallpaper setter"""
        subprocess.run(["hsetroot", "-fill", image_path], 
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=0.5)
        return True
    
    def _try_xloadimage(self, image_path):
        """Try xloadimage wallpaper setter"""
        subprocess.run(["xloadimage", "-onroot", "-fullscreen", image_path], 
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=0.5)
        return True
    
    def _try_gsettings(self, image_path):
        """Try GNOME gsettings"""
        uri = f"file://{image_path}"
        subprocess.run(["gsettings", "set", "org.gnome.desktop.background", 
                       "picture-uri", uri], 
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=0.5)
        return True
    
    def _try_qdbus(self, image_path):
        """Try KDE qdbus"""
        script = f'var allDesktops = desktops(); for (i=0;i<allDesktops.length;i++) {{ d = allDesktops[i]; d.wallpaperPlugin = "org.kde.image"; d.currentConfigGroup = Array("Wallpaper", "org.kde.image", "General"); d.writeConfig("Image", "file://{image_path}") }}'
        subprocess.run(["qdbus", "org.kde.plasmashell", "/PlasmaShell", 
                       "org.kde.PlasmaShell.evaluateScript", script], 
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=0.5)
        return True
    
    def get_info(self):
        """Get information about available methods"""
        info = {
            'custom_binary': self.custom_binary_path,
            'custom_library': self.custom_library_path,
            'library_loaded': self.custom_library is not None,
            'fallback_methods': [m.__name__ for m in self.fallback_methods]
        }
        return info
