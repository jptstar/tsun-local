# TSUN Local Diagnostic 2.7.3

Diagnostic 2.7.3 deepens the strictly read-only logger web research.

## Static JavaScript research

Full diagnostic mode now extracts privacy-scrubbed source bodies for selected logger functions related to network/DNS, remote-server configuration and firmware upload. The source is parsed as text only: JavaScript is never executed, forms are never submitted, and no POST, firmware upload, reboot or configuration write is performed.

Targeted functions include `sta_form_apply`, `step_setting_apply`, `server_setting_apply`, `sw_upload_apply`, `yzsw_upload_apply`, `internetSet` and `wirelessSet`. Function bodies are bounded and include a SHA-256 for comparison across logger firmware versions.

## Metadata fix

The generic logger-firmware fallback now rejects plain numeric UI/help values such as `13`, while explicit `cover_ver` / `webdata_ver` firmware variables remain preferred.

## Windows bundle

The GUI remains 1.4.1. Its updater already refreshes the Windows bundle when the embedded dump engine is older, so publishing dump engine 2.7.3 is sufficient to update existing 1.4.1 executables.

## Safety

Local, privacy-safe and strictly read-only. No logger or inverter write operation is added.
