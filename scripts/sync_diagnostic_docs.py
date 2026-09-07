#!/usr/bin/env python3
"""Keep public diagnostic documentation aligned with the shared desktop build.

This script intentionally edits existing documentation paths in place. Old forum,
issue and website links therefore keep working while the content evolves from the
historical Windows-only diagnostic to the shared Windows/macOS/Linux application.
"""

from __future__ import annotations

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"

WINDOWS = "https://github.com/jptstar/tsun-local/releases/download/diagnostic-latest/TSUN-Local-Diagnostic.exe"
MAC_ARM = "https://github.com/jptstar/tsun-local/releases/download/diagnostic-latest/TSUN-Local-Diagnostic-macOS-arm64.zip"
MAC_INTEL = "https://github.com/jptstar/tsun-local/releases/download/diagnostic-latest/TSUN-Local-Diagnostic-macOS-x86_64.zip"
LINUX_X64 = "https://github.com/jptstar/tsun-local/releases/download/diagnostic-latest/TSUN-Local-Diagnostic-Linux-x86_64"
LINUX_ARM = "https://github.com/jptstar/tsun-local/releases/download/diagnostic-latest/TSUN-Local-Diagnostic-Linux-arm64"
RELEASE = "https://github.com/jptstar/tsun-local/releases/tag/diagnostic-latest"
DUMPER = "https://github.com/jptstar/tsun-local/releases/download/diagnostic-latest/tsun_dump.py"


def version_from(path: Path, variable: str) -> str:
    text = path.read_text(encoding="utf-8")
    match = re.search(rf'^\s*{re.escape(variable)}\s*=\s*["\']([^"\']+)["\']', text, re.MULTILINE)
    if not match:
        raise RuntimeError(f"Unable to read {variable} from {path}")
    return match.group(1)


GUI_VERSION = version_from(ROOT / "tools" / "tsun_diagnostic.py", "APP_VERSION")
DUMP_VERSION = version_from(ROOT / "tools" / "tsun_dump.py", "TOOL_VERSION")


def replace_once(path: Path, pattern: str, replacement: str, *, flags: int = 0) -> None:
    text = path.read_text(encoding="utf-8")
    updated, count = re.subn(pattern, replacement, text, count=1, flags=flags)
    if count != 1:
        raise RuntimeError(f"Expected one replacement in {path}, found {count}: {pattern[:80]}")
    if updated != text:
        path.write_text(updated, encoding="utf-8")


def download_table(labels: tuple[str, str, str]) -> str:
    platform_label, download_label, checksum_label = labels
    return f"""| {platform_label} | {download_label} | {checksum_label} |
|---|---|---|
| Windows x86_64 | [TSUN-Local-Diagnostic.exe]({WINDOWS}) | [SHA-256]({WINDOWS}.sha256) |
| macOS Apple Silicon | [TSUN-Local-Diagnostic-macOS-arm64.zip]({MAC_ARM}) | [SHA-256]({MAC_ARM}.sha256) |
| macOS Intel | [TSUN-Local-Diagnostic-macOS-x86_64.zip]({MAC_INTEL}) | [SHA-256]({MAC_INTEL}.sha256) |
| Linux x86_64 | [TSUN-Local-Diagnostic-Linux-x86_64]({LINUX_X64}) | [SHA-256]({LINUX_X64}.sha256) |
| Linux arm64 | [TSUN-Local-Diagnostic-Linux-arm64]({LINUX_ARM}) | [SHA-256]({LINUX_ARM}.sha256) |"""


LOCALIZED = {
    "README_FR.md": f"""### Application de bureau — Windows, macOS et Linux

La **même interface TSUN Local Diagnostic** est maintenant disponible sur Windows, macOS et Linux. Tous les paquets utilisent le même moteur matériel **strictement en lecture seule**.

{download_table(("Plateforme", "Téléchargement", "Contrôle"))}

Versions actuelles : interface **{GUI_VERSION}** · moteur de dump **{DUMP_VERSION}**.

Le lien Windows historique reste volontairement inchangé afin que les anciens messages et tutoriels continuent de fonctionner.

Le parcours est identique sur les trois systèmes : **1 → 2 → 3 → 4**.

1. **Désactiver TSUN Local** pour le logger concerné.
2. **Lancer le diagnostic**.
3. **Envoi direct du rapport** — recommandé, avec consentement explicite obligatoire.
4. **Envoi manuel par e-mail** — optionnel, uniquement en secours.

Le nom/pseudonyme et jusqu’à 10 modèles de micro-onduleurs avec leurs quantités peuvent être mémorisés localement et restent modifiables. Le consentement n’est jamais mémorisé. Après un envoi réussi, l’application affiche l’identifiant `TSL-...` et un lien sécurisé permettant au testeur de voir exactement le rapport anonymisé envoyé, sans accès au dépôt privé.

Test hors domicile : utilisez exactement `89:89:89:89` comme IP logger et `89898989` comme Monitor SN. Ce mode est explicitement synthétique et ne contacte aucun appareil.

Sous macOS, l’application est signée de manière ad hoc mais pas encore notarifiée Apple : au premier lancement, Finder → clic droit → **Ouvrir** peut être nécessaire. Sous Linux, le fichier téléchargé peut nécessiter `chmod +x` une fois.

**[Release diagnostic stable]({RELEASE})** · 📋 **[Protocole de validation](DIRECT_DIAGNOSTIC_UPLOAD_TEST.md)** · 📚 **[Guide du diagnostic matériel](HARDWARE_DUMP.md)**

### Alternative Python / ligne de commande

[`tsun_dump.py`]({DUMPER}) reste disponible pour Python 3.10+ et les utilisateurs avancés :

```bash
python3 tsun_dump.py --full
```

Sous Windows, `py tsun_dump.py --full` reste également pris en charge.

""",
    "README_DE.md": f"""### Desktop-App — Windows, macOS und Linux

Die **gleiche TSUN Local Diagnostic-Oberfläche** steht jetzt für Windows, macOS und Linux zur Verfügung. Alle Pakete verwenden dieselbe **streng schreibgeschützte** Hardware-Diagnoseengine.

{download_table(("Plattform", "Download", "Prüfsumme"))}

Aktuelle Versionen: GUI **{GUI_VERSION}** · Dump-Engine **{DUMP_VERSION}**.

Der bisherige Windows-Link bleibt absichtlich unverändert, damit ältere Forenbeiträge und Anleitungen weiterhin funktionieren.

Der Ablauf ist auf allen Plattformen identisch: **1 → 2 → 3 → 4**.

1. Betroffenen **TSUN Local-Eintrag deaktivieren**.
2. **Diagnose starten**.
3. **Direkter Bericht-Upload** — empfohlen, nur nach ausdrücklicher Zustimmung.
4. **Manueller E-Mail-Versand** — optionaler Fallback.

Name/Pseudonym sowie bis zu 10 Mikro-Wechselrichtermodelle mit Mengen können lokal gespeichert und später geändert werden. Die Zustimmung wird niemals gespeichert. Nach erfolgreichem Upload zeigt die App die `TSL-...`-ID und einen sicheren Link, über den der Tester genau den gesendeten anonymisierten Bericht sehen kann, ohne Zugriff auf das private Repository.

Test außerhalb des Standorts: Logger-IP `89:89:89:89` und Monitor SN `89898989`. Dieser Modus ist ausdrücklich synthetisch und kontaktiert keine Hardware.

macOS ist derzeit ad-hoc signiert, aber noch nicht von Apple notarisiert; beim ersten Start kann Finder → Rechtsklick → **Öffnen** nötig sein. Unter Linux kann einmalig `chmod +x` erforderlich sein.

**[Stabile Diagnostic-Release]({RELEASE})** · **[Validierungsprotokoll](DIRECT_DIAGNOSTIC_UPLOAD_TEST.md)** · **[Hardware-Diagnosehandbuch](HARDWARE_DUMP.md)**

### Python-/Kommandozeilen-Alternative

[`tsun_dump.py`]({DUMPER}) bleibt für Python 3.10+ und fortgeschrittene Anwender verfügbar:

```bash
python3 tsun_dump.py --full
```

""",
    "README_NL.md": f"""### Desktop-app — Windows, macOS en Linux

De **zelfde TSUN Local Diagnostic-interface** is nu beschikbaar voor Windows, macOS en Linux. Alle pakketten gebruiken dezelfde **strikt alleen-lezen** hardware-engine.

{download_table(("Platform", "Download", "Controle"))}

Huidige versies: GUI **{GUI_VERSION}** · dump-engine **{DUMP_VERSION}**.

De bestaande Windows-link blijft bewust ongewijzigd zodat oudere forum- en documentatielinks blijven werken.

De workflow is overal hetzelfde: **1 → 2 → 3 → 4**.

1. De betreffende **TSUN Local-configuratie uitschakelen**.
2. **Diagnose uitvoeren**.
3. **Rapport direct uploaden** — aanbevolen, alleen na expliciete toestemming.
4. **Handmatig per e-mail** — optionele fallback.

Naam/pseudoniem en maximaal 10 micro-omvormermodellen met aantallen kunnen lokaal worden bewaard en later gewijzigd. Toestemming wordt nooit opgeslagen. Na upload toont de app de `TSL-...`-ID en een beveiligde link waarmee de tester exact het verzonden geanonimiseerde rapport kan bekijken zonder toegang tot de private repository.

Test buiten de installatie: logger-IP `89:89:89:89` en Monitor SN `89898989`. Deze modus is expliciet synthetisch en benadert geen hardware.

macOS is momenteel ad-hoc ondertekend maar nog niet door Apple genotariseerd; bij de eerste start kan Finder → rechtsklik → **Open** nodig zijn. Linux kan eenmalig `chmod +x` vereisen.

**[Stabiele diagnostic-release]({RELEASE})** · **[Validatieprotocol](DIRECT_DIAGNOSTIC_UPLOAD_TEST.md)** · **[Hardwarediagnose](HARDWARE_DUMP.md)**

### Python / commandoregel

[`tsun_dump.py`]({DUMPER}) blijft beschikbaar voor Python 3.10+ en gevorderde gebruikers:

```bash
python3 tsun_dump.py --full
```

""",
    "README_IT.md": f"""### App desktop — Windows, macOS e Linux

La **stessa interfaccia TSUN Local Diagnostic** è ora disponibile per Windows, macOS e Linux. Tutti i pacchetti usano lo stesso motore hardware **rigorosamente in sola lettura**.

{download_table(("Piattaforma", "Download", "Checksum"))}

Versioni correnti: GUI **{GUI_VERSION}** · motore dump **{DUMP_VERSION}**.

Il link Windows storico resta intenzionalmente invariato per mantenere validi i vecchi post e tutorial.

Il flusso è identico su tutte le piattaforme: **1 → 2 → 3 → 4**.

1. **Disattivare TSUN Local** per il logger interessato.
2. **Eseguire la diagnostica**.
3. **Invio diretto del report** — consigliato, solo dopo consenso esplicito.
4. **Invio manuale via e-mail** — fallback opzionale.

Nome/pseudonimo e fino a 10 modelli di microinverter con quantità possono essere memorizzati localmente e modificati in seguito. Il consenso non viene mai memorizzato. Dopo l'upload l'app mostra l'ID `TSL-...` e un link sicuro per vedere esattamente il report anonimizzato inviato, senza accesso al repository privato.

Test fuori sede: IP logger `89:89:89:89` e Monitor SN `89898989`. La modalità è esplicitamente sintetica e non contatta hardware reale.

Su macOS l'app è firmata ad hoc ma non ancora notarizzata Apple; al primo avvio può essere necessario Finder → clic destro → **Apri**. Su Linux può servire una volta `chmod +x`.

**[Release diagnostica stabile]({RELEASE})** · **[Protocollo di validazione](DIRECT_DIAGNOSTIC_UPLOAD_TEST.md)** · **[Guida hardware](HARDWARE_DUMP.md)**

### Alternativa Python / riga di comando

[`tsun_dump.py`]({DUMPER}) resta disponibile per Python 3.10+ e utenti avanzati:

```bash
python3 tsun_dump.py --full
```

""",
    "README_ES.md": f"""### Aplicación de escritorio — Windows, macOS y Linux

La **misma interfaz TSUN Local Diagnostic** está ahora disponible para Windows, macOS y Linux. Todos los paquetes utilizan el mismo motor de hardware **estrictamente de solo lectura**.

{download_table(("Plataforma", "Descarga", "Checksum"))}

Versiones actuales: GUI **{GUI_VERSION}** · motor de dump **{DUMP_VERSION}**.

El enlace histórico de Windows se mantiene intencionadamente sin cambios para que los mensajes y tutoriales antiguos sigan funcionando.

El flujo es idéntico en todas las plataformas: **1 → 2 → 3 → 4**.

1. **Desactivar TSUN Local** para el logger afectado.
2. **Ejecutar el diagnóstico**.
3. **Envío directo del informe** — recomendado, solo con consentimiento explícito.
4. **Envío manual por correo** — alternativa opcional.

El nombre/seudónimo y hasta 10 modelos de microinversor con cantidades pueden guardarse localmente y modificarse después. El consentimiento nunca se guarda. Tras el envío, la aplicación muestra el ID `TSL-...` y un enlace seguro para ver exactamente el informe anonimizado enviado, sin acceso al repositorio privado.

Prueba fuera de la instalación: IP del logger `89:89:89:89` y Monitor SN `89898989`. Este modo es explícitamente sintético y no contacta ningún dispositivo real.

En macOS la app está firmada ad hoc pero todavía no está notarizada por Apple; en el primer inicio puede ser necesario Finder → clic derecho → **Abrir**. En Linux puede ser necesario ejecutar `chmod +x` una vez.

**[Release de diagnóstico estable]({RELEASE})** · **[Protocolo de validación](DIRECT_DIAGNOSTIC_UPLOAD_TEST.md)** · **[Guía de hardware](HARDWARE_DUMP.md)**

### Alternativa Python / línea de comandos

[`tsun_dump.py`]({DUMPER}) sigue disponible para Python 3.10+ y usuarios avanzados:

```bash
python3 tsun_dump.py --full
```

""",
    "README_PL.md": f"""### Aplikacja desktopowa — Windows, macOS i Linux

Ta **sama aplikacja TSUN Local Diagnostic** jest teraz dostępna dla Windows, macOS i Linux. Wszystkie pakiety używają tego samego, **ściśle tylko do odczytu**, silnika diagnostycznego.

{download_table(("Platforma", "Pobieranie", "Suma kontrolna"))}

Aktualne wersje: GUI **{GUI_VERSION}** · silnik dump **{DUMP_VERSION}**.

Dotychczasowy link Windows pozostaje celowo bez zmian, aby starsze posty i poradniki nadal działały.

Przebieg jest identyczny na wszystkich platformach: **1 → 2 → 3 → 4**.

1. **Wyłącz TSUN Local** dla testowanego loggera.
2. **Uruchom diagnostykę**.
3. **Bezpośrednie wysłanie raportu** — zalecane, tylko po wyraźnej zgodzie.
4. **Ręczne wysłanie e-mailem** — opcjonalna metoda awaryjna.

Nazwa/pseudonim oraz do 10 modeli mikroinwerterów z ilościami mogą być zapisane lokalnie i później zmienione. Zgoda nigdy nie jest zapisywana. Po wysłaniu aplikacja pokazuje ID `TSL-...` oraz bezpieczny link do dokładnie tego anonimowego raportu, bez dostępu do prywatnego repozytorium.

Test poza instalacją: IP loggera `89:89:89:89` i Monitor SN `89898989`. Ten tryb jest jawnie syntetyczny i nie łączy się z żadnym urządzeniem.

Na macOS aplikacja jest obecnie podpisana ad hoc, ale jeszcze nienotaryzowana przez Apple; przy pierwszym uruchomieniu może być potrzebne Finder → prawy klik → **Open**. Na Linux może być potrzebne jednorazowe `chmod +x`.

**[Stabilne wydanie diagnostyczne]({RELEASE})** · **[Protokół walidacji](DIRECT_DIAGNOSTIC_UPLOAD_TEST.md)** · **[Przewodnik sprzętowy](HARDWARE_DUMP.md)**

### Alternatywa Python / wiersz poleceń

[`tsun_dump.py`]({DUMPER}) pozostaje dostępny dla Python 3.10+ i zaawansowanych użytkowników:

```bash
python3 tsun_dump.py --full
```

""",
    "README_ZH.md": f"""### 桌面应用 — Windows、macOS 和 Linux

现在 Windows、macOS 和 Linux 都提供**同一套 TSUN Local Diagnostic 界面**。所有安装包都使用同一个**严格只读**的硬件诊断引擎。

{download_table(("平台", "下载", "SHA-256"))}

当前版本：桌面 GUI **{GUI_VERSION}** · dump 引擎 **{DUMP_VERSION}**。

历史 Windows 下载链接刻意保持不变，因此旧论坛帖子和教程中的链接仍然有效。

所有平台都使用相同的 **1 → 2 → 3 → 4** 流程：

1. 为目标 logger **禁用 TSUN Local**。
2. **运行诊断**。
3. **直接上传报告** — 推荐，仅在明确同意后执行。
4. **手动邮件发送** — 仅作为可选备用方式。

用户名/昵称以及最多 10 种微型逆变器型号和数量可以保存在本机并随时修改；上传同意状态**永远不会保存**。上传成功后，应用会显示 `TSL-...` ID 和一个安全链接，让测试者查看自己实际发送的匿名报告，而不会获得私有报告仓库的访问权限。

离线地点测试：logger IP 使用 `89:89:89:89`，Monitor SN 使用 `89898989`。该模式会明确标记为合成测试，并且不会连接任何真实设备。

macOS 应用目前采用 ad-hoc 签名但尚未经过 Apple notarization；首次启动时可能需要 Finder → 右键 → **打开**。Linux 下载后可能需要执行一次 `chmod +x`。

**[稳定诊断发行版]({RELEASE})** · **[验证协议](DIRECT_DIAGNOSTIC_UPLOAD_TEST.md)** · **[硬件诊断指南](HARDWARE_DUMP.md)**

### Python / 命令行备用方式

[`tsun_dump.py`]({DUMPER}) 仍可供 Python 3.10+ 和高级用户使用：

```bash
python3 tsun_dump.py --full
```

""",
}


def sync_localized_readmes() -> None:
    pattern = r"^### Windows[^\n]*\n.*?(?=^### Sunology PLAY2\s*$)"
    for filename, replacement in LOCALIZED.items():
        replace_once(DOCS / filename, pattern, replacement, flags=re.MULTILINE | re.DOTALL)


def sync_hardware_dump() -> None:
    path = DOCS / "HARDWARE_DUMP.md"
    table = download_table(("Platform", "Download", "SHA-256"))
    replacement = f"""## ⬇️ Choose the easiest diagnostic

### Desktop application — Windows, macOS and Linux (recommended)

The **same TSUN Local Diagnostic interface** is packaged for all supported desktop platforms. Every package uses the same privacy-safe, **strictly read-only** `tsun_dump.py` hardware engine; direct report upload is a separate HTTPS action performed only after explicit consent.

{table}

Current standalone diagnostic versions: **desktop GUI {GUI_VERSION}** · **dump engine {DUMP_VERSION}**.

All assets remain on the rolling **`diagnostic-latest`** release. The historical Windows URL and filename are intentionally unchanged so old forum posts, issue comments and documentation links stay valid.

The standard desktop flow is the same everywhere: **1 → 2 → 3 → 4**.

1. reproduce the problem and **do not reload TSUN Local first**;
2. download the Home Assistant diagnostic when possible;
3. **disable the affected TSUN Local config entry** so it does not compete for the logger connection;
4. launch the desktop diagnostic for the current operating system and run the capture;
5. use **step 3 direct upload** after reviewing the explicit consent, or **step 4 manual e-mail** only as fallback;
6. re-enable TSUN Local when the capture is finished.

The direct-upload UI can remember the tester name/pseudonym and up to 10 selected micro-inverter models/quantities across application updates. The consent checkbox is never persisted. A successful upload returns a `TSL-...` receipt plus a private-token Worker link that lets the tester see exactly the anonymized report sent without exposing the private reports repository.

For an upload-only test away from the installation, enter exactly:

```text
Logger IP : 89:89:89:89
Monitor SN: 89898989
```

This dedicated synthetic mode explicitly records `test_mode: true` and `communication_attempted: false`; no logger or micro-inverter is contacted.

Update behavior is platform-specific only at package-replacement level: Windows keeps verified in-place self-update; macOS/Linux check their own architecture-specific package in the same manifest and report when a replacement is available. Saved tester profiles live outside the executable/app bundle and survive replacement.

macOS packages are currently ad-hoc signed but not Apple-notarized. If Gatekeeper blocks first launch, use Finder → right-click **TSUN Local Diagnostic** → **Open**. Linux downloads are portable executables and may need `chmod +x` once after download.

📋 **[Cross-platform desktop/direct-upload validation protocol](DIRECT_DIAGNOSTIC_UPLOAD_TEST.md)**

"""
    replace_once(
        path,
        r"^## ⬇️ Choose the easiest diagnostic\n.*?(?=^### Firmware-resilient logger web capture)",
        replacement,
        flags=re.MULTILINE | re.DOTALL,
    )
    replace_once(
        path,
        r"^### Python script — macOS, Linux and advanced users$",
        "### Python / command-line alternative — all platforms",
        flags=re.MULTILINE,
    )
    replace_once(
        path,
        r"\*\*\[Download `tsun_dump\.py`\]\(https://raw\.githubusercontent\.com/jptstar/tsun-local/main/tools/tsun_dump\.py\)\*\*",
        f"**[Download `tsun_dump.py`]({DUMPER})**",
    )


def sync_homepage() -> None:
    path = DOCS / "index.html"
    old = r'''\s*<a class="card" style="display:block;color:inherit;text-decoration:none" href="https://github\.com/jptstar/tsun-local/releases/download/diagnostic-latest/TSUN-Local-Diagnostic\.exe"><strong>Windows diagnostic →</strong><span class="muted">.*?</span></a>'''
    new = f'''
      <a class="card" style="display:block;color:inherit;text-decoration:none" href="{WINDOWS}"><strong>Windows diagnostic →</strong><span class="muted">Stable historical download link. Same 1 → 2 → 3 → 4 read-only desktop interface, direct report upload and anonymized JSON flow.</span></a>
      <a class="card" style="display:block;color:inherit;text-decoration:none" href="test-your-inverter.html"><strong>macOS &amp; Linux diagnostic →</strong><span class="muted">The same TSUN Local Diagnostic interface is now packaged for Apple Silicon, Intel, Linux x86_64 and Linux arm64.</span></a>'''
    replace_once(path, old, new, flags=re.DOTALL)


def main() -> None:
    sync_localized_readmes()
    sync_hardware_dump()
    sync_homepage()
    print(f"Diagnostic documentation synchronized: GUI {GUI_VERSION}, dump {DUMP_VERSION}")


if __name__ == "__main__":
    main()
