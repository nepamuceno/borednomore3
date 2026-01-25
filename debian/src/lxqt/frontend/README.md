# BNM3 GUI - BoredNoMore3 Wallpaper Manager

**Location:** `frontend/borednomore3-gui.py`  
**Version:** 1.0.3  
**Slogan:** *"Never Stare At The Same Wall Twice"*

## Description

Professional graphical interface for controlling borednomore3 wallpaper changer with real-time terminal output, process management, and persistent settings.

## Features

✨ **Live Terminal Output** - See real-time debug/info messages from the backend script  
🎛️ **Full Control Panel** - All command-line options available via GUI  
💾 **Persistent State** - Saves all settings between sessions  
🎨 **Theme Support** - Light, Dark, and System themes  
⚙️ **Process Management** - Start, Stop, and Force Kill with PID tracking  
📊 **Visual Sliders** - Easy adjustment of timing parameters  
🖥️ **Desktop Universal** - Works on all Linux desktop environments

## Installation

### Dependencies
```bash
# Ubuntu/Debian
sudo apt install python3-tk python3-pil

# Install CustomTkinter
pip3 install customtkinter
```

### Quick Start
```bash
# From frontend directory
python3 borednomore3-gui.py
```

## Interface Overview

### Sidebar (Left Panel)

#### Logo & Info
- **BNM3** branding with custom logo
- Version information
- Slogan display

#### Quick Actions
- **❓ Help** - Shows `-h` output (exits script, displays in console)
- **ℹ️ Version** - Shows `--version` output (exits script, displays in console)  
- **👤 Credits** - Shows `-c` output (exits script, displays in console)

**Note:** These buttons run the commands separately for display only. They don't affect the running instance.

#### Debug Mode
- **☑ Enable Debug Mode (-D)** - Adds `-D` flag to command for detailed real-time output

#### Process Controls
- **▶ START** - Starts wallpaper changer with current settings
- **■ STOP** - Gracefully stops process (SIGHUP)
- **⚠ FORCE KILL** - Force terminates process (SIGKILL)

#### Status Display
- **Status:** Running (green) / Stopped (gray)
- **PID:** Process ID when running

#### Theme Selector
- Light / Dark / System

#### Utility Buttons
- **💾 Save Log** - Export console output to file
- **🗑 Clear Console** - Clear terminal output
- **🧹 Cleanup Processes** - Kill orphaned background processes
- **🚪 EXIT PROGRAM** - Close GUI (with process handling)

### Main Content (Tabs)

#### ⚙ Settings Tab

**📁 FILE PATHS**
- **Script Path** - Path to `borednomore3.py` backend
- **☑ Use custom configuration file** - Override with config file
  - When checked: ALL GUI settings are IGNORED
  - Config file takes priority
- **☑ Use custom wallpaper folder** - Override default wallpaper directory
- **☑ Use patterns file** - Custom wallpaper pattern list

**⏱ TIMING**
- **Change every (seconds)** - Interval between wallpaper changes
  - Slider: 1-3600 seconds
  - Default: 300 (5 minutes)
- **Animation frames (5-100)** - Number of transition frames
  - Slider: 5-100 frames
  - Default: 10
  - More frames = smoother but slower
- **Delay per frame (seconds)** - Time between transition frames
  - Slider: 0.0001-1.0 seconds
  - Default: 0.001
  - Lower = faster transitions

**🎬 TRANSITIONS**
- **Effect IDs** - Comma-separated or ranges (e.g., `1,5,10-15`)
  - Leave empty for all 1000 transitions
  - Specific IDs only use those transitions

**⚡ OPTIONS**
- **☑ Randomize transitions** - Random transition order (`-r`)
- **☑ Randomize wallpapers** - Random wallpaper order (`-w`)
- **☑ Keep previous image** - Keep old image during transition (`-k`)

**ℹ️ INFO PANEL**
Shows configuration priority and usage tips.

#### 🖥 Console Tab

**Live Terminal Output**
- Real-time output from backend script
- Color-coded timestamps
- Debug/Info/Warning/Error messages
- Auto-scroll option
- Shows actual command execution

**What You See:**
```
================================================================================
STARTING WALLPAPER CHANGER
================================================================================
Command: python3 borednomore3.py -D -i 60 -r -w
================================================================================

[Process started with PID: 12345]

[12:30:45.123] [INFO] borednomore3 v0.7.0
[12:30:45.150] [INFO] Desktop: GNOME
[12:30:45.151] [INFO] Resolution: 1920x1080
[12:30:45.200] [INFO] Loaded 50 wallpapers
...
```

#### 🔧 Advanced Tab

**Advanced Options**
- **Python Interpreter** - Path to Python executable
  - Default: Current Python interpreter
- **Extra Arguments** - Additional command-line flags
  - For advanced users
  - Added to end of command

**📋 Command Preview**
- Shows exact command that will be executed
- Click **🔄 Update Preview** to refresh
- Useful for debugging

## Configuration Priority

Settings are applied in this order (highest to lowest):

1. **Custom Config File** (if "Use custom configuration" is checked)
2. **GUI Settings** (Settings tab values)
3. **Default Config** (`../conf/borednomore3.conf`)
4. **Script Defaults** (built into backend)

**Important:** When "Use custom configuration file" is enabled, ALL other GUI settings are IGNORED except file paths.

## Process Management

### Starting
1. Configure settings in Settings tab
2. Click **▶ START**
3. Settings controls become disabled
4. Console shows live output
5. Status changes to "Running"

### Stopping
- **■ STOP** - Sends SIGHUP, waits up to 5 seconds, then SIGKILL if needed
- **⚠ FORCE KILL** - Immediately sends SIGKILL

### Auto-cleanup
- On exit, GUI can stop running process or leave it running
- On startup, detects orphaned processes from previous sessions
- Manual cleanup available via **🧹 Cleanup Processes**

## State Persistence

GUI saves to `.bnm3_gui_state.json`:
- All settings values
- Window size and position
- Theme preference
- Debug mode state
- Last running PID
- File paths

**Location:** Same directory as GUI script

## Debug Mode (-D)

When **Enable Debug Mode (-D)** is checked:
- Adds `-D` flag to command
- Backend outputs detailed information:
  - Desktop detection details
  - Configuration loading steps
  - Wallpaper discovery process
  - Transition generation commands
  - Frame-by-frame progress
  - Resolution details
  - All ImageMagick commands

**Normal vs Debug Output:**

**Normal (INFO):**
```
[INFO] Loaded 50 wallpapers
[INFO] Next wallpaper: sunset.jpg
[INFO] Applying transition: slide-left (ID: 1)
[INFO] Transition complete
```

**Debug (-D):**
```
[DEBUG] Loading wallpapers from: /home/user/wallpapers
[DEBUG] Using patterns: ['*.jpg', '*.png']
[DEBUG] Pattern '*.jpg' matched 30 files
[DEBUG] Pattern '*.png' matched 20 files
[DEBUG] Sequential selection: index 0/49
[DEBUG] Generating 5 exit frames (slide-out-l)...
[DEBUG] Command: convert '/path/to/old.jpg' -duplicate...
[DEBUG] Transition progress: 1/10 (10.0%)
...
```

## Quick Actions Behavior

### Help (❓), Version (ℹ️), Credits (👤)

These buttons run the backend script with special flags that **exit immediately** after displaying output:

- `-h` / `--help` → Shows help, then exits
- `-v` / `--version` → Shows version, then exits  
- `-c` / `--credits` → Shows credits, then exits

**What happens:**
1. GUI runs command separately (not the main process)
2. Captures output
3. Displays in Console tab
4. Command exits with code 0
5. GUI continues normally

**These do NOT:**
- Start the main wallpaper changing process
- Affect any running process
- Continue execution after display

## Command Building

The GUI builds commands like this:

```bash
python3 borednomore3.py [OPTIONS]

# Example 1: With GUI settings
python3 borednomore3.py -D -i 60 -f 15 -r -w

# Example 2: With custom config (ignores GUI settings)
python3 borednomore3.py --config /path/to/custom.conf

# Example 3: With extra args
python3 borednomore3.py -i 120 -t 1-10 --extra-flag
```

## File Locations

```
frontend/
├── borednomore3-gui.py           # This GUI script
├── .bnm3_gui_state.json          # Saved state (auto-created)
└── README.md                      # This file

Relative paths:
├── ../backend/borednomore3.py    # Backend script
├── ../conf/borednomore3.conf     # Default config
├── ../conf/borednomore3.list     # Default patterns
└── ../wallpapers/                # Default wallpaper folder
```

## Keyboard Shortcuts

- **Ctrl+C** in terminal running GUI - Stops GUI (asks about process)
- **q** or **Q** when script is running - Backend exits (not GUI controlled)

## Error Handling

### Script Not Found
```
Error: Script file not found:
/path/to/borednomore3.py
```
**Solution:** Click **...** button and select correct script

### Already Running
```
Already Running
Wallpaper changer is already running!
```
**Solution:** Stop current process first

### Process Ended Unexpectedly
Console shows:
```
[Process ended]
```
**Solution:** Check console output for errors, fix configuration

## Tips & Tricks

### Quick Test Run
1. Set interval to 10 seconds
2. Set frames to 5
3. Enable debug mode
4. Start and watch console

### Finding Issues
1. Enable debug mode
2. Check console for error messages
3. Save log for review
4. Use command preview to verify settings

### Performance Tuning
- **Fast transitions:** Frames=5, Speed=0.0001
- **Smooth transitions:** Frames=50, Speed=0.01
- **Low CPU:** Frames=10, Speed=0.01, Interval=600

### Custom Workflows
1. Save different configs
2. Use "Use custom configuration file"
3. Switch between configs via dropdown

## Troubleshooting

**Q: GUI doesn't start?**  
A: Install customtkinter: `pip3 install customtkinter`

**Q: No output in console?**  
A: Check script path is correct, enable debug mode

**Q: Process won't stop?**  
A: Use Force Kill, then Cleanup Processes

**Q: Settings don't apply?**  
A: Uncheck "Use custom configuration file"

**Q: Orphaned processes?**  
A: Use **🧹 Cleanup Processes** button

**Q: Console fills up?**  
A: Turn off auto-scroll, or clear console

## Technical Details

### Process Management
- Uses `subprocess.Popen` with `preexec_fn=os.setsid`
- Creates process groups for clean termination
- Reads stdout/stderr in background thread
- Handles SIGKILL/SIGHUP signals

### State Persistence
- JSON format for human readability
- Atomic writes to prevent corruption
- Graceful fallback to defaults

### Terminal Output
- Real-time streaming via callbacks
- Thread-safe GUI updates
- Preserved on tab switches

## See Also

- `../backend/borednomore3.py` - Main wallpaper changer
- `../backend/README.md` - Backend documentation
- `../conf/borednomore3.conf` - Configuration file format
- `../libs/` - Backend library modules

---

**Author:** Nepamuceno  
**Repository:** https://github.com/nepamuceno/borednomore3  
**License:** See LICENSE file
