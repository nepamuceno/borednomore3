# Borednomore3 Downloader - GUI & Backend

Modern wallpaper downloader with GUI interface for Pexels, Unsplash, and Pixabay.

## Directory Structure

```
project/
├── backend/
│   └── bnm3d.py              # Backend downloader script
├── frontend/
│   └── bnm3d-gui.py          # GUI application
├── conf/
│   ├── bnm3d.conf            # API keys config (create from template)
│   └── bnm3d-gui.conf        # GUI preferences (auto-created)
├── .env                      # Alternative API keys location (optional)
└── wallpapers/               # Default output directory
```

## Installation

### Prerequisites

```bash
pip install customtkinter requests
```

### Setup API Keys

You have two options for configuring API keys:

#### Option 1: Using conf/bnm3d.conf (Recommended)

1. Copy the template:
```bash
mkdir -p conf
cat > conf/bnm3d.conf << 'EOF'
# Borednomore3 Downloader Configuration
# API Keys for wallpaper sources

PEXELS_API=your_pexels_api_key_here
UNSPLASH_API=your_unsplash_access_key_here
PIXABAY_API=your_pixabay_api_key_here
EOF
```

2. Edit `conf/bnm3d.conf` and add your actual API keys

#### Option 2: Using .env file

1. Create `.env` in the project root:
```bash
cat > .env << 'EOF'
PEXELS_API=your_pexels_api_key_here
UNSPLASH_API=your_unsplash_access_key_here
PIXABAY_API=your_pixabay_api_key_here
EOF
```

**Note:** The backend will try `conf/bnm3d.conf` first, then fall back to `../.env`

### Get API Keys

- **Pexels:** https://www.pexels.com/api/
- **Unsplash:** https://unsplash.com/developers
- **Pixabay:** https://pixabay.com/api/docs/

## Usage

### GUI Application

```bash
python frontend/bnm3d-gui.py
```

**GUI Features:**
- Modern dark theme interface
- Real-time console output
- All parameter controls
- API key status display
- Auto-save preferences
- Browse for output directory
- Start/Stop controls

### Command Line

```bash
python backend/bnm3d.py -s "nature" -n 10 -w all
```

**Parameters:**
- `-s, --search`: Search query (required)
- `-n, --number`: Number of images (default: 5)
- `-w, --website`: pexels, unsplash, pixabay, or all (default: pexels)
- `--balanced`: Equal distribution across all sources (with `-w all`)
- `-o, --output`: Output directory (default: ./wallpapers)
- `-c, --config`: Config file path (default: conf/bnm3d.conf)
- `-d, --debug`: Enable debug mode
- `-v, --verbose`: Enable verbose output
- `-V, --version`: Show version
- `--credits`: Show credits

## Examples

### Download 10 nature images from all sources with balanced distribution:
```bash
python backend/bnm3d.py -s "nature" -n 10 -w all --balanced
```

### Download 5 city images from Pexels only:
```bash
python backend/bnm3d.py -s "city" -n 5 -w pexels
```

### Use custom config file:
```bash
python backend/bnm3d.py -s "abstract" -n 8 -c /path/to/my/config.conf
```

### Debug mode with verbose output:
```bash
python backend/bnm3d.py -s "landscape" -n 5 -d -v
```

## Configuration Priority

The backend loads API keys in this order:

1. **Config file** specified with `-c` (default: `conf/bnm3d.conf`)
2. **Fallback to** `../.env` (relative to backend script)
3. **Error** if no keys found

## GUI Preferences

GUI preferences are automatically saved to `conf/bnm3d-gui.conf`:

```
search=nature
number=5
website=pexels
balanced=false
output=./wallpapers
debug=false
verbose=false
```

## API Key Status

The GUI shows API key status:
- ✓ Green checkmark = Key configured
- ✗ Red X = Key missing

You need at least one API key to download images.

## Features

### Backend (bnm3d.py)
- Downloads from Pexels, Unsplash, and Pixabay
- Configurable via config file or .env
- Duplicate detection (SHA256 hash)
- Error handling and retry logic
- Detailed logging and statistics
- Balanced or random distribution across sources

### GUI (bnm3d-gui.py)
- Modern customtkinter interface
- Real-time console output
- All backend parameters accessible
- API key status display
- Auto-save/load preferences
- Download progress tracking
- Start/Stop controls
- Input validation

## Troubleshooting

### "No API keys found"
- Check that `conf/bnm3d.conf` exists and has keys filled in
- Or create `.env` in project root with API keys
- Make sure keys are not empty (not just `PEXELS_API=`)

### "Script not found"
- Ensure `backend/bnm3d.py` exists
- Run GUI from correct directory (frontend folder or project root)

### GUI won't start
```bash
pip install --upgrade customtkinter
```

### No images downloaded
- Check API keys are valid
- Check internet connection
- Try debug mode: `-d` flag or checkbox in GUI
- Check console output for specific errors

## Credits

Author: Nepamuceno
GitHub: https://github.com/nepamuceno/borednomore3

## License

See project LICENSE file.
