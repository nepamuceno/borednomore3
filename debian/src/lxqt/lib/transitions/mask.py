import subprocess
import time

def apply(old, new, tid, w, h, f, s, cmd, exit_check):
    tmp = "/tmp/bnm3_mask.jpg"
    for frame in range(1, f + 1):
        if exit_check(): break
        pct = (frame / f) * 100
        
        if 100 <= tid <= 460: # Rotating Linear Wipes
            angle = tid - 100
            subprocess.run(["convert", old, new, "(", "-size", f"{w}x{h}", 
                            "gradient:black-white", "-distort", "SRT", str(angle), 
                            "-threshold", f"{pct}%", ")", "-composite", tmp])
        elif 461 <= tid <= 560: # Radial Iris
            radius = int((max(w, h) * 1.5) * (frame/f))
            subprocess.run(["convert", old, new, "(", "-size", f"{w}x{h}", "xc:black", 
                            "-fill", "white", "-draw", f"circle {w//2},{h//2} {w//2},{h//2 + radius}", 
                            ")", "-composite", tmp])
        else: # Plasma/Organic
            subprocess.run(["convert", old, new, "(", "-size", f"{w}x{h}", 
                            "plasma:fractal", "-seed", str(tid), "-threshold", f"{pct}%", 
                            ")", "-composite", tmp])
        
        cmd(tmp)
        time.sleep(s)
