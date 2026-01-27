"""
Transition engine - handles transition selection and application
"""

import os
import subprocess
import random
import sys


def validate_args(config, logger):
    """Validate configuration parameters"""
    errors = []
    
    if config['interval'] < 1:
        errors.append("Interval must be >= 1 second")
    
    if config['frames'] < 5 or config['frames'] > 100:
        errors.append("Frames must be between 5 and 100")
    
    if config['speed'] <= 0 or config['speed'] > 1.0:
        errors.append("Speed must be between 0.0001 and 1.0")
    
    if errors:
        logger.error("Configuration validation failed:")
        for error in errors:
            logger.error(f"  - {error}")
        sys.exit(1)
    
    logger.debug("Configuration validation passed")



# Transition logic map
LOGIC_MAP = {
    0: ["slide-left", "slide-out-l", "slide-in-l"],
    1: ["slide-right", "slide-out-r", "slide-in-r"],
    2: ["slide-up", "slide-out-u", "slide-in-u"],
    3: ["slide-down", "slide-out-d", "slide-in-d"],
    4: ["spin-cw", "rot-out-cw", "rot-in-cw"],
    5: ["spin-ccw", "rot-out-ccw", "rot-in-ccw"],
    6: ["zoom-io", "zoom-out", "zoom-in"]
}

TRANSITIONS = {i: LOGIC_MAP[i % 7] for i in range(1, 1001)}

# Movement transitions that require keep_image
MOVEMENT_IDS = list(range(5, 9)) + list(range(37, 49)) + list(range(82, 86))


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
        
        # Parse transition list
        if transitions:
            self.transition_list = self._parse_transitions(transitions)
        else:
            self.transition_list = list(TRANSITIONS.keys())
        
        self.randomize = randomize
        self.current_index = 0
        
        self.logger.info(f"Initialized with {len(self.transition_list)} transitions")
        self.logger.debug(f"Randomize: {self.randomize}")
        self.logger.debug(f"Frames: {self.frames}")
        self.logger.debug(f"Speed: {self.speed}")
        self.logger.debug(f"Keep image: {self.keep_image}")
    
    def _parse_transitions(self, transition_str):
        """Parse transition string (e.g., '1,5,10-15') into list"""
        try:
            parts = [t.strip() for t in transition_str.split(',')]
            transitions = []
            
            for part in parts:
                if '-' in part:
                    start_str, end_str = part.split('-')
                    start, end = int(start_str), int(end_str)
                    transitions.extend(range(start, end + 1))
                else:
                    transitions.append(int(part))
            
            # Validate transitions
            valid = []
            for t in transitions:
                if t in TRANSITIONS:
                    valid.append(t)
                else:
                    self.logger.warning(f"Invalid transition ID: {t}, skipping")
            
            if not valid:
                self.logger.error("No valid transitions provided")
                raise ValueError("No valid transitions")
            
            return sorted(set(valid))
        except ValueError as e:
            self.logger.error(f"Invalid transition format: {transition_str}")
            raise
    
    def get_next_transition(self):
        """Get next transition based on selection mode"""
        if self.randomize:
            tid = random.choice(self.transition_list)
            self.logger.debug(f"Random transition selected: {tid}")
        else:
            tid = self.transition_list[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.transition_list)
            self.logger.debug(f"Sequential transition {self.current_index}/{len(self.transition_list)}: {tid}")
        
        transition_data = TRANSITIONS[tid]
        return {
            'id': tid,
            'name': transition_data[0],
            'exit_mode': transition_data[1],
            'entry_mode': transition_data[2]
        }
    
    def _get_imagemagick_cmd(self, img, mode, frames, width, height):
        """Generate ImageMagick command for transition phase"""
        t_step = "(t+1)"
        
        # Exit modes (old image leaving)
        if mode == "slide-out-l":
            return rf"convert '{img}' -duplicate {frames-1} -distort Affine '0,0 %[fx:-{t_step}*({width}/{frames})],0' "
        elif mode == "slide-out-r":
            return rf"convert '{img}' -duplicate {frames-1} -distort Affine '0,0 %[fx:{t_step}*({width}/{frames})],0' "
        elif mode == "slide-out-u":
            return rf"convert '{img}' -duplicate {frames-1} -distort Affine '0,0 0,%[fx:-{t_step}*({height}/{frames})]' "
        elif mode == "slide-out-d":
            return rf"convert '{img}' -duplicate {frames-1} -distort Affine '0,0 0,%[fx:{t_step}*({height}/{frames})]' "
        elif mode == "rot-out-cw":
            return rf"convert '{img}' -duplicate {frames-1} -distort SRT '%[fx:{t_step}*(90/{frames})]' "
        elif mode == "rot-out-ccw":
            return rf"convert '{img}' -duplicate {frames-1} -distort SRT '%[fx:-{t_step}*(90/{frames})]' "
        elif mode == "zoom-out":
            return rf"convert '{img}' -duplicate {frames-1} -distort SRT '%[fx:1-{t_step}*(1/{frames})]' "
        
        # Entry modes (new image arriving)
        elif mode == "slide-in-l":
            return rf"convert '{img}' -duplicate {frames-1} -distort Affine '0,0 %[fx:{width}-{t_step}*({width}/{frames})],0' "
        elif mode == "slide-in-r":
            return rf"convert '{img}' -duplicate {frames-1} -distort Affine '0,0 %[fx:-{width}+{t_step}*({width}/{frames})],0' "
        elif mode == "slide-in-u":
            return rf"convert '{img}' -duplicate {frames-1} -distort Affine '0,0 0,%[fx:{height}-{t_step}*({height}/{frames})]' "
        elif mode == "slide-in-d":
            return rf"convert '{img}' -duplicate {frames-1} -distort Affine '0,0 0,%[fx:-{height}+{t_step}*({height}/{frames})]' "
        elif mode == "rot-in-cw":
            return rf"convert '{img}' -duplicate {frames-1} -distort SRT '%[fx:90-{t_step}*(90/{frames})]' "
        elif mode == "rot-in-ccw":
            return rf"convert '{img}' -duplicate {frames-1} -distort SRT '%[fx:-90+{t_step}*(90/{frames})]' "
        elif mode == "zoom-in":
            return rf"convert '{img}' -duplicate {frames-1} -distort SRT '%[fx:{t_step}*(1/{frames})]' "
        
        # Fallback
        return rf"convert '{img}' -morph {frames} "
    
    def apply(self, old_img, new_img, transition, set_wallpaper_func):
        """Apply transition between two images"""
        tid = transition['id']
        exit_mode = transition['exit_mode']
        entry_mode = transition['entry_mode']
        
        self.logger.transition_start(transition['name'], tid)
        
        # Auto-enable keep_image for movement transitions
        effective_keep = self.keep_image or (tid in MOVEMENT_IDS)
        if tid in MOVEMENT_IDS and not self.keep_image:
            self.logger.debug("Auto-enabling keep_image for movement transition")
        
        tmp_dir = "/tmp/bnm3_frames"
        os.makedirs(tmp_dir, exist_ok=True)
        
        self.logger.debug(f"Cleaning temp directory: {tmp_dir}")
        subprocess.run(f"rm -f {tmp_dir}/*.jpg", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Calculate frame split
        exit_frames = self.frames // 2
        entry_frames = self.frames - exit_frames
        
        # Generate exit frames
        if exit_frames > 0:
            self.logger.debug(f"Generating {exit_frames} exit frames ({exit_mode})...")
            cmd_exit = self._get_imagemagick_cmd(old_img, exit_mode, exit_frames, self.width, self.height)
            cmd_exit += f"{tmp_dir}/f01_%03d.jpg"
            self.logger.debug(f"Command: {cmd_exit[:100]}...")
            subprocess.run(cmd_exit, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Generate entry frames
        self.logger.debug(f"Generating {entry_frames} entry frames ({entry_mode})...")
        cmd_entry = self._get_imagemagick_cmd(new_img, entry_mode, entry_frames, self.width, self.height)
        cmd_entry += f"{tmp_dir}/f02_%03d.jpg"
        self.logger.debug(f"Command: {cmd_entry[:100]}...")
        subprocess.run(cmd_entry, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Play frames
        frames_list = sorted([os.path.join(tmp_dir, f) for f in os.listdir(tmp_dir) if f.endswith('.jpg')])
        total_frames = len(frames_list)
        
        self.logger.debug(f"Playing {total_frames} frames...")
        for i, frame in enumerate(frames_list):
            self.logger.transition_progress(i + 1, total_frames)
            set_wallpaper_func(frame)
        
        # Set final wallpaper
        self.logger.debug("Setting final wallpaper...")
        set_wallpaper_func(new_img)
        
        # Cleanup
        self.logger.debug("Cleaning up frames...")
        subprocess.run(f"rm -f {tmp_dir}/*.jpg", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        self.logger.transition_complete()
