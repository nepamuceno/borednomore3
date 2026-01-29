"""
Transition engine - handles transition selection and application
"""

import os
import subprocess
import random
import time


LOGIC_MAP = {
    1: ["slide-left", "slide-out-l", "slide-in-l"],
    2: ["slide-right", "slide-out-r", "slide-in-r"],
    3: ["slide-up", "slide-out-u", "slide-in-u"],
    4: ["slide-down", "slide-out-d", "slide-in-d"],
    7: ["spin-cw", "rot-out-cw", "rot-in-cw"],
    8: ["spin-ccw", "rot-out-ccw", "rot-in-ccw"],
    14: ["zoom-in-out", "zoom-out", "zoom-in"],
    21: ["swirl-cw", "swirl-out-cw", "swirl-in-cw"],
    22: ["swirl-ccw", "swirl-out-ccw", "swirl-in-ccw"],
    23: ["barrel-distort", "barrel-out", "barrel-in"],
    24: ["pinch", "pinch-out", "pinch-in"],
    25: ["wave-h", "wave-out-h", "wave-in-h"],
    28: ["fade", "fade-out", "fade-in"],
    32: ["pixelate", "pixel-out", "pixel-in"],
    33: ["blur-fade", "blur-out", "blur-in"],

    # New categories
    34: ["flip-h", "flip-out-h", "flip-in-h"],
    35: ["flip-v", "flip-out-v", "flip-in-v"],
    36: ["shear-x", "shear-out-x", "shear-in-x"],
    37: ["shear-y", "shear-out-y", "shear-in-y"],
    38: ["ripple", "ripple-out", "ripple-in"],
    39: ["checker", "checker-out", "checker-in"],
    40: ["glitch", "glitch-out", "glitch-in"],
    41: ["color-shift", "color-out", "color-in"],

    # Extra chaos
    42: ["shatter", "shatter-out", "shatter-in"],
    43: ["mosaic", "mosaic-out", "mosaic-in"],
    44: ["gradient", "gradient-out", "gradient-in"],
    45: ["noise", "noise-out", "noise-in"],
    46: ["twist", "twist-out", "twist-in"],
}

TRANSITIONS = {tid: modes for tid, modes in LOGIC_MAP.items()}

CATEGORY_MAP = {
    "slide": [1, 2, 3, 4],
    "spin": [7, 8],
    "zoom": [14],
    "swirl": [21, 22],
    "barrel": [23],
    "pinch": [24],
    "wave": [25],
    "fade": [28],
    "pixelate": [32],
    "blur": [33],
    "flip": [34, 35],
    "shear": [36, 37],
    "ripple": [38],
    "checker": [39],
    "glitch": [40],
    "color": [41],
    "shatter": [42],
    "mosaic": [43],
    "gradient": [44],
    "noise": [45],
    "twist": [46],
}


class TransitionEngine:
    """Handles transition selection and execution"""

    def __init__(self, transitions, randomize, frames, speed, keep_image, desktop_info, logger):
        self.logger = logger
        self.frames = frames
        self.speed = speed
        self.keep_image = keep_image
        self.desktop_info = desktop_info
        self.width = desktop_info['width']
        self.height = desktop_info['height']

        if transitions:
            self.transition_list = self._parse_transitions(transitions)
        else:
            self.transition_list = list(TRANSITIONS.keys())

        self.randomize = randomize
        self.current_index = 0

        self.exit_frames_ready = False
        self.stop_background = False
        self.current_wallpaper_exit_dir = None

    def _parse_transitions(self, transition_str):
        parts = [t.strip() for t in transition_str.split(',')]
        transitions = []
        for part in parts:
            if '-' in part:
                start_str, end_str = part.split('-')
                transitions.extend(range(int(start_str), int(end_str) + 1))
            else:
                transitions.append(int(part))
        return sorted(set([t for t in transitions if t in TRANSITIONS]))

    def get_next_transition(self):
        # Pick a category with equal probability
        category = random.choice(list(CATEGORY_MAP.keys()))
        tid = random.choice(CATEGORY_MAP[category])

        self.logger.debug(f"Chosen category: {category}, Transition ID: {tid}")

        transition_data = TRANSITIONS[tid]
        return {
            'id': tid,
            'name': transition_data[0],
            'exit_mode': transition_data[1],
            'entry_mode': transition_data[2]
        }

    def _build_command(self, img, mode, progress, width, height):
        """Build command for a single frame with progress 0.0–1.0"""

        # --- SLIDE ---
        if mode == "slide-out-l" or mode == "slide-in-l":
            offset = -int(progress * width)
            return ["convert", img, "-roll", f"{offset},0"]
        elif mode == "slide-out-r" or mode == "slide-in-r":
            offset = int(progress * width)
            return ["convert", img, "-roll", f"{offset},0"]
        elif mode == "slide-out-u" or mode == "slide-in-u":
            offset = -int(progress * height)
            return ["convert", img, "-roll", f"0,{offset}"]
        elif mode == "slide-out-d" or mode == "slide-in-d":
            offset = int(progress * height)
            return ["convert", img, "-roll", f"0,{offset}"]

        # --- SPIN ---
        elif mode == "rot-out-cw" or mode == "rot-in-cw":
            angle = progress * 360
            return ["convert", img, "-distort", "SRT", str(angle)]
        elif mode == "rot-out-ccw" or mode == "rot-in-ccw":
            angle = -progress * 360
            return ["convert", img, "-distort", "SRT", str(angle)]

        # --- ZOOM ---
        elif mode == "zoom-out":
            scale = max(0.05, 1 - progress)
            return ["convert", img, "-resize", f"{int(width*scale)}x{int(height*scale)}!"]
        elif mode == "zoom-in":
            scale = max(0.05, progress * 2)
            return ["convert", img, "-resize", f"{int(width*scale)}x{int(height*scale)}!"]

        # --- SWIRL ---
        elif mode == "swirl-out-cw" or mode == "swirl-in-cw":
            angle = progress * 360
            return ["convert", img, "-swirl", str(angle)]
        elif mode == "swirl-out-ccw" or mode == "swirl-in-ccw":
            angle = -progress * 360
            return ["convert", img, "-swirl", str(angle)]

        # --- BARREL ---
        elif mode == "barrel-out" or mode == "barrel-in":
            factor = progress * 0.8
            return ["convert", img, "-distort", "Barrel", f"0.0 {factor} 0.0 1.0"]

        # --- PINCH ---
        elif mode == "pinch-out":
            factor = progress * 1.5
            return ["convert", img, "-implode", str(factor)]
        elif mode == "pinch-in":
            factor = -progress * 1.5
            return ["convert", img, "-implode", str(factor)]

        # --- WAVE ---
        elif mode == "wave-out-h":
            amp = int(progress * 50)
            return ["convert", img, "-wave", f"{amp}x10"]
        elif mode == "wave-in-h":
            amp = int((1-progress) * 50)
            return ["convert", img, "-wave", f"{amp}x10"]

        # --- FADE ---
        elif mode == "fade-out":
            opacity = max(0.01, 1 - progress)
            return ["convert", img, "-alpha", "set", "-channel", "A", "-evaluate", "multiply", str(opacity), "+channel"]
        elif mode == "fade-in":
            opacity = max(0.01, progress)
            return ["convert", img, "-alpha", "set", "-channel", "A", "-evaluate", "multiply", str(opacity), "+channel"]

        # --- PIXELATE ---
        elif mode == "pixel-out":
            coarse = max(1, int(width * (1 - progress)))
            return ["convert", img, "-scale", f"{coarse}x{coarse}!", "-scale", f"{width}x{height}!"]
        elif mode == "pixel-in":
            coarse = max(1, int(width * progress))
            return ["convert", img, "-scale", f"{coarse}x{coarse}!", "-scale", f"{width}x{height}!"]

        # --- BLUR ---
        elif mode == "blur-out":
            radius = progress * 15
            return ["convert", img, "-blur", f"0x{radius}"]
        elif mode == "blur-in":
            radius = (1-progress) * 15
            return ["convert", img, "-blur", f"0x{radius}"]

        # --- FLIP ---
        elif mode == "flip-out-h" or mode == "flip-in-h":
            return ["convert", img, "-flop"]
        elif mode == "flip-out-v" or mode == "flip-in-v":
            return ["convert", img, "-flip"]

        # --- SHEAR ---
        elif mode == "shear-out-x" or mode == "shear-in-x":
            shear = int(progress * 45)
            return ["convert", img, "-shear", f"{shear}x0"]
        elif mode == "shear-out-y" or mode == "shear-in-y":
            shear = int(progress * 45)
            return ["convert", img, "-shear", f"0x{shear}"]

        # --- RIPPLE ---
        elif mode == "ripple-out" or mode == "ripple-in":
            amp = int(progress * 80)
            return ["convert", img, "-wave", f"{amp}x20"]

        # --- CHECKER ---
        elif mode == "checker-out" or mode == "checker-in":
            size = int(20 + progress * 80)
            return ["convert", img, "pattern:checkerboard", "-compose", "Dst_In", "-composite"]

        # --- GLITCH ---
        elif mode == "glitch-out" or mode == "glitch-in":
            spread = int(progress * 30)
            return ["convert", img, "-spread", str(spread)]

        # --- COLOR SHIFT ---
        elif mode == "color-out" or mode == "color-in":
            hue = int(progress * 200)
            return ["convert", img, "-modulate", f"100,100,{hue}"]

        # --- SHATTER ---
        elif mode == "shatter-out" or mode == "shatter-in":
            return ["convert", img, "-implode", str(progress * -2.0)]

        # --- MOSAIC ---
        elif mode == "mosaic-out" or mode == "mosaic-in":
            tile = max(1, int(progress * 100))
            return ["convert", img, "-scale", f"{tile}x{tile}!", "-scale", f"{width}x{height}!"]

        # --- GRADIENT ---
        elif mode == "gradient-out" or mode == "gradient-in":
            return ["convert", img, "-fill", "gradient:red-blue", "-colorize", str(int(progress * 100))]

        # --- NOISE ---
        elif mode == "noise-out" or mode == "noise-in":
            return ["convert", img, "-attenuate", str(progress), "+noise", "Gaussian"]

        # --- TWIST ---
        elif mode == "twist-out" or mode == "twist-in":
            angle = int(progress * 270)
            return ["convert", img, "-swirl", str(angle)]

        # --- FALLBACK ---
        else:
            return ["convert", img]

    def _get_frame_dir(self, tid):
        ram_dir = "/dev/shm"
        if os.path.exists(ram_dir) and os.access(ram_dir, os.W_OK):
            return os.path.join(ram_dir, f"bnm3_frames/{tid}")
        else:
            return f"/tmp/bnm3_frames/{tid}"

    def _cleanup_frames(self, frame_dir):
        if os.path.exists(frame_dir):
            subprocess.run(["rm", "-rf", frame_dir], check=False)

    def _play_frames(self, tmp_dir, set_wallpaper_func):
        if not os.path.exists(tmp_dir):
            return
        frames_list = sorted([os.path.join(tmp_dir, f)
                              for f in os.listdir(tmp_dir) if f.startswith("frame_")])
        total_frames = len(frames_list)

        for i, frame in enumerate(frames_list):
            self.logger.transition_progress(i + 1, total_frames)
            set_wallpaper_func(frame)
            time.sleep(self.speed / 1000.0)

    def apply(self, current_img, future_img, transition, set_wallpaper_func):
        """
        Dual transition:
        - Current wallpaper exits 100% → 0% using its exit mode
        - Future wallpaper enters 0% → 100% using its entry mode
        - Both are blended together per frame
        - Future becomes the new current at the end
        """

        tid = transition['id']
        entry_mode = transition['entry_mode']
        exit_mode = transition['exit_mode']

        self.logger.transition_start(transition['name'], tid)

        tmp_dir = self._get_frame_dir(f"dual_{tid}")
        subprocess.run(["rm", "-rf", tmp_dir], check=False)
        os.makedirs(tmp_dir, exist_ok=True)

        # Resize once
        resized_current = os.path.join(tmp_dir, "cur_resized.jpg")
        resized_future = os.path.join(tmp_dir, "fut_resized.jpg")
        subprocess.run(["convert", current_img, "-resize", f"{self.width}x{self.height}!", resized_current], check=True)
        subprocess.run(["convert", future_img, "-resize", f"{self.width}x{self.height}!", resized_future], check=True)

        total_frames = self.frames
        for t in range(total_frames):
            progress = t / (total_frames - 1) if total_frames > 1 else 1.0
            blend = int(progress * 100)
            out = os.path.join(tmp_dir, f"frame_{t:03d}.jpg")

            # Current wallpaper exit frame (100 → 0)
            out_exit = os.path.join(tmp_dir, f"exit_{t:03d}.jpg")
            exit_progress = 1 - progress
            cmd_exit = self._build_command(resized_current, exit_mode, exit_progress, self.width, self.height)

            # Future wallpaper entry frame (0 → 100)
            out_entry = os.path.join(tmp_dir, f"entry_{t:03d}.jpg")
            entry_progress = progress
            cmd_entry = self._build_command(resized_future, entry_mode, entry_progress, self.width, self.height)

            # Run exit and entry transforms in parallel
            p_exit = subprocess.Popen(cmd_exit + [out_exit])
            p_entry = subprocess.Popen(cmd_entry + [out_entry])
            p_exit.wait()
            p_entry.wait()

            # Blend exit + entry together
            subprocess.run(["composite", "-blend", str(blend), out_entry, out_exit, out], check=True)

        # Play frames
        self._play_frames(tmp_dir, set_wallpaper_func)

        # Final: set full-resolution future wallpaper
        set_wallpaper_func(future_img)

        self._cleanup_frames(tmp_dir)
        self.logger.transition_complete()

    def cleanup(self):
        """Clean up resources"""
        self.stop_background = True
        if self.current_wallpaper_exit_dir:
            self._cleanup_frames(self.current_wallpaper_exit_dir)
