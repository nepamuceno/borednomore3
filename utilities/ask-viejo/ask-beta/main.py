#!/usr/bin/env python3
"""
Prompt Engine - Main Entry Point
"""

import tkinter as tk
import customtkinter as ctk
import signal
import sys
import os
import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import from our packages
from gui.main_window import ModernPromptGUI
from utils.config import APP_CONFIG
from utils.logger import setup_logger

def signal_handler(sig, frame):
    """Handle CTRL+C gracefully"""
    print(f"\n[{datetime.datetime.now()}] INTERRUPT (Ctrl+C). Saving state...")
    if 'app' in globals() and hasattr(app, 'save_state'):
        app.save_state()
    sys.exit(0)

def main():
    """Main application entry point"""
    # Set up logging
    logger = setup_logger()
    logger.info("Starting Prompt Engine application")
    
    # Set up signal handling
    signal.signal(signal.SIGINT, signal_handler)
    
    # Initialize CustomTkinter
    ctk.set_appearance_mode(APP_CONFIG['default_appearance'])
    ctk.set_default_color_theme(APP_CONFIG['default_color_theme'])
    
    # Create main window
    root = ctk.CTk()
    app = ModernPromptGUI(root)
    
    # Start the application
    logger.info("Application started successfully")
    root.mainloop()

if __name__ == "__main__":
    main()
