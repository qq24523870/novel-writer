"""AI小说创作助手 - 移动版"""
import sys, os, traceback

try:
    import flet as ft
except Exception as e:
    os._exit(1)

from utils.logger import logger

I = ft.icons.Icons

def main(page: ft.Page):
    error_container = ft.Container(visible=False)
    main_content = ft.Column(visible=True)

    try:
        page.title = "AI小说创作助手"
        page.theme = ft.Theme(color_scheme_seed="#4A90D9", use_material3=True)
        page.padding = 10
        page.scroll = ft.ScrollMode.AUTO
        page.window.width = 420
        page.window.height = 900

        from models.database import db_manager
        from models.ai_provider import ai_manager

        try:
            db_manager.initialize()
            ai_manager.initialize()
        except Exception as init_err:
            logger.error(f"初始化失败: {init_err}")

        from views.home import HomePage
        from views.project_detail import ProjectDetailPage
        from views.ai_generate import AIGeneratePage
        from views.editor import EditorPage
        from views.settings import SettingsPage

        nav = ft.NavigationBar(
            destinations=[
                ft.NavigationBarDestination(icon=I.HOME_ROUNDED, label="首页"),
                ft.NavigationBarDestination(icon=I.CREATE_ROUNDED, label="AI生成"),
                ft.NavigationBarDestination(icon=I.SETTINGS_ROUNDED, label="设置"),
            ],
            selected_index=0,
        )

        page_all = ft.Column(controls=[], expand=True)

        def navigate(view_name, data=None):
            try:
                page_all.controls.clear()
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
                        page_all.controls.append(content)
                page_all.controls.append(nav)
                page.update()
            except Exception as nav_err:
                page_all.controls.clear()
                page_all.controls.append(ft.Text(f"导航错误: {nav_err}", color=ft.Colors.ERROR))
                page_all.controls.append(nav)
                page.update()

        def on_nav_change(e):
            idx = e.control.selected_index
            maps = {0: "home", 1: "ai_generate", 2: "settings"}
            navigate(maps.get(idx, "home"))

        nav.on_change = on_nav_change
        page.add(page_all)
        navigate("home")

    except Exception as e:
        tb = traceback.format_exc()
        try:
            page.controls.clear()
            page.add(
                ft.Column([
                    ft.Text("应用初始化失败", size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.ERROR),
                    ft.Text(str(e), size=14),
                    ft.Text(tb[-500:], size=10, color=ft.Colors.OUTLINE, selectable=True),
                ], scroll=True)
            )
            page.update()
        except Exception:
            pass


if __name__ == "__main__":
    ft.run(main)
