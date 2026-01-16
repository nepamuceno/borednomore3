#!/usr/bin/env python3
"""
Slide Transitions Category
All directional slide, push, reveal, and whip-pan transitions
"""
import os
import time
import tempfile
from PIL import Image

# =============================================================================
# SLIDE TRANSITIONS
# =============================================================================

def slide_left(old_path, new_path, w, h, frames, speed, set_wp, check_exit, keep_image):
    """Slide from right to left"""
    try:
        old = Image.open(old_path).convert('RGB').resize((w, h), Image.Resampling.LANCZOS)
        new = Image.open(new_path).convert('RGB').resize((w, h), Image.Resampling.LANCZOS)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            for i in range(frames + 1):
                if check_exit(): return
                alpha = i / frames
                offset = int(w * alpha)
                
                canvas = Image.new('RGB', (w, h))
                if keep_image:
                    canvas.paste(old, (0, 0))
                    if offset > 0:
                        new_part = new.crop((w - offset, 0, w, h))
                        canvas.paste(new_part, (w - offset, 0))
                else:
                    canvas.paste(old, (-offset, 0))
                    canvas.paste(new, (w - offset, 0))
                
                path = os.path.join(tmpdir, f"frame_{i:03d}.jpg")
                canvas.save(path, "JPEG", quality=95)
                set_wp(path)
                time.sleep(speed)
        set_wp(new_path)
    except:
        set_wp(new_path)


def slide_right(old_path, new_path, w, h, frames, speed, set_wp, check_exit, keep_image):
    """Slide from left to right"""
    try:
        old = Image.open(old_path).convert('RGB').resize((w, h), Image.Resampling.LANCZOS)
        new = Image.open(new_path).convert('RGB').resize((w, h), Image.Resampling.LANCZOS)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            for i in range(frames + 1):
                if check_exit(): return
                alpha = i / frames
                offset = int(w * alpha)
                
                canvas = Image.new('RGB', (w, h))
                if keep_image:
                    canvas.paste(old, (0, 0))
                    if offset > 0:
                        new_part = new.crop((0, 0, offset, h))
                        canvas.paste(new_part, (0, 0))
                else:
                    canvas.paste(old, (offset, 0))
                    canvas.paste(new, (offset - w, 0))
                
                path = os.path.join(tmpdir, f"frame_{i:03d}.jpg")
                canvas.save(path, "JPEG", quality=95)
                set_wp(path)
                time.sleep(speed)
        set_wp(new_path)
    except:
        set_wp(new_path)


def slide_up(old_path, new_path, w, h, frames, speed, set_wp, check_exit, keep_image):
    """Slide from bottom to top"""
    try:
        old = Image.open(old_path).convert('RGB').resize((w, h), Image.Resampling.LANCZOS)
        new = Image.open(new_path).convert('RGB').resize((w, h), Image.Resampling.LANCZOS)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            for i in range(frames + 1):
                if check_exit(): return
                alpha = i / frames
                offset = int(h * alpha)
                
                canvas = Image.new('RGB', (w, h))
                if keep_image:
                    canvas.paste(old, (0, 0))
                    if offset > 0:
                        new_part = new.crop((0, h - offset, w, h))
                        canvas.paste(new_part, (0, h - offset))
                else:
                    canvas.paste(old, (0, -offset))
                    canvas.paste(new, (0, h - offset))
                
                path = os.path.join(tmpdir, f"frame_{i:03d}.jpg")
                canvas.save(path, "JPEG", quality=95)
                set_wp(path)
                time.sleep(speed)
        set_wp(new_path)
    except:
        set_wp(new_path)


def slide_down(old_path, new_path, w, h, frames, speed, set_wp, check_exit, keep_image):
    """Slide from top to bottom"""
    try:
        old = Image.open(old_path).convert('RGB').resize((w, h), Image.Resampling.LANCZOS)
        new = Image.open(new_path).convert('RGB').resize((w, h), Image.Resampling.LANCZOS)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            for i in range(frames + 1):
                if check_exit(): return
                alpha = i / frames
                offset = int(h * alpha)
                
                canvas = Image.new('RGB', (w, h))
                if keep_image:
                    canvas.paste(old, (0, 0))
                    if offset > 0:
                        new_part = new.crop((0, 0, w, offset))
                        canvas.paste(new_part, (0, 0))
                else:
                    canvas.paste(old, (0, offset))
                    canvas.paste(new, (0, offset - h))
                
                path = os.path.join(tmpdir, f"frame_{i:03d}.jpg")
                canvas.save(path, "JPEG", quality=95)
                set_wp(path)
                time.sleep(speed)
        set_wp(new_path)
    except:
        set_wp(new_path)


# Whip pans - fast versions of slides
def whip_pan_left(old_path, new_path, w, h, frames, speed, set_wp, check_exit, keep_image):
    """Fast pan left"""
    slide_left(old_path, new_path, w, h, frames // 2, speed / 2, set_wp, check_exit, keep_image)


def whip_pan_right(old_path, new_path, w, h, frames, speed, set_wp, check_exit, keep_image):
    """Fast pan right"""
    slide_right(old_path, new_path, w, h, frames // 2, speed / 2, set_wp, check_exit, keep_image)


def whip_pan_up(old_path, new_path, w, h, frames, speed, set_wp, check_exit, keep_image):
    """Fast pan up"""
    slide_up(old_path, new_path, w, h, frames // 2, speed / 2, set_wp, check_exit, keep_image)


def whip_pan_down(old_path, new_path, w, h, frames, speed, set_wp, check_exit, keep_image):
    """Fast pan down"""
    slide_down(old_path, new_path, w, h, frames // 2, speed / 2, set_wp, check_exit, keep_image)


# Push - both images move together
def push_left(old_path, new_path, w, h, frames, speed, set_wp, check_exit, keep_image):
    """Push left - both images move"""
    slide_left(old_path, new_path, w, h, frames, speed, set_wp, check_exit, False)


def push_right(old_path, new_path, w, h, frames, speed, set_wp, check_exit, keep_image):
    """Push right - both images move"""
    slide_right(old_path, new_path, w, h, frames, speed, set_wp, check_exit, False)


def push_up(old_path, new_path, w, h, frames, speed, set_wp, check_exit, keep_image):
    """Push up - both images move"""
    slide_up(old_path, new_path, w, h, frames, speed, set_wp, check_exit, False)


def push_down(old_path, new_path, w, h, frames, speed, set_wp, check_exit, keep_image):
    """Push down - both images move"""
    slide_down(old_path, new_path, w, h, frames, speed, set_wp, check_exit, False)


# Fold - aliases for slides
def fold_left(old_path, new_path, w, h, frames, speed, set_wp, check_exit, keep_image):
    """Fold left"""
    slide_left(old_path, new_path, w, h, frames, speed, set_wp, check_exit, keep_image)


def fold_right(old_path, new_path, w, h, frames, speed, set_wp, check_exit, keep_image):
    """Fold right"""
    slide_right(old_path, new_path, w, h, frames, speed, set_wp, check_exit, keep_image)


def fold_up(old_path, new_path, w, h, frames, speed, set_wp, check_exit, keep_image):
    """Fold up"""
    slide_up(old_path, new_path, w, h, frames, speed, set_wp, check_exit, keep_image)


def fold_down(old_path, new_path, w, h, frames, speed, set_wp, check_exit, keep_image):
    """Fold down"""
    slide_down(old_path, new_path, w, h, frames, speed, set_wp, check_exit, keep_image)
