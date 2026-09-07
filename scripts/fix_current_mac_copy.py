#!/usr/bin/env python3
"""Synchronize current diagnostic download wording and homepage navigation."""

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]

REPLACEMENTS = {
    "Which Mac should I download once the signed builds are published?": "Which Mac should I download?",
    "Which Mac should I download once the signed builds are published?**": "Which Mac should I download?**",
    "Quel Mac choisir lorsque les builds signés seront publiés ?": "Quel Mac choisir ?",
    "Quel Mac choisir lorsque les builds signes seront publies ?": "Quel Mac choisir ?",
}

PATHS = [
    ROOT / "README.md",
    ROOT / "tools" / "README.md",
    ROOT / "docs" / "HARDWARE_DUMP.md",
    ROOT / "docs" / "DIRECT_DIAGNOSTIC_UPLOAD_TEST.md",
    *sorted((ROOT / "docs").glob("README_*.md")),
]

for path in PATHS:
    text = path.read_text(encoding="utf-8")
    updated = text
    for old, new in REPLACEMENTS.items():
        updated = updated.replace(old, new)
    if updated != text:
        path.write_text(updated, encoding="utf-8")

# Homepage: add direct arrows to each validated hardware page.
path = ROOT / "docs" / "index.html"
text = path.read_text(encoding="utf-8")
text = text.replace(
    ".tested-device{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:11px 13px;border:1px solid var(--line);border-radius:12px;background:#fff}",
    ".tested-device{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:11px 13px;border:1px solid var(--line);border-radius:12px;background:#fff;color:inherit;text-decoration:none;transition:border-color .15s ease,transform .15s ease}.tested-device:hover{border-color:#b8cbe1;transform:translateY(-1px)}.tested-device>span:first-child{display:flex;flex-direction:column}.tested-link{flex:0 0 auto;color:var(--blue);font-size:27px;font-weight:900;line-height:1}",
)
text = text.replace(
    ".tested-device{align-items:flex-start;flex-direction:column;gap:2px}",
    ".tested-device{align-items:center;flex-direction:row;gap:12px}",
)

device_links = {
    '<div class="tested-device"><strong>TSOL-MP3000</strong><span class="tested-brand">TSUN</span></div>':
    '<a class="tested-device" href="tsol-mp3000-home-assistant.html"><span><strong>TSOL-MP3000</strong><span class="tested-brand">TSUN</span></span><span class="tested-link" aria-hidden="true">→</span></a>',
    '<div class="tested-device"><strong>TSOL-MX500</strong><span class="tested-brand">TSUN</span></div>':
    '<a class="tested-device" href="tsol-mx500-home-assistant.html"><span><strong>TSOL-MX500</strong><span class="tested-brand">TSUN</span></span><span class="tested-link" aria-hidden="true">→</span></a>',
    '<div class="tested-device"><strong>TSOL-MS800</strong><span class="tested-brand">TSUN</span></div>':
    '<a class="tested-device" href="tsol-ms800-home-assistant.html"><span><strong>TSOL-MS800</strong><span class="tested-brand">TSUN</span></span><span class="tested-link" aria-hidden="true">→</span></a>',
    '<div class="tested-device"><strong>TSOL-MS2000</strong><span class="tested-brand">TSUN</span></div>':
    '<a class="tested-device" href="tsol-ms2000-home-assistant.html"><span><strong>TSOL-MS2000</strong><span class="tested-brand">TSUN</span></span><span class="tested-link" aria-hidden="true">→</span></a>',
    '<div class="tested-device"><strong>PLAY2</strong><span class="tested-brand">Sunology</span></div>':
    '<a class="tested-device" href="sunology-play2.html"><span><strong>PLAY2</strong><span class="tested-brand">Sunology</span></span><span class="tested-link" aria-hidden="true">→</span></a>',
}
for old, new in device_links.items():
    if old in text:
        text = text.replace(old, new, 1)

new_docs = '''  <section id="docs">
    <h2>Diagnostic tools</h2>
    <p class="intro">Choose the simplest way to capture a read-only TSUN diagnostic.</p>
    <div class="grid">
      <a class="card" style="display:block;color:inherit;text-decoration:none" href="https://github.com/jptstar/tsun-local/releases/download/diagnostic-latest/TSUN-Local-Diagnostic.exe"><strong>Windows diagnostic →</strong><span class="muted">Download the Windows app and run the guided diagnostic. No Python required.</span></a>
      <a class="card" style="display:block;color:inherit;text-decoration:none" href="test-your-inverter.html#python"><strong>Python diagnostic →</strong><span class="muted">One script for Windows, macOS and Linux, with clear terminal commands.</span></a>
      <a class="card" style="display:block;color:inherit;text-decoration:none" href="test-your-inverter.html#mac-linux"><strong>Mac &amp; Linux diagnostic →</strong><span class="muted">Download the packaged app for your Mac or Linux architecture.</span></a>
    </div>
  </section>'''
text, count = re.subn(r'  <section id="docs">.*?</section>', new_docs, text, count=1, flags=re.S)
if count != 1:
    raise RuntimeError("Could not replace homepage diagnostic section")
path.write_text(text, encoding="utf-8")

# Test page: present Windows first, Python second, then Mac/Linux.
path = ROOT / "docs" / "test-your-inverter.html"
text = path.read_text(encoding="utf-8")
text = text.replace(
    '<p class="lead"><strong>Not listed yet, or communication unstable?</strong> Run the diagnostic directly with Python or use the packaged Windows, macOS or Linux application, then optionally send an anonymized report.</p>',
    '<p class="lead"><strong>Not listed yet, or communication unstable?</strong> Start with the Windows app, use Python on any platform, or choose the packaged Mac/Linux app.</p>',
)
text = text.replace(
    '<p class="hero-note">Python 3.10+ · Five desktop packages · Strictly read-only hardware communication</p>',
    '<p class="hero-note">Windows · Python 3.10+ · macOS &amp; Linux · Strictly read-only</p>',
)

replacement = '''  <section id="windows">
    <h2>Windows diagnostic</h2>
    <p class="intro"><strong>Recommended on Windows.</strong> Download the app, launch the guided read-only diagnostic, then send the anonymized report directly from the interface after consent.</p>
    <div class="actions">
      <a class="button primary" href="https://github.com/jptstar/tsun-local/releases/download/diagnostic-latest/TSUN-Local-Diagnostic.exe">Download for Windows</a>
      <a class="button secondary" href="https://github.com/jptstar/tsun-local/releases/tag/diagnostic-latest">Release &amp; checksums</a>
    </div>
    <div class="callout"><strong>Simple guided test.</strong>No Python installation is required.</div>
  </section>

  <section id="python">
    <h2>Python diagnostic — all platforms</h2>
    <p class="intro">Prefer the terminal? Download <code>tsun_dump.py</code> and run it with Python 3.10+ on Windows, macOS or Linux.</p>
    <div class="actions">
      <a class="button primary" href="https://github.com/jptstar/tsun-local/releases/download/diagnostic-latest/tsun_dump.py">Download tsun_dump.py</a>
      <a class="button secondary" href="https://github.com/jptstar/tsun-local/releases/download/diagnostic-latest/tsun_dump.py.sha256">SHA-256</a>
      <a class="button secondary" href="https://github.com/jptstar/tsun-local/blob/main/docs/HARDWARE_DUMP.md">Full Python guide</a>
    </div>
    <div class="python-highlight">
      <strong>Recommended full diagnostic</strong>
      <div class="command-grid">
        <div class="command-card"><strong>Windows</strong><pre><code>py tsun_dump.py --full</code></pre></div>
        <div class="command-card"><strong>macOS / Linux</strong><pre><code>python3 tsun_dump.py --full</code></pre></div>
      </div>
      <p>To target one known logger or a routed subnet:</p>
      <div class="command-grid">
        <div class="command-card"><strong>Known logger</strong><pre><code>python3 tsun_dump.py --host 192.168.1.50 --full</code></pre></div>
        <div class="command-card"><strong>Routed subnet / VLAN</strong><pre><code>python3 tsun_dump.py --network 192.168.1.0/24 --full</code></pre></div>
      </div>
      <p>On Windows, replace <code>python3</code> with <code>py</code> in the commands above.</p>
    </div>
  </section>

  <section id="mac-linux">
    <h2>Mac &amp; Linux diagnostic</h2>
    <p class="intro">Use the packaged desktop app if you prefer not to run Python. Choose the package for your architecture.</p>
    <div class="privacy"><strong>Which Mac?</strong> Apple chip <strong>M1, M2, M3, M4 or newer</strong> → Apple Silicon. If <strong>About This Mac</strong> says Intel → Mac Intel.</div>
    <div class="mac-warning"><strong>🟠 macOS — first launch</strong><p><strong>The app is not yet notarized by Apple.</strong> macOS may block the first launch. You do not need to disable Gatekeeper.</p><ol><li>Download and unzip the Mac package.</li><li>Try to open <strong>TSUN Local Diagnostic.app</strong> once, then click <strong>Done</strong> if blocked.</li><li>Open <strong>System Settings → Privacy &amp; Security</strong>.</li><li>Click <strong>Open Anyway</strong>, authenticate, then confirm <strong>Open</strong>.</li></ol></div>
    <div class="actions">
      <a class="button secondary" href="https://github.com/jptstar/tsun-local/releases/download/diagnostic-latest/TSUN-Local-Diagnostic-macOS-arm64.zip">Mac Apple Silicon</a>
      <a class="button secondary" href="https://github.com/jptstar/tsun-local/releases/download/diagnostic-latest/TSUN-Local-Diagnostic-macOS-x86_64.zip">Mac Intel</a>
      <a class="button secondary" href="https://github.com/jptstar/tsun-local/releases/download/diagnostic-latest/TSUN-Local-Diagnostic-Linux-x86_64">Linux x86_64</a>
      <a class="button secondary" href="https://github.com/jptstar/tsun-local/releases/download/diagnostic-latest/TSUN-Local-Diagnostic-Linux-arm64">Linux ARM64</a>
      <a class="button secondary" href="https://github.com/jptstar/tsun-local/releases/tag/diagnostic-latest">Release &amp; checksums</a>
    </div>
    <div class="privacy"><strong>Linux:</strong> the downloaded file may need <code>chmod +x</code> once.</div>
  </section>'''
pattern = r'  <section>\n    <h2>Python / command line — all platforms</h2>.*?  <section>\n    <h2>Four clear steps</h2>'
match = re.search(pattern, text, flags=re.S)
if match:
    text = text[:match.start()] + replacement + '\n\n  <section>\n    <h2>Four clear steps</h2>' + text[match.end():]
text = text.replace(
    '<div class="step"><span class="n">2</span><strong>Run the diagnostic</strong><p>Use the Python command above or launch the desktop application. Discovery, protocol detection and evidence capture are read-only.</p></div>',
    '<div class="step"><span class="n">2</span><strong>Run the diagnostic</strong><p>Use Windows, Python, Mac or Linux. Discovery and evidence capture remain read-only.</p></div>',
)
path.write_text(text, encoding="utf-8")

print("Current diagnostic wording and navigation synchronized.")
