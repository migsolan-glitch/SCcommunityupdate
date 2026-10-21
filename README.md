<div align="center">
  <img src="assets/logo.png" alt="SCcommunityupdate Logo" width="160" style="border-radius: 16px;" />
  <h1>SCcommunityupdate</h1>
  <p><b>Star Citizen Community Launcher, Translation Manager & QoL Mod Merger</b></p>
  <p>Interfaz gráfica moderna y oscura con estética sci-fi, desarrollada en Python con <b>CustomTkinter</b> y diseñada específicamente para la comunidad de <b>Star Citizen</b>.</p>
</div>

---

## 🚀 Características Principales

### 1. 🔍 Detección Automática de Ruta (`LIVE`)
- Escanea automáticamente todas las unidades de almacenamiento (`C:\`, `D:\`, etc.) y los registros del RSI Launcher en busca del directorio oficial de Star Citizen (`\Roberts Space Industries\StarCitizen\LIVE\`).
- Permite seleccionar o cambiar la ruta manualmente mediante un explorador de carpetas en cualquier momento.
- Guarda tu configuración localmente para no tener que volver a seleccionarla.

### 2. 📦 Soporte Inteligente de `releases/latest` (Traducciones y Mods)
- Tanto para los paquetes de **idiomas** como para los **mods/herramientas** de la comunidad, la aplicación consulta en tiempo real la API oficial de GitHub (`https://api.github.com/repos/{owner}/{repo}/releases/latest`).
- Detecta y descarga automáticamente archivos empaquetados `.zip` (ej. `Star_citizen_ES.zip`, `StarStrings-LIVE.zip`, `StarCitizen.Deutsch.LIVE.zip`) o archivos `.ini` publicados en el último Release oficial.
- Extrae en memoria el `global.ini` correspondiente a `LIVE`, analiza `user.cfg` para detectar el código de idioma exacto (`g_language = spanish_(spain)`, etc.) y la subcarpeta de localización apropiada.
- Si un repositorio no utiliza Releases, hace fallback automático a la rama principal (`main`/`master`).

### 3. ✨ Fusión Inteligente de StarStrings + Traducción Activa
- Viene preconfigurado con **[StarStrings (MrKraken)](https://github.com/MrKraken/StarStrings)** y **[StarMeld](https://github.com/dydx/StarMeld)**.
- **Problema habitual en Star Citizen:** El juego solo carga un archivo `global.ini` a la vez. Activar un mod en inglés como StarStrings normalmente desactiva la traducción al español.
- **Solución integrada (`✨ Fusionar con Traducción Activa`):**
  - Descarga los módulos actualizados de StarStrings (`components.ini`, `ordnance.ini`, `contracts.ini`, `mining.ini` — más de 2,000 mejoras de texto).
  - Inyecta las etiquetas de planos y reputación (`<EM4>[... Rep] [BP]*</EM4>`), clasificaciones de componentes (`Mil/1/B`, `Civ/2/A`, etc.), tipos de misiles (`[CS1]`, `[IR2]`, `[EM3]`) y guías de minería **directamente dentro de tu traducción activa (ej. Español)**.
  - Mantiene todos los textos de misiones e interfaz en tu idioma y conserva intacto `g_language = spanish_(spain)` en `user.cfg`.
  - Permite **Actualizar Fusión** o **Quitar de Traducción** (restaurando la traducción limpia desde caché) con un solo clic.

### 4. 🌐 Catálogo de Idiomas Oficiales de la Comunidad
Menú desplegable interactivo con las traducciones comunitarias verificadas para Star Citizen:
- 🇪🇸 **Español** (Comunidad Hispana - `Thord82/Star_citizen_ES`)
- 🇩🇪 **Alemán** (Deutsch - `rjcncpt/StarCitizen-Deutsch-INI`)
- 🇫🇷 **Francés** (Français - `Dymerz/StarCitizen-Localization`)
- 🇨🇳 **Chino Tradicional** (繁體中文 - `Orbit-Startech/TCTP-Star-Citizen`)
- 🇷🇺 **Ruso** (Русский - `n1ghter/StarCitizenRu`)
- 🇮🇹 **Italiano** (`Dymerz/StarCitizen-Localization`)
- 🇧🇷 **Portugués** (Português Brasil - `Dymerz/StarCitizen-Localization`)
- 🇹🇷 **Turco** (Türkçe - `Dymerz/StarCitizen-Localization`)
- 🇬🇧 **Inglés Original** (Cloud Imperium Games - Restaura textos originales)

### 5. 🔒 Control de Activación Exclusiva y Caché Local
- **Única Traducción Activa:** Al activar cualquier traducción, el gestor quita automáticamente la extensión `.ini` a todos los demás archivos en `\data\Localization\` para evitar conflictos, dejando con extensión `.ini` únicamente la traducción seleccionada y configurando `user.cfg` (`g_language` y `g_languageAudio = english`).
- **Caché Local (`translations_cache/`):** Almacena las traducciones y sus metadatos localmente para alternar entre idiomas o restaurar versiones limpias al instante sin re-descargar.
- **Desactivar Traducción:** Quita la extensión `.ini` a todos los archivos de localización y comenta `g_language` en `user.cfg` para que el juego cargue 100% en inglés original de fábrica.

### 6. 🌍 Interfaz Multilingüe (i18n)
- Selector de idioma en la barra superior para cambiar en tiempo real el idioma de toda la aplicación:
  - 🇪🇸 Español | 🇺🇸 English | 🇩🇪 Deutsch | 🇫🇷 Français | 🇨🇳 简体中文 | 🇷🇺 Русский | 🇧🇷 Português | 🇮🇹 Italiano

### 7. 🚀 Lanzador Directo del Juego
- Botón integrado **"🚀 INICIAR LAUNCHER DEL JUEGO"** que detecta y ejecuta automáticamente el **RSI Launcher oficial** (`RSI Launcher.exe`).

---

## 🛠️ Requisitos e Instalación desde Código Fuente

- **Sistema Operativo:** Windows 10 / 11
- **Python:** 3.10 o superior
- **Dependencias:**
  - `customtkinter>=6.0.0`
  - `requests>=2.31.0`
  - `pillow>=10.0.0`

```bash
pip install -r requirements.txt
```

---

## 🎮 Cómo Ejecutarlo

1. **Ejecutable Independiente (`SCcommunityupdate.exe`):**
   - Doble clic en `SCcommunityupdate.exe` (incluido en el proyecto o en la sección de *Releases*). No requiere tener Python instalado ni abre ventanas de consola.
2. **Scripts de Inicio Rápido:**
   - `iniciar_sin_consola.vbs`: Ejecuta la aplicación con Python en segundo plano sin ventana de comandos.
   - `iniciar_launcher.bat`: Inicia el launcher mostrando la salida de diagnóstico en consola.
3. **Desde Terminal:**
   ```bash
   python main.py
   ```

---

## 🏗️ Compilar Ejecutable (`.exe`)

Si deseas compilar tu propio ejecutable con PyInstaller:

```bash
pyinstaller SCcommunityupdate.spec --clean
```
