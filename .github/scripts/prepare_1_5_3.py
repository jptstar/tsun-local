from __future__ import annotations

from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"
VERSION = "1.5.3"
DATE = "2026-08-27"
FOOTER = 'TSUN Local · by <a href="https://github.com/jptstar">jptstar</a> · <a href="https://github.com/jptstar/tsun-local">GitHub</a> · Home Assistant · Read-only by design'


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def stable_refs(text: str) -> str:
    for old, new in (
        ("1.5.3 BETA", "1.5.3"),
        ("1.5.3 beta", "1.5.3"),
        ("1.5.3-beta.2", "1.5.3"),
        ("v1.5.3-beta.2", "v1.5.3"),
    ):
        text = text.replace(old, new)
    text = re.sub(r'(<strong>)1\.5\.[12](</strong>)', rf'\g<1>{VERSION}\g<2>', text)
    return text


def set_title(text: str, title: str) -> str:
    return re.sub(r"<title>.*?</title>", f"<title>{title}</title>", text, count=1, flags=re.S)


def set_description(text: str, description: str) -> str:
    replacement = f'<meta name="description" content="{description}">'
    if re.search(r'<meta name="description"\s+content=".*?">', text, flags=re.S):
        return re.sub(r'<meta name="description"\s+content=".*?">', replacement, text, count=1, flags=re.S)
    return text.replace("</title>", f"</title>\n  {replacement}", 1)


def set_h1(text: str, h1: str) -> str:
    return re.sub(r"<h1>.*?</h1>", f"<h1>{h1}</h1>", text, count=1, flags=re.S)


def set_footer(text: str) -> str:
    text, count = re.subn(r'<footer class="wrap">.*?</footer>', f'<footer class="wrap">{FOOTER}</footer>', text, count=1, flags=re.S)
    if count != 1:
        raise RuntimeError("footer not found")
    return text


def ensure_canonical(text: str, url: str) -> str:
    tag = f'<link rel="canonical" href="{url}">'
    if 'rel="canonical"' in text:
        return re.sub(r'<link rel="canonical" href=".*?">', tag, text, count=1)
    return text.replace("</title>", f"</title>\n  {tag}", 1)


def ensure_index_seo(text: str) -> str:
    text = set_title(text, "TSUN Local — TSUN Microinverters in Home Assistant")
    text = set_description(text, "Monitor compatible TSUN microinverters locally in Home Assistant with TSUN Local 1.5.3. Automatic discovery, clear-text alarms, read-only local access, no cloud and no proxy. Also compatible with Sunology PLAY2.")
    text = ensure_canonical(text, "https://jptstar.github.io/tsun-local/")
    text = set_h1(text, "TSUN microinverters in Home Assistant — local monitoring with TSUN Local")
    if 'property="og:title"' not in text:
        block = '''  <meta property="og:type" content="website">
  <meta property="og:site_name" content="TSUN Local">
  <meta property="og:title" content="TSUN Local — TSUN Microinverters in Home Assistant">
  <meta property="og:description" content="Automatic local TSUN microinverter monitoring in Home Assistant. Read-only, no cloud, no proxy, with clear-text alarms in 1.5.3.">
  <meta property="og:url" content="https://jptstar.github.io/tsun-local/">
  <meta property="og:image" content="https://jptstar.github.io/tsun-local/icon.png">
  <meta name="twitter:card" content="summary">
  <meta name="twitter:title" content="TSUN Local — TSUN Microinverters in Home Assistant">
  <meta name="twitter:description" content="Local TSUN microinverter monitoring for Home Assistant with automatic discovery and readable alarms.">
  <meta name="twitter:image" content="https://jptstar.github.io/tsun-local/icon.png">
'''
        text = text.replace("</head>", block + "</head>", 1)
    if '"@type":"SoftwareSourceCode"' not in text and '"@type": "SoftwareSourceCode"' not in text:
        structured = '''  <script type="application/ld+json">
  {
    "@context":"https://schema.org",
    "@graph":[
      {"@type":"WebSite","name":"TSUN Local","url":"https://jptstar.github.io/tsun-local/","description":"Local TSUN microinverter monitoring for Home Assistant."},
      {"@type":"SoftwareSourceCode","name":"TSUN Local","softwareVersion":"1.5.3","codeRepository":"https://github.com/jptstar/tsun-local","runtimePlatform":"Home Assistant","programmingLanguage":"Python","description":"Open-source local and read-only Home Assistant integration for compatible TSUN microinverters, also validated with Sunology PLAY2."}
    ]
  }
  </script>
'''
        text = text.replace("</head>", structured + "</head>", 1)
    return text


# Public HTML: stable wording, unique SEO/H1, same footer everywhere.
pages = {
    "index.html": (
        "TSUN Local — TSUN Microinverters in Home Assistant",
        "Monitor compatible TSUN microinverters locally in Home Assistant with TSUN Local 1.5.3. Automatic discovery, clear-text alarms, read-only local access, no cloud and no proxy. Also compatible with Sunology PLAY2.",
        "https://jptstar.github.io/tsun-local/",
        "TSUN microinverters in Home Assistant — local monitoring with TSUN Local",
    ),
    "entities.html": (
        "TSUN Local Entities for Home Assistant — TSUN Microinverters",
        "Home Assistant entity reference for TSUN Local 1.5.3: PV and AC telemetry, communication diagnostics, readable alarms, TSOL-MP3000, TSOL-MX500 and Sunology PLAY2.",
        "https://jptstar.github.io/tsun-local/entities.html",
        "TSUN Local entities for Home Assistant",
    ),
    "sunology-play2.html": (
        "Sunology PLAY2 Home Assistant — TSUN Local Compatibility",
        "Use Sunology PLAY2 locally in Home Assistant with TSUN Local 1.5.3. Validated automatic discovery, read-only monitoring, no cloud and no proxy over the supported 02B0 path.",
        "https://jptstar.github.io/tsun-local/sunology-play2.html",
        "Sunology PLAY2 in Home Assistant with TSUN Local",
    ),
    "contributors.html": (
        "TSUN Local Contributors & Credits",
        "Credits for TSUN Local community contributions: 1097 discovery, protocol and country-profile research, and independent Sunology PLAY2 hardware validation.",
        "https://jptstar.github.io/tsun-local/contributors.html",
        "TSUN Local contributors &amp; credits",
    ),
    "test-your-inverter.html": (
        "Test your TSUN Microinverter with TSUN Local",
        "Your TSUN microinverter may already be compatible with TSUN Local even if it is not listed. Test automatic Home Assistant discovery and share the result.",
        "https://jptstar.github.io/tsun-local/test-your-inverter.html",
        "Test your TSUN microinverter with TSUN Local",
    ),
}
for filename, (title, desc, canonical, h1) in pages.items():
    path = DOCS / filename
    text = stable_refs(read(path))
    text = set_title(text, title)
    text = set_description(text, desc)
    text = ensure_canonical(text, canonical)
    text = set_h1(text, h1)
    text = set_footer(text)
    if filename == "index.html":
        text = ensure_index_seo(text)
    elif filename == "sunology-play2.html":
        text = text.replace("<h2>Plug-and-play installation</h2>", "<h2>Easy installation</h2>")
    elif filename == "test-your-inverter.html":
        text = text.replace(
            '<p class="lead">Your TSUN microinverter may already work with TSUN Local even if its exact commercial model has never been tested before.</p>',
            '<p class="lead"><strong>Not listed yet?</strong> Your TSUN microinverter may already work with TSUN Local even if its exact commercial model has never been tested before.</p>',
        )
    write(path, text)

# Promote public Markdown documentation to stable 1.5.3 wording.
md_paths = [ROOT / "README.md", DOCS / "ENTITIES.md", DOCS / "PLAY2_LOCAL_RESEARCH.md", *sorted(DOCS.glob("README_*.md"))]
for path in md_paths:
    text = stable_refs(read(path))
    text = text.replace("releases/tag/v1.5.2", "releases/tag/v1.5.3")
    text = text.replace("Release 1.5.2", "Release 1.5.3")
    write(path, text)

manifest_path = ROOT / "custom_components" / "tsun_local" / "manifest.json"
manifest = json.loads(read(manifest_path))
manifest["version"] = VERSION
write(manifest_path, json.dumps(manifest, indent=2) + "\n")

# Stable changelog entry, preserving beta history below it.
changelog_path = ROOT / "CHANGELOG.md"
changelog = read(changelog_path)
if f"## [{VERSION}]" not in changelog:
    section = f'''## [{VERSION}] - {DATE}

### Added

- Extend the compact clear-text alarm interface to all supported local protocol families: 1511, 02B0 and 1097, with localized functional descriptions and stable protocol-position codes.
- Add a public **Test your microinverter** page so owners of unlisted TSUN/OEM models can try automatic discovery and report hardware tests.
- Add a **Contributors & credits** page documenting concrete community contributions to TSUN Local.

### Validated

- Promote **Sunology PLAY2** to validated 02B0 hardware after an independent direct TSUN Local / Home Assistant installation automatically discovered the device and completed setup successfully.

### Changed

- Publish readable alarm names for 1511, 02B0 and 1097 while preserving raw alarm words as optional advanced diagnostics.
- Restore a TSUN-first public website around easy installation and automatic discovery while preserving **Your inverter. Your network. Your data.**
- Present compatibility by protocol family first, with real-hardware-tested microinverters listed underneath and a prominent reminder that unlisted models may already be compatible.
- Refresh the README, localized READMEs, entity references, SEO metadata and sitemap for stable 1.5.3.
- Use the same project footer across every public web page.

### Community

- Credit **TheSmartGerman** for the real-world installation that unexpectedly revealed TSUN Local detection of protocol 1097.
- Credit **Stefan Allius** for public TSUN GEN3 / 1097 protocol research and country/profile research used as a reference for country-code/profile interpretation and validation.
- Credit **dca31** for independent Sunology PLAY2 validation through the normal Home Assistant integration flow.

### Safety

- All protocol interpretation, alarm decoding and compatibility validation remain local and read-only.
- No inverter configuration, protection-setting, provisioning, country/profile write or control write is added.

'''
    marker = "All notable changes to this project are documented here. The project follows [Semantic Versioning](https://semver.org/).\n\n"
    if marker not in changelog:
        raise RuntimeError("changelog marker not found")
    changelog = changelog.replace(marker, marker + section, 1)
write(changelog_path, changelog)

# Release notes.
release_notes = f'''# TSUN Local {VERSION}

**Your inverter. Your network. Your data.**

TSUN Local 1.5.3 promotes the field-tested beta work to the stable channel. TSUN microinverters remain at the centre of the project, with broader readable alarm support, validated Sunology PLAY2 compatibility on the supported 02B0 path, and a simpler way for owners of unlisted hardware to test compatibility.

## Highlights

- **Readable inverter alarms on 1511, 02B0 and 1097** with localized descriptions and stable diagnostic codes such as `02B0-A014`.
- **Sunology PLAY2 validated on real hardware** through the normal automatic TSUN Local / Home Assistant setup flow.
- **Automatic discovery remains the default experience**: local, read-only, no proxy, no cloud account in the data path and no protocol selector for normal setup.
- **Dynamic PV inputs** are created only for inputs detected on the inverter.
- **New Test your microinverter page** for models not yet listed in the validated compatibility table.
- **New contributors page** documenting protocol discovery, research and independent hardware validation.

## Alarm interface

The same compact Home Assistant alarm interface is available across the supported local protocol families: **Inverter alarm**, **Active alarms** and **Active alarm names**. Known positions receive clear localized descriptions; unknown or reserved positions remain neutral rather than receiving guessed meanings. Raw alarm words remain available as advanced diagnostics and disabled by default.

Examples:

- `Grid undervoltage (02B0-A014)`
- `PV1 input voltage too low (1511-A137)`
- `Unidentified inverter alarm (1097-A041)`

## Compatibility

Validated real-hardware paths include:

- **TITAN / 1511** — TSUN TSOL-MP3000
- **GEN3 / GEN3 PLUS / 02B0** — TSUN TSOL-MX500
- **GEN3 / GEN3 PLUS / 02B0** — Sunology PLAY2
- **1097** remains experimental while broader independent validation continues.

An unlisted microinverter may already be compatible when it exposes a supported local protocol family.

## Community credits

- **TheSmartGerman** — installation that unexpectedly exposed protocol 1097 detection in TSUN Local.
- **Stefan Allius** — public TSUN GEN3 / 1097 protocol research plus country/profile research used as a reference for country-code/profile interpretation and validation.
- **dca31** — independent Sunology PLAY2 validation on real hardware.

## Safety

TSUN Local remains **local and read-only**. This release adds no inverter configuration, protection-setting, provisioning, country/profile write or control write.
'''
write(DOCS / "releases" / f"{VERSION}.md", release_notes)

# Sitemap: index + all public landing pages.
urls = ["", "entities.html", "sunology-play2.html", "test-your-inverter.html", "contributors.html"]
xml = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
for suffix in urls:
    xml.extend(["  <url>", f"    <loc>https://jptstar.github.io/tsun-local/{suffix}</loc>", f"    <lastmod>{DATE}</lastmod>", "  </url>"])
xml.append("</urlset>")
write(DOCS / "sitemap.xml", "\n".join(xml) + "\n")
write(DOCS / "sitemap.txt", "\n".join(f"https://jptstar.github.io/tsun-local/{suffix}" for suffix in urls) + "\n")

# Update metadata tests to the approved website structure.
test_path = ROOT / "tests" / "test_metadata.py"
test = read(test_path)
test = test.replace("self.assertIn('href=\"entities.html\"', index)", "self.assertIn('entities.html', index)")
test = test.replace("self.assertIn('href=\"sunology-play2.html\"', index)", "self.assertIn('sunology-play2.html', index)")
test = test.replace('self.assertIn("Install it. Add it. TSUN Local finds your inverter.", index)', 'self.assertIn("Your inverter. Your network. Your data.", index)')
test = test.replace('self.assertIn("Alarms in clear, human-readable text", index)', 'self.assertIn("Alarms you can actually read", index)')
test = test.replace('self.assertEqual(sitemap.count("<lastmod>2026-08-26</lastmod>"), 3)', 'self.assertEqual(sitemap.count("<lastmod>2026-08-27</lastmod>"), 5)')
old_list = '''            [
                "https://jptstar.github.io/tsun-local/",
                "https://jptstar.github.io/tsun-local/sunology-play2.html",
                "https://jptstar.github.io/tsun-local/entities.html",
            ],'''
new_list = '''            [
                "https://jptstar.github.io/tsun-local/",
                "https://jptstar.github.io/tsun-local/entities.html",
                "https://jptstar.github.io/tsun-local/sunology-play2.html",
                "https://jptstar.github.io/tsun-local/test-your-inverter.html",
                "https://jptstar.github.io/tsun-local/contributors.html",
            ],'''
if old_list not in test:
    raise RuntimeError("sitemap expectation block not found in metadata tests")
test = test.replace(old_list, new_list)
write(test_path, test)

# Stable 1.5.3 web regression checks.
web_test = '''from __future__ import annotations

from pathlib import Path
import json
import re
import unittest

ROOT = Path(__file__).parents[1]
DOCS = ROOT / "docs"
FOOTER = 'TSUN Local · by <a href="https://github.com/jptstar">jptstar</a> · <a href="https://github.com/jptstar/tsun-local">GitHub</a> · Home Assistant · Read-only by design'
PAGES = ("index.html", "entities.html", "sunology-play2.html", "contributors.html", "test-your-inverter.html")


class Release153WebTests(unittest.TestCase):
    def test_manifest_is_stable_153(self) -> None:
        manifest = json.loads((ROOT / "custom_components" / "tsun_local" / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual("1.5.3", manifest["version"])

    def test_public_pages_have_unique_h1_and_seo(self) -> None:
        seen = set()
        for filename in PAGES:
            text = (DOCS / filename).read_text(encoding="utf-8")
            h1 = re.search(r"<h1>(.*?)</h1>", text, flags=re.S)
            self.assertIsNotNone(h1, filename)
            self.assertNotIn(h1.group(1), seen, filename)
            seen.add(h1.group(1))
            self.assertIn('name="description"', text, filename)
            self.assertIn('rel="canonical"', text, filename)

    def test_all_public_pages_use_identical_footer(self) -> None:
        for filename in PAGES:
            text = (DOCS / filename).read_text(encoding="utf-8")
            match = re.search(r'<footer class="wrap">(.*?)</footer>', text, flags=re.S)
            self.assertIsNotNone(match, filename)
            self.assertEqual(FOOTER, match.group(1), filename)

    def test_public_pages_do_not_advertise_beta_153(self) -> None:
        for filename in PAGES:
            text = (DOCS / filename).read_text(encoding="utf-8").lower()
            self.assertNotIn("1.5.3 beta", text, filename)
            self.assertNotIn("1.5.3-beta", text, filename)

    def test_homepage_keeps_project_identity(self) -> None:
        text = (DOCS / "index.html").read_text(encoding="utf-8")
        self.assertIn("Your inverter. Your network. Your data.", text)
        self.assertIn("TSUN microinverters in Home Assistant", text)
        self.assertIn("Sunology PLAY2", text)
        self.assertIn("test-your-inverter.html", text)
        self.assertIn("contributors.html", text)


if __name__ == "__main__":
    unittest.main()
'''
write(ROOT / "tests" / "test_release_153_web.py", web_test)
