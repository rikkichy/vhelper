<p align="center">
  <img
    src="data/icons/hicolor/scalable/apps/com.vhelper.app.svg"
    alt="VHelper logo"
    width="160"
  />
</p>

<h1 align="center">VHelper</h1>

<h3 align="center">Make vtubing suck less on Linux.</h3>

<p align="center">
<img alt="GitHub License" src="https://img.shields.io/github/license/rikkichy/VHelper?style=for-the-badge&labelColor=2D3142&color=B0D7FF">
</p>

---

## Features

- **Shoost** — Install, launch, and manage Shoost inside VTube Studio's Proton container for proper Spout2 texture sharing
- **spout2pw** — Download and install spout2pw to bridge Spout2 output to PipeWire for OBS
- **NTSYNC** — Toggle NT synchronization for better performance (Linux 6.14+)

## Build

> [!NOTE]
> This part is intended for developers who want to build VHelper from source.

```bash
git clone https://github.com/rikkichy/VHelper.git
```
```bash
cd VHelper
```
```bash
makepkg -si
```

## Dependencies

- `python`, `python-gobject`, `gtk4`, `libadwaita`
- `protontricks`
- [`obs-pwvideo`](https://aur.archlinux.org/packages/obs-pwvideo) (AUR) — OBS plugin for PipeWire video sources
