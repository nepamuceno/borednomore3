import subprocess

def apply(b_old, b_new, name, w, h, alpha, out):
    if "focus-in" in name:
        blur = (1 - (alpha/100)) * 25
        subprocess.run(["convert", b_new, "-blur", f"0x{blur}", out])
    elif "focus-out" in name:
        blur = (alpha/100) * 25
        subprocess.run(["convert", b_old, "-blur", f"0x{blur}", out])
    elif "zoom-in" in name:
        scale = 100 + (alpha / 2)
        subprocess.run(["convert", b_new, "-resize", f"{scale}%", "-gravity", "center", "-extent", f"{w}x{h}", out])
    elif "twist" in name or "swirl" in name:
        subprocess.run(["convert", b_new, "-swirl", str(alpha*4), out])
    elif "ripple" in name:
        subprocess.run(["convert", b_new, "-wave", f"{alpha/10}x{w/10}", out])
