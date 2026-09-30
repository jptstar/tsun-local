# TSUN Local Diagnostic architecture

The diagnostic is designed around one rule: **collect useful evidence without changing inverter or logger configuration**.

This document defines the execution structure so new diagnostic capabilities can be added without turning the desktop tool into an implicit chain of wrappers.

## Normal execution pipeline

The normal hardware dump engine remains `tools/tsun_dump.py`. It is standalone, standard-library-only and independently downloadable.

Its stable high-level flow is:

1. **Discovery** — bounded UDP/TCP/HTTP/Tuya discovery identifies LAN candidates.
2. **Identity** — resolve logger identity, Monitor SN and firmware/protocol hints when available.
3. **Classification** — route a candidate to normal TSUN protocol capture or the Tuya LAN candidate path.
4. **Protocol detection** — try the hinted protocol first when reliable evidence exists, otherwise bounded supported-protocol probes.
5. **Standard capture** — collect the existing protocol-specific read-only register evidence.
6. **Conditional desktop research** — only the narrowly matching research/enrichment stages run.
7. **Report/privacy validation** — create an anonymized JSON and reject forbidden privacy fields before upload.
8. **Local save** — the diagnostic JSON exists locally before any optional network submission.
9. **Delivery** — explicit-consent HTTPS upload with bounded transient retries, or the manual/local fallback.

The refactor does **not** change protocol register ranges, Modbus functions, logger write policy, capture timeouts or output schema.

## Desktop runtime extensions

`tools/tsun_diagnostic_runtime.py` is the single composition point for desktop-only extensions. The order is declared and tested:

| Order | Stage | Trigger / role |
|---:|---|---|
| 10 | `1097-research-fallback` | Runs only after the narrow known 1097 transport-change failure condition. |
| 20 | `1097-transport-enrichment` | Enriches only a 1097 research fallback document. |
| 30 | `tuya-authenticated-status` | Enriches only a confirmed Tuya candidate when the user elects to supply in-memory credentials. |

The runtime is idempotent. Re-running configuration cannot wrap capture functions twice, and a conflicting pre-existing stage order is rejected.

Every declared stage must remain `read_only=True`.

## Upload policy

`tools/tsun_report_upload.py` is the canonical upload policy. It owns:

- local JSON/privacy validation;
- additional protection against accidental Tuya credential fields;
- safe model association when unrelated LAN candidates are also discovered;
- HTTPS request construction;
- bounded transient retries and `Retry-After` handling;
- preservation of the local report when transmission fails.

`tsun_report_upload_retry.py` and `tsun_report_model_assignment.py` remain compatibility shims for older imports. They delegate to the canonical implementation and contain no independent policy.

## Long-running observation

`tools/tsun_observe_02b0.py` intentionally remains separate from the normal diagnostic pipeline.

A long observation changes the sampling pattern and can run for hours, so automatically adding it to every hardware dump would be inefficient and could change the behavior being investigated. It reuses diagnostic primitives while keeping its own bounded polling/deep-capture policy.

## Invariants for future diagnostics

New capabilities should follow these rules:

- prefer a conditional stage over another wrapper installed from an unrelated module;
- declare execution order and trigger conditions explicitly;
- stay read-only unless a completely separate, explicitly reviewed tool is created;
- do not persist IP addresses, Monitor SNs, credentials or full serial numbers in shareable reports;
- collect essential evidence before expensive research when behavior changes are intentionally introduced in a dedicated PR;
- keep long-running or intrusive-by-duration investigations separate from the normal one-shot dump;
- preserve local evidence even if upload fails;
- add unit tests for the stage trigger, stage ordering, privacy and idempotence before enabling the stage in the desktop runtime.

## Change discipline

Structural refactors and protocol-behavior optimizations are intentionally separated.

A structural PR should first prove behavioral equivalence. Changes such as reordering register reads, altering retry timing against a logger, changing register ranges, or reducing discovery probes should be measured and reviewed separately so a regression can be attributed to one change set.
