# Borednomore3 - Universal Dynamic Wallpaper Changer

Version 0.7.0 - Modular architecture with debug support and universal desktop compatibility

## Features

✨ **Universal Desktop Support**
- Auto-detects: GNOME, KDE Plasma, XFCE, LXQt, MATE, Cinnamon, Budgie, i3
- Works on any Ubuntu/Debian-based desktop
- No hardcoded desktop-specific commands

🎨 **1000 Professional Transitions**
- Slide, spin, zoom effects
- Sequential or random transition selection
- Configurable transition frames and speed

🖼️ **Smart Wallpaper Management**
- Sequential or random wallpaper selection
- Custom pattern support (*.jpg, *.png, etc.)
- Automatic wallpaper discovery

🐛 **Debug Mode**
- Real-time execution information
- Two logging levels: INFO and DEBUG
- Color-coded output for easy reading

📦 **Modular Architecture**
- Separated into logical libraries
- Easy to maintain and extend
- Clean separation of concerns

## Installation

### 1. Run Setup Script
```bash
chmod +x setup.sh
./setup.sh
```

### 2. Install Dependencies
```bash
# Ubuntu/Debian
sudo apt install imagemagick python3-pil python3-pynput

# Or using pip
pip3 install Pillow pynput
```

### 3. Copy Files to Structure
```bash
# Main script
cp borednomore3.py frontend/

# Libraries (create each file from the artifacts)
# See DIRECTORY_STRUCTURE.md for details
```

### 4. Add Wallpapers
```bash
cp /path/to/your/wallpapers/* wallpapers/
```

### 5. Make Executable
```bash
chmod +x frontend/borednomore3.py
```

## Usage

### Basic Usage
```bash
# Run with defaults
./frontend/borednomore3.py

# Show help (exits after display)
./frontend/borednomore3.py -h

# Show version (exits after display)
./frontend/borednomore3.py -v

# Show credits (exits after display)
./frontend/borednomore3.py -c
```

### Debug Mode
```bash
# Enable debug output (detailed real-time info)
./frontend/borednomore3.py -D

# Debug with custom settings
./frontend/borednomore3.py -D -i 60 -f 20
```

### Custom Configuration
```bash
# Custom wallpaper directory
./frontend/borednomore3.py -d ~/Pictures/Wallpapers

# Custom interval (seconds)
./frontend/borednomore3.py -i 120

# Custom transition frames (5-100)
./frontend/borednomore3.py -f 15

# Randomize transitions
./frontend/borednomore3.py -r

# Randomize wallpapers
./frontend/borednomore3.py -w

# Specific transitions only
./frontend/borednomore3.py -t 1,5,10-20

# Custom wallpaper patterns
./frontend/borednomore3.py -l conf/my-patterns.list
```

### Advanced Examples
```bash
# Fast transitions, random everything
./frontend/borednomore3.py -D -i 30 -f 8 -s 0.0001 -r -w

# Slow, smooth transitions with debug
./frontend/borednomore3.py -D -i 600 -f 50 -s 0.01

# Specific transitions, sequential wallpapers
./frontend/borednomore3.py -t 1-10,50-60 -i 180
```

## Command-Line Options

| Option | Description | Exit Behavior |
|--------|-------------|---------------|
| `-h, --help` | Show help message | **Exits with code 0** |
| `-v, --version` | Show version | **Exits with code 0** |
| `-c, --credits` | Show credits | **Exits with code 0** |
| `-D, --debug` | Enable debug mode | Continues execution |
| `--config <path>` | Config file path | Continues execution |
| `-i, --interval <sec>` | Change interval | Continues execution |
| `-d, --directory <path>` | Wallpaper directory | Continues execution |
| `-f, --frames <num>` | Transition frames (5-100) | Continues execution |
| `-s, --speed <sec>` | Frame delay | Continues execution |
| `-t, --transitions <list>` | Transition IDs | Continues execution |
| `-r, --randomize` | Randomize transitions | Continues execution |
| `-w, --randomize-wallpapers` | Randomize wallpapers | Continues execution |
| `-k, --keep-image` | Keep previous image | Continues execution |
| `-l, --wallpaper-list <file>` | Pattern file | Continues execution |

## Configuration File

Located at `conf/borednomore3.conf`:

```ini
[settings]
interval = 300
directory = ../wallpapers
frames = 10
speed = 0.001
transitions = 
randomize = False
keep_image = False
randomize_wallpapers = False
```

**Note**: CLI arguments always override config file settings.

## Wallpaper Patterns

Located at `conf/borednomore3.list`:

```
*.jpg
*.png
*.jpeg
*.webp
# Add more patterns, one per line
# *.bmp
# *.tiff
```

## Logging Levels

### INFO Mode (Default)
Shows basic execution flow:
```
[12:30:45.123] [INFO] borednomore3 v0.7.0
[12:30:45.150] [INFO] Desktop: GNOME
[12:30:45.151] [INFO] Resolution: 1920x1080
[12:30:45.200] [INFO] Loaded 50 wallpapers
[12:30:45.201] [INFO] Next wallpaper: sunset.jpg
[12:30:45.202] [INFO] Applying transition: slide-left (ID: 1)
[12:30:47.500] [INFO] Transition complete
```

### DEBUG Mode (-D)
Shows detailed real-time information:
```
[12:30:45.125] [DEBUG] Starting desktop detection...
[12:30:45.126] [DEBUG] DESKTOP_SESSION: ubuntu
[12:30:45.127] [DEBUG] XDG_CURRENT_DESKTOP: ubuntu:gnome
[12:30:45.151] [DEBUG] Detected resolution via xrandr: 1920x1080
[12:30:45.152] [DEBUG] Selected wallpaper setter: gsettings
[12:30:45.182] [DEBUG] Loading wallpapers from: /home/user/wallpapers
[12:30:45.183] [DEBUG] Using patterns: ['*.jpg', '*.png']
[12:30:45.184] [DEBUG] Pattern '*.jpg' matched 30 files
[12:30:45.201] [DEBUG] Sequential selection: index 0/49
[12:30:45.210] [DEBUG] Generating 5 exit frames (slide-out-l)...
[12:30:46.901] [DEBUG] Transition progress: 1/10 (10.0%)
[12:30:47.491] [DEBUG] Executing: gsettings set org.gnome.desktop.background...
```

## Supported Desktop Environments

| Desktop | Detection Method | Wallpaper Setter |
|---------|------------------|------------------|
| GNOME | XDG_CURRENT_DESKTOP | gsettings |
| KDE Plasma | XDG_CURRENT_DESKTOP | qdbus |
| XFCE | XDG_CURRENT_DESKTOP | xfconf-query |
| LXQt | XDG_CURRENT_DESKTOP | pcmanfm-qt |
| MATE | XDG_CURRENT_DESKTOP | gsettings (MATE) |
| Cinnamon | XDG_CURRENT_DESKTOP | gsettings (Cinnamon) |
| Budgie | XDG_CURRENT_DESKTOP | gsettings |
| i3 | DESKTOP_SESSION | feh |
| Generic | Fallback | feh/nitrogen/xwallpaper |

## Project Structure

```
borednomore3/
├── frontend/
│   └── borednomore3.py          # Main entry point
├── libs/
│   ├── config/
│   │   └── config_manager.py    # Configuration handling
│   ├── core/
│   │   ├── wallpaper_manager.py # Wallpaper management
│   │   └── transition_engine.py # Transition logic
│   ├── desktop/
│   │   └── desktop_detector.py  # Desktop detection
│   └── utils/
│       ├── logger.py            # Logging system
│       └── validator.py         # Validation
├── conf/
│   ├── borednomore3.conf        # Main config
│   └── borednomore3.list        # Wallpaper patterns
└── wallpapers/
    └── (your wallpapers)
```

## Editing Files

From project root:
```bash
# Main script
nano frontend/borednomore3.py

# Libraries
nano libs/config/config_manager.py
nano libs/core/wallpaper_manager.py
nano libs/core/transition_engine.py
nano libs/desktop/desktop_detector.py
nano libs/utils/logger.py
nano libs/utils/validator.py

# Configuration
nano conf/borednomore3.conf
nano conf/borednomore3.list
```

## Troubleshooting

### No wallpapers found
```bash
# Check directory exists
ls -la wallpapers/

# Check patterns in debug mode
./frontend/borednomore3.py -D
```

### Desktop not detected
```bash
# Check environment variables
echo $XDG_CURRENT_DESKTOP
echo $DESKTOP_SESSION

# Run with debug to see detection
./frontend/borednomore3.py -D
```

### Transitions not working
```bash
# Verify ImageMagick is installed
convert --version

# Check debug output
./frontend/borednomore3.py -D
```

### Import errors
```bash
# Make sure __init__.py files exist
ls -la libs/*/__init__.py

# Run setup script again
./setup.sh
```

## Development

### Adding New Desktop Support

Edit `libs/desktop/desktop_detector.py`:

```python
# Add to _detect_desktop()
elif 'mydesktop' in xdg_current_desktop:
    self.desktop_name = 'MyDesktop'
    self.desktop_session = 'mydesktop'

# Add to _select_wallpaper_setter()
setters = {
    'mydesktop': [
        ('my-setter', ['my-setter', '--wallpaper', '{}'])
    ]
}
```

### Adding New Transitions

Transitions 1-1000 are already available. To customize:

Edit `libs/core/transition_engine.py` to modify `LOGIC_MAP`.

## License

See LICENSE file

## Author

Nepamuceno - https://github.com/nepamuceno/borednomore3

## Changelog

### v0.7.0 (Current)
- Modular architecture with separate libraries
- Debug mode with real-time information
- Universal desktop environment support
- Auto-detection of screen resolution
- Improved logging system
- Better error handling
- Configuration validation

### v0.6.0
- Random wallpaper selection
- Improved transition library
- Config file support

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test on your desktop environment
5. Submit a pull request
