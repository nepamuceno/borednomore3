# BoredNoMore3 Makefile - The "Ultimate" Edition
# Version: 0.5.3

# Binary Names
BIN_GUI        = borednomore3-gui
BIN_SETTER     = borednomore3
BIN_DL         = borednomore3-downloader
BIN_DL_GUI     = borednomore3-downloader-gui

# Source Files
SCRIPT_GUI     = borednomore3_gui.py
SCRIPT_SETTER  = borednomore3.py
SCRIPT_DL      = borednomore3_downloader.py
SCRIPT_DL_GUI  = borednomore3_downloader_gui.py
LIB_TRANS      = borednomore3_transitions.py

# Variables
VERSION = 0.5.3
AUTHOR  = Nepamuceno Bartolo
# Hiding email: Uses environment variable BNM_EMAIL if set, else a placeholder
EMAIL   ?= $(shell echo $${BNM_EMAIL:-"developer@internal.local"})
PACKAGE_NAME = borednomore3

# Optimization
JOBS := $(shell nproc)
NUITKA_SPEED_FLAGS = --lto=no --jobs=$(JOBS)
DIST_BIN = dist/bin

# Colors
BLUE   = \033[0;34m
GREEN  = \033[0;32m
YELLOW = \033[1;33m
NC     = \033[0m

.PHONY: help build clean deb deb-src install-deb requirements

help:
	@echo "$(BLUE)BoredNoMore3 Build System$(NC)"
	@echo "$(YELLOW)make build$(NC)        - Build production binaries"
	@echo "$(YELLOW)make deb$(NC)          - Create binary .deb package"
	@echo "$(YELLOW)make deb-src$(NC)      - Create source .deb package"
	@echo "$(YELLOW)make install-deb$(NC)  - Build and install the .deb immediately"
	@echo "$(YELLOW)make clean$(NC)        - Remove all build artifacts"

requirements:
	@sudo apt update && sudo apt install -y python3-pip python3-pil python3-pynput \
		python3-requests pcmanfm-qt x11-xserver-utils build-essential python3-dev \
		upx-ucl python3-full patchelf python3-tk ccache
	@pip3 install --user nuitka customtkinter --break-system-packages || pip3 install --user nuitka customtkinter

build: clean
	@mkdir -p $(DIST_BIN)
	@echo "$(BLUE)Compiling Main GUI...$(NC)"
	@python3 -m nuitka --standalone --onefile --plugin-enable=tk-inter $(NUITKA_SPEED_FLAGS) --include-module=customtkinter --output-filename=$(BIN_GUI) --output-dir=dist $(SCRIPT_GUI)
	@echo "$(BLUE)Compiling Setter...$(NC)"
	@python3 -m nuitka --standalone --onefile $(NUITKA_SPEED_FLAGS) --include-module=borednomore3_transitions --output-filename=$(BIN_SETTER) --output-dir=dist $(SCRIPT_SETTER)
	@echo "$(BLUE)Compiling Downloader CLI...$(NC)"
	@python3 -m nuitka --standalone --onefile $(NUITKA_SPEED_FLAGS) --output-filename=$(BIN_DL) --output-dir=dist $(SCRIPT_DL)
	@echo "$(BLUE)Compiling Downloader GUI...$(NC)"
	@python3 -m nuitka --standalone --onefile --plugin-enable=tk-inter $(NUITKA_SPEED_FLAGS) --include-module=customtkinter --output-filename=$(BIN_DL_GUI) --output-dir=dist $(SCRIPT_DL_GUI)
	@mv dist/borednomore3* $(DIST_BIN)/ 2>/dev/null || true
	@upx --best $(DIST_BIN)/*
	@chmod +x $(DIST_BIN)/*

# --- BINARY DEBIAN PACKAGE ---
deb: build
	@echo "$(BLUE)Packaging Binary DEB...$(NC)"
	$(eval PKG_DIR := dist/pkg_bin)
	@mkdir -p $(PKG_DIR)/usr/bin
	@mkdir -p $(PKG_DIR)/DEBIAN
	@cp $(DIST_BIN)/* $(PKG_DIR)/usr/bin/
	@echo "Package: $(PACKAGE_NAME)\nVersion: $(VERSION)\nSection: utils\nPriority: optional\nArchitecture: amd64\nDepends: python3, python3-pil, python3-tk\nMaintainer: $(AUTHOR) <$(EMAIL)>\nDescription: Wallpaper suite binaries." > $(PKG_DIR)/DEBIAN/control
	@dpkg-deb --build $(PKG_DIR) $(PACKAGE_NAME)_$(VERSION)_amd64.deb
	@rm -rf $(PKG_DIR)
	@echo "$(GREEN)✓ Created: $(PACKAGE_NAME)_$(VERSION)_amd64.deb$(NC)"

# --- SOURCE DEBIAN PACKAGE ---
deb-src:
	@echo "$(BLUE)Packaging Source DEB...$(NC)"
	$(eval SRC_PKG_DIR := dist/pkg_src)
	@mkdir -p $(SRC_PKG_DIR)/usr/src/$(PACKAGE_NAME)
	@mkdir -p $(SRC_PKG_DIR)/DEBIAN
	@cp *.py $(SRC_PKG_DIR)/usr/src/$(PACKAGE_NAME)/
	@cp Makefile $(SRC_PKG_DIR)/usr/src/$(PACKAGE_NAME)/
	@echo "Package: $(PACKAGE_NAME)-src\nVersion: $(VERSION)\nSection: devel\nPriority: optional\nArchitecture: all\nMaintainer: $(AUTHOR) <$(EMAIL)>\nDescription: Source code for BoredNoMore3." > $(SRC_PKG_DIR)/DEBIAN/control
	@dpkg-deb --build $(SRC_PKG_DIR) $(PACKAGE_NAME)-src_$(VERSION)_all.deb
	@rm -rf $(SRC_PKG_DIR)
	@echo "$(GREEN)✓ Created: $(PACKAGE_NAME)-src_$(VERSION)_all.deb$(NC)"

# --- BUILD AND INSTALL DEB ---
install-deb: deb
	@echo "$(BLUE)Installing package...$(NC)"
	@sudo dpkg -i $(PACKAGE_NAME)_$(VERSION)_amd64.deb
	@sudo apt-get install -f
	@echo "$(GREEN)✓ BoredNoMore3 installed successfully!$(NC)"

clean:
	@rm -rf dist *.build *.dist *.onefile-build *.bin *.deb
	@echo "$(BLUE)✓ Cleaned$(NC)"
