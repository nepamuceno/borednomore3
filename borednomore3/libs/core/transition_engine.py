"""
Transition engine - handles transition selection and application
"""

import os
import subprocess
import random
import time


LOGIC_MAP = {
    1: ["slide-left", "slide-out-r", "slide-in-l"],
    2: ["slide-right", "slide-out-l", "slide-in-r"],
    3: ["slide-up", "slide-out-d", "slide-in-u"],
    4: ["slide-down", "slide-out-u", "slide-in-d"],
    7: ["spin-cw", "rot-out-ccw", "rot-in-cw"],
    8: ["spin-ccw", "rot-out-cw", "rot-in-ccw"],
    14: ["zoom-in-out", "zoom-out", "zoom-in"],
    21: ["swirl-cw", "swirl-out-ccw", "swirl-in-cw"],
    22: ["swirl-ccw", "swirl-out-cw", "swirl-in-ccw"],
    23: ["barrel-distort", "barrel-out", "barrel-in"],
    24: ["pinch", "pinch-out", "pinch-in"],
    25: ["wave-h", "wave-out-h", "wave-in-h"],
    28: ["fade", "fade-out", "fade-in"],
    32: ["pixelate", "pixel-out", "pixel-in"],
    33: ["blur-fade", "blur-out", "blur-in"],
    34: ["flip-h", "flip-out-h", "flip-in-h"],
    35: ["flip-v", "flip-out-v", "flip-in-v"],
    36: ["shear-x", "shear-out-x", "shear-in-x"],
    37: ["shear-y", "shear-out-y", "shear-in-y"],
    38: ["ripple", "ripple-out", "ripple-in"],
    39: ["checker", "checker-out", "checker-in"],
    40: ["glitch", "glitch-out", "glitch-in"],
    41: ["color-shift", "color-out", "color-in"],
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
        self.previous_exit_mode = None

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

        # SLIDE - Clean implementation
        if mode == "slide-in-l":
            offset = int((1 - progress) * width)
            return ["convert", img, "-roll", f"-{offset}+0"]
        elif mode == "slide-out-r":
            offset = int(progress * width)
            return ["convert", img, "-roll", f"+{offset}+0"]
        elif mode == "slide-in-r":
            offset = int((1 - progress) * width)
            return ["convert", img, "-roll", f"+{offset}+0"]
        elif mode == "slide-out-l":
            offset = int(progress * width)
            return ["convert", img, "-roll", f"-{offset}+0"]
        elif mode == "slide-in-u":
            offset = int((1 - progress) * height)
            return ["convert", img, "-roll", f"+0-{offset}"]
        elif mode == "slide-out-d":
            offset = int(progress * height)
            return ["convert", img, "-roll", f"+0+{offset}"]
        elif mode == "slide-in-d":
            offset = int((1 - progress) * height)
            return ["convert", img, "-roll", f"+0+{offset}"]
        elif mode == "slide-out-u":
            offset = int(progress * height)
            return ["convert", img, "-roll", f"+0-{offset}"]

        # SPIN - Reduced to 90 degrees
        elif mode == "rot-in-cw":
            angle = progress * 90
            return ["convert", img, "-background", "none", "-virtual-pixel", "transparent", "-distort", "SRT", str(angle)]
        elif mode == "rot-out-ccw":
            angle = -progress * 90
            return ["convert", img, "-background", "none", "-virtual-pixel", "transparent", "-distort", "SRT", str(angle)]
        elif mode == "rot-in-ccw":
            angle = -progress * 90
            return ["convert", img, "-background", "none", "-virtual-pixel", "transparent", "-distort", "SRT", str(angle)]
        elif mode == "rot-out-cw":
            angle = progress * 90
            return ["convert", img, "-background", "none", "-virtual-pixel", "transparent", "-distort", "SRT", str(angle)]

        # ZOOM - Fixed scale calculation
        elif mode == "zoom-in":
            scale = 0.1 + (progress * 0.9)
            return ["convert", img, "-resize", f"{int(width*scale)}x{int(height*scale)}!", "-gravity", "center", "-background", "black", "-extent", f"{width}x{height}"]
        elif mode == "zoom-out":
            scale = 0.1 + ((1 - progress) * 0.9)
            return ["convert", img, "-resize", f"{int(width*scale)}x{int(height*scale)}!", "-gravity", "center", "-background", "black", "-extent", f"{width}x{height}"]

        # SWIRL - Reduced to 120 degrees
        elif mode == "swirl-in-cw":
            angle = progress * 120
            return ["convert", img, "-swirl", str(angle)]
        elif mode == "swirl-out-ccw":
            angle = -progress * 120
            return ["convert", img, "-swirl", str(angle)]
        elif mode == "swirl-in-ccw":
            angle = -progress * 120
            return ["convert", img, "-swirl", str(angle)]
        elif mode == "swirl-out-cw":
            angle = progress * 120
            return ["convert", img, "-swirl", str(angle)]

        # BARREL - Fixed progression
        elif mode == "barrel-in":
            factor = (1 - progress) * 0.3
            return ["convert", img, "-distort", "Barrel", f"0.0 0.0 {factor}"]
        elif mode == "barrel-out":
            factor = progress * 0.3
            return ["convert", img, "-distort", "Barrel", f"0.0 0.0 {factor}"]

        # PINCH - Fixed progression
        elif mode == "pinch-in":
            factor = (1 - progress) * 0.8
            return ["convert", img, "-implode", str(factor)]
        elif mode == "pinch-out":
            factor = progress * 0.8
            return ["convert", img, "-implode", str(factor)]

        # WAVE - Different wavelengths
        elif mode == "wave-in-h":
            amp = int((1 - progress) * 30)
            return ["convert", img, "-wave", f"{amp}x{width//15}"]
        elif mode == "wave-out-h":
            amp = int(progress * 30)
            return ["convert", img, "-wave", f"{amp}x{width//15}"]

        # FADE
        elif mode == "fade-in":
            opacity = max(0.01, progress)
            return ["convert", img, "-alpha", "set", "-channel", "A", "-evaluate", "multiply", str(opacity), "+channel"]
        elif mode == "fade-out":
            opacity = max(0.01, 1 - progress)
            return ["convert", img, "-alpha", "set", "-channel", "A", "-evaluate", "multiply", str(opacity), "+channel"]

        # PIXELATE - Fixed progression
        elif mode == "pixel-in":
            coarse = max(2, int(width * (1 - progress) * 0.05))
            return ["convert", img, "-scale", f"{coarse}x{coarse}!", "-scale", f"{width}x{height}!"]
        elif mode == "pixel-out":
            coarse = max(2, int(width * progress * 0.05))
            return ["convert", img, "-scale", f"{coarse}x{coarse}!", "-scale", f"{width}x{height}!"]

        # BLUR
        elif mode == "blur-in":
            radius = (1 - progress) * 10
            return ["convert", img, "-blur", f"0x{radius}"]
        elif mode == "blur-out":
            radius = progress * 10
            return ["convert", img, "-blur", f"0x{radius}"]

        # FLIP - Gradual using scale
        elif mode == "flip-in-h":
            scale_x = abs(progress - 0.5) * 2
            return ["convert", img, "-scale", f"{int(width*scale_x)}x{height}!", "-scale", f"{width}x{height}!"]
        elif mode == "flip-out-h":
            scale_x = abs((1-progress) - 0.5) * 2
            return ["convert", img, "-scale", f"{int(width*scale_x)}x{height}!", "-scale", f"{width}x{height}!"]
        elif mode == "flip-in-v":
            scale_y = abs(progress - 0.5) * 2
            return ["convert", img, "-scale", f"{width}x{int(height*scale_y)}!", "-scale", f"{width}x{height}!"]
        elif mode == "flip-out-v":
            scale_y = abs((1-progress) - 0.5) * 2
            return ["convert", img, "-scale", f"{width}x{int(height*scale_y)}!", "-scale", f"{width}x{height}!"]

        # SHEAR - Reduced angle, transparent background
        elif mode == "shear-in-x":
            shear = int((1 - progress) * 15)
            return ["convert", img, "-background", "none", "-virtual-pixel", "transparent", "-shear", f"{shear}x0"]
        elif mode == "shear-out-x":
            shear = int(progress * 15)
            return ["convert", img, "-background", "none", "-virtual-pixel", "transparent", "-shear", f"{shear}x0"]
        elif mode == "shear-in-y":
            shear = int((1 - progress) * 15)
            return ["convert", img, "-background", "none", "-virtual-pixel", "transparent", "-shear", f"0x{shear}"]
        elif mode == "shear-out-y":
            shear = int(progress * 15)
            return ["convert", img, "-background", "none", "-virtual-pixel", "transparent", "-shear", f"0x{shear}"]

        # RIPPLE - Different wavelength from wave
        elif mode == "ripple-in":
            amp = int((1 - progress) * 40)
            return ["convert", img, "-wave", f"{amp}x{width//8}"]
        elif mode == "ripple-out":
            amp = int(progress * 40)
            return ["convert", img, "-wave", f"{amp}x{width//8}"]

        # CHECKER - Fixed progression
        elif mode == "checker-in":
            size = max(10, int((1 - progress) * 50))
            return ["convert", img, "-scale", f"{size}x{size}!", "-scale", f"{width}x{height}!"]
        elif mode == "checker-out":
            size = max(10, int(progress * 50))
            return ["convert", img, "-scale", f"{size}x{size}!", "-scale", f"{width}x{height}!"]

        # GLITCH
        elif mode == "glitch-in":
            spread = int((1 - progress) * 20)
            return ["convert", img, "-spread", str(max(1, spread))]
        elif mode == "glitch-out":
            spread = int(progress * 20)
            return ["convert", img, "-spread", str(max(1, spread))]

        # COLOR SHIFT
        elif mode == "color-in":
            hue = int((1 - progress) * 100)
            return ["convert", img, "-modulate", f"100,{100 + int(progress * 50)},{100 + hue}"]
        elif mode == "color-out":
            hue = int(progress * 100)
            return ["convert", img, "-modulate", f"100,{150 - int(progress * 50)},{100 + hue}"]

        # SHATTER
        elif mode == "shatter-in":
            factor = (1 - progress) * 1.2
            return ["convert", img, "-implode", str(-factor)]
        elif mode == "shatter-out":
            factor = progress * 1.2
            return ["convert", img, "-implode", str(-factor)]

        # MOSAIC
        elif mode == "mosaic-in":
            tile = max(10, int((1 - progress) * 60))
            return ["convert", img, "-scale", f"{tile}x{tile}!", "-scale", f"{width}x{height}!"]
        elif mode == "mosaic-out":
            tile = max(10, int(progress * 60))
            return ["convert", img, "-scale", f"{tile}x{tile}!", "-scale", f"{width}x{height}!"]

        # GRADIENT - Using evaluate for better control
        elif mode == "gradient-in":
            pct = int((1 - progress) * 100)
            return ["convert", img, "(", "+clone", "-fill", "gray", "-colorize", "100", ")", "-compose", "blend", "-define", f"compose:args={pct}", "-composite"]
        elif mode == "gradient-out":
            pct = int(progress * 100)
            return ["convert", img, "(", "+clone", "-fill", "gray", "-colorize", "100", ")", "-compose", "blend", "-define", f"compose:args={pct}", "-composite"]

        # NOISE
        elif mode == "noise-in":
            atten = max(0.1, (1 - progress) * 3)
            return ["convert", img, "-attenuate", str(atten), "+noise", "Gaussian"]
        elif mode == "noise-out":
            atten = max(0.1, progress * 3)
            return ["convert", img, "-attenuate", str(atten), "+noise", "Gaussian"]

        # TWIST - Reduced to 150 degrees
        elif mode == "twist-in":
            angle = int((1 - progress) * 150)
            return ["convert", img, "-swirl", str(angle)]
        elif mode == "twist-out":
            angle = int(progress * 150)
            return ["convert", img, "-swirl", str(angle)]

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
        - Current wallpaper exits 100% → 0% using exit mode (reversed from how it came in)
        - Future wallpaper enters 0% → 100% using entry mode
        - Both blended together per frame
        """

        tid = transition['id']
        entry_mode = transition['entry_mode']
        
        exit_mode = self.previous_exit_mode if self.previous_exit_mode else transition['exit_mode']
        self.previous_exit_mode = transition['exit_mode']

        self.logger.transition_start(transition['name'], tid)

        tmp_dir = self._get_frame_dir(f"dual_{tid}")
        subprocess.run(["rm", "-rf", tmp_dir], check=False)
        os.makedirs(tmp_dir, exist_ok=True)

        resized_current = os.path.join(tmp_dir, "cur_resized.jpg")
        resized_future = os.path.join(tmp_dir, "fut_resized.jpg")
        subprocess.run(["convert", current_img, "-resize", f"{self.width}x{self.height}!", resized_current], check=True)
        subprocess.run(["convert", future_img, "-resize", f"{self.width}x{self.height}!", resized_future], check=True)

        total_frames = self.frames
        for t in range(total_frames):
            progress = t / (total_frames - 1) if total_frames > 1 else 1.0
            blend = int(progress * 100)
            out = os.path.join(tmp_dir, f"frame_{t:03d}.jpg")

            out_exit = os.path.join(tmp_dir, f"exit_{t:03d}.jpg")
            exit_progress = 1 - progress
            cmd_exit = self._build_command(resized_current, exit_mode, exit_progress, self.width, self.height)

            out_entry = os.path.join(tmp_dir, f"entry_{t:03d}.jpg")
            entry_progress = progress
            cmd_entry = self._build_command(resized_future, entry_mode, entry_progress, self.width, self.height)

            subprocess.run(cmd_exit + [out_exit], check=True, capture_output=True)
            subprocess.run(cmd_entry + [out_entry], check=True, capture_output=True)

            subprocess.run(["composite", "-blend", str(blend), out_entry, out_exit, out], check=True, capture_output=True)

        self._play_frames(tmp_dir, set_wallpaper_func)
        set_wallpaper_func(future_img)

        self._cleanup_frames(tmp_dir)
        self.logger.transition_complete()

    def cleanup(self):
        pass
