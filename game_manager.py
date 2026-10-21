"""
Módulo de Gestión de Star Citizen.
Maneja la detección de rutas, descarga de traducciones, edición de user.cfg y ejecución del juego.
"""

import os
import re
import io
import sys
import json
import shutil
import string
import zipfile
import subprocess
from datetime import datetime
from typing import Optional, Tuple, Callable, Dict, Any
import requests


def get_translations_cache_dir() -> str:
    """Retorna la ruta al directorio local de caché de traducciones."""
    if getattr(sys, "frozen", False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    cache_dir = os.path.join(base_dir, "translations_cache")
    os.makedirs(cache_dir, exist_ok=True)
    return cache_dir


class StarCitizenManager:
    """Gestiona la interacción con los archivos y procesos de Star Citizen."""

    DEFAULT_SUBPATH = os.path.join("Roberts Space Industries", "StarCitizen", "LIVE")

    @staticmethod
    def is_valid_live_directory(path: str) -> bool:
        """Comprueba si una ruta dada es un directorio válido de Star Citizen LIVE."""
        if not path or not os.path.isdir(path):
            return False

        # Comprobar presencia de ejecutables típicos o estructura del juego
        exe1 = os.path.join(path, "Bin64", "StarCitizen.exe")
        exe2 = os.path.join(path, "StarCitizen.exe")
        p4k = os.path.join(path, "Data.p4k")
        manifest = os.path.join(path, "build_manifest.id")

        return os.path.isfile(exe1) or os.path.isfile(exe2) or os.path.isfile(p4k) or os.path.isfile(manifest)

    @classmethod
    def get_executable_path(cls, live_path: str) -> Optional[str]:
        """Obtiene la ruta completa al ejecutable StarCitizen.exe."""
        if not live_path or not os.path.isdir(live_path):
            return None

        candidates = [
            os.path.join(live_path, "Bin64", "StarCitizen.exe"),
            os.path.join(live_path, "StarCitizen.exe"),
            os.path.join(live_path, "StarCitizen_Launcher.exe")
        ]
        for c in candidates:
            if os.path.isfile(c):
                return c
        return None

    @classmethod
    def auto_detect_live_directory(cls) -> Optional[str]:
        """
        Escanea automáticamente unidades de almacenamiento y rutas conocidas de Star Citizen.
        Retorna la ruta hacia la carpeta LIVE si la encuentra.
        """
        # 1. Obtener letras de unidad disponibles en Windows
        available_drives = []
        for letter in string.ascii_uppercase:
            drive_root = f"{letter}:\\"
            if os.path.exists(drive_root):
                available_drives.append(drive_root)

        # 2. Rutas candidatas comunes
        subpaths = [
            os.path.join("Program Files", "Roberts Space Industries", "StarCitizen", "LIVE"),
            os.path.join("Program Files (x86)", "Roberts Space Industries", "StarCitizen", "LIVE"),
            os.path.join("Roberts Space Industries", "StarCitizen", "LIVE"),
            os.path.join("Games", "Roberts Space Industries", "StarCitizen", "LIVE"),
            os.path.join("Juegos", "Roberts Space Industries", "StarCitizen", "LIVE"),
            os.path.join("RSI", "StarCitizen", "LIVE"),
            os.path.join("StarCitizen", "LIVE")
        ]

        for drive in available_drives:
            for sub in subpaths:
                candidate = os.path.join(drive, sub)
                if cls.is_valid_live_directory(candidate):
                    return os.path.normpath(candidate)

        # 3. Intentar consultar configuración de RSI Launcher si existe
        appdata = os.environ.get("APPDATA")
        if appdata:
            rsi_log_dir = os.path.join(appdata, "rsilauncher", "logs")
            if os.path.isdir(rsi_log_dir):
                try:
                    for log_file in os.listdir(rsi_log_dir):
                        if log_file.endswith(".log"):
                            full_log = os.path.join(rsi_log_dir, log_file)
                            with open(full_log, "r", encoding="utf-8", errors="ignore") as lf:
                                for line in lf:
                                    if "StarCitizen" in line and "LIVE" in line:
                                        match = re.search(r'([A-Za-z]:\\[^"\'\r\n]+?StarCitizen\\LIVE)', line)
                                        if match:
                                            cand = match.group(1)
                                            if cls.is_valid_live_directory(cand):
                                                return os.path.normpath(cand)
                except Exception:
                    pass

        return None

    @staticmethod
    def get_user_cfg_path(live_path: str) -> str:
        """Obtiene la ruta a user.cfg respetando mayúsculas/minúsculas existentes si ya existe."""
        for name in ["user.cfg", "USER.cfg", "User.cfg"]:
            candidate = os.path.join(live_path, name)
            if os.path.exists(candidate):
                return candidate
        return os.path.join(live_path, "user.cfg")

    @classmethod
    def get_user_cfg_language(cls, live_path: str) -> Optional[str]:
        """Lee el valor configurado para g_language en el user.cfg actual."""
        cfg_path = cls.get_user_cfg_path(live_path)
        if not os.path.isfile(cfg_path):
            return None

        try:
            with open(cfg_path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    stripped = line.strip()
                    if stripped.startswith(";") or stripped.startswith("--") or stripped.startswith("//"):
                        continue
                    match = re.match(r"^g_language\s*=\s*(.+)$", stripped, re.IGNORECASE)
                    if match:
                        return match.group(1).strip()
        except Exception as e:
            print(f"[StarCitizenManager] Error leyendo user.cfg: {e}")
        return None

    @classmethod
    def set_user_cfg_language(cls, live_path: str, lang: str = "en") -> Tuple[bool, str]:
        """
        Asegura que el archivo user.cfg en la raíz de LIVE contenga 'g_language = {lang}'
        y 'g_languageAudio = english'.
        Crea el archivo si no existe, o reemplaza/agrega la directiva preservando el resto de líneas.
        """
        if not os.path.isdir(live_path):
            return False, f"La carpeta LIVE '{live_path}' no existe."

        cfg_path = cls.get_user_cfg_path(live_path)
        new_lines = []
        found_lang = False
        found_audio = False
        target_lang = f"g_language = {lang}"
        target_audio = "g_languageAudio = english"

        if os.path.isfile(cfg_path):
            try:
                with open(cfg_path, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()

                for line in lines:
                    stripped = line.strip()
                    if re.match(r"^;?\s*g_language\s*=", stripped, re.IGNORECASE):
                        new_lines.append(target_lang + "\n")
                        found_lang = True
                    elif re.match(r"^;?\s*g_languageAudio\s*=", stripped, re.IGNORECASE):
                        new_lines.append(target_audio + "\n")
                        found_audio = True
                    else:
                        new_lines.append(line)
            except Exception as e:
                return False, f"Error al leer user.cfg existente: {e}"

        if not found_lang:
            if new_lines and not new_lines[-1].endswith("\n"):
                new_lines.append("\n")
            new_lines.append(target_lang + "\n")

        if not found_audio:
            new_lines.append(target_audio + "\n")

        try:
            with open(cfg_path, "w", encoding="utf-8") as f:
                f.writelines(new_lines)
            return True, f"user.cfg actualizado con '{target_lang}'"
        except Exception as e:
            return False, f"Error al escribir en user.cfg: {e}"

    @classmethod
    def remove_user_cfg_language(cls, live_path: str) -> Tuple[bool, str]:
        """Desactiva o comenta la directiva g_language en user.cfg."""
        cfg_path = cls.get_user_cfg_path(live_path)
        if not os.path.isfile(cfg_path):
            return True, "user.cfg no existía."

        try:
            with open(cfg_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()

            new_lines = []
            for line in lines:
                stripped = line.strip()
                if re.match(r"^g_language\s*=", stripped, re.IGNORECASE):
                    new_lines.append(f"; {line}")  # Comentar
                else:
                    new_lines.append(line)

            with open(cfg_path, "w", encoding="utf-8") as f:
                f.writelines(new_lines)
            return True, "Traducción desactivada en user.cfg."
        except Exception as e:
            return False, f"Error al actualizar user.cfg: {e}"

    @classmethod
    def get_cache_path(cls, repo_id: str) -> str:
        """Obtiene la ruta local en disco para un archivo de traducción en caché."""
        clean_id = re.sub(r'[^\w\-_\.]', '_', repo_id)
        return os.path.join(get_translations_cache_dir(), f"{clean_id}.ini")

    @classmethod
    def get_cache_meta_path(cls, repo_id: str) -> str:
        """Obtiene la ruta local en disco para los metadatos de una traducción en caché."""
        clean_id = re.sub(r'[^\w\-_\.]', '_', repo_id)
        return os.path.join(get_translations_cache_dir(), f"{clean_id}.meta.json")

    @classmethod
    def save_cache_meta(cls, repo_id: str, meta: dict) -> None:
        """Guarda metadatos de configuración (lang_code, subfolder) en disco."""
        try:
            with open(cls.get_cache_meta_path(repo_id), "w", encoding="utf-8") as f:
                json.dump(meta, f)
        except Exception:
            pass

    @classmethod
    def get_cache_meta(cls, repo_id: str) -> dict:
        """Lee los metadatos almacenados para una traducción."""
        path = cls.get_cache_meta_path(repo_id)
        if os.path.isfile(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    @classmethod
    def is_cached(cls, repo_id: str) -> bool:
        """Comprueba si una traducción ya fue descargada y está en el caché local."""
        path = cls.get_cache_path(repo_id)
        return os.path.isfile(path) and os.path.getsize(path) > 100

    @classmethod
    def save_to_cache(cls, repo_id: str, content_bytes: bytes) -> str:
        """Guarda los bytes de una traducción en el caché local."""
        cache_path = cls.get_cache_path(repo_id)
        with open(cache_path, "wb") as f:
            f.write(content_bytes)
        return cache_path

    @classmethod
    def get_cached_bytes(cls, repo_id: str) -> Optional[bytes]:
        """Obtiene los bytes de una traducción almacenada en el caché local."""
        cache_path = cls.get_cache_path(repo_id)
        if os.path.isfile(cache_path):
            try:
                with open(cache_path, "rb") as f:
                    return f.read()
            except Exception:
                return None
        return None

    @classmethod
    def strip_all_ini_extensions(cls, live_path: str) -> int:
        r"""
        Quita la extensión .ini (y .ini.bak) a TODOS los archivos de traducción en toda
        la carpeta \data\Localization\ y sus subdirectorios.
        Renombra cualquier 'global.ini' a 'global' (sin extensión) y cualquier '*.ini' a '*' sin extensión.
        Garantiza que NINGUNA traducción quede activa ni con extensión en el motor del juego.
        """
        if not cls.is_valid_live_directory(live_path):
            return 0

        loc_dir = os.path.join(live_path, "data", "Localization")
        if not os.path.isdir(loc_dir):
            return 0

        stripped_count = 0
        try:
            for root, dirs, files in os.walk(loc_dir):
                if ".cache" in root:
                    continue
                for f in files:
                    lower_f = f.lower()
                    full_path = os.path.join(root, f)

                    if lower_f.endswith(".ini"):
                        name_no_ext = f[:-4]
                        target_path = os.path.join(root, name_no_ext)
                        if os.path.exists(target_path):
                            try:
                                os.remove(target_path)
                            except Exception:
                                pass
                        os.replace(full_path, target_path)
                        stripped_count += 1
                    elif lower_f.endswith(".ini.bak"):
                        name_no_ext = f[:-8] + ".bak"
                        target_path = os.path.join(root, name_no_ext)
                        if os.path.exists(target_path):
                            try:
                                os.remove(target_path)
                            except Exception:
                                pass
                        os.replace(full_path, target_path)
                        stripped_count += 1
        except Exception as e:
            print(f"[StarCitizenManager] Error al quitar extensiones en {loc_dir}: {e}")

        return stripped_count

    @classmethod
    def disable_translation(cls, live_path: str) -> Tuple[bool, str]:
        """
        Desactiva la traducción quitando la extensión a TODOS los archivos en Localization.
        Comenta la directiva g_language en user.cfg para que el juego corra en inglés original.
        """
        if not cls.is_valid_live_directory(live_path):
            return False, f"La carpeta de Star Citizen no es válida: {live_path}"

        count = cls.strip_all_ini_extensions(live_path)
        cls.remove_user_cfg_language(live_path)
        return True, f"Traducción desactivada: Se quitaron todas las extensiones ({count} archivo(s) renombrados sin .ini) y se actualizó user.cfg."

    @classmethod
    def activate_translation(
        cls,
        live_path: str,
        repo_id: str,
        content_bytes: Optional[bytes] = None,
        subfolder: Optional[str] = None,
        lang_code: Optional[str] = None,
        sync_english: bool = True
    ) -> Tuple[bool, str]:
        r"""
        Activa una traducción asegurando que sea la ÚNICA activa en el juego:
        1. Quita la extensión .ini a TODOS los archivos en \data\Localization\ (desactivando cualquier otra).
        2. Obtiene los bytes de la traducción seleccionada (del parámetro o del caché local).
        3. Instala con extensión .ini ÚNICAMENTE el archivo seleccionado en \en\global.ini,
           \english\global.ini y en \{subfolder}\global.ini si corresponde.
        4. Configura g_language = {lang_code} en user.cfg.
        """
        if not cls.is_valid_live_directory(live_path):
            return False, f"La carpeta de Star Citizen no es válida: {live_path}"

        # 1. Quitar todas las extensiones a todos los archivos existentes
        stripped_count = cls.strip_all_ini_extensions(live_path)

        # 2. Obtener bytes de la traducción elegida
        if content_bytes is None:
            content_bytes = cls.get_cached_bytes(repo_id)

        if not content_bytes:
            return False, f"No se encontró el archivo de traducción para '{repo_id}' en caché local. Por favor descárgala primero."

        # Guardar en caché local
        cls.save_to_cache(repo_id, content_bytes)

        # Recuperar o actualizar metadatos
        meta = cls.get_cache_meta(repo_id)
        if lang_code is None:
            lang_code = meta.get("lang_code", "en")
        if subfolder is None:
            subfolder = meta.get("subfolder")

        cls.save_cache_meta(repo_id, {"lang_code": lang_code, "subfolder": subfolder})

        # 3. Escribir únicamente la traducción seleccionada con extensión .ini en \en\
        target_dir_en = os.path.join(live_path, "data", "Localization", "en")
        os.makedirs(target_dir_en, exist_ok=True)
        target_file_en = os.path.join(target_dir_en, "global.ini")
        with open(target_file_en, "wb") as f:
            f.write(content_bytes)

        # Limpiar cualquier archivo 'global' residual sin extensión en \en\
        old_no_ext_en = os.path.join(target_dir_en, "global")
        if os.path.isfile(old_no_ext_en):
            try:
                os.remove(old_no_ext_en)
            except Exception:
                pass

        # Sincronizar con \english\
        if sync_english:
            target_dir_english = os.path.join(live_path, "data", "Localization", "english")
            os.makedirs(target_dir_english, exist_ok=True)
            target_file_english = os.path.join(target_dir_english, "global.ini")
            with open(target_file_english, "wb") as f:
                f.write(content_bytes)
            old_no_ext_eng = os.path.join(target_dir_english, "global")
            if os.path.isfile(old_no_ext_eng):
                try:
                    os.remove(old_no_ext_eng)
                except Exception:
                    pass

        # Escribir en subcarpeta específica si corresponde (ej. spanish_(spain) o german_(germany))
        if subfolder and subfolder.lower() not in ["en", "english"]:
            target_dir_sub = os.path.join(live_path, "data", "Localization", subfolder)
            os.makedirs(target_dir_sub, exist_ok=True)
            target_file_sub = os.path.join(target_dir_sub, "global.ini")
            with open(target_file_sub, "wb") as f:
                f.write(content_bytes)
            old_no_ext_sub = os.path.join(target_dir_sub, "global")
            if os.path.isfile(old_no_ext_sub):
                try:
                    os.remove(old_no_ext_sub)
                except Exception:
                    pass

        # 4. Configurar user.cfg
        ok_cfg, msg_cfg = cls.set_user_cfg_language(live_path, lang_code)
        if not ok_cfg:
            return False, f"Se instaló global.ini pero falló user.cfg: {msg_cfg}"

        return True, f"Traducción activada como la única activa: Se quitaron todas las extensiones previas ({stripped_count} archivos) y se activó global.ini en user.cfg con 'g_language = {lang_code}'."

    @classmethod
    def enable_translation(cls, live_path: str, repo_id: Optional[str] = None, lang: str = "en") -> Tuple[bool, str]:
        r"""
        Activa la traducción. Si se proporciona repo_id o está en caché, usa activate_translation.
        De lo contrario, regresa la extensión a 'global' -> 'global.ini' en \en\ y \english\.
        """
        if repo_id and cls.is_cached(repo_id):
            return cls.activate_translation(live_path, repo_id)

        if not cls.is_valid_live_directory(live_path):
            return False, f"La carpeta de Star Citizen no es válida: {live_path}"

        loc_dir = os.path.join(live_path, "data", "Localization")
        restored_count = 0
        if os.path.isdir(loc_dir):
            for sub in os.listdir(loc_dir):
                sub_path = os.path.join(loc_dir, sub)
                if os.path.isdir(sub_path):
                    ini_file = os.path.join(sub_path, "global.ini")
                    no_ext_file = os.path.join(sub_path, "global")
                    if os.path.isfile(no_ext_file) and not os.path.isfile(ini_file):
                        os.rename(no_ext_file, ini_file)
                        restored_count += 1

        cls.set_user_cfg_language(live_path, lang)
        return True, f"Traducción activada (.ini restaurado) y user.cfg configurado con 'g_language = {lang}'."

    @classmethod
    def get_translation_status(cls, live_path: str) -> Dict[str, Any]:
        """
        Comprueba el estado detallado de la traducción en el directorio del juego.
        """
        if not cls.is_valid_live_directory(live_path):
            return {"active": False, "has_ini": False, "has_no_ext": False, "cfg_lang": None}

        loc_dir = os.path.join(live_path, "data", "Localization")
        has_ini = False
        has_no_ext = False

        if os.path.isdir(loc_dir):
            for sub in os.listdir(loc_dir):
                sub_path = os.path.join(loc_dir, sub)
                if os.path.isdir(sub_path):
                    if os.path.isfile(os.path.join(sub_path, "global.ini")):
                        has_ini = True
                    if os.path.isfile(os.path.join(sub_path, "global")):
                        has_no_ext = True

        cfg_lang = cls.get_user_cfg_language(live_path)
        is_active = has_ini and bool(cfg_lang)

        return {
            "active": is_active,
            "has_ini": has_ini,
            "has_no_ext": has_no_ext,
            "cfg_lang": cfg_lang
        }

    @staticmethod
    def resolve_github_raw_url(url: str) -> Tuple[bool, str, Optional[str]]:
        """
        Dada una URL de repositorio GitHub o un enlace raw, resuelve la URL directa al archivo global.ini.
        Utiliza comprobaciones de rutas comunes y búsqueda recursiva en el árbol de GitHub API si es necesario.
        """
        url = url.strip()
        if not url:
            return False, "", "La URL proporcionada está vacía."

        headers = {"User-Agent": "StarCitizen-Launcher-Tool/1.0"}

        # 1. Si ya es una URL raw directa a un archivo .ini
        if "raw.githubusercontent.com" in url and url.lower().endswith(".ini"):
            try:
                resp = requests.head(url, timeout=4, headers=headers, allow_redirects=True)
                if resp.status_code == 200:
                    return True, url, None
            except Exception:
                pass

        # 2. Si es un enlace de GitHub blob
        blob_match = re.match(r"https?://github\.com/([^/]+)/([^/]+)/blob/([^/]+)/(.+)", url)
        if blob_match:
            owner, repo, branch, path = blob_match.groups()
            raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}"
            try:
                resp = requests.head(raw_url, timeout=4, headers=headers, allow_redirects=True)
                if resp.status_code == 200:
                    return True, raw_url, None
            except Exception:
                pass

        # 3. Extraer owner y repo
        owner = None
        repo = None
        raw_match = re.match(r"https?://raw\.githubusercontent\.com/([^/]+)/([^/]+)/?", url)
        if raw_match:
            owner, repo = raw_match.group(1), raw_match.group(2)
        else:
            repo_match = re.match(r"https?://github\.com/([^/]+)/([^/]+?)(?:\.git)?(?:/.*)?$", url)
            if repo_match:
                owner, repo = repo_match.group(1), repo_match.group(2)

        if not owner or not repo:
            return True, url, None

        # 4. Lista de rutas comunes donde se almacena global.ini en repositorios de Star Citizen
        candidates = [
            f"https://raw.githubusercontent.com/{owner}/{repo}/main/global.ini",
            f"https://raw.githubusercontent.com/{owner}/{repo}/master/global.ini",
            f"https://raw.githubusercontent.com/{owner}/{repo}/main/live/global.ini",
            f"https://raw.githubusercontent.com/{owner}/{repo}/master/live/global.ini",
            f"https://raw.githubusercontent.com/{owner}/{repo}/main/LIVE/global.ini",
            f"https://raw.githubusercontent.com/{owner}/{repo}/master/LIVE/global.ini",
            f"https://raw.githubusercontent.com/{owner}/{repo}/master/src/For_Players/Data/Localization/english/global.ini",
            f"https://raw.githubusercontent.com/{owner}/{repo}/main/src/For_Players/Data/Localization/english/global.ini",
            f"https://raw.githubusercontent.com/{owner}/{repo}/main/data/Localization/spanish_(spain)/global.ini",
            f"https://raw.githubusercontent.com/{owner}/{repo}/master/data/Localization/spanish_(spain)/global.ini",
            f"https://raw.githubusercontent.com/{owner}/{repo}/main/data/Localization/en/global.ini",
            f"https://raw.githubusercontent.com/{owner}/{repo}/master/data/Localization/en/global.ini",
            f"https://raw.githubusercontent.com/{owner}/{repo}/main/data/Localization/english/global.ini",
            f"https://raw.githubusercontent.com/{owner}/{repo}/master/data/Localization/english/global.ini"
        ]

        for cand in candidates:
            try:
                resp = requests.head(cand, timeout=3, headers=headers, allow_redirects=True)
                if resp.status_code == 200:
                    return True, cand, None
            except Exception:
                continue

        # 5. Búsqueda profunda con la API de GitHub para repositorios con estructuras atípicas
        try:
            r_repo = requests.get(f"https://api.github.com/repos/{owner}/{repo}", timeout=5, headers=headers)
            branch = r_repo.json().get("default_branch", "main") if r_repo.status_code == 200 else "main"

            r_tree = requests.get(f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1", timeout=6, headers=headers)
            if r_tree.status_code == 200:
                tree = r_tree.json().get("tree", [])
                ini_paths = [item["path"] for item in tree if item.get("type") == "blob" and item["path"].lower().endswith(".ini")]

                best_path = None
                for p in ini_paths:
                    p_lower = p.lower()
                    if "live/global.ini" in p_lower:
                        best_path = p
                        break
                    elif p_lower.endswith("global.ini") and not best_path:
                        best_path = p
                    elif not best_path:
                        best_path = p

                if best_path:
                    found_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{best_path}"
                    return True, found_url, None
        except Exception:
            pass

        # Fallback
        fallback = f"https://raw.githubusercontent.com/{owner}/{repo}/main/global.ini"
        return False, fallback, "No se pudo verificar disponibilidad previa de global.ini."

    @classmethod
    def fetch_latest_translation(
        cls,
        repo_url_or_raw: str,
        progress_callback: Optional[Callable[[str, float], None]] = None
    ) -> Tuple[bool, Optional[bytes], str, Optional[str], Optional[str]]:
        r"""
        Descarga la traducción más reciente:
        1. Comprueba si el repositorio de GitHub tiene un Release reciente con archivo .zip o .ini.
           Si es un ZIP (ej. Star_citizen_ES.zip, StarCitizen.Deutsch.LIVE.zip, StarStrings-LIVE.zip):
           lo descarga, extrae global.ini y analiza user.cfg para obtener g_language y subcarpeta.
        2. Si no hay Release o falla, descarga directamente desde la URL raw o la rama principal.
        Retorna: (success, content_bytes, lang_code, subfolder, error_message)
        """
        repo_url = repo_url_or_raw.strip()
        headers = {"User-Agent": "SCcommunityupdate/1.0"}

        # Detección heurística de idioma y subcarpeta según URL
        hint_lang = None
        hint_subfolder = None
        lower_url = repo_url.lower()
        if any(k in lower_url for k in ["es", "spanish", "hispana", "thord82"]):
            hint_lang = "spanish_(spain)"
            hint_subfolder = "spanish_(spain)"
        elif any(k in lower_url for k in ["deutsch", "german", "rjcncpt"]):
            hint_lang = "german_(germany)"
            hint_subfolder = "german_(germany)"
        elif any(k in lower_url for k in ["french", "français", "francais", "dymerz"]):
            hint_lang = "french_(france)"
            hint_subfolder = "french_(france)"
        elif any(k in lower_url for k in ["chinese", "tctp", "trad"]):
            hint_lang = "chinese_(traditional)"
            hint_subfolder = "chinese_(traditional)"
        elif any(k in lower_url for k in ["korean", "ru", "russian", "n1ghter"]):
            hint_lang = "korean_(south_korea)"
            hint_subfolder = "korean_(south_korea)"
        elif any(k in lower_url for k in ["italian", "italy"]):
            hint_lang = "italian_(italy)"
            hint_subfolder = "italian_(italy)"
        elif any(k in lower_url for k in ["portuguese", "ptbr", "brazil"]):
            hint_lang = "portuguese_(brazil)"
            hint_subfolder = "portuguese_(brazil)"

        # 1. Intentar buscar GitHub Release
        owner, repo = None, None
        m = re.search(r'(?:github\.com|raw\.githubusercontent\.com)/([^/]+)/([^/]+)', repo_url)
        if m:
            owner = m.group(1)
            repo = m.group(2).replace('.git', '')

        if owner and repo:
            try:
                if progress_callback:
                    progress_callback(f"Buscando última versión oficial en GitHub Releases ({owner}/{repo})...", 0.15)
                api_url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
                rel_resp = requests.get(api_url, headers=headers, timeout=8)
                if rel_resp.status_code == 200:
                    rel_data = rel_resp.json()
                    tag_name = rel_data.get("tag_name", "")
                    assets = rel_data.get("assets", [])

                    zip_asset = None
                    ini_asset = None

                    # Priorizar asset que coincida con el idioma si hay múltiples
                    if hint_subfolder:
                        lang_prefix = hint_subfolder.split("_")[0].lower()
                        for a in assets:
                            a_name = a.get("name", "").lower()
                            if a_name.endswith(".zip") and (lang_prefix in a_name or hint_subfolder.lower() in a_name):
                                zip_asset = a
                                break

                    if not zip_asset:
                        for a in assets:
                            a_name = a.get("name", "").lower()
                            if a_name.endswith(".zip"):
                                zip_asset = a
                                break
                            elif a_name.endswith(".ini") and not ini_asset:
                                ini_asset = a

                    if zip_asset:
                        asset_url = zip_asset.get("browser_download_url")
                        asset_name = zip_asset.get("name")
                        if progress_callback:
                            progress_callback(f"Descargando paquete oficial {tag_name} ({asset_name})...", 0.3)

                        z_resp = requests.get(asset_url, headers=headers, timeout=30)
                        if z_resp.status_code == 200:
                            z = zipfile.ZipFile(io.BytesIO(z_resp.content))
                            ini_path_in_zip = None
                            cfg_path_in_zip = None

                            for n in z.namelist():
                                n_lower = n.lower()
                                if n_lower.endswith("global.ini") and not n.startswith("PTU"):
                                    ini_path_in_zip = n
                                if n_lower.endswith("user.cfg") and not n.startswith("PTU"):
                                    cfg_path_in_zip = n

                            if ini_path_in_zip:
                                ini_bytes = z.read(ini_path_in_zip)
                                lang_code = hint_lang or "en"
                                subfolder = hint_subfolder

                                # Extraer g_language de user.cfg en el zip si existe
                                if cfg_path_in_zip:
                                    try:
                                        cfg_str = z.read(cfg_path_in_zip).decode("utf-8", errors="ignore")
                                        cm = re.search(r"g_language\s*=\s*([a-zA-Z0-9_\(\)]+)", cfg_str)
                                        if cm:
                                            lang_code = cm.group(1).strip()
                                    except Exception:
                                        pass

                                # Determinar subcarpeta (ej. spanish_(spain))
                                parts = ini_path_in_zip.replace("\\", "/").split("/")
                                if len(parts) >= 2 and parts[-1].lower() == "global.ini":
                                    candidate_sub = parts[-2]
                                    if candidate_sub.lower() not in ["localization", "data", "live", "for_players"]:
                                        subfolder = candidate_sub

                                if not subfolder and hint_subfolder:
                                    subfolder = hint_subfolder
                                if not lang_code and hint_lang:
                                    lang_code = hint_lang

                                if progress_callback:
                                    progress_callback(f"¡Actualización {tag_name} extraída ({len(ini_bytes)//1024} KB)!", 0.85)

                                return True, ini_bytes, lang_code, subfolder, None

                    elif ini_asset:
                        asset_url = ini_asset.get("browser_download_url")
                        asset_name = ini_asset.get("name")
                        if progress_callback:
                            progress_callback(f"Descargando archivo {asset_name} de release {tag_name}...", 0.4)
                        i_resp = requests.get(asset_url, headers=headers, timeout=25)
                        if i_resp.status_code == 200:
                            ini_bytes = i_resp.content
                            lang_code = hint_lang or "en"
                            subfolder = hint_subfolder
                            if progress_callback:
                                progress_callback(f"¡Descargado {asset_name} ({len(ini_bytes)//1024} KB)!", 0.85)
                            return True, ini_bytes, lang_code, subfolder, None

            except Exception as e:
                print(f"[ReleaseResolver] Error buscando release: {e}")

        # 2. Fallback: Descarga desde URL Raw directa o resuelta
        if progress_callback:
            progress_callback("Descargando global.ini directamente desde el repositorio...", 0.35)

        target_url = repo_url
        if "raw.githubusercontent.com" not in target_url or not target_url.lower().endswith(".ini"):
            ok_res, res_url, _ = cls.resolve_github_raw_url(repo_url)
            if ok_res:
                target_url = res_url

        try:
            resp = requests.get(target_url, headers=headers, stream=True, timeout=20)
            if resp.status_code == 404:
                ok_res, new_url, _ = cls.resolve_github_raw_url(target_url)
                if ok_res and new_url != target_url:
                    target_url = new_url
                    resp = requests.get(target_url, headers=headers, stream=True, timeout=20)

            if resp.status_code != 200:
                return False, None, "en", None, f"Error del servidor al descargar (Código HTTP {resp.status_code})"

            chunks = []
            for chunk in resp.iter_content(chunk_size=32768):
                if chunk:
                    chunks.append(chunk)

            content_bytes = b"".join(chunks)
            if not content_bytes:
                return False, None, "en", None, "El archivo descargado está vacío."

            lang_code = hint_lang or "en"
            subfolder = hint_subfolder
            return True, content_bytes, lang_code, subfolder, None
        except Exception as e:
            return False, None, "en", None, f"Error de conexión en la descarga: {e}"

    @classmethod
    def download_and_install_translation(
        cls,
        live_path: str,
        repo_url: str,
        repo_id: str = "custom",
        progress_callback: Optional[Callable[[str, float], None]] = None,
        sync_english: bool = True
    ) -> Tuple[bool, str]:
        r"""
        Descarga la versión más reciente del repositorio (usando GitHub Releases o fallback a raw),
        guarda en caché local, quita la extensión a cualquier otra traducción previa
        e instala esta como la ÚNICA activa en el juego.
        """
        if not cls.is_valid_live_directory(live_path):
            return False, f"La ruta de Star Citizen no es válida: {live_path}"

        ok, content_bytes, lang_code, subfolder, err = cls.fetch_latest_translation(
            repo_url,
            progress_callback=progress_callback
        )
        if not ok or not content_bytes:
            return False, err or "No se pudo obtener el archivo de traducción."

        if progress_callback:
            progress_callback("Quitando extensiones a las demás traducciones y activando...", 0.9)

        ok_act, msg_act = cls.activate_translation(
            live_path=live_path,
            repo_id=repo_id,
            content_bytes=content_bytes,
            subfolder=subfolder,
            lang_code=lang_code,
            sync_english=sync_english
        )
        return ok_act, msg_act

    @classmethod
    def get_starstrings_patch_cache_path(cls) -> str:
        """Obtiene la ruta al archivo JSON local donde se guardan las claves modulares de StarStrings."""
        return os.path.join(get_translations_cache_dir(), "starstrings_patch.json")

    @classmethod
    def fetch_starstrings_patch_lines(
        cls,
        progress_callback: Optional[Callable[[str, float], None]] = None
    ) -> Dict[str, str]:
        """
        Descarga o lee de caché las modificaciones modulares de StarStrings (MrKraken: components, contracts, mining, ordnance).
        Retorna un diccionario {clave: valor_parcheado}.
        """
        patch_cache_file = cls.get_starstrings_patch_cache_path()
        patch_dict = {}

        base_url = "https://raw.githubusercontent.com/MrKraken/StarStrings/master/src/For_Tool_Creators/"
        modules = ["components.ini", "contracts.ini", "mining.ini", "ordnance.ini"]
        headers = {"User-Agent": "SCcommunityupdate/1.0"}

        try:
            if progress_callback:
                progress_callback("Obteniendo líneas de mejora de StarStrings (components, contracts, ordnance)...", 0.3)

            for m in modules:
                r = requests.get(base_url + m, headers=headers, timeout=12)
                if r.status_code == 200:
                    for line in r.text.splitlines():
                        line = line.strip().lstrip('\ufeff')
                        if '=' in line and not line.startswith(';') and not line.startswith('#'):
                            k, v = line.split('=', 1)
                            patch_dict[k.strip()] = v.strip()

            if patch_dict:
                try:
                    with open(patch_cache_file, "w", encoding="utf-8") as f:
                        json.dump(patch_dict, f, ensure_ascii=False)
                except Exception:
                    pass
                return patch_dict
        except Exception as e:
            print(f"[StarStrings] Fallo descarga modular: {e}")

        # Fallback a caché local de patch_dict si existe
        if os.path.isfile(patch_cache_file):
            try:
                with open(patch_cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass

        # Fallback a starstrings.ini si existe en caché
        ss_bytes = cls.get_cached_bytes("starstrings")
        if ss_bytes:
            try:
                text = ss_bytes.decode("utf-8", errors="ignore")
                for line in text.splitlines():
                    line = line.strip().lstrip('\ufeff')
                    if '=' in line and not line.startswith(';') and not line.startswith('#'):
                        k, v = line.split('=', 1)
                        if any(t in v for t in ['<EM4>', '[BP]', '[Rep', 'Mil/', 'Civ/', 'Ind/', 'Cmp/', 'Ste/', '[CS', '[EM', '[IR']):
                            patch_dict[k.strip()] = v.strip()
                return patch_dict
            except Exception:
                pass

        return patch_dict

    @classmethod
    def merge_starstrings_into_translation(
        cls,
        base_ini_bytes: bytes,
        patch_dict: Dict[str, str]
    ) -> Tuple[bytes, int]:
        r"""
        Fusiona las líneas de StarStrings directamente sobre un archivo global.ini base:
        1. Para títulos de misiones con etiquetas de recompensa [BP] y [Rep]:
           extrae las etiquetas y las añade al final del título traducido (si no las tenía ya).
        2. Para descripciones de misiones: añade las líneas de reputación al final si faltan.
        3. Para componentes (components.ini) y armamento (ordnance.ini):
           aplica la clasificación de componentes y misiles.
        4. Para cualquier otra línea: preserva la traducción base original al 100%.
        Retorna: (merged_ini_bytes, total_lines_modified)
        """
        if not patch_dict:
            return base_ini_bytes, 0

        text = base_ini_bytes.decode("utf-8", errors="ignore")
        has_bom = text.startswith('\ufeff')
        lines = text.splitlines(keepends=True)

        merged_lines = []
        modified_count = 0

        for line in lines:
            stripped = line.strip()
            if '=' in stripped and not stripped.startswith(';') and not stripped.startswith('#'):
                k, v = stripped.split('=', 1)
                k_clean = k.strip()
                v_clean = v.strip()

                if k_clean in patch_dict:
                    patch_v = patch_dict[k_clean]

                    # Si es un título de misión con etiquetas de recompensa
                    if 'title' in k_clean.lower():
                        tags = re.findall(r'<EM4>.*?</EM4>|\[BP\]\*?|\[\d+.*?Rep\]', patch_v)
                        new_v = v_clean
                        for t in tags:
                            clean_t = t.replace('*', '')
                            if t not in v_clean and clean_t not in v_clean:
                                new_v += ' ' + t
                        merged_lines.append(f"{k_clean}={new_v}\n")
                    # Si es una descripción con sección de reputación
                    elif 'desc' in k_clean.lower() and '<EM4>Reputation Awarded' in patch_v:
                        rep_part = patch_v[patch_v.find('<EM4>Reputation Awarded'):]
                        if '<EM4>Reputation Awarded' not in v_clean:
                            new_v = v_clean + "\\n\\n" + rep_part
                            merged_lines.append(f"{k_clean}={new_v}\n")
                        else:
                            merged_lines.append(f"{k_clean}={v_clean}\n")
                    else:
                        # Componentes, armamento, minería: aplicar clasificación
                        merged_lines.append(f"{k_clean}={patch_v}\n")

                    modified_count += 1
                else:
                    merged_lines.append(line)
            else:
                merged_lines.append(line)

        merged_text = "".join(merged_lines)
        if has_bom and not merged_text.startswith('\ufeff'):
            merged_text = '\ufeff' + merged_text

        return merged_text.encode("utf-8"), modified_count

    @classmethod
    def apply_starstrings_to_active_translation(
        cls,
        live_path: str,
        active_repo_id: str,
        progress_callback: Optional[Callable[[str, float], None]] = None
    ) -> Tuple[bool, str, int]:
        r"""
        Descarga las líneas de StarStrings y las fusiona directamente dentro de los archivos
        de la traducción activa (ej. spanish_(spain), en, english), PRESERVANDO el idioma
        configurado en user.cfg (ej. g_language = spanish_(spain)) para que el juego continúe
        100% en español con todas las etiquetas y clasificaciones añadidas.
        """
        if not cls.is_valid_live_directory(live_path):
            return False, f"La carpeta de Star Citizen no es válida: {live_path}", 0

        # Obtener bytes base de la traducción activa (del caché)
        base_bytes = cls.get_cached_bytes(active_repo_id)
        if not base_bytes:
            meta = cls.get_cache_meta(active_repo_id)
            sub = meta.get("subfolder") or "spanish_(spain)"
            cand_file = os.path.join(live_path, "data", "Localization", sub, "global.ini")
            if not os.path.isfile(cand_file):
                cand_file = os.path.join(live_path, "data", "Localization", "en", "global.ini")
            if os.path.isfile(cand_file):
                try:
                    with open(cand_file, "rb") as f:
                        base_bytes = f.read()
                except Exception:
                    pass

        if not base_bytes:
            return False, f"No se encontró el archivo base de la traducción activa '{active_repo_id}'.", 0

        if progress_callback:
            progress_callback("Descargando líneas de mejora de StarStrings...", 0.3)

        patch_dict = cls.fetch_starstrings_patch_lines(progress_callback)
        if not patch_dict:
            return False, "No se pudieron obtener las líneas de mejora de StarStrings.", 0

        if progress_callback:
            progress_callback(f"Fusionando {len(patch_dict)} líneas de StarStrings en la traducción activa...", 0.7)

        merged_bytes, count = cls.merge_starstrings_into_translation(base_bytes, patch_dict)

        # Determinar subcarpeta y código de idioma activo
        meta = cls.get_cache_meta(active_repo_id)
        lang_code = meta.get("lang_code") or cls.get_user_cfg_language(live_path) or "spanish_(spain)"
        subfolder = meta.get("subfolder") or ("spanish_(spain)" if "es" in active_repo_id else "en")

        # Guardar archivo fusionado en caché especial
        cls.save_to_cache(f"{active_repo_id}_starstrings", merged_bytes)

        # Escribir en las carpetas correspondientes del juego
        # 1. Carpeta subfolder (ej. spanish_(spain))
        if subfolder and subfolder.lower() not in ["en", "english"]:
            target_sub = os.path.join(live_path, "data", "Localization", subfolder)
            os.makedirs(target_sub, exist_ok=True)
            with open(os.path.join(target_sub, "global.ini"), "wb") as f:
                f.write(merged_bytes)

        # 2. Carpeta en
        target_en = os.path.join(live_path, "data", "Localization", "en")
        os.makedirs(target_en, exist_ok=True)
        with open(os.path.join(target_en, "global.ini"), "wb") as f:
            f.write(merged_bytes)

        # 3. Carpeta english
        target_eng = os.path.join(live_path, "data", "Localization", "english")
        os.makedirs(target_eng, exist_ok=True)
        with open(os.path.join(target_eng, "global.ini"), "wb") as f:
            f.write(merged_bytes)

        # Asegurar que user.cfg conserve la traducción activa
        cls.set_user_cfg_language(live_path, lang_code)

        if progress_callback:
            progress_callback(f"¡{count} líneas de StarStrings fusionadas exitosamente!", 1.0)

        return True, f"¡Se fusionaron {count} líneas de StarStrings en la traducción activa ('{active_repo_id}')!", count

    @classmethod
    def revert_starstrings_from_active_translation(
        cls,
        live_path: str,
        active_repo_id: str
    ) -> Tuple[bool, str]:
        r"""
        Restaura la versión original limpia de la traducción activa desde la caché,
        eliminando las líneas fusionadas de StarStrings.
        """
        if not cls.is_valid_live_directory(live_path):
            return False, f"La carpeta de Star Citizen no es válida: {live_path}"

        clean_bytes = cls.get_cached_bytes(active_repo_id)
        if not clean_bytes:
            return False, f"No se encontró la traducción limpia en caché para '{active_repo_id}'."

        ok, msg = cls.activate_translation(live_path, active_repo_id, content_bytes=clean_bytes, sync_english=True)
        if ok:
            return True, f"Traducción restaurada a su versión original sin StarStrings."
        return False, msg

    @classmethod
    def get_launcher_executable_path(cls, live_path: str = "") -> Optional[str]:
        """
        Localiza el ejecutable del launcher oficial de Star Citizen (RSI Launcher.exe).
        """
        candidates = []
        if live_path and os.path.isdir(live_path):
            parent_rsi = os.path.abspath(os.path.join(live_path, "..", ".."))
            candidates.append(os.path.join(parent_rsi, "RSI Launcher", "RSI Launcher.exe"))
            candidates.append(os.path.join(live_path, "StarCitizen_Launcher.exe"))

        for letter in string.ascii_uppercase:
            drive_root = f"{letter}:\\"
            if os.path.exists(drive_root):
                candidates.extend([
                    os.path.join(drive_root, "Program Files", "Roberts Space Industries", "RSI Launcher", "RSI Launcher.exe"),
                    os.path.join(drive_root, "Program Files (x86)", "Roberts Space Industries", "RSI Launcher", "RSI Launcher.exe"),
                    os.path.join(drive_root, "Roberts Space Industries", "RSI Launcher", "RSI Launcher.exe"),
                    os.path.join(drive_root, "Games", "Roberts Space Industries", "RSI Launcher", "RSI Launcher.exe"),
                    os.path.join(drive_root, "Juegos", "Roberts Space Industries", "RSI Launcher", "RSI Launcher.exe"),
                    os.path.join(drive_root, "RSI", "RSI Launcher", "RSI Launcher.exe"),
                ])

        for c in candidates:
            if os.path.isfile(c):
                return os.path.normpath(c)

        if live_path:
            alt = os.path.join(live_path, "StarCitizen_Launcher.exe")
            if os.path.isfile(alt):
                return os.path.normpath(alt)

        return None

    @classmethod
    def launch_game_launcher(cls, live_path: str = "") -> Tuple[bool, str]:
        """Ejecuta el launcher oficial del juego (RSI Launcher)."""
        launcher_path = cls.get_launcher_executable_path(live_path)
        if not launcher_path:
            # Fallback al ejecutable directo si no se localiza el launcher
            exe_direct = cls.get_executable_path(live_path)
            if exe_direct:
                return cls.launch_game(live_path)
            return False, "No se encontró el ejecutable del launcher oficial (RSI Launcher.exe)."

        try:
            working_dir = os.path.dirname(launcher_path)
            subprocess.Popen([launcher_path], cwd=working_dir, shell=False)
            return True, f"RSI Launcher iniciado exitosamente desde: {launcher_path}"
        except Exception as e:
            return False, f"Error al ejecutar el launcher del juego: {e}"

    @classmethod
    def launch_game(cls, live_path: str) -> Tuple[bool, str]:
        """Ejecuta de forma directa StarCitizen.exe."""
        exe_path = cls.get_executable_path(live_path)
        if not exe_path:
            return False, f"No se encontró el ejecutable StarCitizen.exe en: {live_path}"

        try:
            # Directorio de trabajo establecido en Bin64 o en LIVE
            working_dir = os.path.dirname(exe_path)
            # Ejecutar de forma no bloqueante
            subprocess.Popen([exe_path], cwd=working_dir, shell=False)
            return True, f"Star Citizen iniciado exitosamente desde: {exe_path}"
        except Exception as e:
            return False, f"Error al ejecutar Star Citizen: {e}"
