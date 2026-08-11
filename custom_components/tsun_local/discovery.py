# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

"""User-initiated local network search for TSUN devices."""

from __future__ import annotations

import asyncio
from collections.abc import Iterable
from ipaddress import IPv4Address, IPv4Network, ip_network


DISCOVERY_CONCURRENCY = 128
DISCOVERY_TIMEOUT = 1.0
MIN_DISCOVERY_PREFIX = 24


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
