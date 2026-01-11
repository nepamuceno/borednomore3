#!/usr/bin/env python3
"""
Dynamic Wallpaper Changer for Lubuntu/LXQt
Changes wallpapers with smooth transitions using imagemagick

Author: Nepamuceno Bartolo
Email: zzerver@gmail.com
GitHub: https://github.com/nepamuceno/borednomore3
Version: 0.5.0
"""

import os
import sys
import time
import random
import glob
import subprocess
import tempfile
import argparse
from pathlib import Path
from PIL import Image

try:
    from pynput import keyboard
except ImportError:
    print("Error: pynput is required. Install it with:")
    print("sudo apt install python3-pynput")
    sys.exit(1)

try:
    from borednomore3_transitions import TRANSITIONS, apply_transition
except ImportError:
    print("Error: borednomore3_transitions.py is required and must be in the same directory")
    sys.exit(1)

VERSION = "0.5.0"
AUTHOR = "Nepamuceno Bartolo"
EMAIL = "(hidden)"
GITHUB = "https://github.com/nepamuceno/borednomore3"

class BoredNoMore3:
    """Main wallpaper changer application"""
    
    def __init__(self, interval=300, directory=".", frames=5, fade_speed=0.00005, 
                 transitions=None, randomize=False):
        self.interval = interval
        self.directory = os.path.abspath(os.path.expanduser(directory))
        self.transition_frames = frames
        self.fade_speed = fade_speed
        self.wallpapers = []
        self.current_index = -1
        self.should_exit = False
        self.is_transitioning = False
        
        # Setup transitions
        if transitions:
            if randomize:
                # Use specified transitions in random order
                self.transition_list = transitions.copy()
            else:
                # Use specified transitions in order
                self.transition_list = transitions
        else:
            if randomize:
                # Use all transitions in random order
                self.transition_list = list(range(1, len(TRANSITIONS) + 1))
            else:
                # Use all transitions sequentially
                self.transition_list = list(range(1, len(TRANSITIONS) + 1))
        
        self.randomize_transitions = randomize
        self.transition_index = 0
        
        # Setup global keyboard listener for 'q' and 'Q' keys
        self.listener = keyboard.Listener(on_press=self.on_key_press)
        self.listener.start()
        
        # Get screen resolution
        self.screen_width, self.screen_height = self.get_screen_resolution()
    
    def on_key_press(self, key):
        """Handle global keyboard events"""
        try:
            if hasattr(key, 'char') and key.char in ['q', 'Q']:
                if not self.should_exit:
                    print("\n\nExiting gracefully...")
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
        return 1920, 1080
    
    def load_wallpapers(self):
        """Load all JPG wallpapers from the directory"""
        if not os.path.isdir(self.directory):
            print(f"Error: Directory '{self.directory}' does not exist")
            sys.exit(1)
        
        pattern = os.path.join(self.directory, "*.jpg")
        self.wallpapers = glob.glob(pattern)
        
        if not self.wallpapers:
            print(f"Error: No JPG files found in {self.directory}")
            sys.exit(1)
        
        random.shuffle(self.wallpapers)
        print(f"Loaded {len(self.wallpapers)} wallpapers from {self.directory}")
    
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
    
    def get_next_transition(self):
        """Get next transition number"""
        if self.randomize_transitions:
            return random.choice(self.transition_list)
        else:
            transition = self.transition_list[self.transition_index]
            self.transition_index = (self.transition_index + 1) % len(self.transition_list)
            return transition
    
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
            transition_num = self.get_next_transition()
            transition_name = TRANSITIONS.get(transition_num, "fade")
            print(f"Using transition #{transition_num}: {transition_name}")
            
            apply_transition(
                old_wallpaper, new_wallpaper, transition_num,
                self.screen_width, self.screen_height,
                self.transition_frames, self.fade_speed,
                self.set_wallpaper, lambda: self.should_exit
            )
        else:
            self.set_wallpaper(new_wallpaper)
        
        self.is_transitioning = False
    
    def run(self):
        """Start the wallpaper changer"""
        print(f"Screen resolution: {self.screen_width}x{self.screen_height}")
        self.load_wallpapers()
        
        self.change_wallpaper()
        
        print(f"\nBoredNoMore3 running. Changing every {self.interval} seconds.")
        print(f"Transition frames: {self.transition_frames}")
        print(f"Available transitions: {len(TRANSITIONS)}")
        print("\nPress 'q' or 'Q' anywhere to exit immediately.")
        print("Press Ctrl+C to exit.\n")
        
        try:
            while not self.should_exit:
                time.sleep(self.interval)
                if not self.should_exit:
                    self.change_wallpaper()
        except KeyboardInterrupt:
            print("\n\nExiting gracefully...")
            if hasattr(self, 'listener'):
                self.listener.stop()
            sys.exit(0)


def print_help():
    """Print comprehensive help information"""
    help_text = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                      BoredNoMore3 - Dynamic Wallpaper Changer                ║
║                                  Version {VERSION}                                  ║
╚══════════════════════════════════════════════════════════════════════════════╝

DESCRIPTION:
    BoredNoMore3 is a sophisticated wallpaper changer for Lubuntu/LXQt that 
    provides smooth transitions between wallpapers using a comprehensive library
    of professional transition effects.

USAGE:
    borednomore3.py [OPTIONS]

OPTIONS:
    -h, --help
        Display this comprehensive help message and exit.

    -v, --version
        Display version information and exit.

    -c, --credits
        Display credits and author information.

    -i, --interval <seconds>
        Time in seconds between wallpaper changes.
        Default: 300 seconds (5 minutes)
        Example: -i 60 (change every minute)

    -d, --directory <path>
        Directory containing JPG wallpapers.
        Default: current directory
        Example: -d ~/Pictures/Wallpapers

    -f, --frames <number>
        Number of transition frames (higher = smoother transitions).
        Default: 10 frames
        Range: 5-100 frames
        Example: -f 20 (smoother transitions)

    -s, --speed <seconds>
        Seconds per frame in transition (controls transition speed).
        Default: 0.001 seconds per frame
        Range: 0.0001-1.0
        Example: -s 0.05 (slower transitions)

    -t, --transitions <list>
        Comma-separated list of transition numbers to use.
        Example: -t 1,5,10,15
        Use with -r to randomize the specified transitions.
        Without -r, transitions play in the order specified.

    -r, --randomize
        Randomize the order of transitions.
        If used with -t, randomizes only the specified transitions.
        If used alone, randomizes all available transitions.

TRANSITION LIBRARY:
    BoredNoMore3 includes {len(TRANSITIONS)} professional transitions:
    
    1. fade              2. fade-in           3. fade-out
    4. cross-fade        5. dissolve          6. cut
    7. jump-cut          8. match-cut         9. smash-cut
    10. wipe             11. iris-in          12. iris-out
    13. l-cut            14. j-cut            15. whip-pan
    16. zoom-in          17. zoom-out         18. rack-focus
    19. morph            20. invisible-cut    21. light-leak
    22. masking          23. glitch           24. pull-back
    25. push-in          26. clock-wipe       27. slide-in
    28. slide-out        29. dissolve-white   30. dip-black
    31. swipe-left       32. swipe-right      33. swipe-up
    34. swipe-down       35. barn-door        36. checker
    37. pixelate         38. spiral           39. split-vertical
    40. split-horizontal

EXAMPLES:
    Basic usage (all defaults):
        ./borednomore3.py

    Change every 30 seconds from ~/Pictures:
        ./borednomore3.py -i 30 -d ~/Pictures

    Smoother transitions with 20 frames:
        ./borednomore3.py -i 60 -f 20

    Use only fade transitions (1,2,3,4,5):
        ./borednomore3.py -t 1,2,3,4,5

    Randomize all transitions:
        ./borednomore3.py -r

    Randomize specific transitions:
        ./borednomore3.py -t 1,10,20,30 -r

    Complete custom configuration:
        ./borednomore3.py -i 120 -d ~/Wallpapers -f 15 -s 0.05 -t 1,5,10 -r

CONTROLS:
    q or Q          Exit immediately (works globally, anywhere on desktop)
    Ctrl+C          Exit immediately

TECHNICAL NOTES:
    • Requires: python3-pynput, python3-pil (Pillow)
    • Uses direct wallpaper setting - no overlay windows
    • Desktop icons and applications remain fully usable
    • Supports JPG images only
    • Images are automatically resized to screen resolution
    • Transitions are created in real-time

TRANSITION SMOOTHNESS GUIDE:
    Frames  Speed    Total Time    Quality
    ------  -------  -----------   -------
    5       0.001    0.005s        Quick/Choppy
    10      0.001    0.01s         Default/Smooth
    20      0.001    0.02s         Very Smooth
    30      0.05     1.5s          Cinematic

TROUBLESHOOTING:
    If wallpapers don't change:
    • Ensure pcmanfm-qt or feh is installed
    • Verify JPG files exist in the specified directory
    • Check file permissions

    If transitions are choppy:
    • Increase frame count with -f
    • Decrease speed with -s (higher value = slower)
    • Check system resources (CPU/RAM)

AUTHOR:
    {AUTHOR}
    {EMAIL}
    {GITHUB}

LICENSE:
    Open Source - Free to use and modify
"""
    print(help_text)


def print_version():
    """Print version information"""
    print(f"BoredNoMore3 v{VERSION}")


def print_credits():
    """Print credits and author information"""
    credits_text = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                      BoredNoMore3 - Dynamic Wallpaper Changer                ║
╚══════════════════════════════════════════════════════════════════════════════╝

Version:    {VERSION}
Author:     {AUTHOR}
Email:      {EMAIL}
GitHub:     {GITHUB}

Description:
    A sophisticated wallpaper changer for Lubuntu/LXQt featuring smooth
    transitions and a comprehensive library of professional effects.

Features:
    • {len(TRANSITIONS)} professional transition effects
    • Smooth real-time transitions
    • Global keyboard controls
    • Customizable timing and smoothness
    • Random or sequential transition playback
    • No desktop interference

License:
    Open Source - Free to use and modify

Credits:
    Developed with passion for making desktop environments more dynamic
    and visually engaging.

Thank you for using BoredNoMore3!
"""
    print(credits_text)


def parse_transitions(transition_str):
    """Parse transition string into list of integers"""
    try:
        transitions = [int(t.strip()) for t in transition_str.split(',')]
        for t in transitions:
            if t < 1 or t > len(TRANSITIONS):
                print(f"Error: Transition number {t} is out of range (1-{len(TRANSITIONS)})")
                sys.exit(1)
        return transitions
    except ValueError:
        print("Error: Transitions must be comma-separated numbers (e.g., 1,5,10)")
        sys.exit(1)


def main():
    """Main entry point"""
    try:
        parser = argparse.ArgumentParser(
            description='BoredNoMore3 - Dynamic Wallpaper Changer',
            add_help=False
        )
        
        parser.add_argument('-h', '--help', action='store_true',
                          help='Show help message')
        parser.add_argument('-v', '--version', action='store_true',
                          help='Show version information')
        parser.add_argument('-c', '--credits', action='store_true',
                          help='Show credits')
        parser.add_argument('-i', '--interval', type=int, default=300,
                          help='Interval in seconds (default: 300)')
        parser.add_argument('-d', '--directory', type=str, default='.',
                          help='Wallpaper directory (default: current directory)')
        parser.add_argument('-f', '--frames', type=int, default=10,
                          help='Number of transition frames (default: 10)')
        parser.add_argument('-s', '--speed', type=float, default=0.001,
                          help='Seconds per frame (default: 0.001)')
        parser.add_argument('-t', '--transitions', type=str, default=None,
                          help='Comma-separated transition numbers (e.g., 1,5,10)')
        parser.add_argument('-r', '--randomize', action='store_true',
                          help='Randomize transition order')
        
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
        
        # Validate interval
        if args.interval < 1:
            print("Error: Interval must be at least 1 second")
            sys.exit(1)
        
        # Validate frames
        if args.frames < 5 or args.frames > 100:
            print("Error: Frames must be between 5 and 100")
            sys.exit(1)
        
        # Validate speed
        if args.speed <= 0 or args.speed > 1.0:
            print("Error: Speed must be between 0.0001 and 1.0")
            sys.exit(1)
        
        # Parse transitions
        transitions = None
        if args.transitions:
            transitions = parse_transitions(args.transitions)
        
        # Check dependencies
        try:
            from PIL import Image
        except ImportError:
            print("Error: PIL (Pillow) is required. Install it with:")
            print("sudo apt install python3-pil")
            sys.exit(1)
        
        # Create and run
        print(f"BoredNoMore3 v{VERSION}")
        print("=" * 80)
        
        app = BoredNoMore3(
            interval=args.interval,
            directory=args.directory,
            frames=args.frames,
            fade_speed=args.speed,
            transitions=transitions,
            randomize=args.randomize
        )
        app.run()
        
    except KeyboardInterrupt:
        print("\n\nExiting gracefully...")
        sys.exit(0)
    except Exception as e:
        print(f"\nAn error occurred: {str(e)}")
        print("Use --help for usage information")
        sys.exit(1)


if __name__ == "__main__":
    main()
