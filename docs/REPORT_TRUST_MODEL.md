# Diagnostic report trust model

TSUN Local diagnostics are designed to collect useful local protocol evidence without turning a weak signal into a compatibility claim.

## Client-side privacy gate

Before a direct upload, the standalone diagnostic validates the generated JSON locally. Upload requires explicit consent and rejects recognized private fields such as logger IP addresses, monitor serial numbers, full device serial numbers, MAC addresses, Wi-Fi identifiers/passwords, tokens and email addresses.

The direct-upload service performs its own independent validation again. Server-side checks are authoritative for stored reports; the server does not rely only on the client implementation.

## Evidence levels

Stored reports use a server-derived evidence level. The uploaded JSON cannot promote itself to a stronger level.

| Level | Meaning |
|---|---|
| `unverified` | No usable communication evidence was established. |
| `reachable` | The target was reachable, but no protocol/transport was established. |
| `transport_detected` | A candidate transport or protocol endpoint was observed. This is **not** protocol validation. |
| `protocol_validated` | A valid read transaction or an established validated capture confirms protocol communication. |
| `registers_captured` | Valid protocol communication produced raw register evidence. |
| `mapping_verified` | Semantic register mapping was independently reviewed/curated. This level is never granted automatically by an upload. |

Examples:

- TCP port `6668` reachable with no authenticated/read response: `transport_detected`, not "Tuya confirmed".
- Valid Solarman V5 + `02B0` read responses with captured registers: at least `protocol_validated`, normally `registers_captured`.
- A serial prefix such as `Y4Z` can help classify hardware but must never determine the protocol by itself.

## Diagnostic provenance

The upload service records the diagnostic's reported tool version and SHA-256 and compares them with the current `diagnostic-latest` manifest when that manifest is available.

Possible provenance states include:

- `official_current`: version and SHA-256 match the current published dump engine;
- `legacy`: the report came from an older diagnostic version;
- `unverified_build`: no usable tool SHA-256 was supplied;
- `hash_mismatch`: the reported current version does not match the published current SHA-256;
- `non_current_build`: the version is not the current release and is not an older recognized ordering;
- `verification_unavailable`: the release manifest could not be checked at upload time.

Legacy reports remain useful historical evidence; they are not silently discarded. For new protocol research, current diagnostics are preferred.

## Integrity

The report service stores a server-computed SHA-256 of the diagnostic payload. This identifies the exact diagnostic object used for later analysis and helps detect duplicates or accidental substitutions.

## Compatibility claims

A device model or serial-prefix family must not be marked supported from one weak indicator. A support decision should distinguish:

1. hardware identity;
2. transport reachability;
3. protocol validation;
4. register capture;
5. semantic mapping validation;
6. real-device beta confirmation.

This keeps new-device research additive and prevents an experimental detection result from weakening already validated TSUN Local hardware support.
