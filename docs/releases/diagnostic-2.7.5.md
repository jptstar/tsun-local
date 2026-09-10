# TSUN Local Diagnostic 2.7.5

The standalone `tsun_dump.py` command-line tool now offers the same report-sharing choice as the desktop diagnostic flow.

## Python end-of-run sharing

After a successful interactive capture, the user can choose to:

- securely submit the anonymized JSON through the TSUN Local report service,
- use the manual email fallback, or
- keep the report locally without transmitting anything.

No report is uploaded without an explicit user choice. `--submit` (alias `--upload`) provides explicit consent for scripted runs; `--no-submit` disables the sharing prompt.

Before any network transmission, every generated report is loaded and recursively checked for forbidden privacy fields. If any report fails that local validation, none of the reports are transmitted. The server continues to perform its own second validation pass.

The desktop application keeps its existing consent/upload interface and invokes the embedded dump engine with `--no-submit`, so users never see two upload prompts.
