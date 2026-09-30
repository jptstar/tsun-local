# Long-running 02B0 observation

`tools/tsun_observe_02b0.py` is a strictly read-only diagnostic intended for intermittent data-loss cases that a short hardware dump may miss.

It does **not** assume that a CRC error, a short response, Wi-Fi quality, or the inverter model is the root cause. Its purpose is to collect comparable evidence from several 02B0 devices over time.

## Typical use

From the repository `tools` directory:

```bash
python3 tsun_observe_02b0.py --observe 60
```

Windows:

```powershell
py tsun_observe_02b0.py --observe 60
```

The default target interval is 30 seconds. The observer deliberately rejects intervals below 5 seconds.

If discovery needs a routed network:

```bash
python3 tsun_observe_02b0.py --network 192.168.1.0/24 --observe 60
```

## Normal round

For every discovered 02B0 logger, each round performs two fresh-connection reads sequentially:

1. FC03 `0x3000..0x3000` — one-register health/control read;
2. FC03 `0x3008..0x301E` — the 23-register production-shaped read.

The JSON keeps timestamps, TCP reachability/latency, result classification, payload length, Modbus byte-count, expected response length and CRC validity. Logger IP addresses and Monitor SN values are used only in process memory and are never written to the report.

## Deep capture after a failure

A failed baseline round triggers a bounded matrix using fresh connections:

- 1 register;
- 8 registers;
- 16 registers;
- 17 registers;
- the historical 22-register shape;
- the current 23-register shape;
- two bounded `sensor_list=0x0000` controls.

Deep captures have a 120-second cooldown and are limited to five per device. This prevents the diagnostic itself from becoming high-rate traffic during a long observation.

The resulting evidence can distinguish, without assigning a speculative root cause:

- one device failing while peers continue to answer;
- several devices failing in the same observation round;
- a minimal read succeeding while a larger production-shaped read fails;
- recovery on the next fresh TCP connection;
- a repeatable request-size or sensor-list difference;
- short `05 00` / `06 00` markers followed, or not followed, by valid Modbus data.

## Interrupted observations

`Ctrl+C` stops the observation and still writes all evidence collected so far. This is intentional for intermittent faults: a partial real failure capture is more useful than losing the session.

## Secure upload

The observer can submit the saved anonymized report explicitly:

```bash
python3 tsun_observe_02b0.py --observe 60 \
  --submit \
  --tester-name nxenara \
  --device TSOL-MS300 \
  --device TSOL-MX450:2 \
  --device TSOL-MS800
```

Transient upload failures use the same retry layer as the desktop diagnostic. The current policy is five attempts with progressive backoff. HTTP 408/425/429/5xx responses and network/timeout failures are retryable; permanent client/validation errors are not. A numeric `Retry-After` response from the server takes priority, bounded to 30 seconds.

If all retries fail, the JSON remains local and can be retried later or sent using the documented email fallback.

## Safety

- read-only Modbus FC03 only;
- no inverter or logger configuration writes;
- no cloud access required for device observation;
- no IP address or Monitor SN in the observation JSON;
- devices are polled sequentially, not simultaneously;
- fresh TCP connection per read to avoid changing normal logger session behavior;
- deep capture runs only after an observed failure.
