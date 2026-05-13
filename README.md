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
- **obs-pwvideo** — Bundled OBS plugin that exposes the PipeWire stream as a video source. Click _Install obs-pwvideo plugin_ in the main window and restart OBS. The bundled binary is built against `libobs.so.30`; if your OBS major version differs, vhelper warns and you should install `obs-pwvideo` from your distro package manager / AUR instead. Flatpak OBS is not supported.

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
- OBS Studio. `obs-pwvideo` is bundled, but if the bundled binary's `libobs.so` major doesn't match your OBS, fall back to your distro's package (e.g. [`obs-pwvideo`](https://aur.archlinux.org/packages/obs-pwvideo) on the AUR).
