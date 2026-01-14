#!/usr/bin/env python3
"""
Dynamic Wallpaper Changer for Lubuntu/LXQt
Changes wallpapers with smooth transitions using imagemagick

Author: Nepamuceno Bartolo
Email: zzerver@gmail.com
GitHub: https://github.com/nepamuceno/borednomore3
Version: 0.5.2 - Fixed sequential vs random priority
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
    print("Error: borednomore3_transitions.py is required and must be in the same directory")
    sys.exit(1)

VERSION = "0.5.2"
AUTHOR = "Nepamuceno Bartolo"
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
                 transitions=None, randomize=False, keep_image=False):
        self.interval = interval
        self.directory = os.path.abspath(os.path.expanduser(directory))
        self.transition_frames = frames
        self.fade_speed = fade_speed
        self.wallpapers = []
        self.current_index = -1
        self.should_exit = False
        self.is_transitioning = False
        self.keep_image = keep_image
        
        # Set random seed based on current time
        random.seed(time.time())
        
        # Setup transition list
        if transitions:
            self.transition_list = transitions
        else:
            self.transition_list = list(range(1, len(TRANSITIONS) + 1))
        
        self.randomize_transitions = randomize
        self.transition_index = 0  # For sequential mode
        
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
        
        pattern = os.path.join(self.directory, "*.jpg")
        self.wallpapers = sorted(glob.glob(pattern))
        
        if not self.wallpapers:
            print(f"Error: No JPG files found in {self.directory}")
            sys.exit(1)
        
        print(f"Loaded {len(self.wallpapers)} wallpapers from {self.directory}")
    
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
    
    def change_wallpaper(self):
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
        print(f"Using {len(self.transition_list)} transitions")
        self.load_wallpapers()
        
        self.change_wallpaper()
        
        print(f"\nBoredNoMore3 running. Changing every {self.interval} seconds.")
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
╔══════════════════════════════════════════════════════════════════════════════╗
║                      BoredNoMore3 - Dynamic Wallpaper Changer                ║
║                                  Version {VERSION}                                  ║
╚══════════════════════════════════════════════════════════════════════════════╝

DESCRIPTION:
    Changes wallpapers with smooth transitions. Supports random or sequential order.

USAGE:
    python3 borednomore3.py [OPTIONS]

OPTIONS:
    -h, --help                  Show this help message and exit
    -v, --version               Show version information
    -c, --credits               Show credits
    --config <path>             Config file (default: borednomore3.conf)
    -i, --interval <sec>        Change interval (default: 300)
    -d, --directory <path>      Wallpaper directory (default: current)
    -f, --frames <num>          Transition frames (default: 10, range 5-100)
    -s, --speed <sec>           Seconds per frame (default: 0.001)
    -t, --transitions <list>    Comma-separated transition IDs (e.g., 1,5,23)
    -r, --randomize             RANDOMIZE transitions (default: SEQUENTIAL)
    -k, --keep-image            Keep previous image visible during transition

CONFIGURATION FILE:
    Created automatically if missing.
    Command-line flags always override config values.

    Example:
    [settings]
    interval = 300
    directory = .
    frames = 10
    speed = 0.001
    transitions = 1,2,3
    randomize = false
    keep_image = false

TRANSITION LIBRARY:
    {len(TRANSITIONS)} professional transitions available.

AUTHOR:
    {AUTHOR} - {GITHUB}
"""
    print(help_text)


def print_version():
    print(f"BoredNoMore3 v{VERSION}")


def print_credits():
    print(f"""
BoredNoMore3 v{VERSION}
Author: {AUTHOR}
GitHub: {GITHUB}

A dynamic wallpaper changer with smooth transitions for LXQt/Lubuntu.
Enjoy!
""")


def parse_transitions(transition_str):
    try:
        transitions = [int(t.strip()) for t in transition_str.split(',')]
        for t in transitions:
            if t < 1 or t > len(TRANSITIONS):
                print(f"Error: Transition {t} out of range (1-{len(TRANSITIONS)})")
                sys.exit(1)
        return transitions
    except ValueError:
        print("Error: -t must be comma-separated numbers (e.g., 1,5,10)")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description='BoredNoMore3 - Dynamic Wallpaper Changer',
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
    parser.add_argument('-r', '--randomize', action='store_true')  # Explicit flag
    parser.add_argument('-k', '--keep-image', action='store_true')
    
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
    
    # CRITICAL FIX: -r flag controls randomization explicitly
    # If -r is NOT passed → force sequential (even if config says true)
    config['randomize'] = args.randomize  # Only True if -r was given
    
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
    
    # Parse transitions
    transitions = None
    if config['transitions']:
        transitions = parse_transitions(config['transitions'])
    
    # Start the app
    print(f"BoredNoMore3 v{VERSION}")
    print("=" * 80)
    
    app = BoredNoMore3(
        interval=config['interval'],
        directory=config['directory'],
        frames=config['frames'],
        fade_speed=config['speed'],
        transitions=transitions,
        randomize=config['randomize'],  # Now correctly controlled by -r
        keep_image=config['keep_image']
    )
    app.run()


if __name__ == "__main__":
    main()
