# Y4Z / 0x3026 field validation request

This note tracks the first targeted TSUN Local validation request for inverter serial prefix **Y4Z**.

The current stable integration (1.6.1) does not identify this device with protocol families `1511`, `1097`, or `02B0`. A dedicated read-only probe is available at:

- `tools/y4z_3026_readonly_probe.py`

The probe tests the **0x3026** register-family hypothesis using only a local Solarman/AP-wrapped Modbus function `0x03` read of registers `0x0000..0x002C` (45 registers). It deliberately stores raw register values only and does **not** apply the existing DCU1000/battery interpretation.

Validation requested from the device owner:

- exact inverter model from the product label;
- one generated `y4z_3026_probe_*.json` file, or the exact probe error if no valid 3026 response is returned;
- optional confirmation of what the TSUN app reports at the same time (power / daily energy), if convenient.

Safety boundary: read-only, no Modbus writes, no AT commands, no configuration changes, no cloud access. Output does not store logger IP, full inverter serial, full logger serial, MAC address, or credentials.
