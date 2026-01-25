import subprocess

def apply(b_old, b_new, name, w, h, alpha, out):
    offset_x = int((alpha/100) * w)
    offset_y = int((alpha/100) * h)
    
    # Logic for Slide-In (Way-In) and Slide-Out (Way-Out)
    if "left" in name:
        subprocess.run(["convert", b_old, b_new, "+append", "-repage", f"-{offset_x}+0", "-extent", f"{w}x{h}", out])
    elif "right" in name:
        subprocess.run(["convert", b_new, b_old, "+append", "-repage", f"-{w-offset_x}+0", "-extent", f"{w}x{h}", out])
    elif "up" in name:
        subprocess.run(["convert", b_old, b_new, "-append", "-repage", f"+0-{offset_y}", "-extent", f"{w}x{h}", out])
    elif "down" in name:
        subprocess.run(["convert", b_new, b_old, "-append", "-repage", f"+0-{h-offset_y}", "-extent", f"{w}x{h}", out])
