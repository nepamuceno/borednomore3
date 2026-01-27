```markdown
# BoredNoMore3 Wallpaper Manager

BoredNoMore3 is a dual-purpose tool designed to fetch high-quality images and rotate them on your desktop. Whether you want a curated collection from the web or want to cycle through your own personal memories, this tool handles the heavy lifting.

---

## 🚀 Getting Started

To get the most out of the application, you need to follow two simple steps: **Populate** your collection and **Launch** the interface.

### 1. Populate Your Wallpapers
Before running the GUI, you need a directory of images. By default, the scripts look for a folder named `wallpapers/`.

#### Option A: Use the Downloader Script
Use the built-in downloader to fetch images from Pexels and Lorem Picsum automatically.

```bash
./borednomore3_downloader.py [options]

```

**Common Flags:**

* **`-s "<search-string>"`**: Search for specific themes (e.g., "space", "nature"). *(Default: "wallpapers")*
* **`-n <number>`**: The number of images to download. *(Default: 10)*
* **`-h`**: Display the help menu and all available arguments.

**Example:**
To download 15 custom wallpapers:

```bash
./borednomore3_downloader.py -s "mountains" -n 15

```

#### Option B: Use Your Own Photos

You don’t have to download images from the web. If you prefer a personal touch, simply manually move your own photos (**family, travel, work, etc.**) into the `wallpapers/` directory. The system will recognize any standard image format you place there.

---

### 2. Launch the GUI

Once your folder is populated with images, launch the frontend to configure and execute the wallpaper changer:

```bash
./borednomore3/frontend/bnm3.py

```

---

## 🛠 Summary of Features

| Feature | Description |
| --- | --- |
| **Default Directory** | Uses the `wallpapers/` directory for all operations. |
| **Smart Numbering** | The downloader detects existing files and appends new ones without overwriting. |
| **Custom Sources** | Downloads from high-quality APIs like Pexels and Picsum. |
| **Flexibility** | Supports both automated downloads and manual personal photo collections. |

---

*Happy customizing! If you run into issues, remember to use the `-h` flag for detailed command-line instructions.*
