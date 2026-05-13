#!/usr/bin/env python3

import gi
import json
import os
import shutil
import subprocess
import tarfile
import zipfile
from pathlib import Path

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gio, GLib, Gtk

STEAM_ROOT = Path.home() / ".local/share/Steam"
VTS_APPID = "1325860"
VTS_COMPAT = STEAM_ROOT / "steamapps/compatdata" / VTS_APPID
VTS_PREFIX = VTS_COMPAT / "pfx"
SHOOST_DIR = VTS_PREFIX / "drive_c/Shoost"
SPOUT2PW_DIR = Path.home() / ".local/share/spout2pw"
CONFIG_FILE = Path.home() / ".config/vhelper.json"


def detect_proton_from_config():
    config = VTS_COMPAT / "config_info"
    if not config.exists():
        return None
    lines = config.read_text().splitlines()
    for line in lines:
        if "compatibilitytools.d" in line and "files/" in line:
            base = line.split("/files/")[0]
            return Path(base)
    return None


def find_shoost_exe():
    if not SHOOST_DIR.exists():
        return None
    for exe in sorted(SHOOST_DIR.glob("*.exe")):
        name = exe.name.lower()
        if "shoost" in name and "crash" not in name and "unity" not in name.replace("shoost", ""):
            return exe
    return None


def find_spout2pw():
    cfg = load_config()
    custom = cfg.get("spout2pw_path")
    if custom:
        p = Path(custom)
        if p.exists():
            return p

    default = SPOUT2PW_DIR / "spout2pw.sh"
    if default.exists():
        return default

    return None


def detect_vhelper_install():
    """Return install prefix Path if vhelper was launched from an install
    (e.g. /usr/local), or None when running from a source checkout."""
    py = Path(__file__).resolve()
    if py.parent.name != "vhelper" or py.parent.parent.name != "share":
        return None
    prefix = py.parent.parent.parent
    if not (prefix / "bin/vhelper").exists():
        return None
    return prefix


def find_bundled_spout2pw():
    """Return the directory containing the vendored spout2pw files, or None."""
    py = Path(__file__).resolve()
    for cand in (py.parent / "spout2pw-bundle", py.parent / "data/spout2pw"):
        if (cand / "spout2pw.sh").exists():
            return cand
    return None


def load_config():
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text())
    return {}


def save_config(cfg):
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2))


class VHelperWindow(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="VHelper", default_width=520, default_height=580)

        self.proton_path = detect_proton_from_config()
        self.shoost_proc = None
        self.shoost_exe = find_shoost_exe()
        self.spout2pw_sh = find_spout2pw()
        self.cfg = load_config()
        self.use_ntsync = self.cfg.get("ntsync", False)
        self.install_prefix = detect_vhelper_install()
        self.bundled_spout2pw = find_bundled_spout2pw()

        header = Adw.HeaderBar()

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        content.append(header)

        scrollable = Gtk.ScrolledWindow(vexpand=True)
        clamp = Adw.Clamp(maximum_size=600)
        inner = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        inner.set_margin_top(24)
        inner.set_margin_bottom(24)
        inner.set_margin_start(12)
        inner.set_margin_end(12)
        clamp.set_child(inner)
        scrollable.set_child(clamp)
        content.append(scrollable)

        status_group = Adw.PreferencesGroup(title="Status")

        self.vts_row = Adw.ActionRow(title="VTube Studio Prefix")
        self.vts_row.set_subtitle(str(VTS_PREFIX) if VTS_PREFIX.exists() else "Not found")
        self.vts_row.add_suffix(Gtk.Image.new_from_icon_name(
            "emblem-ok-symbolic" if VTS_PREFIX.exists() else "dialog-error-symbolic"
        ))
        status_group.add(self.vts_row)

        self.proton_row = Adw.ActionRow(title="Proton Runtime")
        proton_name = self.proton_path.name if self.proton_path else "Not detected"
        proton_ok = self.proton_path and (self.proton_path / "files/bin/wine64").exists()
        self.proton_row.set_subtitle(proton_name)
        self.proton_row.add_suffix(Gtk.Image.new_from_icon_name(
            "emblem-ok-symbolic" if proton_ok else "dialog-error-symbolic"
        ))
        status_group.add(self.proton_row)

        self.shoost_row = Adw.ActionRow(title="Shoost")
        self._update_shoost_status()
        status_group.add(self.shoost_row)

        self.spout2pw_row = Adw.ActionRow(title="spout2pw")
        self._update_spout2pw_status()
        status_group.add(self.spout2pw_row)

        inner.append(status_group)

        options_group = Adw.PreferencesGroup(title="Options")

        ntsync_available = Path("/dev/ntsync").exists()
        ntsync_row = Adw.SwitchRow(
            title="NTSYNC",
            subtitle="/dev/ntsync " + ("available" if ntsync_available else "not found"),
        )
        ntsync_row.set_active(self.use_ntsync)
        ntsync_row.set_sensitive(ntsync_available)
        ntsync_row.connect("notify::active", self._on_ntsync_toggled)
        options_group.add(ntsync_row)

        inner.append(options_group)

        shoost_group = Adw.PreferencesGroup(title="Shoost")

        extract_row = Adw.ActionRow(
            title="Install Shoost",
            subtitle="Pick a Shoost zip and extract into VTS prefix",
        )
        self.extract_btn = Gtk.Button(label="Browse...", valign=Gtk.Align.CENTER)
        self.extract_btn.add_css_class("suggested-action")
        self.extract_btn.connect("clicked", self.on_extract_shoost)
        extract_row.add_suffix(self.extract_btn)
        extract_row.set_activatable_widget(self.extract_btn)
        shoost_group.add(extract_row)

        launch_row = Adw.ActionRow(
            title="Launch Shoost",
            subtitle="Run inside VTS's container via protontricks",
        )
        info_btn = Gtk.Button(icon_name="dialog-information-symbolic", valign=Gtk.Align.CENTER)
        info_btn.set_tooltip_text("Show terminal command")
        info_btn.connect("clicked", self.on_show_shoost_command)
        launch_row.add_suffix(info_btn)
        self.launch_btn = Gtk.Button(label="Launch", valign=Gtk.Align.CENTER)
        self.launch_btn.add_css_class("suggested-action")
        self.launch_btn.connect("clicked", self.on_launch_shoost)
        launch_row.add_suffix(self.launch_btn)
        launch_row.set_activatable_widget(self.launch_btn)
        shoost_group.add(launch_row)

        stop_row = Adw.ActionRow(
            title="Stop Shoost",
            subtitle="Kill the running Shoost process",
        )
        self.stop_btn = Gtk.Button(label="Stop", valign=Gtk.Align.CENTER)
        self.stop_btn.add_css_class("destructive-action")
        self.stop_btn.connect("clicked", self.on_stop_shoost)
        stop_row.add_suffix(self.stop_btn)
        stop_row.set_activatable_widget(self.stop_btn)
        shoost_group.add(stop_row)

        uninstall_row = Adw.ActionRow(
            title="Uninstall Shoost",
            subtitle=str(SHOOST_DIR),
        )
        self.uninstall_btn = Gtk.Button(label="Uninstall", valign=Gtk.Align.CENTER)
        self.uninstall_btn.add_css_class("destructive-action")
        self.uninstall_btn.connect("clicked", self.on_uninstall_shoost)
        uninstall_row.add_suffix(self.uninstall_btn)
        uninstall_row.set_activatable_widget(self.uninstall_btn)
        shoost_group.add(uninstall_row)

        inner.append(shoost_group)

        spout2pw_group = Adw.PreferencesGroup(
            title="spout2pw",
            description="Bridge Spout2 output to PipeWire for OBS",
        )

        install_s2p_row = Adw.ActionRow(
            title="Install spout2pw",
            subtitle="Use the bundled binaries or pick a local tarball",
        )
        self.install_bundled_btn = Gtk.Button(label="Install bundled", valign=Gtk.Align.CENTER)
        self.install_bundled_btn.add_css_class("suggested-action")
        self.install_bundled_btn.connect("clicked", self.on_install_bundled_spout2pw)
        install_s2p_row.add_suffix(self.install_bundled_btn)
        self.install_s2p_btn = Gtk.Button(label="Install from file", valign=Gtk.Align.CENTER)
        self.install_s2p_btn.connect("clicked", self.on_install_spout2pw)
        install_s2p_row.add_suffix(self.install_s2p_btn)
        install_s2p_row.set_activatable_widget(self.install_bundled_btn)
        spout2pw_group.add(install_s2p_row)

        vts_opts_row = Adw.ActionRow(
            title="VTube Studio Launch Options",
            subtitle="Set in Steam > VTube Studio > Properties > Launch Options",
        )
        self.vts_opts_info_btn = Gtk.Button(
            icon_name="dialog-information-symbolic", valign=Gtk.Align.CENTER
        )
        self.vts_opts_info_btn.set_tooltip_text("Show launch options")
        self.vts_opts_info_btn.connect("clicked", self.on_show_vts_launch_opts)
        vts_opts_row.add_suffix(self.vts_opts_info_btn)
        copy_opts_btn = Gtk.Button(icon_name="edit-copy-symbolic", valign=Gtk.Align.CENTER)
        copy_opts_btn.set_tooltip_text("Copy launch options")
        copy_opts_btn.connect("clicked", self.on_copy_vts_launch_opts)
        vts_opts_row.add_suffix(copy_opts_btn)
        spout2pw_group.add(vts_opts_row)

        uninstall_s2p_row = Adw.ActionRow(
            title="Uninstall spout2pw",
            subtitle=str(SPOUT2PW_DIR),
        )
        self.uninstall_s2p_btn = Gtk.Button(label="Uninstall", valign=Gtk.Align.CENTER)
        self.uninstall_s2p_btn.add_css_class("destructive-action")
        self.uninstall_s2p_btn.connect("clicked", self.on_uninstall_spout2pw)
        uninstall_s2p_row.add_suffix(self.uninstall_s2p_btn)
        uninstall_s2p_row.set_activatable_widget(self.uninstall_s2p_btn)
        spout2pw_group.add(uninstall_s2p_row)

        inner.append(spout2pw_group)

        if self.install_prefix:
            vh_group = Adw.PreferencesGroup(
                title="vhelper",
                description=f"Installed at {self.install_prefix}",
            )
            uninstall_vh_row = Adw.ActionRow(
                title="Uninstall vhelper",
                subtitle="Removes the app. Shoost and spout2pw stay installed.",
            )
            self.uninstall_vh_btn = Gtk.Button(label="Uninstall", valign=Gtk.Align.CENTER)
            self.uninstall_vh_btn.add_css_class("destructive-action")
            self.uninstall_vh_btn.connect("clicked", self.on_uninstall_vhelper)
            uninstall_vh_row.add_suffix(self.uninstall_vh_btn)
            uninstall_vh_row.set_activatable_widget(self.uninstall_vh_btn)
            vh_group.add(uninstall_vh_row)
            inner.append(vh_group)

        log_group = Adw.PreferencesGroup(title="Log")
        self.log_view = Gtk.TextView(editable=False, monospace=True)
        self.log_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.log_buf = self.log_view.get_buffer()

        scroll = Gtk.ScrolledWindow(vexpand=True, min_content_height=100)
        scroll.set_child(self.log_view)

        frame = Gtk.Frame()
        frame.set_child(scroll)
        log_group.add(frame)
        inner.append(log_group)

        self.set_content(content)
        self._update_buttons()
        self._update_s2p_btn_labels()

    def _log(self, msg):
        end = self.log_buf.get_end_iter()
        self.log_buf.insert(end, msg + "\n")
        end = self.log_buf.get_end_iter()
        self.log_view.scroll_to_iter(end, 0, False, 0, 0)

    def _on_ntsync_toggled(self, row, _pspec):
        self.use_ntsync = row.get_active()
        self.cfg["ntsync"] = self.use_ntsync
        save_config(self.cfg)

    def _set_row_status(self, row, subtitle, ok):
        row.set_subtitle(subtitle)
        old = getattr(row, "_status_icon", None)
        if old:
            row.remove(old)
        icon = Gtk.Image.new_from_icon_name(
            "emblem-ok-symbolic" if ok else "dialog-warning-symbolic"
        )
        row.add_suffix(icon)
        row._status_icon = icon

    def _update_shoost_status(self):
        if self.shoost_exe:
            self._set_row_status(self.shoost_row, self.shoost_exe.name, True)
        else:
            self._set_row_status(self.shoost_row, "Not installed", False)

    def _update_spout2pw_status(self):
        if self.spout2pw_sh:
            self._set_row_status(self.spout2pw_row, str(self.spout2pw_sh.parent), True)
        else:
            self._set_row_status(self.spout2pw_row, "Not installed", False)
        if hasattr(self, "install_bundled_btn"):
            self._update_s2p_btn_labels()

    def _update_buttons(self):
        installed = self.shoost_exe is not None
        self.launch_btn.set_sensitive(installed and self.shoost_proc is None)
        self.stop_btn.set_sensitive(self.shoost_proc is not None)
        self.uninstall_btn.set_sensitive(installed and self.shoost_proc is None)
        self.install_bundled_btn.set_sensitive(
            self.bundled_spout2pw is not None and self.spout2pw_sh is None
        )
        self.install_s2p_btn.set_sensitive(self.spout2pw_sh is None)
        self.uninstall_s2p_btn.set_sensitive(self.spout2pw_sh is not None)

    def _get_vts_launch_opts(self):
        ntsync = "PROTON_USE_NTSYNC=1 " if self.use_ntsync else ""
        if self.spout2pw_sh:
            return f"{ntsync}{self.spout2pw_sh} %command%"
        return f"{ntsync}{SPOUT2PW_DIR}/spout2pw.sh %command%"

    def _show_copy_dialog(self, heading, body, copy_text=None):
        dialog = Adw.MessageDialog(
            transient_for=self,
            heading=heading,
            body=body,
        )
        dialog.add_response("copy", "Copy")
        dialog.add_response("close", "Close")
        dialog.set_response_appearance("copy", Adw.ResponseAppearance.SUGGESTED)
        dialog.connect("response", self._on_copy_dialog_response, copy_text or body)
        dialog.present()

    def _on_copy_dialog_response(self, _dialog, response, text):
        if response == "copy":
            self.get_clipboard().set(text)
            self._log("Copied to clipboard")

    def on_extract_shoost(self, _btn):
        dialog = Gtk.FileDialog()
        dialog.set_title("Select Shoost zip")
        zip_filter = Gtk.FileFilter()
        zip_filter.set_name("Zip archives")
        zip_filter.add_pattern("*.zip")
        filters = Gio.ListStore.new(Gtk.FileFilter)
        filters.append(zip_filter)
        dialog.set_filters(filters)

        downloads = Path.home() / "Downloads"
        if downloads.exists():
            dialog.set_initial_folder(Gio.File.new_for_path(str(downloads)))

        dialog.open(self, None, self._on_shoost_zip_picked)

    def _on_shoost_zip_picked(self, dialog, result):
        try:
            file = dialog.open_finish(result)
        except GLib.Error:
            return

        zip_path = Path(file.get_path())
        self._log(f"Selected: {zip_path.name}")

        try:
            with zipfile.ZipFile(zip_path) as zf:
                names = zf.namelist()

                top_dirs = {n.split("/")[0] for n in names if "/" in n}
                strip_prefix = (top_dirs.pop() + "/") if len(top_dirs) == 1 else ""

                exe_name = None
                for n in names:
                    rel = n[len(strip_prefix):] if strip_prefix else n
                    if rel.lower().endswith(".exe") and "shoost" in rel.lower() and "/" not in rel:
                        exe_name = rel
                        break

                if not exe_name:
                    self._log("ERROR: No Shoost .exe found in zip")
                    return

                if SHOOST_DIR.exists():
                    shutil.rmtree(SHOOST_DIR)
                    self._log("Removed old Shoost installation")

                SHOOST_DIR.mkdir(parents=True, exist_ok=True)

                for info in zf.infolist():
                    if strip_prefix and not info.filename.startswith(strip_prefix):
                        continue
                    rel = info.filename[len(strip_prefix):] if strip_prefix else info.filename
                    if not rel:
                        continue
                    dest = SHOOST_DIR / rel
                    if info.is_dir():
                        dest.mkdir(parents=True, exist_ok=True)
                    else:
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        with zf.open(info) as src, open(dest, "wb") as dst:
                            shutil.copyfileobj(src, dst)

                self.shoost_exe = SHOOST_DIR / exe_name
                self._log(f"Extracted {exe_name} to {SHOOST_DIR}")

        except Exception as e:
            self._log(f"ERROR: {e}")

        self._update_shoost_status()
        self._update_buttons()

    def on_show_shoost_command(self, _btn):
        if not self.shoost_exe:
            self._log("Shoost not installed")
            return
        ntsync = "PROTON_USE_NTSYNC=1 " if self.use_ntsync else ""
        cmd = f"{ntsync}protontricks-launch --appid {VTS_APPID} '{self.shoost_exe}'"
        self._show_copy_dialog("Terminal Command", cmd)

    def on_launch_shoost(self, _btn):
        if not self.shoost_exe or not self.shoost_exe.exists():
            self._log("ERROR: Shoost not installed")
            return

        cmd = [
            "protontricks-launch",
            "--appid", VTS_APPID,
            str(self.shoost_exe),
        ]

        env = os.environ.copy()
        if self.use_ntsync:
            env["PROTON_USE_NTSYNC"] = "1"
            self._log("NTSYNC enabled")
        self._log(f"Launching {self.shoost_exe.name} via protontricks-launch")

        try:
            self.shoost_proc = subprocess.Popen(
                cmd,
                env=env,
                cwd=str(SHOOST_DIR),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
            self._log(f"Started (PID {self.shoost_proc.pid})")
            GLib.io_add_watch(
                GLib.IOChannel.unix_new(self.shoost_proc.stdout.fileno()),
                GLib.IOCondition.IN | GLib.IOCondition.HUP,
                self._on_proc_output,
            )
        except Exception as e:
            self._log(f"ERROR: {e}")
            self.shoost_proc = None

        self._update_buttons()

    def _on_proc_output(self, channel, condition):
        if condition & GLib.IOCondition.IN:
            try:
                line = channel.readline()
                if line:
                    self._log(line.rstrip("\n"))
                    return True
            except Exception:
                pass

        if self.shoost_proc:
            ret = self.shoost_proc.poll()
            self._log(f"Shoost exited (code {ret})")
            self.shoost_proc = None
            self._update_buttons()
        return False

    def on_stop_shoost(self, _btn):
        if self.shoost_proc:
            self._log("Stopping Shoost...")
            self.shoost_proc.terminate()
            try:
                self.shoost_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.shoost_proc.kill()
            self._log("Stopped")
            self.shoost_proc = None
            self._update_buttons()

    def on_uninstall_shoost(self, _btn):
        if not SHOOST_DIR.exists():
            self._log("Nothing to uninstall")
            return

        try:
            shutil.rmtree(SHOOST_DIR)
            self.shoost_exe = None
            self._log(f"Removed {SHOOST_DIR}")
        except Exception as e:
            self._log(f"ERROR: {e}")

        self._update_shoost_status()
        self._update_buttons()

    def on_install_bundled_spout2pw(self, _btn):
        if not self.bundled_spout2pw:
            self._log("ERROR: No bundled spout2pw found")
            return
        self._log(f"Installing bundled spout2pw from {self.bundled_spout2pw}")
        try:
            if SPOUT2PW_DIR.exists():
                shutil.rmtree(SPOUT2PW_DIR)
            shutil.copytree(self.bundled_spout2pw, SPOUT2PW_DIR)
            self.spout2pw_sh = SPOUT2PW_DIR / "spout2pw.sh"
            self.spout2pw_sh.chmod(self.spout2pw_sh.stat().st_mode | 0o111)
            self._log(f"Installed spout2pw to {SPOUT2PW_DIR}")
            self._log(f"Set VTS launch options to: {self._get_vts_launch_opts()}")
        except Exception as e:
            self._log(f"ERROR: {e}")
        self._update_spout2pw_status()
        self._update_buttons()

    def _update_s2p_btn_labels(self):
        if self.spout2pw_sh:
            self.install_bundled_btn.set_label("Installed")
            self.install_bundled_btn.set_visible(True)
            self.install_s2p_btn.set_visible(False)
        elif self.bundled_spout2pw:
            self.install_bundled_btn.set_label("Install bundled")
            self.install_bundled_btn.set_visible(True)
            self.install_s2p_btn.set_visible(True)
        else:
            self.install_bundled_btn.set_visible(False)
            self.install_s2p_btn.set_visible(True)

    def _extract_spout2pw_tar(self, tar_path):
        try:
            with tarfile.open(tar_path, "r:gz") as tf:
                members = tf.getnames()

                top_dirs = {m.split("/")[0] for m in members if "/" in m}
                strip_prefix = (top_dirs.pop() + "/") if len(top_dirs) == 1 else ""

                sh_found = any(
                    (m[len(strip_prefix):] if strip_prefix else m) == "spout2pw.sh"
                    for m in members
                )
                if not sh_found:
                    self._log("ERROR: spout2pw.sh not found in tarball")
                    return

                if SPOUT2PW_DIR.exists():
                    shutil.rmtree(SPOUT2PW_DIR)

                SPOUT2PW_DIR.mkdir(parents=True, exist_ok=True)

                for member in tf.getmembers():
                    if strip_prefix and not member.name.startswith(strip_prefix):
                        continue
                    rel = member.name[len(strip_prefix):] if strip_prefix else member.name
                    if not rel:
                        continue

                    dest = SPOUT2PW_DIR / rel
                    if member.isdir():
                        dest.mkdir(parents=True, exist_ok=True)
                    elif member.isfile():
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        with tf.extractfile(member) as src, open(dest, "wb") as dst:
                            shutil.copyfileobj(src, dst)
                        if member.mode & 0o111:
                            dest.chmod(dest.stat().st_mode | 0o111)

                self.spout2pw_sh = SPOUT2PW_DIR / "spout2pw.sh"
                self._log(f"Installed spout2pw to {SPOUT2PW_DIR}")
                self._log(f"Set VTS launch options to: {self._get_vts_launch_opts()}")

        except Exception as e:
            self._log(f"ERROR: {e}")

        self._update_spout2pw_status()
        self._update_buttons()

    def on_install_spout2pw(self, _btn):
        dialog = Gtk.FileDialog()
        dialog.set_title("Select spout2pw tarball")
        tar_filter = Gtk.FileFilter()
        tar_filter.set_name("Tarballs (.tar.gz)")
        tar_filter.add_pattern("*.tar.gz")
        filters = Gio.ListStore.new(Gtk.FileFilter)
        filters.append(tar_filter)
        dialog.set_filters(filters)

        downloads = Path.home() / "Downloads"
        if downloads.exists():
            dialog.set_initial_folder(Gio.File.new_for_path(str(downloads)))

        dialog.open(self, None, self._on_spout2pw_tar_picked)

    def _on_spout2pw_tar_picked(self, dialog, result):
        try:
            file = dialog.open_finish(result)
        except GLib.Error:
            return

        tar_path = Path(file.get_path())
        self._log(f"Selected: {tar_path.name}")
        self._extract_spout2pw_tar(tar_path)

    def on_show_vts_launch_opts(self, _btn):
        opts = self._get_vts_launch_opts()
        self._show_copy_dialog(
            "VTube Studio Launch Options",
            f"Set this in Steam > VTube Studio > Properties > General > Launch Options:\n\n{opts}",
            copy_text=opts,
        )

    def on_copy_vts_launch_opts(self, _btn):
        opts = self._get_vts_launch_opts()
        self.get_clipboard().set(opts)
        self._log(f"Copied: {opts}")

    def on_uninstall_spout2pw(self, _btn):
        if not SPOUT2PW_DIR.exists():
            self._log("Nothing to uninstall")
            return

        try:
            shutil.rmtree(SPOUT2PW_DIR)
            self.spout2pw_sh = None
            self._log(f"Removed {SPOUT2PW_DIR}")
        except Exception as e:
            self._log(f"ERROR: {e}")

        self._update_spout2pw_status()
        self._update_buttons()

    def _vhelper_install_paths(self):
        p = self.install_prefix
        return [
            p / "bin/vhelper",
            p / "share/vhelper",
            p / "share/applications/com.vhelper.app.desktop",
            p / "share/icons/hicolor/scalable/apps/com.vhelper.app.svg",
        ]

    def on_uninstall_vhelper(self, _btn):
        existing = [p for p in self._vhelper_install_paths() if p.exists()]
        if not existing:
            self._log("Nothing to uninstall")
            return
        files_list = "\n".join(f"  • {p}" for p in existing)
        dialog = Adw.MessageDialog(
            transient_for=self,
            heading="Uninstall vhelper?",
            body=(
                f"This will remove:\n\n{files_list}\n\n"
                "Shoost and spout2pw installations are not affected."
            ),
        )
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("uninstall", "Uninstall")
        dialog.set_response_appearance("uninstall", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.set_default_response("cancel")
        dialog.connect("response", self._on_uninstall_vhelper_response, existing)
        dialog.present()

    def _on_uninstall_vhelper_response(self, _dialog, response, existing):
        if response != "uninstall":
            return

        needs_root = not os.access(self.install_prefix, os.W_OK)
        self._log("Uninstalling vhelper...")

        try:
            if needs_root:
                if not shutil.which("pkexec"):
                    self._log("ERROR: pkexec not available; cannot remove root-owned files")
                    return
                result = subprocess.run(
                    ["pkexec", "rm", "-rf", *[str(p) for p in existing]],
                    capture_output=True, text=True,
                )
                if result.returncode != 0:
                    self._log(f"ERROR: {(result.stderr or result.stdout).strip()}")
                    return
            else:
                for p in existing:
                    if p.is_dir():
                        shutil.rmtree(p)
                    else:
                        p.unlink()
            self._log("Removed. Quitting...")
            GLib.timeout_add(800, lambda: (self.get_application().quit(), False)[1])
        except Exception as e:
            self._log(f"ERROR: {e}")


class VHelperApp(Adw.Application):
    def __init__(self):
        super().__init__(
            application_id="com.vhelper.app",
            flags=Gio.ApplicationFlags.FLAGS_NONE,
        )

    def do_activate(self):
        win = self.get_active_window()
        if not win:
            win = VHelperWindow(self)
        win.present()


def main():
    app = VHelperApp()
    app.run()


if __name__ == "__main__":
    main()
