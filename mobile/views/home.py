"""首页 - 项目列表"""
import sys, os
base = os.path.dirname(os.path.abspath(__file__))
if os.path.exists(os.path.join(base, "core")): sys.path.insert(0, base)
else: sys.path.insert(0, os.path.join(base, ".."))

import flet as ft
from core.writing_core import project_manager

I, C = ft.icons.Icons, ft.Colors

class HomePage:
    def __init__(self, page: ft.Page, navigate, data=None):
        self.page, self.navigate = page, navigate

    def build(self) -> ft.Control:
        try:
            projects = project_manager.get_all_projects()
        except Exception:
            projects = []

        controls = [
            ft.Row([
                ft.Text("AI小说创作助手", size=22, weight=ft.FontWeight.BOLD),
                ft.IconButton(icon=I.INFO_OUTLINE, tooltip="开发者: 青易  QQ:24523870"),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.FilledButton("新建项目", icon=I.ADD, on_click=self._show_create_dialog,
                            style=ft.ButtonStyle(padding=ft.padding.all(14))),
            ft.Divider(),
        ]

        if not projects:
            controls.append(ft.Container(
                content=ft.Column([
                    ft.Icon(I.BOOK, size=48, color=C.OUTLINE),
                    ft.Text("还没有项目\n点击「新建项目」开始创作", size=14,
                            color=C.OUTLINE, text_align=ft.TextAlign.CENTER),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                alignment=ft.alignment.center, padding=ft.padding.all(40)))
        else:
            items = []
            for p in projects:
                pid, name = p["id"], p.get("name", "未命名")
                genre = p.get("genre", "")
                updated = p.get("updated_at", "")[:10]
                wc = 0
                try: wc = project_manager.get_project_word_count(pid)
                except: pass
                items.append(ft.Container(
                    content=ft.ListTile(
                        leading=ft.CircleAvatar(content=ft.Text(name[0] if name else "?"), bgcolor=C.PRIMARY_CONTAINER),
                        title=ft.Text(name, weight=ft.FontWeight.BOLD),
                        subtitle=ft.Text(f"{genre}  |  {wc:,}字  |  {updated}" if genre else f"{wc:,}字  |  {updated}"),
                        trailing=ft.PopupMenuButton(items=[
                            ft.PopupMenuItem(content=ft.Text("打开"), icon=I.FOLDER_OPEN,
                                on_click=lambda e, p=pid, n=name: self.navigate("project_detail", {"pid": p, "name": n})),
                            ft.PopupMenuItem(content=ft.Text("AI续写"), icon=I.AUTO_STORIES,
                                on_click=lambda e, p=pid, n=name: self.navigate("ai_generate", {"pid": p, "name": n, "continuation": True})),
                            ft.PopupMenuItem(content=ft.Text("删除"), icon=I.DELETE,
                                on_click=lambda e, p=pid, n=name: self._delete_project(p, n)),
                        ]),
                        on_click=lambda e, p=pid, n=name: self.navigate("project_detail", {"pid": p, "name": n}),
                    ),
                    border_radius=12, bgcolor=C.SURFACE_CONTAINER_HIGHEST,
                    margin=ft.margin.symmetric(horizontal=8, vertical=3)))
            controls.append(ft.ListView(controls=items, spacing=2, height=480))

        controls.append(ft.Text("开发者: 青易  QQ:24523870", size=11, color=C.OUTLINE, text_align=ft.TextAlign.CENTER))
        return ft.Column(controls)

    def _show_create_dialog(self, e):
        name_field = ft.TextField(label="小说名称", border_radius=8, autofocus=True)
        genre_field = ft.TextField(label="小说类型(选填)", border_radius=8)
        def do_create(ev):
            nm = name_field.value.strip()
            if not nm:
                self._snack("请输入小说名称")
                return
            g = genre_field.value.strip()
            try:
                pid = project_manager.create_project(nm, author="AI创作", genre=g, description="新建项目")
                self.page.pop_dialog()
                self.page.update()
                self.navigate("project_detail", {"pid": pid, "name": nm})
            except Exception as ex:
                self._snack(f"创建失败: {ex}")
        dlg = ft.AlertDialog(
            title=ft.Text("新建小说项目"),
            content=ft.Column([name_field, genre_field], spacing=12, tight=True, height=140),
            actions=[
                ft.TextButton("取消", on_click=lambda ev: self.page.pop_dialog()),
                ft.FilledButton("创建", on_click=do_create),
            ])
        self.page.show_dialog(dlg)

    def _delete_project(self, pid, name):
        def do_delete(ev):
            try:
                project_manager.delete_project(pid)
            except:
                pass
            self.page.pop_dialog()
            self.navigate("home")
        dlg = ft.AlertDialog(
            title=ft.Text(f"确认删除《{name}》？"),
            content=ft.Text("删除后可通过回收站恢复。"),
            actions=[
                ft.TextButton("取消", on_click=lambda ev: self.page.pop_dialog()),
                ft.FilledButton("删除", style=ft.ButtonStyle(bgcolor=C.ERROR), on_click=do_delete),
            ])
        self.page.show_dialog(dlg)

    def _snack(self, msg):
        self.page.snack_bar = ft.SnackBar(ft.Text(msg))
        self.page.snack_bar.open = True
        self.page.update()
