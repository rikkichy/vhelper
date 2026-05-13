<p align="center">
  <img
    src="data/icons/hicolor/scalable/apps/com.vhelper.app.svg"
    alt="vhelper logo"
    width="160"
  />
</p>

<h1 align="center">vhelper</h1>

<h3 align="center">Make vtubing suck less on Linux.</h3>

<p align="center">
<img alt="GitHub License" src="https://img.shields.io/github/license/rikkichy/vhelper?style=for-the-badge&labelColor=2D3142&color=B0D7FF">
</p>

---

## Quick Install

```sh
curl -fsSL https://raw.githubusercontent.com/rikkichy/vhelper/main/install.sh | sh
```

Works on Arch, Debian/Ubuntu, Fedora, openSUSE, and Void.

## Features

- **Shoost** — Install, launch, and manage Shoost inside VTube Studio's Proton container for proper Spout2 texture sharing
- **spout2pw** — Bundled spout2pw bridges Spout2 output to PipeWire for OBS

## Build

> [!NOTE]
> This part is intended for developers who want to build vhelper from source.

```bash
git clone https://github.com/rikkichy/vhelper.git
```
```bash
cd vhelper
```
```bash
makepkg -si
```

## Dependencies

- `python`, `python-gobject`, `gtk4`, `libadwaita`
- `protontricks`
- [`obs-pwvideo`](https://aur.archlinux.org/packages/obs-pwvideo) (AUR) — OBS plugin for PipeWire video sources
