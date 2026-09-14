# TSUN Local Diagnostic 1.5.15

## Added

- Optional authenticated, strictly read-only Tuya/ThingClips LAN status probing for candidates detected on TCP 6668.
- Interactive Device ID and masked Local Key prompts; credentials remain in process memory and are never saved or uploaded.
- Automatic bounded protocol fallback across Tuya LAN 3.5, 3.4, 3.3, 3.2 and 3.1 using TinyTuya 1.20.0.
- Multiple sanitized DPS snapshots with stable/changing DPS analysis; text and complex values are fingerprinted rather than exported raw.

## Improved

- Extra unrelated LAN candidates no longer prevent safe model assignment for declared TSUN inverters when rated power makes the mapping unambiguous.
- Tuya credential field names are explicitly rejected by the desktop report privacy gate as defense in depth.

No Tuya control/configuration method is used. Authenticated probing calls status/read operations only.
