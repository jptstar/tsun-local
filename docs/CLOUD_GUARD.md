# TSUN Local Cloud Guard

Cloud Guard is being developed as an optional advanced protection feature for TSUN Local.

## Design principles

- Normal TSUN Local operation remains read-only.
- Network-protection writes will require explicit user opt-in and confirmation.
- Existing logger settings must be captured before any future change and must be restorable.
- No proxy, TLS interception, firmware upload, reboot, or hidden write is performed by the foundation implemented here.
- The official Home Assistant Core TSUN integration is not part of this feature.

## Foundation phase

The first phase only discovers whether the logger exposes the local web capabilities that would be needed later:

- remote/cloud server configuration (`/remote.html`)
- DNS configuration (`/wireless.html`)
- local logger firmware upload interface (`/update.html`)
- local inverter firmware upload interface (`/invupdate.html`)

The integration records only privacy-safe capability metadata in Home Assistant diagnostics. Server host names, DNS addresses, logger IP addresses and credentials are not included in the Cloud Guard research summary.

The diagnostics explicitly report `write_operations_performed: false`.

## Why writes are not enabled yet

Real TSUN firmware families differ, and SSL/10443 devices can react badly to unsafe server changes. Before an opt-in write mode is exposed, TSUN Local must validate on real hardware that the selected operation is reversible and that local access on port 8899 remains available.

The intended future flow is:

1. Read and save the original configuration.
2. Show the exact planned change.
3. Require explicit confirmation.
4. Apply one narrowly scoped change.
5. Verify local web access, port 8899 and protocol polling.
6. Offer immediate restoration of the saved configuration.
7. Abort and restore automatically when validation fails where technically possible.

## Planned protection controls

The target user-facing controls remain independent:

- **Block TSUN cloud communication**
- **Block TSUN firmware downloads**

They will not be presented as guaranteed until the integration can prove the selected mechanism on the detected logger/firmware family.
