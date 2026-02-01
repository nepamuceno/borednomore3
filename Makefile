PREFIX ?= /usr
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
	@echo "BoredNoMore3 Full Build System"

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

	# Install backends
	install -m 755 borednomore3/backend/borednomore3.py $(DESTDIR)$(LIBDIR)/
	install -m 755 borednomore3/backend/bnm3d.py $(DESTDIR)$(LIBDIR)/

	# Install frontends
	install -m 755 borednomore3/frontend/bnm3.py $(DESTDIR)$(LIBDIR)/
	install -m 755 borednomore3/frontend/bnm3d-gui.py $(DESTDIR)$(LIBDIR)/

	# Create all 4 wrappers
	@echo '#!/bin/bash' > $(DESTDIR)$(BINDIR)/borednomore3
	@echo 'exec python3 $(LIBDIR)/borednomore3.py "$$@"' >> $(DESTDIR)$(BINDIR)/borednomore3
	
	@echo '#!/bin/bash' > $(DESTDIR)$(BINDIR)/bnm3d
	@echo 'exec python3 $(LIBDIR)/bnm3d.py "$$@"' >> $(DESTDIR)$(BINDIR)/bnm3d

	@echo '#!/bin/bash' > $(DESTDIR)$(BINDIR)/bnm3
	@echo 'exec python3 $(LIBDIR)/bnm3.py "$$@"' >> $(DESTDIR)$(BINDIR)/bnm3

	@echo '#!/bin/bash' > $(DESTDIR)$(BINDIR)/bnm3d-gui
	@echo 'exec python3 $(LIBDIR)/bnm3d-gui.py "$$@"' >> $(DESTDIR)$(BINDIR)/bnm3d-gui

	chmod 755 $(DESTDIR)$(BINDIR)/borednomore3 $(DESTDIR)$(BINDIR)/bnm3d $(DESTDIR)$(BINDIR)/bnm3 $(DESTDIR)$(BINDIR)/bnm3d-gui

	# Install configs
	install -m 644 borednomore3/conf/bnm3d.conf-example $(DESTDIR)$(CONFDIR)/bnm3d.conf
	install -m 644 borednomore3/conf/borednomore3.conf-example $(DESTDIR)$(CONFDIR)/borednomore3.conf
	install -m 644 borednomore3/conf/borednomore3.list-example $(DESTDIR)$(CONFDIR)/borednomore3.list

uninstall:
	rm -f $(DESTDIR)$(BINDIR)/borednomore3 $(DESTDIR)$(BINDIR)/bnm3d $(DESTDIR)$(BINDIR)/bnm3 $(DESTDIR)$(BINDIR)/bnm3d-gui
	rm -rf $(DESTDIR)$(LIBDIR)
	rm -rf $(DESTDIR)$(CONFDIR)

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete

deb:
	mkdir -p ../debs
	dpkg-buildpackage -us -uc -b
	mv ../*.deb ../debs/ || true
	mv ../*.changes ../debs/ || true
	mv ../*.buildinfo ../debs/ || true
