import subprocess

def apply(b_old, b_new, name, w, h, alpha, out):
    if name == "instant-cut":
        subprocess.run(["cp", b_new, out])
    elif "white" in name:
        subprocess.run(["convert", b_old, b_new, "-average", "-fill", "white", "-colorize", f"{alpha}%", out])
    elif "black" in name:
        subprocess.run(["convert", b_old, b_new, "-average", "-fill", "black", "-colorize", f"{alpha}%", out])
    else: # Default Crossfade / Fade
        subprocess.run(["composite", "-blend", str(alpha), b_new, b_old, out])
