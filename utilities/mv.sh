#!/bin/bash
# create_full_os_structures.sh
# Create full empty OS/desktop folder structures with all subdirectories

echo "Creating full empty OS/desktop structures..."

# Function to create structure for each desktop
create_desktop_structure() {
    local os_dir=$1
    local desktop=$2
    
    # For each desktop, create: backend/, frontend/, lib/, conf/, debian/, wallpapers/
    mkdir -p "$os_dir/src/$desktop/"{backend,frontend,lib,conf,debian,wallpapers,dist/bin}
}

# Linux distributions
for os in fedora arch ubuntu opensuse rhel centos; do
    echo "Creating $os..."
    for desktop in lxqt gnome kde xfce mate cinnamon; do
        create_desktop_structure "$os" "$desktop"
    done
    # Also create top-level dist/bin and debian
    mkdir -p "$os/dist/bin" "$os/debian"
done

# BSD systems (no debian inside desktops)
for os in freebsd openbsd netbsd dragonflybsd; do
    echo "Creating $os..."
    for desktop in lxqt gnome kde xfce mate cinnamon; do
        mkdir -p "$os/src/$desktop/"{backend,frontend,lib,conf,wallpapers,dist/bin}
    done
    mkdir -p "$os/dist/bin"
done

# Windows/macOS
for os in windows macos; do
    echo "Creating $os..."
    for desktop in lxqt gnome kde; do
        mkdir -p "$os/src/$desktop/"{backend,frontend,lib,conf,wallpapers,dist/bin}
    done
    mkdir -p "$os/dist/bin"
done

# Mobile platforms
for os in android ios; do
    echo "Creating $os..."
    for variant in mobile tablet; do
        mkdir -p "$os/src/$variant/"{backend,frontend,lib,conf,assets,dist/bin}
    done
    mkdir -p "$os/dist/bin"
done

echo ""
echo "FULL STRUCTURES CREATED!"
echo ""
echo "Each OS has:"
echo "  OS/src/{desktop}/backend/"
echo "  OS/src/{desktop}/frontend/"
echo "  OS/src/{desktop}/lib/"
echo "  OS/src/{desktop}/conf/"
echo "  OS/src/{desktop}/wallpapers/ (or assets/ for mobile)"
echo "  OS/src/{desktop}/dist/bin/"
echo "  OS/src/{desktop}/debian/ (Linux only)"
echo ""
echo "Total directories created:"
find . -type d | grep -v "\.git" | wc -l | xargs echo "  "
echo ""
echo "Your working directory: debian/src/lxqt/ (unchanged)"
echo "All new directories are empty."
