"""
Universal desktop environment detector for Ubuntu/Debian-based systems
Detects and provides wallpaper-setting capabilities for all major desktops
"""

import os
import subprocess
import shutil


class DesktopDetector:
    """Detects desktop environment and provides wallpaper setting method"""
    
    def __init__(self, logger):
        self.logger = logger
        self.desktop_name = None
        self.desktop_session = None
        self.width = 1920
        self.height = 1080
        self.setter_cmd = None
    
    def detect(self):
        """Detect desktop environment and screen resolution"""
        self.logger.debug("Starting desktop detection...")
        
        # Detect desktop
        self._detect_desktop()
        
        # Detect resolution
        self._detect_resolution()
        
        # Select wallpaper setter
        self._select_wallpaper_setter()
        
        return {
            'name': self.desktop_name,
            'session': self.desktop_session,
            'width': self.width,
            'height': self.height,
            'setter': self.setter_cmd
        }
    
    def _detect_desktop(self):
        """Detect which desktop environment is running"""
        # Check environment variables
        desktop_session = os.environ.get('DESKTOP_SESSION', '').lower()
        xdg_current_desktop = os.environ.get('XDG_CURRENT_DESKTOP', '').lower()
        gdmsession = os.environ.get('GDMSESSION', '').lower()
        
        self.logger.debug(f"DESKTOP_SESSION: {desktop_session}")
        self.logger.debug(f"XDG_CURRENT_DESKTOP: {xdg_current_desktop}")
        self.logger.debug(f"GDMSESSION: {gdmsession}")
        
        # Detect desktop type
        if 'gnome' in xdg_current_desktop or 'gnome' in desktop_session:
            self.desktop_name = 'GNOME'
            self.desktop_session = 'gnome'
        elif 'kde' in xdg_current_desktop or 'plasma' in desktop_session:
            self.desktop_name = 'KDE Plasma'
            self.desktop_session = 'kde'
        elif 'xfce' in xdg_current_desktop or 'xfce' in desktop_session:
            self.desktop_name = 'XFCE'
            self.desktop_session = 'xfce'
        elif 'lxqt' in xdg_current_desktop or 'lxqt' in desktop_session:
            self.desktop_name = 'LXQt'
            self.desktop_session = 'lxqt'
        elif 'mate' in xdg_current_desktop or 'mate' in desktop_session:
            self.desktop_name = 'MATE'
            self.desktop_session = 'mate'
        elif 'cinnamon' in xdg_current_desktop or 'cinnamon' in desktop_session:
            self.desktop_name = 'Cinnamon'
            self.desktop_session = 'cinnamon'
        elif 'budgie' in xdg_current_desktop or 'budgie' in desktop_session:
            self.desktop_name = 'Budgie'
            self.desktop_session = 'budgie'
        elif 'i3' in desktop_session or 'i3' in xdg_current_desktop:
            self.desktop_name = 'i3'
            self.desktop_session = 'i3'
        else:
            self.desktop_name = 'Unknown'
            self.desktop_session = 'generic'
            self.logger.warning(f"Unknown desktop: {xdg_current_desktop}, {desktop_session}")
    
    def _detect_resolution(self):
        """Detect screen resolution"""
        try:
            # Try xrandr first (most reliable)
            output = subprocess.check_output(['xrandr'], text=True, stderr=subprocess.DEVNULL)
            for line in output.split('\n'):
                if ' connected' in line and 'primary' in line:
                    parts = line.split()
                    for part in parts:
                        if 'x' in part and part[0].isdigit():
                            resolution = part.split('+')[0]
                            w, h = resolution.split('x')
                            self.width = int(w)
                            self.height = int(h)
                            self.logger.debug(f"Detected resolution via xrandr: {self.width}x{self.height}")
                            return
            
            # If no primary, take first connected
            output = subprocess.check_output(['xrandr'], text=True, stderr=subprocess.DEVNULL)
            for line in output.split('\n'):
                if ' connected' in line:
                    parts = line.split()
                    for part in parts:
                        if 'x' in part and part[0].isdigit():
                            resolution = part.split('+')[0]
                            w, h = resolution.split('x')
                            self.width = int(w)
                            self.height = int(h)
                            self.logger.debug(f"Detected resolution via xrandr: {self.width}x{self.height}")
                            return
        except:
            self.logger.debug("xrandr failed, trying xdpyinfo...")
        
        try:
            # Try xdpyinfo
            output = subprocess.check_output(['xdpyinfo'], text=True, stderr=subprocess.DEVNULL)
            for line in output.split('\n'):
                if 'dimensions:' in line:
                    dims = line.split()[1]
                    w, h = dims.split('x')
                    self.width = int(w)
                    self.height = int(h)
                    self.logger.debug(f"Detected resolution via xdpyinfo: {self.width}x{self.height}")
                    return
        except:
            self.logger.warning("Could not detect resolution, using default 1920x1080")
    
    def _select_wallpaper_setter(self):
        """Select appropriate wallpaper setter command for desktop"""
        setters = {
            'gnome': [
                ('gsettings', ['gsettings', 'set', 'org.gnome.desktop.background', 'picture-uri', 'file://{}']),
                ('gsettings', ['gsettings', 'set', 'org.gnome.desktop.background', 'picture-uri-dark', 'file://{}'])
            ],
            'kde': [
                ('qdbus', self._kde_setter)
            ],
            'xfce': [
                ('xfconf-query', self._xfce_setter)
            ],
            'lxqt': [
                ('pcmanfm-qt', ['pcmanfm-qt', '--set-wallpaper', '{}', '--wallpaper-mode=stretch', '--desktop'])
            ],
            'mate': [
                ('gsettings', ['gsettings', 'set', 'org.mate.background', 'picture-filename', '{}'])
            ],
            'cinnamon': [
                ('gsettings', ['gsettings', 'set', 'org.cinnamon.desktop.background', 'picture-uri', 'file://{}'])
            ],
            'budgie': [
                ('gsettings', ['gsettings', 'set', 'org.gnome.desktop.background', 'picture-uri', 'file://{}'])
            ],
            'i3': [
                ('feh', ['feh', '--bg-fill', '{}'])
            ],
            'generic': [
                ('feh', ['feh', '--bg-fill', '{}']),
                ('nitrogen', ['nitrogen', '--set-zoom-fill', '{}']),
                ('xwallpaper', ['xwallpaper', '--zoom', '{}'])
            ]
        }
        
        desktop_setters = setters.get(self.desktop_session, setters['generic'])
        
        for tool, cmd in desktop_setters:
            if shutil.which(tool):
                self.setter_cmd = cmd
                self.logger.debug(f"Selected wallpaper setter: {tool}")
                return
        
        # Fallback
        self.logger.warning("No suitable wallpaper setter found, using feh as fallback")
        self.setter_cmd = ['feh', '--bg-fill', '{}']
    
    def _kde_setter(self, wallpaper_path):
        """KDE-specific wallpaper setter using qdbus"""
        script = f"""
qdbus org.kde.plasmashell /PlasmaShell org.kde.PlasmaShell.evaluateScript '
var allDesktops = desktops();
for (i=0;i<allDesktops.length;i++) {{
    d = allDesktops[i];
    d.wallpaperPlugin = "org.kde.image";
    d.currentConfigGroup = Array("Wallpaper", "org.kde.image", "General");
    d.writeConfig("Image", "file://{wallpaper_path}");
}}'
"""
        subprocess.run(script, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    def _xfce_setter(self, wallpaper_path):
        """XFCE-specific wallpaper setter"""
        try:
            # Get all xfce4 properties related to backdrop
            output = subprocess.check_output(
                ['xfconf-query', '-c', 'xfce4-desktop', '-l'],
                text=True,
                stderr=subprocess.DEVNULL
            )
            
            for line in output.split('\n'):
                if '/backdrop/screen' in line and '/last-image' in line:
                    subprocess.run(
                        ['xfconf-query', '-c', 'xfce4-desktop', '-p', line.strip(), '-s', wallpaper_path],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
        except:
            self.logger.debug("XFCE wallpaper setting via xfconf-query failed")
    
    def set_wallpaper(self, wallpaper_path):
        """Set wallpaper using detected desktop method"""
        if callable(self.setter_cmd):
            # Custom function (KDE, XFCE)
            self.logger.debug(f"Setting wallpaper via custom function: {wallpaper_path}")
            self.setter_cmd(wallpaper_path)
        else:
            # Command list
            if isinstance(self.setter_cmd, list):
                # Handle multiple commands (GNOME dark mode)
                if isinstance(self.setter_cmd[0], tuple):
                    for _, cmd in self.setter_cmd:
                        final_cmd = [part.format(wallpaper_path) for part in cmd]
                        self.logger.debug(f"Executing: {' '.join(final_cmd)}")
                        subprocess.run(final_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                else:
                    final_cmd = [part.format(wallpaper_path) for part in self.setter_cmd]
                    self.logger.debug(f"Executing: {' '.join(final_cmd)}")
                    subprocess.run(final_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
