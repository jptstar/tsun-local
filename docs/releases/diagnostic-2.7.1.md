# TSUN Local Diagnostic 2.7.1

This diagnostic-only update adds a deliberately narrow, read-only capability probe for logger DNS configuration.

## Added

- Full diagnostics may query `AT+WSDNS` through the logger's local UDP 48899 assistant interface.
- The probe sends only the getter form: `AT+WSDNS` with no `=` and no configuration value.
- The report records whether the query is supported and privacy-safe address properties only.
- The returned DNS server address is never stored in the shareable JSON.

## Safety

- No DNS setting is changed.
- No inverter or logger configuration write is implemented by this probe.
- Standard diagnostics remain unchanged; the probe runs only with `--full`.
- This is evidence collection for a possible future Cloud/Firmware Protection feature, not a cloud blocker itself.
