# TSUN Local Diagnostic 1.5.20

## Changed

- transient secure-report uploads now use up to **5 attempts** instead of 3;
- retry backoff is progressively increased (`0.75 s`, `2 s`, `5 s`, `10 s`);
- HTTP `Retry-After` is honored for retryable responses when it contains a numeric delay, capped at 30 seconds;
- permanent validation/client errors are still not retried;
- a failed upload always leaves the generated diagnostic JSON available locally for retry or email fallback;
- a new read-only long-duration 02B0 observer is available for intermittent multi-device data-loss investigations.

## Investigation tool

```bash
python3 tools/tsun_observe_02b0.py --observe 60
```

The observer compares a minimal 1-register read with the current 23-register production-shaped read and runs a bounded deeper matrix only when a real failure is observed. It does not store logger IP addresses or Monitor SN values.

Desktop diagnostic: `1.5.20`  
Standalone Python dump tool: `2.9.0`
