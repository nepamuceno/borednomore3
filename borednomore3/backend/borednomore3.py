#!/usr/bin/env python3
"""
Dynamic Wallpaper Changer - Universal Desktop Support
Main entry point with debug capabilities
Author: Nepamuceno
Version: 0.7.0 - Modular refactor with debug mode
"""
import os
import sys
import time
import argparse

# Path setup - works both in development and when installed
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Determine correct library path
if '/usr/' in SCRIPT_DIR or '/usr/local/' in SCRIPT_DIR:
	# Installed: libs are in same directory as this script
	LIBS_BASE = SCRIPT_DIR
else:
	# Development: libs are one level up from backend/
	LIBS_BASE = os.path.abspath(os.path.join(SCRIPT_DIR, '..'))

# Add to Python path
sys.path.insert(0, LIBS_BASE)

# Import libraries
try:
	from libs.config.config_manager import ConfigManager, DEFAULT_CONFIG
	from libs.core.wallpaper_manager import WallpaperManager
	from libs.core.transition_engine import TransitionEngine
	from libs.desktop.desktop_detector import DesktopDetector
	from libs.utils.logger import Logger, DEBUG, INFO
	from libs.utils.validator import validate_args
except ImportError as e:
	print(f"Error importing libraries: {e}")
	print(f"Script directory: {SCRIPT_DIR}")
	print(f"sys.path: {sys.path}")
	sys.exit(1)

VERSION = "0.7.0"
AUTHOR = "Nepamuceno"
GITHUB = "https://github.com/nepamuceno/borednomore3"


def print_help():
	help_text = f"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                      borednomore3 - Dynamic Wallpaper Changer                 ║
║                                  Version {VERSION}                            ║
╚═══════════════════════════════════════════════════════════════════════════════╝

DESCRIPTION:
	Universal wallpaper changer with smooth transitions for all major Linux desktops
	(GNOME, KDE, XFCE, LXQt, MATE, Cinnamon, and more)

USAGE:
	borednomore3 [OPTIONS]

OPTIONS:
	-h, --help                  Show this help and exit
	-v, --version               Show version and exit
	-c, --credits               Show credits and exit
	-D, --debug                 Enable debug mode (detailed real-time info)
	
	--config <path>             Config file path
	-i, --interval <sec>        Change interval in seconds (default: 300)
	-d, --directory <path>      Wallpaper directory
	-f, --frames <num>          Transition frames (5-100, default: 10)
	-s, --speed <sec>           Frame delay (default: 0.001)
	-t, --transitions <list>    Transition IDs (e.g., 1,5,23 or 1-10)
	-r, --randomize             Randomize transitions
	-w, --randomize-wallpapers  Randomize wallpaper selection
	-k, --keep-image            Keep previous image during transition
	-l, --wallpaper-list <file> Custom wallpaper pattern file

AUTHOR:
	{AUTHOR} - {GITHUB}

NOTE:
	Options -v, -c, -h exit immediately after displaying information.
	All other options continue execution with the specified settings.
"""
	print(help_text)


def print_version():
	print(f"borednomore3 v{VERSION}")


def print_credits():
	print(f"""
borednomore3 v{VERSION}
Author: {AUTHOR}
GitHub: {GITHUB}

Universal dynamic wallpaper changer with smooth transitions.
Supports all major Linux desktop environments.
""")


def main():
	parser = argparse.ArgumentParser(
	    description='borednomore3 - Universal Wallpaper Changer',
	    add_help=False
	)
	
	parser.add_argument('-h', '--help', action='store_true')
	parser.add_argument('-v', '--version', action='store_true')
	parser.add_argument('-c', '--credits', action='store_true')
	parser.add_argument('-D', '--debug', action='store_true')
	parser.add_argument('--config', type=str, default=None)
	parser.add_argument('-i', '--interval', type=int, default=None)
	parser.add_argument('-d', '--directory', type=str, default=None)
	parser.add_argument('-f', '--frames', type=int, default=None)
	parser.add_argument('-s', '--speed', type=float, default=None)
	parser.add_argument('-t', '--transitions', type=str, default=None)
	parser.add_argument('-r', '--randomize', action='store_true')
	parser.add_argument('-w', '--randomize-wallpapers', action='store_true')
	parser.add_argument('-k', '--keep-image', action='store_true')
	parser.add_argument('-l', '--wallpaper-list', nargs='?', const='default', default=None)
	
	args = parser.parse_args()
	
	# Info flags exit immediately
	if args.help:
	    print_help()
	    sys.exit(0)
	if args.version:
	    print_version()
	    sys.exit(0)
	if args.credits:
	    print_credits()
	    sys.exit(0)
	
	# Initialize logger
	log_level = DEBUG if args.debug else INFO
	logger = Logger(log_level)
	
	logger.info(f"borednomore3 v{VERSION}")
	logger.info("=" * 80)
	
	# Detect desktop environment
	logger.info("Detecting desktop environment...")
	desktop = DesktopDetector(logger)
	desktop_info = desktop.detect()
	
	logger.info(f"Desktop: {desktop_info['name']}")
	logger.info(f"Resolution: {desktop_info['width']}x{desktop_info['height']}")
	logger.debug(f"Wallpaper setter: {desktop_info['setter']}")
	
	# Load configuration
	logger.info("Loading configuration...")
	config_manager = ConfigManager(logger, args.config)
	config = config_manager.get_config(args)
	
	# Validate configuration
	logger.debug("Validating configuration...")
	validate_args(config, logger)
	
	# Initialize managers
	logger.info("Initializing wallpaper manager...")
	wallpaper_mgr = WallpaperManager(
	    config['directory'],
	    config['wallpaper_patterns'],
	    config['randomize_wallpapers'],
	    logger
	)
	
	logger.info("Initializing transition engine...")
	transition_engine = TransitionEngine(
	    config['transitions'],
	    config['randomize'],
	    config['frames'],
	    config['speed'],
	    config['keep_image'],
	    desktop_info,
	    logger
	)
	
	# Main loop
	logger.info(f"Starting main loop (interval: {config['interval']}s)")
	logger.info("Press 'q' or Ctrl+C to exit\n")

	try:
	    current_wallpaper = wallpaper_mgr.get_next()
	
	    while True:
	        next_wallpaper = wallpaper_mgr.get_next()
	    
	        logger.info(f"Next wallpaper: {os.path.basename(next_wallpaper)}")
	        logger.debug(f"Full path: {next_wallpaper}")
	    
	        transition = transition_engine.get_next_transition()
	        logger.info(f"Applying transition: {transition['name']} (ID: {transition['id']})")
	        logger.debug(f"Transition details: {transition}")
	    
	        transition_engine.apply(
	            current_wallpaper,
	            next_wallpaper,
	            transition,
	            desktop.set_wallpaper
	        )
	    
	        current_wallpaper = next_wallpaper
	        logger.debug(f"Waiting {config['interval']} seconds...")
	        time.sleep(config['interval'])
	    
	except KeyboardInterrupt:
	    logger.info("\nExiting gracefully...")
	    sys.exit(0)


if __name__ == "__main__":
	main()
