"""
Configuration manager for borednomore3
Handles loading, saving, and merging configuration from files and CLI args
"""

import os
import configparser

# Paths - work both in development and when installed
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Determine if we're installed or running from source
if '/usr/' in SCRIPT_DIR or '/usr/local/' in SCRIPT_DIR:
    # Installed system-wide
    CONF_DIR = '/etc/borednomore3'
    WALLPAPERS_DIR = os.path.join(os.path.expanduser('~'), 'Pictures', 'Wallpapers')
    DEFAULT_CONF_FILE = os.path.join(CONF_DIR, 'borednomore3.conf')
    DEFAULT_LIST_FILE = os.path.join(CONF_DIR, 'borednomore3.list')
else:
    # Running from source
    BASE_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, '..', '..'))
    CONF_DIR = os.path.join(BASE_DIR, 'conf')
    WALLPAPERS_DIR = os.path.join(BASE_DIR, 'wallpapers')
    DEFAULT_CONF_FILE = os.path.join(CONF_DIR, 'borednomore3.conf')
    DEFAULT_LIST_FILE = os.path.join(CONF_DIR, 'borednomore3.list')

DEFAULT_CONFIG = {
    'interval': 300,
    'directory': WALLPAPERS_DIR,
    'frames': 10,
    'speed': 0.001,
    'transitions': None,
    'randomize': False,
    'keep_image': False,
    'randomize_wallpapers': False,
    'wallpaper_patterns': ['*.jpg', '*.png', '*.jpeg', '*.webp']
}


class ConfigManager:
    """Manages configuration from files and command-line arguments"""
    
    def __init__(self, logger, config_path=None):
        self.logger = logger
        self.config_path = config_path or DEFAULT_CONF_FILE
        self.config = DEFAULT_CONFIG.copy()
        
        # Ensure conf directory exists (only if running from source)
        if '/usr/' not in SCRIPT_DIR and '/usr/local/' not in SCRIPT_DIR:
            os.makedirs(CONF_DIR, exist_ok=True)
        
        # Create default config if needed and we have write permission
        if not os.path.exists(self.config_path):
            if os.access(os.path.dirname(self.config_path), os.W_OK):
                self.logger.info(f"Creating default config: {self.config_path}")
                self._create_default_config()
            else:
                self.logger.debug(f"Config file not found: {self.config_path} (will use defaults)")
        
        # Load config file
        self._load_config_file()
    
    def _create_default_config(self):
        """Create default configuration file"""
        config_dir = os.path.dirname(self.config_path)
        
        # Use absolute path if installed, relative if running from source  
        if '/usr/' in SCRIPT_DIR or '/usr/local/' in SCRIPT_DIR:
            wallpapers_path = WALLPAPERS_DIR
        else:
            wallpapers_path = os.path.relpath(WALLPAPERS_DIR, config_dir)
        
        parser = configparser.ConfigParser()
        parser['settings'] = {
            'interval': str(DEFAULT_CONFIG['interval']),
            'directory': wallpapers_path,
            'frames': str(DEFAULT_CONFIG['frames']),
            'speed': str(DEFAULT_CONFIG['speed']),
            'transitions': '',
            'randomize': str(DEFAULT_CONFIG['randomize']),
            'keep_image': str(DEFAULT_CONFIG['keep_image']),
            'randomize_wallpapers': str(DEFAULT_CONFIG['randomize_wallpapers'])
        }
        
        try:
            with open(self.config_path, 'w') as f:
                parser.write(f)
            self.logger.debug(f"Created config file: {self.config_path}")
        except Exception as e:
            self.logger.error(f"Failed to create config: {e}")
    
    def _load_config_file(self):
        """Load configuration from file"""
        if not os.path.exists(self.config_path):
            self.logger.debug(f"Config file not found: {self.config_path}, using defaults")
            return
        
        try:
            parser = configparser.ConfigParser()
            parser.read(self.config_path)
            
            if 'settings' in parser:
                settings = parser['settings']
                
                if 'interval' in settings:
                    self.config['interval'] = int(settings['interval'])
                    self.logger.debug(f"Config: interval = {self.config['interval']}")
                
                if 'directory' in settings:
                    dir_path = settings['directory']
                    if not os.path.isabs(dir_path):
                        dir_path = os.path.join(os.path.dirname(self.config_path), dir_path)
                    self.config['directory'] = os.path.abspath(dir_path)
                    self.logger.debug(f"Config: directory = {self.config['directory']}")
                
                if 'frames' in settings:
                    self.config['frames'] = int(settings['frames'])
                    self.logger.debug(f"Config: frames = {self.config['frames']}")
                
                if 'speed' in settings:
                    self.config['speed'] = float(settings['speed'])
                    self.logger.debug(f"Config: speed = {self.config['speed']}")
                
                if 'transitions' in settings and settings['transitions']:
                    self.config['transitions'] = settings['transitions']
                    self.logger.debug(f"Config: transitions = {self.config['transitions']}")
                
                if 'randomize' in settings:
                    self.config['randomize'] = settings.getboolean('randomize')
                    self.logger.debug(f"Config: randomize = {self.config['randomize']}")
                
                if 'keep_image' in settings:
                    self.config['keep_image'] = settings.getboolean('keep_image')
                    self.logger.debug(f"Config: keep_image = {self.config['keep_image']}")
                
                if 'randomize_wallpapers' in settings:
                    self.config['randomize_wallpapers'] = settings.getboolean('randomize_wallpapers')
                    self.logger.debug(f"Config: randomize_wallpapers = {self.config['randomize_wallpapers']}")
            
            self.logger.info(f"Loaded config from: {self.config_path}")
        except Exception as e:
            self.logger.error(f"Error loading config: {e}")
    
    def _load_wallpaper_patterns(self, list_file):
        """Load wallpaper patterns from list file"""
        if list_file == 'default':
            list_file = DEFAULT_LIST_FILE
        
        if not os.path.exists(list_file):
            self.logger.warning(f"Wallpaper list not found: {list_file}")
            if list_file == DEFAULT_LIST_FILE:
                self._create_default_list()
            return DEFAULT_CONFIG['wallpaper_patterns']
        
        try:
            patterns = []
            with open(list_file, 'r') as f:
                for line in f:
                    line = line.split('#', 1)[0].strip()
                    if line:
                        patterns.append(line)
            
            if not patterns:
                self.logger.warning(f"No patterns in {list_file}, using defaults")
                return DEFAULT_CONFIG['wallpaper_patterns']
            
            self.logger.info(f"Loaded {len(patterns)} patterns from {list_file}")
            return patterns
        except Exception as e:
            self.logger.error(f"Error reading wallpaper list: {e}")
            return DEFAULT_CONFIG['wallpaper_patterns']
    
    def _create_default_list(self):
        """Create default wallpaper list file"""
        patterns = [
            "*.jpg",
            "*.png",
            "*.jpeg",
            "*.webp",
            "# Add more patterns, one per line"
        ]
        
        try:
            with open(DEFAULT_LIST_FILE, 'w') as f:
                for pattern in patterns:
                    f.write(pattern + '\n')
            self.logger.debug(f"Created default wallpaper list: {DEFAULT_LIST_FILE}")
        except Exception as e:
            self.logger.error(f"Failed to create wallpaper list: {e}")
    
    def get_config(self, args):
        """Get final configuration by merging file config with CLI args"""
        # CLI args override file config
        if args.interval is not None:
            self.config['interval'] = args.interval
            self.logger.debug(f"CLI override: interval = {args.interval}")
        
        if args.directory is not None:
            self.config['directory'] = os.path.abspath(os.path.expanduser(args.directory))
            self.logger.debug(f"CLI override: directory = {self.config['directory']}")
        
        if args.frames is not None:
            self.config['frames'] = args.frames
            self.logger.debug(f"CLI override: frames = {args.frames}")
        
        if args.speed is not None:
            self.config['speed'] = args.speed
            self.logger.debug(f"CLI override: speed = {args.speed}")
        
        if args.transitions is not None:
            self.config['transitions'] = args.transitions
            self.logger.debug(f"CLI override: transitions = {args.transitions}")
        
        if args.randomize:
            self.config['randomize'] = True
            self.logger.debug("CLI override: randomize = True")
        
        if args.randomize_wallpapers:
            self.config['randomize_wallpapers'] = True
            self.logger.debug("CLI override: randomize_wallpapers = True")
        
        if args.keep_image:
            self.config['keep_image'] = True
            self.logger.debug("CLI override: keep_image = True")
        
        if args.wallpaper_list is not None:
            patterns = self._load_wallpaper_patterns(args.wallpaper_list)
            self.config['wallpaper_patterns'] = patterns
            self.logger.debug(f"CLI override: wallpaper_patterns = {patterns}")
        
        return self.config
