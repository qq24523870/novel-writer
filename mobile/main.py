"""AI小说创作助手 - 移动版"""
import sys, os

base = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, base)
parent = os.path.dirname(base)
if parent not in sys.path: sys.path.insert(0, parent)

import flet as ft
from utils.logger import logger
from utils.config_manager import config_manager
from models.database import db_manager
from models.ai_provider import ai_manager
from views.home import HomePage
from views.project_detail import ProjectDetailPage
from views.ai_generate import AIGeneratePage
from views.editor import EditorPage
from views.settings import SettingsPage

I = ft.icons.Icons

def main(page: ft.Page):
    page.title = "AI小说创作助手"
    page.theme = ft.Theme(color_scheme_seed="#4A90D9", use_material3=True)
    page.padding = 10
    page.scroll = ft.ScrollMode.AUTO
    page.window.width = 420
    page.window.height = 900
    page.window.resizable = True

    try:
        db_manager.initialize()
        ai_manager.initialize()
    except Exception as e:
        logger.error(f"初始化失败: {e}")

    nav = ft.NavigationBar(
        destinations=[
            ft.NavigationBarDestination(icon=I.HOME_ROUNDED, label="首页"),
            ft.NavigationBarDestination(icon=I.CREATE_ROUNDED, label="AI生成"),
            ft.NavigationBarDestination(icon=I.SETTINGS_ROUNDED, label="设置"),
        ],
        selected_index=0,
    )

    def navigate(view_name, data=None):
        page.controls.clear()
        view = None
        if view_name == "home":
            view = HomePage(page, navigate, data)
        elif view_name == "project_detail":
            view = ProjectDetailPage(page, navigate, data)
        elif view_name == "ai_generate":
            view = AIGeneratePage(page, navigate, data)
        elif view_name == "editor":
            view = EditorPage(page, navigate, data)
        elif view_name == "settings":
            view = SettingsPage(page, navigate, data)
        if view is not None:
            content = view.build()
            if content is not None:
                page.controls.append(content)
        page.controls.append(nav)
        page.update()

    def on_nav_change(e):
        idx = e.control.selected_index
        maps = {0: "home", 1: "ai_generate", 2: "settings"}
        navigate(maps.get(idx, "home"))

    nav.on_change = on_nav_change
    navigate("home")

if __name__ == "__main__":
    ft.run(main)
