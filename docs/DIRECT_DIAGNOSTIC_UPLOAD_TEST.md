# TSUN Local Diagnostic — release validation protocol

This checklist validates the public diagnostic workflow before publishing or updating the rolling `diagnostic-latest` release.

## Canonical public assets

Only these primary packages are supported:

- `TSUN-Local-Diagnostic.exe` + checksum;
- `TSUN-Local-Diagnostic-Python.zip` + checksum.

The compatibility fallback `tsun_dump.py` and its checksum may also remain on the release.

`update.json` must contain only the active components required by the current distribution: `dump`, `windows_gui` and `python_full`.

## Build and smoke checks

- [ ] Windows executable builds successfully.
- [ ] Windows GUI starts and remains running during the startup smoke test.
- [ ] Full Python package builds successfully.
- [ ] Python CLI `--help` succeeds on every CI platform in the parity matrix.
- [ ] Windows/Python feature-parity tests pass.
- [ ] Every published package has a matching SHA-256 file.
- [ ] The historical Windows URL still resolves after publication.
- [ ] No unsupported `TSUN-Local-Diagnostic-*` package is left on the rolling release.

## Functional UI validation

- [ ] The user can enter a tester name/pseudonym.
- [ ] Up to 10 inverter model/quantity rows remain searchable and editable.
- [ ] The diagnostic cannot start until the user confirms the affected TSUN Local entry is disabled.
- [ ] Advanced logger IP / Monitor SN fields remain optional.
- [ ] Tuya Local Key input is masked.
- [ ] Consent is explicit and is never saved.
- [ ] Successful upload shows service reachable, report stored and `TSL-...` receipt information.
- [ ] The published report link uses the public Worker view URL only.
- [ ] Manual e-mail remains an optional fallback.

## Privacy and safety validation

- [ ] No report contains full local IP addresses.
- [ ] No report contains full Monitor SN or full inverter serial number.
- [ ] No report contains Wi-Fi passwords, tokens or Local Keys.
- [ ] Diagnostic protocol operations remain read-only.
- [ ] No inverter configuration, reboot, reset or firmware-update path is reachable.

## Publication check

After publication, verify the release page, checksums and `update.json`, then run the documentation verifier:

```bash
python scripts/sync_diagnostic_docs.py
```

The verifier must reject stale or unsupported diagnostic asset names in public documentation.
