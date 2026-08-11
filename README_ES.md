# TSUN Local — Integración local para Home Assistant

[Français](README.md) | [English](README_EN.md) | [Deutsch](README_DE.md) | [Nederlands](README_NL.md) | [Italiano](README_IT.md) | [Español](README_ES.md) | [Polski](README_PL.md) | [简体中文](README_ZH.md)

[![GitHub Release](https://img.shields.io/github/v/release/jptstar/tsun-local)](https://github.com/jptstar/tsun-local/releases)

<p align="center">
  <img src="https://raw.githubusercontent.com/jptstar/tsun-local/main/custom_components/tsun_local/brand/icon@2x.png" width="160" alt="Icono independiente de TSUN Local">
</p>

> **Proyecto no oficial** — Esta integración comunitaria independiente no está desarrollada, aprobada ni mantenida por TSUN y no está afiliada a TSUN de ninguna manera. TSUN y los nombres de sus productos siguen siendo propiedad de sus respectivos titulares. Las solicitudes de asistencia relacionadas con esta integración deben dirigirse a su autor, no a TSUN.

**TSUN Local** integra directamente en Home Assistant los microinversores TSUN compatibles presentes en la red local, sin proxy ni servicio en la nube. La versión 1.1.4 admite los modelos **TSOL-MP3000** y **MX500**, validados en hardware real, además de otros modelos **TITAN**, **GEN3** y **GEN3 PLUS** pendientes de validación.

**Autor: Jean-Philippe TESTART (jptstar)**

## Licencia

Copyright © 2026 Jean-Philippe TESTART (jptstar).

Este proyecto se distribuye bajo la **GNU General Public License v3.0 o posterior** (`GPL-3.0-or-later`). Las versiones modificadas o redistribuidas deben cumplir esta licencia y conservar los avisos de copyright y licencia. Consulte [LICENSE](LICENSE).

La licencia cubre únicamente esta implementación independiente. No concede ningún derecho sobre las marcas, logotipos, programas o productos de TSUN. Este proyecto sigue siendo no oficial y no está afiliado a TSUN.

## Versiones

Las versiones publicadas siguen el formato `MAJOR.MINOR.PATCH`. HACS utiliza las GitHub Releases para ofrecer actualizaciones. Consulte el [registro de cambios](CHANGELOG.md) para conocer los detalles.

## Compatibilidad

**Home Assistant 2026.3.0 o posterior**

### Leyenda

- ✅ Compatible y validado en hardware real
- ❌ Adaptador disponible, validación de hardware pendiente
- ⛔ Actualmente no compatible

### Microinversores

| Familia | Modelos | Estado |
|---|---|---|
| TITAN 2250 W–3000 W | **TSOL-MP3000** | ✅ Validado |
| TITAN 2250 W–3000 W | **TSOL-MP2250, TSOL-MS3000** | ❌ Validación pendiente |
| TITAN 3680 W–6000 W | **MP6000, MP5000, MP4600, MP4000, MP3750, MP3680** | ⛔ No compatible |
| GEN3 / GEN3 PLUS | **MS300, MS350, MS400, MS400-D** | ❌ Validación pendiente |
| GEN3 / GEN3 PLUS | **MS600, MS700, MS800, MS600-D, MS800-D** | ❌ Validación pendiente |
| GEN3 / GEN3 PLUS | **MS1600, MS1800, MS2000, MS2000-D** | ❌ Validación pendiente |
| GEN3 / GEN3 PLUS | **MS3000** | ❌ Validación pendiente |
| GEN3 / GEN3 PLUS | **MX500** | ✅ Validado |
| GEN3 / GEN3 PLUS | **MX450, MX1000** | ❌ Validación pendiente |
| GEN3 / GEN3 PLUS | **MX3000** | ⛔ No compatible |

El adaptador GEN3 / GEN3 PLUS detecta dinámicamente los dispositivos con **1, 2 o 4 entradas FV**.

El **MX3000** no es compatible porque el mapa de registros disponible termina en PV4, mientras que este modelo puede tener entradas adicionales.

### Otros dispositivos

| Tipo | Modelos | Estado |
|---|---|---|
| Sistema de almacenamiento | **DC1000** | ⛔ No compatible |
| Contadores inteligentes | **TSOL-MG3-MS, DDZY422-D2** | ⛔ No compatibles |

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
5. Introduzca la dirección IP, el puerto y el **Monitor SN / Logger SN impreso en la etiqueta del microinversor**.

Al añadir un dispositivo, elija **Buscar en la red local** o **Configuración manual** y seleccione **TITAN** para TSOL-MP3000 o **GEN3 / GEN3 PLUS** para MX500. Introduzca el **Monitor SN / Logger SN** impreso en la etiqueta. La búsqueda examina únicamente la red IPv4 local en el puerto 8899 y no envía datos a las direcciones candidatas.

## Varios dispositivos

Se pueden añadir varios microinversores compatibles a la misma instalación de Home Assistant. Ejecute **Añadir integración** para cada dispositivo e introduzca su dirección IP y su SN único. Cada configuración crea un dispositivo independiente con sus propias entidades y su propio coordinador de comunicación.

## Ajustes en Home Assistant

En **Ajustes → Dispositivos y servicios → TSUN Local**, abra el menú del dispositivo correspondiente:

- **Configurar** establece el intervalo normal entre 10 segundos y 5 minutos (30 segundos de forma predeterminada) y el intervalo sin conexión/nocturno entre 1 y 60 minutos (5 minutos de forma predeterminada);
- **Reconfigurar** permite cambiar la dirección IP y el puerto TCP sin eliminar entidades;
- cada dispositivo tiene intervalos de sondeo independientes.

## Funcionamiento local y aislamiento de la nube

TSUN Local se comunica únicamente por la red local y no utiliza ningún servicio en la nube. La integración no modifica la configuración de nube del firmware.

Para impedir que el microinversor acceda a Internet, cree una regla en el router o cortafuegos que bloquee su acceso WAN y conserve el acceso a la red local y a DHCP. Home Assistant debe seguir pudiendo acceder a la dirección IP del microinversor mediante el puerto TCP **8899**. Tras la instalación, HACS solo necesita Internet para buscar y descargar actualizaciones.

## Funcionamiento nocturno

Cuando el microinversor deja de recibir alimentación, la integración lo marca como desconectado sin repetir un error en cada sondeo:

- las mediciones instantáneas (tensión, corriente, potencia y frecuencia) dejan de estar disponibles para evitar mostrar valores obsoletos;
- los contadores de energía diaria y total permanecen disponibles con su último valor conocido;
- el diagnóstico **Comunicación** indica que el dispositivo está desconectado;
- el contador de errores de comunicación consecutivos vuelve a cero cuando se reanuda la comunicación;
- la hora de la última comunicación correcta permanece disponible;
- los nuevos intentos utilizan el intervalo sin conexión/nocturno configurado;
- el intervalo normal se restablece después de la primera respuesta correcta de la mañana.

## Sensores

La integración crea un único dispositivo con mediciones de CA, 5 mediciones por cada entrada FV detectada, la suma de las potencias de CC detectadas, 4 sensores de diagnóstico y un estado de conectividad.

El número de entradas FV es dinámico: PV1 está disponible después de la primera lectura; de PV2 a PV6 para TITAN o de PV2 a PV4 para GEN3/GEN3 PLUS se añaden cuando se observa una medición o un contador de energía válido. Una entrada detectada permanece registrada en Home Assistant.
