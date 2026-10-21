"""
Interfaz Gráfica del Launcher Alternativo de Star Citizen.
Construida con CustomTkinter para ofrecer una estética moderna, limpia y espacial.
Incluye pestañas para Traducciones y Herramientas de la Comunidad (ej. StarStrings).
"""

import os
import sys
import threading
import webbrowser
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
from PIL import Image

from config_manager import ConfigManager, OFFICIAL_LANGUAGES
from game_manager import StarCitizenManager
from i18n import (
    t,
    set_current_language,
    get_current_language,
    get_display_name_from_code,
    get_code_from_display_name,
    AVAILABLE_LANGUAGES
)


def get_resource_path(relative_path: str) -> str:
    """Obtiene la ruta a un recurso o asset, compatible con PyInstaller y desarrollo."""
    if getattr(sys, "frozen", False):
        base_path = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
        res_path = os.path.join(base_path, relative_path)
        if os.path.exists(res_path):
            return res_path
        exe_dir = os.path.dirname(sys.executable)
        res_path = os.path.join(exe_dir, relative_path)
        if os.path.exists(res_path):
            return res_path
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, relative_path)


class AddRepoDialog(ctk.CTkToplevel):
    """Ventana emergente moderna para añadir un nuevo repositorio de GitHub."""

    def __init__(self, parent, on_save_callback):
        super().__init__(parent)
        self.on_save_callback = on_save_callback

        self.title(t("dialog_repo_title"))
        self.geometry("540x360")
        self.resizable(False, False)
        self.configure(fg_color="#0f141c")

        self.transient(parent)
        self.grab_set()

        self._build_ui()
        self.after(100, self.lift)

    def _build_ui(self):
        title_label = ctk.CTkLabel(
            self,
            text=t("dialog_repo_header"),
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color="#00b4d8"
        )
        title_label.pack(pady=(20, 5))

        desc_label = ctk.CTkLabel(
            self,
            text=t("dialog_repo_desc"),
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="#8b949e",
            justify="center"
        )
        desc_label.pack(pady=(0, 15))

        form_frame = ctk.CTkFrame(self, fg_color="transparent")
        form_frame.pack(fill="x", padx=30, pady=5)

        name_label = ctk.CTkLabel(
            form_frame,
            text=t("dialog_repo_name_lbl"),
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color="#c9d1d9",
            anchor="w"
        )
        name_label.pack(fill="x", pady=(0, 4))

        self.name_entry = ctk.CTkEntry(
            form_frame,
            placeholder_text=t("dialog_repo_name_ph"),
            height=36,
            fg_color="#161b22",
            border_color="#30363d",
            text_color="#f0f6fc"
        )
        self.name_entry.pack(fill="x", pady=(0, 12))

        url_label = ctk.CTkLabel(
            form_frame,
            text=t("dialog_repo_url_lbl"),
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color="#c9d1d9",
            anchor="w"
        )
        url_label.pack(fill="x", pady=(0, 4))

        self.url_entry = ctk.CTkEntry(
            form_frame,
            placeholder_text=t("dialog_repo_url_ph"),
            height=36,
            fg_color="#161b22",
            border_color="#30363d",
            text_color="#f0f6fc"
        )
        self.url_entry.pack(fill="x", pady=(0, 15))

        self.status_lbl = ctk.CTkLabel(
            form_frame,
            text="",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="#f85149"
        )
        self.status_lbl.pack(fill="x", pady=(0, 10))

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=30, pady=(5, 15))

        cancel_btn = ctk.CTkButton(
            btn_frame,
            text=t("dialog_repo_btn_cancel"),
            fg_color="#21262d",
            hover_color="#30363d",
            text_color="#c9d1d9",
            width=110,
            height=36,
            command=self.destroy
        )
        cancel_btn.pack(side="right", padx=(10, 0))

        self.save_btn = ctk.CTkButton(
            btn_frame,
            text=t("dialog_repo_btn_save"),
            fg_color="#238636",
            hover_color="#2ea043",
            text_color="#ffffff",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            width=160,
            height=36,
            command=self._on_save
        )
        self.save_btn.pack(side="right")

    def _on_save(self):
        name = self.name_entry.get().strip()
        url = self.url_entry.get().strip()

        if not name:
            self.status_lbl.configure(text=t("dialog_repo_err_name"))
            return

        if not url or ("github.com" not in url and "githubusercontent.com" not in url):
            self.status_lbl.configure(text=t("dialog_repo_err_url"))
            return

        self.status_lbl.configure(text=t("dialog_repo_verifying"), text_color="#00b4d8")
        self.save_btn.configure(state="disabled")

        def _verify():
            ok, raw_url, warn = StarCitizenManager.resolve_github_raw_url(url)
            self.after(0, lambda: self._finish_save(name, url, raw_url if ok else url))

        threading.Thread(target=_verify, daemon=True).start()

    def _finish_save(self, name: str, url: str, raw_url: str):
        self.on_save_callback(name, url, raw_url)
        self.destroy()


class AddToolDialog(ctk.CTkToplevel):
    """Ventana emergente para añadir herramientas de la comunidad (ej. StarStrings)."""

    def __init__(self, parent, on_save_callback):
        super().__init__(parent)
        self.on_save_callback = on_save_callback

        self.title(t("dialog_tool_title"))
        self.geometry("560x420")
        self.resizable(False, False)
        self.configure(fg_color="#0f141c")

        self.transient(parent)
        self.grab_set()

        self._build_ui()
        self.after(100, self.lift)

    def _build_ui(self):
        title_label = ctk.CTkLabel(
            self,
            text=t("dialog_tool_header"),
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color="#00b4d8"
        )
        title_label.pack(pady=(18, 4))

        desc_label = ctk.CTkLabel(
            self,
            text=t("dialog_tool_desc"),
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="#8b949e",
            justify="center"
        )
        desc_label.pack(pady=(0, 12))

        form_frame = ctk.CTkFrame(self, fg_color="transparent")
        form_frame.pack(fill="x", padx=30, pady=0)

        # Nombre
        lbl_name = ctk.CTkLabel(
            form_frame,
            text=t("dialog_tool_name_lbl"),
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color="#c9d1d9",
            anchor="w"
        )
        lbl_name.pack(fill="x", pady=(0, 2))

        self.name_entry = ctk.CTkEntry(
            form_frame,
            placeholder_text=t("dialog_tool_name_ph"),
            height=34,
            fg_color="#161b22",
            border_color="#30363d",
            text_color="#f0f6fc"
        )
        self.name_entry.pack(fill="x", pady=(0, 8))

        # URL GitHub
        lbl_url = ctk.CTkLabel(
            form_frame,
            text=t("dialog_tool_url_lbl"),
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color="#c9d1d9",
            anchor="w"
        )
        lbl_url.pack(fill="x", pady=(0, 2))

        self.url_entry = ctk.CTkEntry(
            form_frame,
            placeholder_text=t("dialog_tool_url_ph"),
            height=34,
            fg_color="#161b22",
            border_color="#30363d",
            text_color="#f0f6fc"
        )
        self.url_entry.pack(fill="x", pady=(0, 8))

        # Descripción
        lbl_desc = ctk.CTkLabel(
            form_frame,
            text=t("dialog_tool_desc_lbl"),
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color="#c9d1d9",
            anchor="w"
        )
        lbl_desc.pack(fill="x", pady=(0, 2))

        self.desc_entry = ctk.CTkEntry(
            form_frame,
            placeholder_text=t("dialog_tool_desc_ph"),
            height=34,
            fg_color="#161b22",
            border_color="#30363d",
            text_color="#f0f6fc"
        )
        self.desc_entry.pack(fill="x", pady=(0, 10))

        # Checkbox si es mod de strings (global.ini)
        self.is_string_mod_var = ctk.BooleanVar(value=True)
        self.cb_string_mod = ctk.CTkCheckBox(
            form_frame,
            text=t("dialog_tool_check_qol"),
            variable=self.is_string_mod_var,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="#c9d1d9",
            fg_color="#00b4d8",
            hover_color="#0096c7"
        )
        self.cb_string_mod.pack(anchor="w", pady=(0, 10))

        self.status_lbl = ctk.CTkLabel(
            form_frame,
            text="",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="#f85149"
        )
        self.status_lbl.pack(fill="x", pady=(0, 6))

        # Botones
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=30, pady=(6, 14))

        cancel_btn = ctk.CTkButton(
            btn_frame,
            text=t("dialog_tool_btn_cancel"),
            fg_color="#21262d",
            hover_color="#30363d",
            text_color="#c9d1d9",
            width=110,
            height=36,
            command=self.destroy
        )
        cancel_btn.pack(side="right", padx=(10, 0))

        self.save_btn = ctk.CTkButton(
            btn_frame,
            text=t("dialog_tool_btn_save"),
            fg_color="#238636",
            hover_color="#2ea043",
            text_color="#ffffff",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            width=170,
            height=36,
            command=self._on_save
        )
        self.save_btn.pack(side="right")

    def _on_save(self):
        name = self.name_entry.get().strip()
        url = self.url_entry.get().strip()
        desc = self.desc_entry.get().strip()
        is_string_mod = self.is_string_mod_var.get()

        if not name:
            self.status_lbl.configure(text=t("dialog_tool_err_name"))
            return

        if not url:
            self.status_lbl.configure(text=t("dialog_tool_err_url"))
            return

        self.status_lbl.configure(text=t("dialog_tool_verifying"), text_color="#00b4d8")
        self.save_btn.configure(state="disabled")

        def _verify():
            raw_url = ""
            if is_string_mod:
                ok, resolved, _ = StarCitizenManager.resolve_github_raw_url(url)
                if ok:
                    raw_url = resolved
            self.after(0, lambda: self._finish_save(name, url, desc, raw_url, is_string_mod))

        threading.Thread(target=_verify, daemon=True).start()

    def _finish_save(self, name: str, url: str, desc: str, raw_url: str, is_string_mod: bool):
        self.on_save_callback(name, url, desc, raw_url, is_string_mod)
        self.destroy()


class StarCitizenLauncherApp(ctk.CTk):
    """Ventana principal del Launcher Alternativo de Star Citizen."""

    def __init__(self):
        super().__init__()

        # Configuración estética global
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        # Administrador de datos
        self.config_mgr = ConfigManager()
        self.current_live_path = ""

        # Inicializar idioma activo de la interfaz
        saved_lang = self.config_mgr.get_app_language()
        set_current_language(saved_lang)

        self.title(t("window_title"))
        self.geometry("1040x840")
        self.minsize(940, 720)
        self.configure(fg_color="#0b0e14")

        # Cargar icono de ventana
        ico_path = get_resource_path(os.path.join("assets", "logo.ico"))
        if os.path.exists(ico_path):
            try:
                self.iconbitmap(ico_path)
            except Exception as e:
                print(f"[UI] No se pudo asignar iconbitmap: {e}")

        self.current_tab_trans_name = t("tab_translations")
        self.current_tab_tools_name = t("tab_tools")

        self._build_ui()
        self._initialize_path()

    def _build_ui(self):
        # 1. ENCABEZADO SUPERIOR PERMANENTE
        self._build_header()

        # 2. BARRA DE RUTA DE STAR CITIZEN (GLOBAL)
        self._build_path_bar()

        # 3. PESTAÑAS PRINCIPALES (TABVIEW)
        self.tabview = ctk.CTkTabview(
            self,
            fg_color="#121721",
            segmented_button_fg_color="#1c2430",
            segmented_button_selected_color="#0077b6",
            segmented_button_selected_hover_color="#0096c7",
            segmented_button_unselected_color="#1c2430",
            segmented_button_unselected_hover_color="#2b3749",
            text_color="#f0f6fc"
        )
        self.tabview.pack(fill="both", expand=True, padx=20, pady=(4, 8))

        # Crear Pestañas
        self.tab_translations = self.tabview.add(self.current_tab_trans_name)
        self.tab_tools = self.tabview.add(self.current_tab_tools_name)

        # Llenar Pestaña 1: Traducciones
        self._build_translations_tab()

        # Llenar Pestaña 2: Herramientas
        self._build_tools_tab()

        # 4. BARRA INFERIOR PERMANENTE: ACCIÓN PRINCIPAL DE LANZAMIENTO Y LOG
        self._build_bottom_section()

    def _build_header(self):
        header_frame = ctk.CTkFrame(self, fg_color="#0f141c", corner_radius=0, height=72)
        header_frame.pack(fill="x", side="top")
        header_frame.pack_propagate(False)

        inner = ctk.CTkFrame(header_frame, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=20, pady=10)

        # Logo de la aplicación
        logo_path = get_resource_path(os.path.join("assets", "logo.png"))
        if os.path.exists(logo_path):
            try:
                logo_pil = Image.open(logo_path)
                self.logo_ctk = ctk.CTkImage(light_image=logo_pil, dark_image=logo_pil, size=(48, 48))
                self.lbl_logo = ctk.CTkLabel(inner, image=self.logo_ctk, text="")
                self.lbl_logo.pack(side="left", padx=(0, 14))
            except Exception as e:
                print(f"[UI] Error cargando logo en header: {e}")

        # Título y Subtítulo
        title_box = ctk.CTkFrame(inner, fg_color="transparent")
        title_box.pack(side="left")

        self.lbl_app_title = ctk.CTkLabel(
            title_box,
            text=t("app_title"),
            font=ctk.CTkFont(family="Consolas", size=22, weight="bold"),
            text_color="#00b4d8"
        )
        self.lbl_app_title.pack(anchor="w")

        self.lbl_app_sub = ctk.CTkLabel(
            title_box,
            text=t("app_subtitle"),
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            text_color="#8b949e"
        )
        self.lbl_app_sub.pack(anchor="w")

        # Controles y Badges en la cabecera (derecha)
        badge_frame = ctk.CTkFrame(inner, fg_color="transparent")
        badge_frame.pack(side="right", pady=4)

        # Selector de Idioma de la Aplicación
        self.lbl_app_lang = ctk.CTkLabel(
            badge_frame,
            text=t("app_lang_label"),
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color="#8b949e"
        )
        self.lbl_app_lang.pack(side="left", padx=(0, 6))

        curr_display = get_display_name_from_code(get_current_language())
        self.app_lang_menu = ctk.CTkOptionMenu(
            badge_frame,
            values=list(AVAILABLE_LANGUAGES.values()),
            width=145,
            height=30,
            fg_color="#1c2430",
            button_color="#0077b6",
            button_hover_color="#0096c7",
            text_color="#f0f6fc",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            command=self._on_app_language_changed
        )
        self.app_lang_menu.set(curr_display)
        self.app_lang_menu.pack(side="left", padx=(0, 12))

        self.top_status_badge = ctk.CTkLabel(
            badge_frame,
            text=t("badge_ready"),
            fg_color="#1f2937",
            text_color="#9ca3af",
            corner_radius=6,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            padx=12,
            pady=4
        )
        self.top_status_badge.pack(side="left")

    def _build_path_bar(self):
        """Barra accesible para visualización y selección de la carpeta LIVE."""
        bar = ctk.CTkFrame(
            self,
            fg_color="#131924",
            border_width=1,
            border_color="#222d3d",
            corner_radius=8
        )
        bar.pack(fill="x", padx=20, pady=(10, 4))

        inner = ctk.CTkFrame(bar, fg_color="transparent")
        inner.pack(fill="x", padx=14, pady=8)

        self.lbl_path = ctk.CTkLabel(
            inner,
            text=t("path_label"),
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color="#00b4d8"
        )
        self.lbl_path.pack(side="left", padx=(0, 8))

        self.path_entry = ctk.CTkEntry(
            inner,
            placeholder_text=r"C:\Program Files\Roberts Space Industries\StarCitizen\LIVE",
            height=32,
            fg_color="#0b0e14",
            border_color="#2b3749",
            text_color="#f0f6fc",
            font=ctk.CTkFont(family="Consolas", size=11)
        )
        self.path_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.path_entry.bind("<Return>", lambda e: self._on_manual_path_entered())

        self.btn_auto_detect = ctk.CTkButton(
            inner,
            text=t("btn_auto_detect"),
            width=115,
            height=32,
            fg_color="#1f2937",
            hover_color="#374151",
            text_color="#00b4d8",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            command=self._action_auto_detect
        )
        self.btn_auto_detect.pack(side="left", padx=(0, 6))

        self.btn_browse = ctk.CTkButton(
            inner,
            text=t("btn_browse"),
            width=95,
            height=32,
            fg_color="#1f2937",
            hover_color="#374151",
            text_color="#f0f6fc",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            command=self._action_browse_path
        )
        self.btn_browse.pack(side="left", padx=(0, 8))

        self.path_valid_badge = ctk.CTkLabel(
            inner,
            text=t("badge_checking"),
            fg_color="#21262d",
            text_color="#8b949e",
            corner_radius=5,
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            padx=8,
            pady=3
        )
        self.path_valid_badge.pack(side="right")

    # ==========================
    # PESTAÑA 1: TRADUCCIONES
    # ==========================
    def _build_translations_tab(self):
        container = ctk.CTkScrollableFrame(
            self.tab_translations,
            fg_color="transparent",
            scrollbar_button_color="#21262d",
            scrollbar_button_hover_color="#30363d"
        )
        container.pack(fill="both", expand=True, padx=4, pady=4)

        # Barra de progreso
        self.download_progress_bar = ctk.CTkProgressBar(
            container,
            orientation="horizontal",
            height=3,
            fg_color="#1b222d",
            progress_color="#00b4d8"
        )
        self.download_progress_bar.set(0)
        self.download_progress_bar.pack(fill="x", pady=(0, 8))

        # Tarjeta 1: Selector de Idiomas Oficiales de la Comunidad
        self._build_language_selector_card(container)

        # Tarjeta 2: Repositorios de GitHub
        repos_card = ctk.CTkFrame(container, fg_color="#131924", border_width=1, border_color="#222d3d", corner_radius=10)
        repos_card.pack(fill="x", pady=(0, 12))

        header_repos = ctk.CTkFrame(repos_card, fg_color="transparent")
        header_repos.pack(fill="x", padx=16, pady=(12, 8))

        self.lbl_repos_title = ctk.CTkLabel(
            header_repos,
            text=t("repos_card_title"),
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color="#f0f6fc"
        )
        self.lbl_repos_title.pack(side="left")

        self.btn_add_repo = ctk.CTkButton(
            header_repos,
            text=t("btn_add_repo"),
            fg_color="#238636",
            hover_color="#2ea043",
            text_color="#ffffff",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            height=30,
            command=self._action_open_add_repo_dialog
        )
        self.btn_add_repo.pack(side="right")

        self.repos_container = ctk.CTkFrame(repos_card, fg_color="transparent")
        self.repos_container.pack(fill="x", padx=16, pady=(0, 12))
        self._refresh_repository_cards()

        # Tarjeta 3: Configuración de user.cfg
        cfg_card = ctk.CTkFrame(container, fg_color="#131924", border_width=1, border_color="#222d3d", corner_radius=10)
        cfg_card.pack(fill="x", pady=(0, 12))

        header_cfg = ctk.CTkFrame(cfg_card, fg_color="transparent")
        header_cfg.pack(fill="x", padx=16, pady=(12, 6))

        self.lbl_cfg_title = ctk.CTkLabel(
            header_cfg,
            text=t("cfg_card_title"),
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color="#f0f6fc"
        )
        self.lbl_cfg_title.pack(side="left")

        self.cfg_badge = ctk.CTkLabel(
            header_cfg,
            text=t("badge_checking"),
            fg_color="#21262d",
            text_color="#8b949e",
            corner_radius=5,
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            padx=8,
            pady=2
        )
        self.cfg_badge.pack(side="right")

        content_cfg = ctk.CTkFrame(cfg_card, fg_color="transparent")
        content_cfg.pack(fill="x", padx=16, pady=(0, 12))

        self.cfg_status_lbl = ctk.CTkLabel(
            content_cfg,
            text=t("cfg_status_checking"),
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="#c9d1d9",
            anchor="w"
        )
        self.cfg_status_lbl.pack(fill="x", pady=(0, 8))

        actions_cfg = ctk.CTkFrame(content_cfg, fg_color="transparent")
        actions_cfg.pack(fill="x")

        self.btn_force_en = ctk.CTkButton(
            actions_cfg,
            text=t("btn_force_en"),
            width=170,
            height=32,
            fg_color="#238636",
            hover_color="#2ea043",
            text_color="#ffffff",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            command=self._action_set_cfg_en
        )
        self.btn_force_en.pack(side="left", padx=(0, 8))

        self.btn_disable_trans = ctk.CTkButton(
            actions_cfg,
            text=t("btn_disable_trans"),
            width=200,
            height=32,
            fg_color="#21262d",
            hover_color="#30363d",
            text_color="#f85149",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            command=self._action_disable_cfg
        )
        self.btn_disable_trans.pack(side="left", padx=(0, 8))

        self.btn_open_cfg = ctk.CTkButton(
            actions_cfg,
            text=t("btn_open_cfg"),
            width=120,
            height=32,
            fg_color="#21262d",
            hover_color="#30363d",
            text_color="#c9d1d9",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            command=self._action_open_cfg_file
        )
        self.btn_open_cfg.pack(side="left")

    def _build_language_selector_card(self, container):
        """Selector rápido de idiomas con las traducciones comunitarias oficiales verificadas."""
        card = ctk.CTkFrame(
            container,
            fg_color="#131924",
            border_width=1,
            border_color="#222d3d",
            corner_radius=10
        )
        card.pack(fill="x", pady=(0, 12))

        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(12, 6))

        self.lbl_lang_card_title = ctk.CTkLabel(
            header,
            text=t("lang_selector_title"),
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color="#f0f6fc"
        )
        self.lbl_lang_card_title.pack(side="left")

        self.badge_lang_catalog = ctk.CTkLabel(
            header,
            text=t("lang_selector_badge"),
            fg_color="#1f2937",
            text_color="#00b4d8",
            corner_radius=5,
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            padx=8,
            pady=2
        )
        self.badge_lang_catalog.pack(side="right")

        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="x", padx=16, pady=(0, 12))

        self.desc_lang_card = ctk.CTkLabel(
            content,
            text=t("lang_selector_desc"),
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color="#8b949e",
            anchor="w"
        )
        self.desc_lang_card.pack(fill="x", pady=(0, 10))

        # Fila de Controles: OptionMenu + Botón Instalar + Botón Cargar Todos
        row = ctk.CTkFrame(content, fg_color="transparent")
        row.pack(fill="x", pady=(0, 8))

        self.lang_option_menu = ctk.CTkOptionMenu(
            row,
            values=list(OFFICIAL_LANGUAGES.keys()),
            width=290,
            height=34,
            fg_color="#1c2430",
            button_color="#0077b6",
            button_hover_color="#0096c7",
            text_color="#f0f6fc",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            command=self._on_language_selector_changed
        )
        self.lang_option_menu.pack(side="left", padx=(0, 8))

        self.btn_apply_lang = ctk.CTkButton(
            row,
            text=t("btn_install_lang"),
            width=190,
            height=34,
            fg_color="#0077b6",
            hover_color="#0096c7",
            text_color="#ffffff",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            command=self._action_install_selected_language
        )
        self.btn_apply_lang.pack(side="left", padx=(0, 8))

        self.btn_load_all = ctk.CTkButton(
            row,
            text=t("btn_load_all_languages"),
            width=180,
            height=34,
            fg_color="#21262d",
            hover_color="#30363d",
            text_color="#58a6ff",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            command=self._action_load_all_official_languages
        )
        self.btn_load_all.pack(side="left")

        # Información del idioma seleccionado
        self.selected_lang_info_lbl = ctk.CTkLabel(
            content,
            text="",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color="#56d364",
            anchor="w"
        )
        self.selected_lang_info_lbl.pack(fill="x", pady=(2, 0))

        # Inicializar texto de info con la primera opción
        first_key = list(OFFICIAL_LANGUAGES.keys())[0]
        self.lang_option_menu.set(first_key)
        self._on_language_selector_changed(first_key)

    def _on_language_selector_changed(self, choice: str):
        info = OFFICIAL_LANGUAGES.get(choice, {})
        author = info.get("author", "")
        desc = info.get("description", "")

        if choice.startswith("🇬🇧"):
            self.selected_lang_info_lbl.configure(
                text=t("lang_info_original", desc=desc),
                text_color="#e3b341"
            )
            self.btn_apply_lang.configure(
                text=t("btn_restore_english"),
                fg_color="#30363d",
                hover_color="#484f58"
            )
        else:
            self.selected_lang_info_lbl.configure(
                text=t("lang_info_author", author=author, desc=desc),
                text_color="#56d364"
            )
            self.btn_apply_lang.configure(
                text=t("btn_install_lang"),
                fg_color="#0077b6",
                hover_color="#0096c7"
            )

    def _action_install_selected_language(self):
        """Descarga, instala y activa el idioma seleccionado en el selector."""
        if not StarCitizenManager.is_valid_live_directory(self.current_live_path):
            messagebox.showwarning(t("msg_attention"), t("msg_select_live_first"))
            return

        choice = self.lang_option_menu.get()
        info = OFFICIAL_LANGUAGES.get(choice)
        if not info:
            return

        # Si eligió Inglés Original
        if choice.startswith("🇬🇧") or not info.get("raw_url"):
            self._action_disable_cfg()
            return

        name = info["name"]
        raw_url = info["raw_url"]
        repo_url = info["url"]
        lang_id = info["id"]

        self.log(f"Iniciando descarga e instalación del idioma oficial: '{name}'...", "INFO")
        self.download_progress_bar.set(0.1)

        def _worker():
            def _progress_cb(status_text, pct):
                self.log(status_text, "INFO")
                self.after(0, lambda: self.download_progress_bar.set(pct))

            download_url = repo_url or raw_url
            success, message = StarCitizenManager.download_and_install_translation(
                self.current_live_path,
                download_url,
                repo_id=lang_id,
                progress_callback=_progress_cb,
                sync_english=True
            )

            def _done():
                self.download_progress_bar.set(1.0 if success else 0.0)
                if success:
                    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    save_url = raw_url or repo_url
                    repos = self.config_mgr.get_repositories()
                    matched = False
                    for r in repos:
                        if r.get("id") == info["id"] or r.get("name") == info["name"]:
                            r["raw_url"] = save_url
                            r["last_updated"] = now_str
                            self.config_mgr.set_active_repo_id(r["id"])
                            matched = True
                            break
                    if not matched:
                        new_r = self.config_mgr.add_repository(
                            name=info["name"],
                            url=info["url"],
                            raw_url=save_url,
                            description=info["description"]
                        )
                        self.config_mgr.update_repository_timestamp(new_r["id"], now_str)
                        self.config_mgr.set_active_repo_id(new_r["id"])

                    self.config_mgr.set_starstrings_merged_into(None)
                    self._refresh_repository_cards()
                    self._refresh_tools_cards()
                    self._check_user_cfg_status()
                    self.log(f"¡Idioma oficial '{name}' instalado y activado con éxito!", "SUCCESS")
                    messagebox.showinfo(
                        t("msg_lang_installed_title"),
                        t("msg_lang_installed_body", name=name)
                    )
                else:
                    self.log(f"Error instalando '{name}': {message}", "ERROR")
                    messagebox.showerror(t("msg_error"), f"{message}")

            self.after(0, _done)

        threading.Thread(target=_worker, daemon=True).start()

    def _action_load_all_official_languages(self):
        """Carga todas las traducciones oficiales en la lista de repositorios."""
        added = self.config_mgr.load_all_official_languages()
        self._refresh_repository_cards()
        if added > 0:
            self.log(f"Se cargaron {added} nuevas traducciones oficiales a la lista.", "SUCCESS")
            messagebox.showinfo(
                t("msg_load_all_title"),
                t("msg_load_all_body_added", count=added)
            )
        else:
            self.log("Todas las traducciones oficiales ya están presentes en tu lista.", "INFO")
            messagebox.showinfo(
                t("msg_load_all_title"),
                t("msg_load_all_body_already")
            )

    # ==========================
    # PESTAÑA 2: HERRAMIENTAS (STARSTRINGS, ETC.)
    # ==========================
    def _build_tools_tab(self):
        container = ctk.CTkScrollableFrame(
            self.tab_tools,
            fg_color="transparent",
            scrollbar_button_color="#21262d",
            scrollbar_button_hover_color="#30363d"
        )
        container.pack(fill="both", expand=True, padx=4, pady=4)

        # Banner informativo superior
        info_card = ctk.CTkFrame(container, fg_color="#131924", border_width=1, border_color="#222d3d", corner_radius=10)
        info_card.pack(fill="x", pady=(0, 12))

        inner_info = ctk.CTkFrame(info_card, fg_color="transparent")
        inner_info.pack(fill="x", padx=16, pady=12)

        self.lbl_tools_title = ctk.CTkLabel(
            inner_info,
            text=t("tools_info_title"),
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            text_color="#00b4d8",
            anchor="w"
        )
        self.lbl_tools_title.pack(fill="x")

        self.lbl_tools_desc = ctk.CTkLabel(
            inner_info,
            text=t("tools_info_desc"),
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="#8b949e",
            anchor="w",
            justify="left"
        )
        self.lbl_tools_desc.pack(fill="x", pady=(4, 8))

        # Botón añadir herramienta
        self.btn_add_tool = ctk.CTkButton(
            inner_info,
            text=t("btn_add_tool"),
            fg_color="#238636",
            hover_color="#2ea043",
            text_color="#ffffff",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            height=32,
            command=self._action_open_add_tool_dialog
        )
        self.btn_add_tool.pack(anchor="w")

        # Contenedor de herramientas
        self.tools_container = ctk.CTkFrame(container, fg_color="transparent")
        self.tools_container.pack(fill="x", pady=0)

        self._refresh_tools_cards()

    def _refresh_tools_cards(self):
        for widget in self.tools_container.winfo_children():
            widget.destroy()

        tools = self.config_mgr.get_tools()
        if not tools:
            empty_lbl = ctk.CTkLabel(
                self.tools_container,
                text=t("no_tools_msg"),
                font=ctk.CTkFont(family="Segoe UI", size=12),
                text_color="#8b949e"
            )
            empty_lbl.pack(pady=20)
            return

        for tool in tools:
            self._create_tool_card(tool)

    def _create_tool_card(self, tool: dict):
        tool_id = tool.get("id")
        name = tool.get("name", "Herramienta")
        url = tool.get("url", "")
        raw_url = tool.get("raw_url", "")
        releases_url = tool.get("releases_url", f"{url.rstrip('/')}/releases")
        desc = tool.get("description", "")
        is_string_mod = tool.get("is_string_mod", False)
        last_updated = tool.get("last_updated")

        card = ctk.CTkFrame(
            self.tools_container,
            fg_color="#131924",
            border_width=1,
            border_color="#222d3d",
            corner_radius=10
        )
        card.pack(fill="x", pady=6)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=14)

        # Header de la tarjeta de herramienta
        top_row = ctk.CTkFrame(inner, fg_color="transparent")
        top_row.pack(fill="x", pady=(0, 4))

        title_lbl = ctk.CTkLabel(
            top_row,
            text=f"📦 {name}",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            text_color="#f0f6fc",
            anchor="w"
        )
        title_lbl.pack(side="left")

        active_repo_id = self.config_mgr.get_active_repo_id()
        cfg_lang = StarCitizenManager.get_user_cfg_language(self.current_live_path) if self.current_live_path else None
        is_merged = (
            self.config_mgr.is_starstrings_merged()
            and bool(active_repo_id)
            and (self.config_mgr.get_starstrings_merged_into() == active_repo_id)
        )
        is_tool_active = (active_repo_id == tool_id) and (cfg_lang in ["en", "english"])
        has_community_lang = bool(active_repo_id) and bool(cfg_lang) and (cfg_lang.lower() not in ["en", "english"])

        tag_text = t("badge_mod_qol") if is_string_mod else t("badge_ext_tool")
        tag_color = "#1f2937"
        tag_text_color = "#58a6ff" if is_string_mod else "#a371f7"

        tag_badge = ctk.CTkLabel(
            top_row,
            text=tag_text,
            fg_color=tag_color,
            text_color=tag_text_color,
            corner_radius=5,
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            padx=8,
            pady=2
        )
        tag_badge.pack(side="left", padx=(10, 0))

        if is_merged:
            status_badge = ctk.CTkLabel(
                top_row,
                text="✨ FUSIONADO CON TRADUCCIÓN",
                fg_color="#0d3b66",
                text_color="#00b4d8",
                corner_radius=5,
                font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
                padx=8,
                pady=2
            )
            status_badge.pack(side="left", padx=(8, 0))
        elif is_tool_active:
            status_badge = ctk.CTkLabel(
                top_row,
                text="✓ " + t("badge_active_cfg"),
                fg_color="#1b4332",
                text_color="#2ea043",
                corner_radius=5,
                font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
                padx=8,
                pady=2
            )
            status_badge.pack(side="left", padx=(8, 0))

        # Descripción
        if desc:
            desc_lbl = ctk.CTkLabel(
                inner,
                text=desc,
                font=ctk.CTkFont(family="Segoe UI", size=12),
                text_color="#c9d1d9",
                anchor="w",
                justify="left",
                wraplength=600
            )
            desc_lbl.pack(fill="x", pady=(2, 4))

        # Enlace y fecha
        meta_row = ctk.CTkFrame(inner, fg_color="transparent")
        meta_row.pack(fill="x", pady=(2, 10))

        url_lbl = ctk.CTkLabel(
            meta_row,
            text=f"GitHub: {url}",
            font=ctk.CTkFont(family="Consolas", size=11),
            text_color="#58a6ff",
            anchor="w"
        )
        url_lbl.pack(side="left")

        date_str = t("tool_last_installed", date=last_updated) if last_updated else ""
        if date_str:
            date_lbl = ctk.CTkLabel(
                meta_row,
                text=f"•  {date_str}",
                font=ctk.CTkFont(family="Segoe UI", size=11),
                text_color="#8b949e"
            )
            date_lbl.pack(side="left", padx=(12, 0))

        # Botones de Acción
        actions_row = ctk.CTkFrame(inner, fg_color="transparent")
        actions_row.pack(fill="x")

        # Si es un mod instalable de strings como StarStrings
        if is_string_mod:
            if is_merged:
                btn_revert = ctk.CTkButton(
                    actions_row,
                    text="↩️ Quitar de Traducción",
                    width=170,
                    height=32,
                    fg_color="#da3633",
                    hover_color="#b91c1c",
                    text_color="#ffffff",
                    font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                    command=lambda t=tool: self._action_revert_starstrings_merge(t)
                )
                btn_revert.pack(side="left", padx=(0, 8))

                btn_upd = ctk.CTkButton(
                    actions_row,
                    text="🔄 Actualizar Fusión",
                    width=140,
                    height=32,
                    fg_color="#1f6feb",
                    hover_color="#388bfd",
                    text_color="#ffffff",
                    font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                    command=lambda t=tool: self._action_merge_starstrings(t)
                )
                btn_upd.pack(side="left", padx=(0, 8))
            elif is_tool_active:
                btn_upd = ctk.CTkButton(
                    actions_row,
                    text=t("btn_update"),
                    width=130,
                    height=32,
                    fg_color="#1f6feb",
                    hover_color="#388bfd",
                    text_color="#ffffff",
                    font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                    command=lambda t=tool: self._action_install_tool_string_mod(t)
                )
                btn_upd.pack(side="left", padx=(0, 8))
            elif has_community_lang:
                btn_merge = ctk.CTkButton(
                    actions_row,
                    text="✨ Fusionar con Traducción Activa",
                    width=230,
                    height=32,
                    fg_color="#0077b6",
                    hover_color="#0096c7",
                    text_color="#ffffff",
                    font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                    command=lambda t=tool: self._action_merge_starstrings(t)
                )
                btn_merge.pack(side="left", padx=(0, 8))

                btn_en = ctk.CTkButton(
                    actions_row,
                    text="🌐 Activar en Inglés",
                    width=140,
                    height=32,
                    fg_color="#21262d",
                    hover_color="#30363d",
                    text_color="#c9d1d9",
                    font=ctk.CTkFont(family="Segoe UI", size=11),
                    command=lambda t=tool: self._action_install_tool_string_mod(t)
                )
                btn_en.pack(side="left", padx=(0, 8))
            else:
                btn_install = ctk.CTkButton(
                    actions_row,
                    text=t("btn_install_tool_mod"),
                    width=160,
                    height=32,
                    fg_color="#0077b6",
                    hover_color="#0096c7",
                    text_color="#ffffff",
                    font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                    command=lambda t=tool: self._action_install_tool_string_mod(t)
                )
                btn_install.pack(side="left", padx=(0, 8))

        btn_web = ctk.CTkButton(
            actions_row,
            text=t("btn_view_github"),
            width=130,
            height=32,
            fg_color="#21262d",
            hover_color="#30363d",
            text_color="#f0f6fc",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            command=lambda u=url: webbrowser.open(u)
        )
        btn_web.pack(side="left", padx=(0, 8))

        if releases_url:
            btn_rel = ctk.CTkButton(
                actions_row,
                text=t("btn_view_releases"),
                width=120,
                height=32,
                fg_color="#21262d",
                hover_color="#30363d",
                text_color="#c9d1d9",
                font=ctk.CTkFont(family="Segoe UI", size=11),
                command=lambda ru=releases_url: webbrowser.open(ru)
            )
            btn_rel.pack(side="left", padx=(0, 8))

        btn_del = ctk.CTkButton(
            actions_row,
            text="🗑️",
            width=36,
            height=32,
            fg_color="#21262d",
            hover_color="#da3633",
            text_color="#f85149",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            command=lambda tid=tool_id, tname=name: self._action_delete_tool(tid, tname)
        )
        btn_del.pack(side="right")

    def _action_open_add_tool_dialog(self):
        def _on_save(name, url, desc, raw_url, is_string_mod):
            new_item = self.config_mgr.add_tool(
                name=name,
                url=url,
                description=desc,
                raw_url=raw_url,
                is_string_mod=is_string_mod
            )
            self.log(f"Herramienta añadida: '{name}'", "SUCCESS")
            self._refresh_tools_cards()

            if is_string_mod and raw_url:
                if messagebox.askyesno(t("msg_info"), t("msg_tool_prompt_install", name=name)):
                    self._action_install_tool_string_mod(new_item)

        AddToolDialog(self, _on_save)

    def _action_merge_starstrings(self, tool: dict):
        """Descarga y fusiona las líneas de StarStrings directamente en la traducción activa."""
        if not StarCitizenManager.is_valid_live_directory(self.current_live_path):
            messagebox.showwarning(t("msg_attention"), t("msg_select_live_first"))
            return

        name = tool.get("name", "StarStrings")
        active_repo_id = self.config_mgr.get_active_repo_id()
        if not active_repo_id:
            active_repo_id = "thord82-es"

        self.log(f"Iniciando fusión de StarStrings sobre la traducción activa ('{active_repo_id}')...", "INFO")
        self.download_progress_bar.set(0.1)

        def _worker():
            def _progress_cb(status_text, pct):
                self.log(status_text, "INFO")
                self.after(0, lambda: self.download_progress_bar.set(pct))

            success, message, count = StarCitizenManager.apply_starstrings_to_active_translation(
                self.current_live_path,
                active_repo_id=active_repo_id,
                progress_callback=_progress_cb
            )

            def _done():
                self.download_progress_bar.set(1.0 if success else 0.0)
                if success:
                    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    self.config_mgr.update_tool_timestamp(tool.get("id"), now_str)
                    self.config_mgr.set_starstrings_merged_into(active_repo_id)
                    self._refresh_tools_cards()
                    self._refresh_repository_cards()
                    self._check_user_cfg_status()
                    self.log(f"¡{count} líneas de StarStrings fusionadas exitosamente en tu traducción!", "SUCCESS")
                    messagebox.showinfo(
                        "Fusión Exitosa",
                        f"¡Las mejoras de StarStrings se han fusionado exitosamente en tu traducción!\n\n"
                        f"• {count} líneas añadidas/actualizadas (clasificación de componentes, misiles y misiones [BP]/[Rep]).\n"
                        f"• Tu juego permanece 100% en español (o tu idioma activo).\n"
                        f"• Puedes quitar la fusión en cualquier momento pulsando 'Quitar de Traducción'."
                    )
                else:
                    self.log(f"Error fusionando StarStrings: {message}", "ERROR")
                    messagebox.showerror(t("msg_error"), f"{message}")

            self.after(0, _done)

        threading.Thread(target=_worker, daemon=True).start()

    def _action_revert_starstrings_merge(self, tool: dict):
        """Restaura la traducción activa a su versión limpia original desde el caché."""
        if not StarCitizenManager.is_valid_live_directory(self.current_live_path):
            messagebox.showwarning(t("msg_attention"), t("msg_select_live_first"))
            return

        name = tool.get("name", "StarStrings")
        active_repo_id = self.config_mgr.get_active_repo_id() or "thord82-es"

        ok, msg = StarCitizenManager.revert_starstrings_from_active_translation(
            self.current_live_path,
            active_repo_id
        )
        if ok:
            self.config_mgr.set_starstrings_merged_into(None)
            self._refresh_tools_cards()
            self._refresh_repository_cards()
            self._check_user_cfg_status()
            self.log("Traducción restaurada a su versión limpia original sin StarStrings.", "SUCCESS")
            messagebox.showinfo(
                "Restauración Completada",
                "Se ha restaurado la traducción activa a su versión original limpia sin StarStrings."
            )
        else:
            self.log(f"Error al revertir: {msg}", "ERROR")
            messagebox.showerror(t("msg_error"), msg)

    def _action_activate_tool_string_mod(self, tool: dict):
        """Activa un mod de strings desde el caché local."""
        if not StarCitizenManager.is_valid_live_directory(self.current_live_path):
            messagebox.showwarning(t("msg_attention"), t("msg_select_live_first"))
            return

        name = tool.get("name", "StarStrings")
        tool_id = tool.get("id", "starstrings")

        current_cfg_lang = StarCitizenManager.get_user_cfg_language(self.current_live_path)
        if current_cfg_lang and current_cfg_lang.lower() not in ["en", "english"]:
            msg = (
                f"Aviso de Compatibilidad e Idioma:\n\n"
                f"'{name}' es una modificación de textos y etiquetas en INGLÉS.\n"
                f"Actualmente tienes activada una traducción ({current_cfg_lang}).\n\n"
                f"Star Citizen únicamente carga una localización a la vez en el juego. "
                f"Al activar '{name}', el juego pasará a estar en inglés con las mejoras del mod, "
                f"y tu traducción al español quedará guardada en caché pero inactiva en el juego.\n\n"
                f"(Podrás volver a reactivar tu traducción en cualquier momento desde la pestaña de Traducciones).\n\n"
                f"¿Deseas activar '{name}' ahora?"
            )
            if not messagebox.askyesno(t("msg_attention"), msg):
                return

        ok, msg = StarCitizenManager.activate_translation(
            self.current_live_path,
            repo_id=tool_id,
            sync_english=True
        )
        if ok:
            self.config_mgr.set_active_repo_id(tool_id)
            self._refresh_tools_cards()
            self._refresh_repository_cards()
            self._check_user_cfg_status()
            self.log(f"¡'{name}' activado con éxito! Se quitaron las extensiones a las demás traducciones.", "SUCCESS")
            messagebox.showinfo(
                t("msg_tool_installed_title"),
                f"¡Mod '{name}' activado!\nSe quitaron las extensiones a las demás traducciones para evitar conflictos en el juego."
            )
        else:
            self.log(f"Error activando '{name}': {msg}", "ERROR")
            messagebox.showerror(t("msg_error"), msg)

    def _action_install_tool_string_mod(self, tool: dict):
        """Descarga e instala un mod de localización como StarStrings."""
        if not StarCitizenManager.is_valid_live_directory(self.current_live_path):
            messagebox.showwarning(t("msg_attention"), t("msg_select_live_first"))
            return

        name = tool.get("name", "StarStrings")
        url = tool.get("url", "")
        raw_url = tool.get("raw_url") or url
        tool_id = tool.get("id", "starstrings")
        download_url = url if (url and "github.com" in url) else raw_url

        current_cfg_lang = StarCitizenManager.get_user_cfg_language(self.current_live_path)
        if current_cfg_lang and current_cfg_lang.lower() not in ["en", "english"]:
            msg = (
                f"Aviso de Compatibilidad e Idioma:\n\n"
                f"'{name}' es una modificación de textos y etiquetas en INGLÉS oficial.\n"
                f"Actualmente tienes activada una traducción ({current_cfg_lang}).\n\n"
                f"Star Citizen únicamente carga una localización a la vez en el juego. "
                f"Al activar '{name}', el juego pasará a estar en inglés con las mejoras del mod, "
                f"y tu traducción quedará guardada en caché pero inactiva en el juego.\n\n"
                f"(Podrás volver a reactivar tu traducción en cualquier momento desde la pestaña de Traducciones).\n\n"
                f"¿Deseas descargar y activar '{name}' ahora?"
            )
            if not messagebox.askyesno(t("msg_attention"), msg):
                return

        self.log(f"Iniciando descarga e instalación de mod: '{name}'...", "INFO")
        self.download_progress_bar.set(0.1)

        def _worker():
            def _progress_cb(status_text, pct):
                self.log(status_text, "INFO")
                self.after(0, lambda: self.download_progress_bar.set(pct))

            success, message = StarCitizenManager.download_and_install_translation(
                self.current_live_path,
                download_url,
                repo_id=tool_id,
                progress_callback=_progress_cb,
                sync_english=True
            )

            def _done():
                self.download_progress_bar.set(1.0 if success else 0.0)
                if success:
                    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    self.config_mgr.update_tool_timestamp(tool.get("id"), now_str)
                    self.config_mgr.set_active_repo_id(tool_id)
                    self._refresh_tools_cards()
                    self._refresh_repository_cards()
                    self._check_user_cfg_status()
                    self.log(f"¡'{name}' instalado y activado con éxito!", "SUCCESS")
                    messagebox.showinfo(
                        t("msg_tool_installed_title"),
                        t("msg_tool_installed_body", name=name)
                    )
                else:
                    self.log(f"Error instalando '{name}': {message}", "ERROR")
                    messagebox.showerror(t("msg_error"), f"{message}")

            self.after(0, _done)

        threading.Thread(target=_worker, daemon=True).start()

    # ==========================
    # SECCIÓN INFERIOR PERMANENTE (LANZAMIENTO Y CONSOLA)
    # ==========================
    def _build_bottom_section(self):
        bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        bottom_frame.pack(fill="x", padx=20, pady=(2, 14), side="bottom")

        # Tarjeta de Lanzamiento
        launch_card = ctk.CTkFrame(
            bottom_frame,
            fg_color="#101827",
            border_width=2,
            border_color="#0077b6",
            corner_radius=10
        )
        launch_card.pack(fill="x", pady=(0, 8))

        inner_launch = ctk.CTkFrame(launch_card, fg_color="transparent")
        inner_launch.pack(fill="x", padx=16, pady=10)

        info_box = ctk.CTkFrame(inner_launch, fg_color="transparent")
        info_box.pack(side="left", fill="both", expand=True)

        self.lbl_sc = ctk.CTkLabel(
            info_box,
            text=t("launch_title"),
            font=ctk.CTkFont(family="Consolas", size=15, weight="bold"),
            text_color="#00b4d8",
            anchor="w"
        )
        self.lbl_sc.pack(fill="x")

        self.launch_info_lbl = ctk.CTkLabel(
            info_box,
            text=t("launch_desc"),
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color="#8b949e",
            anchor="w"
        )
        self.launch_info_lbl.pack(fill="x")

        self.btn_launch_game = ctk.CTkButton(
            inner_launch,
            text=t("btn_launch_game"),
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            fg_color="#0077b6",
            hover_color="#0096c7",
            text_color="#ffffff",
            width=260,
            height=44,
            corner_radius=8,
            command=self._action_launch_launcher
        )
        self.btn_launch_game.pack(side="right")

        # Consola de Registros
        console_card = ctk.CTkFrame(
            bottom_frame,
            fg_color="#131924",
            border_width=1,
            border_color="#222d3d",
            corner_radius=8
        )
        console_card.pack(fill="x")

        header_c = ctk.CTkFrame(console_card, fg_color="transparent")
        header_c.pack(fill="x", padx=14, pady=(6, 2))

        self.lbl_log_title = ctk.CTkLabel(
            header_c,
            text=t("log_title"),
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color="#8b949e"
        )
        self.lbl_log_title.pack(side="left")

        self.btn_clear_log = ctk.CTkButton(
            header_c,
            text=t("btn_clear_log"),
            width=65,
            height=20,
            fg_color="#1c2128",
            hover_color="#30363d",
            text_color="#8b949e",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            command=self._clear_log
        )
        self.btn_clear_log.pack(side="right")

        self.log_textbox = ctk.CTkTextbox(
            console_card,
            height=85,
            fg_color="#090d13",
            text_color="#00e676",
            font=ctk.CTkFont(family="Consolas", size=10),
            corner_radius=6,
            border_width=1,
            border_color="#1e2633"
        )
        self.log_textbox.pack(fill="x", padx=14, pady=(0, 10))
        self.log_textbox.configure(state="disabled")

    # ==========================
    # REGISTROS Y MENSAJES
    # ==========================
    def log(self, message: str, level: str = "INFO"):
        """Escribe un mensaje formateado con hora en la consola de la UI."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        prefix = {
            "INFO": "ℹ️",
            "SUCCESS": "✅",
            "WARN": "⚠️",
            "ERROR": "❌"
        }.get(level, "•")

        entry = f"[{timestamp}] {prefix} {message}\n"

        def _append():
            self.log_textbox.configure(state="normal")
            self.log_textbox.insert("end", entry)
            self.log_textbox.see("end")
            self.log_textbox.configure(state="disabled")

        self.after(0, _append)

    def _clear_log(self):
        self.log_textbox.configure(state="normal")
        self.log_textbox.delete("1.0", "end")
        self.log_textbox.configure(state="disabled")

    # ==========================
    # DETECCIÓN Y VALIDACIÓN DE RUTA
    # ==========================
    def _initialize_path(self):
        self.log("Iniciando Star Citizen Launcher & Gestor de Comunidad...")
        saved_path = self.config_mgr.get_live_path()
        if saved_path and StarCitizenManager.is_valid_live_directory(saved_path):
            self.log(f"Ruta cargada desde configuración: {saved_path}")
            self._set_current_path(saved_path)
        else:
            self.log("Detectando automáticamente instalación de Star Citizen...")
            self._action_auto_detect()

    def _set_current_path(self, path: str):
        self.current_live_path = path.strip()
        self.path_entry.delete(0, "end")
        self.path_entry.insert(0, self.current_live_path)
        self.config_mgr.set_live_path(self.current_live_path)
        self._validate_and_update_ui()

    def _validate_and_update_ui(self):
        path = self.current_live_path
        is_valid = StarCitizenManager.is_valid_live_directory(path)
        launcher_path = StarCitizenManager.get_launcher_executable_path(path)
        exe_path = StarCitizenManager.get_executable_path(path) if is_valid else None

        if launcher_path:
            self.path_valid_badge.configure(
                text=t("badge_valid_path"),
                fg_color="#1a472a",
                text_color="#56d364"
            )
            self.launch_info_lbl.configure(
                text=f"RSI Launcher: {launcher_path}",
                text_color="#56d364"
            )
            self.top_status_badge.configure(
                text=t("badge_ready"),
                fg_color="#1a472a",
                text_color="#56d364"
            )
            self.btn_launch_game.configure(state="normal")
        elif is_valid and exe_path:
            self.path_valid_badge.configure(
                text=t("badge_valid_path"),
                fg_color="#1a472a",
                text_color="#56d364"
            )
            self.launch_info_lbl.configure(
                text=f"Direct: {exe_path}",
                text_color="#56d364"
            )
            self.top_status_badge.configure(
                text=t("badge_active"),
                fg_color="#1a472a",
                text_color="#56d364"
            )
            self.btn_launch_game.configure(state="normal")
        elif is_valid:
            self.path_valid_badge.configure(
                text=t("badge_checking"),
                fg_color="#4d3800",
                text_color="#e3b341"
            )
            self.launch_info_lbl.configure(
                text=t("launch_desc"),
                text_color="#e3b341"
            )
            self.top_status_badge.configure(
                text=t("badge_checking"),
                fg_color="#4d3800",
                text_color="#e3b341"
            )
            self.btn_launch_game.configure(state="normal")
        else:
            self.path_valid_badge.configure(
                text=t("badge_invalid_path"),
                fg_color="#4d1b1f",
                text_color="#f85149"
            )
            self.launch_info_lbl.configure(
                text=t("cfg_status_no_live"),
                text_color="#f85149"
            )
            self.top_status_badge.configure(
                text=t("badge_disabled"),
                fg_color="#4d1b1f",
                text_color="#f85149"
            )
            self.btn_launch_game.configure(state="disabled")

        self._check_user_cfg_status()

    def _action_auto_detect(self):
        def _worker():
            detected = StarCitizenManager.auto_detect_live_directory()
            if detected:
                self.log(f"Instalación encontrada automáticamente: {detected}", "SUCCESS")
                self.after(0, lambda: self._set_current_path(detected))
            else:
                self.log("No se pudo detectar automáticamente la carpeta LIVE. Selecciónala manualmente.", "WARN")
                self.after(0, lambda: self._validate_and_update_ui())

        threading.Thread(target=_worker, daemon=True).start()

    def _action_browse_path(self):
        chosen = filedialog.askdirectory(
            title="Selecciona la carpeta LIVE de Star Citizen",
            initialdir=self.current_live_path or "C:\\"
        )
        if chosen:
            self._set_current_path(chosen)
            self.log(f"Ruta seleccionada manualmente: {chosen}", "INFO")

    def _on_manual_path_entered(self):
        new_val = self.path_entry.get().strip()
        if new_val != self.current_live_path:
            self._set_current_path(new_val)
            self.log(f"Ruta actualizada manualmente: {new_val}", "INFO")

    # ==========================
    # GESTOR DE USER.CFG
    # ==========================
    def _check_user_cfg_status(self):
        if not self.current_live_path or not os.path.isdir(self.current_live_path):
            self.cfg_badge.configure(text=t("cfg_badge_missing"), fg_color="#21262d", text_color="#8b949e")
            self.cfg_status_lbl.configure(text=t("cfg_status_no_live"))
            return

        status = StarCitizenManager.get_translation_status(self.current_live_path)
        cfg_lang = status.get("cfg_lang")
        has_ini = status.get("has_ini")
        has_no_ext = status.get("has_no_ext")

        if has_ini and cfg_lang and cfg_lang.lower() in ["en", "english"]:
            self.cfg_badge.configure(
                text=t("cfg_badge_configured"),
                fg_color="#1a472a",
                text_color="#56d364"
            )
            self.cfg_status_lbl.configure(
                text=t("cfg_status_active"),
                text_color="#56d364"
            )
        elif has_no_ext and not has_ini:
            self.cfg_badge.configure(
                text=t("cfg_badge_file_disabled"),
                fg_color="#30363d",
                text_color="#d29922"
            )
            self.cfg_status_lbl.configure(
                text=t("cfg_status_disabled_ext"),
                text_color="#d29922"
            )
        elif has_ini:
            self.cfg_badge.configure(
                text=t("cfg_badge_no_directive"),
                fg_color="#1f2937",
                text_color="#58a6ff"
            )
            self.cfg_status_lbl.configure(
                text=t("cfg_status_disabled_directive"),
                text_color="#c9d1d9"
            )
        else:
            self.cfg_badge.configure(
                text=t("cfg_badge_missing"),
                fg_color="#21262d",
                text_color="#8b949e"
            )
            self.cfg_status_lbl.configure(
                text=t("cfg_status_not_found"),
                text_color="#8b949e"
            )

    def _action_set_cfg_en(self):
        if not StarCitizenManager.is_valid_live_directory(self.current_live_path):
            messagebox.showwarning(t("msg_attention"), t("msg_select_live_first"))
            return

        active_id = self.config_mgr.get_active_repo_id()
        ok, msg = StarCitizenManager.enable_translation(self.current_live_path, active_id, "en")
        if ok:
            self.log("Traducción activada: Se quitaron extensiones a las demás y se restauró la extensión .ini únicamente a la activa.", "SUCCESS")
            self._check_user_cfg_status()
            messagebox.showinfo(t("msg_enabled_title"), t("msg_enabled_body"))
        else:
            self.log(f"Error activando traducción: {msg}", "ERROR")
            messagebox.showerror(t("msg_error"), msg)

    def _action_disable_cfg(self):
        if not StarCitizenManager.is_valid_live_directory(self.current_live_path):
            return

        ok, msg = StarCitizenManager.disable_translation(self.current_live_path)
        if ok:
            self.log("Traducción desactivada: Se quitaron todas las extensiones (renombrados a sin extensión). El juego cargará en inglés original.", "SUCCESS")
            self._check_user_cfg_status()
            messagebox.showinfo(
                t("msg_disabled_title"),
                t("msg_disabled_body")
            )
        else:
            self.log(f"Error desactivando traducción: {msg}", "ERROR")
            messagebox.showerror(t("msg_error"), msg)

    def _action_open_cfg_file(self):
        if not self.current_live_path or not os.path.isdir(self.current_live_path):
            return

        cfg_path = StarCitizenManager.get_user_cfg_path(self.current_live_path)
        if not os.path.exists(cfg_path):
            with open(cfg_path, "w", encoding="utf-8") as f:
                f.write("; Archivo user.cfg generado por Star Citizen Launcher\n")

        try:
            os.startfile(cfg_path)
            self.log(f"Abierto archivo: {cfg_path}", "INFO")
        except Exception as e:
            self.log(f"Error abriendo user.cfg: {e}", "ERROR")

    # ==========================
    # GESTIÓN DE REPOSITORIOS Y ACTUALIZACIÓN
    # ==========================
    def _refresh_repository_cards(self):
        for widget in self.repos_container.winfo_children():
            widget.destroy()

        repos = self.config_mgr.get_repositories()
        if not repos:
            no_lbl = ctk.CTkLabel(
                self.repos_container,
                text=t("no_repos_msg"),
                font=ctk.CTkFont(family="Segoe UI", size=12),
                text_color="#8b949e"
            )
            no_lbl.pack(pady=15)
            return

        for repo in repos:
            self._create_repo_card(repo)

    def _create_repo_card(self, repo: dict):
        repo_id = repo.get("id")
        name = repo.get("name", "Traducción")
        url = repo.get("url", "")
        last_updated = repo.get("last_updated")

        card = ctk.CTkFrame(
            self.repos_container,
            fg_color="#0e131b",
            border_width=1,
            border_color="#1e2736",
            corner_radius=8
        )
        card.pack(fill="x", pady=5)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=14, pady=10)

        left = ctk.CTkFrame(inner, fg_color="transparent")
        left.pack(side="left", fill="both", expand=True)

        name_lbl = ctk.CTkLabel(
            left,
            text=f"🌐 {name}",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color="#f0f6fc",
            anchor="w"
        )
        name_lbl.pack(fill="x")

        url_lbl = ctk.CTkLabel(
            left,
            text=f"URL: {url}",
            font=ctk.CTkFont(family="Consolas", size=11),
            text_color="#58a6ff",
            anchor="w"
        )
        url_lbl.pack(fill="x", pady=(1, 1))

        date_str = t("repo_last_download", date=last_updated) if last_updated else "---"
        date_lbl = ctk.CTkLabel(
            left,
            text=date_str,
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color="#8b949e",
            anchor="w"
        )
        date_lbl.pack(fill="x")

        right = ctk.CTkFrame(inner, fg_color="transparent")
        right.pack(side="right")

        btn_update = ctk.CTkButton(
            right,
            text=t("btn_update"),
            width=100,
            height=32,
            fg_color="#1f6feb",
            hover_color="#388bfd",
            text_color="#ffffff",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            command=lambda r=repo: self._action_update_translation(r)
        )
        btn_update.pack(side="left", padx=(0, 6))

        btn_activate = ctk.CTkButton(
            right,
            text=t("btn_activate"),
            width=85,
            height=32,
            fg_color="#238636",
            hover_color="#2ea043",
            text_color="#ffffff",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            command=lambda r=repo: self._action_activate_translation(r)
        )
        btn_activate.pack(side="left", padx=(0, 6))

        btn_del = ctk.CTkButton(
            right,
            text="🗑️",
            width=34,
            height=32,
            fg_color="#21262d",
            hover_color="#da3633",
            text_color="#f85149",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            command=lambda rid=repo_id, rname=name: self._action_delete_repo(rid, rname)
        )
        btn_del.pack(side="left")

    def _action_open_add_repo_dialog(self):
        def _on_save(name, url, raw_url):
            new_item = self.config_mgr.add_repository(name, url, raw_url)
            self.log(f"Repositorio añadido: {name} ({url})", "SUCCESS")
            self._refresh_repository_cards()

            if messagebox.askyesno(t("msg_info"), f"¿Deseas descargar y aplicar '{name}' ahora?"):
                self._action_update_translation(new_item)

        AddRepoDialog(self, _on_save)

    def _action_delete_repo(self, repo_id: str, repo_name: str):
        if messagebox.askyesno(t("msg_attention"), t("msg_confirm_delete_repo", name=repo_name)):
            self.config_mgr.remove_repository(repo_id)
            self.log(f"Repositorio eliminado: {repo_name}", "INFO")
            self._refresh_repository_cards()

    def _action_activate_translation(self, repo: dict):
        if not StarCitizenManager.is_valid_live_directory(self.current_live_path):
            messagebox.showwarning(t("msg_attention"), t("msg_select_live_first"))
            return

        repo_id = repo.get("id", "")
        repo_name = repo.get("name", "Traducción")

        if StarCitizenManager.is_cached(repo_id):
            ok, msg = StarCitizenManager.activate_translation(self.current_live_path, repo_id, sync_english=True)
            if ok:
                self.config_mgr.set_active_repo_id(repo_id)
                self.config_mgr.set_starstrings_merged_into(None)
                self.log(f"Traducción activada: '{repo_name}' es la ÚNICA activa. Se quitaron todas las demás extensiones.", "SUCCESS")
                self._check_user_cfg_status()
                self._refresh_repository_cards()
                self._refresh_tools_cards()
                messagebox.showinfo(
                    t("msg_enabled_title"),
                    f"¡Traducción '{repo_name}' activada como la única activa!\n(Se quitaron las extensiones a las demás traducciones)."
                )
            else:
                self.log(f"Error activando traducción: {msg}", "ERROR")
                messagebox.showerror(t("msg_error"), msg)
        else:
            self.log(f"Traducción '{repo_name}' no encontrada en caché local. Descargando automáticamente...", "INFO")
            self._action_update_translation(repo)

    def _action_update_translation(self, repo: dict):
        r"""
        Descarga global.ini desde la URL raw de GitHub.
        Crea \data\Localization\en\ y pega el archivo allí.
        Asegura que user.cfg tenga g_language = en.
        """
        if not StarCitizenManager.is_valid_live_directory(self.current_live_path):
            messagebox.showwarning(t("msg_attention"), t("msg_select_live_first"))
            return

        name = repo.get("name", "Traducción")
        repo_url = repo.get("url", "")
        raw_url = repo.get("raw_url") or repo_url

        self.log(f"Iniciando actualización de traducción: '{name}'...", "INFO")
        self.download_progress_bar.set(0.1)

        def _worker():
            def _progress_cb(status_text, pct):
                self.log(status_text, "INFO")
                self.after(0, lambda: self.download_progress_bar.set(pct))

            _progress_cb("Buscando actualización oficial en el repositorio...", 0.15)
            download_url = repo_url if (repo_url and "github.com" in repo_url) else (raw_url or repo_url)

            success, message = StarCitizenManager.download_and_install_translation(
                self.current_live_path,
                download_url,
                repo_id=repo.get("id", "custom"),
                progress_callback=_progress_cb,
                sync_english=True
            )

            def _done():
                self.download_progress_bar.set(1.0 if success else 0.0)
                if success:
                    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    self.config_mgr.update_repository_timestamp(repo.get("id"), now_str)
                    self.config_mgr.set_active_repo_id(repo.get("id"))
                    self._refresh_repository_cards()
                    self._refresh_tools_cards()
                    self._check_user_cfg_status()
                    self.log(f"¡Actualización completada con éxito para '{name}'!", "SUCCESS")
                    messagebox.showinfo(
                        t("msg_repo_installed_title"),
                        t("msg_repo_installed_body", name=name)
                    )
                else:
                    self.log(f"Fallo al actualizar traducción: {message}", "ERROR")
                    messagebox.showerror(t("msg_error"), f"{message}")

            self.after(0, _done)

        threading.Thread(target=_worker, daemon=True).start()

    # ==========================
    # CAMBIO DINÁMICO DE IDIOMA DE LA APLICACIÓN
    # ==========================
    def _on_app_language_changed(self, choice_display: str):
        """Manejador ejecutado cuando el usuario cambia el idioma de la aplicación."""
        new_code = get_code_from_display_name(choice_display)
        if new_code == get_current_language():
            return

        set_current_language(new_code)
        self.config_mgr.set_app_language(new_code)
        self._update_ui_texts()
        self.log(t("log_lang_changed", lang=choice_display), "INFO")

    def _update_ui_texts(self):
        """Actualiza todos los textos visuales de la interfaz dinámicamente."""
        # Ventana y cabecera
        self.title(t("window_title"))
        self.lbl_app_title.configure(text=t("app_title"))
        self.lbl_app_sub.configure(text=t("app_subtitle"))
        self.lbl_app_lang.configure(text=t("app_lang_label"))

        # Pestañas
        new_trans = t("tab_translations")
        new_tools = t("tab_tools")
        if self.current_tab_trans_name != new_trans:
            try:
                self.tabview.rename(self.current_tab_trans_name, new_trans)
                self.current_tab_trans_name = new_trans
            except Exception:
                pass
        if self.current_tab_tools_name != new_tools:
            try:
                self.tabview.rename(self.current_tab_tools_name, new_tools)
                self.current_tab_tools_name = new_tools
            except Exception:
                pass

        # Barra de ruta
        self.lbl_path.configure(text=t("path_label"))
        self.btn_auto_detect.configure(text=t("btn_auto_detect"))
        self.btn_browse.configure(text=t("btn_browse"))

        # Tarjeta Selector Oficial
        self.lbl_lang_card_title.configure(text=t("lang_selector_title"))
        self.badge_lang_catalog.configure(text=t("lang_selector_badge"))
        self.desc_lang_card.configure(text=t("lang_selector_desc"))
        self.btn_load_all.configure(text=t("btn_load_all_languages"))
        self._on_language_selector_changed(self.lang_option_menu.get())

        # Tarjeta Repositorios
        self.lbl_repos_title.configure(text=t("repos_card_title"))
        self.btn_add_repo.configure(text=t("btn_add_repo"))
        self._refresh_repository_cards()

        # Tarjeta user.cfg
        self.lbl_cfg_title.configure(text=t("cfg_card_title"))
        self.btn_force_en.configure(text=t("btn_force_en"))
        self.btn_disable_trans.configure(text=t("btn_disable_trans"))
        self.btn_open_cfg.configure(text=t("btn_open_cfg"))
        self._check_user_cfg_status()

        # Pestaña Herramientas
        self.lbl_tools_title.configure(text=t("tools_info_title"))
        self.lbl_tools_desc.configure(text=t("tools_info_desc"))
        self.btn_add_tool.configure(text=t("btn_add_tool"))
        self._refresh_tools_cards()

        # Sección inferior
        self.lbl_sc.configure(text=t("launch_title"))
        self.launch_info_lbl.configure(text=t("launch_desc"))
        self.btn_launch_game.configure(text=t("btn_launch_game"))
        self.lbl_log_title.configure(text=t("log_title"))
        self.btn_clear_log.configure(text=t("btn_clear_log"))

        # Refrescar estados de ruta y badges
        self._validate_and_update_ui()

    # ==========================
    # LANZAMIENTO DEL LAUNCHER DEL JUEGO
    # ==========================
    def _action_launch_launcher(self):
        """Inicia el RSI Launcher oficial del juego."""
        launcher_path = StarCitizenManager.get_launcher_executable_path(self.current_live_path)
        if not launcher_path and not StarCitizenManager.is_valid_live_directory(self.current_live_path):
            messagebox.showwarning(t("msg_attention"), t("msg_launcher_not_found"))
            return

        self.log("Iniciando el launcher oficial de Star Citizen (RSI Launcher)...", "INFO")
        ok, msg = StarCitizenManager.launch_game_launcher(self.current_live_path)
        if ok:
            self.log("¡RSI Launcher iniciado con éxito! ¡Buen vuelo, ciudadano! 🚀", "SUCCESS")
        else:
            self.log(f"Error al iniciar el launcher: {msg}", "ERROR")
            messagebox.showerror(t("msg_error"), msg)

