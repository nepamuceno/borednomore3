---

# borednomore3

**Universal Dynamic Wallpaper Changer for Debian, Ubuntu, and related distributions**

`borednomore3` is a modular suite designed specifically for Debian based distro's. It combines a high-performance Python backend with a CustomTkinter frontend to deliver smooth, ImageMagick-powered wallpaper transitions across environments like GNOME, KDE, XFCE, Cinnamon, and MATE.

## 📂 Project Architecture

The utility is structured as a native Debian package, ensuring a strict separation between logic, interface, and system configuration:

* **`frontend/bnm3.py`**: A professional GUI controller. It acts as a **Process Manager**, handling the backend lifecycle and providing a real-time console.
* **`backend/borednomore3.py`**: The core execution engine. It orchestrates the libraries to perform environment detection and execution loops.
* **`backend/borednomore3_downloader.py`**: A utility for scraping and managing high-resolution wallpaper collections.
* **`libs/`**: The core modular engine:
* `core/`: Handles **Shuffle-and-Cycle** logic and **ImageMagick Affine Distortions**.
* `desktop/`: Identifies specific wallpaper setters via `desktop_detector.py`.
* `config/` & `utils/`: Manages validation, logging, and configuration parsing.


* **`conf/`**: Contains configuration files and pattern lists.
* **`debian/`**: Full packaging stack including manpages, desktop entries, and build rules.

---

## 🖥 Frontend Logic (`bnm3.py`)

The GUI is a robust **Process Controller** with the following technical behaviors:

1. **Process Management**:
* **Start/Stop/Kill**: Uses `os.killpg` with `SIGHUP` for graceful exits and `SIGKILL` for hard termination of the backend and ImageMagick sub-processes.
* **Cleanup**: Automatically purges orphaned backend instances using `pgrep`.


2. **Live Console**: Captures real-time `stdout` and `stderr` streams from the backend, piping them into a thread-safe terminal view with auto-scroll.
3. **State Persistence**: Saves UI settings to a hidden JSON state file to restore session preferences automatically.

---

## ⚙️ Backend & Downloader Logic

The backend follows a strict priority: **CLI Flags > Custom Config > System Default.**

### Core Execution

* **Randomization**: As per the logic, randomization of transitions (`-r`) or wallpapers (`-w`) only occurs if the specific flag is set.
* **The Deck System**: Uses a Fisher-Yates shuffle to ensure no image or transition is repeated until the entire collection has been cycled.
* **Transformation**: Generates frames into temporary storage and pipes them to the desktop setter based on user-defined speed and frame counts.

### Image Acquisition

The `borednomore3_downloader.py` utility allows for keyword-based scraping to populate wallpaper directories directly from the command line.

## 📖 Further Documentation about borednomore3_downloader.py 
For detailed installation steps, troubleshooting, and advanced usage examples, please refer to the [DOWNLOADER.md](./DOWNLOADER.md) file.
---

## 🛠 Debian System Integration

Designed exclusively for Debian based distro's, the suite includes:

* **Manpages**: Native documentation accessible via the `man` command.
* **Desktop Entries**: Integrated files for the application menu.
* **Environment Detection**: Specifically targets Debian standards for wallpaper setting across various desktop environments.

---

## 📜 Installation

**Dependencies:** `python3`, `python3-pil`, `python3-tk`, `imagemagick`, and `feh`.

1. **Install dependencies**: `sudo apt install python3-pil python3-tk imagemagick feh`
2. **Run GUI**: `python3 frontend/bnm3.py`

---
