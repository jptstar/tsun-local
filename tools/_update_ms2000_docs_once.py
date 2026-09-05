#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).parents[1]


def replace_required(text: str, old: str, new: str, *, label: str) -> str:
    if old not in text:
        raise RuntimeError(f"Missing expected text for {label}: {old!r}")
    return text.replace(old, new, 1)


def update_readme(path: Path, credit: str) -> None:
    text = path.read_text(encoding="utf-8")
    text = replace_required(
        text,
        "**TSOL-MX500** · **TSOL-MS800** · **Sunology PLAY2**",
        "**TSOL-MX500** · **TSOL-MS800** · **TSOL-MS2000** · **Sunology PLAY2**",
        label=f"{path} validated 02B0 list",
    )

    lines = text.splitlines()
    updated_lines: list[str] = []
    removed_likely = False
    for line in lines:
        if line.startswith("- **02B0") and "`TSOL-MS2000`" in line:
            line = line.replace(" · `TSOL-MS2000`", "")
            removed_likely = True
        updated_lines.append(line)
    if not removed_likely:
        raise RuntimeError(f"Did not remove MS2000 from likely list in {path}")
    text = "\n".join(updated_lines) + ("\n" if text.endswith("\n") else "")

    ms800_link = "**[TSOL-MS800 Home Assistant](https://jptstar.github.io/tsun-local/tsol-ms800-home-assistant.html)**"
    ms2000_link = "**[TSOL-MS2000 Home Assistant](https://jptstar.github.io/tsun-local/tsol-ms2000-home-assistant.html)**"
    text = replace_required(
        text,
        ms800_link,
        f"{ms800_link} · {ms2000_link}",
        label=f"{path} MS2000 page link",
    )

    if "**paloindici**" not in text:
        marker = next((line for line in text.splitlines() if line.startswith("- **Kmotr**")), None)
        if marker is None:
            raise RuntimeError(f"Missing Kmotr credit in {path}")
        text = text.replace(marker, f"{marker}\n{credit}", 1)

    path.write_text(text, encoding="utf-8")


README_CREDITS = {
    "README.md": "- **paloindici** — independent TSOL-MS2000 validation with TSUN Local, including anonymized Home Assistant diagnostics for both TSOL-MS2000 and TSOL-MP3000 plus the hardware dump that confirmed the 02B0 / four-PV path.",
    "docs/README_FR.md": "- **paloindici** — validation indépendante du TSOL-MS2000 avec TSUN Local, avec diagnostics Home Assistant anonymisés du TSOL-MS2000 et du TSOL-MP3000 ainsi qu’un dump matériel confirmant le chemin 02B0 / 4 entrées PV.",
    "docs/README_DE.md": "- **paloindici** — unabhängige TSOL-MS2000-Validierung mit TSUN Local, einschließlich anonymisierter Home-Assistant-Diagnosen für TSOL-MS2000 und TSOL-MP3000 sowie eines Hardware-Dumps zur Bestätigung des 02B0-/Vier-PV-Pfads.",
    "docs/README_ES.md": "- **paloindici** — validación independiente del TSOL-MS2000 con TSUN Local, con diagnósticos anonimizados de Home Assistant para TSOL-MS2000 y TSOL-MP3000 y un volcado de hardware que confirmó la ruta 02B0 / cuatro entradas PV.",
    "docs/README_IT.md": "- **paloindici** — validazione indipendente del TSOL-MS2000 con TSUN Local, con diagnostica Home Assistant anonimizzata per TSOL-MS2000 e TSOL-MP3000 e un dump hardware che ha confermato il percorso 02B0 / quattro ingressi PV.",
    "docs/README_NL.md": "- **paloindici** — onafhankelijke validatie van de TSOL-MS2000 met TSUN Local, inclusief geanonimiseerde Home Assistant-diagnostiek voor TSOL-MS2000 en TSOL-MP3000 en een hardwaredump die het 02B0-/vier-PV-pad bevestigde.",
    "docs/README_PL.md": "- **paloindici** — niezależna walidacja TSOL-MS2000 z TSUN Local, obejmująca zanonimizowane diagnostyki Home Assistant dla TSOL-MS2000 i TSOL-MP3000 oraz zrzut sprzętowy potwierdzający ścieżkę 02B0 / cztery wejścia PV.",
    "docs/README_ZH.md": "- **paloindici** — 使用 TSUN Local 对 TSOL-MS2000 进行了独立实机验证，提供了 TSOL-MS2000 和 TSOL-MP3000 的匿名 Home Assistant 诊断，以及确认 02B0 / 4 路 PV 路径的硬件转储。",
}

for filename, credit in README_CREDITS.items():
    update_readme(ROOT / filename, credit)

index_path = ROOT / "docs" / "index.html"
index = index_path.read_text(encoding="utf-8")
index = index.replace(
    "Validated on TSOL-MP3000, TSOL-MX500, TSOL-MS800 and Sunology PLAY2;",
    "Validated on TSOL-MP3000, TSOL-MX500, TSOL-MS800, TSOL-MS2000 and Sunology PLAY2;",
)
index = index.replace(
    "TSOL-MP3000, TSOL-MX500, TSOL-MS800, Sunology PLAY2",
    "TSOL-MP3000, TSOL-MX500, TSOL-MS800, TSOL-MS2000, Sunology PLAY2",
)
index = index.replace(
    "real-hardware validation on TSOL-MP3000, TSOL-MX500, TSOL-MS800 and Sunology PLAY2.",
    "real-hardware validation on TSOL-MP3000, TSOL-MX500, TSOL-MS800, TSOL-MS2000 and Sunology PLAY2.",
)
index = index.replace(
    '\"TSOL-MS800\",\"Sunology PLAY2\"',
    '\"TSOL-MS800\",\"TSOL-MS2000\",\"Sunology PLAY2\"',
)
index = replace_required(
    index,
    '<div class="tested-device"><strong>TSOL-MS800</strong><span class="tested-brand">TSUN</span></div>',
    '<div class="tested-device"><strong>TSOL-MS800</strong><span class="tested-brand">TSUN</span></div>\n          <div class="tested-device"><strong>TSOL-MS2000</strong><span class="tested-brand">TSUN</span></div>',
    label="homepage MS2000 tested device",
)
index = index.replace(
    "including validated MX500, MS800 and Sunology PLAY2 paths.",
    "including validated MX500, MS800, MS2000 and Sunology PLAY2 paths.",
)
index = replace_required(
    index,
    '<a class="card" style="display:block;color:inherit;text-decoration:none" href="tsol-ms800-home-assistant.html"><strong>TSOL-MS800 →</strong><span class="muted">Community-validated 02B0 hardware with two MPPT inputs and independent Home Assistant diagnostic feedback.</span></a>',
    '<a class="card" style="display:block;color:inherit;text-decoration:none" href="tsol-ms800-home-assistant.html"><strong>TSOL-MS800 →</strong><span class="muted">Community-validated 02B0 hardware with two MPPT inputs and independent Home Assistant diagnostic feedback.</span></a>\n      <a class="card" style="display:block;color:inherit;text-decoration:none" href="tsol-ms2000-home-assistant.html"><strong>TSOL-MS2000 →</strong><span class="muted">Community-validated 02B0 hardware with four PV inputs, firmware V4.0.39 and independent Home Assistant diagnostics.</span></a>',
    label="homepage MS2000 documentation card",
)
index = replace_required(
    index,
    '<span><a href="https://github.com/Kmotr"><strong>@Kmotr</strong></a> — independent TSOL-MS800 validation with TSUN Local and an anonymized Home Assistant diagnostic.</span>',
    '<span><a href="https://github.com/Kmotr"><strong>@Kmotr</strong></a> — independent TSOL-MS800 validation with TSUN Local and an anonymized Home Assistant diagnostic.</span>\n      <span><a href="https://github.com/paloindici"><strong>@paloindici</strong></a> — independent TSOL-MS2000 validation with four PV inputs, plus anonymized TSOL-MS2000 / MP3000 diagnostics and a hardware dump that improved the standalone diagnostic tool.</span>',
    label="homepage paloindici credit",
)
if "TSOL-MS2000" not in index:
    raise RuntimeError("Homepage does not mention MS2000")
index_path.write_text(index, encoding="utf-8")

contributors_path = ROOT / "docs" / "contributors.html"
contributors = contributors_path.read_text(encoding="utf-8")
contributors = contributors.replace(
    "Sunology PLAY2 validation and TSOL-MS800 hardware validation.",
    "Sunology PLAY2 validation, TSOL-MS800 hardware validation and TSOL-MS2000 hardware validation.",
)
contributors = contributors.replace('"dateModified":"2026-08-28"', '"dateModified":"2026-09-05"')
contributors = replace_required(
    contributors,
    '<div class="card"><span class="role">Independent TSOL-MS800 hardware validation</span><a href="https://github.com/Kmotr"><strong>@Kmotr</strong></a><p>Validated TSUN Local on a real TSOL-MS800, shared an anonymized Home Assistant diagnostic and confirmed the tested 02B0 hardware path works in normal use.</p></div>',
    '<div class="card"><span class="role">Independent TSOL-MS800 hardware validation</span><a href="https://github.com/Kmotr"><strong>@Kmotr</strong></a><p>Validated TSUN Local on a real TSOL-MS800, shared an anonymized Home Assistant diagnostic and confirmed the tested 02B0 hardware path works in normal use.</p></div>\n<div class="card"><span class="role">Independent TSOL-MS2000 hardware validation</span><a href="https://github.com/paloindici"><strong>@paloindici</strong></a><p>Validated TSUN Local on a real TSOL-MS2000 with four PV inputs, shared anonymized Home Assistant diagnostics for the MS2000 and MP3000, and provided the hardware dump that confirmed the tested 02B0 path and helped improve logger metadata parsing in the standalone diagnostic tool.</p></div>',
    label="contributors paloindici card",
)
contributors_path.write_text(contributors, encoding="utf-8")

entities_path = ROOT / "docs" / "entities.html"
entities = entities_path.read_text(encoding="utf-8")
entities = entities.replace(
    "TSOL-MP3000, TSOL-MX500, TSOL-MS800 and Sunology PLAY2.",
    "TSOL-MP3000, TSOL-MX500, TSOL-MS800, TSOL-MS2000 and Sunology PLAY2.",
)
entities = entities.replace(
    "TSOL-MS800 Home Assistant, Sunology PLAY2 Home Assistant sensors",
    "TSOL-MS800 Home Assistant, TSOL-MS2000 Home Assistant, Sunology PLAY2 Home Assistant sensors",
)
entities = entities.replace(
    "TSOL-MX500 · TSOL-MS800 · Sunology PLAY2",
    "TSOL-MX500 · TSOL-MS800 · TSOL-MS2000 · Sunology PLAY2",
)
entities = entities.replace(
    "TSOL-MS800 and Sunology PLAY2 have both been independently validated on real hardware through TSUN Local.",
    "TSOL-MS800, TSOL-MS2000 and Sunology PLAY2 have been independently validated on real hardware through TSUN Local.",
)
entities = entities.replace(
    "Validated on TSOL-MX500, TSOL-MS800 and Sunology PLAY2. Up to four PV inputs are created dynamically when exposed by the device.",
    "Validated on TSOL-MX500, TSOL-MS800, TSOL-MS2000 and Sunology PLAY2. Up to four PV inputs are created dynamically when exposed by the device.",
)
entities = replace_required(
    entities,
    '<div class="card"><strong>TSOL-MS800</strong>Community-validated real hardware with two MPPT inputs and an anonymized Home Assistant diagnostic.</div>',
    '<div class="card"><strong>TSOL-MS800</strong>Community-validated real hardware with two MPPT inputs and an anonymized Home Assistant diagnostic.</div><div class="card"><strong>TSOL-MS2000</strong>Community-validated 02B0 hardware with four detected PV inputs, inverter firmware V4.0.39 and anonymized Home Assistant diagnostics.</div>',
    label="entities MS2000 card",
)
entities = replace_required(
    entities,
    '<a class="btn" href="tsol-ms800-home-assistant.html">TSOL-MS800 compatibility →</a>',
    '<a class="btn" href="tsol-ms800-home-assistant.html">TSOL-MS800 compatibility →</a><a class="btn" href="tsol-ms2000-home-assistant.html">TSOL-MS2000 compatibility →</a>',
    label="entities MS2000 action",
)
entities_path.write_text(entities, encoding="utf-8")

sitemap_path = ROOT / "docs" / "sitemap.xml"
sitemap = sitemap_path.read_text(encoding="utf-8")
sitemap = replace_required(
    sitemap,
    "  <url>\n    <loc>https://jptstar.github.io/tsun-local/tsol-ms800-home-assistant.html</loc>\n  </url>",
    "  <url>\n    <loc>https://jptstar.github.io/tsun-local/tsol-ms800-home-assistant.html</loc>\n  </url>\n  <url>\n    <loc>https://jptstar.github.io/tsun-local/tsol-ms2000-home-assistant.html</loc>\n  </url>",
    label="sitemap MS2000",
)
sitemap_path.write_text(sitemap, encoding="utf-8")

ms2000_page = '''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>TSOL-MS2000 Home Assistant — Local Integration | TSUN Local</title>
  <meta name="description" content="Connect the TSUN TSOL-MS2000 to Home Assistant locally with TSUN Local. Community-validated 02B0 support, four PV inputs, firmware V4.0.39, no cloud and no proxy.">
  <meta name="keywords" content="TSOL-MS2000 Home Assistant, TSUN MS2000, TSUN Local, 02B0, GEN3, HACS, four PV inputs, TSUN microinverter, local solar monitoring">
  <meta name="robots" content="index,follow,max-image-preview:large">
  <meta name="theme-color" content="#0a315e">
  <link rel="canonical" href="https://jptstar.github.io/tsun-local/tsol-ms2000-home-assistant.html">
  <link rel="icon" type="image/png" href="icon.png">
  <meta property="og:type" content="article">
  <meta property="og:site_name" content="TSUN Local">
  <meta property="og:title" content="TSOL-MS2000 in Home Assistant with TSUN Local">
  <meta property="og:description" content="Connect the TSUN TSOL-MS2000 to Home Assistant locally with TSUN Local. Community-validated 02B0 support, four PV inputs, firmware V4.0.39, no cloud and no proxy.">
  <meta property="og:url" content="https://jptstar.github.io/tsun-local/tsol-ms2000-home-assistant.html">
  <meta property="og:image" content="https://jptstar.github.io/tsun-local/icon.png">
  <meta name="twitter:card" content="summary">
  <meta name="twitter:title" content="TSOL-MS2000 in Home Assistant with TSUN Local">
  <meta name="twitter:description" content="Community-validated local 02B0 monitoring for the TSUN TSOL-MS2000 with four PV inputs.">
  <meta name="twitter:image" content="https://jptstar.github.io/tsun-local/icon.png">
  <script type="application/ld+json">{"@context":"https://schema.org","@graph":[{"@type":"TechArticle","headline":"TSOL-MS2000 in Home Assistant — validated local 02B0 monitoring","description":"Connect the TSUN TSOL-MS2000 to Home Assistant locally with TSUN Local. Community-validated 02B0 support, four PV inputs, firmware V4.0.39, no cloud and no proxy.","mainEntityOfPage":"https://jptstar.github.io/tsun-local/tsol-ms2000-home-assistant.html","dateModified":"2026-09-05","author":{"@type":"Person","name":"Jean-Philippe TESTART","url":"https://github.com/jptstar"},"isPartOf":{"@type":"WebSite","name":"TSUN Local","url":"https://jptstar.github.io/tsun-local/"},"about":["TSUN TSOL-MS2000","Home Assistant","TSUN Local","GEN3 / GEN3 PLUS","02B0","four PV inputs","local solar monitoring"]},{"@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":1,"name":"TSUN Local","item":"https://jptstar.github.io/tsun-local/"},{"@type":"ListItem","position":2,"name":"TSOL-MS2000 in Home Assistant — validated local 02B0 monitoring","item":"https://jptstar.github.io/tsun-local/tsol-ms2000-home-assistant.html"}]}]}</script>
  <style>
:root{--ink:#10223a;--muted:#617188;--paper:#f4f7fb;--card:#fff;--line:#dce5ef;--blue:#1167d8;--green:#148660;--green-soft:#e7f7f1;--shadow:0 18px 50px rgba(19,50,88,.10);--max:1000px}*{box-sizing:border-box}body{margin:0;color:var(--ink);background:var(--paper);font:16px/1.6 Inter,ui-sans-serif,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}a{color:var(--blue)}.wrap{width:min(var(--max),calc(100% - 32px));margin:auto}header{padding:26px 0 68px;color:#fff;background:linear-gradient(145deg,#061c39,#0a315e 72%,#105a9a)}.brand{color:#fff;text-decoration:none;font-weight:850}.hero{padding-top:48px}.tag{display:inline-block;padding:6px 10px;border-radius:999px;color:#0d684d;background:#dff7ed;font-size:12px;font-weight:900}h1{max-width:880px;margin:14px 0 0;font-size:clamp(42px,7vw,68px);line-height:1;letter-spacing:-.05em}.lead{max-width:800px;color:#d6e5f7;font-size:20px}.strap{font-weight:850}.actions{display:flex;flex-wrap:wrap;gap:10px;margin-top:24px}.btn{display:inline-block;padding:12px 16px;border-radius:11px;text-decoration:none;font-weight:850}.primary{color:#071829;background:#8ee4ff}.secondary{color:#fff;border:1px solid rgba(255,255,255,.28);background:rgba(255,255,255,.08)}main{margin-top:-28px;padding-bottom:60px}section{margin-top:26px;padding:30px;border:1px solid var(--line);border-radius:22px;background:var(--card);box-shadow:var(--shadow)}h2{margin:0 0 10px;font-size:32px;letter-spacing:-.035em}.intro{margin:0;color:var(--muted);font-size:18px}.grid{display:grid;grid-template-columns:repeat(2,1fr);gap:15px;margin-top:22px}.card{padding:20px;border:1px solid var(--line);border-radius:16px;background:#f8fafd}.card strong{display:block;margin-bottom:6px}.code{margin-top:18px;padding:18px;border-radius:14px;background:#0e2036;color:#dceaff;font:14px/1.55 ui-monospace,SFMono-Regular,Menlo,monospace;white-space:pre-wrap}.note{margin-top:18px;padding:18px;border-radius:15px;color:#0d684d;background:var(--green-soft)}footer{padding:0 0 38px;text-align:center;color:var(--muted);font-size:14px}@media(max-width:700px){.grid{grid-template-columns:1fr}section{padding:23px}}
</style>
</head>
<body>
<header><div class="wrap"><a class="brand" href="./">← TSUN Local</a><div class="hero"><span class="tag">COMMUNITY VALIDATED ON REAL TSOL-MS2000 HARDWARE</span><h1>TSOL-MS2000 in Home Assistant — validated local 02B0 monitoring</h1><p class="lead">A real TSUN TSOL-MS2000 has been tested with TSUN Local in Home Assistant, confirming the 02B0 path, four detected PV inputs and normal adaptive polling on independent hardware.</p><p class="strap">Automatic discovery · Local · Read-only · No cloud · No proxy</p><div class="actions"><a class="btn primary" href="https://my.home-assistant.io/redirect/hacs_repository/?owner=jptstar&amp;repository=tsun-local&amp;category=integration">Add TSUN Local to HACS</a><a class="btn secondary" href="entities.html">Entity reference</a><a class="btn secondary" href="https://github.com/jptstar/tsun-local/issues/41">Validation issue #41</a><a class="btn secondary" href="https://github.com/jptstar/tsun-local">GitHub</a></div></div></div></header>
<main class="wrap">
  <section><h2>Validated compatibility</h2><p class="intro">This page documents a real-hardware compatibility path, not a model-name assumption. TSUN Local still identifies devices from the local protocol exposed by the inverter/logger combination.</p><div class="grid"><div class="card"><strong>✅ Community validation</strong><a href="https://github.com/paloindici"><strong>@paloindici</strong></a> tested a real TSOL-MS2000 with TSUN Local and supplied both the hardware dump and Home Assistant diagnostics.</div><div class="card"><strong>☀️ Four PV inputs</strong>PV1 through PV4 expose voltage, current, power, daily energy and total energy with coherent values on the tested unit.</div><div class="card"><strong>🧩 Tested hardware path</strong>Serial prefix <code>Y00</code>, logger firmware <code>LSW5_SSL_02B0_1.05</code>, logger profile <code>688:Tengsheng_G3</code> and inverter firmware <code>V4.0.39</code>.</div><div class="card"><strong>📡 Communication validation</strong>The Home Assistant diagnostic recorded <strong>176 successful polls out of 176</strong>, zero communication failures and normal adaptive polling at 20 seconds.</div></div></section>
  <section><h2>Local protocol path</h2><div class="code">TSUN TSOL-MS2000
  → local network
  → protocol 02B0
  → TSUN Local
  → Home Assistant</div><div class="note"><strong>Protocol:</strong> 02B0 on the validated unit. Rated power is reported as 2000 W. No inverter configuration writes are implemented.</div></section>
  <section><h2>What the validation confirmed</h2><div class="grid"><div class="card"><strong>AC telemetry</strong>Voltage, current, frequency, power, daily energy and total energy were present and plausible.</div><div class="card"><strong>PV telemetry</strong>All four PV inputs returned coherent voltage, current, power and energy values.</div><div class="card"><strong>Diagnostics</strong>Inverter firmware, temperature, rated/max power, grid diagnostics and alarm state are available through the 02B0 adapter.</div><div class="card"><strong>Alarm state</strong>No active alarm was reported in the supplied Home Assistant diagnostic.</div></div></section>
  <section><h2>Home Assistant setup</h2><ol><li>Install <strong>TSUN Local</strong> through HACS.</li><li>Restart Home Assistant.</li><li>Add <strong>TSUN Local</strong> from Settings → Devices &amp; services.</li><li>Use automatic discovery when available, then verify protocol <strong>02B0</strong> and the four detected PV inputs.</li></ol></section>
  <section><h2>Validation evidence</h2><p class="intro">Thanks to <a href="https://github.com/paloindici"><strong>@paloindici</strong></a> for the independent TSOL-MS2000 test, the anonymized Home Assistant diagnostics for both the MS2000 and MP3000, and the hardware dump shared in <a href="https://github.com/jptstar/tsun-local/issues/41">compatibility issue #41</a>. That dump also exposed false-positive logger firmware/MAC metadata in the standalone dumper, which was subsequently corrected.</p></section>
  <section><h2>Independent community project</h2><p class="intro">TSUN Local is unofficial and independent. It is not developed, approved, endorsed or maintained by TSUN. Product names belong to their respective owners.</p></section>
</main>
<footer class="wrap">TSUN Local · by <a href="https://github.com/jptstar">jptstar</a> · <a href="https://github.com/jptstar/tsun-local">GitHub</a> · Home Assistant · Read-only by design</footer>
</body></html>
'''
(ROOT / "docs" / "tsol-ms2000-home-assistant.html").write_text(ms2000_page, encoding="utf-8")

metadata_test_path = ROOT / "tests" / "test_metadata.py"
metadata_test = metadata_test_path.read_text(encoding="utf-8")
metadata_test = replace_required(
    metadata_test,
    '        play2 = (ROOT / "docs" / "sunology-play2.html").read_text(encoding="utf-8")',
    '        play2 = (ROOT / "docs" / "sunology-play2.html").read_text(encoding="utf-8")\n        ms2000 = (ROOT / "docs" / "tsol-ms2000-home-assistant.html").read_text(encoding="utf-8")',
    label="metadata load MS2000 page",
)
metadata_test = replace_required(
    metadata_test,
    '        self.assertIn("No proxy", play2)',
    '        self.assertIn("No proxy", play2)\n\n        self.assertIn("TSOL-MS2000 in Home Assistant", ms2000)\n        self.assertIn("COMMUNITY VALIDATED ON REAL TSOL-MS2000 HARDWARE", ms2000)\n        self.assertIn("LSW5_SSL_02B0_1.05", ms2000)\n        self.assertIn("V4.0.39", ms2000)\n        self.assertIn("paloindici", ms2000)',
    label="metadata MS2000 assertions",
)
metadata_test = replace_required(
    metadata_test,
    '            "https://jptstar.github.io/tsun-local/tsol-ms800-home-assistant.html",',
    '            "https://jptstar.github.io/tsun-local/tsol-ms800-home-assistant.html",\n            "https://jptstar.github.io/tsun-local/tsol-ms2000-home-assistant.html",',
    label="metadata sitemap MS2000",
)
metadata_test_path.write_text(metadata_test, encoding="utf-8")

web_test_path = ROOT / "tests" / "test_release_154_web.py"
web_test = web_test_path.read_text(encoding="utf-8")
web_test = replace_required(
    web_test,
    'PAGES = ("index.html", "entities.html", "sunology-play2.html", "tsol-mp3000-home-assistant.html", "tsol-mx500-home-assistant.html", "tsol-ms800-home-assistant.html", "contributors.html", "test-your-inverter.html")',
    'PAGES = ("index.html", "entities.html", "sunology-play2.html", "tsol-mp3000-home-assistant.html", "tsol-mx500-home-assistant.html", "tsol-ms800-home-assistant.html", "tsol-ms2000-home-assistant.html", "contributors.html", "test-your-inverter.html")',
    label="web PAGES MS2000",
)
web_test = replace_required(
    web_test,
    '            "tsol-ms800-home-assistant.html",\n            "sunology-play2.html",',
    '            "tsol-ms800-home-assistant.html",\n            "tsol-ms2000-home-assistant.html",\n            "sunology-play2.html",',
    label="web sitemap MS2000",
)
web_test = replace_required(
    web_test,
    '        self.assertIn("tsol-ms800-home-assistant.html", text)',
    '        self.assertIn("tsol-ms800-home-assistant.html", text)\n        self.assertIn("tsol-ms2000-home-assistant.html", text)\n        self.assertIn("paloindici", text)',
    label="homepage MS2000 test",
)
web_test_path.write_text(web_test, encoding="utf-8")

localized_test_path = ROOT / "tests" / "test_stable_151_localized_readmes.py"
localized_test = localized_test_path.read_text(encoding="utf-8")
localized_test = replace_required(
    localized_test,
    '            self.assertIn("**TSOL-MX500** · **TSOL-MS800** · **Sunology PLAY2**", text, filename)',
    '            self.assertIn("**TSOL-MX500** · **TSOL-MS800** · **TSOL-MS2000** · **Sunology PLAY2**", text, filename)',
    label="localized validated list test",
)
localized_test = replace_required(
    localized_test,
    '            self.assertIn("tsol-ms800-home-assistant.html", text, filename)',
    '            self.assertIn("tsol-ms800-home-assistant.html", text, filename)\n            self.assertIn("tsol-ms2000-home-assistant.html", text, filename)',
    label="localized MS2000 link test",
)
localized_test = replace_required(
    localized_test,
    '            self.assertNotIn("`TSOL-MS800`", likely_02b0, filename)',
    '            self.assertNotIn("`TSOL-MS800`", likely_02b0, filename)\n            self.assertNotIn("`TSOL-MS2000`", likely_02b0, filename)',
    label="localized likely list test",
)
localized_test = replace_required(
    localized_test,
    '            self.assertIn("dca31", text, filename)',
    '            self.assertIn("dca31", text, filename)\n            self.assertIn("paloindici", text, filename)',
    label="localized contributor test",
)
localized_test_path.write_text(localized_test, encoding="utf-8")

print("MS2000 documentation update applied")
