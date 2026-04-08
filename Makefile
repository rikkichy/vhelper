PREFIX ?= /usr
DESTDIR ?=

BINDIR = $(DESTDIR)$(PREFIX)/bin
DATADIR = $(DESTDIR)$(PREFIX)/share
APPDIR = $(DATADIR)/vlauncher
DESKTOPDIR = $(DATADIR)/applications
ICONDIR = $(DATADIR)/icons/hicolor/scalable/apps

.PHONY: install uninstall

install:
	install -Dm755 data/vlauncher $(BINDIR)/vlauncher
	install -Dm644 vlauncher.py $(APPDIR)/vlauncher.py
	install -Dm644 data/com.vlauncher.app.desktop $(DESKTOPDIR)/com.vlauncher.app.desktop
	install -Dm644 data/icons/hicolor/scalable/apps/com.vlauncher.app.svg $(ICONDIR)/com.vlauncher.app.svg

uninstall:
	rm -f $(BINDIR)/vlauncher
	rm -f $(APPDIR)/vlauncher.py
	rmdir --ignore-fail-on-non-empty $(APPDIR)
	rm -f $(DESKTOPDIR)/com.vlauncher.app.desktop
	rm -f $(ICONDIR)/com.vlauncher.app.svg
