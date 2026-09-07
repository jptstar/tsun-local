# Direct diagnostic upload test plan

This branch adds an optional, explicit-consent HTTPS upload path to the standalone Windows diagnostic.

Validation checklist:

- [ ] Existing unit tests pass.
- [ ] New report-upload unit tests pass.
- [ ] New GUI wiring tests pass.
- [ ] Windows PyInstaller build succeeds.
- [ ] Portable EXE remains running during the startup smoke test.
- [ ] No GitHub credential is embedded in the client.
- [ ] Upload is impossible until the consent checkbox is selected.
- [ ] A real anonymized diagnostic receives a `TSL-...` report ID from the Worker.
- [ ] The private reports repository stores it under `reports/YYYY/MM/`.
- [ ] `index/reports.json`, `index/devices.json`, and `index/testers.json` are rebuilt automatically.

Do not merge this branch until the real Worker round-trip has been confirmed.
