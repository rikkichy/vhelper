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

## AUR Install (Arch Linux)
```sh
paru -S vhelper
```
OR
```sh
yay -S vhelper
```
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
