# TSUN Local Diagnostic 1.5.17

## Added

- Add an isolated read-only research fallback for HTTP-identified `1097` loggers when the normal TSUN protocol detection fails and legacy TCP `8899` is unavailable.
- Send only the directed `smartlinkfind` UDP discovery request on port `48899`; no `smart_config` or `config_ack` command is implemented.
- Query the logger's configured firmware/update URL with the getter-only `AT+UPURL` command over the local UDP `48899` AT assistant. The diagnostic never sends `AT+UPURL=...`, never triggers OTA, and never contacts the returned external URL.
- Sanitize any returned update URL before it enters the report: credentials, query string and fragment are removed while preserving the scheme, hostname, port, path and firmware filename needed for protocol/firmware research.
- Add a bounded TCP inventory of common ports plus narrow research ranges around legacy TSUN `8899` and logger discovery/config ports.
- Add GET-only HTTP summaries on likely alternate web ports, TLS handshake-only metadata on likely TLS ports, and receive-only banner fingerprints on other open ports.
- Keep raw UDP/banner payloads, host IPs, full certificates and transport HTTP bodies out of the research report.

## Safety and compatibility

- Normal `1511`, `02B0`, `1097`, experimental `3026`, and Tuya diagnostic paths are attempted first and remain unchanged.
- The research fallback runs only after the normal capture raises the existing “No supported TSUN local protocol detected” error for a firmware identified as `1097` over HTTP with no discovered `tcp8899` source.
- Successful legacy `1097` captures never enter the research path.
- `AT+UPURL` is used only in getter form, without `=` or a value. No external firmware server is contacted by the diagnostic.
- No POST, configuration write, inverter write, reboot, firmware update or OTA operation is implemented by the research probe.
- The extended port inventory is bounded; no 65,535-port scan is performed.
