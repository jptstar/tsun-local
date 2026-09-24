# TSUN Local documentation

This directory contains the public website, user documentation, technical notes, research evidence and release history for TSUN Local.

## Public documentation

The files kept directly in `docs/` are intentionally stable because they are linked from the project README, GitHub Pages, forum posts or diagnostic workflows.

- [Entity reference](ENTITIES.md)
- [Hardware validation dump guide](HARDWARE_DUMP.md)
- [Desktop diagnostic validation protocol](DIRECT_DIAGNOSTIC_UPLOAD_TEST.md)
- Localized project documentation: `README_FR.md`, `README_DE.md`, `README_ES.md`, `README_IT.md`, `README_NL.md`, `README_PL.md`, `README_ZH.md`
- GitHub Pages / SEO pages: `*.html`, sitemap and related web assets

## Guides

Focused operational and troubleshooting documentation:

- [Long-running 02B0 observation](guides/02B0_OBSERVATION.md)

## Technical documentation

Internal architecture, privacy and diagnostic design:

- [Diagnostic architecture](technical/DIAGNOSTIC_ARCHITECTURE.md)
- [Diagnostic report trust model](technical/REPORT_TRUST_MODEL.md)
- [Passive OTA traffic probe](technical/OTA_PASSIVE_PROBE.md)

## Research and validation

Protocol and hardware investigations backed by read-only evidence:

- [Sunology PLAY2 local protocol research](research/PLAY2_LOCAL_RESEARCH.md)
- [MP3000 / TITAN field validation](research/MP3000_FIELD_VALIDATION.md)
- [MP3000 research checkpoint — 2026-08-19](research/MP3000_RESEARCH_CHECKPOINT_20260819.md)

Raw supporting material remains under [evidence/](evidence/).

## Statistics

GitHub Release download statistics are isolated from the user-facing documentation:

- [Download statistics](stats/DOWNLOAD_STATS.md)
- Raw daily snapshots and generated charts are stored in `stats/`

These counters come from GitHub Release assets only. They are not TSUN Local telemetry and do not represent unique users.

## Releases

Release notes and diagnostic-tool release notes are stored under [releases/](releases/).

---

When adding new documentation, keep public/stable URLs at the root only when they are intended to be linked externally. New research, technical notes and generated statistics should go into their corresponding subdirectory.
