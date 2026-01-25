#!/bin/bash
# Creates all __init__.py files in the correct locations

# libs/__init__.py
cat > libs/__init__.py << 'EOF'
"""Borednomore3 library modules"""
EOF

# libs/config/__init__.py
cat > libs/config/__init__.py << 'EOF'
"""Configuration management module"""
from .config_manager import ConfigManager, DEFAULT_CONFIG
__all__ = ['ConfigManager', 'DEFAULT_CONFIG']
EOF

# libs/core/__init__.py
cat > libs/core/__init__.py << 'EOF'
"""Core functionality modules"""
from .wallpaper_manager import WallpaperManager
from .transition_engine import TransitionEngine, TRANSITIONS
__all__ = ['WallpaperManager', 'TransitionEngine', 'TRANSITIONS']
EOF

# libs/desktop/__init__.py
cat > libs/desktop/__init__.py << 'EOF'
"""Desktop environment detection and handling"""
from .desktop_detector import DesktopDetector
__all__ = ['DesktopDetector']
EOF

# libs/utils/__init__.py
cat > libs/utils/__init__.py << 'EOF'
"""Utility modules"""
from .logger import Logger, DEBUG, INFO, WARNING, ERROR
from .validator import validate_args
__all__ = ['Logger', 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'validate_args']
EOF

echo "Created __init__.py files in:"
echo "  - libs/__init__.py"
echo "  - libs/config/__init__.py"
echo "  - libs/core/__init__.py"
echo "  - libs/desktop/__init__.py"
echo "  - libs/utils/__init__.py"
