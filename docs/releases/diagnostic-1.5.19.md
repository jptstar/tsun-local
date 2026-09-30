# TSUN Local Diagnostic 1.5.19

## Changed

- Extend the isolated read-only research path used only when a known `1097` logger is identified over HTTP but the legacy TCP `8899` transport is unavailable.
- Parse already-fetched logger configuration evidence such as the configured transport mode, port, UART parameters and inverter profile without storing private IP addresses or remote hostnames.
- Add repeated lifecycle checks of the configured local TCP port before and after harmless read-only probes.
- Add documented query-only HF-A11 AT getters over UDP `48899`; no assignment form (`=`), configuration command, reset or reboot command is sent.
- Add bounded extra TCP inventory, GET-only HTTP rechecks, a read-only UDP `1097` FC03 probe and `1097` validation attempts on a small set of alternate open TCP ports.

## Safety / non-regression

- Normal successful `1511`, `02B0`, `1097`, `3026` and Tuya diagnostic captures are unchanged.
- The extended research activates only after the existing diagnostic has already classified the device as `1097-research` with `legacy_tcp_8899_unavailable`.
- Only Modbus function `0x03` is used by the new active inverter probe; no Modbus write function is sent.
- HTTP research uses `GET` only; no form submission or configuration endpoint is called.
- TCP scanning is bounded and never scans all 65,535 ports.
- If the extension itself fails, the existing partial `1097-research` report is preserved instead of failing the diagnostic.

Desktop diagnostic: `1.5.19`  
Standalone Python dump tool: `2.9.0`
