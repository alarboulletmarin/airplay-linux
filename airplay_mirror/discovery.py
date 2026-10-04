"""AirPlay receiver discovery over mDNS.

Uses the `zeroconf` library directly rather than the avahi daemon, so discovery
works even when avahi-daemon is disabled (the default on some GNOME setups).
"""

from __future__ import annotations

import time
from dataclasses import dataclass

from zeroconf import ServiceBrowser, ServiceListener, Zeroconf

SERVICE_TYPE = "_airplay._tcp.local."


@dataclass(frozen=True)
class Device:
    name: str
    address: str


class _Collector(ServiceListener):
    def __init__(self) -> None:
        self.devices: dict[str, Device] = {}

    def add_service(self, zeroconf: Zeroconf, service_type: str, name: str) -> None:
        info = zeroconf.get_service_info(service_type, name, timeout=2000)
        if info is None:
            return
        ipv4 = next((addr for addr in info.parsed_addresses() if ":" not in addr), None)
        if ipv4 is None:
            return
        suffix = "." + service_type
        label = name[: -len(suffix)] if name.endswith(suffix) else name
        self.devices[name] = Device(label, ipv4)

    def update_service(self, zeroconf: Zeroconf, service_type: str, name: str) -> None:
        self.add_service(zeroconf, service_type, name)

    def remove_service(self, zeroconf: Zeroconf, service_type: str, name: str) -> None:
        self.devices.pop(name, None)


def discover(timeout: float = 4.0) -> list[Device]:
    """Browse the local network for AirPlay receivers.

    Blocks for `timeout` seconds, so call it from a worker thread.
    """
    zeroconf = Zeroconf()
    collector = _Collector()
    ServiceBrowser(zeroconf, SERVICE_TYPE, collector)
    try:
        time.sleep(timeout)
    finally:
        zeroconf.close()
    return sorted(collector.devices.values(), key=lambda device: device.name.lower())
