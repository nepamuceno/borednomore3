import os
import subprocess
import time

# --- 1. THE UNIVERSAL LOGIC REGISTRY ---
# We map all 1000 IDs to these 7 core geometric behaviors
LOGIC_MAP = {
    0: ["slide-left",  "slide-out-l", "slide-in-l"],  # Moves X-
    1: ["slide-right", "slide-out-r", "slide-in-r"],  # Moves X+
    2: ["slide-up",    "slide-out-u", "slide-in-u"],  # Moves Y-
    3: ["slide-down",  "slide-out-d", "slide-in-d"],  # Moves Y+
    4: ["spin-cw",     "rot-out-cw",  "rot-in-cw"],   # Rotate Clockwise
    5: ["spin-ccw",    "rot-out-ccw", "rot-in-ccw"],  # Rotate Counter-Clockwise
    6: ["zoom-io",     "zoom-out",    "zoom-in"]      # Scale
}

TRANSITIONS = {i: LOGIC_MAP[i % 7] for i in range(1, 1001)}

# --- 2. THE GEOMETRIC COMMAND FACTORY ---
def get_cmd(img, mode, f, w, h):
    """
    Standardizes the ImageMagick math for all universal behaviors.
    f = frames in this phase
    """
    t_step = "(t+1)"
    
    # EXIT MODES (Old image leaving)
    if mode == "slide-out-l": return rf"convert '{img}' -duplicate {f-1} -distort Affine '0,0 %[fx:-{t_step}*({w}/{f})],0' "
    if mode == "slide-out-r": return rf"convert '{img}' -duplicate {f-1} -distort Affine '0,0 %[fx:{t_step}*({w}/{f})],0' "
    if mode == "slide-out-u": return rf"convert '{img}' -duplicate {f-1} -distort Affine '0,0 0,%[fx:-{t_step}*({h}/{f})]' "
    if mode == "slide-out-d": return rf"convert '{img}' -duplicate {f-1} -distort Affine '0,0 0,%[fx:{t_step}*({h}/{f})]' "
    if mode == "rot-out-cw":  return rf"convert '{img}' -duplicate {f-1} -distort SRT '%[fx:{t_step}*(90/{f})]' "
    if mode == "rot-out-ccw": return rf"convert '{img}' -duplicate {f-1} -distort SRT '%[fx:-{t_step}*(90/{f})]' "
    if mode == "zoom-out":    return rf"convert '{img}' -duplicate {f-1} -distort SRT '%[fx:1-{t_step}*(1/{f})]' "

    # ENTRY MODES (New image arriving)
    if mode == "slide-in-l":  return rf"convert '{img}' -duplicate {f-1} -distort Affine '0,0 %[fx:{w}-{t_step}*({w}/{f})],0' "
    if mode == "slide-in-r":  return rf"convert '{img}' -duplicate {f-1} -distort Affine '0,0 %[fx:-{w}+{t_step}*({w}/{f})],0' "
    if mode == "slide-in-u":  return rf"convert '{img}' -duplicate {f-1} -distort Affine '0,0 0,%[fx:{h}-{t_step}*({h}/{f})]' "
    if mode == "slide-in-d":  return rf"convert '{img}' -duplicate {f-1} -distort Affine '0,0 0,%[fx:-{h}+{t_step}*({h}/{f})]' "
    if mode == "rot-in-cw":   return rf"convert '{img}' -duplicate {f-1} -distort SRT '%[fx:90-{t_step}*(90/{f})]' "
    if mode == "rot-in-ccw":  return rf"convert '{img}' -duplicate {f-1} -distort SRT '%[fx:-90+{t_step}*(90/{f})]' "
    if mode == "zoom-in":     return rf"convert '{img}' -duplicate {f-1} -distort SRT '%[fx:{t_step}*(1/{f})]' "

    # Fallback
    return rf"convert '{img}' -morph {f} "

# --- 3. THE EXECUTION ENGINE ---
def apply_transition(old_img, new_img, tid, width, height, frames, speed, set_wallpaper_cmd, check_exit, keep_old=False):
    tmp_dir = "/tmp/bnm3_frames"
    os.makedirs(tmp_dir, exist_ok=True)
    subprocess.run(f"rm -f {tmp_dir}/*.jpg", shell=True)
    
    # 1. Fetch metadata [Name, ExitMode, EntryMode]
    meta = TRANSITIONS.get(tid)
    exit_f = frames // 2
    entry_f = frames - exit_f 

    # 2. Sequential Generation (Wait for Exit to finish before starting Entry)
    if exit_f > 0:
        cmd_out = get_cmd(old_img, meta[1], exit_f, width, height) + f"{tmp_dir}/f01_%03d.jpg"
        subprocess.run(cmd_out, shell=True)

    cmd_in = get_cmd(new_img, meta[2], entry_f, width, height) + f"{tmp_dir}/f02_%03d.jpg"
    subprocess.run(cmd_in, shell=True)

    # 3. High-Speed Playback
    frames_list = sorted([os.path.join(tmp_dir, f) for f in os.listdir(tmp_dir) if f.endswith('.jpg')])
    for f in frames_list:
        if check_exit(): break
        set_wallpaper_cmd(f)
        # speed is handled by OS command execution speed since you want maximum speed

    # 4. Final Handoff
    set_wallpaper_cmd(new_img)
    subprocess.run(f"rm -f {tmp_dir}/*.jpg", shell=True)
