from pathlib import Path

ROOT = Path(__file__).parents[1]


def patch_index() -> None:
    path = ROOT / "docs/index.html"
    text = path.read_text(encoding="utf-8")

    text = text.replace(
        '<div class="navlinks"><a href="#features">Features</a><a href="#compatibility">Compatibility</a><a href="#alarms">Alarms</a><a href="#install">Install</a><a href="#docs">Docs</a></div>',
        '<div class="navlinks"><a href="#features">Features</a><a href="#compatibility">Compatibility</a><a href="#alarms">Alarms</a><a href="#install">Install</a><a href="#docs">Docs</a><a href="#community">Credits</a></div>',
        1,
    )

    text = text.replace(
        '.community-credit{margin-top:20px;padding:18px 20px;border:1px solid var(--line);border-radius:16px;background:#f8fafd}.community-credit>strong{display:block;margin-bottom:5px}.community-credit span{display:block;color:var(--muted)}.community-credit a{display:inline-block;margin-top:10px;font-weight:800;text-decoration:none}footer',
        '.community-credit{margin-top:20px;padding:18px 20px;border:1px solid var(--line);border-radius:16px;background:#f8fafd}.community-credit>strong{display:block;margin-bottom:8px}.community-credit span{display:block;color:var(--muted)}.community-credit span+span{margin-top:8px}.community-credit span a{display:inline;font-weight:800}.community-credit>a{display:inline-block;margin-top:12px;font-weight:800;text-decoration:none}footer',
        1,
    )

    old = '''  <section id="community">
    <h2>Independent community project</h2>
    <p class="intro">TSUN Local is unofficial and independent. It is not developed, approved, endorsed or maintained by TSUN or Sunology. Product names belong to their respective owners.</p>
    <p>Created and maintained by <a href="https://github.com/jptstar"><strong>Jean-Philippe TESTART (jptstar)</strong></a> for the Home Assistant community.</p>
    <div class="community-credit">
      <strong>Community contributions</strong>
      <span>TSUN Local has also benefited from protocol research, hardware validation and community testing.</span>
      <a href="contributors.html">See contributors &amp; credits →</a>
    </div>
  </section>'''

    new = '''  <section id="community">
    <h2>Credits &amp; independent community project</h2>
    <p class="intro">TSUN Local is unofficial and independent. It is not developed, approved, endorsed or maintained by TSUN, Sunology, Solarman or the projects and contributors credited below. Product and project names belong to their respective owners.</p>
    <p>Created and maintained by <a href="https://github.com/jptstar"><strong>Jean-Philippe TESTART (jptstar)</strong></a> for the Home Assistant community.</p>
    <div class="community-credit">
      <strong>Public protocol research &amp; community contributions</strong>
      <span><a href="https://github.com/davidrapan/ha-solarman"><strong>David Rapan · ha-solarman</strong></a> — public Home Assistant Solarman protocol and inverter-profile work used as an independent cross-reference during selected 02B0 register research.</span>
      <span><a href="https://github.com/s-allius/tsun-gen3-proxy"><strong>Stefan Allius · tsun-gen3-proxy</strong></a> — public GEN3 / 1097 protocol research and country/profile references used during experimental protocol validation.</span>
      <span><strong>TheSmartGerman</strong> — real-device testing that revealed the additional 1097 protocol family.</span>
      <span><strong>dca31</strong> — independent Sunology PLAY2 validation through the normal TSUN Local Home Assistant flow.</span>
      <a href="contributors.html">Full contributors &amp; credits →</a>
    </div>
  </section>'''

    if old not in text:
        raise RuntimeError("Homepage community block not found")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def patch_contributors() -> None:
    path = ROOT / "docs/contributors.html"
    text = path.read_text(encoding="utf-8")

    needle = '<div class="card"><span class="role">1097 protocol &amp; country-profile research</span><strong>Stefan Allius</strong><p>Public TSUN GEN3 / 1097 protocol research from <a href="https://github.com/s-allius/tsun-gen3-proxy">tsun-gen3-proxy</a> helped inform the experimental 1097 adapter. His country/profile research also provided an important reference for interpreting and validating the inverter country-code/profile data.</p></div>\n'
    addition = needle + '<div class="card"><span class="role">02B0 / Solarman protocol cross-reference</span><strong>David Rapan · ha-solarman</strong><p>Public Home Assistant Solarman protocol and inverter-profile work from <a href="https://github.com/davidrapan/ha-solarman">ha-solarman</a> provided an independent cross-reference for selected 02B0 register semantics during TSUN Local research. TSUN Local keeps its own hardware-validation policy and does not assign unconfirmed meanings from a reference alone.</p></div>\n'

    if 'David Rapan · ha-solarman' not in text:
        if needle not in text:
            raise RuntimeError("Stefan contributor card not found")
        text = text.replace(needle, addition, 1)

    path.write_text(text, encoding="utf-8")


def main() -> None:
    patch_index()
    patch_contributors()


if __name__ == "__main__":
    main()
