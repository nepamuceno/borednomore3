#!/usr/bin/env python3
"""
Wallpaper Fetcher Script
Descarga nuevos wallpapers desde Bing, Unsplash, Pexels y Lorem Picsum
y los guarda en el directorio especificado.

Image Sources:
- Bing (https://bing.com/images)
- Unsplash (https://unsplash.com) - Free stock photos
- Pexels (https://pexels.com) - Free stock photos
- Lorem Picsum (https://picsum.photos) - Random photos

Author: Nepamuceno Bartolo
Email: zzerver@gmail.com
GitHub: https://github.com/nepamuceno/wallpapers
Version: 0.0.5
"""

import os
import sys
import time
import random
import glob
import subprocess
import tempfile
import threading
import requests
from pathlib import Path
from PIL import Image

VERSION = "0.0.5"
AUTHOR = "Nepamuceno Bartolo"
EMAIL = "zzerver@gmail.com"
GITHUB = "https://github.com/nepamuceno/wallpapers"


class WallpaperFetcher:
    """Clase principal para buscar y descargar wallpapers"""

    def __init__(self, wallpaper_dir, keyword=None):
        self.wallpaper_dir = os.path.abspath(os.path.expanduser(wallpaper_dir))
        self.keyword = keyword
        self.downloaded = []

        if not os.path.isdir(self.wallpaper_dir):
            print(f"Error: El directorio '{self.wallpaper_dir}' no existe")
            sys.exit(1)

    def download_from_bing(self):
        """Descargar wallpapers desde Bing según palabra clave"""
        if not self.keyword:
            print("No se especificó palabra clave para Bing.")
            return

        print(f"Buscando en Bing: \"{self.keyword}\" ...")
        try:
            search_url = f"https://www.bing.com/images/search?q={self.keyword}&form=HDRSC2"
            response = requests.get(search_url, timeout=10)
            if response.status_code != 200:
                print("Error al buscar en Bing.")
                return

            urls = []
            for line in response.text.split('"'):
                if line.startswith("http") and (".jpg" in line or ".jpeg" in line):
                    urls.append(line)

            for url in urls[:10]:
                filename = os.path.basename(url.split("?")[0])
                save_path = os.path.join(self.wallpaper_dir, filename)
                if os.path.exists(save_path):
                    continue
                try:
                    img_data = requests.get(url, timeout=10).content
                    with open(save_path, "wb") as f:
                        f.write(img_data)
                    self.downloaded.append(save_path)
                    print(f"Descargado desde Bing: {filename}")
                except Exception as e:
                    print(f"Error al descargar {url}: {e}")
        except Exception as e:
            print(f"Error general en Bing: {e}")

    def download_from_unsplash(self):
        """Descargar wallpapers desde Unsplash"""
        print("Descargando desde Unsplash ...")
        try:
            for i in range(5):
                url = f"https://source.unsplash.com/random/1920x1080/?{self.keyword or 'wallpaper'}"
                filename = f"unsplash_{int(time.time())}_{i}.jpg"
                save_path = os.path.join(self.wallpaper_dir, filename)
                if os.path.exists(save_path):
                    continue
                img_data = requests.get(url, timeout=10).content
                with open(save_path, "wb") as f:
                    f.write(img_data)
                self.downloaded.append(save_path)
                print(f"Descargado desde Unsplash: {filename}")
        except Exception as e:
            print(f"Error en Unsplash: {e}")

    def download_from_pexels(self):
        """Descargar wallpapers desde Pexels"""
        print("Descargando desde Pexels ...")
        try:
            for i in range(5):
                url = f"https://images.pexels.com/photos/{random.randint(1000,9999)}/pexels-photo.jpg"
                filename = f"pexels_{int(time.time())}_{i}.jpg"
                save_path = os.path.join(self.wallpaper_dir, filename)
                if os.path.exists(save_path):
                    continue
                img_data = requests.get(url, timeout=10).content
                with open(save_path, "wb") as f:
                    f.write(img_data)
                self.downloaded.append(save_path)
                print(f"Descargado desde Pexels: {filename}")
        except Exception as e:
            print(f"Error en Pexels: {e}")

    def download_from_picsum(self):
        """Descargar wallpapers desde Lorem Picsum"""
        print("Descargando desde Lorem Picsum ...")
        try:
            for i in range(5):
                url = f"https://picsum.photos/1920/1080"
                filename = f"picsum_{int(time.time())}_{i}.jpg"
                save_path = os.path.join(self.wallpaper_dir, filename)
                if os.path.exists(save_path):
                    continue
                img_data = requests.get(url, timeout=10).content
                with open(save_path, "wb") as f:
                    f.write(img_data)
                self.downloaded.append(save_path)
                print(f"Descargado desde Picsum: {filename}")
        except Exception as e:
            print(f"Error en Picsum: {e}")
    def fetch_all_sources(self):
        """Descargar wallpapers desde todas las fuentes disponibles"""
        print("\n=== Iniciando descarga de wallpapers ===")
        if self.keyword:
            self.download_from_bing()
        self.download_from_unsplash()
        self.download_from_pexels()
        self.download_from_picsum()
        print("=== Descarga finalizada ===\n")


def print_help():
    """Imprimir información de ayuda"""
    help_text = """
Wallpaper Fetcher Script

Uso:
    wallpaper_fetcher.py [DIRECTORIO] [SEARCH_KEYWORD]

Argumentos:
    DIRECTORIO        Directorio donde se guardarán los wallpapers (requerido)
    SEARCH_KEYWORD    Palabra clave para buscar nuevos wallpapers (opcional)

Opciones:
    -h, --help        Mostrar este mensaje de ayuda y salir
    -v, --version     Mostrar información de versión
    -c, --credits     Mostrar créditos y autor
"""
    print(help_text)


def print_version():
    """Imprimir información de versión"""
    print(f"Wallpaper Fetcher v{VERSION}")


def print_credits():
    """Imprimir créditos y autor"""
    credits_text = f"""
Wallpaper Fetcher Script
Version: {VERSION}

Author:  {AUTHOR}
Email:   {EMAIL}
GitHub:  {GITHUB}

License: Open Source
"""
    print(credits_text)


def main():
    # Manejo de flags especiales
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg in ['-h', '--help']:
            print_help()
            sys.exit(0)
        elif arg in ['-v', '--version']:
            print_version()
            sys.exit(0)
        elif arg in ['-c', '--credits']:
            print_credits()
            sys.exit(0)

    if len(sys.argv) < 2:
        print("Error: Falta argumento DIRECTORIO")
        print("Use --help para información de uso")
        sys.exit(1)

    wallpaper_dir = sys.argv[1]

    keyword = None
    if len(sys.argv) >= 3:
        keyword = sys.argv[2]

    print(f"Wallpaper Fetcher v{VERSION}")
    print("=" * 60)

    fetcher = WallpaperFetcher(wallpaper_dir, keyword)

    # Descargar de todas las fuentes
    fetcher.fetch_all_sources()

    print("\nProceso terminado.")
    if fetcher.downloaded:
        print(f"Se descargaron {len(fetcher.downloaded)} nuevos wallpapers en {wallpaper_dir}")
    else:
        print("No se descargaron nuevos wallpapers.")


if __name__ == "__main__":
    main()
