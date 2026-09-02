#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

DESCRIPTIONS = {
    "strings.json": (
        "Configure polling for this micro-inverter. If Adaptive polling is disabled, "
        "the intervals below keep the usual fixed behavior. If it is enabled, they "
        "become the limits used by the algorithm: the normal interval is the regular "
        "cadence, the error interval sets the first retry delay without going below "
        "the normal cadence, and the offline/night interval is applied as soon as the "
        "configured consecutive-failure threshold is reached. Between these limits, "
        "TSUN Local automatically builds progressive backoff steps. As soon as a poll "
        "succeeds again, the micro-inverter is marked online immediately and the "
        "interval progressively returns to normal. Changing the intervals or the "
        "failure threshold therefore changes the adaptive steps automatically. Wi-Fi "
        "signal is diagnostic only and never changes the polling cadence by itself."
    ),
    "en.json": (
        "Configure polling for this micro-inverter. If Adaptive polling is disabled, "
        "the intervals below keep the usual fixed behavior. If it is enabled, they "
        "become the limits used by the algorithm: the normal interval is the regular "
        "cadence, the error interval sets the first retry delay without going below "
        "the normal cadence, and the offline/night interval is applied as soon as the "
        "configured consecutive-failure threshold is reached. Between these limits, "
        "TSUN Local automatically builds progressive backoff steps. As soon as a poll "
        "succeeds again, the micro-inverter is marked online immediately and the "
        "interval progressively returns to normal. Changing the intervals or the "
        "failure threshold therefore changes the adaptive steps automatically. Wi-Fi "
        "signal is diagnostic only and never changes the polling cadence by itself."
    ),
    "fr.json": (
        "Réglez l’interrogation de ce micro-onduleur. Si l’interrogation adaptative est "
        "désactivée, les intervalles ci-dessous gardent le comportement fixe habituel. "
        "Si elle est activée, ils servent de limites à l’algorithme : l’intervalle "
        "normal est la cadence habituelle, l’intervalle après erreur fixe le premier "
        "délai de nouvelle tentative sans descendre sous la cadence normale, et "
        "l’intervalle hors ligne/nuit est appliqué dès que le seuil configuré d’échecs "
        "consécutifs est atteint. Entre ces limites, TSUN Local calcule automatiquement "
        "des paliers progressifs. Dès qu’une lecture réussit de nouveau, le micro-onduleur "
        "repasse immédiatement en ligne puis l’intervalle revient progressivement à la "
        "normale. Modifier les intervalles ou le seuil modifie donc automatiquement les "
        "paliers adaptatifs. Le signal Wi-Fi reste uniquement diagnostique et ne change "
        "jamais la cadence à lui seul."
    ),
    "de.json": (
        "Legen Sie das Abfrageverhalten dieses Mikro-Wechselrichters fest. Ist die "
        "adaptive Abfrage deaktiviert, behalten die folgenden Intervalle das gewohnte "
        "feste Verhalten. Ist sie aktiviert, dienen sie als Grenzen des Algorithmus: "
        "Das normale Intervall ist der übliche Takt, das Fehlerintervall legt die erste "
        "Wiederholungsverzögerung fest, ohne den normalen Takt zu unterschreiten, und "
        "das Offline-/Nachtintervall wird angewendet, sobald die konfigurierte Schwelle "
        "aufeinanderfolgender Fehler erreicht ist. Dazwischen berechnet TSUN Local "
        "automatisch progressive Backoff-Stufen. Sobald eine Abfrage wieder erfolgreich "
        "ist, wird der Mikro-Wechselrichter sofort als online markiert und das Intervall "
        "schrittweise auf normal zurückgeführt. Änderungen an Intervallen oder Schwelle "
        "ändern somit automatisch die adaptiven Stufen. Das WLAN-Signal dient nur der "
        "Diagnose und verändert den Abfragetakt niemals allein."
    ),
    "es.json": (
        "Configure el sondeo de este microinversor. Si el sondeo adaptativo está "
        "desactivado, los intervalos siguientes mantienen el comportamiento fijo habitual. "
        "Si está activado, pasan a ser los límites del algoritmo: el intervalo normal es "
        "la cadencia habitual, el intervalo tras error fija el primer reintento sin bajar "
        "de la cadencia normal y el intervalo sin conexión/nocturno se aplica en cuanto "
        "se alcanza el umbral configurado de fallos consecutivos. Entre estos límites, "
        "TSUN Local calcula automáticamente pasos progresivos de espera. En cuanto una "
        "lectura vuelve a tener éxito, el microinversor se marca inmediatamente como en "
        "línea y el intervalo vuelve progresivamente a la normalidad. Cambiar los "
        "intervalos o el umbral cambia automáticamente los pasos adaptativos. La señal "
        "Wi-Fi es solo diagnóstica y nunca modifica por sí sola la cadencia de sondeo."
    ),
    "it.json": (
        "Configura l’interrogazione di questo microinverter. Se l’interrogazione adattiva "
        "è disattivata, gli intervalli seguenti mantengono il normale comportamento fisso. "
        "Se è attivata, diventano i limiti usati dall’algoritmo: l’intervallo normale è la "
        "cadenza abituale, l’intervallo dopo errore imposta il primo tentativo senza scendere "
        "sotto la cadenza normale e l’intervallo offline/notte viene applicato non appena "
        "si raggiunge la soglia configurata di errori consecutivi. Tra questi limiti, "
        "TSUN Local calcola automaticamente livelli progressivi di backoff. Appena una "
        "lettura riesce di nuovo, il microinverter viene marcato immediatamente online e "
        "l’intervallo torna progressivamente alla normalità. Modificare intervalli o soglia "
        "modifica quindi automaticamente i livelli adattivi. Il segnale Wi-Fi è solo "
        "diagnostico e non modifica mai da solo la cadenza di interrogazione."
    ),
    "nl.json": (
        "Stel het pollinggedrag van deze micro-omvormer in. Als Adaptieve polling is "
        "uitgeschakeld, behouden de onderstaande intervallen het gebruikelijke vaste gedrag. "
        "Als het is ingeschakeld, vormen ze de grenzen voor het algoritme: het normale "
        "interval is het gebruikelijke tempo, het foutinterval bepaalt de eerste nieuwe "
        "poging zonder onder het normale tempo te komen en het offline-/nachtinterval wordt "
        "toegepast zodra de ingestelde drempel voor opeenvolgende fouten is bereikt. Tussen "
        "deze grenzen berekent TSUN Local automatisch oplopende backoff-stappen. Zodra een "
        "poll opnieuw slaagt, wordt de micro-omvormer onmiddellijk online gemarkeerd en keert "
        "het interval stapsgewijs terug naar normaal. Wijzigingen aan intervallen of drempel "
        "wijzigen dus automatisch de adaptieve stappen. Het wifi-signaal is alleen voor "
        "diagnose en verandert nooit zelfstandig het pollingtempo."
    ),
    "pl.json": (
        "Skonfiguruj odpytywanie tego mikrofalownika. Gdy adaptacyjne odpytywanie jest "
        "wyłączone, poniższe interwały zachowują dotychczasowe stałe działanie. Po włączeniu "
        "stają się granicami algorytmu: interwał normalny jest zwykłą częstotliwością, "
        "interwał po błędzie określa pierwszą ponowną próbę bez zejścia poniżej interwału "
        "normalnego, a interwał offline/noc jest stosowany natychmiast po osiągnięciu "
        "ustawionego progu kolejnych błędów. Pomiędzy tymi granicami TSUN Local automatycznie "
        "wylicza stopniowe poziomy backoff. Gdy odczyt ponownie się powiedzie, mikrofalownik "
        "jest natychmiast oznaczany jako online, a interwał stopniowo wraca do normalnego. "
        "Zmiana interwałów lub progu automatycznie zmienia więc poziomy adaptacyjne. Sygnał "
        "Wi-Fi ma wyłącznie znaczenie diagnostyczne i sam nigdy nie zmienia częstotliwości "
        "odpytywania."
    ),
    "zh-Hans.json": (
        "配置此微型逆变器的轮询行为。关闭自适应轮询时，下方各间隔保持原有的固定轮询逻辑。"
        "启用后，这些值将作为算法边界：正常间隔是常规轮询周期；错误间隔决定第一次重试的延迟，"
        "且不会短于正常间隔；达到所配置的连续失败阈值后，会立即使用离线/夜间间隔。TSUN Local "
        "会在这些边界之间自动计算逐级退避间隔。只要再次成功读取，微型逆变器会立即恢复为在线状态，"
        "随后轮询间隔逐步恢复到正常值。因此，修改任一间隔或失败阈值都会自动改变自适应轮询的阶梯。"
        "Wi-Fi 信号仅用于诊断，本身绝不会改变轮询频率。"
    ),
}

ROOT = Path(__file__).resolve().parents[2]
INTEGRATION = ROOT / "custom_components" / "tsun_local"

for filename, description in DESCRIPTIONS.items():
    path = INTEGRATION / filename if filename == "strings.json" else INTEGRATION / "translations" / filename
    data = json.loads(path.read_text(encoding="utf-8"))
    data["options"]["step"]["init"]["description"] = description
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

notes_path = ROOT / "docs" / "releases" / "1.6.0-beta.1.md"
notes = notes_path.read_text(encoding="utf-8")
section = """## Adaptive polling: how the configured delays are used\n\nAdaptive polling reacts only to **real local-protocol communication failures**. Wi-Fi RSSI is never used by itself to slow polling or to mark a micro-inverter offline.\n\nThe values configured in the integration remain authoritative:\n\n- **Normal polling interval**: regular cadence while communication is healthy.\n- **Retry interval after error**: first retry delay; adaptive mode never goes below the normal interval.\n- **Offline/night polling interval**: upper backoff limit and the interval applied immediately when the configured consecutive-failure threshold is reached.\n- **Failures before offline**: number of consecutive failed protocol polls required before `Micro-inverter online` becomes false.\n\nBefore the offline threshold is reached, TSUN Local advances through monotonic backoff steps derived from the configured values: `max(normal, error)`, then approximately `1.5 × normal`, `3 × normal` and `6 × normal`, always capped by the configured offline/night interval. When the failure threshold is reached, it jumps directly to the offline/night interval and marks the micro-inverter offline.\n\nOn the **first successful protocol poll**, the micro-inverter is marked online immediately. The polling interval then decreases by one adaptive step after each successful poll until the normal cadence is restored. Changing the three intervals or the failure threshold therefore automatically changes the adaptive behavior; there is no separate hidden timing profile.\n\nWith the default settings (**20 s normal / 20 s after error / 300 s offline-night / threshold 3**), the sequence after consecutive failures is **20 s → 30 s → 300 s (offline)**. After communication returns, recovery is **120 s → 60 s → 30 s → 20 s → 20 s (normal state)**.\n\n"""
marker = "## Wi-Fi and online-state semantics\n"
if "## Adaptive polling: how the configured delays are used" not in notes:
    if marker not in notes:
        raise SystemExit("release notes insertion marker not found")
    notes = notes.replace(marker, section + marker)
notes_path.write_text(notes, encoding="utf-8")

print("Updated adaptive polling UI text in strings.json and all 8 translations.")
print("Expanded 1.6.0-beta.1 release notes with exact adaptive timing semantics.")
