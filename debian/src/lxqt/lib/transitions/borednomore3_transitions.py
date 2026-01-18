"""
borednomore3 Transition Engine
Handles all transition generation and playback using OpenCV

Author: Nepamuceno
Version: 0.7.0
"""

import os
import time
import random
from pathlib import Path
import cv2
import numpy as np

VERSION = "0.7.0"
AUTHOR = "Nepamuceno"

# --- CURATED TRANSITIONS LIBRARY ---
# Only visually impactful transitions (perceptible differences)
CURATED_TRANSITIONS = {
    # === SLIDE TRANSITIONS (Horizontal) ===
    1: {
        "name": "Slide Left",
        "short_desc": "Slides horizontally to the left",
        "long_desc": "Current wallpaper slides out left while new one enters from right",
        "family": "slide",
        "direction": "left",
        "version": VERSION,
        "author": AUTHOR
    },
    2: {
        "name": "Slide Right",
        "short_desc": "Slides horizontally to the right",
        "long_desc": "Current wallpaper slides out right while new one enters from left",
        "family": "slide",
        "direction": "right",
        "version": VERSION,
        "author": AUTHOR
    },
    
    # === SLIDE TRANSITIONS (Vertical) ===
    3: {
        "name": "Slide Up",
        "short_desc": "Slides vertically upward",
        "long_desc": "Current wallpaper slides out up while new one enters from bottom",
        "family": "slide",
        "direction": "up",
        "version": VERSION,
        "author": AUTHOR
    },
    4: {
        "name": "Slide Down",
        "short_desc": "Slides vertically downward",
        "long_desc": "Current wallpaper slides out down while new one enters from top",
        "family": "slide",
        "direction": "down",
        "version": VERSION,
        "author": AUTHOR
    },
    
    # === SLIDE TRANSITIONS (Diagonal) ===
    5: {
        "name": "Slide Top-Left",
        "short_desc": "Slides diagonally to top-left corner",
        "long_desc": "Current wallpaper exits to top-left while new enters from bottom-right",
        "family": "slide",
        "direction": "top-left",
        "version": VERSION,
        "author": AUTHOR
    },
    6: {
        "name": "Slide Top-Right",
        "short_desc": "Slides diagonally to top-right corner",
        "long_desc": "Current wallpaper exits to top-right while new enters from bottom-left",
        "family": "slide",
        "direction": "top-right",
        "version": VERSION,
        "author": AUTHOR
    },
    7: {
        "name": "Slide Bottom-Left",
        "short_desc": "Slides diagonally to bottom-left corner",
        "long_desc": "Current wallpaper exits to bottom-left while new enters from top-right",
        "family": "slide",
        "direction": "bottom-left",
        "version": VERSION,
        "author": AUTHOR
    },
    8: {
        "name": "Slide Bottom-Right",
        "short_desc": "Slides diagonally to bottom-right corner",
        "long_desc": "Current wallpaper exits to bottom-right while new enters from top-left",
        "family": "slide",
        "direction": "bottom-right",
        "version": VERSION,
        "author": AUTHOR
    },
    
    # === ROTATION TRANSITIONS ===
    9: {
        "name": "Rotate Clockwise 90°",
        "short_desc": "90° clockwise rotation",
        "long_desc": "Current wallpaper rotates 90° clockwise revealing new wallpaper",
        "family": "rotate",
        "angle": 90,
        "direction": "cw",
        "version": VERSION,
        "author": AUTHOR
    },
    10: {
        "name": "Rotate Counter-Clockwise 90°",
        "short_desc": "90° counter-clockwise rotation",
        "long_desc": "Current wallpaper rotates 90° counter-clockwise revealing new wallpaper",
        "family": "rotate",
        "angle": 90,
        "direction": "ccw",
        "version": VERSION,
        "author": AUTHOR
    },
    11: {
        "name": "Rotate Clockwise 180°",
        "short_desc": "180° clockwise spin",
        "long_desc": "Current wallpaper spins 180° clockwise to reveal new wallpaper",
        "family": "rotate",
        "angle": 180,
        "direction": "cw",
        "version": VERSION,
        "author": AUTHOR
    },
    12: {
        "name": "Rotate Counter-Clockwise 180°",
        "short_desc": "180° counter-clockwise spin",
        "long_desc": "Current wallpaper spins 180° counter-clockwise to reveal new wallpaper",
        "family": "rotate",
        "angle": 180,
        "direction": "ccw",
        "version": VERSION,
        "author": AUTHOR
    },
    
    # === ZOOM TRANSITIONS ===
    13: {
        "name": "Zoom Out",
        "short_desc": "Zooms out to reveal new wallpaper",
        "long_desc": "Current wallpaper zooms out from center while new one appears behind",
        "family": "zoom",
        "direction": "out",
        "version": VERSION,
        "author": AUTHOR
    },
    14: {
        "name": "Zoom In",
        "short_desc": "New wallpaper zooms in from center",
        "long_desc": "New wallpaper zooms in from center covering current wallpaper",
        "family": "zoom",
        "direction": "in",
        "version": VERSION,
        "author": AUTHOR
    },
    15: {
        "name": "Zoom Pulse",
        "short_desc": "Pulsing zoom effect",
        "long_desc": "Current wallpaper pulses with zoom effect transitioning to new one",
        "family": "zoom",
        "direction": "pulse",
        "version": VERSION,
        "author": AUTHOR
    },
    
    # === FADE TRANSITIONS ===
    16: {
        "name": "Fade Cross-Dissolve",
        "short_desc": "Classic cross-fade transition",
        "long_desc": "Current wallpaper fades out while new one fades in simultaneously",
        "family": "fade",
        "direction": "cross",
        "version": VERSION,
        "author": AUTHOR
    },
    17: {
        "name": "Fade to Black",
        "short_desc": "Fades through black screen",
        "long_desc": "Current wallpaper fades to black, then new one fades in from black",
        "family": "fade",
        "direction": "black",
        "version": VERSION,
        "author": AUTHOR
    },
    18: {
        "name": "Fade to White",
        "short_desc": "Fades through white screen",
        "long_desc": "Current wallpaper fades to white, then new one fades in from white",
        "family": "fade",
        "direction": "white",
        "version": VERSION,
        "author": AUTHOR
    },
    
    # === WIPE TRANSITIONS ===
    19: {
        "name": "Wipe Left",
        "short_desc": "Wipes from right to left",
        "long_desc": "New wallpaper wipes in from right edge pushing current one left",
        "family": "wipe",
        "direction": "left",
        "version": VERSION,
        "author": AUTHOR
    },
    20: {
        "name": "Wipe Right",
        "short_desc": "Wipes from left to right",
        "long_desc": "New wallpaper wipes in from left edge pushing current one right",
        "family": "wipe",
        "direction": "right",
        "version": VERSION,
        "author": AUTHOR
    },
    21: {
        "name": "Wipe Up",
        "short_desc": "Wipes from bottom to top",
        "long_desc": "New wallpaper wipes in from bottom edge pushing current one up",
        "family": "wipe",
        "direction": "up",
        "version": VERSION,
        "author": AUTHOR
    },
    22: {
        "name": "Wipe Down",
        "short_desc": "Wipes from top to bottom",
        "long_desc": "New wallpaper wipes in from top edge pushing current one down",
        "family": "wipe",
        "direction": "down",
        "version": VERSION,
        "author": AUTHOR
    },
    
    # === PUSH TRANSITIONS ===
    23: {
        "name": "Push Left",
        "short_desc": "Pushes current wallpaper to the left",
        "long_desc": "New wallpaper pushes current one out to the left",
        "family": "push",
        "direction": "left",
        "version": VERSION,
        "author": AUTHOR
    },
    24: {
        "name": "Push Right",
        "short_desc": "Pushes current wallpaper to the right",
        "long_desc": "New wallpaper pushes current one out to the right",
        "family": "push",
        "direction": "right",
        "version": VERSION,
        "author": AUTHOR
    },
    25: {
        "name": "Push Up",
        "short_desc": "Pushes current wallpaper upward",
        "long_desc": "New wallpaper pushes current one out to the top",
        "family": "push",
        "direction": "up",
        "version": VERSION,
        "author": AUTHOR
    },
    26: {
        "name": "Push Down",
        "short_desc": "Pushes current wallpaper downward",
        "long_desc": "New wallpaper pushes current one out to the bottom",
        "family": "push",
        "direction": "down",
        "version": VERSION,
        "author": AUTHOR
    },
    
    # === SPLIT TRANSITIONS ===
    27: {
        "name": "Split Horizontal",
        "short_desc": "Splits horizontally from center",
        "long_desc": "Current wallpaper splits horizontally revealing new one in center",
        "family": "split",
        "direction": "horizontal",
        "version": VERSION,
        "author": AUTHOR
    },
    28: {
        "name": "Split Vertical",
        "short_desc": "Splits vertically from center",
        "long_desc": "Current wallpaper splits vertically revealing new one in center",
        "family": "split",
        "direction": "vertical",
        "version": VERSION,
        "author": AUTHOR
    },
    
    # === BOX TRANSITIONS ===
    29: {
        "name": "Box In",
        "short_desc": "Box grows from center outward",
        "long_desc": "New wallpaper appears in expanding box from center",
        "family": "box",
        "direction": "in",
        "version": VERSION,
        "author": AUTHOR
    },
    30: {
        "name": "Box Out",
        "short_desc": "Box shrinks to center",
        "long_desc": "Current wallpaper shrinks in box to center revealing new one",
        "family": "box",
        "direction": "out",
        "version": VERSION,
        "author": AUTHOR
    },
    
    # === CIRCLE TRANSITIONS ===
    31: {
        "name": "Circle In",
        "short_desc": "Circle grows from center",
        "long_desc": "New wallpaper appears in expanding circle from center",
        "family": "circle",
        "direction": "in",
        "version": VERSION,
        "author": AUTHOR
    },
    32: {
        "name": "Circle Out",
        "short_desc": "Circle shrinks to center",
        "long_desc": "Current wallpaper visible only in shrinking circle revealing new one",
        "family": "circle",
        "direction": "out",
        "version": VERSION,
        "author": AUTHOR
    },
    
    # === PIXELATE TRANSITIONS ===
    33: {
        "name": "Pixelate Dissolve",
        "short_desc": "Dissolves through pixelation",
        "long_desc": "Current wallpaper pixelates and dissolves to new one",
        "family": "pixelate",
        "direction": "dissolve",
        "version": VERSION,
        "author": AUTHOR
    },
    
    # === BLUR TRANSITIONS ===
    34: {
        "name": "Blur Transition",
        "short_desc": "Blurs through transition",
        "long_desc": "Current wallpaper blurs out while new one blurs in",
        "family": "blur",
        "direction": "cross",
        "version": VERSION,
        "author": AUTHOR
    },
    
    # === FLIP TRANSITIONS ===
    35: {
        "name": "Flip Horizontal",
        "short_desc": "Flips horizontally like a card",
        "long_desc": "Wallpaper flips horizontally revealing new one on back",
        "family": "flip",
        "direction": "horizontal",
        "version": VERSION,
        "author": AUTHOR
    },
    36: {
        "name": "Flip Vertical",
        "short_desc": "Flips vertically like a card",
        "long_desc": "Wallpaper flips vertically revealing new one on back",
        "family": "flip",
        "direction": "vertical",
        "version": VERSION,
        "author": AUTHOR
    },
    
    # === DOOR TRANSITIONS ===
    37: {
        "name": "Door Swing Left",
        "short_desc": "Swings open like a door to the left",
        "long_desc": "Current wallpaper swings left like a door revealing new one",
        "family": "door",
        "direction": "left",
        "version": VERSION,
        "author": AUTHOR
    },
    38: {
        "name": "Door Swing Right",
        "short_desc": "Swings open like a door to the right",
        "long_desc": "Current wallpaper swings right like a door revealing new one",
        "family": "door",
        "direction": "right",
        "version": VERSION,
        "author": AUTHOR
    },
    
    # === BARN DOOR TRANSITIONS ===
    39: {
        "name": "Barn Doors Horizontal",
        "short_desc": "Opens like barn doors horizontally",
        "long_desc": "Current wallpaper splits in middle and opens like barn doors",
        "family": "barn",
        "direction": "horizontal",
        "version": VERSION,
        "author": AUTHOR
    },
    40: {
        "name": "Barn Doors Vertical",
        "short_desc": "Opens like barn doors vertically",
        "long_desc": "Current wallpaper splits in middle and opens like barn doors vertically",
        "family": "barn",
        "direction": "vertical",
        "version": VERSION,
        "author": AUTHOR
    },
    
    # === CORNER TRANSITIONS ===
    41: {
        "name": "Corner Peel Top-Left",
        "short_desc": "Peels from top-left corner",
        "long_desc": "Current wallpaper peels from top-left corner revealing new one",
        "family": "peel",
        "direction": "top-left",
        "version": VERSION,
        "author": AUTHOR
    },
    42: {
        "name": "Corner Peel Top-Right",
        "short_desc": "Peels from top-right corner",
        "long_desc": "Current wallpaper peels from top-right corner revealing new one",
        "family": "peel",
        "direction": "top-right",
        "version": VERSION,
        "author": AUTHOR
    },
    43: {
        "name": "Corner Peel Bottom-Left",
        "short_desc": "Peels from bottom-left corner",
        "long_desc": "Current wallpaper peels from bottom-left corner revealing new one",
        "family": "peel",
        "direction": "bottom-left",
        "version": VERSION,
        "author": AUTHOR
    },
    44: {
        "name": "Corner Peel Bottom-Right",
        "short_desc": "Peels from bottom-right corner",
        "long_desc": "Current wallpaper peels from bottom-right corner revealing new one",
        "family": "peel",
        "direction": "bottom-right",
        "version": VERSION,
        "author": AUTHOR
    },
    
    # === WAVE TRANSITIONS ===
    45: {
        "name": "Wave Horizontal",
        "short_desc": "Wave effect horizontally",
        "long_desc": "Current wallpaper waves horizontally transitioning to new one",
        "family": "wave",
        "direction": "horizontal",
        "version": VERSION,
        "author": AUTHOR
    },
    46: {
        "name": "Wave Vertical",
        "short_desc": "Wave effect vertically",
        "long_desc": "Current wallpaper waves vertically transitioning to new one",
        "family": "wave",
        "direction": "vertical",
        "version": VERSION,
        "author": AUTHOR
    },
    
    # === SPIRAL TRANSITIONS ===
    47: {
        "name": "Spiral Clockwise",
        "short_desc": "Spirals clockwise from center",
        "long_desc": "New wallpaper spirals in clockwise from center",
        "family": "spiral",
        "direction": "cw",
        "version": VERSION,
        "author": AUTHOR
    },
    48: {
        "name": "Spiral Counter-Clockwise",
        "short_desc": "Spirals counter-clockwise from center",
        "long_desc": "New wallpaper spirals in counter-clockwise from center",
        "family": "spiral",
        "direction": "ccw",
        "version": VERSION,
        "author": AUTHOR
    },
    
    # === CHECKERBOARD TRANSITIONS ===
    49: {
        "name": "Checkerboard",
        "short_desc": "Checkerboard pattern reveal",
        "long_desc": "New wallpaper reveals in checkerboard pattern",
        "family": "checkerboard",
        "direction": "normal",
        "version": VERSION,
        "author": AUTHOR
    },
    50: {
        "name": "Checkerboard Inverse",
        "short_desc": "Inverse checkerboard pattern",
        "long_desc": "New wallpaper reveals in inverse checkerboard pattern",
        "family": "checkerboard",
        "direction": "inverse",
        "version": VERSION,
        "author": AUTHOR
    }
}


def get_curated_transitions():
    """Return the curated transitions dictionary"""
    return CURATED_TRANSITIONS


class TransitionEngine:
    """Handles transition frame generation using OpenCV with proper compositing"""
    
    def __init__(self, screen_width, screen_height, debug=False):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.debug = debug
        self.tmp_dir = "/tmp/bnm3_frames"
        Path(self.tmp_dir).mkdir(parents=True, exist_ok=True)
    
    def debug_print(self, message):
        """Print debug messages if debug mode is enabled"""
        if self.debug:
            print(f"[TRANSITION DEBUG] {message}")
    
    def prepare_image(self, img_path):
        """Load and resize image to screen resolution"""
        img = cv2.imread(str(img_path))
        if img is None:
            raise ValueError(f"Cannot load image {img_path}")
        return cv2.resize(img, (self.screen_width, self.screen_height), interpolation=cv2.INTER_LANCZOS4)
    
    def composite_images(self, old_img, new_img, old_transform, new_transform, keep_image=False):
        """
        Composite two images with transformations
        
        Args:
            old_img: Current wallpaper (numpy array)
            new_img: New wallpaper (numpy array)
            old_transform: Transformation matrix for old image
            new_transform: Transformation matrix for new image
            keep_image: If True, show new image as background
            
        Returns:
            Composited frame
        """
        w, h = self.screen_width, self.screen_height
        
        # Apply transformations
        old_transformed = cv2.warpAffine(old_img, old_transform, (w, h), 
                                        borderMode=cv2.BORDER_CONSTANT, 
                                        borderValue=(0, 0, 0))
        new_transformed = cv2.warpAffine(new_img, new_transform, (w, h),
                                        borderMode=cv2.BORDER_CONSTANT,
                                        borderValue=(0, 0, 0))
        
        if keep_image:
            # Start with new image as background
            result = new_transformed.copy()
            # Create mask for old image (non-black pixels)
            mask = cv2.cvtColor(old_transformed, cv2.COLOR_BGR2GRAY)
            mask = (mask > 10).astype(np.uint8) * 255
            mask = cv2.merge([mask, mask, mask])
            # Composite old on top where it's not black
            result = np.where(mask > 0, old_transformed, result)
        else:
            # Black background, composite both images
            result = np.zeros((h, w, 3), dtype=np.uint8)
            # Add new image first (background)
            new_mask = cv2.cvtColor(new_transformed, cv2.COLOR_BGR2GRAY)
            new_mask = (new_mask > 10).astype(np.uint8) * 255
            new_mask = cv2.merge([new_mask, new_mask, new_mask])
            result = np.where(new_mask > 0, new_transformed, result)
            # Add old image on top
            old_mask = cv2.cvtColor(old_transformed, cv2.COLOR_BGR2GRAY)
            old_mask = (old_mask > 10).astype(np.uint8) * 255
            old_mask = cv2.merge([old_mask, old_mask, old_mask])
            result = np.where(old_mask > 0, old_transformed, result)
        
        return result
    
    def generate_slide_transition(self, old_img, new_img, direction, num_frames, keep_image=False):
        """Generate slide transition frames with proper compositing"""
        frames = []
        w, h = self.screen_width, self.screen_height
        
        for i in range(num_frames):
            progress = i / max(num_frames - 1, 1)
            
            # Calculate offsets for old and new images
            if direction == "left":
                old_dx, old_dy = -int(progress * w), 0
                new_dx, new_dy = w - int(progress * w), 0
            elif direction == "right":
                old_dx, old_dy = int(progress * w), 0
                new_dx, new_dy = -w + int(progress * w), 0
            elif direction == "up":
                old_dx, old_dy = 0, -int(progress * h)
                new_dx, new_dy = 0, h - int(progress * h)
            elif direction == "down":
                old_dx, old_dy = 0, int(progress * h)
                new_dx, new_dy = 0, -h + int(progress * h)
            elif direction == "top-left":
                old_dx, old_dy = -int(progress * w), -int(progress * h)
                new_dx, new_dy = w - int(progress * w), h - int(progress * h)
            elif direction == "top-right":
                old_dx, old_dy = int(progress * w), -int(progress * h)
                new_dx, new_dy = -w + int(progress * w), h - int(progress * h)
            elif direction == "bottom-left":
                old_dx, old_dy = -int(progress * w), int(progress * h)
                new_dx, new_dy = w - int(progress * w), -h + int(progress * h)
            elif direction == "bottom-right":
                old_dx, old_dy = int(progress * w), int(progress * h)
                new_dx, new_dy = -w + int(progress * w), -h + int(progress * h)
            
            # Create transformation matrices
            old_M = np.float32([[1, 0, old_dx], [0, 1, old_dy]])
            new_M = np.float32([[1, 0, new_dx], [0, 1, new_dy]])
            
            # Composite frame
            frame = self.composite_images(old_img, new_img, old_M, new_M, keep_image)
            
            # Save frame
            frame_path = f"{self.tmp_dir}/frame_{i:04d}.jpg"
            cv2.imwrite(frame_path, frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
            frames.append(frame_path)
        
        return frames
    
    def generate_rotate_transition(self, old_img, new_img, angle, direction, num_frames, keep_image=False):
        """Generate rotation transition frames"""
        frames = []
        w, h = self.screen_width, self.screen_height
        center = (w // 2, h // 2)
        
        for i in range(num_frames):
            progress = i / max(num_frames - 1, 1)
            
            # Calculate rotation angle
            if direction == "cw":
                current_angle = progress * angle
            else:  # ccw
                current_angle = -progress * angle
            
            # Old image rotates out
            old_M = cv2.getRotationMatrix2D(center, current_angle, 1.0)
            
            # New image stays in place (or rotates in from opposite direction)
            new_M = cv2.getRotationMatrix2D(center, 0, 1.0)
            
            # For smooth transition, fade in new image
            old_alpha = 1.0 - progress
            new_alpha = progress
            
            old_transformed = cv2.warpAffine(old_img, old_M, (w, h))
            new_transformed = cv2.warpAffine(new_img, new_M, (w, h))
            
            # Blend with alpha
            frame = cv2.addWeighted(old_transformed, old_alpha, new_transformed, new_alpha, 0)
            
            frame_path = f"{self.tmp_dir}/frame_{i:04d}.jpg"
            cv2.imwrite(frame_path, frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
            frames.append(frame_path)
        
        return frames
    
    def generate_zoom_transition(self, old_img, new_img, zoom_direction, num_frames, keep_image=False):
        """Generate zoom transition frames"""
        frames = []
        w, h = self.screen_width, self.screen_height
        center = (w // 2, h // 2)
        
        for i in range(num_frames):
            progress = i / max(num_frames - 1, 1)
            
            if zoom_direction == "out":
                # Old image zooms out
                old_scale = 1.0 - progress
                new_scale = 1.0
                old_alpha = 1.0 - progress
                new_alpha = progress
            elif zoom_direction == "in":
                # New image zooms in
                old_scale = 1.0
                new_scale = progress
                old_alpha = 1.0 - progress
                new_alpha = progress
            else:  # pulse
                old_scale = 1.0 + 0.3 * np.sin(progress * np.pi)
                new_scale = 1.0
                old_alpha = 1.0 - progress
                new_alpha = progress
            
            if old_scale <= 0:
                old_scale = 0.01
            if new_scale <= 0:
                new_scale = 0.01
            
            old_M = cv2.getRotationMatrix2D(center, 0, old_scale)
            old_M[0, 2] += (w / 2) * (1 - old_scale)
            old_M[1, 2] += (h / 2) * (1 - old_scale)
            
            new_M = cv2.getRotationMatrix2D(center, 0, new_scale)
            new_M[0, 2] += (w / 2) * (1 - new_scale)
            new_M[1, 2] += (h / 2) * (1 - new_scale)
            
            old_transformed = cv2.warpAffine(old_img, old_M, (w, h))
            new_transformed = cv2.warpAffine(new_img, new_M, (w, h))
            
            frame = cv2.addWeighted(old_transformed, old_alpha, new_transformed, new_alpha, 0)
            
            frame_path = f"{self.tmp_dir}/frame_{i:04d}.jpg"
            cv2.imwrite(frame_path, frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
            frames.append(frame_path)
        
        return frames
    
    def generate_fade_transition(self, old_img, new_img, fade_type, num_frames, keep_image=False):
        """Generate fade transition frames"""
        frames = []
        w, h = self.screen_width, self.screen_height
        
        for i in range(num_frames):
            progress = i / max(num_frames - 1, 1)
            
            if fade_type == "cross":
                # Simple cross-dissolve
                frame = cv2.addWeighted(old_img, 1.0 - progress, new_img, progress, 0)
            elif fade_type == "black":
                # Fade through black
                if progress < 0.5:
                    # Fade old to black
                    black = np.zeros_like(old_img)
                    frame = cv2.addWeighted(old_img, 1.0 - (progress * 2), black, progress * 2, 0)
                else:
                    # Fade from black to new
                    black = np.zeros_like(new_img)
                    frame = cv2.addWeighted(black, 1.0 - ((progress - 0.5) * 2), new_img, (progress - 0.5) * 2, 0)
            else:  # white
                # Fade through white
                if progress < 0.5:
                    white = np.full_like(old_img, 255)
                    frame = cv2.addWeighted(old_img, 1.0 - (progress * 2), white, progress * 2, 0)
                else:
                    white = np.full_like(new_img, 255)
                    frame = cv2.addWeighted(white, 1.0 - ((progress - 0.5) * 2), new_img, (progress - 0.5) * 2, 0)
            
            frame_path = f"{self.tmp_dir}/frame_{i:04d}.jpg"
            cv2.imwrite(frame_path, frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
            frames.append(frame_path)
        
        return frames
    
    def generate_wipe_transition(self, old_img, new_img, direction, num_frames, keep_image=False):
        """Generate wipe transition frames"""
        frames = []
        w, h = self.screen_width, self.screen_height
        
        for i in range(num_frames):
            progress = i / max(num_frames - 1, 1)
            frame = old_img.copy()
            
            if direction == "left":
                x_cut = int((1.0 - progress) * w)
                frame[:, x_cut:] = new_img[:, x_cut:]
            elif direction == "right":
                x_cut = int(progress * w)
                frame[:, :x_cut] = new_img[:, :x_cut]
            elif direction == "up":
                y_cut = int((1.0 - progress) * h)
                frame[y_cut:, :] = new_img[y_cut:, :]
            elif direction == "down":
                y_cut = int(progress * h)
                frame[:y_cut, :] = new_img[:y_cut, :]
            
            frame_path = f"{self.tmp_dir}/frame_{i:04d}.jpg"
            cv2.imwrite(frame_path, frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
            frames.append(frame_path)
        
        return frames
    
    def generate_push_transition(self, old_img, new_img, direction, num_frames, keep_image=False):
        """Generate push transition (both images move together)"""
        return self.generate_slide_transition(old_img, new_img, direction, num_frames, keep_image)
    
    def generate_split_transition(self, old_img, new_img, direction, num_frames, keep_image=False):
        """Generate split transition frames"""
        frames = []
        w, h = self.screen_width, self.screen_height
        
        for i in range(num_frames):
            progress = i / max(num_frames - 1, 1)
            frame = new_img.copy()
            
            if direction == "horizontal":
                # Split horizontally from center
                half_h = h // 2
                offset = int((1.0 - progress) * half_h)
                frame[:half_h - offset, :] = old_img[:half_h - offset, :]
                frame[half_h + offset:, :] = old_img[half_h + offset:, :]
            else:  # vertical
                # Split vertically from center
                half_w = w // 2
                offset = int((1.0 - progress) * half_w)
                frame[:, :half_w - offset] = old_img[:, :half_w - offset]
                frame[:, half_w + offset:] = old_img[:, half_w + offset:]
            
            frame_path = f"{self.tmp_dir}/frame_{i:04d}.jpg"
            cv2.imwrite(frame_path, frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
            frames.append(frame_path)
        
        return frames
    
    def generate_box_transition(self, old_img, new_img, direction, num_frames, keep_image=False):
        """Generate box transition frames"""
        frames = []
        w, h = self.screen_width, self.screen_height
        
        for i in range(num_frames):
            progress = i / max(num_frames - 1, 1)
            
            if direction == "in":
                # Box grows from center
                frame = old_img.copy()
                box_w = int(progress * w)
                box_h = int(progress * h)
                x1 = (w - box_w) // 2
                y1 = (h - box_h) // 2
                x2 = x1 + box_w
                y2 = y1 + box_h
                frame[y1:y2, x1:x2] = new_img[y1:y2, x1:x2]
            else:  # out
                # Box shrinks to center
                frame = new_img.copy()
                box_w = int((1.0 - progress) * w)
                box_h = int((1.0 - progress) * h)
                x1 = (w - box_w) // 2
                y1 = (h - box_h) // 2
                x2 = x1 + box_w
                y2 = y1 + box_h
                frame[y1:y2, x1:x2] = old_img[y1:y2, x1:x2]
            
            frame_path = f"{self.tmp_dir}/frame_{i:04d}.jpg"
            cv2.imwrite(frame_path, frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
            frames.append(frame_path)
        
        return frames
    
    def generate_circle_transition(self, old_img, new_img, direction, num_frames, keep_image=False):
        """Generate circle transition frames"""
        frames = []
        w, h = self.screen_width, self.screen_height
        center = (w // 2, h // 2)
        max_radius = int(np.sqrt(w**2 + h**2) / 2)
        
        for i in range(num_frames):
            progress = i / max(num_frames - 1, 1)
            
            if direction == "in":
                radius = int(progress * max_radius)
                frame = old_img.copy()
                mask = np.zeros((h, w), dtype=np.uint8)
                cv2.circle(mask, center, radius, 255, -1)
                mask = cv2.merge([mask, mask, mask])
                frame = np.where(mask > 0, new_img, old_img)
            else:  # out
                radius = int((1.0 - progress) * max_radius)
                frame = new_img.copy()
                mask = np.zeros((h, w), dtype=np.uint8)
                cv2.circle(mask, center, radius, 255, -1)
                mask = cv2.merge([mask, mask, mask])
                frame = np.where(mask > 0, old_img, new_img)
            
            frame_path = f"{self.tmp_dir}/frame_{i:04d}.jpg"
            cv2.imwrite(frame_path, frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
            frames.append(frame_path)
        
        return frames
    
    def generate_pixelate_transition(self, old_img, new_img, direction, num_frames, keep_image=False):
        """Generate pixelate transition frames"""
        frames = []
        
        for i in range(num_frames):
            progress = i / max(num_frames - 1, 1)
            
            # Pixelate factor (more pixelated in the middle)
            if progress < 0.5:
                pixel_factor = int(1 + (progress * 2) * 20)
            else:
                pixel_factor = int(1 + ((1.0 - progress) * 2) * 20)
            
            # Pixelate based on progress
            if progress < 0.5:
                base = old_img.copy()
            else:
                base = new_img.copy()
            
            h, w = base.shape[:2]
            temp = cv2.resize(base, (w // pixel_factor, h // pixel_factor), interpolation=cv2.INTER_LINEAR)
            frame = cv2.resize(temp, (w, h), interpolation=cv2.INTER_NEAREST)
            
            # Blend with target
            if progress < 0.5:
                frame = cv2.addWeighted(frame, 1.0, new_img, progress * 2, 0)
            else:
                frame = cv2.addWeighted(old_img, 1.0 - ((progress - 0.5) * 2), frame, 1.0, 0)
            
            frame_path = f"{self.tmp_dir}/frame_{i:04d}.jpg"
            cv2.imwrite(frame_path, frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
            frames.append(frame_path)
        
        return frames
    
    def generate_blur_transition(self, old_img, new_img, direction, num_frames, keep_image=False):
        """Generate blur transition frames"""
        frames = []
        
        for i in range(num_frames):
            progress = i / max(num_frames - 1, 1)
            
            # Blur strength (max in middle)
            if progress < 0.5:
                blur_amount = int(1 + (progress * 2) * 30)
                alpha = 1.0 - (progress * 2)
                base = old_img
            else:
                blur_amount = int(1 + ((1.0 - progress) * 2) * 30)
                alpha = (progress - 0.5) * 2
                base = new_img
            
            if blur_amount % 2 == 0:
                blur_amount += 1
            
            blurred = cv2.GaussianBlur(base, (blur_amount, blur_amount), 0)
            
            # Crossfade
            if progress < 0.5:
                frame = cv2.addWeighted(blurred, 1.0, new_img, progress * 2, 0)
            else:
                frame = cv2.addWeighted(old_img, 1.0 - alpha, blurred, 1.0, 0)
            
            frame_path = f"{self.tmp_dir}/frame_{i:04d}.jpg"
            cv2.imwrite(frame_path, frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
            frames.append(frame_path)
        
        return frames
    
    def generate_flip_transition(self, old_img, new_img, direction, num_frames, keep_image=False):
        """Generate 3D flip transition frames"""
        frames = []
        w, h = self.screen_width, self.screen_height
        
        for i in range(num_frames):
            progress = i / max(num_frames - 1, 1)
            
            # 3D flip effect using perspective transform
            if direction == "horizontal":
                # Horizontal flip
                scale_x = abs(np.cos(progress * np.pi))
                if progress < 0.5:
                    base = old_img
                else:
                    base = cv2.flip(new_img, 1)  # Flip new image horizontally
                
                M = np.float32([[scale_x, 0, w * (1 - scale_x) / 2], [0, 1, 0]])
            else:  # vertical
                scale_y = abs(np.cos(progress * np.pi))
                if progress < 0.5:
                    base = old_img
                else:
                    base = cv2.flip(new_img, 0)  # Flip new image vertically
                
                M = np.float32([[1, 0, 0], [0, scale_y, h * (1 - scale_y) / 2]])
            
            frame = cv2.warpAffine(base, M, (w, h))
            
            frame_path = f"{self.tmp_dir}/frame_{i:04d}.jpg"
            cv2.imwrite(frame_path, frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
            frames.append(frame_path)
        
        return frames
    
    def generate_door_transition(self, old_img, new_img, direction, num_frames, keep_image=False):
        """Generate door swing transition frames"""
        frames = []
        w, h = self.screen_width, self.screen_height
        
        for i in range(num_frames):
            progress = i / max(num_frames - 1, 1)
            frame = new_img.copy()
            
            # Door swing effect using perspective
            swing_width = int(w * (1.0 - progress))
            
            if direction == "left":
                # Door swings from left edge
                if swing_width > 0:
                    door_part = old_img[:, :swing_width]
                    # Perspective scale
                    scale = 1.0 - progress * 0.5
                    new_h = int(h * scale)
                    if new_h > 0:
                        resized = cv2.resize(door_part, (swing_width, new_h))
                        y_offset = (h - new_h) // 2
                        frame[y_offset:y_offset+new_h, :swing_width] = resized
            else:  # right
                # Door swings from right edge
                if swing_width > 0:
                    door_part = old_img[:, -swing_width:]
                    scale = 1.0 - progress * 0.5
                    new_h = int(h * scale)
                    if new_h > 0:
                        resized = cv2.resize(door_part, (swing_width, new_h))
                        y_offset = (h - new_h) // 2
                        frame[y_offset:y_offset+new_h, -swing_width:] = resized
            
            frame_path = f"{self.tmp_dir}/frame_{i:04d}.jpg"
            cv2.imwrite(frame_path, frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
            frames.append(frame_path)
        
        return frames
    
    def generate_barn_transition(self, old_img, new_img, direction, num_frames, keep_image=False):
        """Generate barn door transition frames"""
        frames = []
        w, h = self.screen_width, self.screen_height
        
        for i in range(num_frames):
            progress = i / max(num_frames - 1, 1)
            frame = new_img.copy()
            
            if direction == "horizontal":
                # Horizontal barn doors
                door_width = int((w // 2) * (1.0 - progress))
                if door_width > 0:
                    frame[:, :door_width] = old_img[:, :door_width]
                    frame[:, -door_width:] = old_img[:, -door_width:]
            else:  # vertical
                door_height = int((h // 2) * (1.0 - progress))
                if door_height > 0:
                    frame[:door_height, :] = old_img[:door_height, :]
                    frame[-door_height:, :] = old_img[-door_height:, :]
            
            frame_path = f"{self.tmp_dir}/frame_{i:04d}.jpg"
            cv2.imwrite(frame_path, frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
            frames.append(frame_path)
        
        return frames
    
    def generate_peel_transition(self, old_img, new_img, corner, num_frames, keep_image=False):
        """Generate corner peel transition frames"""
        frames = []
        w, h = self.screen_width, self.screen_height
        
        for i in range(num_frames):
            progress = i / max(num_frames - 1, 1)
            frame = new_img.copy()
            
            # Calculate peel area
            peel_w = int(w * (1.0 - progress))
            peel_h = int(h * (1.0 - progress))
            
            if corner == "top-left":
                if peel_w > 0 and peel_h > 0:
                    frame[:peel_h, :peel_w] = old_img[:peel_h, :peel_w]
            elif corner == "top-right":
                if peel_w > 0 and peel_h > 0:
                    frame[:peel_h, -peel_w:] = old_img[:peel_h, -peel_w:]
            elif corner == "bottom-left":
                if peel_w > 0 and peel_h > 0:
                    frame[-peel_h:, :peel_w] = old_img[-peel_h:, :peel_w]
            else:  # bottom-right
                if peel_w > 0 and peel_h > 0:
                    frame[-peel_h:, -peel_w:] = old_img[-peel_h:, -peel_w:]
            
            frame_path = f"{self.tmp_dir}/frame_{i:04d}.jpg"
            cv2.imwrite(frame_path, frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
            frames.append(frame_path)
        
        return frames
    
    def generate_wave_transition(self, old_img, new_img, direction, num_frames, keep_image=False):
        """Generate wave transition frames"""
        frames = []
        w, h = self.screen_width, self.screen_height
        
        for i in range(num_frames):
            progress = i / max(num_frames - 1, 1)
            frame = old_img.copy()
            
            for y in range(h):
                if direction == "horizontal":
                    # Horizontal wave
                    wave_offset = int(20 * np.sin((y / h * 10 + progress * 5) * np.pi))
                    cut_x = int(progress * w) + wave_offset
                    if 0 <= cut_x < w:
                        frame[y, :cut_x] = new_img[y, :cut_x]
                else:  # vertical
                    # Vertical wave
                    wave_offset = int(20 * np.sin((y / h * 10 + progress * 5) * np.pi))
                    cut_y = int(progress * h)
                    if cut_y < h:
                        frame[cut_y:, :] = new_img[cut_y:, :]
            
            frame_path = f"{self.tmp_dir}/frame_{i:04d}.jpg"
            cv2.imwrite(frame_path, frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
            frames.append(frame_path)
        
        return frames
    
    def generate_spiral_transition(self, old_img, new_img, direction, num_frames, keep_image=False):
        """Generate spiral transition frames"""
        frames = []
        w, h = self.screen_width, self.screen_height
        center = (w // 2, h // 2)
        
        for i in range(num_frames):
            progress = i / max(num_frames - 1, 1)
            frame = old_img.copy()
            
            # Create spiral mask
            mask = np.zeros((h, w), dtype=np.uint8)
            max_radius = int(np.sqrt(w**2 + h**2) / 2)
            
            for radius in range(0, int(progress * max_radius), 2):
                if direction == "cw":
                    angle_range = np.linspace(0, progress * 4 * np.pi, 100)
                else:  # ccw
                    angle_range = np.linspace(0, -progress * 4 * np.pi, 100)
                
                for angle in angle_range:
                    r = radius
                    x = int(center[0] + r * np.cos(angle))
                    y = int(center[1] + r * np.sin(angle))
                    if 0 <= x < w and 0 <= y < h:
                        cv2.circle(mask, (x, y), 3, 255, -1)
            
            mask = cv2.merge([mask, mask, mask])
            frame = np.where(mask > 0, new_img, old_img)
            
            frame_path = f"{self.tmp_dir}/frame_{i:04d}.jpg"
            cv2.imwrite(frame_path, frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
            frames.append(frame_path)
        
        return frames
    
    def generate_checkerboard_transition(self, old_img, new_img, pattern_type, num_frames, keep_image=False):
        """Generate checkerboard transition frames"""
        frames = []
        w, h = self.screen_width, self.screen_height
        checker_size = 40
        
        for i in range(num_frames):
            progress = i / max(num_frames - 1, 1)
            frame = old_img.copy()
            
            for y in range(0, h, checker_size):
                for x in range(0, w, checker_size):
                    checker_row = y // checker_size
                    checker_col = x // checker_size
                    
                    if pattern_type == "normal":
                        is_checker = (checker_row + checker_col) % 2 == 0
                    else:  # inverse
                        is_checker = (checker_row + checker_col) % 2 == 1
                    
                    # Random reveal based on progress
                    reveal_threshold = progress + random.random() * 0.1
                    
                    if is_checker and reveal_threshold > 0.5:
                        y2 = min(y + checker_size, h)
                        x2 = min(x + checker_size, w)
                        frame[y:y2, x:x2] = new_img[y:y2, x:x2]
            
            frame_path = f"{self.tmp_dir}/frame_{i:04d}.jpg"
            cv2.imwrite(frame_path, frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
            frames.append(frame_path)
        
        return frames
    
    def generate_transition_frames(self, old_img, new_img, trans_id, total_frames, keep_image=False):
        """
        Generate all frames for a transition with proper compositing
        
        Args:
            old_img: Path to current wallpaper
            new_img: Path to next wallpaper
            trans_id: Transition ID from CURATED_TRANSITIONS
            total_frames: Total number of frames to generate
            keep_image: Whether to keep new image visible as background
            
        Returns:
            List of frame paths
        """
        if trans_id not in CURATED_TRANSITIONS:
            self.debug_print(f"Invalid transition ID {trans_id}, using random")
            trans_id = random.choice(list(CURATED_TRANSITIONS.keys()))
        
        transition = CURATED_TRANSITIONS[trans_id]
        
        self.debug_print(f"Transition #{trans_id}: {transition['name']}")
        self.debug_print(f"  {transition['short_desc']}")
        self.debug_print(f"  Keep image mode: {keep_image}")
        
        # Prepare images
        self.debug_print("Loading and resizing images...")
        old_img_prepared = self.prepare_image(old_img)
        new_img_prepared = self.prepare_image(new_img)
        
        # Generate frames based on family
        family = transition['family']
        direction = transition.get('direction', '')
        
        self.debug_print(f"Generating {total_frames} frames for family '{family}'")
        
        if family == "slide":
            frames = self.generate_slide_transition(old_img_prepared, new_img_prepared, direction, total_frames, keep_image)
        elif family == "rotate":
            angle = transition.get('angle', 90)
            frames = self.generate_rotate_transition(old_img_prepared, new_img_prepared, angle, direction, total_frames, keep_image)
        elif family == "zoom":
            frames = self.generate_zoom_transition(old_img_prepared, new_img_prepared, direction, total_frames, keep_image)
        elif family == "fade":
            frames = self.generate_fade_transition(old_img_prepared, new_img_prepared, direction, total_frames, keep_image)
        elif family == "wipe":
            frames = self.generate_wipe_transition(old_img_prepared, new_img_prepared, direction, total_frames, keep_image)
        elif family == "push":
            frames = self.generate_push_transition(old_img_prepared, new_img_prepared, direction, total_frames, keep_image)
        elif family == "split":
            frames = self.generate_split_transition(old_img_prepared, new_img_prepared, direction, total_frames, keep_image)
        elif family == "box":
            frames = self.generate_box_transition(old_img_prepared, new_img_prepared, direction, total_frames, keep_image)
        elif family == "circle":
            frames = self.generate_circle_transition(old_img_prepared, new_img_prepared, direction, total_frames, keep_image)
        elif family == "pixelate":
            frames = self.generate_pixelate_transition(old_img_prepared, new_img_prepared, direction, total_frames, keep_image)
        elif family == "blur":
            frames = self.generate_blur_transition(old_img_prepared, new_img_prepared, direction, total_frames, keep_image)
        elif family == "flip":
            frames = self.generate_flip_transition(old_img_prepared, new_img_prepared, direction, total_frames, keep_image)
        elif family == "door":
            frames = self.generate_door_transition(old_img_prepared, new_img_prepared, direction, total_frames, keep_image)
        elif family == "barn":
            frames = self.generate_barn_transition(old_img_prepared, new_img_prepared, direction, total_frames, keep_image)
        elif family == "peel":
            frames = self.generate_peel_transition(old_img_prepared, new_img_prepared, direction, total_frames, keep_image)
        elif family == "wave":
            frames = self.generate_wave_transition(old_img_prepared, new_img_prepared, direction, total_frames, keep_image)
        elif family == "spiral":
            frames = self.generate_spiral_transition(old_img_prepared, new_img_prepared, direction, total_frames, keep_image)
        elif family == "checkerboard":
            frames = self.generate_checkerboard_transition(old_img_prepared, new_img_prepared, direction, total_frames, keep_image)
        else:
            self.debug_print(f"Unknown family '{family}', using fade")
            frames = self.generate_fade_transition(old_img_prepared, new_img_prepared, "cross", total_frames, keep_image)
        
        self.debug_print(f"Generated {len(frames)} total frames")
        
        return frames
    
    def cleanup_frames(self):
        """Clean up temporary frame files"""
        try:
            for file in Path(self.tmp_dir).glob("*.jpg"):
                file.unlink()
            self.debug_print("Cleaned up temporary frames")
        except Exception as e:
            self.debug_print(f"Error cleaning up frames: {e}")


def print_transition_library():
    """Print all available transitions with metadata"""
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
        print(f"\n### {family.upper()} TRANSITIONS ###")
        for tid, trans in sorted(transitions):
            print(f"  [{tid:3d}] {trans['name']}")
            print(f"        {trans['short_desc']}")
    
    print(f"\n{'='*80}")
    print(f"Total: {len(CURATED_TRANSITIONS)} curated transitions across {len(families)} families")
    print(f"{'='*80}\n")


# Global export for main program
if __name__ == "__main__":
    print_transition_library()
