"""GTK4/Adwaita interface for AirPlay Mirror."""

from __future__ import annotations

import threading

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, GLib, Gtk  # noqa: E402

from .discovery import Device, discover  # noqa: E402
from .i18n import Translator  # noqa: E402
from .session import (  # noqa: E402
    STATE_CONNECTING,
    STATE_ERROR,
    STATE_IDLE,
    STATE_MIRRORING,
    STATE_RECONNECTING,
    MirrorSession,
    find_doubletake,
)

APP_ID = "org.airplaymirror.AirPlayMirror"
STATE_SCANNING = "scanning"

# (translation key, doubletake -hwaccel value)
ENCODERS = [
    ("enc_openh264", "openh264"),
    ("enc_vaapi", "vaapi"),
    ("enc_auto", "auto"),
]


class Window(Adw.ApplicationWindow):
    def __init__(self, app: Adw.Application, binary: str | None) -> None:
        super().__init__(application=app, title="AirPlay Mirror")
        self.set_default_size(420, 640)
        self.tr = Translator()
        self.binary = binary
        self.selected_address: str | None = None
        self.state = STATE_IDLE
        self.detail = ""
        self._timer_id = 0
        self._elapsed = 0
        self.session = (
            MirrorSession(binary, self.set_state, self.request_pin) if binary else None
        )

        self._build_ui()
        self.retranslate()
        if binary is None:
            self.set_state(STATE_ERROR, "no_doubletake")
        else:
            self.scan()

    # -- construction -------------------------------------------------------

    def _build_ui(self) -> None:
        header = Adw.HeaderBar()
        self.refresh_button = Gtk.Button(icon_name="view-refresh-symbolic")
        self.refresh_button.connect("clicked", lambda _button: self.scan())
        header.pack_start(self.refresh_button)
        header.pack_end(self._build_language_button())

        content = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=16,
            margin_top=16,
            margin_bottom=16,
            margin_start=16,
            margin_end=16,
        )

        status = Gtk.Box(spacing=10, halign=Gtk.Align.CENTER)
        self.spinner = Gtk.Spinner()
        self.status_label = Gtk.Label(css_classes=["title-4"])
        status.append(self.spinner)
        status.append(self.status_label)
        content.append(status)

        self.devices_label = Gtk.Label(xalign=0, css_classes=["heading"])
        content.append(self.devices_label)
        self.device_list = Gtk.ListBox(selection_mode=Gtk.SelectionMode.SINGLE)
        self.device_list.add_css_class("boxed-list")
        self.device_list.connect("row-selected", self._on_device_selected)
        content.append(self.device_list)

        options = Gtk.ListBox(selection_mode=Gtk.SelectionMode.NONE)
        options.add_css_class("boxed-list")
        self.encoder_row = Adw.ComboRow()
        options.append(self.encoder_row)
        self.audio_switch = Gtk.Switch(valign=Gtk.Align.CENTER)
        self.audio_row = Adw.ActionRow()
        self.audio_row.add_suffix(self.audio_switch)
        self.audio_row.set_activatable_widget(self.audio_switch)
        options.append(self.audio_row)
        self.pair_switch = Gtk.Switch(valign=Gtk.Align.CENTER)
        self.pair_row = Adw.ActionRow()
        self.pair_row.add_suffix(self.pair_switch)
        self.pair_row.set_activatable_widget(self.pair_switch)
        options.append(self.pair_row)
        content.append(options)

        content.append(Gtk.Box(vexpand=True))
        self.action_button = Gtk.Button(sensitive=False)
        self.action_button.add_css_class("pill")
        self.action_button.connect("clicked", self._on_action_clicked)
        content.append(self.action_button)

        view = Adw.ToolbarView()
        view.add_top_bar(header)
        view.set_content(content)
        self.set_content(view)

    def _build_language_button(self) -> Gtk.MenuButton:
        button = Gtk.MenuButton(icon_name="preferences-desktop-locale-symbolic")
        box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=4,
            margin_top=8,
            margin_bottom=8,
            margin_start=8,
            margin_end=8,
        )
        group: Gtk.CheckButton | None = None
        for code, label in (("en", "English"), ("fr", "Français")):
            radio = Gtk.CheckButton(label=label, active=code == self.tr.language)
            if group is None:
                group = radio
            else:
                radio.set_group(group)
            radio.connect("toggled", self._on_language_toggled, code)
            box.append(radio)
        popover = Gtk.Popover()
        popover.set_child(box)
        button.set_popover(popover)
        return button

    # -- translation --------------------------------------------------------

    def _on_language_toggled(self, radio: Gtk.CheckButton, code: str) -> None:
        if radio.get_active():
            self.tr.set_language(code)
            self.retranslate()

    def retranslate(self) -> None:
        self.refresh_button.set_tooltip_text(self.tr("search"))
        self.devices_label.set_label(self.tr("devices_group"))
        self.encoder_row.set_title(self.tr("encoder"))
        selected = max(self.encoder_row.get_selected(), 0)
        self.encoder_row.set_model(
            Gtk.StringList.new([self.tr(key) for key, _ in ENCODERS])
        )
        self.encoder_row.set_selected(selected)
        self.audio_row.set_title(self.tr("audio"))
        self.audio_row.set_subtitle(self.tr("audio_sub"))
        self.pair_row.set_title(self.tr("pair"))
        self.pair_row.set_subtitle(self.tr("pair_sub"))
        self._apply_state()

    # -- discovery ----------------------------------------------------------

    def scan(self) -> None:
        self.refresh_button.set_sensitive(False)
        self.set_state(STATE_SCANNING, "")
        threading.Thread(target=self._scan_worker, daemon=True).start()

    def _scan_worker(self) -> None:
        try:
            result: list[Device] | Exception = discover()
        except Exception as error:  # noqa: BLE001 - reported to the user
            result = error
        GLib.idle_add(self._scan_finished, result)

    def _scan_finished(self, result: list[Device] | Exception) -> bool:
        self.refresh_button.set_sensitive(True)
        self._clear_device_list()
        if isinstance(result, Exception):
            self.set_state(STATE_ERROR, f"search:{result}")
            return False
        for device in result:
            row = Adw.ActionRow(title=device.name, subtitle=device.address)
            row.address = device.address  # type: ignore[attr-defined]
            self.device_list.append(row)
        self.set_state(STATE_IDLE, "" if result else "no_devices")
        return False

    def _clear_device_list(self) -> None:
        child = self.device_list.get_first_child()
        while child is not None:
            self.device_list.remove(child)
            child = self.device_list.get_first_child()
        self.selected_address = None

    def _on_device_selected(self, _list: Gtk.ListBox, row: Gtk.ListBoxRow | None) -> None:
        self.selected_address = row.address if row else None  # type: ignore[attr-defined]
        self._apply_state()

    # -- mirroring ----------------------------------------------------------

    def _on_action_clicked(self, _button: Gtk.Button) -> None:
        if self.session is None:
            return
        if self.session.active:
            self.session.stop()
        elif self.selected_address:
            encoder = ENCODERS[self.encoder_row.get_selected()][1]
            self.session.start(
                self.selected_address,
                encoder,
                self.audio_switch.get_active(),
                self.pair_switch.get_active(),
            )

    def request_pin(self) -> bool:
        dialog = Adw.MessageDialog(
            transient_for=self,
            modal=True,
            heading=self.tr("pin_heading"),
            body=self.tr("pin_body"),
        )
        entry = Gtk.Entry(input_purpose=Gtk.InputPurpose.DIGITS, activates_default=True)
        dialog.set_extra_child(entry)
        dialog.add_response("cancel", self.tr("cancel"))
        dialog.add_response("confirm", self.tr("confirm"))
        dialog.set_default_response("confirm")
        dialog.set_response_appearance("confirm", Adw.ResponseAppearance.SUGGESTED)
        dialog.connect("response", self._on_pin_response, entry)
        dialog.present()
        return False

    def _on_pin_response(
        self, _dialog: Adw.MessageDialog, response: str, entry: Gtk.Entry
    ) -> None:
        pin = entry.get_text().strip()
        if response == "confirm" and pin and self.session is not None:
            self.session.send_pin(pin)
        elif self.session is not None:
            self.session.stop()

    # -- state and status ---------------------------------------------------

    def set_state(self, state: str, detail: str = "") -> bool:
        self.state = state
        self.detail = detail
        self._apply_state()
        return False

    def _apply_state(self) -> None:
        running = self.state in (STATE_CONNECTING, STATE_MIRRORING, STATE_RECONNECTING)
        busy = self.state in (STATE_SCANNING, STATE_CONNECTING, STATE_RECONNECTING)
        mirroring = self.state == STATE_MIRRORING
        can_start = self.binary is not None and self.selected_address is not None

        self.spinner.set_spinning(busy or mirroring)
        self.action_button.set_label(self.tr("stop") if running else self.tr("start"))
        self.action_button.set_sensitive(running or can_start)
        self.action_button.remove_css_class("suggested-action")
        self.action_button.remove_css_class("destructive-action")
        self.action_button.add_css_class(
            "destructive-action" if running else "suggested-action"
        )
        self.device_list.set_sensitive(not running)
        self.encoder_row.set_sensitive(not running)

        self._update_timer(mirroring)
        self.status_label.remove_css_class("error")
        if self.state == STATE_ERROR:
            self.status_label.add_css_class("error")
        if not mirroring:
            self.status_label.set_label(self._status_text())

    def _status_text(self) -> str:
        if self.state == STATE_SCANNING:
            return self.tr("st_searching")
        if self.state == STATE_CONNECTING:
            return self.tr("st_connecting")
        if self.state == STATE_RECONNECTING:
            return self.tr("st_reconnecting")
        if self.state == STATE_ERROR:
            return self._error_text()
        if self.detail == "no_devices":
            return self.tr("no_devices")
        return self.tr("st_ready")

    def _error_text(self) -> str:
        if self.detail == "too_many":
            return self.tr("err_too_many")
        if self.detail == "no_doubletake":
            return self.tr("err_no_doubletake")
        if self.detail.startswith("search:"):
            return self.tr("err_search", error=self.detail[len("search:"):])
        if self.detail:
            return self.tr("err_launch", error=self.detail)
        return self.tr("st_error")

    def _update_timer(self, mirroring: bool) -> None:
        if mirroring and self._timer_id == 0:
            self._elapsed = 0
            self.status_label.set_label(self.tr("st_mirroring"))
            self._timer_id = GLib.timeout_add_seconds(1, self._on_timer_tick)
        elif not mirroring and self._timer_id != 0:
            GLib.source_remove(self._timer_id)
            self._timer_id = 0

    def _on_timer_tick(self) -> bool:
        self._elapsed += 1
        minutes, seconds = divmod(self._elapsed, 60)
        self.status_label.set_label(
            self.tr("st_mirroring_time", time=f"{minutes:02d}:{seconds:02d}")
        )
        return True


class Application(Adw.Application):
    def __init__(self, binary: str | None) -> None:
        super().__init__(application_id=APP_ID)
        self._binary = binary

    def do_activate(self) -> None:
        window = self.props.active_window or Window(self, self._binary)
        window.present()


def main() -> int:
    return Application(find_doubletake()).run(None)
