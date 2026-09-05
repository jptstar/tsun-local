from pathlib import Path

ROOT = Path(__file__).parents[1]

OLD_EXE = "https://github.com/jptstar/tsun-local/releases/latest/download/TSUN-Local-Diagnostic.exe"
NEW_EXE = "https://github.com/jptstar/tsun-local/releases/download/diagnostic-latest/TSUN-Local-Diagnostic.exe"
OLD_SHA = "https://github.com/jptstar/tsun-local/releases/latest/download/TSUN-Local-Diagnostic.exe.sha256"
NEW_SHA = "https://github.com/jptstar/tsun-local/releases/download/diagnostic-latest/TSUN-Local-Diagnostic.exe.sha256"

LINK_FILES = [
    "README.md",
    "tools/README.md",
    "docs/HARDWARE_DUMP.md",
    "docs/README_DE.md",
    "docs/README_ES.md",
    "docs/README_FR.md",
    "docs/README_IT.md",
    "docs/README_NL.md",
    "docs/README_PL.md",
    "docs/README_ZH.md",
    "docs/index.html",
    "docs/test-your-inverter.html",
]

for name in LINK_FILES:
    path = ROOT / name
    text = path.read_text(encoding="utf-8")
    text = text.replace(OLD_EXE, NEW_EXE).replace(OLD_SHA, NEW_SHA)
    # Avoid introducing trailing-space Markdown line breaks on changed download links.
    text = text.replace(f"]({NEW_EXE})**  \n", f"]({NEW_EXE})**\n")
    path.write_text(text, encoding="utf-8")


def replace_once(path: str, old: str, new: str) -> None:
    file = ROOT / path
    text = file.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{path}: expected one match, found {count}")
    file.write_text(text.replace(old, new, 1), encoding="utf-8")


replace_once(
    "README.md",
    "No installation and no Python environment are required. The portable app uses the same read-only dump engine, discovers TSUN loggers, tests the supported **1511 / 02B0 / 1097** protocol families and creates an anonymized JSON report.\n\nIf you are investigating a communication problem or unavailable entities, **disable the affected TSUN Local config entry before starting the capture**, then re-enable it afterwards.",
    "No installation and no Python environment are required. The portable app uses the same read-only dump engine, discovers TSUN loggers, tests the supported **1511 / 02B0 / 1097** protocol families and creates an anonymized JSON report. The diagnostic tool is distributed independently from TSUN Local integration releases through the rolling **`diagnostic-latest`** release.\n\nThe current Windows interface uses a simple **1 → 2 → 3** flow: disable the affected TSUN Local entry, run the diagnostic, then send the generated JSON to **dev@jptstar.com**. Advanced IP / Monitor SN options and technical logs stay collapsed by default.\n\nThe dump engine is firmware-resilient: it recognizes several Wi-Fi signal layouts (`%` and `dBm`) and can capture a bounded set of passive, same-logger web pages as **anonymized HTML evidence**. It never submits forms, follows external links or calls reboot/reset/update pages.\n\nIf you are investigating a communication problem or unavailable entities, **disable the affected TSUN Local config entry before starting the capture**, then re-enable it afterwards."
)

replace_once(
    "docs/HARDWARE_DUMP.md",
    "No installation and no Python environment are required. The executable is built from the same **strictly read-only** `tsun_dump.py` engine and creates the same privacy-safe JSON reports.",
    "No installation and no Python environment are required. The executable is built from the same **strictly read-only** `tsun_dump.py` engine and creates the same privacy-safe JSON reports. The Windows diagnostic is distributed independently from Home Assistant integration releases through the rolling **`diagnostic-latest`** release.\n\nCurrent standalone diagnostic versions: **dump engine 2.5.0** · **Windows GUI 1.2.0**."
)

replace_once(
    "docs/HARDWARE_DUMP.md",
    "The Windows executable is currently unsigned, so Windows SmartScreen may show an **Unknown publisher** warning. The published SHA-256 file can be used to verify the download.",
    "The Windows executable is currently unsigned, so Windows SmartScreen may show an **Unknown publisher** warning. The published SHA-256 file can be used to verify the download.\n\n### Firmware-resilient logger web capture\n\nFirmware revisions do not always expose logger metadata on the same HTML page or under the same variable name. The 2.5.0 dump engine therefore:\n\n- accepts multiple Wi-Fi signal layouts and preserves whether the value is **%** or **dBm**;\n- records the page/key source used for the detected Wi-Fi signal;\n- starts from the known logger pages and may follow a **bounded maximum of 10 passive same-logger HTML navigation paths**;\n- stores only **anonymized HTML** in the JSON so future firmware layouts can be analysed without keeping the logger IP, full serial number, full MAC address, Wi-Fi credentials or user email;\n- never follows external links, submits forms or calls paths associated with reboot, reset, firmware update, upload, delete or erase actions.\n\nThis web-page capture is diagnostic evidence only. It does not turn the Home Assistant integration into a web crawler and does not add any write path."
)

replace_once(
    "docs/index.html",
    '<a class="card" style="display:block;color:inherit;text-decoration:none" href="https://github.com/jptstar/tsun-local/releases/download/diagnostic-latest/TSUN-Local-Diagnostic.exe"><strong>Windows diagnostic →</strong><span class="muted">Portable read-only diagnostic for unlisted models, unavailable entities and communication issues. No Python required.</span></a>',
    '<a class="card" style="display:block;color:inherit;text-decoration:none" href="https://github.com/jptstar/tsun-local/releases/download/diagnostic-latest/TSUN-Local-Diagnostic.exe"><strong>Windows diagnostic →</strong><span class="muted">Portable read-only tool with a simple 1 → 2 → 3 interface, firmware-resilient Wi-Fi/web diagnostics and anonymized JSON output. Distributed independently through diagnostic-latest.</span></a>'
)

replace_once(
    "docs/test-your-inverter.html",
    '<p class="intro">Capture the problem before reloading the integration. On Windows, the portable diagnostic requires no Python or command prompt and uses the same strictly read-only diagnostic engine.</p>',
    '<p class="intro">Capture the problem before reloading the integration. On Windows, the portable diagnostic requires no Python or command prompt and uses the same strictly read-only diagnostic engine. Its clear 1 → 2 → 3 interface keeps advanced settings hidden unless they are needed.</p>'
)

replace_once(
    "docs/test-your-inverter.html",
    "      Download the Home Assistant diagnostic when possible, then disable the affected TSUN Local config entry. Run the diagnostic, re-enable the entry afterwards, and send both reports together.",
    "      Download the Home Assistant diagnostic when possible, then disable the affected TSUN Local config entry. Run the diagnostic, re-enable the entry afterwards, and send both reports together to dev@jptstar.com. The standalone tool can also retain anonymized evidence from several safe local logger pages when firmware revisions move Wi-Fi or identity fields."
)

replace_once(
    "tools/README.md",
    "For users who are not comfortable with Python or a command prompt, TSUN Local also provides a portable Windows executable built from the same read-only dump engine.",
    "For users who are not comfortable with Python or a command prompt, TSUN Local also provides a portable Windows executable built from the same read-only dump engine. It is published independently from integration releases under `diagnostic-latest`; the current GUI is 1.2.0 and uses the 2.5.0 dump engine."
)

# Guardrails for future documentation changes.
for name in LINK_FILES:
    text = (ROOT / name).read_text(encoding="utf-8")
    if OLD_EXE in text or OLD_SHA in text:
        raise RuntimeError(f"stale diagnostic release link remains in {name}")

for required in ("README.md", "docs/index.html", "docs/test-your-inverter.html", "docs/HARDWARE_DUMP.md"):
    text = (ROOT / required).read_text(encoding="utf-8")
    if "diagnostic-latest" not in text:
        raise RuntimeError(f"missing diagnostic-latest link in {required}")
