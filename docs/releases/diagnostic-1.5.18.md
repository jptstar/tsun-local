# TSUN Local Diagnostic 1.5.18

## Fixed

- A reachable inverter no longer ends the diagnostic without a report when none of the known local protocol families can be validated.
- Failed protocol detection now produces a privacy-safe JSON report with the bounded `1511`, `02B0`, `1097` and experimental `3026` detection attempts retained for analysis.
- With `--full`, the failure report adds one bounded read-only Modbus observation for each `02B0`, `1097` and `3026` candidate so unknown hardware can be characterized without guessing a register map.
- The existing dedicated `1097` research fallback remains compatible because protocol-detection failures still derive from `RuntimeError`.

## Safety and privacy

- No inverter or logger configuration writes were added.
- The additional Modbus observations use function `0x03` only and request one register per candidate.
- No cloud access is added.
- Host IP, Monitor SN and full inverter serial remain excluded from the shareable report.

## Versions

- Desktop diagnostic: `1.5.18`
- Standalone Python dump tool: `2.8.6`
