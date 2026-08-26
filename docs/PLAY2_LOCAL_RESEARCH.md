# Sunology PLAY2 — local compatibility and research history

This document records the read-only local-protocol work that led to direct **Sunology PLAY2** support in TSUN Local.

## Current status — ✅ validated in Home Assistant

The tested Sunology PLAY2 is no longer considered research-only.

An independent community test confirmed that the normal TSUN Local integration in Home Assistant:

- detected the PLAY2 **automatically and quickly**;
- completed the normal integration flow successfully;
- created the device without requiring the dedicated research probe;
- used the local 02B0 path implemented in TSUN Local 1.5.2.

The validated path is:

```text
Sunology PLAY2
  → LSW5BLE logger
  → TCP 8899
  → Solarman V5
  → sensor list 0x02B0
  → Modbus RTU FC03
  → TSUN Local
  → Home Assistant
```

Field-tested logger firmware: `LSW5BLE_17_02B0_1.08-D1`.

> [!IMPORTANT]
> A commercial PLAY2 name may cover different hardware or logger revisions. TSUN Local therefore continues to rely on the **detected local protocol** rather than assuming every PLAY2 unit is electrically or internally identical.

## Recommended installation path

For ordinary PLAY2 users, start with the normal TSUN Local integration:

1. Install TSUN Local through HACS.
2. Restart Home Assistant.
3. Add **TSUN Local** from **Settings → Devices & services**.
4. Let automatic discovery identify the logger and supported protocol.

In the validated test, no manual IP address was required in the successful automatic flow.

The dedicated PLAY2 probe below is retained for hardware research and unusual variants, not as the normal installation method.

## How the local path was identified

Before direct integration validation, PLAY2 testing established the following read-only transport facts:

- iGEN / High-Flying style UDP discovery is available on ports **49999/48899**;
- the actual local logger can be discovered independently from an initially supplied host address;
- TCP **8899** returns valid **Solarman V5** envelopes;
- V5 requests use control code **`0x4510`** and observed responses use **`0x1510`**;
- the real Monitoring SN was required during targeted protocol probing;
- the decisive read used the explicit Solarman sensor-list selector **`0x02B0`**;
- the returned embedded frame was a valid **Modbus RTU FC03** response.

TSUN Local 1.5.2 therefore sends `sensor_list=0x02B0` explicitly for every 02B0 request.

## Logger identity

A bare 12-hex value returned by local discovery is treated as a **logger/module MAC candidate**, not automatically as the MAC address visible to the PLAY2 user.

The historical `WIFIKIT-214028-READ` response layout is:

```text
<IP>,<base MAC>,<logger serial>
```

The diagnostic code keeps separate concepts for:

- an explicit/separated MAC address;
- a compact 12-hex logger/module MAC candidate;
- the PLAY2-visible MAC address.

Full local IP addresses, Monitoring SNs and full MAC addresses are redacted from privacy-safe evidence output.

## Dedicated read-only probe

The research tool remains available for validating other PLAY2 / OEM revisions:

**[`tools/tsun_play2_probe.py`](../tools/tsun_play2_probe.py)**

Windows example:

```powershell
py tsun_play2_probe.py --host PLAY2_IP --monitor-sn MONITOR_SN
```

The probe can perform UDP discovery, local identity correlation, read-only HTTP checks, Solarman V5 reads, embedded-payload classification and a narrow historical V4 read cross-check.

## Safety

The PLAY2 research path is intentionally read-only:

- Modbus **FC03 / FC04 reads only**;
- one historical V4 **read** command `0x0001` in the probe;
- no Modbus write functions;
- no inverter configuration commands;
- no BLE/Wi-Fi provisioning changes;
- no cloud login required for TSUN Local runtime;
- no proxy required in the Home Assistant data path.

## Validation history

The research progressed in two separate steps:

1. **Protocol validation:** a real PLAY2 returned a valid Solarman V5 / 02B0 / Modbus RTU response through TCP 8899.
2. **Integration validation:** the same hardware family was then successfully discovered and installed through the normal TSUN Local Home Assistant flow.

That second step is what changed the public status from **field-confirmed protocol path** to **validated Sunology PLAY2 compatibility**.
