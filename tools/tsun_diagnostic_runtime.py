#!/usr/bin/env python3
# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Explicit runtime composition for the TSUN Local desktop diagnostic.

The standalone ``tsun_dump.py`` remains dependency-free and unchanged.  Desktop-
only research extensions are composed here in one deterministic order instead of
being installed from several unrelated places in the GUI entry point.

All registered stages are read-only.  This module only wires existing diagnostic
capabilities together; it does not add protocol writes or alter register ranges.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

import tsun_1097_research_probe
import tsun_1097_transport_extension
import tsun_tuya_probe


ValuePrompt = Callable[[str], str]
SecretPrompt = Callable[[str], str]


@dataclass(frozen=True, slots=True)
class RuntimeStage:
    """One ordered desktop-only diagnostic extension stage."""

    name: str
    phase: str
    order: int
    conditional: bool = True
    read_only: bool = True


RUNTIME_STAGES: tuple[RuntimeStage, ...] = (
    RuntimeStage(
        name="1097-research-fallback",
        phase="protocol-failure",
        order=10,
    ),
    RuntimeStage(
        name="1097-transport-enrichment",
        phase="post-fallback-enrichment",
        order=20,
    ),
    RuntimeStage(
        name="tuya-authenticated-status",
        phase="tuya-capture-enrichment",
        order=30,
    ),
)

SECRET_PROMPT_PREFIX = tsun_tuya_probe.SECRET_PROMPT_PREFIX
_RUNTIME_MARKER = "_tsun_diagnostic_runtime_signature"


def validate_runtime_stages(
    stages: tuple[RuntimeStage, ...] = RUNTIME_STAGES,
) -> None:
    """Fail fast if the declared runtime pipeline becomes ambiguous or unsafe."""
    if not stages:
        raise RuntimeError("diagnostic runtime must declare at least one stage")
    names = [stage.name for stage in stages]
    orders = [stage.order for stage in stages]
    if len(names) != len(set(names)):
        raise RuntimeError("diagnostic runtime stage names must be unique")
    if len(orders) != len(set(orders)):
        raise RuntimeError("diagnostic runtime stage order values must be unique")
    if orders != sorted(orders):
        raise RuntimeError("diagnostic runtime stages must be declared in execution order")
    if any(not stage.read_only for stage in stages):
        raise RuntimeError("desktop diagnostic runtime stages must remain read-only")


def pipeline_stage_names() -> tuple[str, ...]:
    """Return the stable ordered stage signature used by tests and diagnostics."""
    return tuple(stage.name for stage in RUNTIME_STAGES)


def pipeline_description() -> tuple[dict[str, object], ...]:
    """Return a serializable description of the desktop extension pipeline."""
    return tuple(
        {
            "name": stage.name,
            "phase": stage.phase,
            "order": stage.order,
            "conditional": stage.conditional,
            "read_only": stage.read_only,
        }
        for stage in RUNTIME_STAGES
    )


def configure_dump_extensions(
    tsun_dump_module: Any,
    *,
    value_prompt: ValuePrompt | None = None,
    secret_prompt: SecretPrompt | None = None,
) -> tuple[str, ...]:
    """Install desktop-only extensions once, in one tested deterministic order.

    The existing extension modules remain responsible for their narrow trigger
    conditions.  Centralising composition here makes precedence explicit:

    1. the 1097 fallback gets first chance after the normal capture fails;
    2. the transport extension can enrich that fallback document;
    3. the independent Tuya authenticated enrichment is then attached.

    Repeated calls are intentionally idempotent so GUI startup/tests cannot wrap
    capture functions multiple times.
    """
    validate_runtime_stages()
    signature = pipeline_stage_names()
    installed = tuple(getattr(tsun_dump_module, _RUNTIME_MARKER, ()) or ())
    if installed:
        if installed != signature:
            raise RuntimeError(
                "diagnostic runtime is already configured with a different stage order"
            )
        return signature

    tsun_1097_research_probe.install(tsun_dump_module)
    tsun_1097_transport_extension.install(tsun_dump_module)
    tsun_tuya_probe.install(
        tsun_dump_module,
        value_prompt=value_prompt,
        secret_prompt=secret_prompt,
    )
    setattr(tsun_dump_module, _RUNTIME_MARKER, signature)
    return signature


validate_runtime_stages()
