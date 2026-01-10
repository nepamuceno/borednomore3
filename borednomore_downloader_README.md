# borednomore3 - Wallpaper Fetcher

![Version](https://img.shields.io/badge/version-0.0.5-orange.svg)
![License](https://img.shields.io/badge/license-Open%20Source-green.svg)

**borednomore3** is a multi-source image downloader that automatically fetches high-resolution wallpapers from the web. Whether you want random beautiful landscapes or specific themed images, this script scrapes the best free stock photo sites to keep your collection fresh.

---

## 📸 Supported Sources

* **Bing:** Keyword-based search scraping.
* **Unsplash:** High-quality professional photography.
* **Pexels:** Curated free stock photos.
* **Lorem Picsum:** Random high-resolution placeholders.

---

## 🛠️ Prerequisites

This script requires **Python 3** and the `requests` and `Pillow` libraries.

```bash
# Update your system
sudo apt update

# Install required dependencies
sudo apt install python3-requests python3-pil

## 🚀 Installation

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/nepamuceno/borednomore3.git](https://github.com/nepamuceno/borednomore3.git)
   cd borednomore3
   
2. **Make the script executable:**
   ```bash
   chmod +x borednomore3_downloader.py
   
## 📖 Usage

Run the script by specifying a directory where the images should be saved.

./borednomore3_downloader.py [DIRECTORY] [SEARCH_KEYWORD]

### Arguments

| Argument | Description | Required |
| :--- | :--- | :--- |
| DIRECTORY | Folder where images will be saved | Yes |
| SEARCH_KEYWORD | Theme for the images (e.g., "nature", "cyberpunk") | No |

---

## 💡 Examples

* Download to a local folder:
  ./borednomore3_downloader.py ~/Pictures/borednomore3

* Search for specific themes (e.g., Space):
  ./borednomore3_downloader.py ~/Pictures/borednomore3 space

* Get help and version info:
  ./borednomore3_downloader.py --help
  ./borednomore3_downloader.py --version

---

## ⚙️ Features

* Keyword Integration: Uses your search term to fetch relevant images from Bing and Unsplash.
* Duplicate Prevention: Checks the destination folder to ensure you don't download the same file twice.
* Automatic Naming: Assigns clean, timestamped filenames to downloads.
* Error Handling: Robust timeout and connection handling to prevent the script from hanging on slow APIs.

---

## 👤 Author

**Nepamuceno Bartolo**
* Email: zzerver@gmail.com
* GitHub: https://github.com/nepamuceno/wallpapers

---
*Generated for borednomore3 v0.0.5*
