"""
Módulo de Gestión de Configuración para Star Citizen Launcher.
Guarda y carga las preferencias del usuario, la ruta del juego y la lista de repositorios.
"""

import os
import sys
import json
from typing import List, Dict, Optional, Any

CONFIG_FILE_NAME = "config.json"

OFFICIAL_LANGUAGES: Dict[str, Dict[str, Any]] = {
    "🇪🇸 Español (Comunidad Hispana)": {
        "id": "thord82-es",
        "lang_code": "es",
        "name": "Español (Comunidad Hispana)",
        "author": "Thord82",
        "url": "https://github.com/Thord82/Star_citizen_ES",
        "raw_url": "https://raw.githubusercontent.com/Thord82/Star_citizen_ES/main/global.ini",
        "description": "Traducción completa al español de España y Latinoamérica para Star Citizen."
    },
    "🇩🇪 Alemán (Deutsch)": {
        "id": "official-de",
        "lang_code": "de",
        "name": "Alemán (Deutsch)",
        "author": "rjcncpt",
        "url": "https://github.com/rjcncpt/StarCitizen-Deutsch-INI",
        "raw_url": "https://raw.githubusercontent.com/rjcncpt/StarCitizen-Deutsch-INI/main/live/global.ini",
        "description": "Traducción oficial de la comunidad alemana adaptada para LIVE."
    },
    "🇫🇷 Francés (Français)": {
        "id": "official-fr",
        "lang_code": "fr",
        "name": "Francés (Français)",
        "author": "Dymerz / SC-FR",
        "url": "https://github.com/Dymerz/StarCitizen-Localization/blob/main/data/Localization/french_(france)/global.ini",
        "raw_url": "https://raw.githubusercontent.com/Dymerz/StarCitizen-Localization/main/data/Localization/french_(france)/global.ini",
        "description": "Traducción oficial de la comunidad francesa (Star Citizen Traduction FR)."
    },
    "🇨🇳 Chino Tradicional (繁體中文)": {
        "id": "official-zh",
        "lang_code": "zh",
        "name": "Chino Tradicional (繁體中文)",
        "author": "Orbit-Startech (TCTP)",
        "url": "https://github.com/Orbit-Startech/StarCitizen-TCTP",
        "raw_url": "https://raw.githubusercontent.com/Orbit-Startech/StarCitizen-TCTP/main/chinese_(traditional)/global.ini",
        "description": "Proyecto TCTP de localización al chino tradicional."
    },
    "🇷🇺 Ruso (Русский)": {
        "id": "official-ru",
        "lang_code": "ru",
        "name": "Ruso (Русский)",
        "author": "n1ghter",
        "url": "https://github.com/n1ghter/StarCitizenRu",
        "raw_url": "https://raw.githubusercontent.com/n1ghter/StarCitizenRu/master/data/Localization/korean_(south_korea)/global.ini",
        "description": "Traducción de la comunidad rusa (StarCitizenRu)."
    },
    "🇮🇹 Italiano": {
        "id": "official-it",
        "lang_code": "it",
        "name": "Italiano",
        "author": "Dymerz / SC-IT",
        "url": "https://github.com/Dymerz/StarCitizen-Localization/blob/main/data/Localization/italian_(italy)/global.ini",
        "raw_url": "https://raw.githubusercontent.com/Dymerz/StarCitizen-Localization/main/data/Localization/italian_(italy)/global.ini",
        "description": "Traducción de la comunidad italiana."
    },
    "🇧🇷 Portugués (Português)": {
        "id": "official-pt",
        "lang_code": "pt",
        "name": "Portugués (Português - Brasil)",
        "author": "Dymerz / SC-PTBR",
        "url": "https://github.com/Dymerz/StarCitizen-Localization/blob/main/data/Localization/portuguese_(brazil)/global.ini",
        "raw_url": "https://raw.githubusercontent.com/Dymerz/StarCitizen-Localization/main/data/Localization/portuguese_(brazil)/global.ini",
        "description": "Traducción de la comunidad brasileña y portuguesa."
    },
    "🇹🇷 Turco (Türkçe)": {
        "id": "official-tr",
        "lang_code": "tr",
        "name": "Turco (Türkçe)",
        "author": "Dymerz / SC-TR",
        "url": "https://github.com/Dymerz/StarCitizen-Localization/blob/main/data/Localization/turkish_(turkey)/global.ini",
        "raw_url": "https://raw.githubusercontent.com/Dymerz/StarCitizen-Localization/main/data/Localization/turkish_(turkey)/global.ini",
        "description": "Traducción de la comunidad turca."
    },
    "🇬🇧 Inglés Original (Sin traducción)": {
        "id": "official-en",
        "lang_code": "en_original",
        "name": "Inglés Original (Predeterminado)",
        "author": "Cloud Imperium Games",
        "url": "",
        "raw_url": "",
        "description": "Textos originales del juego en inglés sin ninguna traducción externa aplicada."
    }
}

DEFAULT_TOOLS: List[Dict[str, Any]] = [
    {
        "id": "starstrings",
        "name": "StarStrings (MrKraken)",
        "url": "https://github.com/MrKraken/StarStrings",
        "raw_url": "https://raw.githubusercontent.com/MrKraken/StarStrings/master/src/For_Players/Data/Localization/english/global.ini",
        "releases_url": "https://github.com/MrKraken/StarStrings/releases",
        "description": "Mod QoL de textos que destaca recompensas [BP] (Blueprints) en misiones, clasifica componentes y mejora nombres en mobiGlas.",
        "is_string_mod": True,
        "last_updated": None
    },
    {
        "id": "starmeld",
        "name": "StarMeld (Fusionador de Traducciones)",
        "url": "https://github.com/dydx/StarMeld",
        "raw_url": "",
        "releases_url": "https://github.com/dydx/StarMeld/releases",
        "description": "Herramienta comunitaria para fusionar varios archivos global.ini (ej. traducción al español + StarStrings) en uno solo.",
        "is_string_mod": False,
        "last_updated": None
    }
]

DEFAULT_CONFIG: Dict[str, Any] = {
    "app_language": "es",
    "live_path": "",
    "active_repo_id": "thord82-es",
    "sync_english_folder": True,
    "repositories": [
        {
            "id": "thord82-es",
            "name": "Comunidad Hispana (Thord82)",
            "url": "https://github.com/Thord82/Star_citizen_ES",
            "raw_url": "https://raw.githubusercontent.com/Thord82/Star_citizen_ES/main/global.ini",
            "last_updated": None,
            "description": "Traducción comunitaria al español de España y Latinoamérica para Star Citizen."
        }
    ],
    "tools": DEFAULT_TOOLS
}


class ConfigManager:
    """Administra la persistencia de configuraciones en un archivo JSON local."""

    def __init__(self, base_dir: Optional[str] = None):
        if base_dir is None:
            if getattr(sys, "frozen", False):
                base_dir = os.path.dirname(sys.executable)
            else:
                base_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_path = os.path.join(base_dir, CONFIG_FILE_NAME)
        self.data: Dict[str, Any] = {}
        self.load()

    def load(self) -> None:
        """Carga la configuración desde el disco o crea una por defecto si no existe."""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    self.data = DEFAULT_CONFIG.copy()
                    self.data.update(loaded)
                    # Asegurar que repositorios existe y es una lista
                    if "repositories" not in self.data or not isinstance(self.data["repositories"], list):
                        self.data["repositories"] = DEFAULT_CONFIG["repositories"].copy()
                    # Asegurar que tools existe y es una lista
                    if "tools" not in self.data or not isinstance(self.data["tools"], list):
                        self.data["tools"] = DEFAULT_TOOLS.copy()
                    return
            except Exception as e:
                print(f"[ConfigManager] Error leyendo configuración: {e}. Restaurando valores por defecto.")
        
        self.data = DEFAULT_CONFIG.copy()
        self.save()

    def save(self) -> None:
        """Guarda la configuración actual en el disco."""
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"[ConfigManager] Error guardando configuración: {e}")

    def get_live_path(self) -> str:
        """Obtiene la ruta guardada de Star Citizen LIVE."""
        return self.data.get("live_path", "")

    def set_live_path(self, path: str) -> None:
        """Actualiza y guarda la ruta de Star Citizen LIVE."""
        self.data["live_path"] = path.strip()
        self.save()

    def get_repositories(self) -> List[Dict[str, Any]]:
        """Devuelve la lista de repositorios configurados."""
        return self.data.get("repositories", [])

    def add_repository(self, name: str, url: str, raw_url: str, description: str = "") -> Dict[str, Any]:
        """Añade un nuevo repositorio a la lista y guarda."""
        import uuid
        repo_id = str(uuid.uuid4())[:8]
        new_repo = {
            "id": repo_id,
            "name": name.strip(),
            "url": url.strip(),
            "raw_url": raw_url.strip(),
            "last_updated": None,
            "description": description.strip()
        }
        self.data.setdefault("repositories", []).append(new_repo)
        self.save()
        return new_repo

    def remove_repository(self, repo_id: str) -> bool:
        """Elimina un repositorio por su ID."""
        repos = self.data.get("repositories", [])
        initial_len = len(repos)
        self.data["repositories"] = [r for r in repos if r.get("id") != repo_id]
        if len(self.data["repositories"]) < initial_len:
            self.save()
            return True
        return False

    def update_repository_timestamp(self, repo_id: str, timestamp_str: str) -> None:
        """Actualiza la fecha de última actualización de un repositorio."""
        for repo in self.data.get("repositories", []):
            if repo.get("id") == repo_id:
                repo["last_updated"] = timestamp_str
                break
        self.save()

    def update_repository_raw_url(self, repo_id: str, raw_url: str) -> None:
        """Actualiza la URL raw directa de descarga de un repositorio."""
        for repo in self.data.get("repositories", []):
            if repo.get("id") == repo_id:
                repo["raw_url"] = raw_url
                break
        self.save()

    def load_all_official_languages(self) -> int:
        """Carga todas las traducciones oficiales en la lista de repositorios si no existen ya."""
        repos = self.data.setdefault("repositories", [])
        existing_urls = {r.get("url", "").lower().strip() for r in repos if r.get("url")}
        existing_names = {r.get("name", "").lower().strip() for r in repos if r.get("name")}
        added_count = 0

        for key, info in OFFICIAL_LANGUAGES.items():
            if not info.get("url"):
                continue  # Saltar Inglés Original
            
            url_clean = info["url"].lower().strip()
            name_clean = info["name"].lower().strip()

            if url_clean not in existing_urls and name_clean not in existing_names:
                new_entry = {
                    "id": info["id"],
                    "name": info["name"],
                    "url": info["url"],
                    "raw_url": info["raw_url"],
                    "last_updated": None,
                    "description": info["description"]
                }
                repos.append(new_entry)
                existing_urls.add(url_clean)
                existing_names.add(name_clean)
                added_count += 1

        if added_count > 0:
            self.save()
        return added_count

    def get_active_repo_id(self) -> Optional[str]:
        return self.data.get("active_repo_id")

    def set_active_repo_id(self, repo_id: str) -> None:
        self.data["active_repo_id"] = repo_id
        self.save()

    def is_starstrings_merged(self) -> bool:
        """Indica si StarStrings está actualmente fusionado sobre la traducción activa."""
        return bool(self.data.get("starstrings_merged_into"))

    def set_starstrings_merged_into(self, repo_id: Optional[str]) -> None:
        """Establece qué ID de repositorio tiene StarStrings fusionado encima (o None si no está fusionado)."""
        self.data["starstrings_merged_into"] = repo_id
        self.save()

    def get_starstrings_merged_into(self) -> Optional[str]:
        return self.data.get("starstrings_merged_into")

    def get_tools(self) -> List[Dict[str, Any]]:
        """Devuelve la lista de herramientas configuradas."""
        return self.data.get("tools", [])

    def add_tool(
        self,
        name: str,
        url: str,
        description: str = "",
        raw_url: str = "",
        releases_url: str = "",
        is_string_mod: bool = False
    ) -> Dict[str, Any]:
        """Añade una nueva herramienta a la lista y guarda."""
        import uuid
        tool_id = str(uuid.uuid4())[:8]
        new_tool = {
            "id": tool_id,
            "name": name.strip(),
            "url": url.strip(),
            "raw_url": raw_url.strip(),
            "releases_url": releases_url.strip() or f"{url.rstrip('/')}/releases",
            "description": description.strip(),
            "is_string_mod": is_string_mod,
            "last_updated": None
        }
        self.data.setdefault("tools", []).append(new_tool)
        self.save()
        return new_tool

    def remove_tool(self, tool_id: str) -> bool:
        """Elimina una herramienta por su ID."""
        tools = self.data.get("tools", [])
        initial_len = len(tools)
        self.data["tools"] = [t for t in tools if t.get("id") != tool_id]
        if len(self.data["tools"]) < initial_len:
            self.save()
            return True
        return False

    def update_tool_timestamp(self, tool_id: str, timestamp_str: str) -> None:
        """Actualiza la fecha de última actualización de una herramienta."""
        for tool in self.data.get("tools", []):
            if tool.get("id") == tool_id:
                tool["last_updated"] = timestamp_str
                break
        self.save()

    def get_app_language(self) -> str:
        """Obtiene el idioma configurado para la interfaz del launcher (por defecto 'es')."""
        return self.data.get("app_language", "es")

    def set_app_language(self, lang_code: str) -> None:
        """Establece y guarda el idioma de la interfaz del launcher."""
        self.data["app_language"] = lang_code.strip()
        self.save()
