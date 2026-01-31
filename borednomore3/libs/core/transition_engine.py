"""
Transition engine - Hollywood-Grade Cinema Quality
Individual transitions with professional fine-tuning and performance optimization
"""

import os
import subprocess
import random
import time
import math


LOGIC_MAP = {
    1: ["slide-left", "slide-out-r", "slide-in-l"],
    2: ["slide-right", "slide-out-l", "slide-in-r"],
    3: ["slide-up", "slide-out-d", "slide-in-u"],
    4: ["slide-down", "slide-out-u", "slide-in-d"],
    7: ["spin-cw", "rot-out-ccw", "rot-in-cw"],
    8: ["spin-ccw", "rot-out-cw", "rot-in-ccw"],
    14: ["zoom-in-out", "zoom-out", "zoom-in"],
    21: ["swirl-cw", "swirl-out-cw", "swirl-in-cw"],
    22: ["swirl-ccw", "swirl-out-ccw", "swirl-in-ccw"],
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
    """Hollywood-grade transition engine with individual functions"""

    def __init__(self, transitions, randomize, frames, speed, keep_image, desktop_info, logger):
        self.logger = logger
        self.frames = frames
        self.speed = speed
        self.keep_image = keep_image
        self.desktop_info = desktop_info
        self.width = desktop_info['width']
        self.height = desktop_info['height']
        
        # PERFORMANCE: Calculate optimal processing resolution
        self.work_width, self.work_height = self._calculate_work_resolution()
        self.scale_factor = self.width / self.work_width
        
        self.logger.debug(f"Display: {self.width}x{self.height}, Processing: {self.work_width}x{self.work_height}, Speedup: {self.scale_factor:.1f}x")

        if transitions:
            self.transition_list = self._parse_transitions(transitions)
        else:
            self.transition_list = list(TRANSITIONS.keys())

        self.randomize = randomize
        self.current_index = 0
        self.previous_exit_mode = None

    def _calculate_work_resolution(self):
        """Calculate optimal processing resolution for speed"""
        pixels = self.width * self.height
        aspect = self.width / self.height
        
        if pixels >= 3840 * 2160:  # 4K or higher
            work_h = 1080
        elif pixels >= 2560 * 1440:  # QHD
            work_h = 720
        elif pixels >= 1920 * 1080:  # Full HD
            work_h = 720
        else:  # Below 1080p
            return self.width, self.height
            
        work_w = int(work_h * aspect)
        work_w = work_w - (work_w % 2)
        work_h = work_h - (work_h % 2)
        
        return work_w, work_h

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
        if self.randomize:
            category = random.choice(list(CATEGORY_MAP.keys()))
            tid = random.choice(CATEGORY_MAP[category])
        else:
            tid = self.transition_list[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.transition_list)

        transition_data = TRANSITIONS[tid]
        return {
            'id': tid,
            'name': transition_data[0],
            'exit_mode': transition_data[1],
            'entry_mode': transition_data[2]
        }

    # === EASING FUNCTIONS ===
    
    def _ease_damped_spring(self, progress):
        """Hollywood-grade spring physics"""
        if progress < 0.15:
            return -0.02 * math.sin((progress / 0.15) * (math.pi / 2))
        if progress <= 0.9:
            t = (progress - 0.15) / 0.75
            return 1 - math.pow(1 - t, 5)
        t_settle = (progress - 0.9) / 0.1
        return 1.0 + 0.008 * math.sin(t_settle * math.pi * 3) * math.exp(-t_settle * 4)

    def _ease_smooth(self, progress):
        """Cinematic quintic ease"""
        if progress < 0.5:
            return 16 * progress ** 5
        else:
            t = progress - 1
            return 1 + 16 * t ** 5
            
    def _gamma_fade_in(self, progress):
        """Filmic sigmoid fade in"""
        if progress < 0.5:
            return 4 * progress ** 3
        else:
            t = (2 * progress) - 2
            return 0.5 * (t * t * t + 2)

    def _gamma_fade_out(self, progress):
        """Filmic sigmoid fade out"""
        t = 1.0 - progress
        if t > 0.5:
            return 1.0 - (4 * (1.0 - t) ** 3)
        else:
            return 4 * t ** 3

    def _s_curve_blend(self, progress):
        """Perceptual cross-dissolve"""
        blend_factor = 0.5 * (1.0 - math.cos(progress * math.pi))
        return int(blend_factor * 100)

    # === HOLLYWOOD-GRADE TRANSITION FUNCTIONS ===
    
    def _mode_slide_in_l(self, img, progress):
        eased = self._ease_damped_spring(progress)
        offset = int((1 - eased) * self.work_width)
        # HOLLYWOOD: Light directional blur for motion feel
        return ["convert", img, "-roll", f"-{offset}+0", "-blur", "0.3x0.3"]

    def _mode_slide_out_r(self, img, progress):
        eased = self._ease_damped_spring(progress)
        offset = int(eased * self.work_width)
        return ["convert", img, "-roll", f"+{offset}+0", "-blur", "0.3x0.3"]

    def _mode_slide_in_r(self, img, progress):
        eased = self._ease_damped_spring(progress)
        offset = int((1 - eased) * self.work_width)
        return ["convert", img, "-roll", f"+{offset}+0", "-blur", "0.3x0.3"]

    def _mode_slide_out_l(self, img, progress):
        eased = self._ease_damped_spring(progress)
        offset = int(eased * self.work_width)
        return ["convert", img, "-roll", f"-{offset}+0", "-blur", "0.3x0.3"]

    def _mode_slide_in_u(self, img, progress):
        eased = self._ease_damped_spring(progress)
        offset = int((1 - eased) * self.work_height)
        return ["convert", img, "-roll", f"+0-{offset}", "-blur", "0.3x0.3"]

    def _mode_slide_out_d(self, img, progress):
        eased = self._ease_damped_spring(progress)
        offset = int(eased * self.work_height)
        return ["convert", img, "-roll", f"+0+{offset}", "-blur", "0.3x0.3"]

    def _mode_slide_in_d(self, img, progress):
        eased = self._ease_damped_spring(progress)
        offset = int((1 - eased) * self.work_height)
        return ["convert", img, "-roll", f"+0+{offset}", "-blur", "0.3x0.3"]

    def _mode_slide_out_u(self, img, progress):
        eased = self._ease_damped_spring(progress)
        offset = int(eased * self.work_height)
        return ["convert", img, "-roll", f"+0-{offset}", "-blur", "0.3x0.3"]

    def _mode_rot_in_cw(self, img, progress):
        eased = self._ease_smooth(progress)
        scale = 0.85 + (eased * 0.15)
        angle = eased * 180
        # HOLLYWOOD: Add vignette during rotation for depth
        vignette = int(abs(math.sin(eased * math.pi)) * 15)
        return ["convert", img, "-resize", f"{int(self.work_width*scale)}x{int(self.work_height*scale)}!", "-gravity", "south", "-background", "black", "-virtual-pixel", "edge", "-distort", "SRT", f"{self.work_width/2},{self.work_height} 1.0 {angle}", "-vignette", f"0x{vignette}", "-extent", f"{self.work_width}x{self.work_height}"]

    def _mode_rot_out_ccw(self, img, progress):
        eased = self._ease_smooth(progress)
        scale = 1.0 - (eased * 0.2)
        angle = -eased * 180
        vignette = int(abs(math.sin(eased * math.pi)) * 15)
        return ["convert", img, "-resize", f"{int(self.work_width*scale)}x{int(self.work_height*scale)}!", "-gravity", "south", "-background", "black", "-virtual-pixel", "edge", "-distort", "SRT", f"{self.work_width/2},{self.work_height} 1.0 {angle}", "-vignette", f"0x{vignette}", "-extent", f"{self.work_width}x{self.work_height}"]

    def _mode_rot_in_ccw(self, img, progress):
        eased = self._ease_smooth(progress)
        scale = 0.85 + (eased * 0.15)
        angle = -eased * 180
        vignette = int(abs(math.sin(eased * math.pi)) * 15)
        return ["convert", img, "-resize", f"{int(self.work_width*scale)}x{int(self.work_height*scale)}!", "-gravity", "south", "-background", "black", "-virtual-pixel", "edge", "-distort", "SRT", f"{self.work_width/2},{self.work_height} 1.0 {angle}", "-vignette", f"0x{vignette}", "-extent", f"{self.work_width}x{self.work_height}"]

    def _mode_rot_out_cw(self, img, progress):
        eased = self._ease_smooth(progress)
        scale = 1.0 - (eased * 0.2)
        angle = eased * 180
        vignette = int(abs(math.sin(eased * math.pi)) * 15)
        return ["convert", img, "-resize", f"{int(self.work_width*scale)}x{int(self.work_height*scale)}!", "-gravity", "south", "-background", "black", "-virtual-pixel", "edge", "-distort", "SRT", f"{self.work_width/2},{self.work_height} 1.0 {angle}", "-vignette", f"0x{vignette}", "-extent", f"{self.work_width}x{self.work_height}"]

    def _mode_zoom_in(self, img, progress):
        eased = self._ease_smooth(progress)
        scale = 0.4 + (eased * 0.6)
        # HOLLYWOOD: Vignette pulse with zoom
        vignette = int(abs(0.5 - eased) * 40)
        return ["convert", img, "-resize", f"{int(self.work_width*scale)}x{int(self.work_height*scale)}!", "-gravity", "center", "-background", "black", "-vignette", f"0x{vignette}", "-extent", f"{self.work_width}x{self.work_height}"]

    def _mode_zoom_out(self, img, progress):
        eased = self._ease_smooth(progress)
        scale = 1.0 - (eased * 0.6)
        vignette = int(abs(0.5 - eased) * 40)
        return ["convert", img, "-resize", f"{int(self.work_width*scale)}x{int(self.work_height*scale)}!", "-gravity", "center", "-background", "black", "-vignette", f"0x{vignette}", "-extent", f"{self.work_width}x{self.work_height}"]
        
    def _mode_swirl_in_cw(self, img, progress):
        eased = self._ease_smooth(progress)
        # HOLLYWOOD: Increased to 180 degrees for dramatic effect
        angle = eased * 180
        # Saturation boost at peak swirl
        sat = 100 + int(abs(math.sin(eased * math.pi)) * 30)
        return ["convert", img, "-swirl", str(angle), "-modulate", f"100,{sat},100"]

    def _mode_swirl_out_cw(self, img, progress):
        eased = self._ease_smooth(1 - progress)
        angle = eased * 180
        sat = 100 + int(abs(math.sin(eased * math.pi)) * 30)
        return ["convert", img, "-swirl", str(angle), "-modulate", f"100,{sat},100"]

    def _mode_swirl_in_ccw(self, img, progress):
        eased = self._ease_smooth(progress)
        angle = -eased * 180
        sat = 100 + int(abs(math.sin(eased * math.pi)) * 30)
        return ["convert", img, "-swirl", str(angle), "-modulate", f"100,{sat},100"]

    def _mode_swirl_out_ccw(self, img, progress):
        eased = self._ease_smooth(1 - progress)
        angle = -eased * 180
        sat = 100 + int(abs(math.sin(eased * math.pi)) * 30)
        return ["convert", img, "-swirl", str(angle), "-modulate", f"100,{sat},100"]

    def _mode_barrel_in(self, img, progress):
        eased = self._ease_smooth(1 - progress)
        factor = eased * 0.5
        # HOLLYWOOD: Stronger vignette + edge blur for lens feel
        vignette = int(eased * 50)
        edge_blur = eased * 2
        return ["convert", img, "-distort", "Barrel", f"0.0 0.0 {factor} 1.0", "-vignette", f"0x{vignette}", "-virtual-pixel", "mirror", "-blur", f"0x{edge_blur}"]

    def _mode_barrel_out(self, img, progress):
        eased = self._ease_smooth(progress)
        factor = eased * 0.5
        vignette = int(eased * 50)
        edge_blur = eased * 2
        return ["convert", img, "-distort", "Barrel", f"0.0 0.0 {factor} 1.0", "-vignette", f"0x{vignette}", "-virtual-pixel", "mirror", "-blur", f"0x{edge_blur}"]

    def _mode_pinch_in(self, img, progress):
        eased = self._ease_smooth(progress)
        # HOLLYWOOD: Increased factor + vignette + desaturation for "black hole"
        factor = (1.0 - eased) * 1.5
        vignette = int((1 - eased) * 40)
        desat = 100 - int((1 - eased) * 30)
        return ["convert", img, "-implode", str(factor), "-vignette", f"0x{vignette}", "-modulate", f"100,{desat},100"]

    def _mode_pinch_out(self, img, progress):
        eased = self._ease_smooth(progress)
        factor = eased * 1.5
        vignette = int(eased * 40)
        desat = 100 - int(eased * 30)
        return ["convert", img, "-implode", str(factor), "-vignette", f"0x{vignette}", "-modulate", f"100,{desat},100"]

    def _mode_wave_in_h(self, img, progress):
        eased = self._ease_smooth(progress)
        amp = int((1.0 - eased) * 35)
        wl = self.work_width // max(1, int(10 + (eased * 15)))
        return ["convert", img, "-wave", f"{amp}x{wl}"]

    def _mode_wave_out_h(self, img, progress):
        eased = self._ease_smooth(progress)
        amp = int(eased * 35)
        wl = self.work_width // max(1, int(25 - (eased * 15)))
        return ["convert", img, "-wave", f"{amp}x{wl}"]

    def _mode_fade_in(self, img, progress):
        alpha = self._gamma_fade_in(progress)
        return ["convert", img, "-alpha", "set", "-channel", "A", "-evaluate", "set", f"{alpha*100}%", "+channel"]

    def _mode_fade_out(self, img, progress):
        alpha = self._gamma_fade_out(progress)
        return ["convert", img, "-alpha", "set", "-channel", "A", "-evaluate", "set", f"{alpha*100}%", "+channel"]

    def _mode_pixel_in(self, img, progress):
        eased = self._ease_smooth(progress)
        coarse = max(1, int(28 * (1.0 - eased)))
        if coarse <= 1: 
            return ["convert", img]
        # HOLLYWOOD: Add dither + posterization at high pixelation
        cmd = ["convert", img, "-scale", f"{self.work_width//coarse}x{self.work_height//coarse}!", "-scale", f"{self.work_width}x{self.work_height}!"]
        if coarse > 10:
            cmd.extend(["-ordered-dither", "o2x2", "-posterize", "6"])
        return cmd
    
    def _mode_pixel_out(self, img, progress):
        eased = self._ease_smooth(progress)
        coarse = max(1, int(28 * eased))
        if coarse <= 1: 
            return ["convert", img]
        cmd = ["convert", img, "-scale", f"{self.work_width//coarse}x{self.work_height//coarse}!", "-scale", f"{self.work_width}x{self.work_height}!"]
        if coarse > 10:
            cmd.extend(["-ordered-dither", "o2x2", "-posterize", "6"])
        return cmd

    def _mode_blur_in(self, img, progress):
        eased = 1.0 - self._ease_smooth(progress)
        # HOLLYWOOD: Add vignette at peak blur for bokeh effect
        vignette = int(max(0, eased - 0.6) * 120) if eased > 0.6 else 0
        return ["convert", img, "-blur", f"0x{eased * 15}", "-vignette", f"0x{vignette}"]

    def _mode_blur_out(self, img, progress):
        eased = self._ease_smooth(progress)
        vignette = int(max(0, eased - 0.6) * 120) if eased > 0.6 else 0
        return ["convert", img, "-blur", f"0x{eased * 15}", "-vignette", f"0x{vignette}"]

    def _mode_flip_in_h(self, img, progress):
        eased = self._ease_smooth(progress)
        p = eased * self.work_width * 0.35
        # HOLLYWOOD: Add blur at mid-flip + slight shadow
        cmd = ["convert", img, "-virtual-pixel", "black", "-background", "black", "-distort", "Perspective", f"0,0 {p},0  0,{self.work_height} {p},{self.work_height}  {self.work_width},0 {self.work_width-p},0  {self.work_width},{self.work_height} {self.work_width-p},{self.work_height}"]
        if 0.4 < eased < 0.6:
            cmd.extend(["-blur", "0x2"])
        return cmd

    def _mode_flip_out_h(self, img, progress):
        eased = self._ease_smooth(progress)
        p = eased * self.work_width * 0.35
        # HOLLYWOOD: Increased brightness drop for depth
        brightness = 100 - (eased * 60)
        cmd = ["convert", img, "-virtual-pixel", "black", "-background", "black", "-distort", "Perspective", f"0,0 {p},0  0,{self.work_height} {p},{self.work_height}  {self.work_width},0 {self.work_width-p},0  {self.work_width},{self.work_height} {self.work_width-p},{self.work_height}", "-modulate", f"{brightness},100,100"]
        if 0.4 < eased < 0.6:
            cmd.extend(["-blur", "0x2"])
        return cmd
                
    def _mode_flip_in_v(self, img, progress):
        eased = self._ease_smooth(progress)
        p = eased * self.work_height * 0.35
        cmd = ["convert", img, "-virtual-pixel", "black", "-background", "black", "-distort", "Perspective", f"0,0 0,{p}  {self.work_width},0 {self.work_width},{p}  0,{self.work_height} 0,{self.work_height-p}  {self.work_width},{self.work_height} {self.work_width},{self.work_height-p}"]
        if 0.4 < eased < 0.6:
            cmd.extend(["-blur", "0x2"])
        return cmd

    def _mode_flip_out_v(self, img, progress):
        eased = self._ease_smooth(progress)
        p = eased * self.work_height * 0.35
        brightness = 100 - (eased * 60)
        cmd = ["convert", img, "-virtual-pixel", "black", "-background", "black", "-distort", "Perspective", f"0,0 0,{p}  {self.work_width},0 {self.work_width},{p}  0,{self.work_height} 0,{self.work_height-p}  {self.work_width},{self.work_height} {self.work_width},{self.work_height-p}", "-modulate", f"{brightness},100,100"]
        if 0.4 < eased < 0.6:
            cmd.extend(["-blur", "0x2"])
        return cmd

    def _mode_shear_in_x(self, img, progress):
        eased = self._ease_smooth(progress)
        # HOLLYWOOD: Reduced shear angle + alpha for less jarring
        shear_val = (1 - eased) * 8
        alpha = 0.7 + eased * 0.3
        return ["convert", img, "-background", "black", "-virtual-pixel", "edge", "-shear", f"{shear_val}x0", "-alpha", "set", "-channel", "A", "-evaluate", "multiply", str(alpha), "+channel"]

    def _mode_shear_out_x(self, img, progress):
        eased = self._ease_smooth(progress)
        shear_val = eased * 8
        alpha = 1.0 - eased * 0.3
        return ["convert", img, "-background", "black", "-virtual-pixel", "edge", "-shear", f"{shear_val}x0", "-alpha", "set", "-channel", "A", "-evaluate", "multiply", str(alpha), "+channel"]

    def _mode_shear_in_y(self, img, progress):
        eased = self._ease_smooth(progress)
        shear_val = (1 - eased) * 8
        alpha = 0.7 + eased * 0.3
        return ["convert", img, "-background", "black", "-virtual-pixel", "edge", "-shear", f"0x{shear_val}", "-alpha", "set", "-channel", "A", "-evaluate", "multiply", str(alpha), "+channel"]

    def _mode_shear_out_y(self, img, progress):
        eased = self._ease_smooth(progress)
        shear_val = eased * 8
        alpha = 1.0 - eased * 0.3
        return ["convert", img, "-background", "black", "-virtual-pixel", "edge", "-shear", f"0x{shear_val}", "-alpha", "set", "-channel", "A", "-evaluate", "multiply", str(alpha), "+channel"]

    def _mode_ripple_in(self, img, progress):
        eased = self._ease_smooth(progress)
        amp = int((1.0 - eased) * 45)
        wl = self.work_width // max(1, int(5 + (eased * 12)))
        return ["convert", img, "-wave", f"{amp}x{wl}"]

    def _mode_ripple_out(self, img, progress):
        eased = self._ease_smooth(progress)
        amp = int(eased * 45)
        wl = self.work_width // max(1, int(17 - (eased * 12)))
        return ["convert", img, "-wave", f"{amp}x{wl}"]

    def _mode_checker_in(self, img, progress):
        eased = self._ease_smooth(progress)
        levels = max(2, int(2 + (eased * 12)))
        return ["convert", img, "-ordered-dither", "o4x4", "-posterize", str(levels)]

    def _mode_checker_out(self, img, progress):
        eased = self._ease_smooth(progress)
        levels = max(2, int(14 - (eased * 12)))
        return ["convert", img, "-ordered-dither", "o4x4", "-posterize", str(levels)]

    def _mode_glitch_in(self, img, progress):
        eased = 1.0 - self._ease_smooth(progress)
        r_shift = int(eased * 40)
        g_shift = int(eased * 20)
        b_shift = int(eased * 30)
        
        # IMv6 Robust Method: 
        # Shift channels using -channel masks without breaking the stack
        cmd = [
            "convert", img,
            "-channel", "R", "-roll", f"{r_shift}+0",
            "-channel", "G", "-roll", f"-{g_shift}+0",
            "-channel", "B", "-roll", f"0+{b_shift}",
            "+channel" # This resets the channel mask so noise/output works
        ]
        
        if eased > 0.5:
            cmd.extend(["-attenuate", "0.5", "+noise", "Impulse"])
        return cmd
                
    def _mode_glitch_out(self, img, progress):
        eased = self._ease_smooth(progress)
        r_shift = int(eased * 45)
        g_shift = int(eased * 25)
        b_shift = int(eased * 35)
        
        cmd = [
            "convert", img,
            "-channel", "R", "-roll", f"-{r_shift}+0",
            "-channel", "G", "-roll", f"+{g_shift}+0",
            "-channel", "B", "-roll", f"0-{b_shift}",
            "+channel"
        ]
        
        if eased > 0.5:
            cmd.extend(["-attenuate", "0.5", "+noise", "Impulse"])
        return cmd
        
    def _mode_color_in(self, img, progress):
        eased = self._ease_smooth(progress)
        # HOLLYWOOD: Reduced saturation + gamma for film look
        sat = 100 + (1.0 - eased) * 60
        bright = 100 + (1.0 - eased) * 15
        gamma = 1.0 + (1.0 - eased) * 0.3
        hue = 100 - (1.0 - eased) * 5
        return ["convert", img, "-modulate", f"{bright},{sat},{hue}", "-gamma", str(gamma)]

    def _mode_color_out(self, img, progress):
        eased = self._ease_smooth(progress)
        sat = 100 + eased * 60
        bright = 100 + eased * 20
        gamma = 1.0 + eased * 0.3
        return ["convert", img, "-modulate", f"{bright},{sat},100", "-gamma", str(gamma)]

    def _mode_shatter_in(self, img, progress):
        eased = 1.0 - self._ease_smooth(progress)
        tilt = eased * 15
        # HOLLYWOOD: Add spread + desaturation for fragment feel
        spread = int(eased * 8)
        desat = 100 - int(eased * 20)
        return ["convert", img, "-distort", "SRT", f"{tilt}", "-spread", str(max(1, spread)), "-modulate", f"100,{desat},100"]

    def _mode_shatter_out(self, img, progress):
        eased = self._ease_smooth(progress)
        fall = int(eased * self.work_height * 0.4)
        rotate = eased * 12
        spread = int(eased * 8)
        desat = 100 - int(eased * 20)
        return ["convert", img, "-roll", f"+0+{fall}", "-distort", "SRT", f"{rotate}", "-spread", str(max(1, spread)), "-modulate", f"100,{desat},100"]

    def _mode_mosaic_in(self, img, progress):
        eased = self._ease_smooth(progress)
        tile_size = max(1, int(25 * (1.0 - eased)))
        if tile_size <= 1: 
            return ["convert", img]
        # HOLLYWOOD: Increased paint + posterize for artistic feel
        posterize_lvl = int(8 + eased * 8)
        return ["convert", img, "-resize", "30%", "-spread", str(tile_size // 3), "-paint", "3", "+dither", "-posterize", str(posterize_lvl), "-resize", f"{self.work_width}x{self.work_height}!"]
                
    def _mode_mosaic_out(self, img, progress):
        eased = self._ease_smooth(progress)
        tile_size = max(1, int(25 * eased))
        if tile_size <= 1: 
            return ["convert", img]
        posterize_lvl = int(16 - eased * 8)
        return ["convert", img, "-resize", "30%", "-spread", str(tile_size // 3), "-paint", "3", "+dither", "-posterize", str(posterize_lvl), "-resize", f"{self.work_width}x{self.work_height}!"]

    def _mode_gradient_in(self, img, progress):
        eased = 1.0 - self._ease_smooth(progress)
        red_tint = int(eased * 50)
        gamma = 1.0 + (eased * 0.4)
        return ["convert", img, "-fill", "orange", "-colorize", f"{red_tint}%", "-gamma", str(gamma)]

    def _mode_gradient_out(self, img, progress):
        eased = self._ease_smooth(progress)
        wash = int(eased * 60)
        return ["convert", img, "-fill", "white", "-colorize", f"{wash}%"]

    def _mode_noise_in(self, img, progress):
        eased = 1.0 - self._ease_smooth(progress)
        # HOLLYWOOD: Impulse noise for film grain + desaturation
        noise_level = eased * 4
        desat = 100 - int(eased * 15)
        return ["convert", img, "-attenuate", str(noise_level), "+noise", "Impulse", "-modulate", f"100,{desat},100"]

    def _mode_noise_out(self, img, progress):
        eased = self._ease_smooth(progress)
        noise_level = eased * 6
        desat = 100 - int(eased * 15)
        return ["convert", img, "-attenuate", str(noise_level), "+noise", "Impulse", "-modulate", f"100,{desat},100"]

    def _mode_twist_in(self, img, progress):
        eased = 1.0 - self._ease_smooth(progress)
        # HOLLYWOOD: Increased swirl angle + rotation for dramatic twist
        angle = eased * 150
        rotation = eased * 5
        return ["convert", img, "-swirl", str(angle), "-wave", f"{int(eased*25)}x{self.work_width//5}", "-distort", "SRT", str(rotation)]

    def _mode_twist_out(self, img, progress):
        eased = self._ease_smooth(progress)
        angle = eased * 180
        rotation = eased * 5
        return ["convert", img, "-swirl", str(angle), "-wave", f"{int(eased*40)}x{self.work_width//10}", "-distort", "SRT", str(rotation)]

    def _build_command(self, img, mode, progress, width, height):
        """Route to individual transition functions"""
        func_name = f"_mode_{mode.replace('-', '_')}"
        if hasattr(self, func_name):
            return getattr(self, func_name)(img, progress)
        return ["convert", img]

    # === INFRASTRUCTURE ===

    def _get_frame_dir(self, tid):
        ram_dir = "/dev/shm"
        if os.path.exists(ram_dir) and os.access(ram_dir, os.W_OK):
            return os.path.join(ram_dir, f"bnm3_frames/{tid}")
        return f"/tmp/bnm3_frames/{tid}"

    def _cleanup_frames(self, frame_dir):
        if os.path.exists(frame_dir):
            subprocess.run(["rm", "-rf", frame_dir], check=False)

    def _play_frames(self, tmp_dir, set_wallpaper_func):
        if not os.path.exists(tmp_dir): 
            return
        frames_list = sorted([os.path.join(tmp_dir, f) for f in os.listdir(tmp_dir) if f.startswith("frame_")])
        total_frames = len(frames_list)
        for i, frame in enumerate(frames_list):
            self.logger.transition_progress(i + 1, total_frames)
            set_wallpaper_func(frame)
            time.sleep(self.speed / 1000.0)

    def apply(self, current_img, future_img, transition, set_wallpaper_func):
        """Hollywood-grade transition with performance optimization"""
        tid = transition['id']
        entry_mode = transition['entry_mode']
        exit_mode = self.previous_exit_mode if self.previous_exit_mode else transition['exit_mode']
        self.previous_exit_mode = transition['entry_mode']

        self.logger.transition_start(transition['name'], tid)
        tmp_dir = self._get_frame_dir(f"dual_{tid}")
        subprocess.run(["rm", "-rf", tmp_dir], check=False)
        os.makedirs(tmp_dir, exist_ok=True)

        # PERFORMANCE: Resize to work resolution ONCE
        work_cur = os.path.join(tmp_dir, "cur.jpg")
        work_fut = os.path.join(tmp_dir, "fut.jpg")
        subprocess.run(["convert", current_img, "-resize", f"{self.work_width}x{self.work_height}!", "-quality", "95", work_cur], check=True)
        subprocess.run(["convert", future_img, "-resize", f"{self.work_width}x{self.work_height}!", "-quality", "95", work_fut], check=True)

        # Generate frames at work resolution
        for t in range(self.frames):
            progress = t / (self.frames - 1) if self.frames > 1 else 1.0
            out_work = os.path.join(tmp_dir, f"work_{t:03d}.jpg")
            out_final = os.path.join(tmp_dir, f"frame_{t:03d}.jpg")
            out_exit = os.path.join(tmp_dir, f"ex_{t:03d}.jpg")
            out_entry = os.path.join(tmp_dir, f"en_{t:03d}.jpg")

            subprocess.run(self._build_command(work_cur, exit_mode, 1 - progress, self.work_width, self.work_height) + [out_exit], check=True, capture_output=True)
            subprocess.run(self._build_command(work_fut, entry_mode, progress, self.work_width, self.work_height) + [out_entry], check=True, capture_output=True)
            subprocess.run(["composite", "-blend", str(self._s_curve_blend(progress)), out_entry, out_exit, out_work], check=True, capture_output=True)
            
            # PERFORMANCE: Upscale to display resolution ONCE per frame
            subprocess.run(["convert", out_work, "-resize", f"{self.width}x{self.height}!", "-quality", "95", "-unsharp", "0x0.5", out_final], check=True, capture_output=True)

        self._play_frames(tmp_dir, set_wallpaper_func)
        set_wallpaper_func(future_img)
        self._cleanup_frames(tmp_dir)
        self.logger.transition_complete()

    def cleanup(self): 
        pass
