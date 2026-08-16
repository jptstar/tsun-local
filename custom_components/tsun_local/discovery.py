# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

"""User-initiated local network search for TSUN devices."""

from __future__ import annotations

import asyncio
import base64
from collections.abc import Iterable
from ipaddress import IPv4Address, IPv4Network, ip_network
import re


DISCOVERY_CONCURRENCY = 128
DISCOVERY_TIMEOUT = 1.0
UDP_DISCOVERY_PORT = 48899
UDP_DISCOVERY_TIMEOUT = 1.5
UDP_DISCOVERY_MESSAGES = (
    b"WIFIKIT-214028-READ",
    b"HF-A11ASSISTHREAD",
    b"devicelinkfind",
)
MIN_DISCOVERY_PREFIX = 24
FIRMWARE_HTTP_TIMEOUT = 1.5
FIRMWARE_PAGE_LIMIT = 256 * 1024
FIRMWARE_STATUS_PATHS = ("/status.html", "/index_cn.html", "/index.html", "/")
_FIRMWARE_VALUE_PATTERNS = (
    re.compile(
        r"\b(?:webdata|cover)[_-]ver\s*[:=]\s*[\"']"
        r"([A-Za-z0-9][A-Za-z0-9._-]{1,79})",
        re.IGNORECASE,
    ),
    re.compile(
        r"firmware\s*version[^A-Za-z0-9]+"
        r"([A-Za-z0-9][A-Za-z0-9._-]{1,79})",
        re.IGNORECASE,
    ),
)
_FIRMWARE_PROTOCOL_TOKEN = re.compile(
    r"(?:^|[_-])(1511|1097|02b0)(?=[_-]|$)",
    re.IGNORECASE,
)


def protocol_from_firmware(firmware_version: str | None) -> str | None:
    """Return a supported TSUN protocol token from a firmware version."""
    if not firmware_version:
        return None
    match = _FIRMWARE_PROTOCOL_TOKEN.search(firmware_version)
    if match is None:
        return None
    return match.group(1).lower()


def _firmware_version_from_document(document: str) -> str | None:
    """Extract the firmware version from a logger status document."""
    for pattern in _FIRMWARE_VALUE_PATTERNS:
        if match := pattern.search(document):
            return match.group(1)
    return None


async def _async_read_status_document(
    host: str, path: str, *, authenticated: bool
) -> str | None:
    """Read a local logger page using GET only."""
    writer: asyncio.StreamWriter | None = None
    try:
        async with asyncio.timeout(FIRMWARE_HTTP_TIMEOUT):
            reader, writer = await asyncio.open_connection(host, 80)
            headers = [
                f"GET {path} HTTP/1.1",
                f"Host: {host}",
                "Connection: close",
                "User-Agent: TSUN-Local-Discovery",
            ]
            if authenticated:
                token = base64.b64encode(b"admin:admin").decode("ascii")
                headers.append(f"Authorization: Basic {token}")
            writer.write(
                ("\r\n".join(headers) + "\r\n\r\n").encode("ascii")
            )
            await writer.drain()
            response = await reader.read(FIRMWARE_PAGE_LIMIT + 1)
    except (OSError, TimeoutError, asyncio.IncompleteReadError):
        return None
    finally:
        if writer is not None:
            writer.close()
            try:
                await writer.wait_closed()
            except OSError:
                pass

    if len(response) > FIRMWARE_PAGE_LIMIT:
        return None
    header, separator, body = response.partition(b"\r\n\r\n")
    if not separator:
        return None
    if b" 200 " not in header.split(b"\r\n", 1)[0]:
        return None
    return body.decode("utf-8", errors="replace")


async def async_identify_tsun_firmware(host: str) -> str | None:
    """Return the firmware-selected protocol for a recognized TSUN candidate."""
    for path in FIRMWARE_STATUS_PATHS:
        for authenticated in (False, True):
            document = await _async_read_status_document(
                host, path, authenticated=authenticated
            )
            if document is None:
                continue
            firmware_version = _firmware_version_from_document(document)
            if protocol_name := protocol_from_firmware(firmware_version):
                return protocol_name
    return None


def bounded_ipv4_network(
    address: str, network_prefix: int
) -> IPv4Network | None:
    """Return a safe scan network containing at most 254 hosts."""
    ip_address = IPv4Address(address)
    if (
        ip_address.is_loopback
        or ip_address.is_link_local
        or ip_address.is_multicast
        or ip_address.is_unspecified
    ):
        return None
    network = ip_network(
        f"{ip_address}/{max(network_prefix, MIN_DISCOVERY_PREFIX)}",
        strict=False,
    )
    if not isinstance(network, IPv4Network):
        return None
    return network


def parse_discovery_network(value: str) -> IPv4Network:
    """Parse a user-provided IPv4 network limited to a /24 or smaller scan."""
    network = ip_network(value.strip(), strict=False)
    if not isinstance(network, IPv4Network):
        raise ValueError("An IPv4 network is required")
    if network.prefixlen < MIN_DISCOVERY_PREFIX:
        raise ValueError("The discovery network must be /24 or smaller")
    return network


async def _async_port_is_open(
    host: IPv4Address, port: int, semaphore: asyncio.Semaphore
) -> str | None:
    """Return the host when its local TCP port accepts a connection."""
    writer: asyncio.StreamWriter | None = None
    try:
        async with semaphore, asyncio.timeout(DISCOVERY_TIMEOUT):
            _, writer = await asyncio.open_connection(str(host), port)
        return str(host)
    except (OSError, TimeoutError):
        return None
    finally:
        if writer is not None:
            writer.close()
            try:
                await writer.wait_closed()
            except OSError:
                pass


async def async_scan_hosts(hosts: Iterable[IPv4Address], port: int) -> list[str]:
    """Find hosts accepting the TSUN local TCP port without sending data."""
    semaphore = asyncio.Semaphore(DISCOVERY_CONCURRENCY)
    results = await asyncio.gather(
        *(_async_port_is_open(host, port, semaphore) for host in hosts)
    )
    return sorted(
        (host for host in results if host is not None), key=IPv4Address
    )


async def async_scan_networks(
    networks: Iterable[IPv4Network], port: int
) -> list[str]:
    """Find hosts on all selected networks without scanning an address twice."""
    hosts = {
        host
        for discovered_network in networks
        for host in discovered_network.hosts()
    }
    return await async_scan_hosts(hosts, port)


def parse_udp_discovery_reply(
    payload: bytes, source: str
) -> str | None:
    """Return a candidate IPv4 address from a known logger UDP reply."""
    message = payload.decode("utf-8", errors="ignore").strip("\x00\r\n ")
    if not message or payload in UDP_DISCOVERY_MESSAGES:
        return None

    candidate = ""
    if message.startswith("{"):
        # Some logger variants answer devicelinkfind with a small JSON object.
        import json

        try:
            candidate = str(json.loads(message).get("ip", ""))
        except (TypeError, ValueError):
            return None
    elif "," in message:
        # LPB replies use IP, MAC, identifier. Only the IP is needed here.
        candidate = message.split(",", 1)[0].strip()
    elif message.startswith("HF-"):
        # A11 replies identify themselves in the payload; their source is the
        # candidate address.
        candidate = source
    else:
        return None

    try:
        address = IPv4Address(candidate)
    except ValueError:
        return None
    if (
        address.is_loopback
        or address.is_link_local
        or address.is_multicast
        or address.is_unspecified
    ):
        return None
    return str(address)


class _UdpDiscoveryProtocol(asyncio.DatagramProtocol):
    """Collect candidate hosts from read-only UDP discovery replies."""

    def __init__(self) -> None:
        self.hosts: set[str] = set()

    def datagram_received(
        self, data: bytes, addr: tuple[str, int]
    ) -> None:
        if host := parse_udp_discovery_reply(data, addr[0]):
            self.hosts.add(host)


async def async_discover_udp(targets: Iterable[str]) -> list[str]:
    """Discover candidate loggers through their read-only UDP service."""
    loop = asyncio.get_running_loop()
    protocol = _UdpDiscoveryProtocol()
    try:
        transport, _ = await loop.create_datagram_endpoint(
            lambda: protocol,
            local_addr=("0.0.0.0", UDP_DISCOVERY_PORT),
            allow_broadcast=True,
        )
    except OSError:
        return []

    try:
        for target in set(targets):
            for message in UDP_DISCOVERY_MESSAGES:
                transport.sendto(message, (target, UDP_DISCOVERY_PORT))
        await asyncio.sleep(UDP_DISCOVERY_TIMEOUT)
    finally:
        transport.close()
    return sorted(protocol.hosts, key=IPv4Address)


async def async_discover_devices(
    networks: Iterable[IPv4Network], port: int
) -> list[str]:
    """Combine UDP discovery with bounded TCP scanning and validation."""
    discovery_networks = tuple(networks)
    udp_targets = {
        "255.255.255.255",
        *(str(network.broadcast_address) for network in discovery_networks),
    }
    tcp_task = asyncio.create_task(
        async_scan_networks(discovery_networks, port)
    )
    udp_hosts = await async_discover_udp(udp_targets)
    tcp_hosts = set(await tcp_task)

    # Never trust an announcement alone: require the configured local TCP port
    # to accept a connection before Home Assistant proposes the candidate.
    unvalidated = [
        IPv4Address(host) for host in udp_hosts if host not in tcp_hosts
    ]
    if unvalidated:
        tcp_hosts.update(await async_scan_hosts(unvalidated, port))

    # Other Solarman-based equipment can expose the same TCP port. Automatic
    # discovery proposes only candidates with a supported protocol token in
    # the local logger firmware. Unknown devices remain available to manual
    # setup, where the user can explicitly force protocol probing.
    candidates = sorted(tcp_hosts, key=IPv4Address)
    identified_protocols = await asyncio.gather(
        *(async_identify_tsun_firmware(host) for host in candidates)
    )
    return [
        host
        for host, protocol_name in zip(candidates, identified_protocols)
        if protocol_name is not None
    ]
