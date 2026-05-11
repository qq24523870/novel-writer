"""编辑器 - 文本编辑 + AI辅助"""
import sys, os, logging
base = os.path.dirname(os.path.abspath(__file__))
if os.path.exists(os.path.join(base, "core")): sys.path.insert(0, base)
else: sys.path.insert(0, os.path.join(base, ".."))

import flet as ft
from core.writing_core import chapter_manager
from models.ai_provider import ai_manager
from core.ai_prompts import get_prompt
from utils.text_processor import text_processor

I, C = ft.icons.Icons, ft.Colors

class EditorPage:
    def __init__(self, page: ft.Page, navigate, data=None):
        self.page, self.navigate = page, navigate
        self.pid = data.get("pid", 0)
        self.cid = data.get("cid", 0)
        self.title = data.get("title", "")
        self.ai_busy = False
        self.editor = ft.TextField(multiline=True, min_lines=30, max_lines=999,
            border_radius=8, border_color=C.OUTLINE, text_size=15,
            hint_text="在此输入或生成小说内容...", on_change=self._on_change)
        self.wc_text = ft.Text("0字", size=12, color=C.OUTLINE)
        self.ai_stat = ft.Text("", size=12, color=C.PRIMARY)

    def build(self) -> ft.Control:
        try:
            ch = chapter_manager.get_chapter(self.cid)
            if ch:
                ct = ch.get("content", "")
                self.editor.value = ct
                self.wc_text.value = f"{text_processor.count_words(ct or ''):,}字"
        except: pass
        return ft.Column([
            ft.Row([
                ft.IconButton(icon=I.ARROW_BACK, on_click=lambda e: self.navigate("project_detail", {"pid": self.pid, "name": ""})),
                ft.Text(self.title, size=18, weight=ft.FontWeight.BOLD),
                ft.IconButton(icon=I.SAVE, icon_color=C.PRIMARY, tooltip="保存", on_click=lambda e: self._save()),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Row([
                ft.FilledButton("续写", icon=I.AUTO_STORIES, on_click=self._ai_continue,
                    style=ft.ButtonStyle(padding=ft.padding.symmetric(horizontal=8, vertical=4))),
                ft.FilledButton("润色", icon=I.BRUSH, on_click=self._ai_polish,
                    style=ft.ButtonStyle(padding=ft.padding.symmetric(horizontal=8, vertical=4))),
                ft.FilledButton("扩写", icon=I.ADD_CIRCLE, on_click=self._ai_expand,
                    style=ft.ButtonStyle(padding=ft.padding.symmetric(horizontal=8, vertical=4))),
            ], spacing=4, wrap=True),
            ft.Row([self.wc_text, self.ai_stat]),
            ft.Container(content=self.editor, height=450, padding=ft.padding.only(top=4)),
        ])

    def _on_change(self, e):
        ct = self.editor.value or ""
        self.wc_text.value = f"{text_processor.count_words(ct):,}字"
        self.page.update()

    def _save(self, e=None):
        try:
            chapter_manager.save_chapter(self.cid, self.editor.value or "", self.title)
            self._snack("已保存")
        except Exception as ex:
            self._snack(f"保存失败: {ex}")

    def _snack(self, msg):
        self.page.snack_bar = ft.SnackBar(ft.Text(msg))
        self.page.snack_bar.open = True
        self.page.update()

    def _ctx(self):
        t = self.editor.value or ""
        if len(t) > 3000: return t[:1500] + "\n...(中间省略)...\n" + t[-1500:]
        return t

    def _ai_continue(self, e):
        if self.ai_busy: return
        self.ai_busy = True; self.ai_stat.value = "AI续写中..."; self.page.update()
        self._call_ai(get_prompt("continue", content=self._ctx() or "", length=500, novel_context=""))

    def _ai_polish(self, e):
        if self.ai_busy: return
        if not (self.editor.value or "").strip(): self._snack("请先撰写一些内容"); return
        self.ai_busy = True; self.ai_stat.value = "AI润色中..."; self.page.update()
        self._call_ai(get_prompt("polish", content=self._ctx(), intensity="适当"), replace=True)

    def _ai_expand(self, e):
        if self.ai_busy: return
        if not (self.editor.value or "").strip(): self._snack("请先撰写一些内容"); return
        self.ai_busy = True; self.ai_stat.value = "AI扩写中..."; self.page.update()
        self._call_ai(get_prompt("expand", content=self._ctx(), length=300), replace=True)

    def _call_ai(self, prompt, replace=False):
        def on_done(result):
            self.ai_busy = False
            if result and not result.startswith("错误:") and not result.startswith("生成失败"):
                if replace: self.editor.value = result
                else: self.editor.value = (self.editor.value or "") + "\n\n" + result
                self.ai_stat.value = "完成"; self._save()
            else: self.ai_stat.value = f"失败: {result or '空结果'}"
            self._on_change(None); self.page.update()
        def on_error(err):
            self.ai_busy = False; self.ai_stat.value = f"错误: {err}"; self.page.update()
        ai_manager.generate_async(prompt=prompt, max_tokens=800, temperature=0.8, on_complete=on_done, on_error=on_error)
