# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

"""User-initiated local network search for TSUN devices."""

from __future__ import annotations

import asyncio
from collections.abc import Iterable
from ipaddress import IPv4Address


DISCOVERY_CONCURRENCY = 64
DISCOVERY_TIMEOUT = 0.5


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
