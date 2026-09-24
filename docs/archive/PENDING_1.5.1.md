# TSUN Local 1.5.1 research backlog

These MP3000/1511 correlations are intentionally **kept out of 1.5.1 semantic Home Assistant entities** until independently validated by a controlled setting change or distinct hardware observation.

## Very strong — exact live/profile match

- `0x07F1` → Reactive mode candidate, live raw `0x0066`, profile `0066`. The surrounding 1511 sequence also mirrors the public 02B0/GEN3 parameter sequence (`1, 0x139C, 0x0FA0, temperature, 0x0066, 1000, 1024`).
- `0x07F2` → GFCI enable candidate, live raw `1000`, profile `1000`; also positionally corroborated by the same 02B0 sequence.
- `0x07F9` → Calibration K3 candidate, live raw `1003`, profile `1003`; the immediately preceding pair is `1024, 1024`, matching K1/K2 values.
- `0x080D` → Anti-current / anti-reflux delay candidate, live raw `10`, profile `10 s`, inside the adjacent zero-export cluster.

Evidence status remains: **LIVE DEVICE READ CONFIRMED; CONFIGURATION CHANGE VALIDATION PENDING**.

## Strong but order-indeterminate

- `0x07F7` / `0x07F8` → Calibration K1 / K2 candidate pair, both live raw `1024`; K1 and K2 also both equal `1024` in the profile, so their individual order cannot be distinguished on this unit.

## Stronger than before

- `0x07ED = 1` is now the leading candidate for the **overfrequency-reduction enable/signal** because it sits immediately before the confirmed `0x07EE = 50.20 Hz` reduction threshold and `0x07EF = 40.00 %/Hz` coefficient, and the homologous public 02B0 sequence has the same leading `1` at this position.
- `0x0809 = 1` should no longer be treated as an equal reduction-signal candidate. Its position immediately before the anti-reflux/zero-export cluster makes it an unidentified enable/status flag; semantic assignment remains open.

## Very promising cluster

- `0x080B`–`0x080E` currently reads `3000, 0, 10, 0`. This matches the value set formed by zero-export injection power (`3000 W`), anti-current delay (`10 s`) and zero-valued anti-current/anti-reflux fields, but the individual zero-valued assignments remain ambiguous. `0x080D` is the distinctive member and is tracked separately above.

## Dynamic isolation candidate — do not name Rx/Ry yet

- `0x0BD2` previously read `60000`, which is compatible with `60.000 MΩ` at `×0.001 MΩ`; the latest low-power dump reads `44666`, compatible with `44.666 MΩ` at the same scale. This behaviour is more consistent with a **live insulation measurement** than a fixed 60 MΩ setting.
- The profile contains both Rx and Ry at `60.00 MΩ`, but there is not yet a second independently identified 1511 word proving which channel, if either, `0x0BD2` represents. Do not expose it as Rx or Ry yet.

No write command is implemented or required for this research backlog.
