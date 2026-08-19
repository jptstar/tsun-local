# TSUN Local 1.5.1 research backlog

These MP3000/1511 correlations are intentionally **kept out of 1.5.1-beta.3 semantic Home Assistant entities** until independently validated.

## Very strong

- `0x07F1` → Reactive mode candidate, live raw `0x0066`.
- `0x07F2` → GFCI enable candidate, live raw `1000`.
- `0x07F9` → Calibration K3 candidate, live raw `1003`.
- `0x080D` → Anti-current / anti-reflux delay candidate, live raw `10`, profile value `10 s`.

## Strong but order-indeterminate

- `0x07F7` / `0x07F8` → Calibration K1 / K2 candidate pair, both live raw `1024`; individual order is not assigned.

## Very promising cluster

- `0x080B`–`0x080E` → anti-reflux / zero-export configuration cluster. Individual semantic assignments remain pending.

## Still too ambiguous

- `0x07ED` / `0x0809` → reduction-signal candidates.
- `0x0BD2` → isolation candidate around `60 MΩ`; Rx/Ry assignment is not distinguishable from the current profile.

No write command is implemented or required for this research backlog.
