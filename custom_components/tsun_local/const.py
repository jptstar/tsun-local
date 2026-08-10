# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Constants for the TSUN Local integration using protocol 1511."""

from datetime import timedelta

DOMAIN = "tsun_local"
PLATFORMS = ["binary_sensor", "sensor"]

CONF_LOGGER_SN = "logger_sn"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_OFFLINE_SCAN_INTERVAL = "offline_scan_interval"

DEFAULT_SCAN_INTERVAL = 30
MIN_SCAN_INTERVAL = 10
MAX_SCAN_INTERVAL = 300
DEFAULT_OFFLINE_SCAN_INTERVAL = 300
MIN_OFFLINE_SCAN_INTERVAL = 60
MAX_OFFLINE_SCAN_INTERVAL = 3600
DEFAULT_UPDATE_INTERVAL = timedelta(seconds=DEFAULT_SCAN_INTERVAL)

MANUFACTURER = "TSUN"
MODEL = "TITAN"

BLOCKS = (
    (0xA1, 0x01, 0x0BB8, 0x0BD0),
    (0xA3, 0x03, 0x0E10, 0x0E2D),
    (0xA4, 0x04, 0x0ED8, 0x0EF5),
)
