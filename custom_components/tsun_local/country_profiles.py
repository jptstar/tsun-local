# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Protocol-aware TSUN country / grid-profile presentation."""

from __future__ import annotations

from typing import Any, Mapping


COUNTRY_PROFILE_SOURCE_KEYS: dict[str, str] = {
    "1511": "country_profile_raw",
    "02b0": "product_compliance_type_raw",
    "1097": "country_profile_raw",
}

# 1511 / TITAN evidence is intentionally conservative. Local MP3000 dumps
# currently confirm code 6 on three independent units and code 8 on two units.
# Cloud-side TSUN/Talent profile evidence also associates 1002/1006/1008 with
# Germany/Poland/France respectively, matching a local +1000 export offset.
COUNTRY_PROFILES_1511: dict[int, str] = {
    2: "Deutschland",
    6: "Polska",
    8: "France",
}

# 02B0 and 1097 expose the established TSUN product-compliance enumeration.
# Country names use a native/endonym form where practical.
COUNTRY_PROFILES_GEN3_GEN4: dict[int, str] = {
    0: "Testing",
    1: "Brasil",
    2: "Deutschland",
    3: "Nederland",
    4: "Éire / Ireland",
    5: "Italia",
    6: "Polska",
    7: "België / Belgique / Belgien",
    8: "France",
    9: "Österreich",
    10: "España",
    11: "VDE 0126",
    12: "Australia",
    13: "ประเทศไทย (MEA)",
    14: "ประเทศไทย (PEA)",
    15: "South Africa",
    16: "United Kingdom",
}

COUNTRY_PROFILES_BY_PROTOCOL: dict[str, Mapping[int, str]] = {
    "1511": COUNTRY_PROFILES_1511,
    "02b0": COUNTRY_PROFILES_GEN3_GEN4,
    "1097": COUNTRY_PROFILES_GEN3_GEN4,
}


def country_profile_raw_value(
    protocol: str, data: Mapping[str, Any]
) -> int | None:
    """Return the raw country/profile code for one runtime protocol."""
    key = COUNTRY_PROFILE_SOURCE_KEYS.get(protocol.lower())
    if key is None:
        return None
    value = data.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return value


def country_profile_name(protocol: str, raw_code: int) -> str | None:
    """Return a protocol-specific native country/profile name."""
    profiles = COUNTRY_PROFILES_BY_PROTOCOL.get(protocol.lower())
    if profiles is None:
        return None
    return profiles.get(raw_code)


def country_profile_state(
    protocol: str, data: Mapping[str, Any]
) -> str | None:
    """Return ``code (native name)`` while preserving unknown raw codes."""
    raw_code = country_profile_raw_value(protocol, data)
    if raw_code is None:
        return None
    name = country_profile_name(protocol, raw_code)
    return f"{raw_code} ({name})" if name is not None else str(raw_code)
