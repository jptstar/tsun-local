<p align="center">
  <a href="https://github.com/jptstar/tsun-local/blob/main/README.md">English</a> ·
  <a href="https://github.com/jptstar/tsun-local/blob/main/docs/README_FR.md">Français</a> ·
  <a href="https://github.com/jptstar/tsun-local/blob/main/docs/README_DE.md">Deutsch</a> ·
  <a href="https://github.com/jptstar/tsun-local/blob/main/docs/README_NL.md">Nederlands</a> ·
  <a href="https://github.com/jptstar/tsun-local/blob/main/docs/README_IT.md">Italiano</a> ·
  <a href="https://github.com/jptstar/tsun-local/blob/main/docs/README_ES.md">Español</a> ·
  <a href="https://github.com/jptstar/tsun-local/blob/main/docs/README_PL.md">Polski</a> ·
  <a href="https://github.com/jptstar/tsun-local/blob/main/docs/README_ZH.md">简体中文</a>
</p>

<p align="center">
  <img src="../custom_components/tsun_local/brand/icon@2x.png" width="160" alt="TSUN Local">
</p>

<h1 align="center">TSUN Local</h1>
<h3 align="center">Tu inversor. Tu red. Tus datos.</h3>
<p align="center"><strong>Local. Solo lectura. Sin nube. Sin proxy.</strong></p>
<p align="center">Acceso local directo a microinversores TSUN compatibles en Home Assistant.<br><strong>1.5.4</strong></p>

<p align="center">
  <a href="https://github.com/jptstar/tsun-local/releases"><img alt="GitHub Release" src="https://img.shields.io/github/v/release/jptstar/tsun-local"></a>
  <a href="https://github.com/hacs/integration"><img alt="HACS" src="https://img.shields.io/badge/HACS-Custom-41BDF5"></a>
  <a href="../LICENSE"><img alt="GPL-3.0-or-later" src="https://img.shields.io/badge/License-GPL--3.0--or--later-blue"></a>
</p>

---

## Tu inversor TSUN puede funcionar ya

TSUN Local admite **tres familias de protocolos locales TSUN**.

| Protocolo | Familia / referencia validada | Estado |
|:---:|---|:---:|
| **1511** | TITAN · **TSOL-MP3000** | ✅ **Validado** |
| **02B0** | GEN3 / GEN3 PLUS · **TSOL-MX500** | ✅ **Validado** |
| **1097** | GEN3 / GEN3 PLUS | 🧪 **Experimental** |

> [!TIP]
> **No aparecer en la lista no significa que no sea compatible.** Si tu inversor usa **1511, 02B0 o 1097**, puede funcionar ya.

<p align="center">
  <a href="https://my.home-assistant.io/redirect/hacs_repository/?owner=jptstar&repository=tsun-local&category=integration">
    <img alt="Añadir TSUN Local a HACS" src="https://my.home-assistant.io/badges/hacs_repository.svg">
  </a>
</p>

---

## De un vistazo

| | Lo que expone TSUN Local |
|---|---|
| ☀️ **PV** | Tensión · Corriente · Potencia · Energía diaria · Energía total |
| ⚡ **AC** | Tensión · Corriente · Frecuencia · Potencia · Energía diaria · Energía total |
| 🚨 **Diagnóstico** | Alarmas activas · Comunicación · Información del logger |
| 🛡️ **Avanzado** | Protección de red · Firmware · Diagnóstico del inversor · Datos experimentales de validación |
| 🔒 **Seguridad** | Solo lectura · Sin escrituras de configuración en el inversor |

📚 **[Referencia completa de entidades por protocolo](ENTITIES.md)**

---

## Compatibilidad

**Home Assistant 2026.3.0 o posterior.**

> [!NOTE]
> **✅ Validado** = confirmado en hardware real con TSUN Local.  
> **🔎 Probablemente compatible** = la familia de protocolo está soportada, pero este modelo exacto aún no se ha validado.  
> **🧪 Experimental** = existe soporte del protocolo, pero todavía necesita más validación en dispositivos reales.

### 1511 · TITAN — ✅ Validado

**✅ Validado**  
`TSOL-MP3000`

**🔎 Probablemente compatible**  
`TSOL-MP2250` · `TSOL-MS3000` *(generación TITAN)*

Hasta 6 entradas PV, telemetría AC/PV, energía, diagnóstico del inversor, versiones de firmware, alarmas y diagnóstico avanzado de red de solo lectura.

📚 **[Detalles de validación MP3000 / TITAN](MP3000_FIELD_VALIDATION.md)**

### 02B0 · GEN3 / GEN3 PLUS — ✅ Validado

**✅ Validado**  
`TSOL-MX500` · `Sunology PLAY2`

**🔎 Probablemente compatible**  
`TSOL-MX450` · `TSOL-MX800` · `TSOL-MX1000` · `TSOL-MX3000`  
`TSOL-MS800` · `TSOL-MS1600` · `TSOL-MS1800` · `TSOL-MS2000`

Las variantes `-D` correspondientes también pueden ser compatibles cuando existan.

Detección dinámica de entradas PV, telemetría AC/PV, alarmas del inversor y diagnóstico avanzado de solo lectura.


Validación independiente de **Sunology PLAY2** en Home Assistant: descubrimiento automático y configuración de TSUN Local completados correctamente en hardware real.

TSUN Local 1.5.4 añade la temperatura del inversor, la versión de firmware del inversor y diagnósticos 02B0 adicionales de solo lectura, incluido un valor bruto de conformidad del producto.

### 1097 · GEN3 / GEN3 PLUS — 🧪 Experimental

**🔎 Probablemente compatible**  
`TSOL-MS300` · `TSOL-MS350` · `TSOL-MS400`  
`TSOL-MS600` · `TSOL-MS700` · `TSOL-MS800`  
`TSOL-MS3000` · `TSOL-MX3000D`

El soporte del protocolo está implementado, pero aún requiere más validación en dispositivos reales.

> [!NOTE]
> Un mismo nombre comercial puede cubrir distintas generaciones de hardware o logger. **Para TSUN Local, el protocolo local detectado es la referencia de compatibilidad.**

---

## 🚨 Alarmas MP3000

TSUN Local admite el bitfield completo de alarmas MP3000 manteniendo compacta la interfaz de Home Assistant. **Las 224 posiciones de alarma se conservan y se evalúan cuando se activan.**

Las **12 correspondencias funcionales observadas en hardware** cubren baja tensión de entrada PV y fallos DSP para PV1 a PV6. Las otras **212 posiciones** conservan identificadores TSUN Local neutros y estables hasta que su significado funcional se valide físicamente.

Home Assistant muestra un estado **Alarma del inversor**, un contador **Alarmas activas** y un sensor **Nombres de alarmas activas**. Las 14 palabras brutas completas permanecen disponibles como diagnóstico desactivado por defecto, sin crear 224 entidades permanentes.

---


> [!TIP]
> Las alarmas activas también se muestran como **texto claro localizado** con un código de posición estable, por ejemplo `Subtensión de red (02B0-A014)`. **Sunology PLAY2** utiliza la misma interfaz compacta de alarmas 02B0; las cuatro palabras ERR brutas siguen disponibles como diagnóstico avanzado.

## 🛡️ Diagnóstico avanzado

Las entidades avanzadas están **desactivadas por defecto** de forma intencionada. Según el protocolo incluyen valores de protección de red, firmware, diagnóstico del inversor y algunos valores experimentales de validación.

Para activarlas:

**Ajustes → Dispositivos y servicios → TSUN Local → Dispositivo → Entidades → Entidades desactivadas**

Las asociaciones semánticas experimentales permanecen claramente marcadas hasta su validación independiente. No se implementan escrituras de configuración hacia el inversor.

📚 **[Evidencias de validación MP3000](MP3000_FIELD_VALIDATION.md)**  
📚 **[Referencia completa de entidades](ENTITIES.md)**

---

## Instalación

### HACS

<p align="center">
  <a href="https://my.home-assistant.io/redirect/hacs_repository/?owner=jptstar&repository=tsun-local&category=integration">
    <img alt="Añadir TSUN Local a HACS" src="https://my.home-assistant.io/badges/hacs_repository.svg">
  </a>
</p>

O añade `https://github.com/jptstar/tsun-local` en **HACS → Repositorios personalizados → Integración**, instala **TSUN Local** y reinicia Home Assistant.

### Manual

Copia `custom_components/tsun_local` en `/config/custom_components/`, reinicia Home Assistant y añade **TSUN Local** desde **Ajustes → Dispositivos y servicios**.

---

## Cómo funciona

```text
Inversor TSUN
     │
     │ Red local
     ▼
 TSUN Local
     │
     ▼
Home Assistant
```

**Sin nube en la ruta de datos. Sin proxy. Sin servicio de ejecución remoto. Sin escrituras de configuración en el inversor.**

Solo sondeo local directo.

---

## 🔬 Validar otro modelo TSUN

TSUN Local incluye una herramienta autónoma de captura de hardware, respetuosa con la privacidad y **estrictamente de solo lectura**.

**⬇️ [Descargar `tsun_dump.py`](https://raw.githubusercontent.com/jptstar/tsun-local/main/tools/tsun_dump.py)**

Python 3.10+ es suficiente.

macOS / Linux:

```bash
cd ~/Downloads
python3 tsun_dump.py --full
```

Windows:

```powershell
py tsun_dump.py --full
```

La herramienta puede descubrir loggers TSUN compatibles, detectar familias de protocolo soportadas y crear un volcado JSON respetuoso con la privacidad por dispositivo. No implementa ninguna escritura hacia el inversor.

Para VLAN, descubrimiento dirigido, comparaciones antes/después y validación avanzada:

📚 **[Guía Hardware Validation Dump Tool](HARDWARE_DUMP.md)**

---

## Probar un inversor no listado

Si TSUN Local detecta `1511`, `02B0` o `1097`, déjalo funcionar y comprueba las entidades descubiertas.

La información más útil incluye el modelo exacto, el protocolo detectado, la versión de firmware, el número de entradas PV y qué entidades devuelven valores plausibles.

> [!TIP]
> **Tu inversor podría convertirse en el próximo modelo validado.**

---

## Política de validación

TSUN Local separa el soporte de hardware confirmado de la investigación experimental de protocolos.

Los nombres funcionales y el soporte de un modelo solo se marcan como validados tras comprobaciones reproducibles con hardware real. Un valor que simplemente coincide con un perfil esperado es una evidencia, no una prueba definitiva; las asociaciones experimentales permanecen marcadas hasta que una observación independiente las distinga sin ambigüedad.

---

## Contribuciones

TSUN Local se beneficia de investigación pública sobre protocolos y pruebas de la comunidad en hardware real.

- **Stefan Allius / `s-allius/tsun-gen3-proxy`** — investigación pública GEN3 / 1097 utilizada como referencia para determinadas asociaciones experimentales.
- **TheSmartGerman** — comentarios de compatibilidad en hardware real.

La procedencia detallada y las evidencias de validación se documentan junto a la investigación de protocolo correspondiente.

---

## Proyecto

> [!IMPORTANT]
> **Proyecto comunitario no oficial.** TSUN Local es independiente y no está desarrollado, aprobado, respaldado ni mantenido por TSUN.

Creado y mantenido por **Jean-Philippe TESTART · `jptstar`**  
*Creado y compartido por diversión, curiosidad técnica y para la comunidad de Home Assistant.*

---

## Licencia

Copyright © 2026 Jean-Philippe TESTART (`jptstar`).

Distribuido bajo la **GNU General Public License v3.0 o posterior**. Consulta [LICENSE](../LICENSE).
