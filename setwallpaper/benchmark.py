#!/usr/bin/env python3
"""
Benchmark script for wallpaper setters
Compares binary vs shared library performance
Version: 1.0.1
"""

import subprocess
import time
import os
import sys
import ctypes
import argparse
import glob
from pathlib import Path

VERSION = "1.0.1"
AUTHOR = "Nepamuceno"
GITHUB = "https://github.com/nepamuceno/borednomore3"

def print_help():
    """Print comprehensive help information"""
    help_text = f"""
Wallpaper Setter Benchmark Tool v{VERSION}

DESCRIPTION:
    Benchmark different wallpaper setting methods (binary, library, system tools)
    to determine the fastest approach for your system.

USAGE:
    {sys.argv[0]} [OPTIONS]

OPTIONS:
    -h, --help                Show this help message and exit
    -v, --version             Show version information
    -c, --credits             Show author and credits
    -f, --folder <path>       Path to images (supports wildcards)
                            Examples: 
                            -f /path/to/folder/*.jpg
                            -f /path/to/single/image.png
                            -f "/path with spaces/*.jpg"
    -l, --loops <number>      Number of benchmark repetitions (default: 5)
    -d, --debug               Enable debug output
    --list-methods           List available wallpaper setting methods

EXAMPLES:
    # Benchmark with default frames directory
    {sys.argv[0]}

    # Benchmark specific folder with wildcards
    {sys.argv[0]} -f "~/Pictures/wallpapers/*.jpg"

    # Benchmark with custom repetitions
    {sys.argv[0]} -f "/tmp/frames/*.jpg" -l 10

    # Debug mode with single image
    {sys.argv[0]} -f "/path/to/image.png" -d

    # Show available methods only
    {sys.argv[0]} --list-methods

PERFORMANCE TIPS:
    - Use pre-generated frames for consistent results
    - Higher loop counts provide more accurate averages
    - Debug mode shows detailed timing information

AUTHOR:
    {AUTHOR}
    GitHub: {GITHUB}
"""
    print(help_text)

def print_version():
    """Print version information"""
    print(f"Wallpaper Benchmark Tool v{VERSION}")

def print_credits():
    """Print credits and author information"""
    print(f"""
Wallpaper Benchmark Tool v{VERSION}
Author: {AUTHOR}
GitHub: {GITHUB}

Part of the borednomore3 dynamic wallpaper changer project.
This tool helps determine the optimal wallpaper setting method for your system.
""")

def expand_path(path_pattern):
    """Expand path with wildcards and environment variables"""
    # Expand user and environment variables
    expanded = os.path.expanduser(os.path.expandvars(path_pattern))
    
    # Handle wildcards
    if '*' in expanded or '?' in expanded:
        matches = glob.glob(expanded)
        return matches if matches else []
    elif os.path.isfile(expanded):
        return [expanded]
    elif os.path.isdir(expanded):
        # If directory, get all common image files
        images = []
        for ext in ['*.jpg', '*.jpeg', '*.png', '*.webp']:
            images.extend(glob.glob(os.path.join(expanded, ext)))
        return sorted(images)
    else:
        return []

def detect_methods():
    """Detect available wallpaper setting methods"""
    methods = {}
    
    # Check custom binary
    if os.path.exists("./setwallpaper"):
        methods['binary'] = "./setwallpaper"
    
    # Check custom shared library
    if os.path.exists("./setwallpaper.so"):
        try:
            lib = ctypes.CDLL("./setwallpaper.so")
            if hasattr(lib, 'set_wallpaper_universal'):
                methods['library'] = lib
        except Exception as e:
            pass
    
    # Check system methods
    system_methods = [
        (["feh", "--version"], ["feh", "--bg-fill"]),
        (["nitrogen", "--help"], ["nitrogen", "--set-zoom-fill"]),
        (["pcmanfm-qt", "--version"], ["pcmanfm-qt", "--set-wallpaper", "--wallpaper-mode=stretch", "--desktop"]),
        (["xwallpaper", "--version"], ["xwallpaper", "--zoom"]),
        (["hsetroot", "-help"], ["hsetroot", "-fill"]),
        (["xloadimage", "-version"], ["xloadimage", "-onroot", "-fullscreen"]),
    ]
    
    for test_cmd, apply_cmd in system_methods:
        try:
            subprocess.run(test_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=1)
            methods[test_cmd[0]] = apply_cmd
        except:
            continue
    
    # GNOME gsettings
    try:
        subprocess.run(["gsettings", "help"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=1)
        methods['gsettings'] = lambda p: ["gsettings", "set", "org.gnome.desktop.background", "picture-uri", f"file://{p}"]
    except:
        pass
    
    # KDE qdbus
    try:
        subprocess.run(["qdbus", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=1)
        methods['qdbus'] = lambda p: [
            "qdbus", "org.kde.plasmashell", "/PlasmaShell", 
            "org.kde.PlasmaShell.evaluateScript",
            f'var allDesktops = desktops(); for (i=0;i<allDesktops.length;i++) {{ d = allDesktops[i]; d.wallpaperPlugin = "org.kde.image"; d.currentConfigGroup = Array("Wallpaper", "org.kde.image", "General"); d.writeConfig("Image", "file://{p}") }}'
        ]
    except:
        pass
    
    return methods

def benchmark_binary(binary_path, frames, reps, debug=False):
    """Benchmark binary executable"""
    total_time = 0.0
    
    for rep in range(1, reps + 1):
        if debug:
            print(f"  [DEBUG] Starting repetition {rep}/{reps}")
        
        start = time.time()
        for i, frame in enumerate(frames):
            if debug and i % 10 == 0:
                print(f"    [DEBUG] Processing frame {i+1}/{len(frames)}")
            
            result = subprocess.run([binary_path, frame], 
                                    stdout=subprocess.DEVNULL, 
                                    stderr=subprocess.DEVNULL)
            if result.returncode != 0 and debug:
                print(f"    [DEBUG] Warning: Binary returned code {result.returncode} for {frame}")
        
        end = time.time()
        elapsed = end - start
        total_time += elapsed
        
        avg_per_frame = elapsed / len(frames)
        print(f"  Repetition {rep}: {elapsed:.4f}s total, {avg_per_frame:.6f}s/frame")
    
    return total_time

def benchmark_library(lib, frames, reps, debug=False):
    """Benchmark shared library"""
    total_time = 0.0
    
    # Set argument and return types
    lib.set_wallpaper_universal.argtypes = [ctypes.c_char_p]
    lib.set_wallpaper_universal.restype = ctypes.c_int
    
    for rep in range(1, reps + 1):
        if debug:
            print(f"  [DEBUG] Starting repetition {rep}/{reps}")
        
        start = time.time()
        for i, frame in enumerate(frames):
            if debug and i % 10 == 0:
                print(f"    [DEBUG] Processing frame {i+1}/{len(frames)}")
            
            frame_bytes = frame.encode('utf-8')
            result = lib.set_wallpaper_universal(frame_bytes)
            if result != 0 and debug:
                print(f"    [DEBUG] Warning: Library returned error code {result} for {frame}")
        
        end = time.time()
        elapsed = end - start
        total_time += elapsed
        
        avg_per_frame = elapsed / len(frames)
        print(f"  Repetition {rep}: {elapsed:.4f}s total, {avg_per_frame:.6f}s/frame")
    
    return total_time

def benchmark_system(method_cmd, frames, reps, debug=False):
    """Benchmark system method"""
    total_time = 0.0
    
    for rep in range(1, reps + 1):
        if debug:
            print(f"  [DEBUG] Starting repetition {rep}/{reps}")
        
        start = time.time()
        for i, frame in enumerate(frames):
            if debug and i % 10 == 0:
                print(f"    [DEBUG] Processing frame {i+1}/{len(frames)}")
            
            if callable(method_cmd):
                cmd = method_cmd(frame)
            else:
                cmd = method_cmd + [frame]
            
            result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if result.returncode != 0 and debug:
                print(f"    [DEBUG] Warning: Command returned code {result.returncode} for {frame}")
        
        end = time.time()
        elapsed = end - start
        total_time += elapsed
        
        avg_per_frame = elapsed / len(frames)
        print(f"  Repetition {rep}: {elapsed:.4f}s total, {avg_per_frame:.6f}s/frame")
    
    return total_time

def main():
    # Argument parser
    parser = argparse.ArgumentParser(
        description='Wallpaper Setter Benchmark Tool',
        add_help=False,
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    parser.add_argument('-h', '--help', action='store_true', help='Show help message')
    parser.add_argument('-v', '--version', action='store_true', help='Show version information')
    parser.add_argument('-c', '--credits', action='store_true', help='Show credits')
    parser.add_argument('-f', '--folder', type=str, default=None, help='Path to images (supports wildcards)')
    parser.add_argument('-l', '--loops', type=int, default=5, help='Number of benchmark repetitions (default: 5)')
    parser.add_argument('-d', '--debug', action='store_true', help='Enable debug output')
    parser.add_argument('--list-methods', action='store_true', help='List available wallpaper methods')
    
    args = parser.parse_args()
    
    # Handle help first
    if args.help:
        print_help()
        sys.exit(0)
    
    if args.version:
        print_version()
        sys.exit(0)
    
    if args.credits:
        print_credits()
        sys.exit(0)
    
    # List methods if requested
    if args.list_methods:
        methods = detect_methods()
        print("Available wallpaper setting methods:")
        for method, impl in methods.items():
            if method == 'library':
                print(f"  - {method}: Custom shared library")
            elif method in ['binary', 'gsettings', 'qdbus', 'feh', 'nitrogen', 'pcmanfm-qt', 'xwallpaper', 'hsetroot', 'xloadimage']:
                print(f"  - {method}: {'Custom binary' if method == 'binary' else method}")
            else:
                print(f"  - {method}: System method")
        
        if not methods:
            print("  No methods available. Compile setwallpaper and setwallpaper.so first.")
        sys.exit(0)
    
    # Determine image sources
    if args.folder:
        frames = expand_path(args.folder)
        if not frames:
            print(f"Error: No images found matching pattern: {args.folder}")
            sys.exit(1)
    else:
        # Default frames directory
        frames_dir = "/tmp/bnm3_frames"
        if not os.path.exists(frames_dir):
            print(f"Error: Default directory {frames_dir} does not exist")
            print("Use -f to specify image path or run borednomore3 to generate frames")
            sys.exit(1)
        
        frames = sorted(
            os.path.join(frames_dir, f) for f in os.listdir(frames_dir) 
            if f.endswith((".jpg", ".jpeg", ".png", ".webp"))
        )
        
        if not frames:
            print(f"Error: No images found in {frames_dir}")
            sys.exit(1)
    
    num_frames = len(frames)
    print(f"Found {num_frames} images to benchmark")
    
    if args.debug:
        print(f"[DEBUG] Images: {frames[:3]}{'...' if len(frames) > 3 else ''}")
    
    # Detect available methods
    methods = detect_methods()
    
    if not methods:
        print("Error: No wallpaper setting methods available")
        print("Please compile setwallpaper and/or setwallpaper.so first")
        sys.exit(1)
    
    print(f"\nDetected methods: {', '.join(methods.keys())}")
    print(f"Benchmark loops: {args.loops}")
    print(f"Images per loop: {num_frames}")
    print("=" * 80)
    
    if args.debug:
        print(f"[DEBUG] Method details: {methods}")
    
    results = {}
    
    # Benchmark each method
    for method_name, method_impl in methods.items():
        print(f"\n[{method_name.upper()}]")
        
        try:
            if method_name == 'binary':
                total_time = benchmark_binary(method_impl, frames, args.loops, args.debug)
            elif method_name == 'library':
                total_time = benchmark_library(method_impl, frames, args.loops, args.debug)
            else:
                total_time = benchmark_system(method_impl, frames, args.loops, args.debug)
            
            avg_per_frame = total_time / (args.loops * num_frames)
            results[method_name] = {
                'total': total_time,
                'avg_per_frame': avg_per_frame
            }
            
        except Exception as e:
            print(f"  Error: {e}")
            if args.debug:
                import traceback
                traceback.print_exc()
            results[method_name] = None
    
    # Print summary
    print("\n" + "=" * 80)
    print("PERFORMANCE SUMMARY")
    print("=" * 80)
    
    valid_results = {k: v for k, v in results.items() if v is not None}
    
    if valid_results:
        # Sort by average time per frame (fastest first)
        sorted_results = sorted(valid_results.items(), key=lambda x: x[1]['avg_per_frame'])
        
        print(f"{'Method':<15} {'Total Time':<15} {'Time/Frame':<15} {'Speed':<15}")
        print("-" * 60)
        
        fastest = sorted_results[0][1]['avg_per_frame']
        
        for method_name, result in sorted_results:
            total = result['total']
            avg = result['avg_per_frame']
            speed_ratio = fastest / avg if avg > 0 else 0
            
            print(f"{method_name:<15} {total:<15.4f} {avg:<15.6f} {speed_ratio:<15.2f}x")
        
        print("-" * 60)
        print(f"Fastest method: {sorted_results[0][0]} ({sorted_results[0][1]['avg_per_frame']:.6f}s/frame)")
        
        # Calculate improvement between binary and library
        if 'binary' in valid_results and 'library' in valid_results:
            binary_time = valid_results['binary']['avg_per_frame']
            library_time = valid_results['library']['avg_per_frame']
            if binary_time > 0:
                improvement = (binary_time - library_time) / binary_time * 100
                print(f"\nLibrary improvement over binary: {improvement:.1f}%")
    else:
        print("No valid results to compare")

if __name__ == "__main__":
    main()
