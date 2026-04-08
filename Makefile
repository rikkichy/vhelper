PREFIX ?= /usr
DESTDIR ?=

BINDIR = $(DESTDIR)$(PREFIX)/bin
DATADIR = $(DESTDIR)$(PREFIX)/share
APPDIR = $(DATADIR)/vhelper
DESKTOPDIR = $(DATADIR)/applications
ICONDIR = $(DATADIR)/icons/hicolor/scalable/apps

.PHONY: install uninstall

install:
	install -Dm755 data/vhelper $(BINDIR)/vhelper
	install -Dm644 vhelper.py $(APPDIR)/vhelper.py
	install -Dm644 data/com.vhelper.app.desktop $(DESKTOPDIR)/com.vhelper.app.desktop
	install -Dm644 data/icons/hicolor/scalable/apps/com.vhelper.app.svg $(ICONDIR)/com.vhelper.app.svg

uninstall:
	rm -f $(BINDIR)/vhelper
	rm -f $(APPDIR)/vhelper.py
	rmdir --ignore-fail-on-non-empty $(APPDIR)
	rm -f $(DESKTOPDIR)/com.vhelper.app.desktop
	rm -f $(ICONDIR)/com.vhelper.app.svg
