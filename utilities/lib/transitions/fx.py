import subprocess
import time

def apply(old, new, tid, w, h, f, s, cmd, exit_check):
    tmp = "/tmp/bnm3_fx.jpg"
    for frame in range(1, f + 1):
        if exit_check(): break
        p = frame / f
        pct = p * 100
        
        if 801 <= tid <= 900: # Pixel Scatter
            scale = (tid - 800) // 5 + 2
            subprocess.run(["convert", old, new, "(", "-size", f"{w//scale}x{h//scale}", 
                            "xc:black", "+noise", "Random", "-threshold", f"{pct}%", 
                            "-scale", f"{w}x{h}!", ")", "-composite", tmp])
        else: # Glitch Slices
            slices = (tid - 900) + 10
            subprocess.run(["convert", old, new, "(", "-size", f"1x{slices}", 
                            "xc:black", "+noise", "Random", "-threshold", f"{pct}%", 
                            "-scale", f"{w}x{h}!", ")", "-composite", tmp])
        
        cmd(tmp)
        time.sleep(s)
