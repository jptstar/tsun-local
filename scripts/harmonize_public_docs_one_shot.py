from pathlib import Path
import re

ROOT = Path(__file__).parents[1]
DOCS = ROOT / "docs"

SITE_CSS = ".site-actions{display:flex;flex-wrap:wrap;gap:10px;margin-top:24px;align-items:center}.site-action{display:inline-block;padding:12px 16px;border-radius:11px;text-decoration:none;font-weight:850;color:#fff;border:1px solid rgba(255,255,255,.28);background:rgba(255,255,255,.08)}.site-hacs{display:inline-flex;align-items:center}.site-hacs img{display:block;height:44px;width:auto;max-width:100%}"
SITE_ACTIONS = '<div class="site-actions"><a class="site-hacs" href="https://my.home-assistant.io/redirect/hacs_repository/?owner=jptstar&amp;repository=tsun-local&amp;category=integration"><img alt="Add TSUN Local to HACS" src="https://my.home-assistant.io/badges/hacs_repository.svg"></a><a class="site-action" href="https://github.com/jptstar/tsun-local">GitHub</a><a class="site-action" href="entities.html">Entity reference</a></div>'


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def add_site_css(text: str) -> str:
    if ".site-actions{" not in text:
        if "</style>" not in text:
            raise SystemExit("Missing </style> while adding shared site actions")
        text = text.replace("</style>", SITE_CSS + "\n  </style>", 1)
    return text


def replace_existing_hero_actions(filename: str) -> None:
    path = DOCS / filename
    text = add_site_css(read(path))
    text, count = re.subn(r'<div class="actions">.*?</div>', SITE_ACTIONS, text, count=1, flags=re.S)
    if count != 1:
        raise SystemExit(f"{filename}: expected one hero actions block")
    write(path, text)


def add_missing_hero_actions(filename: str) -> None:
    path = DOCS / filename
    text = add_site_css(read(path))
    if 'class="site-actions"' not in text:
        text, count = re.subn(
            r'(<div class="hero">.*)(</div>\s*</div>\s*</header>)',
            lambda m: m.group(1) + SITE_ACTIONS + m.group(2),
            text,
            count=1,
            flags=re.S,
        )
        if count != 1:
            raise SystemExit(f"{filename}: could not insert hero actions")
    write(path, text)


# Homepage hero is intentionally excluded.
for filename in (
    "sunology-play2.html",
    "tsol-mp3000-home-assistant.html",
    "tsol-mx500-home-assistant.html",
    "tsol-ms800-home-assistant.html",
    "tsol-ms2000-home-assistant.html",
):
    replace_existing_hero_actions(filename)

for filename in ("entities.html", "contributors.html", "test-your-inverter.html"):
    add_missing_hero_actions(filename)

# Homepage: keep the contributors-page link, remove the duplicated detailed catalogue.
index_path = DOCS / "index.html"
index = read(index_path)
compact_credit = '''<div class="community-credit">
      <strong>Community contributors &amp; research credits</strong>
      <span>Hardware validation and public research credits are maintained on the dedicated contributors page so the attribution stays current.</span>
      <a href="contributors.html">Full contributors &amp; credits →</a>
    </div>'''
index, count = re.subn(r'<div class="community-credit">.*?</div>', compact_credit, index, count=1, flags=re.S)
if count != 1:
    raise SystemExit("Homepage contributor block not found")
write(index_path, index)

# Contributors: separate direct hardware validation from public research references.
contributors_path = DOCS / "contributors.html"
contributors = read(contributors_path)
direct_and_research = '''<section><h2>Direct hardware contributors &amp; validation</h2><p class="intro">These contributors supplied real-device testing, diagnostics or hardware captures that directly validated TSUN Local behaviour.</p><div class="grid">
<div class="card"><span class="role">TSOL-MP3000 / 1511 hardware validation</span><a href="https://github.com/TheSmartGerman"><strong>@TheSmartGerman</strong></a><p>Tested TSUN Local on a real TSOL-MP3000 using the 1511 path and shared compatibility feedback. During that real-world test an additional 1097 protocol family was observed, which triggered further protocol investigation.</p></div>
<div class="card"><span class="role">Sunology PLAY2 / 02B0 hardware validation</span><a href="https://github.com/dca31"><strong>@dca31</strong></a><p>Validated a real Sunology PLAY2 through the normal TSUN Local Home Assistant flow, confirming automatic discovery and the supported local 02B0 path on independent hardware.</p></div>
<div class="card"><span class="role">Sunology PLAY2 GEN4 / 1097 field validation</span><a href="https://github.com/phildeg31"><strong>@phildeg31</strong></a><p>Shared real-hardware PLAY2 diagnostics for the GEN4 / 1097 path and is carrying out stability validation, including communication and daily-energy behaviour.</p></div>
<div class="card"><span class="role">TSOL-MS800 / 02B0 hardware validation</span><a href="https://github.com/Kmotr"><strong>@Kmotr</strong></a><p>Validated TSUN Local on a real TSOL-MS800, shared an anonymized Home Assistant diagnostic and confirmed the tested 02B0 path in normal use.</p></div>
<div class="card"><span class="role">TSOL-MS2000 &amp; TSOL-MP3000 hardware validation</span><a href="https://github.com/paloindici"><strong>@paloindici</strong></a><p>Validated a real TSOL-MS2000 with four PV inputs and shared anonymized diagnostics plus hardware dumps from both the MS2000 and MP3000. The MP3000 evidence helped confirm the TITAN / 1511 six-PV path and firmware/temperature behaviour on independent hardware.</p></div>
</div></section>
<section><h2>Public research references</h2><p class="intro">These projects were used as independent public research references. They are credited separately from TSUN Local hardware validation.</p><div class="grid">
<div class="card"><span class="role">1097 protocol &amp; country-profile research</span><strong>Stefan Allius</strong><p>Public TSUN GEN3 / 1097 protocol and country/profile research from <a href="https://github.com/s-allius/tsun-gen3-proxy">tsun-gen3-proxy</a> informed selected experimental 1097 investigations.</p></div>
<div class="card"><span class="role">02B0 / Solarman protocol cross-reference</span><strong>David Rapan · ha-solarman</strong><p>Public Home Assistant Solarman protocol and inverter-profile work from <a href="https://github.com/davidrapan/ha-solarman">ha-solarman</a> provided an independent cross-reference for selected 02B0 register semantics.</p></div>
</div></section>
'''
contributors, count = re.subn(
    r'<section><h2>Who contributed to what</h2>.*?(?=<section><h2>Testers and issue reporters</h2>)',
    direct_and_research,
    contributors,
    count=1,
    flags=re.S,
)
if count != 1:
    raise SystemExit("Contributors detail section not found")
write(contributors_path, contributors)

# MP3000: only actual MP3000 hardware contributors.
mp_path = DOCS / "tsol-mp3000-home-assistant.html"
mp = read(mp_path)
mp_validation = '''<section id="community-validation">
    <h2>Community validation</h2>
    <p class="intro">Real TSOL-MP3000 hardware contributions used directly to validate the TITAN / 1511 path.</p>
    <div class="grid">
      <div class="card"><strong><a href="https://github.com/TheSmartGerman">@TheSmartGerman</a></strong><span class="muted">Tested TSUN Local on a real TSOL-MP3000 using protocol 1511 and shared compatibility feedback from that installation.</span></div>
      <div class="card"><strong><a href="https://github.com/paloindici">@paloindici</a></strong><span class="muted">Shared anonymized Home Assistant diagnostics and a hardware dump from a real TSOL-MP3000, helping confirm the six-PV TITAN / 1511 path and firmware-dependent diagnostics.</span></div>
    </div>
  </section>'''
mp, count = re.subn(r'<section id="community-validation">.*?</section>', mp_validation, mp, count=1, flags=re.S)
if count != 1:
    raise SystemExit("MP3000 community validation section not found")
write(mp_path, mp)

# Entity reference: align 1097 with the current real PLAY2 GEN4 field evidence.
entities_path = DOCS / "entities.html"
entities = read(entities_path)
old_entity_row = '<tr><td><strong>1097</strong></td><td>GEN3 / GEN3 PLUS candidates</td><td>🧪 Experimental</td></tr>'
new_entity_row = '<tr><td><strong>1097</strong></td><td>Sunology PLAY2 · GEN4</td><td>🧪 Field validation</td></tr>'
if old_entity_row not in entities:
    raise SystemExit("entities.html: old 1097 row not found")
entities = entities.replace(old_entity_row, new_entity_row, 1)
write(entities_path, entities)

readmes = {
    "README.md": {
        "status": "🧪 **Field validation**",
        "play2": '''### Sunology PLAY2

Sunology PLAY2 is documented on two local hardware/protocol paths observed on real installations:

- **GEN3 Plus / 02B0 — validated:** automatic discovery and normal TSUN Local operation were confirmed independently by [@dca31](https://github.com/dca31).
- **GEN4 / 1097 — field validation:** real-hardware diagnostics and stability testing are provided by [@phildeg31](https://github.com/phildeg31).
- TSUN Local uses the local protocol exposed by the inverter/logger; no manual protocol selector or cloud connection is required.
- Monitoring remains read-only; no inverter configuration writes are implemented.

📚 **[PLAY2 compatibility page](https://jptstar.github.io/tsun-local/sunology-play2.html)**''',
        "credits": '''## Contributions & credits

Contributor, hardware-validation and public-research credits are maintained on the dedicated contributors page so they stay accurate as field validation evolves.

📚 **[Full contributors & credits](docs/contributors.html)**''',
    },
    "docs/README_FR.md": {
        "status": "🧪 **Validation terrain**",
        "play2": '''### Sunology PLAY2

Sunology PLAY2 est documenté sur deux chemins matériels/protocoles locaux observés sur des installations réelles :

- **GEN3 Plus / 02B0 — validé :** la découverte automatique et le fonctionnement normal de TSUN Local ont été confirmés indépendamment par [@dca31](https://github.com/dca31).
- **GEN4 / 1097 — validation terrain :** les diagnostics sur matériel réel et les tests de stabilité sont fournis par [@phildeg31](https://github.com/phildeg31).
- TSUN Local utilise le protocole local réellement exposé par l’onduleur/logger ; aucun sélecteur manuel de protocole ni connexion cloud n’est nécessaire.
- La surveillance reste en lecture seule ; aucune écriture de configuration de l’onduleur n’est implémentée.

📚 **[Page de compatibilité PLAY2](https://jptstar.github.io/tsun-local/sunology-play2.html)**''',
        "credits": '''## Contributions et crédits

Les contributions, validations matérielles et références de recherche publique sont centralisées sur la page dédiée afin de rester à jour au fil des validations terrain.

📚 **[Tous les contributeurs et crédits](contributors.html)**''',
    },
    "docs/README_DE.md": {
        "status": "🧪 **Feldvalidierung**",
        "play2": '''### Sunology PLAY2

Sunology PLAY2 ist auf zwei lokalen Hardware-/Protokollpfaden dokumentiert, die auf realen Installationen beobachtet wurden:

- **GEN3 Plus / 02B0 — validiert:** automatische Erkennung und normaler TSUN-Local-Betrieb wurden unabhängig von [@dca31](https://github.com/dca31) bestätigt.
- **GEN4 / 1097 — Feldvalidierung:** Real-Hardware-Diagnosen und Stabilitätstests werden von [@phildeg31](https://github.com/phildeg31) bereitgestellt.
- TSUN Local verwendet das lokal tatsächlich bereitgestellte Protokoll; keine manuelle Protokollauswahl und keine Cloud-Verbindung sind erforderlich.
- Die Überwachung bleibt schreibgeschützt; es werden keine Wechselrichter-Konfigurationsschreibvorgänge implementiert.

📚 **[PLAY2-Kompatibilitätsseite](https://jptstar.github.io/tsun-local/sunology-play2.html)**''',
        "credits": '''## Beiträge & Danksagungen

Beiträge, Hardware-Validierungen und öffentliche Forschungsreferenzen werden zentral auf der Contributor-Seite gepflegt, damit die Zuordnung aktuell bleibt.

📚 **[Alle Mitwirkenden & Danksagungen](contributors.html)**''',
    },
    "docs/README_NL.md": {
        "status": "🧪 **Veldvalidatie**",
        "play2": '''### Sunology PLAY2

Sunology PLAY2 is gedocumenteerd op twee lokale hardware-/protocolpaden die op echte installaties zijn waargenomen:

- **GEN3 Plus / 02B0 — gevalideerd:** automatische detectie en normaal TSUN Local-gebruik zijn onafhankelijk bevestigd door [@dca31](https://github.com/dca31).
- **GEN4 / 1097 — veldvalidatie:** real-hardwarediagnostiek en stabiliteitstests worden geleverd door [@phildeg31](https://github.com/phildeg31).
- TSUN Local gebruikt het lokale protocol dat de omvormer/logger werkelijk aanbiedt; geen handmatige protocolkeuze of cloudverbinding is nodig.
- Monitoring blijft alleen-lezen; er zijn geen configuratieschrijfbewerkingen voor de omvormer geïmplementeerd.

📚 **[PLAY2-compatibiliteitspagina](https://jptstar.github.io/tsun-local/sunology-play2.html)**''',
        "credits": '''## Bijdragen & credits

Bijdragen, hardwarevalidaties en openbare onderzoeksreferenties worden centraal bijgehouden op de contributor-pagina zodat de toeschrijving actueel blijft.

📚 **[Alle contributors & credits](contributors.html)**''',
    },
    "docs/README_IT.md": {
        "status": "🧪 **Validazione sul campo**",
        "play2": '''### Sunology PLAY2

Sunology PLAY2 è documentato su due percorsi hardware/protocollo locali osservati su installazioni reali:

- **GEN3 Plus / 02B0 — validato:** il rilevamento automatico e il normale funzionamento di TSUN Local sono stati confermati indipendentemente da [@dca31](https://github.com/dca31).
- **GEN4 / 1097 — validazione sul campo:** diagnostica su hardware reale e test di stabilità sono forniti da [@phildeg31](https://github.com/phildeg31).
- TSUN Local usa il protocollo locale realmente esposto da inverter/logger; non servono selettore manuale del protocollo né connessione cloud.
- Il monitoraggio resta in sola lettura; non sono implementate scritture di configurazione dell’inverter.

📚 **[Pagina compatibilità PLAY2](https://jptstar.github.io/tsun-local/sunology-play2.html)**''',
        "credits": '''## Contributi e crediti

Contributi, validazioni hardware e riferimenti di ricerca pubblica sono centralizzati nella pagina dedicata ai contributor per mantenere aggiornate le attribuzioni.

📚 **[Tutti i contributor e crediti](contributors.html)**''',
    },
    "docs/README_ES.md": {
        "status": "🧪 **Validación de campo**",
        "play2": '''### Sunology PLAY2

Sunology PLAY2 está documentado en dos rutas locales de hardware/protocolo observadas en instalaciones reales:

- **GEN3 Plus / 02B0 — validado:** la detección automática y el funcionamiento normal de TSUN Local fueron confirmados de forma independiente por [@dca31](https://github.com/dca31).
- **GEN4 / 1097 — validación de campo:** los diagnósticos en hardware real y las pruebas de estabilidad son aportados por [@phildeg31](https://github.com/phildeg31).
- TSUN Local usa el protocolo local que realmente expone el inversor/logger; no se necesita selector manual de protocolo ni conexión a la nube.
- La supervisión sigue siendo de solo lectura; no se implementan escrituras de configuración del inversor.

📚 **[Página de compatibilidad PLAY2](https://jptstar.github.io/tsun-local/sunology-play2.html)**''',
        "credits": '''## Contribuciones y créditos

Las contribuciones, validaciones de hardware y referencias de investigación pública se centralizan en la página de colaboradores para mantener las atribuciones actualizadas.

📚 **[Todos los colaboradores y créditos](contributors.html)**''',
    },
    "docs/README_PL.md": {
        "status": "🧪 **Walidacja terenowa**",
        "play2": '''### Sunology PLAY2

Sunology PLAY2 jest udokumentowany na dwóch lokalnych ścieżkach sprzęt/protokół zaobserwowanych w rzeczywistych instalacjach:

- **GEN3 Plus / 02B0 — zweryfikowany:** automatyczne wykrywanie i normalne działanie TSUN Local zostały niezależnie potwierdzone przez [@dca31](https://github.com/dca31).
- **GEN4 / 1097 — walidacja terenowa:** diagnostykę rzeczywistego sprzętu i testy stabilności dostarcza [@phildeg31](https://github.com/phildeg31).
- TSUN Local używa lokalnego protokołu faktycznie udostępnianego przez falownik/logger; ręczny wybór protokołu ani połączenie z chmurą nie są potrzebne.
- Monitorowanie pozostaje tylko do odczytu; nie zaimplementowano zapisów konfiguracji falownika.

📚 **[Strona zgodności PLAY2](https://jptstar.github.io/tsun-local/sunology-play2.html)**''',
        "credits": '''## Wkład i podziękowania

Wkład społeczności, walidacje sprzętowe i publiczne źródła badawcze są centralnie utrzymywane na stronie contributorów, aby przypisania pozostawały aktualne.

📚 **[Wszyscy contributorzy i podziękowania](contributors.html)**''',
    },
    "docs/README_ZH.md": {
        "status": "🧪 **现场验证**",
        "play2": '''### Sunology PLAY2

Sunology PLAY2 已记录两条在真实安装中观察到的本地硬件/协议路径：

- **GEN3 Plus / 02B0 — 已验证：** [@dca31](https://github.com/dca31) 独立确认了自动发现和 TSUN Local 的正常运行。
- **GEN4 / 1097 — 现场验证：** [@phildeg31](https://github.com/phildeg31) 提供真实硬件诊断并持续进行稳定性测试。
- TSUN Local 使用逆变器/logger 实际暴露的本地协议；无需手动选择协议，也无需云连接。
- 监控保持只读；不会向逆变器写入配置。

📚 **[PLAY2 兼容性页面](https://jptstar.github.io/tsun-local/sunology-play2.html)**''',
        "credits": '''## 贡献与致谢

贡献者、硬件验证和公开研究参考统一维护在专门的贡献者页面，以便随着现场验证持续保持准确。

📚 **[全部贡献者与致谢](contributors.html)**''',
    },
}

for filename, cfg in readmes.items():
    path = ROOT / filename
    text = read(path)
    text, count = re.subn(
        r'^\| \*\*1097\*\* \|.*$',
        f'| **1097** | GEN4 | **Sunology PLAY2** | {cfg["status"]} |',
        text,
        count=1,
        flags=re.M,
    )
    if count != 1:
        raise SystemExit(f"{filename}: 1097 compatibility row not found")

    text = re.sub(r'^- \*\*1097\b.*\n?', '', text, flags=re.M)
    text = re.sub(r'^\*\*[^*\n]*1\.6\.0[^*\n]*\*\*\s*', '', text, flags=re.M)

    play_start = text.find("### Sunology PLAY2")
    if play_start < 0:
        raise SystemExit(f"{filename}: Sunology PLAY2 section not found")
    play_end = text.find("\n---\n", play_start)
    if play_end < 0:
        raise SystemExit(f"{filename}: Sunology PLAY2 section end not found")
    text = text[:play_start] + cfg["play2"].strip() + "\n" + text[play_end:]

    credit_anchor = text.find("- **David Rapan")
    if credit_anchor < 0:
        raise SystemExit(f"{filename}: detailed credits anchor not found")
    credit_start = text.rfind("\n## ", 0, credit_anchor)
    credit_end = text.find("\n---\n", credit_anchor)
    if credit_start < 0 or credit_end < 0:
        raise SystemExit(f"{filename}: detailed credits block boundaries not found")
    text = text[:credit_start] + "\n" + cfg["credits"].strip() + "\n" + text[credit_end:]
    write(path, text)

# Web contract tests.
webtest_path = ROOT / "tests" / "test_release_154_web.py"
webtest = read(webtest_path)
webtest = webtest.replace(
    '        self.assertIn("paloindici", text)\n',
    '        self.assertNotIn("paloindici", text)\n        self.assertNotIn("TheSmartGerman", text)\n        self.assertNotIn("phildeg31", text)\n        self.assertNotIn("dca31", text)\n',
    1,
)
webtest = webtest.replace(
    '            "index.html",\n            "sunology-play2.html",',
    '            "index.html",\n            "entities.html",\n            "contributors.html",\n            "test-your-inverter.html",\n            "sunology-play2.html",',
    1,
)
insert = '''
    def test_non_home_pages_share_three_global_actions(self) -> None:
        for filename in PAGES:
            text = (DOCS / filename).read_text(encoding="utf-8")
            if filename == "index.html":
                self.assertNotIn('class="site-actions"', text)
                continue
            match = re.search(r'<div class="site-actions">(.*?)</div>', text, flags=re.S)
            self.assertIsNotNone(match, filename)
            actions = match.group(1)
            self.assertIn("https://my.home-assistant.io/badges/hacs_repository.svg", actions, filename)
            self.assertIn('href="https://github.com/jptstar/tsun-local">GitHub</a>', actions, filename)
            self.assertIn('href="entities.html">Entity reference</a>', actions, filename)
            self.assertEqual(actions.count('class="site-action"'), 2, filename)

    def test_mp3000_community_validation_lists_only_real_contributors(self) -> None:
        text = (DOCS / "tsol-mp3000-home-assistant.html").read_text(encoding="utf-8")
        section = re.search(r'<section id="community-validation">(.*?)</section>', text, flags=re.S)
        self.assertIsNotNone(section)
        body = section.group(1)
        self.assertIn("TheSmartGerman", body)
        self.assertIn("paloindici", body)
        self.assertNotIn("Stefan", body)
        self.assertNotIn("Open field validation", body)

'''
marker = '    def test_hardware_test_page_promotes_current_diagnostic(self) -> None:\n'
if "test_non_home_pages_share_three_global_actions" not in webtest:
    if marker not in webtest:
        raise SystemExit("Web test insertion marker not found")
    webtest = webtest.replace(marker, insert + marker, 1)
write(webtest_path, webtest)

localized_test_path = ROOT / "tests" / "test_stable_151_localized_readmes.py"
localized_test = read(localized_test_path)
localized_test = localized_test.replace(
    '            self.assertEqual(text.count("| **1097** | GEN3 / GEN3 PLUS |"), 1, filename)\n',
    '            self.assertEqual(text.count("| **1097** | GEN4 | **Sunology PLAY2** |"), 1, filename)\n',
    1,
)
localized_test = localized_test.replace(
    '            self.assertIn("ha-solarman", text, filename)\n            self.assertIn("dca31", text, filename)\n            self.assertIn("paloindici", text, filename)\n',
    '            self.assertIn("dca31", text, filename)\n            self.assertIn("phildeg31", text, filename)\n            self.assertIn("contributors.html", text, filename)\n            self.assertNotIn("- **Stefan Allius", text, filename)\n            self.assertNotIn("- **David Rapan", text, filename)\n            self.assertNotIn("- **1097", text, filename)\n',
    1,
)
write(localized_test_path, localized_test)

# Final assertions.
homepage = read(DOCS / "index.html")
assert "contributors.html" in homepage
for name in ("TheSmartGerman", "phildeg31", "paloindici", "dca31", "Kmotr"):
    assert name not in homepage, name

mp = read(mp_path)
mp_section = re.search(r'<section id="community-validation">(.*?)</section>', mp, flags=re.S).group(1)
assert "TheSmartGerman" in mp_section and "paloindici" in mp_section
assert "Stefan" not in mp_section and "Open field validation" not in mp_section

for filename in (
    "entities.html",
    "contributors.html",
    "test-your-inverter.html",
    "sunology-play2.html",
    "tsol-mp3000-home-assistant.html",
    "tsol-mx500-home-assistant.html",
    "tsol-ms800-home-assistant.html",
    "tsol-ms2000-home-assistant.html",
):
    page = read(DOCS / filename)
    assert page.count('class="site-actions"') == 1, filename
    assert "badges/hacs_repository.svg" in page, filename

for filename in readmes:
    text = read(ROOT / filename)
    assert "| **1097** | GEN4 | **Sunology PLAY2** |" in text, filename
    assert "phildeg31" in text, filename
    assert "contributors.html" in text, filename
