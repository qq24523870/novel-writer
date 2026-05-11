import re
from typing import Callable, Optional
from PySide6.QtCore import Qt, Signal, QTimer, QRect, QSize
from PySide6.QtGui import (
    QFont, QColor, QKeySequence, QShortcut, QAction,
    QTextCursor, QSyntaxHighlighter, QTextCharFormat, QPainter, QTextFormat
)
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPlainTextEdit,
    QLabel, QApplication, QTextEdit, QMenu, QInputDialog, QMessageBox,
    QProgressBar
)
from utils.config_manager import config_manager
from utils.text_processor import text_processor
from ui.theme_manager import theme_manager
from core.novel_memory import novel_memory_manager
from utils.logger import logger


class LineNumberArea(QWidget):
    """行号区域"""

    def __init__(self, editor):
        super().__init__(editor)
        self._editor = editor

    def sizeHint(self):
        return QSize(self._editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self._editor.line_number_area_paint_event(event)


class NovelEditor(QPlainTextEdit):
    """小说文本编辑器，基于QPlainTextEdit实现专业写作功能"""

    textChanged_signal = Signal()
    cursorPositionChanged_signal = Signal(int, int)
    wordCountChanged = Signal(int, int, int)
    aiStatusChanged = Signal(str)
    aiStreamingToken = Signal(str)
    aiTokenReceived = Signal(str)
    aiGenerationFinished = Signal(str)
    aiGenerationError = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._chapter_id: Optional[int] = None
        self._is_modified = False
        self._auto_save_timer = QTimer(self)
        self._word_count_timer = QTimer(self)
        self._typing_timer = QTimer(self)
        self._typing_count = 0
        self._typing_start = 0
        self._saved_content = ""
        self._find_widget = None
        self._ai_generating = False
        self._ai_stream_buffer = ""
        self._ai_is_continue = False
        self._ai_timeout_timer = QTimer(self)
        self._ai_timeout_timer.setSingleShot(True)
        self._ai_timeout_timer.setInterval(120000)
        self._ai_timeout_timer.timeout.connect(self._on_ai_timeout)
        self._current_font_size = config_manager.get("editor.font_size", 14)

        self.setup_editor()
        self.setup_shortcuts()
        self.setup_timers()
        self.connect_signals()
        self.connect_ai_signals()

    def setup_editor(self):
        """配置编辑器基本属性"""
        font_family = config_manager.get("editor.font_family", "Microsoft YaHei")
        self._current_font_size = config_manager.get("editor.font_size", 14)
        font = QFont(font_family, self._current_font_size)
        font.setStyleStrategy(QFont.PreferAntialias)
        self.setFont(font)
        self.setTabStopDistance(
            self.fontMetrics().horizontalAdvance(" ") * config_manager.get("editor.tab_width", 4)
        )

        self.setLineWrapMode(QPlainTextEdit.WidgetWidth if config_manager.get("editor.wrap_mode", True)
                            else QPlainTextEdit.NoWrap)
        self.setMaximumBlockCount(0)

        self.line_number_area = LineNumberArea(self)
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

    def apply_font_size(self, size: int):
        """应用编辑器字体大小"""
        self._current_font_size = max(8, min(48, size))
        font = QFont(config_manager.get("editor.font_family", "Microsoft YaHei"), self._current_font_size)
        font.setStyleStrategy(QFont.PreferAntialias)
        self.setFont(font)
        self.setTabStopDistance(
            self.fontMetrics().horizontalAdvance(" ") * config_manager.get("editor.tab_width", 4)
        )
        self.viewport().update()

    def wheelEvent(self, event):
        """Ctrl+滚轮缩放编辑器字号"""
        if event.modifiers() & Qt.ControlModifier:
            delta = event.angleDelta().y()
            if delta > 0:
                self.apply_font_size(self._current_font_size + 1)
            elif delta < 0:
                self.apply_font_size(self._current_font_size - 1)
            config_manager.set("editor.font_size", self._current_font_size)
            return
        super().wheelEvent(event)

    def setup_shortcuts(self):
        """设置快捷键"""
        shortcuts_config = config_manager.get("shortcuts", {})

        self._shortcuts = {}

    def setup_timers(self):
        """设置定时器"""
        auto_save_interval = config_manager.get("editor.auto_save_interval", 30) * 1000
        self._auto_save_timer.setInterval(auto_save_interval)
        self._auto_save_timer.timeout.connect(self.auto_save)

        self._word_count_timer.setInterval(2000)
        self._word_count_timer.timeout.connect(self.update_word_count)
        self._word_count_timer.start()

        self._typing_timer.setInterval(1000)
        self._typing_timer.timeout.connect(self.update_typing_speed)

    def connect_signals(self):
        """连接信号"""
        self.textChanged.connect(self.on_text_changed)
        self.cursorPositionChanged.connect(self.on_cursor_position_changed)
        self.textChanged_signal.connect(self.update_word_count)

    def line_number_area_width(self) -> int:
        """计算行号区域宽度"""
        digits = 1
        max_num = max(1, self.blockCount())
        while max_num >= 10:
            max_num //= 10
            digits += 1
        return 10 + self.fontMetrics().horizontalAdvance("9") * digits

    def line_number_area_paint_event(self, event):
        """绘制行号区域"""
        painter = QPainter(self)
        colors = theme_manager.get_theme_colors()

        painter.fillRect(event.rect(), QColor(colors.get("bg_secondary", "#F5F5F5")))

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = round(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + round(self.blockBoundingRect(block).height())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(QColor(colors.get("editor_line_number", "#999999")))
                painter.drawText(
                    0, top, self.line_number_area_width() - 4,
                    self.fontMetrics().height(),
                    Qt.AlignRight, number
                )

            block = block.next()
            top = bottom
            bottom = top + round(self.blockBoundingRect(block).height())
            block_number += 1

    def resizeEvent(self, event):
        """窗口大小改变事件"""
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(
            QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height())
        )

    def on_text_changed(self):
        """文本变更事件"""
        self._is_modified = True
        self._typing_count += 1
        if self._typing_start == 0:
            self._typing_start = 1
        self._typing_timer.start()
        self.textChanged_signal.emit()

    def on_cursor_position_changed(self):
        """光标位置变更事件"""
        cursor = self.textCursor()
        line = cursor.blockNumber() + 1
        col = cursor.columnNumber() + 1
        self.cursorPositionChanged_signal.emit(line, col)

    def update_word_count(self):
        """更新字数统计"""
        text = self.toPlainText()
        total_words = text_processor.count_words(text)
        chinese_chars = text_processor.count_chinese_chars(text)
        paragraphs = text_processor.count_paragraphs(text)
        self.wordCountChanged.emit(total_words, chinese_chars, paragraphs)

    def update_typing_speed(self):
        """更新打字速度"""
        self._typing_timer.stop()
        self._typing_count = 0
        self._typing_start = 0

    def auto_save(self):
        """自动保存"""
        if self._is_modified and self._chapter_id:
            from core.writing_core import chapter_manager
            content = self.toPlainText()
            chapter_manager.save_chapter(self._chapter_id, content)
            self._is_modified = False
            self._saved_content = content

    def load_chapter(self, chapter_id: int, content: str = "", title: str = ""):
        """加载章节内容

        Args:
            chapter_id: 章节ID
            content: 章节内容
            title: 章节标题
        """
        self._chapter_id = chapter_id
        self.setPlainText(content)
        self._saved_content = content
        self._is_modified = False
        self._auto_save_timer.start()

    def save_current(self) -> bool:
        """保存当前内容

        Returns:
            是否保存成功
        """
        if self._chapter_id:
            from core.writing_core import chapter_manager
            content = self.toPlainText()
            chapter_manager.save_chapter(self._chapter_id, content)
            self._is_modified = False
            self._saved_content = content
            return True
        return False

    def is_modified(self) -> bool:
        """检查内容是否已修改"""
        return self._is_modified

    def get_chapter_id(self) -> Optional[int]:
        """获取当前章节ID"""
        return self._chapter_id

    def insert_text(self, text: str):
        """在光标位置插入文本

        Args:
            text: 要插入的文本
        """
        cursor = self.textCursor()
        cursor.insertText(text)
        self.setTextCursor(cursor)

    def replace_selection(self, text: str):
        """替换选中的文本

        Args:
            text: 替换文本
        """
        cursor = self.textCursor()
        if cursor.hasSelection():
            cursor.insertText(text)
            self.setTextCursor(cursor)

    def get_selected_text(self) -> str:
        """获取选中的文本"""
        cursor = self.textCursor()
        return cursor.selectedText() if cursor.hasSelection() else ""

    def show_context_menu(self, pos):
        """显示右键菜单"""
        menu = QMenu(self)

        menu.addAction("剪切", self.cut, QKeySequence.Cut)
        menu.addAction("复制", self.copy, QKeySequence.Copy)
        menu.addAction("粘贴", self.paste, QKeySequence.Paste)
        menu.addSeparator()

        ai_menu = menu.addMenu("AI 辅助")

        self._pending_ai_action = None
        def set_pending(action_type):
            self._pending_ai_action = action_type
            self._pending_ai_menu = menu
            menu.close()

        ai_menu.addAction("📝 一键续写(全文)", lambda: set_pending("continue"))
        ai_menu.addAction("✨ 智能润色", lambda: set_pending("polish"))
        ai_menu.addAction("🔍 内容扩写", lambda: set_pending("expand"))
        ai_menu.addAction("📋 内容缩写", lambda: set_pending("summarize"))
        ai_menu.addSeparator()
        ai_menu.addAction("🎨 风格改写", lambda: set_pending("style_rewrite"))
        ai_menu.addAction("✅ 错别字检查", lambda: set_pending("check_spelling"))

        menu.addSeparator()
        menu.addAction("全选", self.selectAll, QKeySequence.SelectAll)

        menu.exec(self.mapToGlobal(pos))

        if self._pending_ai_action:
            action = self._pending_ai_action
            self._pending_ai_action = None
            QTimer.singleShot(0, lambda: self._safe_request_ai(action))

    def _safe_request_ai(self, action_type: str):
        """菜单关闭后安全调用AI操作"""
        try:
            self.request_ai_action(action_type)
        except Exception as e:
            logger.error(f"_safe_request_ai 异常: {e}")
            import traceback
            logger.error(traceback.format_exc())
            QMessageBox.critical(self.window(), "错误", f"AI操作失败：{e}")

    def _build_novel_context(self) -> str:
        """构建完整的小说上下文供AI使用"""
        if not self._chapter_id:
            return ""
        try:
            from models.database import db_manager
            chapter = db_manager.fetch_one(
                "SELECT * FROM chapters WHERE id = ?", (self._chapter_id,)
            )
            if not chapter:
                return ""
            volume = db_manager.fetch_one(
                "SELECT project_id, title FROM volumes WHERE id = ?",
                (chapter["volume_id"],)
            )
            if not volume:
                return ""
            memory = novel_memory_manager.get_memory(volume["project_id"])

            context_parts = []
            ai_context = memory.get_ai_context(
                current_chapter_id=self._chapter_id,
                max_summary_chapters=5
            )
            if ai_context:
                context_parts.append("【前文概要、伏笔与情节连贯性参考】")
                context_parts.append(ai_context)

            all_chapters = db_manager.fetch_all(
                "SELECT id, title, sort_order FROM chapters WHERE volume_id = ? AND is_deleted = 0 ORDER BY sort_order",
                (chapter["volume_id"],)
            )
            current_sort = chapter.get("sort_order", 0)
            prev_chapters = [ch for ch in all_chapters if ch["sort_order"] < current_sort]
            if prev_chapters:
                context_parts.append(f"\n【当前卷《{volume['title']}】章节结构（前面已有{len(prev_chapters)}章）")
                context_parts.append("前面章节标题: " + ", ".join([ch["title"] for ch in prev_chapters[-5:]]))

            project_id = volume["project_id"]
            characters = db_manager.fetch_all(
                "SELECT name, personality, gender FROM characters WHERE project_id = ? AND is_deleted = 0",
                (project_id,)
            )
            if characters:
                context_parts.append(f"\n【本作品主要人物（共{len(characters)}人）】")
                for c in characters:
                    personality = c.get("personality", "")
                    if personality:
                        context_parts.append(f"  - {c['name']}({c.get('gender', '')}): {personality[:50]}")
                    else:
                        context_parts.append(f"  - {c['name']}({c.get('gender', '')})")

            world_settings = db_manager.fetch_all(
                "SELECT title, content FROM world_settings WHERE project_id = ? AND is_deleted = 0 LIMIT 5",
                (project_id,)
            )
            if world_settings:
                context_parts.append(f"\n【世界观设定参考】")
                for ws in world_settings:
                    context_parts.append(f"  - {ws['title']}: {ws.get('content', '')[:80]}")

            return "\n".join(context_parts)
        except Exception as e:
            logger.error(f"构建小说上下文失败: {e}")
            return ""

    def request_ai_action(self, action_type: str):
        logger.info(f"=== request_ai_action 被调用: action_type='{action_type}' ===")
        selected_text = self.get_selected_text()
        full_text = self.toPlainText()
        logger.info(f"selected_text长度={len(selected_text)}, full_text长度={len(full_text)}")

        if self._ai_generating:
            logger.info("重置_ai_generating（上一轮可能未完成）")
            self._ai_generating = False
            self.setReadOnly(False)

        if action_type == "continue":
            text_for_ai = full_text if full_text else selected_text
            logger.info(f"continue分支: text_for_ai长度={len(text_for_ai)}")
            if not text_for_ai:
                QMessageBox.information(self, "提示", "当前章节内容为空，请先写一些内容")
                return
            default_len = config_manager.get("writing.continue_word_count", 500)
            logger.info(f"准备弹出QInputDialog, default_len={default_len}")
            from PySide6.QtWidgets import QApplication
            QApplication.processEvents()
            dlg_parent = self.window() if self.window() else self
            length, ok = QInputDialog.getInt(
                dlg_parent, "续写设置", "续写字数（建议100-2000）：",
                default_len, 50, 5000, 50
            )
            logger.info(f"QInputDialog返回: ok={ok}, length={length}")
            if ok:
                novel_context = self._build_novel_context()
                from core.ai_prompts import get_prompt
                prompt = get_prompt("continue", content=text_for_ai, length=length, novel_context=novel_context)
                logger.info(f"提示词已生成, 长度={len(prompt)}")
                max_tokens = int(length * 1.8) + 100
                self._run_ai_stream_generation(prompt, f"🔮 AI正在续写 ({length}字)...", max_tokens=max_tokens)
                logger.info("_run_ai_stream_generation 已调用")
            else:
                logger.info("用户取消了续写对话框")

        elif action_type == "polish":
            if not selected_text:
                QMessageBox.information(self, "提示", "请先选中要润色的文本")
                return
            from core.ai_prompts import get_prompt
            intensities = {"轻度": "轻度", "中度": "中度", "重度": "重度"}
            intensity, ok = QInputDialog.getItem(self, "润色强度", "选择润色强度：",
                                                 list(intensities.keys()), 1, False)
            if ok and intensity:
                prompt = get_prompt("polish", content=selected_text, intensity=intensities[intensity])
                self._run_ai_stream_generation(prompt, f"✨ AI正在润色 ({intensity})...")

        elif action_type == "expand":
            if not selected_text:
                QMessageBox.information(self, "提示", "请先选中要扩写的文本")
                return
            from core.ai_prompts import get_prompt
            prompt = get_prompt("expand", content=selected_text, length=300)
            self._run_ai_stream_generation(prompt, "🔍 AI正在扩写...")

        elif action_type == "summarize":
            if not selected_text:
                QMessageBox.information(self, "提示", "请先选中要缩写的文本")
                return
            from core.ai_prompts import get_prompt
            prompt = get_prompt("summarize", content=selected_text)
            self._run_ai_stream_generation(prompt, "📋 AI正在缩写...")

        elif action_type == "style_rewrite":
            if not selected_text:
                QMessageBox.information(self, "提示", "请先选中要改写的文本")
                return
            styles = ["古风", "现代", "科幻", "悬疑", "言情", "奇幻", "武侠"]
            style, ok = QInputDialog.getItem(self, "选择风格", "选择目标风格：",
                                             styles, 0, False)
            if ok and style:
                from core.ai_prompts import get_prompt
                prompt = get_prompt("style_rewrite", content=selected_text, style=style)
                self._run_ai_stream_generation(prompt, f"🎨 AI正在改写为{style}风格...")

        elif action_type == "check_spelling":
            if not selected_text:
                QMessageBox.information(self, "提示", "请先选中要检查的文本")
                return
            from core.ai_prompts import get_prompt
            prompt = get_prompt("check_spelling", content=selected_text)
            self._run_ai_stream_generation(prompt, "✅ AI正在检查错别字...")

    def get_whole_content(self) -> str:
        """获取编辑器全文"""
        return self.toPlainText()

    def append_to_end(self, text: str):
        """在文档末尾追加文本"""
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(text)
        self.setTextCursor(cursor)

    def connect_ai_signals(self):
        """连接AI相关信号（跨线程安全）"""
        self.aiTokenReceived.connect(self._on_token_main_thread)
        self.aiGenerationFinished.connect(self._on_finished_main_thread)
        self.aiGenerationError.connect(self._on_error_main_thread)

    def _on_token_main_thread(self, token: str):
        """主线程处理AI生成的token（安全直接操作UI）"""
        if self._ai_is_continue:
            cursor = self.textCursor()
            cursor.movePosition(QTextCursor.End)
            cursor.insertText(token)
            self.setTextCursor(cursor)
        else:
            self.insertPlainText(token)

    def _on_finished_main_thread(self, result: str):
        """主线程处理AI生成完成"""
        self._ai_timeout_timer.stop()
        self._ai_generating = False
        self.setReadOnly(False)
        logger.info(f"AI生成完成, 结果长度={len(result) if result else 0}")
        if not result:
            self.aiStatusChanged.emit("❌ AI生成失败：结果为空")
            QMessageBox.warning(self, "提示", "AI生成结果为空，请检查模型配置")
        elif result.startswith("错误:") or result.startswith("生成失败"):
            self.aiStatusChanged.emit("❌ " + result[:40])
            QMessageBox.critical(self, "AI错误", result)
        else:
            self.aiStatusChanged.emit("✅ AI生成完成")
            self._is_modified = True

    def _on_error_main_thread(self, error: str):
        """主线程处理AI生成错误"""
        self._ai_timeout_timer.stop()
        self._ai_generating = False
        self.setReadOnly(False)
        self.aiStatusChanged.emit("❌ 生成失败")
        logger.error(f"AI生成错误: {error}")
        QMessageBox.critical(self, "错误", f"AI生成失败：{error}")

    def _on_ai_timeout(self):
        """AI生成超时，自动重置状态"""
        self._ai_generating = False
        self.setReadOnly(False)
        self.aiStatusChanged.emit("⏰ AI生成超时，已自动重置")
        logger.warning("AI生成超时（120秒），已自动重置_ai_generating")

    def _run_ai_stream_generation(self, prompt: str, status_message: str, max_tokens: int = 0):
        """运行AI生成（流式输出）

        Args:
            prompt: AI提示词
            status_message: 状态提示信息
            max_tokens: 最大生成token数，0表示使用默认值
        """
        logger.info(f"[_run_ai_stream_generation] 进入方法, status={status_message}")
        logger.info(f"[_run_ai_stream_generation] _ai_generating={self._ai_generating}")
        if self._ai_generating:
            QMessageBox.information(self, "提示", "AI正在生成中，请等待完成")
            return

        self._ai_generating = True
        self._ai_is_continue = "续写" in status_message
        self._ai_stream_buffer = ""
        self.aiStatusChanged.emit(f"⏳ {status_message}")
        self.setReadOnly(True)
        self._ai_timeout_timer.start()
        logger.info(f"AI生成开始: {status_message}")

        is_continue_action = "续写" in status_message

        if is_continue_action:
            enhanced_prompt = prompt
        else:
            memory_context = ""
            if self._chapter_id:
                try:
                    from models.database import db_manager
                    chapter = db_manager.fetch_one(
                        "SELECT * FROM chapters WHERE id = ?", (self._chapter_id,)
                    )
                    if chapter:
                        volume = db_manager.fetch_one(
                            "SELECT project_id FROM volumes WHERE id = ?",
                            (chapter["volume_id"],)
                        )
                        if volume:
                            memory = novel_memory_manager.get_memory(volume["project_id"])
                            memory_context = memory.get_ai_context(
                                current_chapter_id=self._chapter_id,
                                max_summary_chapters=5
                            )
                except:
                    pass

            if memory_context and "=== 待解决的伏笔" in memory_context:
                enhanced_prompt = (
                    f"{prompt}\n\n"
                    "【小说记忆上下文 - 请务必参考以下信息保持连贯】\n"
                    f"{memory_context}\n"
                    "注意：请确保内容与上述伏笔和情节发展保持一致。"
                )
            else:
                enhanced_prompt = prompt

        self._run_async_stream_generate(enhanced_prompt, max_tokens=max_tokens)

    def _run_async_stream_generate(self, prompt: str, max_tokens: int = 0):
        """异步流式模式"""
        from models.ai_provider import ai_manager

        def on_token(token: str):
            self._ai_stream_buffer += token
            self.aiTokenReceived.emit(token)
            self.aiStreamingToken.emit(token)

        def on_complete(result: str):
            self.aiGenerationFinished.emit(result)

        def on_error(error: str):
            self.aiGenerationError.emit(error)

        ai_manager.generate_async(
            prompt=prompt,
            max_tokens=max_tokens if max_tokens > 0 else 2048,
            on_complete=on_complete,
            on_error=on_error,
            on_token=on_token
        )

    def find_text(self, text: str, forward: bool = True, case_sensitive: bool = False,
                  use_regex: bool = False) -> bool:
        """查找文本

        Args:
            text: 要查找的文本
            forward: 是否向前查找
            case_sensitive: 是否区分大小写
            use_regex: 是否使用正则表达式

        Returns:
            是否找到
        """
        flags = QTextDocument.FindFlags()
        if not forward:
            flags |= QTextDocument.FindBackward
        if case_sensitive:
            flags |= QTextDocument.FindCaseSensitively

        if use_regex:
            try:
                pattern = re.compile(text)
                cursor = self.textCursor()
                if forward:
                    cursor.movePosition(QTextCursor.Start)
                else:
                    cursor.movePosition(QTextCursor.End)
                self.setTextCursor(cursor)
                found = self.find(pattern.pattern, flags)
                return found
            except re.error:
                return False
        else:
            return self.find(text, flags)

    def replace_text(self, find_text: str, replace_text: str,
                     case_sensitive: bool = False, use_regex: bool = False) -> bool:
        """替换文本

        Args:
            find_text: 查找文本
            replace_text: 替换文本
            case_sensitive: 是否区分大小写
            use_regex: 是否使用正则表达式

        Returns:
            是否替换成功
        """
        cursor = self.textCursor()
        if cursor.hasSelection():
            selected = cursor.selectedText()
            if (not case_sensitive and selected.lower() == find_text.lower()) or \
               (case_sensitive and selected == find_text):
                cursor.insertText(replace_text)
                self.setTextCursor(cursor)
                return True
        return self.find_text(find_text, True, case_sensitive, use_regex)

    def replace_all(self, find_text: str, replace_text: str,
                    case_sensitive: bool = False, use_regex: bool = False) -> int:
        """替换所有匹配文本

        Args:
            find_text: 查找文本
            replace_text: 替换文本
            case_sensitive: 是否区分大小写
            use_regex: 是否使用正则表达式

        Returns:
            替换次数
        """
        count = 0
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.Start)
        self.setTextCursor(cursor)

        while self.find_text(find_text, True, case_sensitive, use_regex):
            tc = self.textCursor()
            tc.insertText(replace_text)
            self.setTextCursor(tc)
            count += 1

        return count

    def apply_theme_colors(self):
        """应用主题颜色到编辑器"""
        colors = theme_manager.get_theme_colors()

        self.setStyleSheet(f"""
            QPlainTextEdit {{
                background-color: {colors.get('editor_bg', '#FFFFFF')};
                color: {colors.get('editor_text', '#333333')};
                border: none;
                font-family: {config_manager.get("editor.font_family", "Microsoft YaHei")};
                font-size: {self._current_font_size}pt;
                selection-background-color: {colors.get('editor_selection', '#D0E4F5')};
            }}
        """)

        palette = self.palette()
        palette.setColor(self.backgroundRole(), QColor(colors.get("editor_bg", "#FFFFFF")))
        self.setPalette(palette)
        self.viewport().update()


class FindReplaceWidget(QWidget):
    """查找替换面板"""

    def __init__(self, editor: NovelEditor, parent=None):
        super().__init__(parent)
        self._editor = editor
        self.setup_ui()

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)

        from PySide6.QtWidgets import QLineEdit, QPushButton, QCheckBox

        self._find_input = QLineEdit()
        self._find_input.setPlaceholderText("查找...")
        self._find_input.setMinimumWidth(200)
        self._find_input.textChanged.connect(self.on_find_text_changed)
        layout.addWidget(self._find_input)

        self._replace_input = QLineEdit()
        self._replace_input.setPlaceholderText("替换为...")
        self._replace_input.setMinimumWidth(150)
        layout.addWidget(self._replace_input)

        self._case_check = QCheckBox("区分大小写")
        layout.addWidget(self._case_check)

        self._regex_check = QCheckBox("正则")
        layout.addWidget(self._regex_check)

        find_btn = QPushButton("查找")
        find_btn.clicked.connect(self.find_next)
        layout.addWidget(find_btn)

        replace_btn = QPushButton("替换")
        replace_btn.clicked.connect(self.replace)
        layout.addWidget(replace_btn)

        replace_all_btn = QPushButton("全部替换")
        replace_all_btn.clicked.connect(self.replace_all)
        layout.addWidget(replace_all_btn)

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(24, 24)
        close_btn.clicked.connect(self.hide)
        layout.addWidget(close_btn)

        layout.addStretch()

    def on_find_text_changed(self, text: str):
        if text:
            self._editor.find_text(text, True, self._case_check.isChecked(), self._regex_check.isChecked())

    def find_next(self):
        text = self._find_input.text()
        if text:
            self._editor.find_text(text, True, self._case_check.isChecked(), self._regex_check.isChecked())

    def replace(self):
        find_text = self._find_input.text()
        replace_text = self._replace_input.text()
        if find_text:
            self._editor.replace_text(find_text, replace_text, self._case_check.isChecked(), self._regex_check.isChecked())

    def replace_all(self):
        find_text = self._find_input.text()
        replace_text = self._replace_input.text()
        if find_text:
            count = self._editor.replace_all(find_text, replace_text, self._case_check.isChecked(), self._regex_check.isChecked())
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.information(self, "替换完成", f"共替换了 {count} 处")


class EditorTabWidget(QWidget):
    """编辑器标签页组件"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._editor = NovelEditor(self)
        self._find_widget = FindReplaceWidget(self._editor, self)
        self._find_widget.hide()

        self._ai_status_label = QLabel("")
        self._ai_status_label.setStyleSheet(
            "background-color: #E8F4FD; color: #4A90D9; padding: 4px 12px; "
            "font-size: 12px; font-weight: bold;"
        )
        self._ai_status_label.setAlignment(Qt.AlignCenter)
        self._ai_status_label.hide()

        self.setup_ui()
        self.connect_ai_signals()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self._ai_status_label)
        layout.addWidget(self._find_widget)
        layout.addWidget(self._editor)

    def connect_ai_signals(self):
        self._editor.aiStatusChanged.connect(self.on_ai_status_changed)
        self._editor.aiStreamingToken.connect(lambda t: None)

    def on_ai_status_changed(self, status: str):
        self._ai_status_label.setText(status)
        self._ai_status_label.show()
        if status.startswith("✅") or status.startswith("❌"):
            QTimer.singleShot(5000, self._ai_status_label.hide)

    def editor(self) -> NovelEditor:
        return self._editor

    def show_find(self):
        self._find_widget.show()
        self._find_widget._find_input.setFocus()
        self._find_widget._find_input.selectAll()

    def hide_find(self):
        self._find_widget.hide()