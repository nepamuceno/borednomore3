#!/usr/bin/env python3
import sys
import os
import time

# Add the lib path so we can find our modules
sys.path.append(os.path.abspath("../lib"))
sys.path.append(os.path.abspath("../lib/transitions"))

try:
    from borednomore3_transitions import TRANSITIONS, apply_transition
except ImportError as e:
    print(f"Error: Could not find transition library. {e}")
    sys.exit(1)

# Configuration for the test
WALLPAPER_DIR = "../wallpapers"
RES_W, RES_H = 1920, 1080
TEST_FRAMES = 10
TEST_SPEED = 0.005

def dummy_set_wallpaper(img_path):
    # This mimics the real wallpaper setter but for testing
    # You can change this to your actual setter (e.g., pcmanfm-qt)
    os.system(f"pcmanfm-qt -w {img_path}")

def run_benchmark():
    # Get list of wallpapers
    images = [os.path.join(WALLPAPER_DIR, f) for f in os.listdir(WALLPAPER_DIR) if f.endswith(('.jpg', '.png'))]
    if len(images) < 2:
        print("Need at least 2 wallpapers in ../wallpapers to test.")
        return

    print(f"Starting Benchmark of {len(TRANSITIONS)} transitions...")
    
    # Sort IDs so we go in order
    sorted_ids = sorted(TRANSITIONS.keys())

    for i in range(len(sorted_ids)):
        tid = sorted_ids[i]
        old_img = images[i % len(images)]
        new_img = images[(i + 1) % len(images)]
        
        name = TRANSITIONS.get(tid, "Unknown")
        print(f"Testing ID #{tid}: {name}")
        
        try:
            apply_transition(
                old_img, new_img, tid, RES_W, RES_H, 
                TEST_FRAMES, TEST_SPEED, dummy_set_wallpaper, lambda: False
            )
        except Exception as e:
            print(f"FAILED on ID {tid}: {e}")
        
        time.sleep(0.5) # Short pause between transitions

if __name__ == "__main__":
    run_benchmark()
