# Borednomore3 - Main Script

**Location:** `backend/borednomore3.py`  
**Version:** 0.7.0  
**Type:** Main entry point for the wallpaper changer

## Description

This is the main executable script for borednomore3. It coordinates all libraries and handles the main execution loop for dynamic wallpaper changing with smooth transitions.

## Quick Start
```bash
# From backend directory
python3 borednomore3.py

# With debug mode
python3 borednomore3.py -D

# Show help
python3 borednomore3.py -h
```

## Command-Line Arguments

### Information (Exit Immediately)
```bash
python3 borednomore3.py -h    # Help
python3 borednomore3.py -v    # Version
python3 borednomore3.py -c    # Credits
```
**Note:** These exit with code 0 after displaying information.

### Execution Options (Continue Running)
```bash
-D, --debug                     # Enable detailed debug output
-i, --interval <seconds>        # Wallpaper change interval (default: 300)
-d, --directory <path>          # Wallpaper directory
-f, --frames <number>           # Transition frames 5-100 (default: 10)
-s, --speed <seconds>           # Frame delay (default: 0.001)
-t, --transitions <list>        # Specific transitions (e.g., 1,5,10-20)
-r, --randomize                 # Randomize transition order
-w, --randomize-wallpapers      # Randomize wallpaper order
-k, --keep-image                # Keep previous image during transition
-l, --wallpaper-list <file>     # Custom pattern file
--config <path>                 # Custom config file
```

## Examples

### Basic Usage
```bash
# Run with defaults
python3 borednomore3.py

# Every 60 seconds with debug
python3 borednomore3.py -D -i 60

# Random everything
python3 borednomore3.py -r -w -i 120
```

### Advanced Usage
```bash
# Fast transitions, specific IDs only
python3 borednomore3.py -D -t 1-10,50-60 -f 5 -s 0.0001

# Custom wallpaper directory
python3 borednomore3.py -d ~/Pictures/Wallpapers -i 180

# Slow smooth transitions
python3 borednomore3.py -f 50 -s 0.01 -i 600
```

## Dependencies

### Python Modules
- **config.config_manager** - Configuration handling
- **core.wallpaper_manager** - Wallpaper loading/selection
- **core.transition_engine** - Transition effects
- **desktop.desktop_detector** - Desktop environment detection
- **utils.logger** - Logging system
- **utils.validator** - Configuration validation

All modules are loaded from `../libs/`

### System Requirements
```bash
# Install dependencies
sudo apt install imagemagick python3-pil python3-pynput
```

## How It Works

1. **Parse Arguments** - Command-line arguments override config file
2. **Detect Desktop** - Auto-detect DE (GNOME, KDE, XFCE, etc.) and resolution
3. **Load Config** - Read from config file, merge with CLI args
4. **Validate** - Check all parameters are valid
5. **Initialize Managers** - Set up wallpaper and transition handlers
6. **Main Loop** - Continuously change wallpapers with transitions

## Output Modes

### INFO Mode (Default)
```
[12:30:45.123] [INFO] borednomore3 v0.7.0
[12:30:45.150] [INFO] Desktop: GNOME
[12:30:45.151] [INFO] Resolution: 1920x1080
[12:30:45.200] [INFO] Loaded 50 wallpapers
[12:30:45.201] [INFO] Next wallpaper: sunset.jpg
[12:30:45.202] [INFO] Applying transition: slide-left (ID: 1)
[12:30:47.500] [INFO] Transition complete
```

### DEBUG Mode (-D flag)
```
[12:30:45.125] [DEBUG] Starting desktop detection...
[12:30:45.126] [DEBUG] DESKTOP_SESSION: ubuntu
[12:30:45.151] [DEBUG] Detected resolution via xrandr: 1920x1080
[12:30:45.182] [DEBUG] Loading wallpapers from: /home/user/wallpapers
[12:30:45.184] [DEBUG] Pattern '*.jpg' matched 30 files
[12:30:45.201] [DEBUG] Sequential selection: index 0/49
[12:30:45.210] [DEBUG] Generating 5 exit frames (slide-out-l)...
[12:30:46.901] [DEBUG] Transition progress: 1/10 (10.0%)
[12:30:47.491] [DEBUG] Executing: gsettings set...
```

## Path Resolution
```python
SCRIPT_DIR = backend/
LIBS_DIR = ../libs/
```

The script automatically locates libraries relative to its location:
- From `backend/` → looks in `../libs/`
- Supports `libs/config/`, `libs/core/`, `libs/desktop/`, `libs/utils/`

## Error Handling

### Import Errors
```
Error importing libraries: cannot import name 'X' from 'Y'
Make sure all libraries are in: /path/to/libs
```
**Solution:** Check that all library files exist in `../libs/`

### Configuration Errors
```
[ERROR] Configuration validation failed:
  - Interval must be >= 1 second
  - Frames must be between 5 and 100
```
**Solution:** Fix the invalid parameter values

### Desktop Detection Errors
```
[WARNING] Unknown desktop: X, Y
```
**Solution:** Script falls back to generic mode using feh/nitrogen

## Exit Codes

- **0** - Normal exit or info flag (-h, -v, -c)
- **1** - Error (missing dependencies, invalid config, no wallpapers)

## Keyboard Controls

- **q** or **Q** - Exit gracefully at any time
- **Ctrl+C** - Exit gracefully

## Configuration Priority

1. **CLI Arguments** (highest priority)
2. **Config File** (`--config` or default)
3. **Default Values** (built-in)

## File Locations

- **Script:** `backend/borednomore3.py`
- **Libraries:** `../libs/*/*.py`
- **Config:** `../conf/borednomore3.conf`
- **Patterns:** `../conf/borednomore3.list`
- **Wallpapers:** `../wallpapers/`

## Logging

- **Console:** Auto-clears every 1000 lines
- **Log File:** Optional, auto-rotates (keep last 1000 lines)
- **Colors:** Enabled for console output
  - DEBUG: Cyan
  - INFO: Green
  - WARNING: Yellow
  - ERROR: Red

## Supported Desktops

- GNOME (gsettings)
- KDE Plasma (qdbus)
- XFCE (xfconf-query)
- LXQt (pcmanfm-qt)
- MATE (gsettings)
- Cinnamon (gsettings)
- Budgie (gsettings)
- i3 (feh)
- Generic (feh/nitrogen/xwallpaper)

## Notes

- All library imports are relative to `../libs/`
- Config file is auto-created if missing
- Wallpaper directory must exist
- Supports 1000 built-in transitions
- Transitions auto-repeat if list is exhausted

## Troubleshooting

**Q: Script can't find libraries?**  
A: Check `../libs/` exists and contains all subdirectories with `__init__.py`

**Q: No wallpapers found?**  
A: Run with `-D` to see which directory is being scanned

**Q: Desktop not detected?**  
A: Run with `-D` to see environment variables

**Q: Transitions not working?**  
A: Verify `imagemagick` is installed: `convert --version`

## See Also

- `../libs/config/config_manager.py` - Configuration handling
- `../libs/core/wallpaper_manager.py` - Wallpaper management
- `../libs/core/transition_engine.py` - Transition effects
- `../libs/desktop/desktop_detector.py` - Desktop detection
- `../conf/borednomore3.conf` - Main configuration file

---

**Author:** Nepamuceno  
**Repository:** https://github.com/nepamuceno/borednomore3  
**License:** See LICENSE file
