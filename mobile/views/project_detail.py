"""项目详情 - 卷与章节管理"""
import sys, os
base = os.path.dirname(os.path.abspath(__file__))
if os.path.exists(os.path.join(base, "core")): sys.path.insert(0, base)
else: sys.path.insert(0, os.path.join(base, ".."))

import flet as ft
from core.writing_core import project_manager, volume_manager, chapter_manager

I, C = ft.icons.Icons, ft.Colors

class ProjectDetailPage:
    def __init__(self, page: ft.Page, navigate, data=None):
        self.page, self.navigate = page, navigate
        self.pid = data.get("pid", 0) if data else 0
        self.name = data.get("name", "") if data else ""

    def build(self) -> ft.Control:
        try: vols = volume_manager.get_volumes(self.pid)
        except: vols = []
        try: wc = project_manager.get_project_word_count(self.pid)
        except: wc = 0

        controls = [
            ft.Row([
                ft.IconButton(icon=I.ARROW_BACK, on_click=lambda e: self.navigate("home")),
                ft.Text(self.name, size=20, weight=ft.FontWeight.BOLD),
                ft.Text(f"{wc:,}字", size=13, color=C.OUTLINE),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Row([
                ft.FilledButton("新建卷", icon=I.CREATE_NEW_FOLDER, on_click=self._new_volume),
                ft.FilledButton("新建章", icon=I.NOTE_ADD, on_click=self._new_chapter),
                ft.FilledButton("AI续写", icon=I.AUTO_STORIES,
                    on_click=lambda e: self.navigate("ai_generate", {"pid": self.pid, "name": self.name, "continuation": True})),
            ], spacing=8, wrap=True),
            ft.Divider(),
        ]

        for vol in vols:
            vid = vol["id"]
            vtitle = vol.get("title", f"第{vid}卷")
            chapters = chapter_manager.get_chapters(vid)
            controls.append(ft.Text(f"📁 {vtitle}", weight=ft.FontWeight.BOLD, size=16))
            if not chapters:
                controls.append(ft.Text("   暂无章节", size=13, color=C.OUTLINE, italic=True))
                continue
            for ch in chapters:
                cid = ch["id"]
                ct = ch.get("title", f"第{cid}章")
                ctxt = ch.get("content", "")
                cwc = len(ctxt) if ctxt else 0
                controls.append(ft.Container(
                    content=ft.ListTile(
                        leading=ft.Icon(I.ARTICLE),
                        title=ft.Text(ct, size=14),
                        subtitle=ft.Text(f"{cwc:,}字"),
                        trailing=ft.PopupMenuButton(items=[
                            ft.PopupMenuItem(content=ft.Text("编辑"), icon=I.EDIT,
                                on_click=lambda e, c=cid, t=ct: self.navigate("editor", {"pid": self.pid, "cid": c, "title": t})),
                            ft.PopupMenuItem(content=ft.Text("删除"), icon=I.DELETE,
                                on_click=lambda e, c=cid: self._delete_chapter(c)),
                        ]),
                        on_click=lambda e, c=cid, t=ct: self.navigate("editor", {"pid": self.pid, "cid": c, "title": t}),
                    ),
                    border_radius=8, bgcolor=C.SURFACE_CONTAINER_HIGHEST,
                    margin=ft.Margin.symmetric(vertical=2, horizontal=8)))
        return ft.Column(controls)

    def _new_volume(self, e):
        tf = ft.TextField(label="卷名称", border_radius=8, autofocus=True)
        def create(ev):
            t = tf.value.strip()
            if not t: return
            volume_manager.create_volume(self.pid, t)
            self.page.pop_dialog()
            self.navigate("project_detail", {"pid": self.pid, "name": self.name})
        dlg = ft.AlertDialog(title=ft.Text("新建卷"), content=tf,
            actions=[ft.TextButton("取消", on_click=lambda ev: self.page.pop_dialog()),
                     ft.FilledButton("创建", on_click=create)])
        self.page.show_dialog(dlg)

    def _new_chapter(self, e):
        try: vols = volume_manager.get_volumes(self.pid)
        except: vols = []
        if not vols:
            self._snack("请先创建卷")
            return
        tf = ft.TextField(label="章节名称", border_radius=8, autofocus=True)
        dd = ft.Dropdown(label="所属卷",
            options=[ft.dropdown.Option(str(v["id"]), v.get("title", f"第{v['id']}卷")) for v in vols],
            value=str(vols[0]["id"]))
        def create(ev):
            t = tf.value.strip() or "新章节"
            vid = int(dd.value)
            chapter_manager.create_chapter(vid, t)
            self.page.pop_dialog()
            self.navigate("project_detail", {"pid": self.pid, "name": self.name})
        dlg = ft.AlertDialog(title=ft.Text("新建章节"),
            content=ft.Column([tf, dd], spacing=12, tight=True, height=180),
            actions=[ft.TextButton("取消", on_click=lambda ev: self.page.pop_dialog()),
                     ft.FilledButton("创建", on_click=create)])
        self.page.show_dialog(dlg)

    def _delete_chapter(self, cid):
        def do_del(ev):
            chapter_manager.delete_chapter(cid)
            self.page.pop_dialog()
            self.navigate("project_detail", {"pid": self.pid, "name": self.name})
        dlg = ft.AlertDialog(title=ft.Text("确认删除此章节？"),
            actions=[ft.TextButton("取消", on_click=lambda ev: self.page.pop_dialog()),
                     ft.FilledButton("删除", style=ft.ButtonStyle(bgcolor=C.ERROR), on_click=do_del)])
        self.page.show_dialog(dlg)

    def _snack(self, msg):
        self.page.snack_bar = ft.SnackBar(ft.Text(msg))
        self.page.snack_bar.open = True
        self.page.update()
