"""AI生成 - 新建小说 / 大纲生成 / 续写章节"""
import sys, os, threading, concurrent.futures, time
base = os.path.dirname(os.path.abspath(__file__))
if os.path.exists(os.path.join(base, "core")): sys.path.insert(0, base)
else: sys.path.insert(0, os.path.join(base, ".."))

import flet as ft
from core.writing_core import project_manager, volume_manager, chapter_manager
from core.ai_prompts import make_chapter_prompt
from models.ai_provider import ai_manager
from utils.text_processor import text_processor
from utils.logger import logger

I = ft.icons.Icons
C = ft.Colors

WRITING_STYLES = [
    ("（默认）", ""),
    ("自动文笔", "请根据故事大纲和主题内容，自动选择最适合的文笔风格进行创作。"),
    ("简洁干练型", "采用简洁干练型文笔风格。短句为主，叙事直接，节奏明快。"),
    ("华丽繁复型", "采用华丽繁复型文笔风格。辞藻丰赡，修辞密集，意象层叠，善用比喻通感。"),
    ("细腻写实型", "采用细腻写实型文笔风格。细节描写精准，画面感强，真实沉浸。"),
    ("幽默诙谐型", "采用幽默诙谐型文笔风格。轻松活泼，俏皮有趣，带吐槽调侃。"),
    ("冷峻沉郁型", "采用冷峻沉郁型文笔风格。冷静克制，语言简洁有力量，氛围压抑。"),
    ("诗意唯美型", "采用诗意唯美型文笔风格。语言富有韵律，意象优美，意境深远。"),
    ("古风典雅型", "采用古风典雅型文笔风格。文言词汇，典雅有韵味，古风十足。"),
    ("通俗口语型", "采用通俗口语型文笔风格。口语化表达，自然流畅，接地气。"),
    ("悬疑紧张型", "采用悬疑紧张型文笔风格。短句压迫感，悬念层层递进，氛围紧张。"),
]

OPENING_STRATEGIES = [
    ("冲突开篇", "用强烈的冲突或危机感开篇，让读者立刻感到紧张和好奇"),
    ("悬念开篇", "设置一个引人入胜的悬念，让读者迫切想知道答案"),
    ("画面开篇", "用震撼的视觉画面或独特的场景描写吸引读者"),
    ("对话开篇", "用精彩有深度的对话开篇，快速展现人物性格"),
    ("倒叙开篇", "从故事高潮或关键情节倒叙，制造强烈的反差感"),
]

class AIGeneratePage:
    def __init__(self, page: ft.Page, navigate, data=None):
        self.page = page
        self.navigate = navigate
        self.continuation = data.get("continuation", False) if data else False
        self.pid = data.get("pid", 0) if data else 0
        self.name = data.get("name", "") if data else ""
        self.mode = data.get("mode", "detail") if data else "detail"
        self.running = False
        self._log_counter = 0

    def build(self) -> ft.Control:
        if self.continuation:
            return self._build_continuation()
        if self.mode == "outline":
            return self._build_outline()
        return self._build_detail()

    # ===== 详细设定（新建小说） =====
    def _build_detail(self):
        self.name_f = ft.TextField(label="小说名称", border_radius=8, value="")
        self.genre_f = ft.Dropdown(label="小说类型", options=[
            ft.dropdown.Option("玄幻"), ft.dropdown.Option("奇幻"), ft.dropdown.Option("武侠"),
            ft.dropdown.Option("仙侠"), ft.dropdown.Option("都市"), ft.dropdown.Option("言情"),
            ft.dropdown.Option("历史"), ft.dropdown.Option("科幻"), ft.dropdown.Option("悬疑"),
            ft.dropdown.Option("恐怖"), ft.dropdown.Option("二次元"),
        ], value="玄幻")
        self.protag_f = ft.TextField(label="主角设定", hint_text="例：林夜，22岁大学生，性格坚毅", border_radius=8, max_lines=2)
        self.plot_f = ft.TextField(label="核心剧情", hint_text="主角获得能力后卷入惊天阴谋……", border_radius=8, max_lines=3)
        self.setting_f = ft.TextField(label="故事背景", hint_text="例：公元3000年星际殖民时代", border_radius=8, max_lines=2)
        self.male_f = ft.TextField(label="男主角名（选填）", border_radius=8)
        self.female_f = ft.TextField(label="女主角名（选填）", border_radius=8)

        self.style_f = ft.Dropdown(label="文笔风格", options=[
            ft.dropdown.Option(s[0]) for s in WRITING_STYLES
        ], value=WRITING_STYLES[0][0])
        self.gender_f = ft.Dropdown(label="阅读向", options=[
            ft.dropdown.Option("男频（男主视角）"),
            ft.dropdown.Option("女频（女主视角）"),
        ], value="男频（男主视角）")
        self.ch_f = ft.Dropdown(label="生成章数", options=[ft.dropdown.Option(str(n)) for n in [3,5,10,20,30]], value="10")
        self.wc_f = ft.Dropdown(label="每章字数", options=[ft.dropdown.Option(str(n)) for n in [1000,2000,3000,5000]], value="2000")

        self.log = ft.ListView(spacing=2, height=220, auto_scroll=True)
        self.prog = ft.ProgressBar(value=0, width=350)
        self.stat = ft.Text("准备就绪", size=14, weight=ft.FontWeight.BOLD, color=C.PRIMARY)
        self.winfo = ft.Text("", size=12, color=C.OUTLINE)

        return ft.Column([
            ft.Row([
                ft.IconButton(icon=I.ARROW_BACK, on_click=lambda e: self.navigate("home")),
                ft.Text("AI自动生成", size=20, weight=ft.FontWeight.BOLD),
                ft.OutlinedButton("大纲模式", icon=I.ARTICLE, on_click=self._switch_to_outline,
                                  style=ft.ButtonStyle(padding=ft.padding.symmetric(horizontal=6, vertical=2))),
            ]),
            self.name_f, self.genre_f, self.male_f, self.female_f,
            self.protag_f, self.plot_f, self.setting_f,
            self.style_f, self.gender_f,
            self.ch_f, self.wc_f,
            ft.FilledButton("开始生成", icon=I.PLAY_ARROW, on_click=self._do_generate,
                            style=ft.ButtonStyle(padding=ft.padding.all(14))),
            ft.Divider(),
            self.stat, ft.Row([self.prog, self.winfo]),
            ft.Container(content=self.log, height=220, border_radius=12,
                         bgcolor=C.SURFACE_CONTAINER_HIGHEST, padding=8),
        ])

    # ===== 大纲生成（方式二） =====
    def _build_outline(self):
        self.name_f = ft.TextField(label="小说名称", border_radius=8)
        self.outline_f = ft.TextField(
            label="总大纲", border_radius=8, multiline=True, min_lines=8, max_lines=20,
            hint_text="填写完整总大纲：\n【世界观】公元3000年…\n【主要人物】林夜：男，22岁…\n【剧情脉络】\n第一卷：觉醒篇（第1-5章）\n  第一章：意外觉醒\n  第二章：初次测试…",
        )
        self.style_f = ft.Dropdown(label="文笔风格", options=[
            ft.dropdown.Option(s[0]) for s in WRITING_STYLES
        ], value=WRITING_STYLES[0][0])
        self.gender_f = ft.Dropdown(label="阅读向", options=[
            ft.dropdown.Option("男频（男主视角）"),
            ft.dropdown.Option("女频（女主视角）"),
        ], value="男频（男主视角）")
        self.wc_f = ft.Dropdown(label="每章字数", options=[ft.dropdown.Option(str(n)) for n in [1000,2000,3000,5000]], value="2000")
        self.log = ft.ListView(spacing=2, height=220, auto_scroll=True)
        self.prog = ft.ProgressBar(value=0, width=350)
        self.stat = ft.Text("准备就绪", size=14, weight=ft.FontWeight.BOLD, color=C.PRIMARY)
        self.winfo = ft.Text("", size=12, color=C.OUTLINE)

        return ft.Column([
            ft.Row([
                ft.IconButton(icon=I.ARROW_BACK, on_click=lambda e: self.navigate("home")),
                ft.Text("AI大纲生成", size=20, weight=ft.FontWeight.BOLD),
                ft.OutlinedButton("详细模式", icon=I.LIST, on_click=self._switch_to_detail,
                                  style=ft.ButtonStyle(padding=ft.padding.symmetric(horizontal=6, vertical=2))),
            ]),
            self.name_f, self.outline_f,
            self.style_f, self.gender_f, self.wc_f,
            ft.FilledButton("开始生成", icon=I.PLAY_ARROW, on_click=self._do_generate_outline,
                            style=ft.ButtonStyle(padding=ft.padding.all(14))),
            ft.Divider(),
            self.stat, ft.Row([self.prog, self.winfo]),
            ft.Container(content=self.log, height=220, border_radius=12,
                         bgcolor=C.SURFACE_CONTAINER_HIGHEST, padding=8),
        ])

    # ===== 续写（从项目详情进入） =====
    def _build_continuation(self):
        gb = 0
        try:
            gb = len(chapter_manager.get_all_chapters_for_project(self.pid))
        except Exception:
            gb = 0
        mx = max(2, gb + 3)
        self.from_f = ft.Dropdown(label="起始章", options=[ft.dropdown.Option(str(i)) for i in range(1, mx)],
                                  value=str(gb + 1) if gb else "1")
        self.to_f = ft.Dropdown(label="目标章", options=[ft.dropdown.Option(str(i)) for i in range(1, mx)],
                                value=str(gb + 5) if gb else "5")
        self.wc_f = ft.Dropdown(label="每章字数", options=[ft.dropdown.Option(str(n)) for n in [1000,2000,3000,5000]], value="2000")
        self.log = ft.ListView(spacing=2, height=220, auto_scroll=True)
        self.prog = ft.ProgressBar(value=0, width=350)
        self.stat = ft.Text("准备就绪", size=14, weight=ft.FontWeight.BOLD, color=C.PRIMARY)
        self.winfo = ft.Text("", size=12, color=C.OUTLINE)

        return ft.Column([
            ft.Row([
                ft.IconButton(icon=I.ARROW_BACK, on_click=lambda e: self.navigate("project_detail", {"pid": self.pid, "name": self.name})),
                ft.Text(f"续写: {self.name}", size=20, weight=ft.FontWeight.BOLD),
            ]),
            ft.Text(f"已有 {gb} 章，将从第 {gb + 1} 章开始续写", size=13, color=C.OUTLINE),
            self.wc_f, ft.Row([self.from_f, self.to_f], spacing=12),
            ft.FilledButton("续写生成", icon=I.AUTO_STORIES, on_click=self._do_continuation,
                            style=ft.ButtonStyle(padding=ft.padding.all(14))),
            ft.Divider(),
            self.stat, ft.Row([self.prog, self.winfo]),
            ft.Container(content=self.log, height=220, border_radius=12,
                         bgcolor=C.SURFACE_CONTAINER_HIGHEST, padding=8),
        ])

    # ===== 三个启动入口 =====
    def _do_generate(self, e):
        if self.running: return
        nm = self.name_f.value.strip()
        if not nm: self._snack("请填写小说名称"); return
        if not self.protag_f.value.strip() or not self.plot_f.value.strip():
            self._snack("请填写主角设定和核心剧情"); return
        if not self._common_start(): return
        ctx = {
            "master_outline": "", "novel_type": self.genre_f.value,
            "protagonist": self.protag_f.value.strip(),
            "setting": self.setting_f.value.strip(),
            "plot": self.plot_f.value.strip(), "outline": "",
            "male_name": self.male_f.value.strip(),
            "female_name": self.female_f.value.strip(),
            "writing_style": self._resolve_style(),
            "gender": self.gender_f.value,
            "novel_name": nm, "existing_project_context": "",
        }
        total = int(self.ch_f.value)
        wc_per = int(self.wc_f.value)
        threading.Thread(target=self._worker, args=(nm, self.genre_f.value, ctx, total, wc_per, False, "detail"),
                         daemon=True).start()

    def _do_generate_outline(self, e):
        if self.running: return
        nm = self.name_f.value.strip()
        outline = self.outline_f.value.strip()
        if not nm: self._snack("请填写小说名称"); return
        if not outline or len(outline) < 20:
            self._snack("大纲太短，请至少写20字以上的大纲"); return
        if not self._common_start(): return
        ctx = {
            "master_outline": outline, "novel_type": "",
            "protagonist": "", "setting": "", "plot": "", "outline": "",
            "male_name": "", "female_name": "",
            "writing_style": self._resolve_style(),
            "gender": self.gender_f.value,
            "novel_name": nm, "existing_project_context": "",
        }
        wc_per = int(self.wc_f.value)
        total = outline.count("第") or 10
        threading.Thread(target=self._worker, args=(nm, "", ctx, total, wc_per, False, "outline"), daemon=True).start()

    def _do_continuation(self, e):
        if self.running: return
        fi = int(self.from_f.value)
        ti = int(self.to_f.value)
        if fi > ti: self._snack("起始章不能大于目标章"); return
        if not self._common_start(): return
        parts = []
        try:
            for ch in chapter_manager.get_all_chapters_for_project(self.pid):
                ct = ch.get("content", "")
                if ct:
                    parts.append(f"【{ch['title']}】{ct[:80]}……【结尾】{ct[-150:]}")
        except Exception:
            pass
        ctx = {
            "master_outline": "", "novel_type": "", "protagonist": "", "setting": "",
            "plot": "", "outline": "", "male_name": "", "female_name": "",
            "writing_style": "", "gender": "", "novel_name": self.name,
            "existing_project_context": "\n\n".join(parts) if parts else "",
        }
        total = ti - fi + 1
        wc_per = int(self.wc_f.value)
        threading.Thread(target=self._worker, args=(self.name, "", ctx, total, wc_per, True, "continuation"),
                         daemon=True).start()

    def _common_start(self):
        self.running = True
        self._log_counter = 0
        self.log.controls.clear()
        self.winfo.value = ""
        self.stat.value = "🚀 启动中..."
        self.prog.value = 0

        providers = ai_manager.get_available_providers()
        if not providers:
            self._log("❌ 没有可用的AI模型！请先在【设置】中填入API密钥并启用")
            self.stat.value = "❌ 无可用AI模型"
            self.running = False
            self.page.update()
            return False
        self._log(f"✅ 可用模型: {', '.join(providers)}")
        self.page.update()
        return True

    def _switch_to_outline(self, e):
        self.mode = "outline"
        self.navigate("ai_generate", {"mode": "outline"})

    def _switch_to_detail(self, e):
        self.mode = "detail"
        self.navigate("ai_generate", {"mode": "detail"})

    def _resolve_style(self):
        raw = self.style_f.value
        if raw == "（默认）":
            return ""
        for name, desc in WRITING_STYLES:
            if name == raw:
                if name == "自动文笔":
                    return "请根据故事大纲和主题内容，自动选择最适合的文笔风格进行创作（如热血类用简洁有力、言情类用细腻优美、悬疑类用冷峻紧张等）。"
                return desc
        return ""

    # ===== 工作线程 =====
    def _worker(self, name, ntype, ctx, total, wc_per, is_cont, ctx_type):
        def ui_log(msg):
            logger.info(f"[AI生成] {msg}")
            try:
                self.page.run_thread_safe(lambda m=msg: self._log(m))
            except Exception:
                pass

        def ui_prog(val, msg):
            try:
                self.page.run_thread_safe(lambda v=val, s=msg: (
                    setattr(self.prog, 'value', v),
                    setattr(self.stat, 'value', s),
                    self.page.update()
                ))
            except Exception:
                pass

        def ui_wc(val):
            try:
                self.page.run_thread_safe(lambda v=val: (
                    setattr(self.winfo, 'value', f"累计 {v:,}字"),
                    self.page.update()
                ))
            except Exception:
                pass

        ui_log(f"📚 开始生成《{name}》，共 {total} 章，每章 {wc_per} 字")
        tot_wc = 0

        try:
            if not is_cont:
                pid = project_manager.create_project(name=name, author="AI创作",
                    genre=ntype or "通用", description="AI自动生成",
                    word_goal=total * wc_per)
                vols = volume_manager.get_volumes(pid)
                vid = vols[0]["id"] if vols else volume_manager.create_volume(pid, "第一卷")
            else:
                pid = self.pid
                vols = volume_manager.get_volumes(pid)
                vid = vols[-1]["id"] if vols else volume_manager.create_volume(pid, "第一卷")

            gb = len(chapter_manager.get_all_chapters_for_project(pid)) if is_cont else 0
            prev = []
            for i in range(1, total + 1):
                if not self.running:
                    ui_log("⏹ 用户停止"); break

                n = gb + i
                ct = f"第{n}章"
                ui_log(f"📝 {ct} 生成中...")
                ui_prog(i / total, f"正在写 {ct} ({i}/{total})")

                cid = chapter_manager.create_chapter(vid, ct)
                if not cid:
                    ui_log(f"❌ 创建章节失败: {ct}"); continue

                prompt = make_chapter_prompt(
                    context_type=ctx_type, context_data=ctx,
                    chapter_number=n, chapter_title=ct,
                    word_count=wc_per, previous_summaries=prev,
                )
                logger.info(f"[AI生成] prompt长度={len(prompt)}")

                fut = concurrent.futures.Future()
                ai_manager.generate_async(
                    prompt=prompt, max_tokens=int(wc_per * 1.5) + 200, temperature=0.8,
                    on_complete=lambda r, f=fut: f.set_result(r) if not f.done() else None,
                    on_error=lambda e, f=fut: f.set_exception(Exception(e)) if not f.done() else None,
                )
                try:
                    result = fut.result(timeout=600)
                except concurrent.futures.TimeoutError:
                    ui_log(f"❌ {ct} AI响应超时"); continue
                except Exception as exc:
                    ui_log(f"❌ {ct} AI调用异常: {exc}"); continue

                if not result or result.startswith("错误:") or result.startswith("生成失败"):
                    ui_log(f"❌ {ct} 生成失败: {str(result)[:80] if result else '空结果'}")
                    continue

                chapter_manager.save_chapter(cid, result)
                wc = text_processor.count_words(result)
                tot_wc += wc
                prev.append(f"【{ct}】{result[:100]}…【结尾】{result[-200:]}[{wc}字]")
                ui_log(f"✅ {ct} 完成 - {wc:,}字")
                ui_wc(tot_wc)

            ui_log(f"🎉 全部完成! 共 {total} 章, {tot_wc:,} 字")
            ui_prog(1.0, "✅ 全部完成")
        except Exception as ex:
            import traceback
            tb = traceback.format_exc()
            logger.error(f"[AI生成] 异常: {ex}\n{tb}")
            ui_log(f"❌ 系统异常: {ex}")
        finally:
            self.running = False

    def _log(self, msg):
        self._log_counter += 1
        self.log.controls.append(ft.Text(msg, size=12))
        self.page.update()

    def _snack(self, msg):
        self.page.snack_bar = ft.SnackBar(ft.Text(msg))
        self.page.snack_bar.open = True
        self.page.update()
