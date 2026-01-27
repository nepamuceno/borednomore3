"""
Wallpaper manager - handles wallpaper loading and selection
"""

import os
import glob
import random


class WallpaperManager:
    """Manages wallpaper collection and selection"""
    
    def __init__(self, directory, patterns, randomize, logger):
        self.directory = os.path.abspath(os.path.expanduser(directory))
        self.patterns = patterns
        self.randomize = randomize
        self.logger = logger
        self.wallpapers = []
        self.current_index = -1
        
        self._load_wallpapers()
    
    def _load_wallpapers(self):
        """Load wallpapers from directory using patterns"""
        if not os.path.isdir(self.directory):
            self.logger.error(f"Directory not found: {self.directory}")
            raise FileNotFoundError(f"Wallpaper directory not found: {self.directory}")
        
        self.logger.debug(f"Loading wallpapers from: {self.directory}")
        self.logger.debug(f"Using patterns: {self.patterns}")
        
        self.wallpapers = []
        for pattern in self.patterns:
            full_pattern = os.path.join(self.directory, pattern)
            matched = sorted(glob.glob(full_pattern))
            self.wallpapers.extend(matched)
            self.logger.debug(f"Pattern '{pattern}' matched {len(matched)} files")
        
        # Remove duplicates
        self.wallpapers = sorted(list(set(self.wallpapers)))
        
        if not self.wallpapers:
            self.logger.error(f"No wallpapers found in {self.directory}")
            self.logger.error(f"Patterns used: {self.patterns}")
            raise FileNotFoundError("No wallpapers matched the patterns")
        
        self.logger.info(f"Loaded {len(self.wallpapers)} wallpapers")
        
        # Log first few wallpapers in debug mode
        if self.logger.level == 0:  # DEBUG
            for i, wp in enumerate(self.wallpapers[:5]):
                self.logger.debug(f"  [{i}] {os.path.basename(wp)}")
            if len(self.wallpapers) > 5:
                self.logger.debug(f"  ... and {len(self.wallpapers) - 5} more")
    
    def get_next(self):
        """Get next wallpaper based on selection mode"""
        if self.randomize:
            # Random selection
            self.current_index = random.randint(0, len(self.wallpapers) - 1)
            self.logger.debug(f"Random selection: index {self.current_index}")
        else:
            # Sequential selection
            self.current_index = (self.current_index + 1) % len(self.wallpapers)
            self.logger.debug(f"Sequential selection: index {self.current_index}/{len(self.wallpapers) - 1}")
        
        wallpaper = self.wallpapers[self.current_index]
        self.logger.debug(f"Selected: {wallpaper}")
        return wallpaper
    
    def get_current(self):
        """Get current wallpaper"""
        if self.current_index >= 0:
            return self.wallpapers[self.current_index]
        return None
    
    def reload(self):
        """Reload wallpaper list"""
        self.logger.info("Reloading wallpapers...")
        old_count = len(self.wallpapers)
        self._load_wallpapers()
        new_count = len(self.wallpapers)
        self.logger.info(f"Wallpapers: {old_count} -> {new_count}")
