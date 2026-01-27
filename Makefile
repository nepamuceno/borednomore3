PREFIX ?= /usr/local
BINDIR = $(PREFIX)/bin
LIBDIR = $(PREFIX)/lib/borednomore3
CONFDIR = /etc/borednomore3
DATADIR = $(PREFIX)/share
MANDIR = $(DATADIR)/man/man1
APPLICATIONSDIR = $(DATADIR)/applications
DOCDIR = $(DATADIR)/doc/borednomore3
WALLPAPERSDIR = $(DATADIR)/borednomore3/wallpapers

.PHONY: all install uninstall clean help deb

all:
	@echo "BoredNoMore3 Makefile"
	@echo ""
	@echo "Targets:"
	@echo "  make install    - Install to $(PREFIX)"
	@echo "  make uninstall  - Remove installation"
	@echo "  make clean      - Clean build artifacts"
	@echo "  make help       - Show this help"
	@echo "  make deb        - Build Debian package into ../debs/"

install:
	@echo "Installing BoredNoMore3..."

	# Create directories
	install -d $(DESTDIR)$(BINDIR)
	install -d $(DESTDIR)$(LIBDIR)
	install -d $(DESTDIR)$(CONFDIR)
	install -d $(DESTDIR)$(WALLPAPERSDIR)
	install -d $(DESTDIR)$(MANDIR)
	install -d $(DESTDIR)$(APPLICATIONSDIR)
	install -d $(DESTDIR)$(DOCDIR)

	# Install libraries
	cp -r borednomore3/libs $(DESTDIR)$(LIBDIR)/
	find $(DESTDIR)$(LIBDIR)/libs -type f -name "*.py" -exec chmod 644 {} \;
	find $(DESTDIR)$(LIBDIR)/libs -type d -exec chmod 755 {} \;

	# Install backend
	install -m 755 borednomore3/backend/borednomore3.py $(DESTDIR)$(LIBDIR)/

	# Install frontend (GUI)
	install -m 755 borednomore3/frontend/bnm3.py $(DESTDIR)$(LIBDIR)/

	# Install downloader
	install -m 755 borednomore3_downloader.py $(DESTDIR)$(BINDIR)/borednomore3-downloader

	# Create wrapper script for backend
	@echo '#!/bin/bash' > $(DESTDIR)$(BINDIR)/borednomore3
	@echo 'exec python3 "$(LIBDIR)/borednomore3.py" "$$@"' >> $(DESTDIR)$(BINDIR)/borednomore3
	@chmod 755 $(DESTDIR)$(BINDIR)/borednomore3

	# Create wrapper script for GUI (bnm3)
	@echo '#!/bin/bash' > $(DESTDIR)$(BINDIR)/bnm3
	@echo 'exec python3 "$(LIBDIR)/bnm3.py" "$$@"' >> $(DESTDIR)$(BINDIR)/bnm3
	@chmod 755 $(DESTDIR)$(BINDIR)/bnm3

	# Install config examples
	install -m 644 borednomore3/conf/borednomore3.conf-example $(DESTDIR)$(CONFDIR)/borednomore3.conf
	install -m 644 borednomore3/conf/borednomore3.list-example $(DESTDIR)$(CONFDIR)/borednomore3.list

	# Install man pages
	install -m 644 debian/borednomore3.1 $(DESTDIR)$(MANDIR)/
	install -m 644 debian/bnm3.1 $(DESTDIR)$(MANDIR)/
	install -m 644 debian/borednomore3-downloader.1 $(DESTDIR)$(MANDIR)/
	gzip -f $(DESTDIR)$(MANDIR)/borednomore3.1
	gzip -f $(DESTDIR)$(MANDIR)/bnm3.1
	gzip -f $(DESTDIR)$(MANDIR)/borednomore3-downloader.1

	# Install desktop files
	install -m 644 debian/bnm3.desktop $(DESTDIR)$(APPLICATIONSDIR)/
	install -m 644 debian/borednomore3-downloader.desktop $(DESTDIR)$(APPLICATIONSDIR)/

	# Install documentation
	install -m 644 README.md $(DESTDIR)$(DOCDIR)/
	install -m 644 DOWNLOADER.md $(DESTDIR)$(DOCDIR)/

	@echo ""
	@echo "Installation complete!"
	@echo ""
	@echo "Available commands:"
	@echo "  borednomore3              - Backend daemon (CLI)"
	@echo "  bnm3                      - GUI interface"
	@echo "  borednomore3-downloader   - Wallpaper downloader"
	@echo ""
	@echo "Configuration: $(CONFDIR)/"
	@echo "Wallpapers: $(WALLPAPERSDIR)/"

uninstall:
	@echo "Uninstalling BoredNoMore3..."
	rm -f $(DESTDIR)$(BINDIR)/borednomore3
	rm -f $(DESTDIR)$(BINDIR)/bnm3
	rm -f $(DESTDIR)$(BINDIR)/borednomore3-downloader
	rm -rf $(DESTDIR)$(LIBDIR)
	rm -rf $(DESTDIR)$(CONFDIR)
	rm -rf $(DESTDIR)$(WALLPAPERSDIR)
	rm -f $(DESTDIR)$(MANDIR)/borednomore3.1.gz
	rm -f $(DESTDIR)$(MANDIR)/bnm3.1.gz
	rm -f $(DESTDIR)$(MANDIR)/borednomore3-downloader.1.gz
	rm -f $(DESTDIR)$(APPLICATIONSDIR)/bnm3.desktop
	rm -f $(DESTDIR)$(APPLICATIONSDIR)/borednomore3-downloader.desktop
	rm -rf $(DESTDIR)$(DOCDIR)
	@echo "Uninstallation complete!"

clean:
	@echo "Cleaning build artifacts..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf build/ dist/ *.egg-info/
	@echo "Clean complete!"

deb:
	@echo "Building Debian package into ../debs/"
	mkdir -p ../debs
	dpkg-buildpackage -us -uc -b
	mv ../*.deb ../debs/ || true
	mv ../*.changes ../debs/ || true
	mv ../*.buildinfo ../debs/ || true
	@echo "✅ Packages moved to ../debs/"

help:
	@echo "BoredNoMore3 Makefile"
	@echo ""
	@echo "Usage:"
	@echo "  make install PREFIX=/usr        - System-wide install"
	@echo "  make install PREFIX=~/.local    - User install"
	@echo "  make uninstall                  - Remove installation"
	@echo "  make clean                      - Clean build files"
	@echo "  make deb                        - Build Debian package into ../debs/"
	@echo ""
	@echo "Environment variables:"
	@echo "  PREFIX      - Installation prefix (default: /usr/local)"
	@echo "  DESTDIR     - Staging directory for packaging"
	@echo ""
	@echo "Installed binaries:"
	@echo "  $(BINDIR)/borednomore3          - Backend daemon"
	@echo "  $(BINDIR)/bnm3                  - GUI interface"
	@echo "  $(BINDIR)/borednomore3-downloader - Downloader utility"

