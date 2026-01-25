import os
import sys
import time

# Ensure the package is findable
sys.path.append(os.getcwd())

from bnm3_transitions.manager import TransitionManager

def run_test():
    manager = TransitionManager()
    
    # 1. Scan the Catalog (For GUI population)
    catalog = manager.scan_transitions()
    print("--- TRANSITION CATALOG ---")
    for cat_id, meta in catalog.items():
        print(f"Loaded: {meta['category_name']} (v{meta['version']})")

    # 2. Test Symmetry (The Way In and The Way Out)
    print("\n--- SYMMETRY TEST: FADE ---")
    fade_engine = manager.get_transition_instance("fades")
    if fade_engine:
        # Way In
        fade_engine.run(widget="GUI_Button", duration=0.5, direction="in")
        print("... Widget is visible ...")
        time.sleep(0.5)
        # Way Out
        fade_engine.run(widget="GUI_Button", duration=0.5, direction="out")

    print("\n--- SYMMETRY TEST: SLIDE ---")
    slide_engine = manager.get_transition_instance("slides")
    if slide_engine:
        slide_engine.run(widget="GUI_Panel", duration=0.5, direction="in", side="left")
        print("... Widget is in position ...")
        time.sleep(0.5)
        slide_engine.run(widget="GUI_Panel", duration=0.5, direction="out", side="left")

if __name__ == "__main__":
    run_test()
