#!/usr/bin/env python3
"""
Dynamic Wallpaper Changer for Lubuntu/LXQt
Changes wallpapers with smooth crossfade using imagemagick

Author: Nepamuceno Bartolo
Email: zzerver@gmail.com
GitHub: https://github.com/nepamuceno/borednomore3
Version: 0.0.3
"""

import os
import sys
import time
import random
import glob
import subprocess
import tempfile
import threading
from pathlib import Path
from PIL import Image

try:
    from pynput import keyboard
except ImportError:
    print("Error: pynput is required. Install it with:")
    print("sudo apt install python3-pynput")
    sys.exit(1)


VERSION = "0.0.3"
AUTHOR = "Nepamuceno Bartolo"
EMAIL = "zzerver@gmail.com"
GITHUB = "https://github.com/nepamuceno/borednomore3"


class WallpaperChanger:
    """Main wallpaper changer application"""
    
    def __init__(self, interval, wallpaper_dir, transition_frames=20, fade_speed=0.02):
        self.interval = interval
        self.wallpaper_dir = os.path.abspath(os.path.expanduser(wallpaper_dir))
        self.transition_frames = transition_frames  # More frames = smoother transition
        self.fade_speed = fade_speed
        self.wallpapers = []
        self.current_index = -1
        self.should_exit = False
        self.is_transitioning = False
        
        # Setup global keyboard listener for 'q' key
        self.listener = keyboard.Listener(on_press=self.on_key_press)
        self.listener.start()
        
        # Get screen resolution
        self.screen_width, self.screen_height = self.get_screen_resolution()
        
    def on_key_press(self, key):
        """Handle global keyboard events"""
        try:
            if hasattr(key, 'char') and key.char == 'q':
                if not self.should_exit:
                    print("\n\nExiting (pressed 'q')...")
                    self.should_exit = True
                    if hasattr(self, 'listener'):
                        self.listener.stop()
                    sys.exit(0)
        except:
            pass
    
    def get_screen_resolution(self):
        """Get screen resolution using xrandr"""
        try:
            output = subprocess.check_output(['xrandr'], text=True)
            for line in output.split('\n'):
                if ' connected' in line and 'primary' in line:
                    parts = line.split()
                    for part in parts:
                        if 'x' in part and part[0].isdigit():
                            resolution = part.split('+')[0]
                            w, h = resolution.split('x')
                            return int(w), int(h)
            # Fallback: try first connected display
            for line in output.split('\n'):
                if ' connected' in line:
                    parts = line.split()
                    for part in parts:
                        if 'x' in part and part[0].isdigit():
                            resolution = part.split('+')[0]
                            w, h = resolution.split('x')
                            return int(w), int(h)
        except:
            pass
        return 1920, 1080  # Default fallback
        
    def load_wallpapers(self):
        """Load all JPG wallpapers from the directory"""
        if not os.path.isdir(self.wallpaper_dir):
            print(f"Error: Directory '{self.wallpaper_dir}' does not exist")
            sys.exit(1)
        
        pattern = os.path.join(self.wallpaper_dir, "*.jpg")
        self.wallpapers = glob.glob(pattern)
        
        if not self.wallpapers:
            print(f"Error: No JPG files found in {self.wallpaper_dir}")
            sys.exit(1)
        
        random.shuffle(self.wallpapers)
        print(f"Loaded {len(self.wallpapers)} wallpapers from {self.wallpaper_dir}")
    
    def set_wallpaper(self, image_path):
        """Set wallpaper using pcmanfm-qt or feh"""
        try:
            subprocess.run([
                "pcmanfm-qt", "--set-wallpaper", image_path,
                "--wallpaper-mode=stretch", "--desktop"
            ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except:
            try:
                subprocess.run(["feh", "--bg-fill", image_path], 
                             check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except:
                pass
    
    def crossfade_transition(self, old_path, new_path):
        """Create smooth crossfade transition between two wallpapers"""
        if self.should_exit:
            return
            
        print(f"  Creating smooth crossfade transition ({self.transition_frames} frames, {self.fade_speed}s per frame)...")
        
        try:
            # Open and resize images
            old_img = Image.open(old_path).convert('RGB')
            new_img = Image.open(new_path).convert('RGB')
            
            # Resize to screen resolution
            old_img = old_img.resize((self.screen_width, self.screen_height), Image.Resampling.LANCZOS)
            new_img = new_img.resize((self.screen_width, self.screen_height), Image.Resampling.LANCZOS)
            
            # Create temporary directory for transition frames
            with tempfile.TemporaryDirectory() as tmpdir:
                # Generate crossfade frames
                for i in range(self.transition_frames + 1):
                    if self.should_exit:
                        return
                        
                    alpha = i / self.transition_frames
                    
                    # Blend images
                    blended = Image.blend(old_img, new_img, alpha)
                    
                    # Save frame
                    frame_path = os.path.join(tmpdir, f"frame_{i:03d}.jpg")
                    blended.save(frame_path, "JPEG", quality=95)
                    
                    # Set as wallpaper
                    self.set_wallpaper(frame_path)
                    
                    # Small delay between frames (adjust for smoothness)
                    time.sleep(self.fade_speed)
                
                # Finally set the actual new wallpaper
                self.set_wallpaper(new_path)
                
        except Exception as e:
            print(f"  Error during transition: {e}")
            # Fallback: just set the new wallpaper
            self.set_wallpaper(new_path)
    
    def change_wallpaper(self):
        """Change to next wallpaper with transition"""
        if self.should_exit or self.is_transitioning:
            return
        
        self.is_transitioning = True
        
        old_index = self.current_index
        self.current_index = (self.current_index + 1) % len(self.wallpapers)
        
        new_wallpaper = self.wallpapers[self.current_index]
        print(f"\nChanging to: {os.path.basename(new_wallpaper)}")
        
        if old_index >= 0:
            old_wallpaper = self.wallpapers[old_index]
            # Do crossfade transition
            self.crossfade_transition(old_wallpaper, new_wallpaper)
        else:
            # First wallpaper, set immediately
            self.set_wallpaper(new_wallpaper)
        
        self.is_transitioning = False
    
    def run(self):
        """Start the wallpaper changer"""
        print(f"Screen resolution: {self.screen_width}x{self.screen_height}")
        self.load_wallpapers()
        
        # Set first wallpaper immediately
        self.change_wallpaper()
        
        print(f"\nWallpaper changer running. Changing every {self.interval} seconds.")
        print(f"Transition frames: {self.transition_frames} (higher = smoother)")
        print("\nPress 'q' anywhere to exit immediately.")
        print("Press Ctrl+C to exit.\n")
        
        try:
            while not self.should_exit:
                time.sleep(self.interval)
                if not self.should_exit:
                    self.change_wallpaper()
        except KeyboardInterrupt:
            print("\n\nExiting (Ctrl+C)...")
            if hasattr(self, 'listener'):
                self.listener.stop()
            sys.exit(0)


def print_help():
    """Print help information"""
    help_text = """
Dynamic Wallpaper Changer for Lubuntu/LXQt

Usage:
    wallpaper_changer.py [OPTIONS] INTERVAL [DIRECTORY] [FRAMES] [FADE_SPEED]

Arguments:
    INTERVAL              Time in seconds between wallpaper changes (required)
    DIRECTORY             Directory containing JPG wallpapers (default: current directory)
    FRAMES                Number of transition frames (default: 20, range: 10-50)
                         More frames = smoother but slower transition
    FADE_SPEED            Seconds per frame in transition (default: 0.02, range: 0.01-1.0)

Options:
    -h, --help           Show this help message and exit
    -v, --version        Show version information
    -c, --credits        Show credits and author information

Examples:
    wallpaper_changer.py 30                       # Change every 30s, 20 frames
    wallpaper_changer.py 60 ~/Pictures            # Change every 60s from ~/Pictures
    wallpaper_changer.py 10 ~/wallpapers 30       # 10s interval, 30 frames (smoother)
    wallpaper_changer.py 5 ~/wallpapers 15        # 5s interval, 15 frames (faster)

Controls:
    Press 'q'            Exit immediately (works globally, anywhere)
    Press Ctrl+C         Exit immediately

Transition Smoothness:
    - 10 frames  = 0.5 second transition (quick)
    - 20 frames  = 1.0 second transition (default, smooth)
    - 30 frames  = 1.5 second transition (very smooth)
    - 40 frames  = 2.0 second transition (cinematic)

Notes:
    - Uses direct wallpaper setting - no overlay windows
    - Desktop icons and applications remain fully usable
    - Creates smooth crossfade by blending images
    - Requires: python3-pynput, python3-pil
"""
    print(help_text)


def print_version():
    """Print version information"""
    print(f"Dynamic Wallpaper Changer v{VERSION}")


def print_credits():
    """Print credits and author information"""
    credits_text = f"""
Dynamic Wallpaper Changer for Lubuntu/LXQt
Version: {VERSION}

Author:  {AUTHOR}
Email:   {EMAIL}
GitHub:  {GITHUB}

License: Open Source
"""
    print(credits_text)


def main():
    # Handle special flags first
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg in ['-h', '--help']:
            print_help()
            sys.exit(0)
        elif arg in ['-v', '--version']:
            print_version()
            sys.exit(0)
        elif arg in ['-c', '--credits']:
            print_credits()
            sys.exit(0)
    
    # Parse regular arguments
    if len(sys.argv) < 2:
        print("Error: Missing required argument INTERVAL")
        print("Use --help for usage information")
        sys.exit(1)
    
    # Get interval
    try:
        interval = int(sys.argv[1])
        if interval < 1:
            raise ValueError
    except ValueError:
        print("Error: INTERVAL must be a positive integer")
        sys.exit(1)
    
    # Get directory (default to current directory)
    if len(sys.argv) >= 3:
        wallpaper_dir = sys.argv[2]
    else:
        wallpaper_dir = "."
    
    # Get transition frames (default to 20)
    if len(sys.argv) >= 4:
        try:
            frames = int(sys.argv[3])
            if frames < 5 or frames > 100:
                raise ValueError
        except ValueError:
            print("Error: FRAMES must be an integer between 5 and 100")
            sys.exit(1)
    else:
        frames = 20  # Default: 20 frames = ~1 second smooth transition

    # Get fade speed (default to 0.02s per frame)
    fade_speed = 0.02
    if len(sys.argv) >= 5:
        try:
            fade_speed = float(sys.argv[4])
            if fade_speed <= 0 or fade_speed > 1.0:
                raise ValueError
        except ValueError:
            print("Error: FADE_SPEED must be a float between 0.01 and 1.0")
            sys.exit(1)
    
    # Check dependencies
    try:
        from PIL import Image
    except ImportError:
        print("Error: PIL (Pillow) is required. Install it with:")
        print("sudo apt install python3-pil")
        sys.exit(1)
    
    # Create and run changer
    print(f"Dynamic Wallpaper Changer v{VERSION}")
    print("=" * 60)
    
    changer = WallpaperChanger(interval, wallpaper_dir, frames, fade_speed)
    changer.run()


if __name__ == "__main__":
    main()
