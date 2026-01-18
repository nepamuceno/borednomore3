import os
import subprocess
import time
import random
from pathlib import Path
import cv2
import numpy as np


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

# --- CURATED TRANSITIONS ---
CURATED = {}
for tid, meta in TRANSITIONS.items():
    family_name = meta[0]
    CURATED.setdefault(family_name, []).append(tid)

print("================================================================================")
print("[DEBUG] Curated transitions summary:")
total_curated = 0
for family, ids in CURATED.items():
    print(f"  {family}: {len(ids)} IDs")
    total_curated += len(ids)
print(f"[DEBUG] Total curated transitions: {total_curated}")
print("================================================================================")

# --- STATE TRACKING ---
_STATE = {
    "last_img": None,
    "last_tid": None
}

# --- IMAGE OPTIMIZER ---
def prepare_image(img_path, w, h):
    img = cv2.imread(str(img_path))
    if img is None:
        raise ValueError(f"Cannot load image {img_path}")
    return cv2.resize(img, (w, h))


# --- RECIPES ---
RECIPES = {
    "slide": {
        "out": {
            "l": "convert '{img}' -duplicate {f} -crop {w}x{h}+%[fx:n*{w}/{f}]+0 +repage '{out}'",
            "r": "convert '{img}' -duplicate {f} -crop {w}x{h}+%[fx:{w}-n*{w}/{f}]+0 +repage '{out}'",
            "u": "convert '{img}' -duplicate {f} -crop {w}x{h}+0+%[fx:n*{h}/{f}] +repage '{out}'",
            "d": "convert '{img}' -duplicate {f} -crop {w}x{h}+0+%[fx:{h}-n*{h}/{f}] +repage '{out}'",
        },
        "in": {
            "l": "convert '{img}' -duplicate {f} -crop {w}x{h}+%[fx:{w}-n*{w}/{f}]+0 +repage '{out}'",
            "r": "convert '{img}' -duplicate {f} -crop {w}x{h}+%[fx:n*{w}/{f}]+0 +repage '{out}'",
            "u": "convert '{img}' -duplicate {f} -crop {w}x{h}+0+%[fx:{h}-n*{h}/{f}] +repage '{out}'",
            "d": "convert '{img}' -duplicate {f} -crop {w}x{h}+0+%[fx:n*{h}/{f}] +repage '{out}'",
        }
    },
    "rot": {
        "out": {
            "cw": "convert '{img}' -duplicate {f} -virtual-pixel black "
                  "-distort SRT '{hw},{hh} 1 %[fx:n*90/{f}]' -gravity center "
                  "-extent {w}x{h} '{out}'",
            "ccw": "convert '{img}' -duplicate {f} -virtual-pixel black "
                   "-distort SRT '{hw},{hh} 1 %[fx:-n*90/{f}]' -gravity center "
                   "-extent {w}x{h} '{out}'",
        },
        "in": {
            "cw": "convert '{img}' -duplicate {f} -virtual-pixel black "
                  "-distort SRT '{hw},{hh} 1 %[fx:90-n*90/{f}]' -gravity center "
                  "-extent {w}x{h} '{out}'",
            "ccw": "convert '{img}' -duplicate {f} -virtual-pixel black "
                   "-distort SRT '{hw},{hh} 1 %[fx:-90+n*90/{f}]' -gravity center "
                   "-extent {w}x{h} '{out}'",
        }
    },
    "zoom": {
        "out": {
            None: "convert '{img}' -duplicate {f} -virtual-pixel black "
                  "-distort SRT '{hw},{hh} %[fx:1-n/{f}] 0' -gravity center "
                  "-extent {w}x{h} '{out}'",
        },
        "in": {
            None: "convert '{img}' -duplicate {f} -virtual-pixel black "
                  "-distort SRT '{hw},{hh} %[fx:n/{f}] 0' -gravity center "
                  "-extent {w}x{h} '{out}'",
        }
    }
}

# --- COMMAND FACTORY ---
def get_cmd(img, mode, frames, w, h, out_pattern):
    f = frames
    hw, hh = w // 2, h // 2
    out = out_pattern
    parts = mode.split("-")
    family = parts[0]
    phase = parts[1]
    variant = "-".join(parts[2:]) if len(parts) > 2 else None
    print(f"[get_cmd] mode={mode}, family={family}, phase={phase}, variant={variant}, frames={frames}")

    frames_list = []

    # Asegurar que 'image' sea un numpy.ndarray
    if isinstance(img, np.ndarray):
        image = img
    else:
        image = cv2.imread(str(img))
        if image is None:
            print(f"[get_cmd] ERROR: cannot load {img}")
            return []

    if family == "slide":
        for i in range(f):
            dx, dy = 0, 0
            if variant == "l":
                dx = int(i * w / f)
            elif variant == "r":
                dx = -int(i * w / f)
            elif variant == "u":
                dy = int(i * h / f)
            elif variant == "d":
                dy = -int(i * h / f)
            M = np.float32([[1, 0, dx], [0, 1, dy]])
            frame = cv2.warpAffine(image, M, (w, h))
            frame_path = out % i
            cv2.imwrite(frame_path, frame)
            frames_list.append(frame_path)

    elif family == "rot":
        center = (w // 2, h // 2)
        for i in range(f):
            angle = (i * 90 / f) if variant == "cw" else -(i * 90 / f)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            frame = cv2.warpAffine(image, M, (w, h))
            frame_path = out % i
            cv2.imwrite(frame_path, frame)
            frames_list.append(frame_path)

    elif family == "zoom":
        for i in range(f):
            scale = (1.0 - i / f) if phase == "out" else (i / f)
            if scale <= 0:
                scale = 0.01
            M = cv2.getRotationMatrix2D((w // 2, h // 2), 0, scale)
            frame = cv2.warpAffine(image, M, (w, h))
            frame_path = out % i
            cv2.imwrite(frame_path, frame)
            frames_list.append(frame_path)

    print(f"[get_cmd] Generated {len(frames_list)} frames")
    return frames_list


# --- MAIN TRANSITION ENGINE ---
def apply_transition(old_img, current_img, trans_id, w, h, frames, speed,
                     set_wall_func, check_exit, keep_image=True, interval=5, wall_list=None):
    global _STATE
    tmp_dir = "/tmp/bnm3_frames"
    Path(tmp_dir).mkdir(parents=True, exist_ok=True)

    print(f"  [OPTIMIZE] Preparing images for {w}x{h} screen...")
    source_img_original = _STATE["last_img"] if _STATE["last_img"] else old_img
    source_img = prepare_image(source_img_original, w, h)
    current_img_optimized = prepare_image(current_img, w, h)

    if trans_id not in TRANSITIONS or trans_id not in CURATED[TRANSITIONS[trans_id][0]]:
        trans_id = random.choice([tid for ids in CURATED.values() for tid in ids])
    meta = TRANSITIONS[trans_id]
    print(f"Using transition #{trans_id}: {meta[0]}")

    exit_frames = frames // 2
    entry_frames = frames - exit_frames

    # ==================== PHASE 1: EXIT ====================
    exit_pattern = f"{tmp_dir}/f01_%04d.jpg"
    exit_frames_list = get_cmd(source_img, meta[1], exit_frames, w, h, exit_pattern)
    print(f"  [EXIT] Rendering {len(exit_frames_list)} frames...")

    # ==================== PHASE 2: ENTRY ====================
    entry_pattern = f"{tmp_dir}/f02_%04d.jpg"
    entry_frames_list = get_cmd(current_img_optimized, meta[2], entry_frames, w, h, entry_pattern)
    print(f"  [ENTRY] Rendering {len(entry_frames_list)} frames...")

    # ==================== PLAYBACK ====================
    frames_list = exit_frames_list + entry_frames_list

    if not frames_list:
        print(f"  [ERROR] No frames generated! Using direct cut.")
        set_wall_func(current_img)
    else:
        print(f"  [PLAYBACK] Playing {len(frames_list)} frames at {speed}s per frame...")
        for frame_path in frames_list:
            if check_exit():
                break
            set_wall_func(frame_path)
            if speed > 0:
                time.sleep(speed)
            else:
                time.sleep(0.016)
        print(f"  [COMPLETE] Animation finished")

    set_wall_func(current_img)
    _STATE["last_img"] = current_img
    _STATE["last_tid"] = trans_id
