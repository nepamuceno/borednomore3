"""
Transition engine - handles transition selection and application
Fixed: Implemented synchronous frame purging and targeted file globbing to prevent ghost frames.
"""

import os
import subprocess
import random
import glob
import time

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
        # Initialize random seed for unique results every session
        random.seed(time.time_ns())

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
        self.current_index = -1
        self.transition_playlist = [] # The "deck" of transitions
        
        # Prepare the first cycle
        self._prepare_transition_playlist()
        
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

    def _prepare_transition_playlist(self):
        """Creates the playback queue for transitions and shuffles if needed"""
        self.transition_playlist = list(self.transition_list)
        if self.randomize:
            self.logger.debug("Shuffling transition playlist for non-repeating randomization...")
            random.shuffle(self.transition_playlist)
        self.current_index = -1

    def get_next_transition(self):
        """Get next transition based on selection mode"""
        # Increment index
        self.current_index += 1

        # Reshuffle if we've used all transitions in the current list
        if self.current_index >= len(self.transition_playlist):
            self.logger.info("Transition cycle complete. Reshuffling transitions...")
            self._prepare_transition_playlist()
            self.current_index = 0

        tid = self.transition_playlist[self.current_index]
        
        if self.randomize:
            self.logger.debug(f"Random transition selected (from playlist): {tid}")
        else:
            tid = self.transition_playlist[self.current_index]
            self.logger.debug(f"Sequential transition {self.current_index + 1}/{len(self.transition_playlist)}: {tid}")
        
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
        
        return rf"convert '{img}' -morph {frames} "

    def apply(self, old_img, new_img, transition, set_wallpaper_func):
        """Apply transition between two images with clean frame state."""
        tid = transition['id']
        exit_mode = transition['exit_mode']
        entry_mode = transition['entry_mode']
        
        self.logger.transition_start(transition['name'], tid)
        
        tmp_dir = "/tmp/bnm3_frames"
        os.makedirs(tmp_dir, exist_ok=True)
        
        # --- HARD PURGE (FIX) ---
        # Using native Python to ensure files are deleted synchronously 
        # before ImageMagick starts writing.
        self.logger.debug(f"Purging old frames from: {tmp_dir}")
        for f in os.listdir(tmp_dir):
            if f.endswith('.jpg'):
                try:
                    os.remove(os.path.join(tmp_dir, f))
                except OSError:
                    pass

        exit_frames = self.frames // 2
        entry_frames = self.frames - exit_frames
        
        # Generate exit frames
        if exit_frames > 0:
            self.logger.debug(f"Generating {exit_frames} exit frames...")
            cmd_exit = self._get_imagemagick_cmd(old_img, exit_mode, exit_frames, self.width, self.height)
            cmd_exit += f" {tmp_dir}/f01_%03d.jpg"
            subprocess.run(cmd_exit, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Generate entry frames
        self.logger.debug(f"Generating {entry_frames} entry frames...")
        cmd_entry = self._get_imagemagick_cmd(new_img, entry_mode, entry_frames, self.width, self.height)
        cmd_entry += f" {tmp_dir}/f02_%03d.jpg"
        subprocess.run(cmd_entry, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Play frames (Targeted Filter)
        # We only play files starting with our specific session prefixes
        frames_list = sorted([
            os.path.join(tmp_dir, f) for f in os.listdir(tmp_dir) 
            if f.endswith('.jpg') and (f.startswith('f01_') or f.startswith('f02_'))
        ])
        
        total_frames = len(frames_list)
        self.logger.debug(f"Playing {total_frames} clean frames...")
        
        for i, frame in enumerate(frames_list):
            self.logger.transition_progress(i + 1, total_frames)
            set_wallpaper_func(frame)
        
        # Set final wallpaper
        set_wallpaper_func(new_img)
        
        # Post-transition cleanup
        self.logger.debug("Finalizing cleanup...")
        for f in frames_list:
            try:
                os.remove(frame)
            except:
                pass
        
        self.logger.transition_complete()
