"""
borednomore3 Transition Engine - Core Module
Handles transition coordination and imports

Author: Nepamuceno
Version: 0.7.0
"""

import os
import random
from pathlib import Path
import cv2
import numpy as np

VERSION = "0.7.0"
AUTHOR = "Nepamuceno"

# Import transition categories
try:
    from borednomore3_transitions_basic import BasicTransitions
    from borednomore3_transitions_geometric import GeometricTransitions
    from borednomore3_transitions_effects import EffectTransitions
except ImportError as e:
    print(f"Error importing transition modules: {e}")
    print("Make sure all transition modules are in the same directory")
    raise

# === CURATED TRANSITIONS LIBRARY - 73 Transitions ===
CURATED_TRANSITIONS = {
    # SLIDE (1-8)
    1: {"name": "Slide Left", "short_desc": "Slides left", "long_desc": "Current exits left, new enters from right", "family": "slide", "direction": "left", "version": VERSION, "author": AUTHOR},
    2: {"name": "Slide Right", "short_desc": "Slides right", "long_desc": "Current exits right, new enters from left", "family": "slide", "direction": "right", "version": VERSION, "author": AUTHOR},
    3: {"name": "Slide Up", "short_desc": "Slides up", "long_desc": "Current exits up, new enters from bottom", "family": "slide", "direction": "up", "version": VERSION, "author": AUTHOR},
    4: {"name": "Slide Down", "short_desc": "Slides down", "long_desc": "Current exits down, new enters from top", "family": "slide", "direction": "down", "version": VERSION, "author": AUTHOR},
    5: {"name": "Slide Top-Left", "short_desc": "Diagonal slide to top-left", "long_desc": "Current exits to top-left corner", "family": "slide", "direction": "top-left", "version": VERSION, "author": AUTHOR},
    6: {"name": "Slide Top-Right", "short_desc": "Diagonal slide to top-right", "long_desc": "Current exits to top-right corner", "family": "slide", "direction": "top-right", "version": VERSION, "author": AUTHOR},
    7: {"name": "Slide Bottom-Left", "short_desc": "Diagonal slide to bottom-left", "long_desc": "Current exits to bottom-left corner", "family": "slide", "direction": "bottom-left", "version": VERSION, "author": AUTHOR},
    8: {"name": "Slide Bottom-Right", "short_desc": "Diagonal slide to bottom-right", "long_desc": "Current exits to bottom-right corner", "family": "slide", "direction": "bottom-right", "version": VERSION, "author": AUTHOR},
    
    # ROTATION (9-12)
    9: {"name": "Rotate CW 90°", "short_desc": "90° clockwise rotation", "long_desc": "Rotates 90° clockwise", "family": "rotate", "angle": 90, "direction": "cw", "version": VERSION, "author": AUTHOR},
    10: {"name": "Rotate CCW 90°", "short_desc": "90° counter-clockwise", "long_desc": "Rotates 90° counter-clockwise", "family": "rotate", "angle": 90, "direction": "ccw", "version": VERSION, "author": AUTHOR},
    11: {"name": "Rotate CW 180°", "short_desc": "180° clockwise spin", "long_desc": "Full 180° clockwise rotation", "family": "rotate", "angle": 180, "direction": "cw", "version": VERSION, "author": AUTHOR},
    12: {"name": "Rotate CCW 180°", "short_desc": "180° counter-clockwise", "long_desc": "Full 180° counter-clockwise rotation", "family": "rotate", "angle": 180, "direction": "ccw", "version": VERSION, "author": AUTHOR},
    
    # ZOOM (13-15)
    13: {"name": "Zoom Out", "short_desc": "Zooms out revealing new", "long_desc": "Current zooms out, new appears behind", "family": "zoom", "direction": "out", "version": VERSION, "author": AUTHOR},
    14: {"name": "Zoom In", "short_desc": "New zooms in from center", "long_desc": "New wallpaper zooms in covering current", "family": "zoom", "direction": "in", "version": VERSION, "author": AUTHOR},
    15: {"name": "Zoom Pulse", "short_desc": "Pulsing zoom effect", "long_desc": "Wallpaper pulses during transition", "family": "zoom", "direction": "pulse", "version": VERSION, "author": AUTHOR},
    
    # FADE (16-18)
    16: {"name": "Fade Cross", "short_desc": "Classic cross-fade", "long_desc": "Smooth cross-dissolve transition", "family": "fade", "direction": "cross", "version": VERSION, "author": AUTHOR},
    17: {"name": "Fade to Black", "short_desc": "Fades through black", "long_desc": "Fades to black then new fades in", "family": "fade", "direction": "black", "version": VERSION, "author": AUTHOR},
    18: {"name": "Fade to White", "short_desc": "Fades through white", "long_desc": "Fades to white then new fades in", "family": "fade", "direction": "white", "version": VERSION, "author": AUTHOR},
    
    # WIPE (19-22)
    19: {"name": "Wipe Left", "short_desc": "Wipes from right to left", "long_desc": "New wipes in from right edge", "family": "wipe", "direction": "left", "version": VERSION, "author": AUTHOR},
    20: {"name": "Wipe Right", "short_desc": "Wipes from left to right", "long_desc": "New wipes in from left edge", "family": "wipe", "direction": "right", "version": VERSION, "author": AUTHOR},
    21: {"name": "Wipe Up", "short_desc": "Wipes from bottom to top", "long_desc": "New wipes in from bottom edge", "family": "wipe", "direction": "up", "version": VERSION, "author": AUTHOR},
    22: {"name": "Wipe Down", "short_desc": "Wipes from top to bottom", "long_desc": "New wipes in from top edge", "family": "wipe", "direction": "down", "version": VERSION, "author": AUTHOR},
    
    # PUSH (23-26) - Same as slide
    23: {"name": "Push Left", "short_desc": "Pushes current left", "long_desc": "New pushes current out to left", "family": "slide", "direction": "left", "version": VERSION, "author": AUTHOR},
    24: {"name": "Push Right", "short_desc": "Pushes current right", "long_desc": "New pushes current out to right", "family": "slide", "direction": "right", "version": VERSION, "author": AUTHOR},
    25: {"name": "Push Up", "short_desc": "Pushes current up", "long_desc": "New pushes current out to top", "family": "slide", "direction": "up", "version": VERSION, "author": AUTHOR},
    26: {"name": "Push Down", "short_desc": "Pushes current down", "long_desc": "New pushes current out to bottom", "family": "slide", "direction": "down", "version": VERSION, "author": AUTHOR},
    
    # Continue with rest... (27-73 defined in imports)
}

# SPLIT (27-28)
CURATED_TRANSITIONS[27] = {"name": "Split Horizontal", "short_desc": "Splits horizontally", "long_desc": "Current splits horizontally revealing new", "family": "split", "direction": "horizontal", "version": VERSION, "author": AUTHOR}
CURATED_TRANSITIONS[28] = {"name": "Split Vertical", "short_desc": "Splits vertically", "long_desc": "Current splits vertically revealing new", "family": "split", "direction": "vertical", "version": VERSION, "author": AUTHOR}

# BOX (29-30)
CURATED_TRANSITIONS[29] = {"name": "Box In", "short_desc": "Box grows from center", "long_desc": "New appears in expanding box", "family": "box", "direction": "in", "version": VERSION, "author": AUTHOR}
CURATED_TRANSITIONS[30] = {"name": "Box Out", "short_desc": "Box shrinks to center", "long_desc": "Current shrinks in box revealing new", "family": "box", "direction": "out", "version": VERSION, "author": AUTHOR}

# CIRCLE (31-32)
CURATED_TRANSITIONS[31] = {"name": "Circle In", "short_desc": "Circle grows from center", "long_desc": "New appears in expanding circle", "family": "circle", "direction": "in", "version": VERSION, "author": AUTHOR}
CURATED_TRANSITIONS[32] = {"name": "Circle Out", "short_desc": "Circle shrinks to center", "long_desc": "Current visible in shrinking circle", "family": "circle", "direction": "out", "version": VERSION, "author": AUTHOR}

# PIXELATE (33)
CURATED_TRANSITIONS[33] = {"name": "Pixelate", "short_desc": "Pixelation dissolve", "long_desc": "Current pixelates to new", "family": "pixelate", "direction": "dissolve", "version": VERSION, "author": AUTHOR}

# BLUR (34)
CURATED_TRANSITIONS[34] = {"name": "Blur Transition", "short_desc": "Blurs through transition", "long_desc": "Current blurs out, new blurs in", "family": "blur", "direction": "cross", "version": VERSION, "author": AUTHOR}

# FLIP (35-36)
CURATED_TRANSITIONS[35] = {"name": "Flip Horizontal", "short_desc": "Flips horizontally", "long_desc": "Wallpaper flips like a card horizontally", "family": "flip", "direction": "horizontal", "version": VERSION, "author": AUTHOR}
CURATED_TRANSITIONS[36] = {"name": "Flip Vertical", "short_desc": "Flips vertically", "long_desc": "Wallpaper flips like a card vertically", "family": "flip", "direction": "vertical", "version": VERSION, "author": AUTHOR}

# DOOR (37-38)
CURATED_TRANSITIONS[37] = {"name": "Door Left", "short_desc": "Door swings left", "long_desc": "Current swings left like a door", "family": "door", "direction": "left", "version": VERSION, "author": AUTHOR}
CURATED_TRANSITIONS[38] = {"name": "Door Right", "short_desc": "Door swings right", "long_desc": "Current swings right like a door", "family": "door", "direction": "right", "version": VERSION, "author": AUTHOR}

# BARN (39-40)
CURATED_TRANSITIONS[39] = {"name": "Barn Doors H", "short_desc": "Barn doors horizontal", "long_desc": "Splits and opens like barn doors", "family": "barn", "direction": "horizontal", "version": VERSION, "author": AUTHOR}
CURATED_TRANSITIONS[40] = {"name": "Barn Doors V", "short_desc": "Barn doors vertical", "long_desc": "Splits and opens like barn doors vertically", "family": "barn", "direction": "vertical", "version": VERSION, "author": AUTHOR}

# PEEL (41-44)
CURATED_TRANSITIONS[41] = {"name": "Peel Top-Left", "short_desc": "Peels from top-left", "long_desc": "Current peels from top-left corner", "family": "peel", "direction": "top-left", "version": VERSION, "author": AUTHOR}
CURATED_TRANSITIONS[42] = {"name": "Peel Top-Right", "short_desc": "Peels from top-right", "long_desc": "Current peels from top-right corner", "family": "peel", "direction": "top-right", "version": VERSION, "author": AUTHOR}
CURATED_TRANSITIONS[43] = {"name": "Peel Bottom-Left", "short_desc": "Peels from bottom-left", "long_desc": "Current peels from bottom-left corner", "family": "peel", "direction": "bottom-left", "version": VERSION, "author": AUTHOR}
CURATED_TRANSITIONS[44] = {"name": "Peel Bottom-Right", "short_desc": "Peels from bottom-right", "long_desc": "Current peels from bottom-right corner", "family": "peel", "direction": "bottom-right", "version": VERSION, "author": AUTHOR}

# WAVE (45-46)
CURATED_TRANSITIONS[45] = {"name": "Wave Horizontal", "short_desc": "Wave effect horizontal", "long_desc": "Waves horizontally during transition", "family": "wave", "direction": "horizontal", "version": VERSION, "author": AUTHOR}
CURATED_TRANSITIONS[46] = {"name": "Wave Vertical", "short_desc": "Wave effect vertical", "long_desc": "Waves vertically during transition", "family": "wave", "direction": "vertical", "version": VERSION, "author": AUTHOR}

# RADIAL (47-48)
CURATED_TRANSITIONS[47] = {"name": "Radial Wipe CW", "short_desc": "Radial wipe clockwise", "long_desc": "New reveals in clockwise radial wipe", "family": "radial", "direction": "cw", "version": VERSION, "author": AUTHOR}
CURATED_TRANSITIONS[48] = {"name": "Radial Wipe CCW", "short_desc": "Radial wipe counter-clockwise", "long_desc": "New reveals in counter-clockwise radial wipe", "family": "radial", "direction": "ccw", "version": VERSION, "author": AUTHOR}

# CHECKERBOARD (49-50)
CURATED_TRANSITIONS[49] = {"name": "Checkerboard", "short_desc": "Checkerboard reveal", "long_desc": "Reveals in checkerboard pattern", "family": "checkerboard", "direction": "normal", "version": VERSION, "author": AUTHOR}
CURATED_TRANSITIONS[50] = {"name": "Checkerboard Inverse", "short_desc": "Inverse checkerboard", "long_desc": "Reveals in inverse checkerboard", "family": "checkerboard", "direction": "inverse", "version": VERSION, "author": AUTHOR}

# CUBE (51-54)
CURATED_TRANSITIONS[51] = {"name": "Cube Rotate Left", "short_desc": "3D cube rotates left", "long_desc": "Wallpapers on cube faces rotating left", "family": "cube", "direction": "left", "version": VERSION, "author": AUTHOR}
CURATED_TRANSITIONS[52] = {"name": "Cube Rotate Right", "short_desc": "3D cube rotates right", "long_desc": "Wallpapers on cube faces rotating right", "family": "cube", "direction": "right", "version": VERSION, "author": AUTHOR}
CURATED_TRANSITIONS[53] = {"name": "Cube Rotate Up", "short_desc": "3D cube rotates up", "long_desc": "Wallpapers on cube faces rotating up", "family": "cube", "direction": "up", "version": VERSION, "author": AUTHOR}
CURATED_TRANSITIONS[54] = {"name": "Cube Rotate Down", "short_desc": "3D cube rotates down", "long_desc": "Wallpapers on cube faces rotating down", "family": "cube", "direction": "down", "version": VERSION, "author": AUTHOR}

# GLITCH (55, 57)
CURATED_TRANSITIONS[55] = {"name": "Glitch", "short_desc": "Digital glitch effect", "long_desc": "Glitchy digital transition", "family": "glitch", "direction": "normal", "version": VERSION, "author": AUTHOR}
CURATED_TRANSITIONS[57] = {"name": "RGB Split", "short_desc": "RGB channel split", "long_desc": "Color channels separate and recombine", "family": "glitch", "direction": "rgb-split", "version": VERSION, "author": AUTHOR}

# NOISE (56)
CURATED_TRANSITIONS[56] = {"name": "Static Noise", "short_desc": "TV static noise", "long_desc": "Transitions through static noise", "family": "noise", "direction": "static", "version": VERSION, "author": AUTHOR}

# BLINDS (58-59)
CURATED_TRANSITIONS[58] = {"name": "Blinds Horizontal", "short_desc": "Venetian blinds horizontal", "long_desc": "Reveals like horizontal blinds opening", "family": "blinds", "direction": "horizontal", "version": VERSION, "author": AUTHOR}
CURATED_TRANSITIONS[59] = {"name": "Blinds Vertical", "short_desc": "Venetian blinds vertical", "long_desc": "Reveals like vertical blinds opening", "family": "blinds", "direction": "vertical", "version": VERSION, "author": AUTHOR}

# MOSAIC (60)
CURATED_TRANSITIONS[60] = {"name": "Mosaic", "short_desc": "Mosaic tile effect", "long_desc": "Breaks into mosaic tiles", "family": "mosaic", "direction": "scatter", "version": VERSION, "author": AUTHOR}

# RIPPLE (61)
CURATED_TRANSITIONS[61] = {"name": "Ripple", "short_desc": "Water ripple effect", "long_desc": "Transitions with ripple distortion", "family": "ripple", "direction": "center", "version": VERSION, "author": AUTHOR}

# SWIRL (62-63)
CURATED_TRANSITIONS[62] = {"name": "Swirl CW", "short_desc": "Swirl clockwise", "long_desc": "Current swirls out clockwise", "family": "swirl", "direction": "cw", "version": VERSION, "author": AUTHOR}
CURATED_TRANSITIONS[63] = {"name": "Swirl CCW", "short_desc": "Swirl counter-clockwise", "long_desc": "Current swirls out counter-clockwise", "family": "swirl", "direction": "ccw", "version": VERSION, "author": AUTHOR}

# DIAMOND (64-65)
CURATED_TRANSITIONS[64] = {"name": "Diamond Wipe In", "short_desc": "Diamond shape grows", "long_desc": "New reveals in growing diamond shape", "family": "diamond", "direction": "in", "version": VERSION, "author": AUTHOR}
CURATED_TRANSITIONS[65] = {"name": "Diamond Wipe Out", "short_desc": "Diamond shape shrinks", "long_desc": "Current visible in shrinking diamond", "family": "diamond", "direction": "out", "version": VERSION, "author": AUTHOR}

# RANDOM BLOCKS (69)
CURATED_TRANSITIONS[69] = {"name": "Random Blocks", "short_desc": "Random block reveals", "long_desc": "Reveals in random rectangular blocks", "family": "random-blocks", "direction": "normal", "version": VERSION, "author": AUTHOR}

# DRIFT (70-73)
CURATED_TRANSITIONS[70] = {"name": "Drift Left", "short_desc": "Drifts and fades left", "long_desc": "Fades while drifting left", "family": "drift", "direction": "left", "version": VERSION, "author": AUTHOR}
CURATED_TRANSITIONS[71] = {"name": "Drift Right", "short_desc": "Drifts and fades right", "long_desc": "Fades while drifting right", "family": "drift", "direction": "right", "version": VERSION, "author": AUTHOR}
CURATED_TRANSITIONS[72] = {"name": "Drift Up", "short_desc": "Drifts and fades up", "long_desc": "Fades while drifting up", "family": "drift", "direction": "up", "version": VERSION, "author": AUTHOR}
CURATED_TRANSITIONS[73] = {"name": "Drift Down", "short_desc": "Drifts and fades down", "long_desc": "Fades while drifting down", "family": "drift", "direction": "down", "version": VERSION, "author": AUTHOR}


def get_curated_transitions():
    """Return the curated transitions dictionary"""
    return CURATED_TRANSITIONS


class TransitionEngine:
    """Main transition engine - delegates to specialized generators"""
    
    def __init__(self, screen_width, screen_height, debug=False):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.debug = debug
        self.tmp_dir = "/tmp/bnm3_frames"
        Path(self.tmp_dir).mkdir(parents=True, exist_ok=True)
        
        # Initialize transition generators
        self.basic = BasicTransitions(screen_width, screen_height, debug, self.tmp_dir)
        self.geometric = GeometricTransitions(screen_width, screen_height, debug, self.tmp_dir)
        self.effects = EffectTransitions(screen_width, screen_height, debug, self.tmp_dir)
    
    def debug_print(self, message):
        if self.debug:
            print(f"[TRANSITION DEBUG] {message}")
    
    def prepare_image(self, img_path):
        img = cv2.imread(str(img_path))
        if img is None:
            raise ValueError(f"Cannot load image {img_path}")
        return cv2.resize(img, (self.screen_width, self.screen_height), interpolation=cv2.INTER_LANCZOS4)
    
    def generate_transition_frames(self, old_img, new_img, trans_id, total_frames):
        """Main transition generator - routes to appropriate handler"""
        if trans_id not in CURATED_TRANSITIONS:
            self.debug_print(f"Invalid transition {trans_id}, using fade")
            trans_id = 16
        
        transition = CURATED_TRANSITIONS[trans_id]
        family = transition['family']
        direction = transition.get('direction', '')
        
        self.debug_print(f"Generating {total_frames} frames for family '{family}'")
        
        old_prepared = self.prepare_image(old_img)
        new_prepared = self.prepare_image(new_img)
        
        try:
            # Route to appropriate generator
            if family in ["slide", "rotate", "zoom", "fade", "wipe"]:
                return self.basic.generate(family, old_prepared, new_prepared, direction, 
                                          total_frames, transition.get('angle', 90))
            elif family in ["split", "box", "circle", "radial", "checkerboard", 
                           "cube", "diamond"]:
                return self.geometric.generate(family, old_prepared, new_prepared, 
                                              direction, total_frames)
            elif family in ["pixelate", "blur", "flip", "door", "barn", "peel", 
                           "wave", "glitch", "noise", "drift", "blinds", "mosaic", 
                           "ripple", "swirl", "random-blocks"]:
                return self.effects.generate(family, old_prepared, new_prepared, 
                                            direction, total_frames)
            else:
                # Fallback to fade
                return self.basic.generate("fade", old_prepared, new_prepared, 
                                          "cross", total_frames, 0)
        except Exception as e:
            self.debug_print(f"Error generating transition: {e}")
            return self.basic.generate("fade", old_prepared, new_prepared, 
                                      "cross", total_frames, 0)


def print_transition_library():
    """Print all transitions"""
    print("\n" + "="*80)
    print("CURATED TRANSITION LIBRARY")
    print("="*80)
    
    families = {}
    for tid, trans in CURATED_TRANSITIONS.items():
        family = trans['family']
        if family not in families:
            families[family] = []
        families[family].append((tid, trans))
    
    for family, transitions in sorted(families.items()):
        print(f"\n### {family.upper()} ###")
        for tid, trans in sorted(transitions):
            print(f"  [{tid:3d}] {trans['name']}: {trans['short_desc']}")
    
    print(f"\n{'='*80}")
    print(f"Total: {len(CURATED_TRANSITIONS)} transitions")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    print_transition_library()
