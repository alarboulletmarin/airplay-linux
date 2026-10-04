"""Drive the doubletake mirroring process.

doubletake does the real AirPlay work; this wrapper starts it, reads its
output, prompts for a pairing PIN when needed, and restarts it when the GNOME
capture pipeline drops mid-stream (the `not-negotiated` failure that otherwise
stops mirroring after a while). Restart storms are capped so a genuinely broken
setup surfaces as an error instead of looping forever.

All callbacks are re-emitted on the GTK main thread through GLib.idle_add.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import threading
import time
from collections.abc import Callable

from gi.repository import GLib

STATE_IDLE = "idle"
STATE_CONNECTING = "connecting"
STATE_MIRRORING = "mirroring"
STATE_RECONNECTING = "reconnecting"
STATE_ERROR = "error"

MAX_RESTARTS = 5          # rapid failures tolerated before giving up
RESTART_WINDOW = 30.0     # seconds; a run longer than this resets the counter
RESTART_DELAY_MS = 1200   # pause before a restart


def find_doubletake() -> str | None:
    """Locate the doubletake engine.

    Prefers the copy bundled with AirPlay Mirror, so the app carries its own
    engine and does not depend on a separately installed doubletake. Falls back
    to PATH for development checkouts. Override with AIRPLAY_MIRROR_DOUBLETAKE.
    """
    override = os.environ.get("AIRPLAY_MIRROR_DOUBLETAKE")
    if override and os.path.exists(override):
        return override
    for candidate in _bundled_candidates():
        if os.path.exists(candidate):
            return candidate
    return shutil.which("doubletake") or _local_bin_fallback()


def _bundled_candidates() -> list[str]:
    here = os.path.dirname(os.path.abspath(__file__))
    return [
        "/usr/lib/airplay-mirror/doubletake",
        os.path.expanduser("~/.local/lib/airplay-mirror/doubletake"),
        os.path.join(here, "vendor", "doubletake"),
    ]


def _local_bin_fallback() -> str | None:
    candidate = os.path.expanduser("~/.local/bin/doubletake")
    return candidate if os.path.exists(candidate) else None


class MirrorSession:
    def __init__(
        self,
        binary: str,
        on_state: Callable[[str, str], None],
        on_pin_request: Callable[[], None],
    ) -> None:
        self._binary = binary
        self._on_state = on_state
        self._on_pin_request = on_pin_request
        self._process: subprocess.Popen[bytes] | None = None
        self._command: list[str] = []
        self._running = False
        self._restarts: list[float] = []
        self._pin_requested = False

    @property
    def active(self) -> bool:
        return self._running

    def start(self, address: str, encoder: str, audio: bool, pair: bool) -> None:
        command = [self._binary, "-target", address, "-hwaccel", encoder]
        if not audio:
            command.append("-no-audio")
        if pair:
            command.append("-pair")
        self._command = command
        self._running = True
        self._restarts = []
        self._spawn()

    def stop(self) -> None:
        self._running = False
        self._terminate()
        self._on_state(STATE_IDLE, "")

    def send_pin(self, pin: str) -> None:
        process = self._process
        if process is None or process.stdin is None:
            return
        try:
            process.stdin.write((pin + "\n").encode())
            process.stdin.flush()
        except (BrokenPipeError, ValueError):
            pass

    def _terminate(self) -> None:
        process, self._process = self._process, None
        if process is None or process.poll() is not None:
            return
        process.terminate()
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            process.kill()

    def _spawn(self) -> None:
        self._pin_requested = False
        started_at = time.monotonic()
        self._restarts.append(started_at)
        self._on_state(STATE_CONNECTING, "")
        try:
            self._process = subprocess.Popen(
                self._command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=0,
            )
        except OSError as error:
            self._running = False
            self._on_state(STATE_ERROR, str(error))
            return
        thread = threading.Thread(
            target=self._read_output, args=(self._process, started_at), daemon=True
        )
        thread.start()

    def _read_output(self, process: subprocess.Popen[bytes], started_at: float) -> None:
        """Read raw output; the PIN prompt has no trailing newline."""
        buffer = b""
        fd = process.stdout.fileno()  # type: ignore[union-attr]
        while True:
            try:
                chunk = os.read(fd, 4096)
            except OSError:
                chunk = b""
            if not chunk:
                break
            buffer += chunk
            while b"\n" in buffer:
                line, buffer = buffer.split(b"\n", 1)
                self._handle_line(line.decode("utf-8", "replace").rstrip())
            if not self._pin_requested and b"PIN" in buffer:
                self._pin_requested = True
                GLib.idle_add(self._on_pin_request)
        process.wait()
        GLib.idle_add(self._on_process_ended, started_at)

    def _handle_line(self, line: str) -> None:
        if "mirror session ready" in line:
            GLib.idle_add(self._on_state, STATE_MIRRORING, "")

    def _on_process_ended(self, started_at: float) -> bool:
        if not self._running:
            return False
        if time.monotonic() - started_at > RESTART_WINDOW:
            self._restarts = []
        recent = [t for t in self._restarts if time.monotonic() - t < RESTART_WINDOW]
        if len(recent) >= MAX_RESTARTS:
            self._running = False
            self._on_state(STATE_ERROR, "too_many")
            return False
        self._on_state(STATE_RECONNECTING, "")
        GLib.timeout_add(RESTART_DELAY_MS, self._restart)
        return False

    def _restart(self) -> bool:
        if self._running:
            self._spawn()
        return False
