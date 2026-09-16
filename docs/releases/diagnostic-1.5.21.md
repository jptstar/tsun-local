# TSUN Local Diagnostic 1.5.21

## Architecture consolidation

This release reorganizes the desktop diagnostic composition without changing the TSUN protocol transactions performed by `tsun_dump.py`.

- desktop-only 1097/Tuya extensions now have one explicit, tested runtime composition point;
- the extension order is declared and idempotent, preventing accidental double wrapping;
- upload privacy validation, safe model association and transient retry policy now live in one canonical uploader;
- Tuya credential field names are rejected by the canonical privacy gate rather than being added at desktop startup;
- the extra-LAN-candidate model assignment used for mixed TSUN/Tuya installations is now the default canonical policy;
- the former retry and model-assignment modules remain compatibility shims so existing imports continue to work;
- the long-running 02B0 observer remains deliberately separate from the normal one-shot diagnostic.

## Unchanged behavior

This structural release does **not** change:

- protocol register ranges;
- Modbus/native read functions;
- logger/inverter write policy (still read-only);
- TSUN protocol detection order or retry counts;
- capture timeouts;
- diagnostic JSON schema;
- the user consent requirement for upload;
- Windows/macOS/Linux packaging behavior.

## Validation focus

New tests cover:

- explicit 1097/Tuya runtime ordering;
- runtime idempotence and conflicting-order rejection;
- canonical 5-attempt upload retry behavior;
- HTTP `Retry-After` handling;
- permanent 4xx no-retry behavior;
- Tuya credential privacy rejection;
- nxenara-style TSUN + unrelated Tuya model assignment;
- compatibility of the former retry/model-assignment import paths.

See [`DIAGNOSTIC_ARCHITECTURE.md`](../DIAGNOSTIC_ARCHITECTURE.md) for the maintained execution model and rules for future diagnostic extensions.
