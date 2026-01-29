"""
Wallpaper manager - handles wallpaper selection and shuffling
"""

import os
import glob
import random


class WallpaperManager:
    """Manages wallpaper loading and randomization"""
    
    def __init__(self, directory, patterns, randomize, logger):
        self.logger = logger
        self.directory = directory
        self.patterns = patterns
        self.randomize = randomize
        self.wallpapers = []
        self.current_index = 0
        self.shuffle_playlist = []
        
        # Seed random with high-resolution time
        random.seed()
        
        self._load_wallpapers()
        
        if self.randomize:
            self._create_shuffle_playlist()
    
    def _load_wallpapers(self):
        """Load wallpapers matching patterns from directory"""
        if not os.path.exists(self.directory):
            self.logger.error(f"Directory not found: {self.directory}")
            raise FileNotFoundError(f"Wallpaper directory not found: {self.directory}")
        
        self.logger.debug(f"Loading wallpapers from: {self.directory}")
        self.logger.debug(f"Using patterns: {self.patterns}")
        
        all_files = []
        for pattern in self.patterns:
            full_pattern = os.path.join(self.directory, pattern)
            files = glob.glob(full_pattern)
            all_files.extend(files)
            self.logger.debug(f"Pattern '{pattern}' matched {len(files)} files")
        
        self.wallpapers = sorted(set(all_files))
        
        if not self.wallpapers:
            self.logger.error(f"No wallpapers found in {self.directory}")
            raise FileNotFoundError(f"No wallpapers found matching patterns: {self.patterns}")
        
        self.logger.info(f"Loaded {len(self.wallpapers)} wallpapers")
        
        for i, wp in enumerate(self.wallpapers[:5]):
            self.logger.debug(f"  {i+1}. {os.path.basename(wp)}")
        if len(self.wallpapers) > 5:
            self.logger.debug(f"  ... and {len(self.wallpapers)-5} more")
    
    def _create_shuffle_playlist(self):
        """Create a new shuffled playlist"""
        self.shuffle_playlist = self.wallpapers.copy()
        random.shuffle(self.shuffle_playlist)
        self.current_index = 0
        self.logger.debug(f"Created new shuffle playlist with {len(self.shuffle_playlist)} wallpapers")
    
    def get_next(self):
        """Get next wallpaper based on randomization setting"""
        if self.randomize:
            # True shuffle: go through entire playlist before reshuffling
            if self.current_index >= len(self.shuffle_playlist):
                self.logger.debug("Shuffle playlist exhausted, creating new playlist")
                self._create_shuffle_playlist()
            
            wallpaper = self.shuffle_playlist[self.current_index]
            self.current_index += 1
            self.logger.debug(f"Shuffle mode: {self.current_index}/{len(self.shuffle_playlist)}")
            return wallpaper
        else:
            # Sequential mode
            wallpaper = self.wallpapers[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.wallpapers)
            self.logger.debug(f"Sequential mode: {self.current_index}/{len(self.wallpapers)}")
            return wallpaper
