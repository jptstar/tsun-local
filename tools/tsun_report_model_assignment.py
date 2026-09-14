#!/usr/bin/env python3
# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Safer per-report model assignment when discovery finds extra LAN devices."""

from __future__ import annotations

from typing import Any, Iterable

import tsun_report_upload as base


def associate_declared_models(
    diagnostics: list[dict[str, Any]],
    declared_devices: Iterable[dict[str, Any]],
) -> dict[int, str]:
    """Assign inventory to dumps only when evidence remains unambiguous.

    Extra discovered diagnostics are allowed. This matters on LANs that contain
    unrelated Tuya devices: TSUN dumps can still be linked by rated power while
    unrelated candidates remain unassigned. If fewer diagnostics than declared
    inverter units are present, assignment stays disabled because evidence is
    incomplete.
    """
    remaining = base._expanded_declared_models(declared_devices)
    if not diagnostics or not remaining or len(remaining) > len(diagnostics):
        return {}

    unresolved: set[int] = set(range(len(diagnostics)))
    assignments: dict[int, str] = {}

    for index, diagnostic in enumerate(diagnostics):
        metadata = diagnostic.get("metadata")
        existing = (
            metadata.get("model_supplied_by_user")
            if isinstance(metadata, dict)
            else None
        )
        if isinstance(existing, str) and existing.strip():
            model = existing.strip()
            if not base._pop_model(remaining, model):
                return {}
            unresolved.discard(index)
            assignments[index] = model

    progress = True
    while progress and remaining:
        progress = False
        for index in sorted(tuple(unresolved)):
            rated = base._diagnostic_rated_power(diagnostics[index])
            if rated is None:
                continue
            candidates: dict[str, str] = {}
            for model in remaining:
                if base._model_nominal_power(model) == rated:
                    candidates.setdefault(model.casefold(), model)
            if len(candidates) != 1:
                continue
            model = next(iter(candidates.values()))
            base._annotate_model(diagnostics[index], model, "rated_power_match")
            base._pop_model(remaining, model)
            unresolved.remove(index)
            assignments[index] = model
            progress = True

    # Retain the historical fallback only when every unresolved diagnostic is
    # needed to consume every remaining declared unit. With extra LAN candidates
    # this condition is false, preventing accidental Tuya -> inverter assignment.
    if unresolved and remaining and len(remaining) == len(unresolved):
        distinct = {model.casefold(): model for model in remaining}
        if len(distinct) == 1:
            model = next(iter(distinct.values()))
            for index in sorted(unresolved):
                base._annotate_model(
                    diagnostics[index], model, "remaining_declared_inventory"
                )
                assignments[index] = model
            remaining.clear()
            unresolved.clear()

    return assignments


def install(report_upload_module: Any = base) -> None:
    """Replace only the association policy; upload/privacy code stays unchanged."""
    report_upload_module.associate_declared_models = associate_declared_models
