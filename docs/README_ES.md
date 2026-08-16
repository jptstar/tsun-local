<p align="center">
  <a href="https://github.com/jptstar/tsun-local/blob/beta-1097/README.md">English</a> ·
  <a href="https://github.com/jptstar/tsun-local/blob/beta-1097/docs/README_FR.md">Français</a> ·
  <a href="https://github.com/jptstar/tsun-local/blob/beta-1097/docs/README_DE.md">Deutsch</a> ·
  <a href="https://github.com/jptstar/tsun-local/blob/beta-1097/docs/README_NL.md">Nederlands</a> ·
  <a href="https://github.com/jptstar/tsun-local/blob/beta-1097/docs/README_IT.md">Italiano</a> ·
  <a href="https://github.com/jptstar/tsun-local/blob/beta-1097/docs/README_ES.md">Español</a> ·
  <a href="https://github.com/jptstar/tsun-local/blob/beta-1097/docs/README_PL.md">Polski</a> ·
  <a href="https://github.com/jptstar/tsun-local/blob/beta-1097/docs/README_ZH.md">简体中文</a>
</p>

<p align="center">
  <img src="../custom_components/tsun_local/brand/icon@2x.png" width="160" alt="TSUN Local">
</p>

<h1 align="center">TSUN Local</h1>
<h3 align="center">Tu inversor. Tu red. Tus datos.</h3>
<p align="center"><strong>Local. Solo lectura. Sin nube. Sin proxy.</strong></p>
<p align="center">Acceso local directo a microinversores TSUN compatibles en Home Assistant.<br><strong>1.4.0-beta.8</strong></p>

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
| **02B0** | GEN3 PLUS · **TSOL-MX500** | ✅ **Validado** |
| **1097** | GEN3 | 🧪 **Experimental** |

> [!TIP]
> **No aparecer en la lista no significa que no sea compatible.** Si tu inversor usa **1511, 02B0 o 1097**, puede funcionar ya.

<p align="center">
  <a href="https://my.home-assistant.io/redirect/hacs_repository/?owner=jptstar&repository=tsun-local&category=integration">
    <img alt="Añadir TSUN Local a HACS" src="https://my.home-assistant.io/badges/hacs_repository.svg">
  </a>
</p>

<p align="center"><strong>Instálalo. Deja que TSUN Local identifique el protocolo. Comprueba qué expone tu inversor.</strong></p>

---

## De un vistazo

| | Lo que expone TSUN Local |
|---|---|
| ☀️ **PV** | Tensión · Corriente · Potencia · Energía diaria · Energía total |
| ⚡ **AC** | Tensión · Corriente · Frecuencia · Potencia · Energía diaria · Energía total |
| 🚨 **Diagnóstico** | Alarmas · Comunicación · Información del logger |
| 🛡️ **Avanzado** | Protección de red · Diagnóstico del inversor · Desactivado por defecto |
| 🔒 **Seguridad** | Solo lectura · Sin escrituras de configuración en el inversor |

📚 **[Referencia completa de entidades por protocolo](ENTITIES.md)** — sensores, sensores binarios y botones para **1511, 02B0 y 1097**.

---

## Compatibilidad

**Home Assistant 2026.3.0 o posterior.**

> [!NOTE]
> **✅ Validado** = confirmado en hardware real con TSUN Local.  
> **🔎 Probablemente compatible** = la familia de protocolo está soportada, pero este modelo exacto aún no se ha validado con TSUN Local.  
> **🧪 Experimental** = existe soporte del protocolo, pero todavía necesita más validación en dispositivos reales.

### 1511 · TITAN — ✅ Validado

**✅ Validado**  
`TSOL-MP3000`

**🔎 Probablemente compatible**  
`TSOL-MP2250` · `TSOL-MS3000` *(generación TITAN)*

| | Datos disponibles |
|---|---|
| ☀️ **PV** | Hasta 6 entradas · Tensión · Corriente · Potencia · Energía diaria y total |
| ⚡ **AC** | Tensión · Corriente · Frecuencia · Potencia · Energía diaria y total |
| 🚨 **Diagnóstico** | Alarmas del inversor |
| 🛡️ **Avanzado** | Umbrales de protección de red y diagnósticos de temporización |

### 02B0 · GEN3 PLUS — ✅ Validado

**✅ Validado**  
`TSOL-MX500`

**🔎 Probablemente compatible**  
`TSOL-MX450` · `TSOL-MX800` · `TSOL-MX1000` · `TSOL-MX3000`  
`TSOL-MS800` · `TSOL-MS1600` · `TSOL-MS1800` · `TSOL-MS2000`  
Las variantes `-D` correspondientes también pueden ser compatibles cuando existan.

> [!NOTE]
> La investigación pública sobre GEN3 PLUS asocia generalmente estos dispositivos con la familia de números de serie **Y17 / Y47**. Esto ayuda a distinguir modelos cuyo nombre también existe en variantes GEN3 anteriores.

| | Datos disponibles |
|---|---|
| ☀️ **PV** | Detección dinámica de entradas PV · Tensión · Corriente · Potencia · Energía |
| ⚡ **AC** | Tensión · Corriente · Frecuencia · Potencia · Energía |
| 🚨 **Diagnóstico** | Alarmas del inversor |
| 🛡️ **Avanzado** | Diagnóstico de protección de red · Coeficiente de salida |

### 1097 · GEN3 — 🧪 Experimental

**🔎 Probablemente compatible**  
`TSOL-MS300` · `TSOL-MS350` · `TSOL-MS400`  
`TSOL-MS600` · `TSOL-MS700` · `TSOL-MS800`  
`TSOL-MS3000`

> [!NOTE]
> La investigación pública sobre GEN3 asocia generalmente estos dispositivos con la familia de números de serie **R17 / R47**. La compatibilidad con el protocolo **1097** de TSUN Local sigue siendo experimental hasta confirmarse en más hardware real.

| | Datos disponibles |
|---|---|
| ☀️ **PV** | Telemetría PV estándar |
| ⚡ **AC** | Telemetría estándar del inversor / AC |
| 🚨 **Diagnóstico** | Diagnósticos disponibles del inversor |
| 🛡️ **Avanzado** | Versión de protocolo · Versión de inversor · Temperatura · Aislamiento RX/RY · Valor bruto país/perfil · Potencia de diseño |

> **🔎 Probablemente compatible no significa validado.** Significa que TSUN Local ya implementa la familia de protocolo correspondiente, lo que convierte al dispositivo en un buen candidato de compatibilidad.

---

## 🛡️ Diagnóstico avanzado

Las entidades avanzadas están **desactivadas por defecto** de forma intencionada. Así, la página normal del dispositivo permanece simple, mientras que la información técnica sigue disponible cuando se necesita.

Para activar una:

**Ajustes → Dispositivos y servicios → TSUN Local → Dispositivo → Entidades → Entidades desactivadas**

No se implementan escrituras de configuración hacia el inversor.

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

## Probar otro modelo TSUN

Tu inversor no tiene que aparecer en la lista anterior.

Si TSUN Local identifica uno de estos protocolos:

```text
1511
02B0
1097
```

déjalo funcionar y comprueba las entidades detectadas.

> [!TIP]
> **Tu inversor podría convertirse en el próximo modelo validado.** Son útiles el modelo exacto, el protocolo detectado, el número de entradas PV, la versión de firmware y qué entidades devuelven valores plausibles.

---

## TSUN Local 1.4

### Un TSUN Local más amplio

La versión 1.4 lleva TSUN Local desde modelos conocidos individuales hacia la **compatibilidad por familias de protocolos**.

| | |
|---|---|
| 🔌 | **1511 · 02B0 · 1097** |
| 🔍 | Identificación automática del protocolo |
| ☀️ | Detección progresiva / dinámica de entradas PV |
| 📊 | Telemetría local ampliada |
| 🛡️ | Diagnóstico avanzado de solo lectura |
| 🌍 | 8 idiomas |
| 🧪 | Pruebas más sencillas de nuevos modelos TSUN |

---

## Ingeniería inversa y validación

Las implementaciones 1511 y 02B0 se desarrollan mediante **análisis independiente del protocolo local, observación de dispositivos reales y validación de hardware**.

Los candidatos de compatibilidad se etiquetan de forma intencionadamente separada del hardware realmente validado.

---

## Contribuciones

TSUN Local también se beneficia de contribuciones de la comunidad:

- **Stefan Allius / `s-allius/tsun-gen3-proxy`** — investigación pública del protocolo 1097 que contribuyó al mapeo experimental utilizado por TSUN Local.
- **TheSmartGerman** — pruebas en hardware real y comentarios de compatibilidad para el **TSOL-MP3000 con 1511**, durante las cuales se detectó involuntariamente el protocolo **1097**.

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
