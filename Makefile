# BoredNoMore3 Makefile
# Dynamic Wallpaper Changer Installation System
# Version: 0.5.0

# Variables
PACKAGE_NAME = borednomore3
VERSION = 0.5.0
AUTHOR = Nepamuceno Bartolo
EMAIL = (hidden)

# Installation directories
PREFIX = /usr/local
BINDIR = $(PREFIX)/bin
LIBDIR = $(PREFIX)/lib/$(PACKAGE_NAME)
SHAREDIR = $(PREFIX)/share/$(PACKAGE_NAME)
SYSTEMD_DIR = /etc/systemd/system
SYSTEMD_USER_DIR = ~/.config/systemd/user

# Local installation directories
LOCAL_PREFIX = $(HOME)/.local
LOCAL_BINDIR = $(LOCAL_PREFIX)/bin
LOCAL_LIBDIR = $(LOCAL_PREFIX)/lib/$(PACKAGE_NAME)
LOCAL_SHAREDIR = $(LOCAL_PREFIX)/share/$(PACKAGE_NAME)

# Debian package directories
DEB_DIR = debian-build
DEB_PKG_DIR = $(DEB_DIR)/$(PACKAGE_NAME)_$(VERSION)
DEB_DEBIAN_DIR = $(DEB_PKG_DIR)/DEBIAN
DEB_BIN_DIR = $(DEB_PKG_DIR)$(BINDIR)
DEB_LIB_DIR = $(DEB_PKG_DIR)$(LIBDIR)
DEB_SHARE_DIR = $(DEB_PKG_DIR)$(SHAREDIR)
DEB_SYSTEMD_DIR = $(DEB_PKG_DIR)/etc/systemd/system

# Files
MAIN_SCRIPT = borednomore3.py
TRANSITIONS = borednomore3_transitions.py
DOWNLOADER = borednomore3_downloader.py

# Colors for output
RED = \033[0;31m
GREEN = \033[0;32m
YELLOW = \033[1;33m
BLUE = \033[0;34m
NC = \033[0m # No Color

.PHONY: help install install-local install-global install-service install-user-service \
        uninstall uninstall-local uninstall-global requirements check deb clean

# Default target
help:
	@echo "$(BLUE)╔══════════════════════════════════════════════════════════════════════════════╗$(NC)"
	@echo "$(BLUE)║                    BoredNoMore3 - Installation System                        ║$(NC)"
	@echo "$(BLUE)║                              Version $(VERSION)                                     ║$(NC)"
	@echo "$(BLUE)╚══════════════════════════════════════════════════════════════════════════════╝$(NC)"
	@echo ""
	@echo "$(GREEN)Available targets:$(NC)"
	@echo ""
	@echo "  $(YELLOW)make requirements$(NC)      - Install all Python dependencies"
	@echo "  $(YELLOW)make check$(NC)             - Check if all dependencies are installed"
	@echo ""
	@echo "  $(YELLOW)make install-local$(NC)     - Install to ~/.local (user only, no sudo)"
	@echo "  $(YELLOW)make install-global$(NC)    - Install to /usr/local (system-wide, needs sudo)"
	@echo "  $(YELLOW)make install$(NC)           - Interactive installation (choose local/global)"
	@echo ""
	@echo "  $(YELLOW)make install-service$(NC)   - Install as systemd service (global, needs sudo)"
	@echo "  $(YELLOW)make install-user-service$(NC) - Install as user systemd service (no sudo)"
	@echo ""
	@echo "  $(YELLOW)make deb$(NC)               - Create .deb package for easy distribution"
	@echo ""
	@echo "  $(YELLOW)make uninstall-local$(NC)   - Remove local installation"
	@echo "  $(YELLOW)make uninstall-global$(NC)  - Remove global installation (needs sudo)"
	@echo "  $(YELLOW)make clean$(NC)             - Clean build artifacts"
	@echo ""
	@echo "$(GREEN)Quick start:$(NC)"
	@echo "  1. Install dependencies:  $(YELLOW)make requirements$(NC)"
	@echo "  2. Install locally:       $(YELLOW)make install-local$(NC)"
	@echo "  3. Or install globally:   $(YELLOW)sudo make install-global$(NC)"
	@echo "  4. Optional service:      $(YELLOW)make install-user-service$(NC)"
	@echo ""
	@echo "$(GREEN)To create distributable package:$(NC)"
	@echo "  $(YELLOW)make deb$(NC)                 - Creates $(PACKAGE_NAME)_$(VERSION).deb"
	@echo ""

# Check dependencies
check:
	@echo "$(BLUE)Checking dependencies...$(NC)"
	@python3 -c "import pynput" 2>/dev/null && echo "$(GREEN)✓ pynput installed$(NC)" || echo "$(RED)✗ pynput missing$(NC)"
	@python3 -c "import PIL" 2>/dev/null && echo "$(GREEN)✓ Pillow installed$(NC)" || echo "$(RED)✗ Pillow missing$(NC)"
	@python3 -c "import requests" 2>/dev/null && echo "$(GREEN)✓ requests installed$(NC)" || echo "$(RED)✗ requests missing$(NC)"
	@which xrandr >/dev/null 2>&1 && echo "$(GREEN)✓ xrandr available$(NC)" || echo "$(RED)✗ xrandr missing$(NC)"
	@which pcmanfm-qt >/dev/null 2>&1 && echo "$(GREEN)✓ pcmanfm-qt available$(NC)" || echo "$(YELLOW)⚠ pcmanfm-qt missing (will try feh)$(NC)"
	@which feh >/dev/null 2>&1 && echo "$(GREEN)✓ feh available$(NC)" || echo "$(YELLOW)⚠ feh missing (needs pcmanfm-qt or feh)$(NC)"

# Install Python requirements
requirements:
	@echo "$(BLUE)Installing Python dependencies...$(NC)"
	@if command -v pip3 >/dev/null 2>&1; then \
		pip3 install --user pynput Pillow requests; \
		echo "$(GREEN)✓ Python dependencies installed$(NC)"; \
	else \
		echo "$(RED)Error: pip3 not found. Install python3-pip first.$(NC)"; \
		exit 1; \
	fi
	@echo ""
	@echo "$(YELLOW)Checking system dependencies...$(NC)"
	@if ! command -v pcmanfm-qt >/dev/null 2>&1 && ! command -v feh >/dev/null 2>&1; then \
		echo "$(YELLOW)⚠ Warning: Neither pcmanfm-qt nor feh found.$(NC)"; \
		echo "$(YELLOW)  Install one of them:$(NC)"; \
		echo "    sudo apt install pcmanfm-qt   # For LXQt"; \
		echo "    sudo apt install feh          # Alternative"; \
	fi

# Interactive installation
install:
	@echo "$(BLUE)╔══════════════════════════════════════════════════════════════════════════════╗$(NC)"
	@echo "$(BLUE)║                    BoredNoMore3 - Interactive Installation                   ║$(NC)"
	@echo "$(BLUE)╚══════════════════════════════════════════════════════════════════════════════╝$(NC)"
	@echo ""
	@echo "$(GREEN)Choose installation type:$(NC)"
	@echo "  1) Local  (~/.local) - No sudo required, user only"
	@echo "  2) Global (/usr/local) - Requires sudo, available to all users"
	@echo "  3) Cancel"
	@echo ""
	@read -p "Enter choice [1-3]: " choice; \
	case $$choice in \
		1) $(MAKE) install-local ;; \
		2) $(MAKE) install-global ;; \
		3) echo "$(YELLOW)Installation cancelled.$(NC)" ;; \
		*) echo "$(RED)Invalid choice.$(NC)" ;; \
	esac

# Local installation (user only)
install-local:
	@echo "$(BLUE)Installing BoredNoMore3 locally to ~/.local...$(NC)"
	@mkdir -p $(LOCAL_BINDIR)
	@mkdir -p $(LOCAL_LIBDIR)
	@mkdir -p $(LOCAL_SHAREDIR)
	
	@echo "$(GREEN)→ Copying files...$(NC)"
	@install -m 755 $(MAIN_SCRIPT) $(LOCAL_BINDIR)/borednomore3
	@install -m 755 $(DOWNLOADER) $(LOCAL_BINDIR)/borednomore3-downloader
	@install -m 644 $(TRANSITIONS) $(LOCAL_LIBDIR)/
	@cp -f $(TRANSITIONS) $(LOCAL_BINDIR)/
	
	@echo "$(GREEN)→ Creating wrapper scripts...$(NC)"
	@echo '#!/bin/bash' > $(LOCAL_BINDIR)/borednomore3-wrapper
	@echo 'export PYTHONPATH="$(LOCAL_LIBDIR):$$PYTHONPATH"' >> $(LOCAL_BINDIR)/borednomore3-wrapper
	@echo 'exec python3 $(LOCAL_BINDIR)/borednomore3 "$$@"' >> $(LOCAL_BINDIR)/borednomore3-wrapper
	@chmod +x $(LOCAL_BINDIR)/borednomore3-wrapper
	
	@echo ""
	@echo "$(GREEN)✓ Installation complete!$(NC)"
	@echo ""
	@echo "$(YELLOW)Important: Make sure ~/.local/bin is in your PATH$(NC)"
	@echo "Add this to your ~/.bashrc or ~/.profile:"
	@echo "    export PATH=\"\$$HOME/.local/bin:\$$PATH\""
	@echo ""
	@echo "$(GREEN)Usage:$(NC)"
	@echo "  borednomore3 --help"
	@echo "  borednomore3-downloader --help"
	@echo ""
	@echo "$(BLUE)To install as user service:$(NC)"
	@echo "  make install-user-service"

# Global installation (system-wide)
install-global:
	@echo "$(BLUE)Installing BoredNoMore3 globally to /usr/local...$(NC)"
	@if [ "$$(id -u)" -ne 0 ]; then \
		echo "$(RED)Error: Global installation requires sudo$(NC)"; \
		echo "Run: sudo make install-global"; \
		exit 1; \
	fi
	
	@mkdir -p $(BINDIR)
	@mkdir -p $(LIBDIR)
	@mkdir -p $(SHAREDIR)
	
	@echo "$(GREEN)→ Copying files...$(NC)"
	@install -m 755 $(MAIN_SCRIPT) $(BINDIR)/borednomore3
	@install -m 755 $(DOWNLOADER) $(BINDIR)/borednomore3-downloader
	@install -m 644 $(TRANSITIONS) $(LIBDIR)/
	@cp -f $(TRANSITIONS) $(BINDIR)/
	
	@echo ""
	@echo "$(GREEN)✓ Global installation complete!$(NC)"
	@echo ""
	@echo "$(GREEN)Usage:$(NC)"
	@echo "  borednomore3 --help"
	@echo "  borednomore3-downloader --help"
	@echo ""
	@echo "$(BLUE)To install as system service:$(NC)"
	@echo "  sudo make install-service"

# Install as systemd service (global)
install-service:
	@echo "$(BLUE)Installing BoredNoMore3 as systemd service...$(NC)"
	@if [ "$$(id -u)" -ne 0 ]; then \
		echo "$(RED)Error: Service installation requires sudo$(NC)"; \
		echo "Run: sudo make install-service"; \
		exit 1; \
	fi
	
	@echo "$(GREEN)→ Creating service file...$(NC)"
	@echo "[Unit]" > $(SYSTEMD_DIR)/borednomore3.service
	@echo "Description=BoredNoMore3 Dynamic Wallpaper Changer" >> $(SYSTEMD_DIR)/borednomore3.service
	@echo "After=graphical.target" >> $(SYSTEMD_DIR)/borednomore3.service
	@echo "" >> $(SYSTEMD_DIR)/borednomore3.service
	@echo "[Service]" >> $(SYSTEMD_DIR)/borednomore3.service
	@echo "Type=simple" >> $(SYSTEMD_DIR)/borednomore3.service
	@echo "ExecStart=$(BINDIR)/borednomore3 -i 300 -d ~/Pictures/Wallpapers" >> $(SYSTEMD_DIR)/borednomore3.service
	@echo "Restart=on-failure" >> $(SYSTEMD_DIR)/borednomore3.service
	@echo "RestartSec=10" >> $(SYSTEMD_DIR)/borednomore3.service
	@echo "" >> $(SYSTEMD_DIR)/borednomore3.service
	@echo "[Install]" >> $(SYSTEMD_DIR)/borednomore3.service
	@echo "WantedBy=default.target" >> $(SYSTEMD_DIR)/borednomore3.service
	
	@systemctl daemon-reload
	@echo ""
	@echo "$(GREEN)✓ Service installed!$(NC)"
	@echo ""
	@echo "$(YELLOW)To enable and start the service:$(NC)"
	@echo "  sudo systemctl enable borednomore3.service"
	@echo "  sudo systemctl start borednomore3.service"
	@echo ""
	@echo "$(YELLOW)To check status:$(NC)"
	@echo "  sudo systemctl status borednomore3.service"

# Install as user systemd service (no sudo)
install-user-service:
	@echo "$(BLUE)Installing BoredNoMore3 as user systemd service...$(NC)"
	@mkdir -p $(SYSTEMD_USER_DIR)
	
	@echo "$(GREEN)→ Creating user service file...$(NC)"
	@echo "[Unit]" > $(SYSTEMD_USER_DIR)/borednomore3.service
	@echo "Description=BoredNoMore3 Dynamic Wallpaper Changer (User)" >> $(SYSTEMD_USER_DIR)/borednomore3.service
	@echo "After=graphical-session.target" >> $(SYSTEMD_USER_DIR)/borednomore3.service
	@echo "" >> $(SYSTEMD_USER_DIR)/borednomore3.service
	@echo "[Service]" >> $(SYSTEMD_USER_DIR)/borednomore3.service
	@echo "Type=simple" >> $(SYSTEMD_USER_DIR)/borednomore3.service
	@echo "ExecStart=$(LOCAL_BINDIR)/borednomore3 -i 300 -d $(HOME)/Pictures/Wallpapers" >> $(SYSTEMD_USER_DIR)/borednomore3.service
	@echo "Restart=on-failure" >> $(SYSTEMD_USER_DIR)/borednomore3.service
	@echo "RestartSec=10" >> $(SYSTEMD_USER_DIR)/borednomore3.service
	@echo "Environment=DISPLAY=:0" >> $(SYSTEMD_USER_DIR)/borednomore3.service
	@echo "Environment=XAUTHORITY=$(HOME)/.Xauthority" >> $(SYSTEMD_USER_DIR)/borednomore3.service
	@echo "" >> $(SYSTEMD_USER_DIR)/borednomore3.service
	@echo "[Install]" >> $(SYSTEMD_USER_DIR)/borednomore3.service
	@echo "WantedBy=default.target" >> $(SYSTEMD_USER_DIR)/borednomore3.service
	
	@systemctl --user daemon-reload
	@echo ""
	@echo "$(GREEN)✓ User service installed!$(NC)"
	@echo ""
	@echo "$(YELLOW)To enable and start the service:$(NC)"
	@echo "  systemctl --user enable borednomore3.service"
	@echo "  systemctl --user start borednomore3.service"
	@echo ""
	@echo "$(YELLOW)To check status:$(NC)"
	@echo "  systemctl --user status borednomore3.service"
	@echo ""
	@echo "$(YELLOW)To enable at login:$(NC)"
	@echo "  loginctl enable-linger $$USER"

# Uninstall local
uninstall-local:
	@echo "$(BLUE)Uninstalling local installation...$(NC)"
	@rm -f $(LOCAL_BINDIR)/borednomore3
	@rm -f $(LOCAL_BINDIR)/borednomore3-downloader
	@rm -f $(LOCAL_BINDIR)/borednomore3-wrapper
	@rm -rf $(LOCAL_LIBDIR)
	@rm -rf $(LOCAL_SHAREDIR)
	@rm -f $(SYSTEMD_USER_DIR)/borednomore3.service
	@systemctl --user daemon-reload 2>/dev/null || true
	@echo "$(GREEN)✓ Local installation removed$(NC)"

# Uninstall global
uninstall-global:
	@echo "$(BLUE)Uninstalling global installation...$(NC)"
	@if [ "$$(id -u)" -ne 0 ]; then \
		echo "$(RED)Error: Global uninstall requires sudo$(NC)"; \
		echo "Run: sudo make uninstall-global"; \
		exit 1; \
	fi
	@systemctl stop borednomore3.service 2>/dev/null || true
	@systemctl disable borednomore3.service 2>/dev/null || true
	@rm -f $(BINDIR)/borednomore3
	@rm -f $(BINDIR)/borednomore3-downloader
	@rm -rf $(LIBDIR)
	@rm -rf $(SHAREDIR)
	@rm -f $(SYSTEMD_DIR)/borednomore3.service
	@systemctl daemon-reload
	@echo "$(GREEN)✓ Global installation removed$(NC)"

# Create Debian package
deb:
	@echo "$(BLUE)╔══════════════════════════════════════════════════════════════════════════════╗$(NC)"
	@echo "$(BLUE)║                    Creating Debian Package (.deb)                            ║$(NC)"
	@echo "$(BLUE)╚══════════════════════════════════════════════════════════════════════════════╝$(NC)"
	@echo ""
	
	@echo "$(GREEN)→ Creating directory structure...$(NC)"
	@rm -rf $(DEB_DIR)
	@mkdir -p $(DEB_DEBIAN_DIR)
	@mkdir -p $(DEB_BIN_DIR)
	@mkdir -p $(DEB_LIB_DIR)
	@mkdir -p $(DEB_SHARE_DIR)
	@mkdir -p $(DEB_SYSTEMD_DIR)
	
	@echo "$(GREEN)→ Copying files...$(NC)"
	@install -m 755 $(MAIN_SCRIPT) $(DEB_BIN_DIR)/borednomore3
	@install -m 755 $(DOWNLOADER) $(DEB_BIN_DIR)/borednomore3-downloader
	@install -m 644 $(TRANSITIONS) $(DEB_LIB_DIR)/
	@cp -f $(TRANSITIONS) $(DEB_BIN_DIR)/
	
	@echo "$(GREEN)→ Creating systemd service...$(NC)"
	@echo "[Unit]" > $(DEB_SYSTEMD_DIR)/borednomore3.service
	@echo "Description=BoredNoMore3 Dynamic Wallpaper Changer" >> $(DEB_SYSTEMD_DIR)/borednomore3.service
	@echo "After=graphical.target" >> $(DEB_SYSTEMD_DIR)/borednomore3.service
	@echo "" >> $(DEB_SYSTEMD_DIR)/borednomore3.service
	@echo "[Service]" >> $(DEB_SYSTEMD_DIR)/borednomore3.service
	@echo "Type=simple" >> $(DEB_SYSTEMD_DIR)/borednomore3.service
	@echo "ExecStart=/usr/local/bin/borednomore3 -i 300 -d /home/%u/Pictures/Wallpapers" >> $(DEB_SYSTEMD_DIR)/borednomore3.service
	@echo "Restart=on-failure" >> $(DEB_SYSTEMD_DIR)/borednomore3.service
	@echo "" >> $(DEB_SYSTEMD_DIR)/borednomore3.service
	@echo "[Install]" >> $(DEB_SYSTEMD_DIR)/borednomore3.service
	@echo "WantedBy=default.target" >> $(DEB_SYSTEMD_DIR)/borednomore3.service
	
	@echo "$(GREEN)→ Creating control file...$(NC)"
	@echo "Package: $(PACKAGE_NAME)" > $(DEB_DEBIAN_DIR)/control
	@echo "Version: $(VERSION)" >> $(DEB_DEBIAN_DIR)/control
	@echo "Section: utils" >> $(DEB_DEBIAN_DIR)/control
	@echo "Priority: optional" >> $(DEB_DEBIAN_DIR)/control
	@echo "Architecture: all" >> $(DEB_DEBIAN_DIR)/control
	@echo "Depends: python3 (>= 3.6), python3-pil, python3-pynput, python3-requests" >> $(DEB_DEBIAN_DIR)/control
	@echo "Recommends: pcmanfm-qt | feh" >> $(DEB_DEBIAN_DIR)/control
	@echo "Maintainer: $(AUTHOR) <$(EMAIL)>" >> $(DEB_DEBIAN_DIR)/control
	@echo "Description: Dynamic wallpaper changer with smooth transitions" >> $(DEB_DEBIAN_DIR)/control
	@echo " BoredNoMore3 is a sophisticated wallpaper changer for Lubuntu/LXQt" >> $(DEB_DEBIAN_DIR)/control
	@echo " featuring 40+ professional transition effects and multi-source" >> $(DEB_DEBIAN_DIR)/control
	@echo " wallpaper downloading capabilities." >> $(DEB_DEBIAN_DIR)/control
	@echo " ." >> $(DEB_DEBIAN_DIR)/control
	@echo " Features:" >> $(DEB_DEBIAN_DIR)/control
	@echo "  * 40+ professional transition effects" >> $(DEB_DEBIAN_DIR)/control
	@echo "  * Multi-source wallpaper downloader" >> $(DEB_DEBIAN_DIR)/control
	@echo "  * Smart duplicate detection" >> $(DEB_DEBIAN_DIR)/control
	@echo "  * Systemd service support" >> $(DEB_DEBIAN_DIR)/control
	@echo "  * Global keyboard controls" >> $(DEB_DEBIAN_DIR)/control
	
	@echo "$(GREEN)→ Creating postinst script...$(NC)"
	@echo "#!/bin/bash" > $(DEB_DEBIAN_DIR)/postinst
	@echo "set -e" >> $(DEB_DEBIAN_DIR)/postinst
	@echo "echo 'BoredNoMore3 installed successfully!'" >> $(DEB_DEBIAN_DIR)/postinst
	@echo "echo ''" >> $(DEB_DEBIAN_DIR)/postinst
	@echo "echo 'Usage:'" >> $(DEB_DEBIAN_DIR)/postinst
	@echo "echo '  borednomore3 --help'" >> $(DEB_DEBIAN_DIR)/postinst
	@echo "echo '  borednomore3-downloader --help'" >> $(DEB_DEBIAN_DIR)/postinst
	@echo "echo ''" >> $(DEB_DEBIAN_DIR)/postinst
	@echo "echo 'To enable systemd service:'" >> $(DEB_DEBIAN_DIR)/postinst
	@echo "echo '  systemctl --user enable borednomore3.service'" >> $(DEB_DEBIAN_DIR)/postinst
	@echo "echo '  systemctl --user start borednomore3.service'" >> $(DEB_DEBIAN_DIR)/postinst
	@chmod 755 $(DEB_DEBIAN_DIR)/postinst
	
	@echo "$(GREEN)→ Building package...$(NC)"
	@dpkg-deb --build $(DEB_PKG_DIR) $(PACKAGE_NAME)_$(VERSION).deb
	
	@echo ""
	@echo "$(GREEN)✓ Debian package created: $(PACKAGE_NAME)_$(VERSION).deb$(NC)"
	@echo ""
	@echo "$(YELLOW)To install the package:$(NC)"
	@echo "  sudo dpkg -i $(PACKAGE_NAME)_$(VERSION).deb"
	@echo "  sudo apt-get install -f  # Install dependencies if needed"
	@echo ""
	@echo "$(YELLOW)To distribute:$(NC)"
	@echo "  Share the $(PACKAGE_NAME)_$(VERSION).deb file"
	@echo ""

# Clean build artifacts
clean:
	@echo "$(BLUE)Cleaning build artifacts...$(NC)"
	@rm -rf $(DEB_DIR)
	@rm -f $(PACKAGE_NAME)_*.deb
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "$(GREEN)✓ Clean complete$(NC)"
