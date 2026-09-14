# TSUN Local Diagnostic 1.5.14

## Fixed

- Retry transient diagnostic report upload failures automatically up to three times.
- Retry only safe temporary failures: network/timeout errors and HTTP 408, 425, 429 and selected 5xx responses.
- Do not retry permanent validation/client failures such as HTTP 400.
- Keep the generated diagnostic report local when all retries fail and tell the user to retry later or use the email fallback.

The diagnostic capture itself is unchanged and remains read-only.
