#!/usr/bin/env python3
# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Compatibility shim for diagnostic model assignment.

The safe extra-candidate-aware assignment policy now lives in the canonical
``tsun_report_upload`` module.  Keeping these exports avoids breaking older test
helpers or external tooling that imported this module directly.
"""

from __future__ import annotations

from typing import Any

import tsun_report_upload as base

associate_declared_models = base.associate_declared_models


def install(report_upload_module: Any = base) -> None:
    """Compatibility no-op/alias installer for older callers."""
    report_upload_module.associate_declared_models = associate_declared_models
