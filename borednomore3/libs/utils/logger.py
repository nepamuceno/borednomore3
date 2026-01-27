"""
Logger utility for real-time debug and info messages with rotation
"""
import sys
import os
from datetime import datetime

# Log levels
DEBUG = 0
INFO = 1
WARNING = 2
ERROR = 3


class Logger:
    """Real-time logging with debug support and auto-rotation"""
    
    def __init__(self, level=INFO, log_file=None, max_lines=1000):
        self.level = level
        self.log_file = log_file
        self.max_lines = max_lines
        self.line_count = 0
        self.colors = {
            'DEBUG': '\033[36m',
            'INFO': '\033[32m',
            'WARNING': '\033[33m',
            'ERROR': '\033[31m',
            'RESET': '\033[0m'
        }
        
        # Clear console on start only if terminal
        if sys.stdout.isatty():
            os.system('clear' if os.name != 'nt' else 'cls')
        
        # Trim log file if it exists
        if self.log_file and os.path.exists(self.log_file):
            self._trim_log_file()
    
    def _trim_log_file(self):
        """Keep only last max_lines in log file"""
        try:
            with open(self.log_file, 'r') as f:
                lines = f.readlines()
            
            if len(lines) > self.max_lines:
                with open(self.log_file, 'w') as f:
                    f.writelines(lines[-self.max_lines:])
        except:
            pass
    
    def _trim_console(self):
        """Clear console when line count exceeds max_lines"""
        if not sys.stdout.isatty():
            return
        self.line_count += 1
        if self.line_count >= self.max_lines:
            os.system('clear' if os.name != 'nt' else 'cls')
            self.line_count = 0
            print(f"[Console cleared at {self.max_lines} lines]")
    
    def _log(self, level, level_name, message):
        """Internal log method"""
        if level < self.level:
            return
        
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        
        # Console output with color only if terminal
        if sys.stdout.isatty():
            color = self.colors.get(level_name, '')
            reset = self.colors['RESET']
            prefix = f"{color}[{timestamp}] [{level_name}]{reset}"
        else:
            prefix = f"[{timestamp}] [{level_name}]"
        
        print(f"{prefix} {message}", flush=True)
        self._trim_console()
        
        # File output without color
        if self.log_file:
            try:
                with open(self.log_file, 'a') as f:
                    f.write(f"[{timestamp}] [{level_name}] {message}\n")
                self._trim_log_file()
            except:
                pass
    
    def debug(self, message):
        self._log(DEBUG, 'DEBUG', message)
    
    def info(self, message):
        self._log(INFO, 'INFO', message)
    
    def warning(self, message):
        self._log(WARNING, 'WARNING', message)
    
    def error(self, message):
        self._log(ERROR, 'ERROR', message)
    
    def transition_start(self, transition_name, transition_id):
        self.info(f"Starting transition: {transition_name} (ID: {transition_id})")
    
    def transition_progress(self, current, total):
        if self.level <= DEBUG:
            percent = (current / total) * 100
            self.debug(f"Transition progress: {current}/{total} ({percent:.1f}%)")
    
    def transition_complete(self):
        self.info("Transition complete")
    
    def wallpaper_change(self, wallpaper_name, index, total):
        self.info(f"Changing to wallpaper {index + 1}/{total}: {wallpaper_name}")
