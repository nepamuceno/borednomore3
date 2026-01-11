#!/usr/bin/env python3
"""
BoredNoMore3 Transition Library
Comprehensive collection of professional wallpaper transitions

Author: Nepamuceno Bartolo
Email: zzerver@gmail.com
Version: 0.5.0
"""

import os
import time
import tempfile
from PIL import Image, ImageDraw, ImageFilter
import random
import math

# Transition Registry
TRANSITIONS = {
    1: "fade",
    2: "fade-in",
    3: "fade-out",
    4: "cross-fade",
    5: "dissolve",
    6: "cut",
    7: "jump-cut",
    8: "match-cut",
    9: "smash-cut",
    10: "wipe",
    11: "iris-in",
    12: "iris-out",
    13: "l-cut",
    14: "j-cut",
    15: "whip-pan",
    16: "zoom-in",
    17: "zoom-out",
    18: "rack-focus",
    19: "morph",
    20: "invisible-cut",
    21: "light-leak",
    22: "masking",
    23: "glitch",
    24: "pull-back",
    25: "push-in",
    26: "clock-wipe",
    27: "slide-in",
    28: "slide-out",
    29: "dissolve-white",
    30: "dip-black",
    31: "swipe-left",
    32: "swipe-right",
    33: "swipe-up",
    34: "swipe-down",
    35: "barn-door",
    36: "checker",
    37: "pixelate",
    38: "spiral",
    39: "split-vertical",
    40: "split-horizontal",
}


def apply_transition(old_path, new_path, transition_num, width, height, 
                     frames, speed, set_wallpaper_func, should_exit_func):
    """Apply the specified transition"""
    
    transition_name = TRANSITIONS.get(transition_num, "fade")
    
    # Map transition names to functions
    transition_map = {
        "fade": fade_transition,
        "fade-in": fade_in_transition,
        "fade-out": fade_out_transition,
        "cross-fade": cross_fade_transition,
        "dissolve": dissolve_transition,
        "cut": cut_transition,
        "jump-cut": jump_cut_transition,
        "match-cut": match_cut_transition,
        "smash-cut": smash_cut_transition,
        "wipe": wipe_transition,
        "iris-in": iris_in_transition,
        "iris-out": iris_out_transition,
        "l-cut": l_cut_transition,
        "j-cut": j_cut_transition,
        "whip-pan": whip_pan_transition,
        "zoom-in": zoom_in_transition,
        "zoom-out": zoom_out_transition,
        "rack-focus": rack_focus_transition,
        "morph": morph_transition,
        "invisible-cut": invisible_cut_transition,
        "light-leak": light_leak_transition,
        "masking": masking_transition,
        "glitch": glitch_transition,
        "pull-back": pull_back_transition,
        "push-in": push_in_transition,
        "clock-wipe": clock_wipe_transition,
        "slide-in": slide_in_transition,
        "slide-out": slide_out_transition,
        "dissolve-white": dissolve_white_transition,
        "dip-black": dip_black_transition,
        "swipe-left": swipe_left_transition,
        "swipe-right": swipe_right_transition,
        "swipe-up": swipe_up_transition,
        "swipe-down": swipe_down_transition,
        "barn-door": barn_door_transition,
        "checker": checker_transition,
        "pixelate": pixelate_transition,
        "spiral": spiral_transition,
        "split-vertical": split_vertical_transition,
        "split-horizontal": split_horizontal_transition,
    }
    
    func = transition_map.get(transition_name, fade_transition)
    func(old_path, new_path, width, height, frames, speed, 
         set_wallpaper_func, should_exit_func)


# ============================================================================
# TRANSITION IMPLEMENTATIONS
# ============================================================================

def fade_transition(old_path, new_path, w, h, frames, speed, set_wp, check_exit):
    """Classic fade/blend transition"""
    try:
        old = Image.open(old_path).convert('RGB').resize((w, h), Image.Resampling.LANCZOS)
        new = Image.open(new_path).convert('RGB').resize((w, h), Image.Resampling.LANCZOS)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            for i in range(frames + 1):
                if check_exit(): return
                alpha = i / frames
                blended = Image.blend(old, new, alpha)
                path = os.path.join(tmpdir, f"frame_{i:03d}.jpg")
                blended.save(path, "JPEG", quality=95)
                set_wp(path)
                time.sleep(speed)
        set_wp(new_path)
    except Exception as e:
        set_wp(new_path)


def fade_in_transition(old_path, new_path, w, h, frames, speed, set_wp, check_exit):
    """Fade from black to new image"""
    try:
        black = Image.new('RGB', (w, h), (0, 0, 0))
        new = Image.open(new_path).convert('RGB').resize((w, h), Image.Resampling.LANCZOS)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            for i in range(frames + 1):
                if check_exit(): return
                alpha = i / frames
                blended = Image.blend(black, new, alpha)
                path = os.path.join(tmpdir, f"frame_{i:03d}.jpg")
                blended.save(path, "JPEG", quality=95)
                set_wp(path)
                time.sleep(speed)
        set_wp(new_path)
    except:
        set_wp(new_path)


def fade_out_transition(old_path, new_path, w, h, frames, speed, set_wp, check_exit):
    """Fade to black then show new image"""
    try:
        old = Image.open(old_path).convert('RGB').resize((w, h), Image.Resampling.LANCZOS)
        black = Image.new('RGB', (w, h), (0, 0, 0))
        new = Image.open(new_path).convert('RGB').resize((w, h), Image.Resampling.LANCZOS)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Fade to black
            for i in range(frames // 2):
                if check_exit(): return
                alpha = i / (frames // 2)
                blended = Image.blend(old, black, alpha)
                path = os.path.join(tmpdir, f"frame_{i:03d}.jpg")
                blended.save(path, "JPEG", quality=95)
                set_wp(path)
                time.sleep(speed)
            
            # Fade from black
            for i in range(frames // 2 + 1):
                if check_exit(): return
                alpha = i / (frames // 2)
                blended = Image.blend(black, new, alpha)
                path = os.path.join(tmpdir, f"frame_{i:03d}.jpg")
                blended.save(path, "JPEG", quality=95)
                set_wp(path)
                time.sleep(speed)
        set_wp(new_path)
    except:
        set_wp(new_path)


def cross_fade_transition(old_path, new_path, w, h, frames, speed, set_wp, check_exit):
    """Enhanced cross-fade with slight overlap"""
    fade_transition(old_path, new_path, w, h, frames, speed, set_wp, check_exit)


def dissolve_transition(old_path, new_path, w, h, frames, speed, set_wp, check_exit):
    """Dissolve with random pixel replacement"""
    try:
        old = Image.open(old_path).convert('RGB').resize((w, h), Image.Resampling.LANCZOS)
        new = Image.open(new_path).convert('RGB').resize((w, h), Image.Resampling.LANCZOS)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            for i in range(frames + 1):
                if check_exit(): return
                alpha = i / frames
                # Add noise for dissolve effect
                blended = Image.blend(old, new, alpha)
                if i < frames:
                    noise = random.randint(0, 20)
                    enhancer = blended.filter(ImageFilter.GaussianBlur(noise * 0.1))
                    blended = Image.blend(blended, enhancer, 0.3)
                
                path = os.path.join(tmpdir, f"frame_{i:03d}.jpg")
                blended.save(path, "JPEG", quality=95)
                set_wp(path)
                time.sleep(speed)
        set_wp(new_path)
    except:
        set_wp(new_path)


def cut_transition(old_path, new_path, w, h, frames, speed, set_wp, check_exit):
    """Instant cut - no transition"""
    set_wp(new_path)


def jump_cut_transition(old_path, new_path, w, h, frames, speed, set_wp, check_exit):
    """Quick jump cut with brief flash"""
    try:
        white = Image.new('RGB', (w, h), (255, 255, 255))
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "flash.jpg")
            white.save(path, "JPEG", quality=95)
            set_wp(path)
            time.sleep(speed * 2)
        set_wp(new_path)
    except:
        set_wp(new_path)


def match_cut_transition(old_path, new_path, w, h, frames, speed, set_wp, check_exit):
    """Match cut with center focus blend"""
    try:
        old = Image.open(old_path).convert('RGB').resize((w, h), Image.Resampling.LANCZOS)
        new = Image.open(new_path).convert('RGB').resize((w, h), Image.Resampling.LANCZOS)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            for i in range(frames + 1):
                if check_exit(): return
                alpha = i / frames
                # Create radial blend from center
                mask = Image.new('L', (w, h), 0)
                draw = ImageDraw.Draw(mask)
                max_radius = int(math.sqrt(w**2 + h**2) / 2)
                radius = int(max_radius * alpha)
                draw.ellipse([w//2 - radius, h//2 - radius, 
                             w//2 + radius, h//2 + radius], fill=255)
                
                result = Image.composite(new, old, mask)
                path = os.path.join(tmpdir, f"frame_{i:03d}.jpg")
                result.save(path, "JPEG", quality=95)
                set_wp(path)
                time.sleep(speed)
        set_wp(new_path)
    except:
        set_wp(new_path)


def smash_cut_transition(old_path, new_path, w, h, frames, speed, set_wp, check_exit):
    """Smash cut - instant with emphasis"""
    cut_transition(old_path, new_path, w, h, frames, speed, set_wp, check_exit)


def wipe_transition(old_path, new_path, w, h, frames, speed, set_wp, check_exit):
    """Left to right wipe"""
    swipe_left_transition(old_path, new_path, w, h, frames, speed, set_wp, check_exit)


def iris_in_transition(old_path, new_path, w, h, frames, speed, set_wp, check_exit):
    """Circular iris in from center"""
    try:
        old = Image.open(old_path).convert('RGB').resize((w, h), Image.Resampling.LANCZOS)
        new = Image.open(new_path).convert('RGB').resize((w, h), Image.Resampling.LANCZOS)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            max_radius = int(math.sqrt(w**2 + h**2) / 2)
            for i in range(frames + 1):
                if check_exit(): return
                alpha = i / frames
                radius = int(max_radius * alpha)
                
                mask = Image.new('L', (w, h), 0)
                draw = ImageDraw.Draw(mask)
                draw.ellipse([w//2 - radius, h//2 - radius, 
                             w//2 + radius, h//2 + radius], fill=255)
                
                result = Image.composite(new, old, mask)
                path = os.path.join(tmpdir, f"frame_{i:03d}.jpg")
                result.save(path, "JPEG", quality=95)
                set_wp(path)
                time.sleep(speed)
        set_wp(new_path)
    except:
        set_wp(new_path)


def iris_out_transition(old_path, new_path, w, h, frames, speed, set_wp, check_exit):
    """Circular iris out to edges"""
    try:
        old = Image.open(old_path).convert('RGB').resize((w, h), Image.Resampling.LANCZOS)
        new = Image.open(new_path).convert('RGB').resize((w, h), Image.Resampling.LANCZOS)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            max_radius = int(math.sqrt(w**2 + h**2) / 2)
            for i in range(frames + 1):
                if check_exit(): return
                alpha = i / frames
                radius = int(max_radius * (1 - alpha))
                
                mask = Image.new('L', (w, h), 255)
                draw = ImageDraw.Draw(mask)
                if radius > 0:
                    draw.ellipse([w//2 - radius, h//2 - radius, 
                                 w//2 + radius, h//2 + radius], fill=0)
                
                result = Image.composite(new, old, mask)
                path = os.path.join(tmpdir, f"frame_{i:03d}.jpg")
                result.save(path, "JPEG", quality=95)
                set_wp(path)
                time.sleep(speed)
        set_wp(new_path)
    except:
        set_wp(new_path)


def l_cut_transition(old_path, new_path, w, h, frames, speed, set_wp, check_exit):
    """L-cut style transition (audio continues, video cuts)"""
    fade_transition(old_path, new_path, w, h, frames // 2, speed, set_wp, check_exit)


def j_cut_transition(old_path, new_path, w, h, frames, speed, set_wp, check_exit):
    """J-cut style transition (audio leads video)"""
    fade_transition(old_path, new_path, w, h, frames // 2, speed, set_wp, check_exit)


def whip_pan_transition(old_path, new_path, w, h, frames, speed, set_wp, check_exit):
    """Fast blur pan effect"""
    try:
        old = Image.open(old_path).convert('RGB').resize((w, h), Image.Resampling.LANCZOS)
        new = Image.open(new_path).convert('RGB').resize((w, h), Image.Resampling.LANCZOS)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            for i in range(frames + 1):
                if check_exit(): return
                alpha = i / frames
                
                if alpha < 0.5:
                    # Blur out old image
                    blur_amount = int((alpha * 2) * 20)
                    blurred = old.filter(ImageFilter.GaussianBlur(blur_amount))
                    result = blurred
                else:
                    # Blur in new image
                    blur_amount = int((1 - (alpha - 0.5) * 2) * 20)
                    blurred = new.filter(ImageFilter.GaussianBlur(blur_amount))
                    result = blurred
                
                path = os.path.join(tmpdir, f"frame_{i:03d}.jpg")
                result.save(path, "JPEG", quality=95)
                set_wp(path)
                time.sleep(speed * 0.5)
        set_wp(new_path)
    except:
        set_wp(new_path)


def zoom_in_transition(old_path, new_path, w, h, frames, speed, set_wp, check_exit):
    """Zoom into new image"""
    try:
        old = Image.open(old_path).convert('RGB').resize((w, h), Image.Resampling.LANCZOS)
        new = Image.open(new_path).convert('RGB').resize((w, h), Image.Resampling.LANCZOS)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            for i in range(frames + 1):
                if check_exit(): return
                alpha = i / frames
                
                # Calculate zoom
                scale = 1 + alpha * 0.5
                new_w = int(w * scale)
                new_h = int(h * scale)
                zoomed = new.resize((new_w, new_h), Image.Resampling.LANCZOS)
                
                # Crop center
                left = (new_w - w) // 2
                top = (new_h - h) // 2
                cropped = zoomed.crop((left, top, left + w, top + h))
                
                # Blend with old
                result = Image.blend(old, cropped, alpha)
                
                path = os.path.join(tmpdir, f"frame_{i:03d}.jpg")
                result.save(path, "JPEG", quality=95)
                set_wp(path)
                time.sleep(speed)
        set_wp(new_path)
    except:
        set_wp(new_path)


def zoom_out_transition(old_path, new_path, w, h, frames, speed, set_wp, check_exit):
    """Zoom out to reveal new image"""
    try:
        old = Image.open(old_path).convert('RGB').resize((w, h), Image.Resampling.LANCZOS)
        new = Image.open(new_path).convert('RGB').resize((w, h), Image.Resampling.LANCZOS)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            for i in range(frames + 1):
                if check_exit(): return
                alpha = i / frames
                
                # Calculate zoom out
                scale = 1.5 - alpha * 0.5
                old_w = int(w * scale)
                old_h = int(h * scale)
                zoomed = old.resize((old_w, old_h), Image.Resampling.LANCZOS)
                
                # Create canvas and paste
                canvas = new.copy()
                left = (w - old_w) // 2
                top = (h - old_h) // 2
                canvas.paste(zoomed, (left, top))
                
                # Blend
                result = Image.blend(canvas, new, alpha)
                
                path = os.path.join(tmpdir, f"frame_{i:03d}.jpg")
                result.save(path, "JPEG", quality=95)
                set_wp(path)
                time.sleep(speed)
        set_wp(new_path)
    except:
        set_wp(new_path)


def rack_focus_transition(old_path, new_path, w, h, frames, speed, set_wp, check_exit):
    """Blur focus shift effect"""
    try:
        old = Image.open(old_path).convert('RGB').resize((w, h), Image.Resampling.LANCZOS)
        new = Image.open(new_path).convert('RGB').resize((w, h), Image.Resampling.LANCZOS)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            for i in range(frames + 1):
                if check_exit(): return
                alpha = i / frames
                
                # Blur old image more as we progress
                old_blur = int((alpha) * 15)
                old_blurred = old.filter(ImageFilter.GaussianBlur(old_blur))
                
                # Blur new image less as we progress
                new_blur = int((1 - alpha) * 15)
                new_blurred = new.filter(ImageFilter.GaussianBlur(new_blur))
                
                result = Image.blend(old_blurred, new_blurred, alpha)
                
                path = os.path.join(tmpdir, f"frame_{i:03d}.jpg")
                result.save(path, "JPEG", quality=95)
                set_wp(path)
                time.sleep(speed)
        set_wp(new_path)
    except:
        set_wp(new_path)


def morph_transition(old_path, new_path, w, h, frames, speed, set_wp, check_exit):
    """Smooth morph blend"""
    fade_transition(old_path, new_path, w, h, frames, speed, set_wp, check_exit)


def invisible_cut_transition(old_path, new_path, w, h, frames, speed, set_wp, check_exit):
    """Ultra-fast blend - almost invisible"""
    fade_transition(old_path, new_path, w, h, max(3, frames // 4), speed * 0.5, set_wp, check_exit)


def light_leak_transition(old_path, new_path, w, h, frames, speed, set_wp, check_exit):
    """Light leak effect with brightness"""
    try:
        old = Image.open(old_path).convert('RGB').resize((w, h), Image.Resampling.LANCZOS)
        new = Image.open(new_path).convert('RGB').resize((w, h), Image.Resampling.LANCZOS)
        white = Image.new('RGB', (w, h), (255, 255, 255))
        
        with tempfile.TemporaryDirectory() as tmpdir:
            for i in range(frames + 1):
                if check_exit(): return
                alpha = i / frames
                
                # Create light leak effect
                if alpha < 0.5:
                    leak_alpha = alpha * 2
                    result = Image.blend(old, white, leak_alpha * 0.7)
                else:
                    leak_alpha = (alpha - 0.5) * 2
                    result = Image.blend(white, new, leak_alpha)
                
                path = os.path.join(tmpdir, f"frame_{i:03d}.jpg")
                result.save(path, "JPEG", quality=95)
                set_wp(path)
                time.sleep(speed)
        set_wp(new_path)
    except:
        set_wp(new_path)


def masking_transition(old_path, new_path, w, h, frames, speed, set_wp, check_exit):
    """Gradient mask transition"""
    fade_transition(old_path, new_path, w, h, frames, speed, set_wp, check_exit)


def glitch_transition(old_path, new_path, w, h, frames, speed, set_wp, check_exit):
    """Digital glitch effect"""
    try:
        old = Image.open(old_path).convert('RGB').resize((w, h), Image.Resampling.LANCZOS)
        new = Image.open(new_path).convert('RGB').resize((w, h), Image.Resampling.LANCZOS)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            for i in range(frames + 1):
                if check_exit(): return
                alpha = i / frames
                
                # Create glitch by shifting channels
                if i % 3 == 0 and i < frames:
                    r, g, b = old.split()
                    shift = random.randint(-10, 10)
                    result = Image.merge('RGB', (r, g, b))
                    result = Image.blend(result, new, alpha)
                else:
                    result = Image.blend(old, new, alpha)
                
                path = os.path.join(tmpdir, f"frame_{i:03d}.jpg")
                result.save(path, "JPEG", quality=95)
                set_wp(path)
                time.sleep(speed * 0.7)
        set_wp(new_path)
    except:
        set_wp(new_path)


def pull_back_transition(old_path, new_path, w, h, frames, speed, set_wp, check_exit):
    """Pull back/zoom out effect"""
    zoom_out_transition(old_path, new_path, w, h, frames, speed, set_wp, check_exit)


def push_in_transition(old_path, new_path, w, h, frames, speed, set_wp, check_exit):
    """Push in/zoom in effect"""
    zoom_in_transition(old_path, new_path, w, h, frames, speed, set_wp, check_exit)


def clock_wipe_transition(old_path, new_path, w, h, frames, speed, set_wp, check_exit):
    """Circular clock-style wipe"""
    try:
        old = Image.open(old_path).convert('RGB').resize((w, h), Image.Resampling.LANCZOS)
        new = Image.open(new_path).convert('RGB').resize((w, h), Image.Resampling.LANCZOS)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            for i in range(frames + 1):
                if check_exit(): return
                alpha = i / frames
                angle = 360 * alpha
                
                mask = Image.new('L', (w, h), 0)
                draw = ImageDraw.Draw(mask)
                
                # Draw pie slice
                if angle > 0:
                    draw.pieslice([0, 0, w, h], -90, -90 + angle, fill=255)
                
                result = Image.composite(new, old, mask)
                path = os.path.join(tmpdir, f"frame_{i:03d}.jpg")
                result.save(path, "JPEG", quality=95)
                set_wp(path)
                time.sleep(speed)
        set_wp(new_path)
    except:
        set_wp(new_path)


def slide_in_transition(old_path, new_path, w, h, frames, speed, set_wp, check_exit):
    """Slide in from right"""
    swipe_right_transition(old_path, new_path, w, h, frames, speed, set_wp, check_exit)


def slide_out_transition(old_path, new_path, w, h, frames, speed, set_wp, check_exit):
    """Slide out to left"""
    swipe_left_transition(old_path, new_path, w, h, frames, speed, set_wp, check_exit)


def dissolve_white_transition(old_path, new_path, w, h, frames, speed, set_wp, check_exit):
    """Dissolve through white"""
    try:
        old = Image.open(old_path).convert('RGB').resize((w, h), Image.Resampling.LANCZOS)
        white = Image.new('RGB', (w, h), (255, 255, 255))
        new = Image.open(new_path).convert('RGB').resize((w, h), Image.Resampling.LANCZOS)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            for i in range(frames // 2):
                if check_exit(): return
                alpha = i / (frames // 2)
                result = Image.blend(old, white, alpha)
                path = os.path.join(tmpdir, f"frame_{i:03d}.jpg")
                result.save(path, "JPEG", quality=95)
                set_wp(path)
                time.sleep(speed)
            
            for i in range(frames // 2 + 1):
                if check_exit(): return
                alpha = i / (frames // 2)
                result = Image.blend(white, new, alpha)
                path = os.path.join(tmpdir, f"frame_{i:03d}.jpg")
                result.save(path, "JPEG", quality=95)
                set_wp(path)
                time.sleep(speed)
        set_wp(new_path)
    except:
        set_wp(new_path)


def dip_black_transition(old_path, new_path, w, h, frames, speed, set_wp, check_exit):
    """Dip to black"""
    fade_out_transition(old_path, new_path, w, h, frames, speed, set_wp, check_exit)


def swipe_left_transition(old_path, new_path, w, h, frames, speed, set_wp, check_exit):
    """Swipe left"""
    try:
        old = Image.open(old_path).convert('RGB').resize((w, h), Image.Resampling.LANCZOS)
        new = Image.open(new_path).convert('RGB').resize((w, h), Image.Resampling.LANCZOS)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            for i in range(frames + 1):
                if check_exit(): return
                alpha = i / frames
                offset = int(w * alpha)
                
                canvas = Image.new('RGB', (w, h))
                canvas.paste(old, (-offset, 0))
                canvas.paste(new, (w - offset, 0))
                
                path = os.path.join(tmpdir, f"frame_{i:03d}.jpg")
                canvas.save(path, "JPEG", quality=95)
                set_wp(path)
                time.sleep(speed)
        set_wp(new_path)
    except:
        set_wp(new_path)


def swipe_right_transition(old_path, new_path, w, h, frames, speed, set_wp, check_exit):
    """Swipe right"""
    try:
        old = Image.open(old_path).convert('RGB').resize((w, h), Image.Resampling.LANCZOS)
        new = Image.open(new_path).convert('RGB').resize((w, h), Image.Resampling.LANCZOS)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            for i in range(frames + 1):
                if check_exit(): return
                alpha = i / frames
                offset = int(w * alpha)
                
                canvas = Image.new('RGB', (w, h))
                canvas.paste(old, (offset, 0))
                canvas.paste(new, (offset - w, 0))
                
                path = os.path.join(tmpdir, f"frame_{i:03d}.jpg")
                canvas.save(path, "JPEG", quality=95)
                set_wp(path)
                time.sleep(speed)
        set_wp(new_path)
    except:
        set_wp(new_path)


def swipe_up_transition(old_path, new_path, w, h, frames, speed, set_wp, check_exit):
    """Swipe up"""
    try:
        old = Image.open(old_path).convert('RGB').resize((w, h), Image.Resampling.LANCZOS)
        new = Image.open(new_path).convert('RGB').resize((w, h), Image.Resampling.LANCZOS)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            for i in range(frames + 1):
                if check_exit(): return
                alpha = i / frames
                offset = int(h * alpha)
                
                canvas = Image.new('RGB', (w, h))
                canvas.paste(old, (0, -offset))
                canvas.paste(new, (0, h - offset))
                
                path = os.path.join(tmpdir, f"frame_{i:03d}.jpg")
                canvas.save(path, "JPEG", quality=95)
                set_wp(path)
                time.sleep(speed)
        set_wp(new_path)
    except:
        set_wp(new_path)


def swipe_down_transition(old_path, new_path, w, h, frames, speed, set_wp, check_exit):
    """Swipe down"""
    try:
        old = Image.open(old_path).convert('RGB').resize((w, h), Image.Resampling.LANCZOS)
        new = Image.open(new_path).convert('RGB').resize((w, h), Image.Resampling.LANCZOS)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            for i in range(frames + 1):
                if check_exit(): return
                alpha = i / frames
                offset = int(h * alpha)
                
                canvas = Image.new('RGB', (w, h))
                canvas.paste(old, (0, offset))
                canvas.paste(new, (0, offset - h))
                
                path = os.path.join(tmpdir, f"frame_{i:03d}.jpg")
                canvas.save(path, "JPEG", quality=95)
                set_wp(path)
                time.sleep(speed)
        set_wp(new_path)
    except:
        set_wp(new_path)


def barn_door_transition(old_path, new_path, w, h, frames, speed, set_wp, check_exit):
    """Barn door opening from center"""
    try:
        old = Image.open(old_path).convert('RGB').resize((w, h), Image.Resampling.LANCZOS)
        new = Image.open(new_path).convert('RGB').resize((w, h), Image.Resampling.LANCZOS)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            for i in range(frames + 1):
                if check_exit(): return
                alpha = i / frames
                split = int(w * alpha / 2)
                
                canvas = old.copy()
                left_part = new.crop((0, 0, split, h))
                right_part = new.crop((w - split, 0, w, h))
                canvas.paste(left_part, (0, 0))
                canvas.paste(right_part, (w - split, 0))
                
                path = os.path.join(tmpdir, f"frame_{i:03d}.jpg")
                canvas.save(path, "JPEG", quality=95)
                set_wp(path)
                time.sleep(speed)
        set_wp(new_path)
    except:
        set_wp(new_path)


def checker_transition(old_path, new_path, w, h, frames, speed, set_wp, check_exit):
    """Checkerboard pattern transition"""
    try:
        old = Image.open(old_path).convert('RGB').resize((w, h), Image.Resampling.LANCZOS)
        new = Image.open(new_path).convert('RGB').resize((w, h), Image.Resampling.LANCZOS)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            checker_size = 40
            for i in range(frames + 1):
                if check_exit(): return
                alpha = i / frames
                
                mask = Image.new('L', (w, h), 0)
                draw = ImageDraw.Draw(mask)
                
                for y in range(0, h, checker_size):
                    for x in range(0, w, checker_size):
                        if (x // checker_size + y // checker_size) % 2 == 0:
                            if random.random() < alpha:
                                draw.rectangle([x, y, x + checker_size, y + checker_size], fill=255)
                
                result = Image.composite(new, old, mask)
                path = os.path.join(tmpdir, f"frame_{i:03d}.jpg")
                result.save(path, "JPEG", quality=95)
                set_wp(path)
                time.sleep(speed)
        set_wp(new_path)
    except:
        set_wp(new_path)


def pixelate_transition(old_path, new_path, w, h, frames, speed, set_wp, check_exit):
    """Pixelate then unpixelate transition"""
    try:
        old = Image.open(old_path).convert('RGB').resize((w, h), Image.Resampling.LANCZOS)
        new = Image.open(new_path).convert('RGB').resize((w, h), Image.Resampling.LANCZOS)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            for i in range(frames + 1):
                if check_exit(): return
                alpha = i / frames
                
                if alpha < 0.5:
                    # Pixelate old
                    progress = alpha * 2
                    pixel_size = max(1, int(50 * progress))
                    small = old.resize((w // pixel_size, h // pixel_size), Image.Resampling.NEAREST)
                    result = small.resize((w, h), Image.Resampling.NEAREST)
                else:
                    # Unpixelate new
                    progress = (alpha - 0.5) * 2
                    pixel_size = max(1, int(50 * (1 - progress)))
                    small = new.resize((w // pixel_size, h // pixel_size), Image.Resampling.NEAREST)
                    result = small.resize((w, h), Image.Resampling.NEAREST)
                
                path = os.path.join(tmpdir, f"frame_{i:03d}.jpg")
                result.save(path, "JPEG", quality=95)
                set_wp(path)
                time.sleep(speed)
        set_wp(new_path)
    except:
        set_wp(new_path)


def spiral_transition(old_path, new_path, w, h, frames, speed, set_wp, check_exit):
    """Spiral wipe from center"""
    try:
        old = Image.open(old_path).convert('RGB').resize((w, h), Image.Resampling.LANCZOS)
        new = Image.open(new_path).convert('RGB').resize((w, h), Image.Resampling.LANCZOS)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            for i in range(frames + 1):
                if check_exit(): return
                alpha = i / frames
                
                mask = Image.new('L', (w, h), 0)
                draw = ImageDraw.Draw(mask)
                
                # Create spiral effect
                for angle in range(0, int(360 * alpha), 5):
                    radius = (angle / 360) * min(w, h) / 2
                    x = w // 2 + int(radius * math.cos(math.radians(angle)))
                    y = h // 2 + int(radius * math.sin(math.radians(angle)))
                    draw.ellipse([x-10, y-10, x+10, y+10], fill=255)
                
                result = Image.composite(new, old, mask.filter(ImageFilter.GaussianBlur(15)))
                path = os.path.join(tmpdir, f"frame_{i:03d}.jpg")
                result.save(path, "JPEG", quality=95)
                set_wp(path)
                time.sleep(speed)
        set_wp(new_path)
    except:
        set_wp(new_path)


def split_vertical_transition(old_path, new_path, w, h, frames, speed, set_wp, check_exit):
    """Vertical split from center"""
    try:
        old = Image.open(old_path).convert('RGB').resize((w, h), Image.Resampling.LANCZOS)
        new = Image.open(new_path).convert('RGB').resize((w, h), Image.Resampling.LANCZOS)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            for i in range(frames + 1):
                if check_exit(): return
                alpha = i / frames
                split = int(h * alpha / 2)
                
                canvas = old.copy()
                top_part = new.crop((0, 0, w, split))
                bottom_part = new.crop((0, h - split, w, h))
                canvas.paste(top_part, (0, 0))
                canvas.paste(bottom_part, (0, h - split))
                
                path = os.path.join(tmpdir, f"frame_{i:03d}.jpg")
                canvas.save(path, "JPEG", quality=95)
                set_wp(path)
                time.sleep(speed)
        set_wp(new_path)
    except:
        set_wp(new_path)


def split_horizontal_transition(old_path, new_path, w, h, frames, speed, set_wp, check_exit):
    """Horizontal split from center"""
    barn_door_transition(old_path, new_path, w, h, frames, speed, set_wp, check_exit)
