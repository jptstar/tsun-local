#!/usr/bin/env python3
"""Collect GitHub Release asset download counts and render TSUN Local stats SVGs."""

from __future__ import annotations

import csv
import datetime as dt
import html
import json
import os
from collections import defaultdict
from pathlib import Path
from urllib.request import Request, urlopen

REPO = os.environ.get("GITHUB_REPOSITORY", "jptstar/tsun-local")
ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
CSV_PATH = DOCS / "download-stats.csv"
SUMMARY_SVG = DOCS / "download-stats-summary.svg"
HISTORY_SVG = DOCS / "download-stats-history.svg"
DAILY_SVG = DOCS / "download-stats-daily.svg"
ASSET_NAME = "tsun-local.zip"
MAX_RELEASES = 8


def github_json(path: str):
    token = os.environ.get("GITHUB_TOKEN", "")
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "tsun-local-download-stats",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = Request(f"https://api.github.com{path}", headers=headers)
    with urlopen(req, timeout=30) as response:
        return json.load(response)


def stable_release_counts():
    releases = github_json(f"/repos/{REPO}/releases?per_page=100")
    rows = []
    for release in releases:
        if release.get("draft") or release.get("prerelease"):
            continue
        asset = next(
            (a for a in release.get("assets", []) if a.get("name") == ASSET_NAME),
            None,
        )
        if not asset:
            continue
        published = release.get("published_at") or release.get("created_at") or ""
        rows.append(
            {
                "version": str(release.get("tag_name", "")).removeprefix("v"),
                "tag": release.get("tag_name", ""),
                "published_at": published,
                "downloads": int(asset.get("download_count", 0)),
            }
        )
    rows.sort(key=lambda r: r["published_at"], reverse=True)
    return rows[:MAX_RELEASES]


def read_history():
    if not CSV_PATH.exists():
        return []
    with CSV_PATH.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_history(rows):
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CSV_PATH.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["snapshot_date", "version", "published_at", "downloads"],
        )
        writer.writeheader()
        writer.writerows(rows)


def merge_snapshot(history, releases, today):
    by_key = {(r["snapshot_date"], r["version"]): r for r in history}
    for release in releases:
        by_key[(today, release["version"])] = {
            "snapshot_date": today,
            "version": release["version"],
            "published_at": release["published_at"],
            "downloads": str(release["downloads"]),
        }
    rows = list(by_key.values())
    rows.sort(key=lambda r: (r["snapshot_date"], r["version"]))
    return rows


def esc(value):
    return html.escape(str(value), quote=True)


def svg_text(
    x,
    y,
    text,
    size=14,
    weight="normal",
    anchor="start",
    opacity=1.0,
):
    return (
        f'<text x="{x}" y="{y}" '
        'font-family="system-ui,-apple-system,Segoe UI,Roboto,sans-serif" '
        f'font-size="{size}" font-weight="{weight}" text-anchor="{anchor}" '
        f'opacity="{opacity}">{esc(text)}</text>'
    )


def build_snapshots(history):
    snapshots = defaultdict(dict)
    for row in history:
        snapshots[row["snapshot_date"]][row["version"]] = int(row["downloads"])
    return snapshots


def period_delta(snapshots, today, days):
    dates = sorted(snapshots)
    if len(dates) < 2:
        return None

    current = snapshots.get(today, {})
    target = dt.date.fromisoformat(today) - dt.timedelta(days=days)
    earlier = [d for d in dates if dt.date.fromisoformat(d) <= target]
    if not earlier:
        return None

    base = snapshots[earlier[-1]]
    return sum(
        max(0, current.get(version, 0) - base.get(version, current.get(version, 0)))
        for version in current
    )


def write_summary_svg(history, releases, today):
    snapshots = build_snapshots(history)
    latest = releases[0] if releases else None
    day_delta = period_delta(snapshots, today, 1)
    week_delta = period_delta(snapshots, today, 7)

    items = [
        ("Latest stable", f"v{latest['version']}" if latest else "—"),
        (
            "Latest release downloads",
            f"{latest['downloads']:,}" if latest else "—",
        ),
        ("Last 24 h", f"+{day_delta:,}" if day_delta is not None else "tracking"),
        ("Last 7 days", f"+{week_delta:,}" if week_delta is not None else "tracking"),
    ]

    width, height = 920, 150
    parts = [
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
            f'height="{height}" viewBox="0 0 {width} {height}">'
        ),
        '<rect width="100%" height="100%" rx="12" fill="#f6f8fa" stroke="#d0d7de"/>',
    ]
    cell = width / len(items)

    for i, (label, value) in enumerate(items):
        cx = cell * i + cell / 2
        if i:
            parts.append(
                f'<line x1="{cell*i}" y1="24" x2="{cell*i}" y2="126" stroke="#d8dee4"/>'
            )
        parts.append(svg_text(cx, 58, value, 24, "700", "middle"))
        parts.append(svg_text(cx, 92, label, 13, "normal", "middle", 0.72))

    parts.append(
        svg_text(
            width / 2,
            127,
            f"GitHub Release asset: {ASSET_NAME} · snapshot {today}",
            11,
            "normal",
            "middle",
            0.55,
        )
    )
    parts.append("</svg>")
    SUMMARY_SVG.write_text("\n".join(parts), encoding="utf-8")


def write_history_svg(history, releases):
    release_versions = [r["version"] for r in releases[:5]]
    values = defaultdict(dict)

    for row in history:
        if row["version"] in release_versions:
            values[row["version"]][row["snapshot_date"]] = int(row["downloads"])

    all_dates = sorted({d for per_version in values.values() for d in per_version})
    width, height = 920, 390
    left, right, top, bottom = 72, 28, 48, 62
    plot_w, plot_h = width - left - right, height - top - bottom

    parts = [
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
            f'height="{height}" viewBox="0 0 {width} {height}">'
        ),
        '<rect width="100%" height="100%" rx="12" fill="#ffffff" stroke="#d0d7de"/>',
        svg_text(left, 29, "Cumulative downloads by stable version", 17, "700"),
    ]

    if len(all_dates) < 2:
        parts.append(
            svg_text(
                width / 2,
                height / 2,
                "Historical tracking has just started — the curve will appear after the next daily snapshots.",
                14,
                "normal",
                "middle",
                0.7,
            )
        )
        parts.append("</svg>")
        HISTORY_SVG.write_text("\n".join(parts), encoding="utf-8")
        return

    all_vals = [v for version in values.values() for v in version.values()]
    ymax = max(all_vals) if all_vals else 1
    ymin = min(all_vals) if all_vals else 0
    if ymax == ymin:
        ymax += 1
    span = ymax - ymin

    for i in range(5):
        frac = i / 4
        y = top + plot_h * (1 - frac)
        val = round(ymin + span * frac)
        parts.append(
            f'<line x1="{left}" y1="{y:.1f}" x2="{width-right}" y2="{y:.1f}" stroke="#eaeef2"/>'
        )
        parts.append(svg_text(left - 10, y + 4, f"{val:,}", 11, "normal", "end", 0.65))

    parts.append(
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top+plot_h}" stroke="#8c959f"/>'
    )
    parts.append(
        f'<line x1="{left}" y1="{top+plot_h}" x2="{width-right}" y2="{top+plot_h}" stroke="#8c959f"/>'
    )

    palette = ["#0969da", "#1a7f37", "#8250df", "#bf8700", "#cf222e"]
    x_index = {date: i for i, date in enumerate(all_dates)}

    for idx, version in enumerate(release_versions):
        points = []
        for date, val in sorted(values.get(version, {}).items()):
            x = left + plot_w * (x_index[date] / max(1, len(all_dates) - 1))
            y = top + plot_h * (1 - (val - ymin) / span)
            points.append(f"{x:.1f},{y:.1f}")

        if len(points) >= 2:
            parts.append(
                f'<polyline points="{" ".join(points)}" fill="none" '
                f'stroke="{palette[idx]}" stroke-width="2.5"/>'
            )
        elif points:
            x, y = points[0].split(",")
            parts.append(f'<circle cx="{x}" cy="{y}" r="3" fill="{palette[idx]}"/>')

        legend_x = left + idx * 140
        parts.append(
            f'<line x1="{legend_x}" y1="{height-24}" x2="{legend_x+22}" '
            f'y2="{height-24}" stroke="{palette[idx]}" stroke-width="3"/>'
        )
        parts.append(svg_text(legend_x + 29, height - 20, f"v{version}", 11))

    label_dates = [all_dates[0], all_dates[len(all_dates) // 2], all_dates[-1]]
    for date in dict.fromkeys(label_dates):
        x = left + plot_w * (x_index[date] / max(1, len(all_dates) - 1))
        parts.append(
            svg_text(x, top + plot_h + 24, date[5:], 11, "normal", "middle", 0.65)
        )

    parts.append("</svg>")
    HISTORY_SVG.write_text("\n".join(parts), encoding="utf-8")


def write_daily_svg(history):
    snapshots = build_snapshots(history)
    dates = sorted(snapshots)
    deltas = []

    for previous, current in zip(dates, dates[1:]):
        previous_values = snapshots[previous]
        current_values = snapshots[current]
        delta = sum(
            max(
                0,
                current_values.get(version, 0)
                - previous_values.get(version, current_values.get(version, 0)),
            )
            for version in current_values
        )
        deltas.append((current, delta))

    deltas = deltas[-30:]

    width, height = 920, 320
    left, right, top, bottom = 62, 28, 48, 56
    plot_w, plot_h = width - left - right, height - top - bottom

    parts = [
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
            f'height="{height}" viewBox="0 0 {width} {height}">'
        ),
        '<rect width="100%" height="100%" rx="12" fill="#ffffff" stroke="#d0d7de"/>',
        svg_text(left, 29, "New release-package downloads per day", 17, "700"),
    ]

    if not deltas:
        parts.append(
            svg_text(
                width / 2,
                height / 2,
                "Daily deltas will appear after two snapshots.",
                14,
                "normal",
                "middle",
                0.7,
            )
        )
        parts.append("</svg>")
        DAILY_SVG.write_text("\n".join(parts), encoding="utf-8")
        return

    ymax = max(value for _, value in deltas) or 1

    for i in range(5):
        frac = i / 4
        y = top + plot_h * (1 - frac)
        val = round(ymax * frac)
        parts.append(
            f'<line x1="{left}" y1="{y:.1f}" x2="{width-right}" y2="{y:.1f}" stroke="#eaeef2"/>'
        )
        parts.append(svg_text(left - 10, y + 4, f"{val:,}", 11, "normal", "end", 0.65))

    bar_w = plot_w / max(1, len(deltas)) * 0.68

    for i, (date, value) in enumerate(deltas):
        x = left + plot_w * (i + 0.5) / len(deltas)
        bar_height = plot_h * (value / ymax)
        y = top + plot_h - bar_height
        parts.append(
            f'<rect x="{x-bar_w/2:.1f}" y="{y:.1f}" width="{bar_w:.1f}" '
            f'height="{bar_height:.1f}" rx="2" fill="#0969da"/>'
        )

    for i in sorted({0, len(deltas) // 2, len(deltas) - 1}):
        date = deltas[i][0]
        x = left + plot_w * (i + 0.5) / len(deltas)
        parts.append(
            svg_text(x, top + plot_h + 24, date[5:], 11, "normal", "middle", 0.65)
        )

    parts.append(
        svg_text(
            width - right,
            height - 16,
            "Daily differences between GitHub snapshots",
            10,
            "normal",
            "end",
            0.55,
        )
    )
    parts.append("</svg>")
    DAILY_SVG.write_text("\n".join(parts), encoding="utf-8")


def main():
    today = dt.datetime.now(dt.timezone.utc).date().isoformat()
    releases = stable_release_counts()
    if not releases:
        raise SystemExit(f"No stable release containing {ASSET_NAME!r} was found")

    history = merge_snapshot(read_history(), releases, today)
    write_history(history)
    write_summary_svg(history, releases, today)
    write_history_svg(history, releases)
    write_daily_svg(history)
    print(f"Recorded {len(releases)} stable releases for {today}")


if __name__ == "__main__":
    main()
