"""
BoredNoMore3 - Dynamic Wallpaper Changer

Universal wallpaper management suite for Debian-based Linux distributions
with smooth ImageMagick-powered transitions.
"""

__version__ = '0.7.0'
__author__ = 'Nepamuceno Bartolo'
__license__ = 'GPL-3.0+'
__url__ = 'https://github.com/nepamuceno/borednomore3'
__description__ = 'Dynamic wallpaper changer with smooth transitions'

# Import main components for easy access
from borednomore3.libs.config import ConfigManager
from borednomore3.libs.core import WallpaperManager, TransitionEngine
from borednomore3.libs.desktop import DesktopDetector
from borednomore3.libs.utils import Logger

__all__ = [
    '__version__',
    '__author__',
    '__license__',
    '__url__',
    '__description__',
    'ConfigManager',
    'WallpaperManager',
    'TransitionEngine',
    'DesktopDetector',
    'Logger',
]
