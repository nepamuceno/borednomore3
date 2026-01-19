#!/usr/bin/env python3
"""
Dynamic Wallpaper Changer for Lubuntu/LXQt
Changes wallpapers with smooth transitions using OpenCV

Author: Nepamuceno
Email: (hidden)
GitHub: https://github.com/nepamuceno/borednomore3
Version: 0.7.0 - Major refactor with OpenCV, pre-calculated frames, and debug mode
"""

import os
import sys
import time
import random
import glob
import subprocess
import argparse
import configparser
from pathlib import Path

# --- STEP 1: DEFINE BASE DIRECTORIES ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LIB_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, '..', 'lib'))
TRANS_DIR = os.path.join(LIB_DIR, 'transitions')

# --- STEP 2: DEFINE CONFIG AND WALLPAPER PATHS ---
CONF_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, '..', 'conf'))
WALLPAPERS_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, '..', 'wallpapers'))

# --- STEP 3: UPDATE SYSTEM PATHS ---
if LIB_DIR not in sys.path:
    sys.path.insert(0, LIB_DIR)
if TRANS_DIR not in sys.path:
    sys.path.insert(0, TRANS_DIR)

# --- STEP 4: IMPORT ---
try:
    from borednomore3_transitions import TransitionEngine, get_curated_transitions
except ImportError as e:
    print(f"Error: Could not import borednomore3_transitions from {TRANS_DIR}")
    print(f"Python looked in: {sys.path[:2]}")
    sys.exit(1)

try:
    from PIL import Image
except ImportError:
    print("Error: PIL/Pillow is required.")
    sys.exit(1)

try:
    from pynput import keyboard
except ImportError:
    print("Error: pynput is required.")
    sys.exit(1)

try:
    import cv2
    import numpy as np
except ImportError:
    print("Error: opencv-python (cv2) and numpy are required.")
    sys.exit(1)

VERSION = "0.7.0"
AUTHOR = "Nepamuceno"
EMAIL = "(hidden)"
GITHUB = "https://github.com/nepamuceno/borednomore3"

# Default configuration values
DEFAULT_CONFIG = {
    'interval': 300,
    'directory': WALLPAPERS_DIR,
    'frames': 8,
    'speed': 0,
    'transitions': None,
    'randomize': False,
    'randomize_wallpapers': False,
    'debug': False,
    'borednomore3_gui_binary': 'borednomore3-gui'
}

# Default config file paths
DEFAULT_CONF_FILE = os.path.join(CONF_DIR, 'borednomore3.conf')
DEFAULT_LIST_FILE = os.path.join(CONF_DIR, 'borednomore3.list')


def load_config_file(config_path):
    """Load configuration from file"""
    config = {}
    if not os.path.exists(config_path):
        return config
    
    try:
        parser = configparser.ConfigParser()
        parser.read(config_path)
        
        if 'settings' in parser:
            settings = parser['settings']
            
            if 'interval' in settings:
                config['interval'] = int(settings['interval'])
            if 'directory' in settings:
                dir_path = settings['directory']
                if not os.path.isabs(dir_path):
                    dir_path = os.path.join(os.path.dirname(config_path), dir_path)
                config['directory'] = os.path.abspath(dir_path)
            if 'frames' in settings:
                config['frames'] = int(settings['frames'])
            if 'speed' in settings:
                config['speed'] = float(settings['speed'])
            if 'transitions' in settings:
                config['transitions'] = settings['transitions']
            if 'randomize' in settings:
                config['randomize'] = settings.getboolean('randomize')
            if 'randomize_wallpapers' in settings:
                config['randomize_wallpapers'] = settings.getboolean('randomize_wallpapers')
            if 'debug' in settings:
                config['debug'] = settings.getboolean('debug')
            if 'borednomore3_gui_binary' in settings:
                config['borednomore3_gui_binary'] = settings['borednomore3_gui_binary']
        
        print(f"[*] Loaded configuration from: {config_path}")
        return config
    except Exception as e:
        print(f"[WARNING] Error loading config file: {e}")
        return config


class BoredNoMore3:
    """Main wallpaper changer application"""
    
    def __init__(self, interval=300, directory=None, frames=10, fade_speed=0.001, 
                 transitions=None, randomize=False, randomize_wallpapers=False,
                 wallpaper_patterns=None, debug=False):
        
        self.debug = debug
        
        # Initialize true random seed once
        random.seed(int(time.time() * 1000000) % (2**32))
        
        if directory is None:
            self.directory = WALLPAPERS_DIR
        else:
            self.directory = os.path.abspath(os.path.expanduser(directory))
            
        self.interval = interval
        self.transition_frames = frames
        self.fade_speed = fade_speed
        self.wallpapers = []
        self.current_index = -1
        self.should_exit = False
        self.is_transitioning = False
        self.randomize_wallpapers = randomize_wallpapers
        
        # Get screen resolution
        self.screen_width, self.screen_height = self.get_screen_resolution()
        
        # Initialize transition engine
        self.transition_engine = TransitionEngine(
            self.screen_width, 
            self.screen_height,
            debug=self.debug
        )
        
        # Setup transition list
        self.curated = get_curated_transitions()
        if transitions:
            self.transition_list = transitions
        else:
            self.transition_list = list(self.curated.keys())
        
        self.randomize_transitions = randomize
        self.transition_index = 0
        
        # Wallpaper patterns
        self.wallpaper_patterns = wallpaper_patterns if wallpaper_patterns else ["*.jpg", "*.png", "*.jpeg", "*.webp"]

        # Setup keyboard listener
        self.listener = keyboard.Listener(on_press=self.on_key_press)
        self.listener.start()
        
        # Pre-calculated frames cache
        self.next_frames = None
        self.next_wallpaper = None
        self.next_transition_id = None
        
        # Cache fastest wallpaper setter method
        self.wallpaper_setter = self._detect_wallpaper_setter()
    
    def _detect_wallpaper_setter(self):
        """Detect and cache the fastest available wallpaper setter"""
        methods = [
            (["nitrogen", "--help"], lambda p: ["nitrogen", "--set-zoom-fill", p]),
            (["feh", "--version"], lambda p: ["feh", "--bg-fill", p]),
            (["xwallpaper", "--version"], lambda p: ["xwallpaper", "--zoom", p]),
            (["pcmanfm-qt", "--version"], lambda p: ["pcmanfm-qt", "--set-wallpaper", p, "--wallpaper-mode=stretch", "--desktop"]),
            (["gsettings", "help"], lambda p: ["gsettings", "set", "org.gnome.desktop.background", "picture-uri", f"file://{p}"])
        ]
        
        for test_cmd, cmd_builder in methods:
            try:
                subprocess.run(test_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=1)
                self.debug_print(f"Detected wallpaper setter: {test_cmd[0]}")
                return cmd_builder
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue
        
        self.debug_print("Warning: No wallpaper setter found!")
        return None
    
    def debug_print(self, message):
        """Print debug messages if debug mode is enabled"""
        if self.debug:
            print(f"[DEBUG] {message}")
    
    def on_key_press(self, key):
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
        """Detect screen resolution using xrandr"""
        try:
            output = subprocess.check_output(['xrandr'], text=True)
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
        """Load wallpaper list from directory"""
        if not os.path.isdir(self.directory):
            print(f"Error: Directory '{self.directory}' does not exist")
            print(f"Please create the directory or specify a different one with --directory")
            sys.exit(1)
        
        self.wallpapers = []
        for pattern in self.wallpaper_patterns:
            full_pattern = os.path.join(self.directory, pattern)
            matched = sorted(glob.glob(full_pattern))
            self.wallpapers.extend(matched)
        
        self.wallpapers = sorted(list(set(self.wallpapers)))
        
        if not self.wallpapers:
            print(f"Error: No files matched the patterns in {self.directory}")
            print(f"Patterns used: {', '.join(self.wallpaper_patterns)}")
            sys.exit(1)
        
        print(f"Loaded {len(self.wallpapers)} wallpapers from {self.directory}")
        if self.debug:
            print(f"Using patterns: {', '.join(self.wallpaper_patterns)}")
    
    def get_current_wallpaper(self):
        """Detect current system wallpaper"""
        try:
            # Try pcmanfm-qt config
            config_path = os.path.expanduser("~/.config/pcmanfm-qt/lxqt/settings.conf")
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    for line in f:
                        if 'Wallpaper=' in line:
                            wallpaper = line.split('=', 1)[1].strip()
                            if os.path.exists(wallpaper):
                                self.debug_print(f"Current wallpaper detected: {wallpaper}")
                                return wallpaper
        except Exception as e:
            self.debug_print(f"Could not detect current wallpaper: {e}")
        
        return None
    
    def set_wallpaper(self, image_path):
        """Set system wallpaper using cached fastest method"""
        if self.wallpaper_setter is None:
            self.debug_print("No wallpaper setter available")
            return
        
        try:
            cmd = self.wallpaper_setter(image_path)
            # Use Popen for non-blocking, faster execution
            subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )
        except Exception as e:
            self.debug_print(f"Error setting wallpaper: {e}")
    
    def get_next_transition(self):
        """Get next transition ID"""
        if self.randomize_transitions:
            return random.choice(self.transition_list)
        else:
            transition = self.transition_list[self.transition_index]
            self.transition_index = (self.transition_index + 1) % len(self.transition_list)
            return transition
    
    def get_next_wallpaper_index(self):
        """Get next wallpaper index"""
        if self.randomize_wallpapers:
            return random.randint(0, len(self.wallpapers) - 1)
        else:
            return (self.current_index + 1) % len(self.wallpapers)
    
    def validate_and_resize_image(self, image_path):
        """Validate if image can be resized to screen resolution"""
        try:
            img = cv2.imread(image_path)
            if img is None:
                self.debug_print(f"Cannot load image: {image_path}")
                return None
            
            # Try to resize
            resized = cv2.resize(img, (self.screen_width, self.screen_height))
            if resized is not None:
                return image_path
            return None
        except Exception as e:
            self.debug_print(f"Error validating image {image_path}: {e}")
            return None
    
    def find_valid_wallpaper(self, start_index):
        """Find next valid wallpaper that can be resized"""
        attempts = 0
        test_index = start_index
        
        while attempts < len(self.wallpapers):
            test_wallpaper = self.wallpapers[test_index]
            if self.validate_and_resize_image(test_wallpaper):
                return test_index, test_wallpaper
            
            # Try next
            if self.randomize_wallpapers:
                test_index = random.randint(0, len(self.wallpapers) - 1)
            else:
                test_index = (test_index + 1) % len(self.wallpapers)
            
            attempts += 1
        
        print("Error: No valid wallpapers found that can be resized")
        sys.exit(1)
    
    def change_wallpaper(self):
        """Change wallpaper with transition"""
        if self.should_exit or self.is_transitioning:
            return
        
        self.is_transitioning = True
        old_index = self.current_index
        
        # Get next wallpaper
        next_idx = self.get_next_wallpaper_index()
        next_idx, new_wallpaper = self.find_valid_wallpaper(next_idx)
        self.current_index = next_idx
        
        # Get transition info
        trans_id = self.get_next_transition()
        trans_info = self.curated[trans_id]
        
        # Print transition info
        print(f"\n{'='*80}")
        print(f"Transition #{trans_id}: {trans_info['name']}")
        print(f"  → {trans_info['short_desc']}")
        print(f"  → Changing to: {os.path.basename(new_wallpaper)}")
        print(f"{'='*80}")
        
        if old_index >= 0:
            old_wallpaper = self.wallpapers[old_index]
            
            self.debug_print(f"Generating {self.transition_frames} frames...")
            
            # Generate transition frames
            frames = self.transition_engine.generate_transition_frames(
                old_wallpaper, new_wallpaper, trans_id, self.transition_frames
            )
            
            if frames:
                self.debug_print(f"Playing {len(frames)} frames at {self.fade_speed}s per frame")
                
                # Play all frames
                for frame_path in frames:
                    if self.should_exit:
                        break
                    self.set_wallpaper(frame_path)
                    if self.fade_speed > 0:
                        time.sleep(self.fade_speed)
                    else:
                        time.sleep(0.016)  # ~60fps
                
                self.debug_print("Transition complete")
        
        # Set final wallpaper
        self.set_wallpaper(new_wallpaper)
        self.is_transitioning = False
    
    def run(self):
        """Main execution loop"""
        print(f"Screen resolution: {self.screen_width}x{self.screen_height}")
        print(f"Transition mode: {'RANDOM' if self.randomize_transitions else 'SEQUENTIAL'}")
        print(f"Wallpaper selection: {'RANDOM' if self.randomize_wallpapers else 'SEQUENTIAL'}")
        print(f"Debug mode: {'Enabled' if self.debug else 'Disabled'}")
        print(f"Using {len(self.transition_list)} transitions")
        
        self.load_wallpapers()
        
        # Initial wallpaper
        self.current_index = 0 if not self.randomize_wallpapers else random.randint(0, len(self.wallpapers) - 1)
        self.set_wallpaper(self.wallpapers[self.current_index])
        print(f"Initial wallpaper: {os.path.basename(self.wallpapers[self.current_index])}")
        
        print(f"\nborednomore3 running. Changing every {self.interval} seconds.")
        print(f"Transition frames: {self.transition_frames}")
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
    def_interval = DEFAULT_CONFIG['interval']
    def_dir = DEFAULT_CONFIG['directory']
    def_frames = DEFAULT_CONFIG['frames']
    def_speed = DEFAULT_CONFIG['speed']

    help_text = f"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                 borednomore3 - Dynamic Wallpaper Changer                  ║
║                                Version {VERSION}                                 ║
╚═══════════════════════════════════════════════════════════════════════════════╝

DESCRIPTION:
    Changes wallpapers with smooth transitions using OpenCV. Supports random or 
    sequential order for both transitions and wallpaper selection.

USAGE:
    borednomore3 [OPTIONS]

OPTIONS:
    -h, --help                Show this help message and exit
    -v, --version             Show version information
    -c, --credits             Show credits
    --config <path>           Path to a custom .conf file (default: {DEFAULT_CONF_FILE})
    -i, --interval <sec>      Change interval in seconds (default: {def_interval})
    -d, --directory <path>    Directory to search for wallpapers (default: {def_dir})
    -f, --frames <num>        Transition frames (default: {def_frames}, range 5-100)
    -s, --speed <sec>         Seconds per frame (default: {def_speed})
    -t, --transitions <list>  Comma-separated transition IDs (e.g., 1,5,23)
                              When used with -r, randomizes only from this list
    -r, --randomize           RANDOMIZE transitions (default: SEQUENTIAL)
    -w, --randomize-wallpapers RANDOMIZE wallpaper selection (default: SEQUENTIAL)
    -D, --debug               Enable debug output (default: disabled)
    -l, --wallpaper-list <file> Load patterns from file (default: {DEFAULT_LIST_FILE})
    --list-transitions        Show all available transitions in JSON format

CONFIGURATION PRIORITY:
    1. Command-line flags (Highest priority)
    2. Config file settings (--config or auto-detected via -l)
    3. Source code default values (Lowest priority)

PERFORMANCE:
    - Uses OpenCV for fast frame generation
    - Auto-detects fastest wallpaper setter (nitrogen > feh > pcmanfm-qt)
    - True random seed initialization for better randomization

AUTHOR:
    {AUTHOR} - {GITHUB}
"""
    print(help_text)


def print_version():
    print(f"borednomore3 v{VERSION}")


def print_credits():
    print(f"""
borednomore3 v{VERSION}
Author: {AUTHOR}
GitHub: {GITHUB}

A dynamic wallpaper changer with smooth transitions for LXQt/Lubuntu.
Powered by OpenCV for optimal performance.
Enjoy!
""")


def print_transitions_json():
    """Print transitions in JSON format for external programs"""
    import json
    transitions = get_curated_transitions()
    print(json.dumps(transitions, indent=2))


def parse_transitions(transition_str):
    """Parse transition string into list of IDs"""
    try:
        parts = [t.strip() for t in transition_str.split(',')]
        transitions = []
        for part in parts:
            if '-' in part:
                start_str, end_str = part.split('-')
                start, end = int(start_str), int(end_str)
                transitions.extend(range(start, end + 1))
            else:
                transitions.append(int(part))
        
        curated = get_curated_transitions()
        valid_transitions = []
        for t in transitions:
            if t in curated:
                valid_transitions.append(t)
            else:
                print(f"Warning: Transition {t} is not in the library. Skipping.")
        
        if not valid_transitions:
             print("Error: No valid transition IDs provided.")
             sys.exit(1)

        return sorted(set(valid_transitions))
    except ValueError:
        print("Error: -t must be comma-separated numbers or ranges (e.g., 1,5,10-15)")
        sys.exit(1)


def load_wallpaper_patterns(list_file):
    """Load wallpaper patterns from a list file"""
    patterns = []
    if not os.path.exists(list_file):
        return ["*.jpg", "*.png", "*.jpeg", "*.webp"]
    
    try:
        with open(list_file, 'r') as f:
            for line in f:
                line = line.split('#', 1)[0].strip()
                if line:
                    patterns.append(line)
        if not patterns:
            return ["*.jpg", "*.png", "*.jpeg", "*.webp"]
        print(f"Loaded {len(patterns)} wallpaper patterns from {list_file}")
        return patterns
    except Exception as e:
        print(f"Error reading wallpaper list file {list_file}: {e}")
        return ["*.jpg", "*.png", "*.jpeg", "*.webp"]


def main():
    parser = argparse.ArgumentParser(
        description='borednomore3 - Dynamic Wallpaper Changer',
        add_help=False,
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    parser.add_argument('-h', '--help', action='store_true')
    parser.add_argument('-v', '--version', action='store_true')
    parser.add_argument('-c', '--credits', action='store_true')
    parser.add_argument('--config', type=str, default=None)
    parser.add_argument('-i', '--interval', type=int, default=None)
    parser.add_argument('-d', '--directory', type=str, default=None)
    parser.add_argument('-f', '--frames', type=int, default=None)
    parser.add_argument('-s', '--speed', type=float, default=None)
    parser.add_argument('-t', '--transitions', type=str, default=None)
    parser.add_argument('-r', '--randomize', action='store_true')
    parser.add_argument('-w', '--randomize-wallpapers', action='store_true')
    parser.add_argument('-D', '--debug', action='store_true')
    parser.add_argument('-l', '--wallpaper-list', nargs='?', const=DEFAULT_LIST_FILE, 
                       default=None)
    parser.add_argument('--list-transitions', action='store_true',
                       help='Show all available transitions in JSON format')
    
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
    if args.list_transitions:
        print_transitions_json()
        sys.exit(0)
    
    # Start with defaults
    config = DEFAULT_CONFIG.copy()

    # Config file selection
    config_file = DEFAULT_CONF_FILE
    
    if args.config:
        config_file = args.config
    elif args.wallpaper_list and args.wallpaper_list != DEFAULT_LIST_FILE:
        potential_conf = os.path.splitext(args.wallpaper_list)[0] + ".conf"
        if os.path.exists(potential_conf):
            config_file = potential_conf

    if os.path.exists(config_file):
        file_config = load_config_file(config_file)
        config.update(file_config)
    
    # Command-line overrides
    if args.interval is not None:
        config['interval'] = args.interval
    if args.directory is not None:
        config['directory'] = args.directory
    if args.frames is not None:
        config['frames'] = args.frames
    if args.speed is not None:
        config['speed'] = args.speed
    if args.transitions is not None:
        config['transitions'] = args.transitions
    if args.randomize:
        config['randomize'] = True
    if args.randomize_wallpapers:
        config['randomize_wallpapers'] = True
    if args.debug:
        config['debug'] = True
    
    # Wallpaper patterns
    list_file = args.wallpaper_list if args.wallpaper_list else DEFAULT_LIST_FILE
    wallpaper_patterns = load_wallpaper_patterns(list_file)
    
    # Validate
    if config['interval'] < 1:
        print("Error: Interval must be >= 1 second")
        sys.exit(1)
    if config['frames'] < 5 or config['frames'] > 100:
        print("Error: Frames must be 5-100")
        sys.exit(1)
    if config['speed'] < 0 or config['speed'] > 1.0:
        print("Error: Speed must be 0-1.0")
        sys.exit(1)
    
    # Parse transitions
    transitions = None
    if config['transitions']:
        transitions = parse_transitions(config['transitions'])
    
    # Start the app
    print(f"borednomore3 v{VERSION}")
    print("=" * 80)
    
    app = BoredNoMore3(
        interval=config['interval'],
        directory=config['directory'],
        frames=config['frames'],
        fade_speed=config['speed'],
        transitions=transitions,
        randomize=config['randomize'],
        randomize_wallpapers=config['randomize_wallpapers'],
        wallpaper_patterns=wallpaper_patterns,
        debug=config['debug']
    )
    app.run()


if __name__ == "__main__":
    main()
