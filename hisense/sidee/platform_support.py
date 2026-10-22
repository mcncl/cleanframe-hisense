"""Small platform boundary for resources, private state, and LAN discovery."""
from __future__ import annotations

import errno
import ipaddress
import os
from pathlib import Path
import re
import socket
import subprocess
import sys


def resource_root(module_file: str | None = None) -> Path:
    """Return packaged data without relying on the launcher's working folder."""
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent)).resolve()
    parent = Path(module_file or __file__).resolve().parent
    return parent.parent if parent.name == "core" else parent


def _state_override() -> Path | None:
    value = os.environ.get("SIDEE_STATE_DIR", "").strip()
    return Path(value).expanduser().resolve() if value else None


def profile_dir() -> Path:
    """Preserve existing pairings; explicit test state never reads the profile."""
    base = _state_override()
    if base is None:
        home = Path(os.path.expanduser("~"))
        base, legacy = home / ".sidee", home / ".vidaa-tile"
        if not (base / "session.json").is_file() and (legacy / "session.json").is_file():
            base = legacy
    base.mkdir(mode=0o700, parents=True, exist_ok=True)
    return base


def dashboard_state_path(project_root: str | Path) -> Path:
    """Keep writable runtime files outside a frozen macOS application bundle."""
    override = _state_override()
    if override is not None:
        return override / "runtime" / "dashboard.json"
    if sys.platform == "darwin" and getattr(sys, "frozen", False):
        return (Path(os.path.expanduser("~")) / "Library" / "Application Support"
                / "Sidee" / "runtime" / "dashboard.json")
    return Path(project_root) / ".runtime" / "dashboard.json"


def allow_reuse_address() -> bool:
    """Unix can reuse closed listeners; Windows must reserve its own port."""
    return os.name != "nt"


def configure_exclusive_tcp_socket(sock: socket.socket) -> None:
    if os.name == "nt":
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)


def address_in_use(error: OSError) -> bool:
    return (error.errno == errno.EADDRINUSE
            or getattr(error, "winerror", None) in (10013, 10048))


def _broadcast(host: str, mask: str) -> str | None:
    try:
        address = ipaddress.IPv4Address(host)
        network = ipaddress.IPv4Network(f"{address}/{mask}", strict=False)
        if network.is_loopback or network.prefixlen >= 31:
            return None
        return str(network.broadcast_address)
    except ValueError:
        return None


def _interfaces_from_ipconfig(output: str) -> list[tuple[str, str]]:
    """Parse Windows IPv4 + mask pairs in ipconfig output.

    The Windows output is line-oriented: IPv4 appears on a line, then the mask on
    the immediately following line. Keep the parser stateful instead of searching
    for arbitrary IPv4-looking strings on every line, which breaks when multiple
    adapters are present.
    """
    interfaces: set[tuple[str, str]] = set()
    pending_ip = None
    ip_match = re.compile(r"(?<![\d.])(\d{1,3}(?:\.\d{1,3}){3})(?![\d.])")
    for raw in output.splitlines():
        line = raw.strip()
        if not line:
            continue
        lower = line.lower()
        if "ipv4" in lower:
            match = ip_match.search(line)
            pending_ip = match.group(1) if match else None
            continue
        if pending_ip and ("mask" in lower or "subnet" in lower or "netmask" in lower):
            match = ip_match.search(line)
            if match:
                mask = match.group(1)
                target = _broadcast(pending_ip, mask)
                if target:
                    interfaces.add((pending_ip, target))
            pending_ip = None
    return sorted(interfaces)


def broadcasts_from_ipconfig(output: str) -> list[str]:
    return sorted({target for _, target in _interfaces_from_ipconfig(output)})


def _interfaces_from_ifconfig(output: str) -> list[tuple[str, str]]:
    """Parse active macOS broadcast interfaces, including hexadecimal masks."""
    interfaces = set()
    active = False
    pending = set()
    for line in output.splitlines():
        if line and not line[0].isspace():
            if active:
                interfaces.update(pending)
            pending = set()
            flags = re.search(r"<([^>]+)>", line)
            names = set(flags.group(1).split(",")) if flags else set()
            active = {"UP", "BROADCAST"}.issubset(names) and not names.intersection(
                {"LOOPBACK", "POINTOPOINT"})
        elif re.search(r"\bstatus:\s+inactive\b", line):
            active = False
        if not active:
            continue
        match = re.search(r"\binet\s+(\d{1,3}(?:\.\d{1,3}){3})\s+netmask\s+(\S+)", line)
        if not match:
            continue
        try:
            address = ipaddress.IPv4Address(match.group(1))
        except ValueError:
            continue
        if (address.is_unspecified or address.is_multicast or address.is_link_local):
            continue
        mask = match.group(2)
        if mask.lower().startswith("0x"):
            try:
                mask = str(ipaddress.IPv4Address(int(mask, 16)))
            except (ValueError, ipaddress.AddressValueError):
                continue
        target = _broadcast(match.group(1), mask)
        if target:
            pending.add((str(address), target))
    if active:
        interfaces.update(pending)
    return sorted(interfaces)


def broadcasts_from_ifconfig(output: str) -> list[str]:
    return sorted({target for _, target in _interfaces_from_ifconfig(output)})


def local_ipv4_interfaces() -> list[tuple[str, str]]:
    """Inspect native LAN interfaces, returning their IPv4/broadcast pairs."""
    kwargs = dict(capture_output=True, text=True, errors="replace", timeout=3)
    if sys.platform == "darwin":
        command, parser = ["/sbin/ifconfig"], _interfaces_from_ifconfig
    elif os.name == "nt":
        command, parser = ["ipconfig"], _interfaces_from_ipconfig
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
    else:
        return []
    try:
        result = subprocess.run(command, **kwargs)
        return parser(result.stdout) if result.returncode == 0 else []
    except (OSError, subprocess.TimeoutExpired):
        return []


def local_broadcasts() -> list[str]:
    """Use only native interface inspection, with global/multicast fallback."""
    return sorted({target for _, target in local_ipv4_interfaces()})
