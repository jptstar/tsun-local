# TSUN Local — Integración local para Home Assistant

[English](../README.md) | [Français](README_FR.md) | [Deutsch](README_DE.md) | [Nederlands](README_NL.md) | [Italiano](README_IT.md) | [Español](README_ES.md) | [Polski](README_PL.md) | [简体中文](README_ZH.md)

[![GitHub Release](https://img.shields.io/github/v/release/jptstar/tsun-local)](https://github.com/jptstar/tsun-local/releases)

<p align="center">
  <img src="https://raw.githubusercontent.com/jptstar/tsun-local/main/custom_components/tsun_local/brand/icon@2x.png" width="160" alt="Icono independiente de TSUN Local">
</p>

> **Proyecto no oficial** — Esta integración comunitaria independiente no está desarrollada, aprobada ni mantenida por TSUN y no está afiliada a TSUN de ninguna manera. TSUN y los nombres de sus productos siguen siendo propiedad de sus respectivos titulares. Las solicitudes de asistencia relacionadas con esta integración deben dirigirse a su autor, no a TSUN.

**TSUN Local** integra directamente en Home Assistant los microinversores TSUN compatibles **a través de la red local, sin proxy ni servicio en la nube**.

La versión 1.4.0-beta.4 admite los modelos **TSOL-MP3000** y **MX500**, validados en hardware real, además de otros modelos **TITAN**, **GEN3** y **GEN3 PLUS** pendientes de validación.

**Autor: Jean-Philippe TESTART (jptstar)**

## Naturaleza del proyecto y soporte

TSUN Local es una integración de Home Assistant que desarrollé inicialmente por afición y para mi uso personal. Como muchos usuarios tienen dificultades para establecer una conexión local con los microinversores TITAN, la pongo a disposición para que pueda beneficiarse el mayor número posible de personas.

Si recibo comentarios e información de diagnóstico sobre modelos concretos, estoy dispuesto a dedicar algo de tiempo a mejorar la compatibilidad y corregir errores. Sin embargo, TSUN Local sigue siendo un hobby y una actividad secundaria, no mi actividad principal. Por ello, es posible que algunas respuestas o correcciones tarden un poco.

## Versiones

Las versiones publicadas siguen el formato `MAJOR.MINOR.PATCH`. HACS utiliza las GitHub Releases para ofrecer actualizaciones. Consulte el [registro de cambios](../CHANGELOG.md) para conocer los detalles.

## Compatibilidad

**Home Assistant 2026.3.0 o posterior**

### Leyenda

- ✅ Compatible y validado en hardware real
- 🧪 Listo para pruebas de la comunidad — adaptador disponible; agradecemos los comentarios
- 🔎 Se necesitan datos del hardware — compatibilidad pendiente de confirmación

### Microinversores

#### TITAN

| Configuración | Modelos | Estado |
|---|---|---|
| 6-in-1 | **TSOL-MP3000** | ✅ Validado |
| 6-in-1 | **TSOL-MP2250, TSOL-MS3000** | 🧪 Se buscan probadores |
| Entradas por determinar | **MP6000, MP5000, MP4600, MP4000, MP3750, MP3680** | 🔎 Se buscan datos del hardware |

#### GEN3 / GEN3 PLUS — serie MX

| Configuración | Modelos | Estado |
|---|---|---|
| 1-in-1 | **MX500** | ✅ Validado |
| 1-in-1 | **MX450, MX400** | 🧪 Se buscan probadores |
| 2-in-1 | **MX1000, MX900, MX800** | 🧪 Se buscan probadores |
| 4-in-1 | **MX2250** | 🧪 Se buscan probadores |
| 6-in-1 | **MX3300, MX3000, MX2700, MX2500, MX2400** | 🔎 Se buscan datos del hardware |

#### GEN3 / GEN3 PLUS — serie MS

| Configuración | Modelos | Estado |
|---|---|---|
| 1-in-1 | **MS400, MS350, MS300, MS400-D** | 🧪 Se buscan probadores |
| 2-in-1 | **MS800, MS700, MS600, MS600-D, MS800-D** | 🧪 Se buscan probadores |
| 4-in-1 | **MS2000, MS1800, MS1600, MS2000-D, MS3000** | 🧪 Se buscan probadores |

La detección FV es dinámica hasta **6 entradas para TITAN**. Para GEN3 / GEN3 PLUS, el mapa actual cubre **1, 2 o 4 entradas FV**; PV5 y PV6 todavía no se detectan.

> **¿Tiene uno de estos modelos?** Los modelos marcados con 🧪 están listos para pruebas de la comunidad. [Abra un informe de compatibilidad](https://github.com/jptstar/tsun-local/issues/new) indicando el modelo exacto, la versión del firmware y el resultado de la prueba. Oculte los números de serie completos y los datos privados de la red.

## Instalación

### Con HACS

[![Añadir TSUN Local a HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=jptstar&repository=tsun-local&category=integration)

O añádalo manualmente:

1. En HACS, abra el menú **⋮** de la esquina superior derecha y seleccione **Repositorios personalizados**.
2. Añada `https://github.com/jptstar/tsun-local` con el tipo **Integración**.
3. Seleccione **Añadir** y abra **TSUN Local**.
4. Seleccione **Descargar** y elija la última versión disponible.
5. Reinicie Home Assistant.

Si no aparece la última versión, abra el menú del repositorio y seleccione **Actualizar información**.

### Instalación manual

1. Copie `custom_components/tsun_local` en `/config/custom_components/`.
2. Reinicie Home Assistant.
3. Abra **Ajustes → Dispositivos y servicios → Añadir integración**.
4. Busque **TSUN Local**.

## Añadir un dispositivo

TSUN Local puede buscar microinversores en la red local. También puede introducir manualmente su dirección IP. El puerto TCP `8899` se propone de forma predeterminada y puede modificarse.

El protocolo local y el **SN** numérico se detectan automáticamente. Si es necesario, el SN puede introducirse manualmente desde la página local o la etiqueta del dispositivo. Es distinto del **SN del microinversor** alfanumérico.

Si el dispositivo está en otra VLAN y no se encuentra, indique su subred en notación CIDR o utilice la configuración manual.

Se pueden añadir varios microinversores. Cada dispositivo dispone de sus propias entidades y ajustes de sondeo.

## Ajustes en Home Assistant

En **Ajustes → Dispositivos y servicios → TSUN Local**, abra el menú del dispositivo correspondiente:

- **Configurar** establece el intervalo normal entre 10 segundos y 5 minutos (20 segundos de forma predeterminada), el reintento tras un error entre 10 segundos y 5 minutos (20 segundos de forma predeterminada), el intervalo sin conexión/nocturno entre 1 y 60 minutos (5 minutos de forma predeterminada) y el umbral entre 1 y 20 fallos consecutivos (3 de forma predeterminada);
- **Reconfigurar** permite cambiar la dirección IP y el puerto TCP sin eliminar entidades;
- cada dispositivo tiene intervalos de sondeo independientes.

## Funcionamiento local y aislamiento de la nube

TSUN Local se comunica únicamente por la red local y no utiliza ningún servicio en la nube. La integración no modifica la configuración de nube del firmware.

Para impedir que el microinversor acceda a Internet, cree una regla en el router o cortafuegos que bloquee su acceso WAN y conserve el acceso a la red local y a DHCP. Home Assistant debe seguir pudiendo acceder a la dirección IP del microinversor mediante el puerto TCP **8899**. Tras la instalación, HACS solo necesita Internet para buscar y descargar actualizaciones.

## Funcionamiento nocturno

Cuando el microinversor deja de recibir alimentación, la integración lo marca como desconectado sin repetir un error en cada sondeo:

Hasta alcanzar el umbral configurable, los últimos valores siguen disponibles y los reintentos usan el intervalo tras error. Al alcanzar el umbral (3 fallos de forma predeterminada), el dispositivo pasa a desconectado y usa el intervalo sin conexión/nocturno. La primera respuesta correcta pone el contador a cero y restablece el intervalo normal.

- las mediciones instantáneas (tensión, corriente, potencia y frecuencia) dejan de estar disponibles para evitar mostrar valores obsoletos;
- los contadores de energía diaria y total permanecen disponibles con su último valor conocido;
- el sensor binario **Microinversor en línea** indica que el dispositivo está desconectado;
- el contador de errores de comunicación consecutivos vuelve a cero cuando se reanuda la comunicación;
- la hora de la última comunicación correcta permanece disponible;
- los nuevos intentos utilizan el intervalo sin conexión/nocturno configurado;
- el intervalo normal se restablece después de la primera respuesta correcta de la mañana.

## Sensores

La integración crea un único dispositivo con mediciones de CA, 5 mediciones por cada entrada FV detectada, la suma de las potencias de CC detectadas, 4 diagnósticos de comunicación, sensores de diagnóstico para **SN**, **SN del microinversor**, firmware y dirección MAC del logger, y el sensor binario de conectividad **Microinversor en línea**.

El número de entradas FV es dinámico: PV1 está disponible después de la primera lectura; de PV2 a PV6 para TITAN o de PV2 a PV4 para GEN3/GEN3 PLUS se añaden cuando se observa una medición o un contador de energía válido. Una entrada detectada permanece registrada en Home Assistant.

## Licencia

Copyright © 2026 Jean-Philippe TESTART (jptstar).

Este proyecto se distribuye bajo la **GNU General Public License v3.0 o posterior** (GPL-3.0-or-later). Las versiones modificadas o redistribuidas deben cumplir esta licencia y conservar los avisos de copyright y licencia. Consulte [LICENSE](https://github.com/jptstar/tsun-local/blob/main/LICENSE).

La licencia cubre únicamente esta implementación independiente. No concede ningún derecho sobre las marcas, logotipos, programas o productos de TSUN. Este proyecto sigue siendo no oficial y no está afiliado a TSUN.
