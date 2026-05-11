from typing import Optional
from PySide6.QtCore import Qt, QTimer, QObject, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton,
    QLabel, QFrame, QScrollArea, QToolButton, QComboBox, QSizePolicy
)
from models.ai_provider import ai_manager
from core.ai_prompts import AI_CONSULTANT_SYSTEM
from core.novel_memory import novel_memory_manager
from utils.logger import logger


class ChatBubble(QFrame):
    """AI对话气泡"""

    def __init__(self, content: str = "", is_user: bool = False, parent=None,
                 is_streaming: bool = False):
        super().__init__(parent)
        self._content_label = None
        self._is_streaming = is_streaming
        self.setup_ui(content, is_user)

    def setup_ui(self, content: str, is_user: bool):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(2)

        role_text = "你" if is_user else "AI 顾问"
        if self._is_streaming:
            role_text += " (正在输入...)"
        role_label = QLabel(role_text)
        role_label.setStyleSheet(
            f"font-weight: bold; font-size: 11px; color: {'#4A90D9' if is_user else '#52C41A'};"
        )
        layout.addWidget(role_label)

        self._content_label = QLabel(content if content else " ")
        self._content_label.setWordWrap(True)
        self._content_label.setStyleSheet(
            f"font-size: 13px; padding: 8px; border-radius: 6px; "
            f"background-color: {'#E8F4FD' if is_user else '#F0F9F0'};"
        )
        self._content_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(self._content_label)

    def append_text(self, text: str):
        if self._content_label:
            current = self._content_label.text()
            if current == " ":
                self._content_label.setText(text)
            else:
                self._content_label.setText(current + text)


class AIConsultantPanel(QWidget):
    """AI剧情顾问面板"""

    _aiTokenReceived = Signal(str)
    _aiReplyFinished = Signal(str)
    _aiReplyError = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._project_id: Optional[int] = None
        self._conversation_history = []
        self._streaming_bubble = None
        self.setup_ui()
        self._aiTokenReceived.connect(self._on_token_main_thread)
        self._aiReplyFinished.connect(self._on_reply_finished_main_thread)
        self._aiReplyError.connect(self._on_reply_error_main_thread)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QFrame()
        header.setFixedHeight(40)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(8, 4, 8, 4)

        title_label = QLabel("AI 剧情顾问")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        self._model_combo = QComboBox()
        self._model_combo.setMinimumWidth(100)
        self._model_combo.setToolTip("选择要使用的AI模型（需先在设置中配置）")
        self._model_combo.currentTextChanged.connect(self.on_model_changed)
        header_layout.addWidget(self._model_combo)

        clear_btn = QToolButton()
        clear_btn.setText("清空")
        clear_btn.setToolTip("清空当前AI对话记录")
        clear_btn.clicked.connect(self.clear_conversation)
        header_layout.addWidget(clear_btn)

        layout.addWidget(header)

        self._scroll_area = QScrollArea()
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self._chat_container = QWidget()
        self._chat_layout = QVBoxLayout(self._chat_container)
        self._chat_layout.setAlignment(Qt.AlignTop)
        self._chat_layout.setSpacing(8)
        self._chat_layout.addStretch()

        self._scroll_area.setWidget(self._chat_container)
        layout.addWidget(self._scroll_area, 1)

        input_container = QFrame()
        input_container.setFixedHeight(120)
        input_layout = QVBoxLayout(input_container)
        input_layout.setContentsMargins(8, 4, 8, 4)
        input_layout.setSpacing(4)

        self._input_edit = QTextEdit()
        self._input_edit.setPlaceholderText("输入你的问题，与AI讨论剧情...")
        self._input_edit.setMaximumHeight(60)
        input_layout.addWidget(self._input_edit)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self._send_btn = QPushButton("发送")
        self._send_btn.setFixedWidth(80)
        self._send_btn.setToolTip("将问题发送给AI剧情顾问")
        self._send_btn.clicked.connect(self.send_message)
        self._input_edit.installEventFilter(self)
        input_layout.addLayout(btn_layout)
        btn_layout.addWidget(self._send_btn)

        layout.addWidget(input_container)

        self.refresh_models()

    def set_project(self, project_id: int):
        self._project_id = project_id

    def refresh_models(self):
        current = self._model_combo.currentText()
        self._model_combo.clear()
        providers = ai_manager.get_available_providers()
        if providers:
            self._model_combo.addItems(providers)
            if current in providers:
                self._model_combo.setCurrentText(current)
        else:
            self._model_combo.addItem("未配置模型")

    def on_model_changed(self, model_name: str):
        if model_name and model_name != "未配置模型":
            ai_manager.set_current_provider(model_name)

    def send_message(self):
        content = self._input_edit.toPlainText().strip()
        if not content:
            return

        self.add_message(content, is_user=True)
        self._input_edit.clear()
        self._send_btn.setEnabled(False)
        self._send_btn.setText("等待回复...")

        self._conversation_history.append({"role": "user", "content": content})

        novel_context = ""
        if self._project_id:
            try:
                memory = novel_memory_manager.get_memory(self._project_id)
                novel_context = memory.get_ai_context(max_summary_chapters=5)
                logger.info(f"剧情顾问获取小说上下文: {len(novel_context)}字符")
            except Exception as e:
                logger.error(f"获取小说上下文失败: {e}")

        messages_text = self._build_conversation_context()
        if novel_context:
            full_prompt = f"【当前小说进度与伏笔】\n{novel_context}\n\n【用户当前问题】\n{messages_text}"
        else:
            full_prompt = messages_text

        def on_token(token: str):
            self._aiTokenReceived.emit(token)

        def on_complete(result: str):
            self._aiReplyFinished.emit(result)

        def on_error(error: str):
            self._aiReplyError.emit(error)

        ai_manager.generate_async(
            prompt=full_prompt,
            system_prompt=AI_CONSULTANT_SYSTEM,
            on_complete=on_complete,
            on_error=on_error,
            on_token=on_token
        )

    def _on_token_main_thread(self, token: str):
        """主线程处理AI流式token"""
        if not self._streaming_bubble:
            self._streaming_bubble = ChatBubble("", is_user=False, is_streaming=True)
            self._chat_layout.insertWidget(
                self._chat_layout.count() - 1, self._streaming_bubble
            )
        self._streaming_bubble.append_text(token)
        QTimer.singleShot(10, self._scroll_to_bottom)

    def _on_reply_finished_main_thread(self, result: str):
        """主线程处理AI回复完成"""
        self._send_btn.setEnabled(True)
        self._send_btn.setText("发送")
        self._streaming_bubble = None
        if result:
            if result.startswith("错误:") or result.startswith("生成失败"):
                self.add_message(f"AI响应出错：{result}", is_user=False)
            else:
                self._conversation_history.append(
                    {"role": "assistant", "content": result}
                )

    def _on_reply_error_main_thread(self, error: str):
        """主线程处理AI回复错误"""
        self._send_btn.setEnabled(True)
        self._send_btn.setText("发送")
        self._streaming_bubble = None
        self.add_message(f"抱歉，AI响应出错：{error}", is_user=False)

    def _build_conversation_context(self) -> str:
        parts = []
        for msg in self._conversation_history[-6:]:
            role = "用户" if msg["role"] == "user" else "AI顾问"
            parts.append(f"{role}: {msg['content'][:300]}")
        if not parts:
            return self._conversation_history[-1]["content"] if self._conversation_history else ""
        return "\n\n".join(parts)

    def add_message(self, content: str, is_user: bool = False):
        bubble = ChatBubble(content, is_user)
        if is_user:
            self._streaming_bubble = None
        self._chat_layout.insertWidget(self._chat_layout.count() - 1, bubble)
        QTimer.singleShot(100, self._scroll_to_bottom)

    def clear_conversation(self):
        while self._chat_layout.count() > 1:
            item = self._chat_layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()
        self._conversation_history.clear()
        self._streaming_bubble = None

    def _scroll_to_bottom(self):
        scrollbar = self._scroll_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())


class AIActionPanel(QWidget):
    """AI操作快捷面板"""

    actionRequested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        title = QLabel("AI 辅助操作")
        title.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title)

        actions = [
            ("一键续写", "continue"),
            ("智能润色", "polish"),
            ("内容扩写", "expand"),
            ("内容缩写", "summarize"),
            ("风格改写", "style_rewrite"),
            ("错别字检查", "check_spelling"),
        ]

        tooltips = {
            "continue": "根据选中的文本内容，让AI继续往下写作",
            "polish": "优化选中文句的通顺度和文采",
            "expand": "为选中的短句或段落增加细节描写",
            "summarize": "将选中的内容精简为核心梗概",
            "style_rewrite": "将选中的内容改写为指定风格（古风/科幻等）",
            "check_spelling": "检测选中文段中的错别字和语法错误",
        }

        for text, action_type in actions:
            btn = QPushButton(text)
            btn.setToolTip(tooltips.get(action_type, ""))
            btn.clicked.connect(lambda checked, a=action_type: self.actionRequested.emit(a))
            layout.addWidget(btn)

        layout.addStretch()


class AIPanel(QWidget):
    """右侧AI面板，包含AI顾问和快捷操作"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        from PySide6.QtWidgets import QTabWidget

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._tab_widget = QTabWidget()

        self._consultant_panel = AIConsultantPanel()
        self._action_panel = AIActionPanel()

        self._tab_widget.addTab(self._consultant_panel, "剧情顾问")
        self._tab_widget.addTab(self._action_panel, "快捷操作")

        layout.addWidget(self._tab_widget)

    def set_project(self, project_id: int):
        self._consultant_panel.set_project(project_id)

    def refresh_models(self):
        self._consultant_panel.refresh_models()

    def consultant_panel(self) -> AIConsultantPanel:
        return self._consultant_panel
