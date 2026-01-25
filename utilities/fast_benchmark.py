#!/usr/bin/env python3
import sys
import os
import time
import random

# Add library paths
sys.path.append(os.path.abspath("../lib"))
sys.path.append(os.path.abspath("../lib/transitions"))

try:
    from borednomore3_transitions import TRANSITIONS, apply_transition
except ImportError:
    print("Error: Library not found.")
    sys.exit(1)

# Category ranges
CATEGORIES = {
    "Core (Crossfade/Fades)": [1, 2, 3, 4],
    "Movement (Slides/Pushes)": [5, 6, 7, 8, 41, 42, 43, 44],
    "Cinematic (Whip Pans + Blur)": [37, 38, 39, 40],
    "Geometric (Linear Wipes)": list(range(100, 461)),
    "Masks (Radial/Organic)": list(range(461, 661)),
    "Tiling (Blinds/Checkers)": list(range(661, 801)),
    "Digital (Glitch/Noise)": list(range(801, 1001))
}

WALLPAPER_DIR = "../wallpapers"
images = [os.path.join(WALLPAPER_DIR, f) for f in os.listdir(WALLPAPER_DIR) if f.endswith(('.jpg', '.png'))]

def dummy_set(img):
    os.system(f"pcmanfm-qt -w {img}")

print("--- STARTING FAST CATEGORY TEST ---")
for cat_name, ids in CATEGORIES.items():
    tid = random.choice(ids)
    name = TRANSITIONS.get(tid, "Unknown")
    
    print(f"[*] Testing {cat_name} -> ID #{tid}: {name}")
    
    old_img = random.choice(images)
    new_img = random.choice(images)
    
    try:
        apply_transition(old_img, new_img, tid, 1920, 1080, 15, 0.01, dummy_set, lambda: False)
        print(f"    [OK] Finished {name}")
    except Exception as e:
        print(f"    [FAIL] ID {tid}: {e}")
    
    time.sleep(1)

print("\n--- ALL CATEGORIES VERIFIED ---")
