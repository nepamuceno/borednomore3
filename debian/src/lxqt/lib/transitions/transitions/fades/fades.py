#!/usr/bin/env python3
"""
Fade Transitions Category
All fade-based transitions including crossfades, dissolves, and blur transitions
"""
import os
import time
import tempfile
from PIL import Image, ImageFilter

# =============================================================================
# FADE TRANSITIONS
# =============================================================================

def instant_cut(old_path, new_path, w, h, frames, speed, set_wp, check_exit, keep_image):
    """Instant cut - no transition"""
    set_wp(new_path)


def fade(old_path, new_path, w, h, frames, speed, set_wp, check_exit, keep_image):
    """Classic fade transition from image A to image B"""
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
    except Exception:
        set_wp(new_path)


def fade_in(old_path, new_path, w, h, frames, speed, set_wp, check_exit, keep_image):
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


def fade_out(old_path, new_path, w, h, frames, speed, set_wp, check_exit, keep_image):
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


def crossfade(old_path, new_path, w, h, frames, speed, set_wp, check_exit, keep_image):
    """Alias for standard fade"""
    fade(old_path, new_path, w, h, frames, speed, set_wp, check_exit, keep_image)


def dissolve_white(old_path, new_path, w, h, frames, speed, set_wp, check_exit, keep_image):
    """Dissolve through white"""
    try:
        old = Image.open(old_path).convert('RGB').resize((w, h), Image.Resampling.LANCZOS)
        white = Image.new('RGB', (w, h), (255, 255, 255))
        new = Image.open(new_path).convert('RGB').resize((w, h), Image.Resampling.LANCZOS)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            for i in range(frames // 2 + 1):
                if check_exit(): return
                alpha = i / (frames // 2)
                blended = Image.blend(old, white, alpha)
                path = os.path.join(tmpdir, f"frame_{i:03d}.jpg")
                blended.save(path, "JPEG", quality=95)
                set_wp(path)
                time.sleep(speed)
            
            for i in range(frames // 2 + 1):
                if check_exit(): return
                alpha = i / (frames // 2)
                blended = Image.blend(white, new, alpha)
                path = os.path.join(tmpdir, f"frame_{frames//2 + i:03d}.jpg")
                blended.save(path, "JPEG", quality=95)
                set_wp(path)
                time.sleep(speed)
        set_wp(new_path)
    except:
        set_wp(new_path)


def dissolve_black(old_path, new_path, w, h, frames, speed, set_wp, check_exit, keep_image):
    """Dissolve through black"""
    try:
        old = Image.open(old_path).convert('RGB').resize((w, h), Image.Resampling.LANCZOS)
        black = Image.new('RGB', (w, h), (0, 0, 0))
        new = Image.open(new_path).convert('RGB').resize((w, h), Image.Resampling.LANCZOS)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            for i in range(frames // 2 + 1):
                if check_exit(): return
                alpha = i / (frames // 2)
                blended = Image.blend(old, black, alpha)
                path = os.path.join(tmpdir, f"frame_{i:03d}.jpg")
                blended.save(path, "JPEG", quality=95)
                set_wp(path)
                time.sleep(speed)
            
            for i in range(frames // 2 + 1):
                if check_exit(): return
                alpha = i / (frames // 2)
                blended = Image.blend(black, new, alpha)
                path = os.path.join(tmpdir, f"frame_{frames//2 + i:03d}.jpg")
                blended.save(path, "JPEG", quality=95)
                set_wp(path)
                time.sleep(speed)
        set_wp(new_path)
    except:
        set_wp(new_path)


def focus_in(old_path, new_path, w, h, frames, speed, set_wp, check_exit, keep_image):
    """Blur focus shift from old to new"""
    try:
        old = Image.open(old_path).convert('RGB').resize((w, h), Image.Resampling.LANCZOS)
        new = Image.open(new_path).convert('RGB').resize((w, h), Image.Resampling.LANCZOS)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            for i in range(frames + 1):
                if check_exit(): return
                alpha = i / frames
                
                old_blur = int(alpha * 20)
                old_blurred = old.filter(ImageFilter.GaussianBlur(old_blur))
                
                new_blur = int((1 - alpha) * 20)
                new_blurred = new.filter(ImageFilter.GaussianBlur(new_blur))
                
                result = Image.blend(old_blurred, new_blurred, alpha)
                
                path = os.path.join(tmpdir, f"frame_{i:03d}.jpg")
                result.save(path, "JPEG", quality=95)
                set_wp(path)
                time.sleep(speed)
        set_wp(new_path)
    except:
        set_wp(new_path)


def focus_out(old_path, new_path, w, h, frames, speed, set_wp, check_exit, keep_image):
    """Blur focus shift from new to old (reverse)"""
    try:
        old = Image.open(old_path).convert('RGB').resize((w, h), Image.Resampling.LANCZOS)
        new = Image.open(new_path).convert('RGB').resize((w, h), Image.Resampling.LANCZOS)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            for i in range(frames + 1):
                if check_exit(): return
                alpha = i / frames
                
                old_blur = int((1 - alpha) * 20)
                old_blurred = old.filter(ImageFilter.GaussianBlur(old_blur))
                
                new_blur = int(alpha * 20)
                new_blurred = new.filter(ImageFilter.GaussianBlur(new_blur))
                
                result = Image.blend(old_blurred, new_blurred, alpha)
                
                path = os.path.join(tmpdir, f"frame_{i:03d}.jpg")
                result.save(path, "JPEG", quality=95)
                set_wp(path)
                time.sleep(speed)
        set_wp(new_path)
    except:
        set_wp(new_path)
