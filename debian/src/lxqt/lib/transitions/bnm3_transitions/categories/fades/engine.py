import os
import subprocess
import tempfile
from bnm3_transitions.base import Transition

class FadeTransition(Transition):
    def __init__(self):
        super().__init__(name="Linear Fade")

    def run(self, widget, duration, direction="in", **kwargs):
        # We need two images to transition between
        old_img = kwargs.get('old_wallpaper')
        new_img = kwargs.get('new_wallpaper')
        set_wallpaper_func = kwargs.get('set_wallpaper_func')
        frames = kwargs.get('frames', 10)

        if not old_img or not new_img:
            print("Error: Missing image paths for fade.")
            return False

        print(f"[*] Transitioning: {os.path.basename(old_img)} -> {os.path.basename(new_img)}")

        with tempfile.TemporaryDirectory() as tmpdir:
            for i in range(frames + 1):
                opacity = (i / frames) * 100
                out_file = os.path.join(tmpdir, f"frame_{i:03d}.jpg")
                
                # ImageMagick Blend Command
                subprocess.run([
                    "composite", "-blend", str(int(opacity)),
                    new_img, old_img, out_file
                ])
                
                # Apply the frame to the desktop
                if set_wallpaper_func:
                    set_wallpaper_func(out_file)
        
        # Finally, set the real file to save resources
        set_wallpaper_func(new_img)
        return True
