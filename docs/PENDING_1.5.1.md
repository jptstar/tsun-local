# Pending TSUN Local 1.5.1 corrections

**Development branch only — do not publish a new beta yet.**

Corrections currently staged on `beta-1097` while additional review is still in progress:

- MP3000 / 1511 register `0x07EF`: raw `4000` (`0x0FA0`) is decoded with candidate factor `0.01`, giving `40.00 %/Hz` for the overfrequency reduction coefficient. Evidence status remains `LIVE DEVICE READ CONFIRMED; CONFIGURATION CHANGE VALIDATION PENDING`.
- Add a real Home Assistant entity `sensor.…_active_alarm_names` for protocol 1511. The technical entity key/ID stays in English; the displayed entity name and alarm text are localized in all eight supported languages.
- Keep `A001`–`A224` as internal/debug identifiers. User-facing unknown alarm wording no longer includes the internal `Axxx` code; the codes remain available for diagnostics.
- Keep `binary_sensor.…_inverter_alarm` as the simple OK/problem state and `sensor.…_alarm_active_count` as the numeric count.
- No inverter write or configuration command is added.

More corrections may be added before the next beta is published.
