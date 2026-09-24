# Passive OTA traffic probe

`tools/tsun_ota_probe.py` is a research-only, passive network observer for identifying the network path used by TSUN logger firmware updates.

It is deliberately separate from the Home Assistant integration and from the normal hardware dump. It **does not trigger an update**, open a socket to the logger, change DNS/server settings, submit logger web forms, upload firmware, or inject packets.

## What it observes

The probe delegates packet capture to `tcpdump`, consumes the capture stream in memory, and writes only reduced metadata to JSON:

- DNS query names sent by the logger;
- TLS ClientHello SNI when visible;
- HTTP host, method and path, with query strings removed;
- remote transport/port activity and private/public scope;
- packet counts.

The logger IP, MAC addresses, raw packets, PCAP data, packet payloads, HTTP query strings, cookies and credentials are not written to the report. Private DNS suffixes such as `.home`, `.lan` and `.local` are replaced with `<private-domain>`.

The capture filter is intentionally broad enough to discover an OTA path that is not yet known:

```text
host <LOGGER_IP> and (udp port 53 or (tcp and not port 8899))
```

Port 8899 is excluded so normal TSUN Local polling does not dominate the research capture.

## Running it

Requirements:

- Python 3.10+
- `tcpdump` available in `PATH` (or pass `--tcpdump PATH`)
- permission to capture on the selected interface

Example on Linux / Synology / another host that can observe the logger traffic:

```bash
sudo python3 tools/tsun_ota_probe.py \
  --host 192.168.1.50 \
  --interface any \
  --duration 300 \
  --output tsun_ota_probe.json
```

On macOS, select the interface that carries the logger traffic, for example `en0`, instead of assuming `any` is available.

Windows can use this tool only when a tcpdump-compatible capture binary is installed (for example through a packet-capture environment based on Npcap). The normal portable TSUN diagnostic EXE does **not** install a packet driver and this research probe is not embedded in it.

## Recommended research sequence

1. Start the passive probe.
2. Leave TSUN Local operating normally if desired; port 8899 is excluded from this capture.
3. From the official TSUN application or vendor interface, perform only a **check for firmware/update availability** when such a function is available.
4. Do not confirm or start an actual firmware installation unless that is explicitly intended.
5. Stop the probe after the check and share the generated JSON.

If the vendor application does not expose a harmless update-check action, simply leave the probe running during a normal cloud session. The report may still reveal DNS, cloud endpoints or a firmware-download connection, but absence of such traffic does not prove that no OTA path exists.

## Current limitations

Version 0.1.0 decodes IPv4 only. TLS is never decrypted; only SNI from a ClientHello that fits in one captured TCP segment can be recorded. HTTP paths are visible only for unencrypted HTTP. These limitations are intentional for the first privacy-safe research iteration.
