"""设置 - API密钥 + 关于"""
import sys, os
base = os.path.dirname(os.path.abspath(__file__))
if os.path.exists(os.path.join(base, "core")): sys.path.insert(0, base)
else: sys.path.insert(0, os.path.join(base, ".."))

import flet as ft
from utils.config_manager import config_manager
from models.ai_provider import ai_manager

I, C = ft.icons.Icons, ft.Colors

class SettingsPage:
    def __init__(self, page: ft.Page, navigate, data=None):
        self.page, self.navigate = page, navigate
        self.tab = 0

    def build(self) -> ft.Control:
        self.container = ft.Container(height=500)
        self._render_tab(0, update=False)
        return ft.Column([
            ft.Row([
                ft.IconButton(icon=I.ARROW_BACK, on_click=lambda e: self.navigate("home")),
                ft.Text("设置", size=22, weight=ft.FontWeight.BOLD),
            ]),
            ft.Row([
                ft.FilledButton("API密钥", icon=I.KEY, on_click=lambda e: self._render_tab(0)),
                ft.OutlinedButton("关于", icon=I.INFO_OUTLINE, on_click=lambda e: self._render_tab(1)),
            ], spacing=8),
            ft.Divider(),
            self.container,
        ])

    def _render_tab(self, idx, update=True):
        self.tab = idx
        items = []
        if idx == 0:
            items.append(ft.Text("API密钥配置", size=18, weight=ft.FontWeight.BOLD))
            items.append(ft.Text("填写后保存在本地，不会上传到云端", size=12, color=C.OUTLINE))
            items.append(ft.Divider())
            for key, label in [
                ("siliconflow", "硅基流动"), ("deepseek", "DeepSeek"),
                ("openai", "OpenAI"), ("wenxin", "百度文心"),
                ("tongyi", "通义千问"), ("doubao", "豆包"),
            ]:
                try:
                    en = config_manager.get(f"ai.cloud_models.{key}.enabled", False)
                    ak = config_manager.get(f"ai.cloud_models.{key}.api_key", "")
                    md = config_manager.get(f"ai.cloud_models.{key}.model", "")
                except:
                    en, ak, md = False, "", ""
                kf = ft.TextField(label=f"{label} API Key", value=ak, password=True,
                                  can_reveal_password=True, border_radius=8)
                sw = ft.Switch(value=en, label=f"启用{label}")
                btns = [sw, kf]
                mf = None
                if md:
                    mf = ft.TextField(label=f"{label} 模型名", value=md, border_radius=8)
                    btns.append(mf)
                def mk_save(kk=key, kf_=kf, mf_=mf, sw_=sw):
                    return lambda ev: self._save(kk, kf_.value, mf_.value if mf_ else "", sw_.value)
                btns.append(ft.FilledButton("保存", on_click=mk_save()))
                items.append(ft.Container(content=ft.Column(btns, spacing=8),
                    border_radius=12, bgcolor=C.SURFACE_CONTAINER_HIGHEST, padding=12))
        else:
            items = [
                ft.Container(height=10),
                ft.Icon(I.BOOK, size=64, color=C.PRIMARY),
                ft.Text("AI小说创作助手", size=24, weight=ft.FontWeight.BOLD),
                ft.Text("v1.0.0", size=14, color=C.OUTLINE),
                ft.Divider(),
                ft.Text("开发者: 青易", size=16),
                ft.Text("QQ: 24523870", size=16, color=C.PRIMARY),
                ft.Text("如有问题欢迎联系", size=13, color=C.OUTLINE),
                ft.Divider(),
                ft.Text("基于 Flet + Python 开发", size=12, color=C.OUTLINE),
            ]
        self.container.content = ft.Column(items)
        if update:
            self.page.update()

    def _save(self, key, key_val, model_val, enabled_val):
        config_manager.set(f"ai.cloud_models.{key}.api_key", key_val)
        if model_val:
            config_manager.set(f"ai.cloud_models.{key}.model", model_val)
        config_manager.set(f"ai.cloud_models.{key}.enabled", enabled_val)
        if enabled_val and key_val:
            config_manager.set("ai.default_model", key)
        ai_manager.reinitialize()
        providers = ai_manager.get_available_providers()
        msg = f"已保存，可用模型: {', '.join(providers) if providers else '无'}"
        self.page.snack_bar = ft.SnackBar(ft.Text(msg))
        self.page.snack_bar.open = True
        self.page.update()
