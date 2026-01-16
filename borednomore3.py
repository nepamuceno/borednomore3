#!/usr/bin/env python3
"""
Dynamic Wallpaper Changer for Lubuntu/LXQt
Changes wallpapers with smooth transitions using imagemagick

Author: Nepamuceno
Email: (hidden)
GitHub: https://github.com/nepamuceno/borednomore3
Version: 0.6.0 - Added random wallpaper selection feature
"""

import os
import sys
import time
import random
import glob
import subprocess
import tempfile
import argparse
import configparser
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
    print("Error: borednomore3_transitions is required and must be in the same directory")
    sys.exit(1)

VERSION = "0.6.0"
AUTHOR = "Nepamuceno"
EMAIL = "(hidden)"
GITHUB = "https://github.com/nepamuceno/borednomore3"

# Default configuration values (used if no config file exists)
DEFAULT_CONFIG = {
    'interval': 300,
    'directory': '.',
    'frames': 10,
    'speed': 0.001,
    'transitions': None,
    'randomize': False,
    'keep_image': False,
    'randomize_wallpapers': False,
    'borednomore3_gui_binary': 'borednomore3-gui'
}


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
                config['directory'] = settings['directory']
            if 'frames' in settings:
                config['frames'] = int(settings['frames'])
            if 'speed' in settings:
                config['speed'] = float(settings['speed'])
            if 'transitions' in settings:
                config['transitions'] = settings['transitions']
            if 'randomize' in settings:
                config['randomize'] = settings.getboolean('randomize')
            if 'keep_image' in settings:
                config['keep_image'] = settings.getboolean('keep_image')
            if 'randomize_wallpapers' in settings:
                config['randomize_wallpapers'] = settings.getboolean('randomize_wallpapers')
            if 'borednomore3_gui_binary' in settings:
                config['borednomore3_gui_binary'] = settings['borednomore3_gui_binary']
        
        print(f"[*] Loaded configuration from: {config_path}")
        return config
    except Exception as e:
        print(f"[WARNING] Error loading config file: {e}")
        return config


def save_default_config(config_path):
    """Create default borednomore3.conf if it doesn't exist"""
    parser = configparser.ConfigParser()
    parser['settings'] = {
        'interval': str(DEFAULT_CONFIG['interval']),
        'directory': DEFAULT_CONFIG['directory'],
        'frames': str(DEFAULT_CONFIG['frames']),
        'speed': str(DEFAULT_CONFIG['speed']),
        'transitions': '',
        'randomize': str(DEFAULT_CONFIG['randomize']),
        'keep_image': str(DEFAULT_CONFIG['keep_image']),
        'randomize_wallpapers': str(DEFAULT_CONFIG['randomize_wallpapers']),
        'borednomore3_gui_binary': DEFAULT_CONFIG['borednomore3_gui_binary']
    }
    
    try:
        with open(config_path, 'w') as f:
            parser.write(f)
        print(f"[*] Created default configuration file: {config_path}")
        return True
    except Exception as e:
        print(f"[WARNING] Failed to create default config: {e}")
        return False


class BoredNoMore3:
    """Main wallpaper changer application"""
    
    def __init__(self, interval=300, directory=".", frames=10, fade_speed=0.001, 
                 transitions=None, randomize=False, keep_image=False, randomize_wallpapers=False,
                 wallpaper_patterns=None):
        self.interval = interval
        self.directory = os.path.abspath(os.path.expanduser(directory))
        self.transition_frames = frames
        self.fade_speed = fade_speed
        self.wallpapers = []
        self.current_index = -1
        self.should_exit = False
        self.is_transitioning = False
        self.keep_image = keep_image
        self.randomize_wallpapers = randomize_wallpapers
        
        # Set random seed based on current time
        random.seed(time.time())
        
        # Setup transition list
        if transitions:
            self.transition_list = transitions
        else:
            self.transition_list = list(range(1, len(TRANSITIONS) + 1))
        
        self.randomize_transitions = randomize
        self.transition_index = 0  # For sequential mode
        
        # Wallpaper patterns (for --wallpaper-list)
        self.wallpaper_patterns = wallpaper_patterns if wallpaper_patterns else ["*.jpg", "*.png", "*.jpeg", "*.webp"]
        
        # Setup keyboard listener
        self.listener = keyboard.Listener(on_press=self.on_key_press)
        self.listener.start()
        
        # Screen resolution
        self.screen_width, self.screen_height = self.get_screen_resolution()
    
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
        if not os.path.isdir(self.directory):
            print(f"Error: Directory '{self.directory}' does not exist")
            sys.exit(1)
        
        self.wallpapers = []
        for pattern in self.wallpaper_patterns:
            full_pattern = os.path.join(self.directory, pattern)
            matched = sorted(glob.glob(full_pattern))
            self.wallpapers.extend(matched)
        
        # Remove duplicates if any patterns overlap
        self.wallpapers = sorted(list(set(self.wallpapers)))
        
        if not self.wallpapers:
            print(f"Error: No files matched the patterns in {self.directory}")
            print(f"Patterns used: {', '.join(self.wallpaper_patterns)}")
            sys.exit(1)
        
        print(f"Loaded {len(self.wallpapers)} wallpapers from {self.directory}")
        print(f"Using patterns: {', '.join(self.wallpaper_patterns)}")
    
    def set_wallpaper(self, image_path):
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
        if self.randomize_transitions:
            return random.choice(self.transition_list)
        else:
            # Sequential: cycle through the list in order
            transition = self.transition_list[self.transition_index]
            self.transition_index = (self.transition_index + 1) % len(self.transition_list)
            return transition
    
    def get_next_wallpaper_index(self):
        """Get the next wallpaper index based on randomize_wallpapers setting"""
        if self.randomize_wallpapers:
            # Random selection
            return random.randint(0, len(self.wallpapers) - 1)
        else:
            # Sequential selection
            return (self.current_index + 1) % len(self.wallpapers)
    
    def change_wallpaper(self):
        if self.should_exit or self.is_transitioning:
            return
        
        self.is_transitioning = True
        old_index = self.current_index
        self.current_index = self.get_next_wallpaper_index()
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
                self.set_wallpaper, lambda: self.should_exit,
                self.keep_image
            )
        else:
            self.set_wallpaper(new_wallpaper)
        
        self.is_transitioning = False
    
    def run(self):
        print(f"Screen resolution: {self.screen_width}x{self.screen_height}")
        print(f"Keep image mode: {'Enabled' if self.keep_image else 'Disabled'}")
        print(f"Transition mode: {'RANDOM' if self.randomize_transitions else 'SEQUENTIAL'}")
        print(f"Wallpaper selection: {'RANDOM' if self.randomize_wallpapers else 'SEQUENTIAL'}")
        print(f"Using {len(self.transition_list)} transitions")
        self.load_wallpapers()
        
        self.change_wallpaper()
        
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
    help_text = f"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                      borednomore3 - Dynamic Wallpaper Changer                ║
║                                  Version {VERSION}                                  ║
╚═══════════════════════════════════════════════════════════════════════════════╝

DESCRIPTION:
    Changes wallpapers with smooth transitions. Supports random or sequential order
    for both transitions and wallpaper selection.

USAGE:
    borednomore3 [OPTIONS]

OPTIONS:
    -h, --help                  Show this help message and exit
    -v, --version               Show version information
    -c, --credits               Show credits
    --config <path>             Config file (default: borednomore3.conf)
    -i, --interval <sec>        Change interval in seconds (default: 300)
    -d, --directory <path>      Wallpaper directory (default: current)
    -f, --frames <num>          Transition frames (default: 10, range 5-100)
    -s, --speed <sec>           Seconds per frame (default: 0.001)
    -t, --transitions <list>    Comma-separated transition IDs (e.g., 1,5,23)
                                When used with -r, randomizes only from this list
    -r, --randomize             RANDOMIZE transitions (default: SEQUENTIAL)
                                If -t is given → random from that list only
                                If no -t → random from all available transitions
    -w, --randomize-wallpapers  RANDOMIZE wallpaper selection (default: SEQUENTIAL)
                                When enabled, picks a random wallpaper each time
                                instead of cycling in order
    -k, --keep-image            Keep previous image visible during transition
    -l, --wallpaper-list <file> File with wallpaper patterns (one per line)
                                If no file given after flag → uses borednomore3.list
                                Default without flag: *.jpg, *.png, *.jpeg, *.webp

CONFIGURATION FILE:
    Created automatically if missing.
    Command-line flags always override config values.

TRANSITION LIBRARY:
    {len(TRANSITIONS)} professional transitions available.

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
Enjoy!
""")


def parse_transitions(transition_str):
    try:
        parts = [t.strip() for t in transition_str.split(',')]
        transitions = []
        for part in parts:
            if '-' in part:
                start, end = map(int, part.split('-'))
                transitions.extend(range(start, end + 1))
            else:
                transitions.append(int(part))
        
        for t in transitions:
            if t < 1 or t > len(TRANSITIONS):
                print(f"Error: Transition {t} out of range (1-{len(TRANSITIONS)})")
                sys.exit(1)
        return sorted(set(transitions))  # remove duplicates and sort
    except ValueError:
        print("Error: -t must be comma-separated numbers or ranges (e.g., 1,5,10-15)")
        sys.exit(1)


def load_wallpaper_patterns(list_file):
    """Load wallpaper patterns from a list file"""
    patterns = []
    if not os.path.exists(list_file):
        print(f"Warning: Wallpaper list file not found: {list_file}")
        return ["*.jpg", "*.png", "*.jpeg", "*.webp"]
    
    try:
        with open(list_file, 'r') as f:
            for line in f:
                # Remove inline comments (anything after #) and strip whitespace
                line = line.split('#', 1)[0].strip()
                if line:  # only add non-empty patterns
                    patterns.append(line)
        if not patterns:
            print(f"Warning: No valid patterns in {list_file}, falling back to common formats")
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
    parser.add_argument('-k', '--keep-image', action='store_true')
    parser.add_argument('-l', '--wallpaper-list', nargs='?', const='borednomore3.list', 
                       default=None, help="File with wallpaper patterns (default: borednomore3.list)")
    
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
    
    # Seed random
    random.seed(time.time())
    
    # Config file logic
    config_file = args.config if args.config else 'borednomore3.conf'
    if config_file == 'borednomore3.conf' and not os.path.exists(config_file):
        save_default_config(config_file)
    
    config = DEFAULT_CONFIG.copy()
    if os.path.exists(config_file):
        file_config = load_config_file(config_file)
        config.update(file_config)
    
    # Apply command-line overrides (highest priority)
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
    if args.keep_image:
        config['keep_image'] = True
    
    # Transition randomization: -r overrides config
    config['randomize'] = args.randomize
    
    # Wallpaper randomization: -w overrides config
    config['randomize_wallpapers'] = args.randomize_wallpapers
    
    # Wallpaper list file handling
    wallpaper_patterns = ["*.jpg", "*.png", "*.jpeg", "*.webp"]
    if args.wallpaper_list:
        wallpaper_patterns = load_wallpaper_patterns(args.wallpaper_list)
    
    # Validate
    if config['interval'] < 1:
        print("Error: Interval must be >= 1 second")
        sys.exit(1)
    if config['frames'] < 5 or config['frames'] > 100:
        print("Error: Frames must be 5-100")
        sys.exit(1)
    if config['speed'] <= 0 or config['speed'] > 1.0:
        print("Error: Speed must be 0.0001-1.0")
        sys.exit(1)
    
    # Parse transitions (command-line has highest priority)
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
        keep_image=config['keep_image'],
        randomize_wallpapers=config['randomize_wallpapers'],
        wallpaper_patterns=wallpaper_patterns
    )
    app.run()


if __name__ == "__main__":
    main()
