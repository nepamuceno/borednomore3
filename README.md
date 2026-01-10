# Dynamic Wallpaper Changer for Lubuntu/LXQt

![Version](https://img.shields.io/badge/version-0.0.3-blue.svg)
![License](https://img.shields.io/badge/license-Open%20Source-green.svg)

A lightweight Python-based wallpaper manager designed specifically for **Lubuntu (LXQt)** and other X11-based Linux distributions. This tool provides a smooth, cinematic crossfade transition between borednomore3 by dynamically blending images in real-time.

---

## ✨ Features

* **Smooth Crossfade:** Transitions between images using a frame-by-frame blending algorithm.
* **Automatic Scaling:** Detects your primary monitor resolution via `xrandr` and resizes images to fit perfectly.
* **Native Desktop Support:** Works directly with `pcmanfm-qt` (Lubuntu's default) and falls back to `feh` if needed.
* **Global Exit Key:** Press **'q'** at any time (even if the terminal isn't focused) to stop the script.
* **Resource Efficient:** Uses a temporary directory for transition frames and cleans up automatically.

---

## 🛠️ Prerequisites

The script requires **Python 3** and the following system dependencies:

```bash
# Update your package list
sudo apt update

# Install required Python libraries and X11 utilities
sudo apt install python3-pynput python3-pil x11-xserver-utils

# (Optional) Install feh as a fallback wallpaper setter
sudo apt install feh
## 🚀 Installation

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/nepamuceno/borednomore3.git](https://github.com/nepamuceno/borednomore3.git)
   cd borednomore3
   
## 📖 Usage

Run the script from your terminal using the following syntax:

```bash
./borednomore3.py INTERVAL [DIRECTORY] [FRAMES] [FADE_SPEED]

### Arguments

| Argument | Description | Default |
| :--- | :--- | :--- |
| INTERVAL | Time in seconds between wallpaper changes | Required |
| DIRECTORY | Folder containing your .jpg borednomore3 | . (current dir) |
| FRAMES | Number of transition frames (Higher = Smoother) | 20 |
| FADE_SPEED | Seconds to wait between each transition frame | 0.02 |

---

## 💡 Examples

* **Basic Start:** Change every 30 seconds using images in the current folder:
  `./borednomore3.py 30`

* **Custom Folder:** Change every 60 seconds from your Pictures directory:
  `./borednomore3.py 60 ~/Pictures/borednomore3`

* **Ultra Smooth:** Change every 10 seconds with a slow, 40-frame cinematic fade:
  `./borednomore3.py 10 ~/borednomore3 40 0.05`

* **Fast Transition:** Change every 5 seconds with a quick 10-frame snap-fade:
  `./borednomore3.py 5 ~/borednomore3 10`

---

## ⌨️ Controls

* **'q'**: Exit the program immediately (Works globally).
* **Ctrl + C**: Exit via the terminal.

---

## 📝 Transition Smoothness Guide

* **10 frames**: ~0.5 second transition (quick)
* **20 frames**: ~1.0 second transition (default, smooth)
* **30 frames**: ~1.5 second transition (very smooth)
* **40 frames**: ~2.0 second transition (cinematic)

---

## 👤 Author

**Nepamuceno Bartolo**
* **Email:** zzerver@gmail.com
* **GitHub:** [https://github.com/nepamuceno/borednomore3](https://github.com/nepamuceno/borednomore3)

---
*Generated for version 0.0.3*
