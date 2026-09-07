# macOS Developer ID signing and notarization

TSUN Local Diagnostic only publishes macOS packages to the rolling `diagnostic-latest` release when both Developer ID signing and Apple notarization succeed.

This is deliberate: ordinary users must not be asked to bypass Gatekeeper security warnings. Windows and Linux remain publishable even while the Apple credentials are not configured.

## Required Apple material

Use an active Apple Developer Program account and create:

1. A **Developer ID Application** certificate, exported from Keychain Access as a password-protected `.p12` file.
2. An **App Store Connect API key** (`.p8`) with access suitable for notarization.

Do not commit either file to the repository.

## GitHub Actions secrets

Configure these repository Actions secrets:

- `MACOS_CERTIFICATE_P12_BASE64` — base64 of the exported Developer ID Application `.p12`.
- `MACOS_CERTIFICATE_P12_PASSWORD` — password used when exporting the `.p12`.
- `APPLE_NOTARY_KEY_P8_BASE64` — base64 of the App Store Connect `AuthKey_XXXXXXXXXX.p8` file.
- `APPLE_NOTARY_KEY_ID` — the API key ID.
- `APPLE_NOTARY_ISSUER_ID` — the App Store Connect issuer ID.

Example local encoding commands:

```bash
base64 -i DeveloperIDApplication.p12 | pbcopy
base64 -i AuthKey_XXXXXXXXXX.p8 | pbcopy
```

Paste only the resulting base64 values into GitHub Actions secrets.

## Release behavior

On pull requests, macOS builds may use an ad-hoc signature only for CI smoke testing.

On `main`:

1. PyInstaller builds `TSUN Local Diagnostic.app`.
2. The workflow imports the Developer ID Application certificate into a temporary keychain.
3. The app is signed with hardened runtime and timestamping.
4. The signed app is submitted with `xcrun notarytool`.
5. Apple acceptance is required.
6. The notarization ticket is stapled to the app.
7. `stapler`, `codesign` and `spctl` verification must pass.
8. Only then is the final ZIP uploaded to `diagnostic-latest`.

The public filenames stay unchanged:

- `TSUN-Local-Diagnostic-macOS-arm64.zip`
- `TSUN-Local-Diagnostic-macOS-x86_64.zip`

Therefore the same stable download URLs can be reused after notarization is enabled.

If the Apple secrets are missing, the workflow deliberately withholds/removes public macOS assets instead of distributing an unnotarized app.
