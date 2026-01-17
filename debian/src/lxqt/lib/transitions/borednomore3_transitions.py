import os
import subprocess
import time
import random
from pathlib import Path

# --- CORE TRANSITION LOGIC (7 base geometries) ---
LOGIC_MAP = {
    0: ["Slide Left",      "slide-out-l", "slide-in-l"],
    1: ["Slide Right",     "slide-out-r", "slide-in-r"],
    2: ["Slide Up",        "slide-out-u", "slide-in-u"],
    3: ["Slide Down",      "slide-out-d", "slide-in-d"],
    4: ["Spin Clockwise",  "rot-out-cw",  "rot-in-cw"],
    5: ["Spin Counter-CW", "rot-out-ccw", "rot-in-ccw"],
    6: ["Zoom In/Out",     "zoom-out",    "zoom-in"]
}

# Map 1000 transition IDs to 7 core behaviors
TRANSITIONS = {i: LOGIC_MAP[i % 7] for i in range(1, 1001)}

# State tracking
_STATE = {
    "last_img": None,
    "last_tid": None
}

# --- IMAGE OPTIMIZER ---
def prepare_image(img_path, w, h, tmp_dir):
    """
    Pre-process image to exact screen resolution for faster transitions.
    Returns path to optimized image.
    """
    # Check if image is already at correct size
    try:
        result = subprocess.run(
            f"identify -format '%wx%h' '{img_path}'",
            shell=True,
            capture_output=True,
            text=True,
            timeout=5
        )
        
        current_size = result.stdout.strip()
        target_size = f"{w}x{h}"
        
        if current_size == target_size:
            # Already perfect size, use as-is
            return img_path
        
        # Need to resize - create optimized version
        optimized_path = os.path.join(tmp_dir, f"opt_{os.path.basename(img_path)}")
        
        # Resize to exact dimensions with high quality
        resize_cmd = f"convert '{img_path}' -resize {w}x{h}! -quality 90 '{optimized_path}'"
        
        subprocess.run(
            resize_cmd,
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=10
        )
        
        if os.path.exists(optimized_path):
            return optimized_path
        else:
            # Fallback to original if resize failed
            return img_path
            
    except:
        # Any error, just use original
        return img_path

# --- COMMAND FACTORY ---
def get_cmd(img, mode, frames, w, h, out_pattern):
    """
    Generate ImageMagick command for specific mode
    mode: exit or entry behavior
    frames: number of frames for this phase
    """
    f = frames
    hw, hh = w // 2, h // 2
    t = "(t+1)"  # Frame index (1-based)
    
    # === EXIT MODES (Old image leaving) ===
    if mode == "slide-out-l":
        # Slide left: progressively reveal black on right
        return f"convert '{img}' \\( +clone -background black -splice %[fx:{t}*{w}/{f}]x0 \\) -duplicate {f-1} -delete 0 -crop {w}x{h}+0+0 +repage '{out_pattern}'"
    
    elif mode == "slide-out-r":
        # Slide right: progressively reveal black on left
        return f"convert '{img}' \\( +clone -background black -splice %[fx:{t}*{w}/{f}]x0+0+0 \\) -duplicate {f-1} -delete 0 -crop {w}x{h}+%[fx:{t}*{w}/{f}]+0 +repage '{out_pattern}'"
    
    elif mode == "slide-out-u":
        # Slide up: progressively reveal black on bottom
        return f"convert '{img}' \\( +clone -background black -splice 0x%[fx:{t}*{h}/{f}] \\) -duplicate {f-1} -delete 0 -crop {w}x{h}+0+0 +repage '{out_pattern}'"
    
    elif mode == "slide-out-d":
        # Slide down: progressively reveal black on top
        return f"convert '{img}' \\( +clone -background black -splice 0x%[fx:{t}*{h}/{f}]+0+0 \\) -duplicate {f-1} -delete 0 -crop {w}x{h}+0+%[fx:{t}*{h}/{f}] +repage '{out_pattern}'"
    
    elif mode == "rot-out-cw":
        return f"convert '{img}' -duplicate {f-1} -virtual-pixel black -distort SRT '{hw},{hh} 1 %[fx:{t}*90/{f}]' -gravity center -extent {w}x{h} '{out_pattern}'"
    
    elif mode == "rot-out-ccw":
        return f"convert '{img}' -duplicate {f-1} -virtual-pixel black -distort SRT '{hw},{hh} 1 %[fx:-{t}*90/{f}]' -gravity center -extent {w}x{h} '{out_pattern}'"
    
    elif mode == "zoom-out":
        return f"convert '{img}' -duplicate {f-1} -virtual-pixel black -distort SRT '{hw},{hh} %[fx:1-{t}/{f}] 0' -gravity center -extent {w}x{h} '{out_pattern}'"
    
    # === ENTRY MODES (New image arriving) ===
    elif mode == "slide-in-l":
        # Slide in from left: progressively reveal image from left
        return f"convert -size {w}x{h} xc:black '{img}' +append -duplicate {f-1} -crop {w}x{h}+%[fx:{w}-{t}*{w}/{f}]+0 +repage '{out_pattern}'"
    
    elif mode == "slide-in-r":
        # Slide in from right: progressively reveal image from right  
        return f"convert '{img}' -size {w}x{h} xc:black +append -duplicate {f-1} -crop {w}x{h}+%[fx:{t}*{w}/{f}]+0 +repage '{out_pattern}'"
    
    elif mode == "slide-in-u":
        # Slide in from top: progressively reveal image from top
        return f"convert -size {w}x{h} xc:black '{img}' -append -duplicate {f-1} -crop {w}x{h}+0+%[fx:{h}-{t}*{h}/{f}] +repage '{out_pattern}'"
    
    elif mode == "slide-in-d":
        # Slide in from bottom: progressively reveal image from bottom
        return f"convert '{img}' -size {w}x{h} xc:black -append -duplicate {f-1} -crop {w}x{h}+0+%[fx:{t}*{h}/{f}] +repage '{out_pattern}'"
    
    elif mode == "rot-in-cw":
        return f"convert '{img}' -duplicate {f-1} -virtual-pixel black -distort SRT '{hw},{hh} 1 %[fx:90-{t}*90/{f}]' -gravity center -extent {w}x{h} '{out_pattern}'"
    
    elif mode == "rot-in-ccw":
        return f"convert '{img}' -duplicate {f-1} -virtual-pixel black -distort SRT '{hw},{hh} 1 %[fx:-90+{t}*90/{f}]' -gravity center -extent {w}x{h} '{out_pattern}'"
    
    elif mode == "zoom-in":
        return f"convert '{img}' -duplicate {f-1} -virtual-pixel black -distort SRT '{hw},{hh} %[fx:{t}/{f}] 0' -gravity center -extent {w}x{h} '{out_pattern}'"
    
    # Fallback
    return f"convert '{img}' -duplicate {f-1} '{out_pattern}'"

# --- MAIN TRANSITION ENGINE ---
def apply_transition(old_img, current_img, trans_id, w, h, frames, speed, 
                     set_wall_func, check_exit, keep_image=True, interval=5, wall_list=None):
    """
    Two-phase transition system:
    1. EXIT: Old image leaves
    2. ENTRY: New image arrives
    
    CRITICAL: speed parameter controls playback speed
    - speed=0 means INSTANT playback (frames flash too fast to see)
    - speed=0.05 means 50ms per frame (smooth animation)
    """
    global _STATE
    
    tmp_dir = "/tmp/bnm3_frames"
    Path(tmp_dir).mkdir(parents=True, exist_ok=True)
    
    # === PRE-OPTIMIZE IMAGES TO EXACT SCREEN SIZE ===
    # This makes transitions 5-10x faster!
    print(f"  [OPTIMIZE] Preparing images for {w}x{h} screen...")
    
    # Use last_img for continuity
    source_img_original = _STATE["last_img"] if _STATE["last_img"] else old_img
    
    # Optimize both images to exact screen resolution
    source_img = prepare_image(source_img_original, w, h, tmp_dir)
    current_img_optimized = prepare_image(current_img, w, h, tmp_dir)
    
    # Get transition metadata
    if trans_id not in TRANSITIONS:
        trans_id = random.randint(1, 1000)
    
    meta = TRANSITIONS[trans_id]  # [Name, ExitMode, EntryMode]
    
    print(f"Using transition #{trans_id}: {meta[0]}")
    
    # Split frames between exit and entry
    exit_frames = frames // 2
    entry_frames = frames - exit_frames
    
    # Clean old frames
    subprocess.run(f"rm -f {tmp_dir}/*.jpg", shell=True, stderr=subprocess.DEVNULL)
    
    # ==================== PHASE 1: EXIT ====================
    exit_pattern = f"{tmp_dir}/f01_%04d.jpg"
    
    if exit_frames > 0:
        exit_cmd = get_cmd(source_img, meta[1], exit_frames, w, h, exit_pattern)
        print(f"  [EXIT] Rendering {exit_frames} frames...")
        
        subprocess.run(
            exit_cmd,
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=30
        )
    
    # ==================== PHASE 2: ENTRY ====================
    entry_pattern = f"{tmp_dir}/f02_%04d.jpg"
    entry_cmd = get_cmd(current_img_optimized, meta[2], entry_frames, w, h, entry_pattern)
    
    print(f"  [ENTRY] Rendering {entry_frames} frames...")
    subprocess.run(
        entry_cmd,
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=30
    )
    
    # ==================== PLAYBACK ====================
    # Collect frames in order: f01_0000, f01_0001, ..., f02_0000, f02_0001, ...
    frames_list = sorted([
        os.path.join(tmp_dir, f) 
        for f in os.listdir(tmp_dir) 
        if f.endswith('.jpg')
    ])
    
    if not frames_list:
        print(f"  [ERROR] No frames generated! Using direct cut.")
        set_wall_func(current_img)
    else:
        print(f"  [PLAYBACK] Playing {len(frames_list)} frames at {speed}s per frame...")
        
        # CRITICAL: Actually play the frames with proper timing
        for i, frame_path in enumerate(frames_list):
            if check_exit():
                break
            
            # Set wallpaper to this frame
            set_wall_func(frame_path)
            
            # FORCE desktop refresh even with speed=0
            # LXQt needs time to actually apply the wallpaper change
            if speed > 0:
                time.sleep(speed)
            else:
                # Minimum delay for desktop to register the change
                # Without this, frames change too fast for X11/compositor
                time.sleep(0.016)  # ~60fps (16ms per frame)
        
        print(f"  [COMPLETE] Animation finished")
    
    # Final lock (use ORIGINAL full-res image for final display)
    set_wall_func(current_img)
    
    # Update state with ORIGINAL image path
    _STATE["last_img"] = current_img
    _STATE["last_tid"] = trans_id
    
    # Cleanup (remove optimized temps and frames)
    subprocess.run(f"rm -f {tmp_dir}/*.jpg", shell=True, stderr=subprocess.DEVNULL)

# --- RESET ---
def reset_transition_state():
    global _STATE
    _STATE = {
        "last_img": None,
        "last_tid": None
    }

# --- USAGE INFO ---
"""
USAGE NOTES:
============

1. SPEED PARAMETER IS CRITICAL:
   -s 0     = INSTANT (no visible animation, frames flash too fast)
   -s 0.05  = 50ms per frame (smooth, visible animation)
   -s 0.1   = 100ms per frame (slower, more visible)

2. FRAME COUNT:
   -f 10    = 10 total frames (5 exit + 5 entry)
   -f 20    = 20 total frames (10 exit + 10 entry)

3. EXAMPLE COMMANDS:
   ./borednomore3.py -i 5 -f 20 -s 0.05 -w -r  # Smooth animation
   ./borednomore3.py -i 3 -f 10 -s 0.1 -w -r   # Slower animation

4. TRANSITIONS:
   - 1000 transition IDs available (1-1000)
   - All map to 7 core geometries:
     * Slide Left/Right/Up/Down
     * Spin Clockwise/Counter-Clockwise  
     * Zoom In/Out
   - Random selection picks from all 1000
   - Specific ID uses that transition
"""
