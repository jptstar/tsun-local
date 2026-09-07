# TSUN Local Diagnostic — cross-platform validation protocol

This document is the canonical validation protocol for the standalone **TSUN Local Diagnostic** desktop application and its optional direct-report upload.

The document path is intentionally kept stable so links published in older forum posts, issues and discussions continue to work.

## Scope

The same shared Tk desktop interface is packaged for:

- Windows x86_64 — `TSUN-Local-Diagnostic.exe`
- macOS — Mac M1 / M2 / M3 / M4… (Apple Silicon) — `TSUN-Local-Diagnostic-macOS-arm64.zip`
- macOS — Mac Intel (older Macs) — `TSUN-Local-Diagnostic-macOS-x86_64.zip`
- Linux x86_64 — `TSUN-Local-Diagnostic-Linux-x86_64`
- Linux arm64 — `TSUN-Local-Diagnostic-Linux-arm64`

All packages must use the same read-only diagnostic engine and the same user flow:

1. **Disable TSUN Local** for the logger being tested.
2. **Run the diagnostic**.
3. **Direct report upload** — recommended, explicit consent required.
4. **Manual e-mail report** — optional fallback only.

The Python `tsun_dump.py` tool remains available for advanced/terminal use and must keep the same read-only behavior.

## Stable download channel

All desktop packages and the Python dumper are published under the rolling `diagnostic-latest` release:

`https://github.com/jptstar/tsun-local/releases/tag/diagnostic-latest`

The historical Windows download URL is deliberately unchanged:

`https://github.com/jptstar/tsun-local/releases/download/diagnostic-latest/TSUN-Local-Diagnostic.exe`

This compatibility rule is part of the release protocol: do not rename or remove the existing Windows asset or the `diagnostic-latest` tag.

## CI / packaging validation

Before a desktop diagnostic update is considered published:

- [ ] Existing unit tests pass.
- [ ] Report-upload unit tests pass.
- [ ] GUI wiring/privacy tests pass.
- [ ] HACS validation passes.
- [ ] Hassfest validation passes.
- [ ] Windows PyInstaller build succeeds.
- [ ] Windows GUI remains running during the startup smoke test.
- [ ] macOS — Mac M1 / M2 / M3 / M4… (Apple Silicon) application build succeeds.
- [ ] macOS — Mac M1 / M2 / M3 / M4… (Apple Silicon) GUI remains running during the startup smoke test.
- [ ] macOS — Mac Intel (older Macs) application build succeeds.
- [ ] macOS — Mac Intel (older Macs) GUI remains running during the startup smoke test.
- [ ] Linux x86_64 portable build succeeds.
- [ ] Linux x86_64 GUI remains running under the virtual-display smoke test.
- [ ] Linux arm64 portable build succeeds.
- [ ] Linux arm64 GUI remains running under the virtual-display smoke test.
- [ ] Every release asset has a matching `.sha256` file.
- [ ] `update.json` contains the `dump`, `windows_gui`, `macos_arm64_gui`, `macos_x86_64_gui`, `linux_x86_64_gui` and `linux_arm64_gui` components.
- [ ] The existing Windows URL still resolves after publication.

## Functional UI validation

Run these checks on each desktop platform when practical:

- [ ] The same **1 → 2 → 3 → 4** layout is displayed.
- [ ] The read-only status is visible.
- [ ] The application-up-to-date indicator becomes green only after a successful update check.
- [ ] The diagnostic cannot start until the user confirms that the affected TSUN Local entry is disabled.
- [ ] Advanced logger IP / Monitor SN fields remain optional.
- [ ] The output folder can be changed and opened with the native file manager (Explorer / Finder / Linux desktop file manager).
- [ ] Step 3 remains the recommended direct-report path.
- [ ] Step 4 remains clearly marked as optional / fallback.
- [ ] `© 2026 @jptstar · GitHub` is visible and opens the public TSUN Local repository.

## Tester profile / micro-inverter selector

- [ ] Up to 10 micro-inverter rows are available.
- [ ] Each row has a searchable model field and an independent quantity field.
- [ ] Typing a fragment filters models (`MS`, `MP3000`, `PLAY`, `800`, etc.).
- [ ] `Sunology PLAY 2` is selectable and searchable by `PLAY` or `Sunology`.
- [ ] Mouse-wheel scrolling over a model or quantity control does **not** silently change its value.
- [ ] Duplicate selected models are merged safely and quantities remain valid (`1..99`).
- [ ] Tester name/pseudonym and selected micro-inverters survive application updates and restarts.
- [ ] Stored profile data remains editable at any time.
- [ ] The explicit upload-consent checkbox is **never** persisted.

Expected profile locations:

- Windows: user `LOCALAPPDATA` / `APPDATA` under `TSUN Local Diagnostic`.
- macOS: `~/Library/Application Support/TSUN Local Diagnostic/` (with migration support for the older `~/.config` location).
- Linux: `$XDG_CONFIG_HOME/TSUN Local Diagnostic/` or `~/.config/TSUN Local Diagnostic/`.

## Off-site synthetic test mode

The upload path can be tested without being at the installation site.

Use exactly:

```text
Logger IP : 89:89:89:89
Monitor SN: 89898989
```

Expected behavior:

- [ ] The application recognizes the dedicated test mode.
- [ ] No logger or micro-inverter network communication is attempted.
- [ ] The generated diagnostic explicitly contains `test_mode: true`.
- [ ] The generated diagnostic explicitly contains `communication_attempted: false`.
- [ ] The user can still enter a tester name and one or more micro-inverter models/quantities.
- [ ] The synthetic report can be sent through the real report-upload service after explicit consent.

This mode validates the complete application → HTTPS Worker → private report storage round trip without pretending that hardware was contacted.

## Direct upload / privacy validation

- [ ] No GitHub credential, GitHub App private key or repository token is embedded in the desktop client.
- [ ] Upload is impossible until the consent checkbox is selected.
- [ ] The client performs its local forbidden-field/privacy validation before network upload.
- [ ] The Worker performs the same privacy validation again server-side.
- [ ] A successful upload returns a unique `TSL-YYYYMMDD-XXXXXXXX` report ID.
- [ ] A successful upload returns a private-token `view_url` for that report.
- [ ] The application displays the report ID and the clickable **Open report / Ouvrir le rapport** link after upload.
- [ ] The report link remains visible in step 3 after the upload dialog is closed.
- [ ] The public application never exposes a direct link to the private reports repository.
- [ ] Opening the Worker link shows exactly the anonymized report associated with that receipt.
- [ ] An invalid or missing view key cannot access the report.

The private reports repository stores each diagnostic once in its chronological `reports/` tree. Generated navigation/indexes then make reports easy to find by **micro-inverter**, **tester** and **month** without duplicating the JSON source file.

## Report index validation

After a real upload:

- [ ] The new report appears once in the private `reports/` tree.
- [ ] `index/reports.json` is rebuilt.
- [ ] `index/devices.json` is rebuilt.
- [ ] `index/testers.json` is rebuilt.
- [ ] The `devices/` navigation reflects every declared model in the report.
- [ ] The `testers/` navigation reflects the pseudonym when one was supplied, otherwise the anonymous group.
- [ ] The `months/` navigation reflects the report submission month.
- [ ] The private repository dashboard remains consistent with the generated indexes.

## Platform-specific release checks

### Windows

- [ ] Existing `TSUN-Local-Diagnostic.exe` download URL remains unchanged.
- [ ] Verified in-place update replaces only the executable after SHA-256 validation.
- [ ] Persisted tester configuration is not removed by an update.

### macOS

- [ ] Both Apple Silicon and Intel archives contain `TSUN Local Diagnostic.app`.
- [ ] The application launches with the same interface and functionality as Windows.
- [ ] Until Apple notarization is configured, documentation explains the first-launch Gatekeeper procedure instead of claiming the package is notarized.
- [ ] Update check uses the correct architecture-specific package and never installs the wrong architecture.

### Linux

- [ ] x86_64 and arm64 assets are separate and correctly identified.
- [ ] Documentation explains that the downloaded file may need `chmod +x` before first launch.
- [ ] Update check uses the matching architecture-specific package.

## Regression rule

A desktop-only change must not add a device write path. The TSUN communication engine remains strictly read-only on all supported desktop platforms. Direct report upload is a separate HTTPS action performed only after explicit user consent.
