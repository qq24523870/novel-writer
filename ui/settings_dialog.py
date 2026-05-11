from typing import Dict, Optional
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QLabel, QLineEdit, QPushButton, QSpinBox, QDoubleSpinBox,
    QComboBox, QCheckBox, QGroupBox, QFormLayout, QFileDialog,
    QDialogButtonBox, QMessageBox, QListWidget, QListWidgetItem,
    QTextEdit, QSlider, QScrollArea
)
from utils.config_manager import config_manager
from models.ai_provider import ai_manager
from ui.theme_manager import theme_manager
from utils.logger import logger


class AISettingsPage(QWidget):
    """AI设置页面（带滚动条）"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        scroll_content = QWidget()
        layout = QVBoxLayout(scroll_content)

        cloud_group = QGroupBox("云端AI模型")
        cloud_layout = QVBoxLayout(cloud_group)

        def make_group(title, fields):
            """辅助创建模型配置组"""
            g = QGroupBox(title)
            gl = QVBoxLayout(g)
            gl.setSpacing(4)
            for label_text, widget in fields:
                row = QHBoxLayout()
                label = QLabel(label_text)
                label.setFixedWidth(100)
                row.addWidget(label)
                row.addWidget(widget, 1)
                gl.addLayout(row)
            return g

        openai_fields = [
            ("启用", self._make_checkbox("_openai_enabled", "勾选后启用OpenAI API")),
            ("API密钥", self._make_lineedit("_openai_key", True, "sk-...", "在OpenAI官网获取的API密钥")),
            ("API地址", self._make_lineedit("_openai_base", False, "https://api.openai.com/v1", "API请求地址，使用代理时可修改")),
            ("模型", self._make_combo("_openai_model", ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo", "gpt-4o"], "选择要使用的GPT模型版本")),
        ]
        cloud_layout.addWidget(make_group("OpenAI (GPT系列)", openai_fields))

        wenxin_fields = [
            ("启用", self._make_checkbox("_wenxin_enabled", "勾选后启用百度文心一言API")),
            ("API Key", self._make_lineedit("_wenxin_key", True, "", "百度智能云平台获取的API Key")),
            ("Secret Key", self._make_lineedit("_wenxin_secret", True, "", "百度智能云平台获取的Secret Key")),
        ]
        cloud_layout.addWidget(make_group("百度文心一言", wenxin_fields))

        tongyi_fields = [
            ("启用", self._make_checkbox("_tongyi_enabled", "勾选后启用阿里通义千问API")),
            ("API密钥", self._make_lineedit("_tongyi_key", True, "", "阿里云DashScope平台获取的API密钥")),
        ]
        cloud_layout.addWidget(make_group("阿里通义千问", tongyi_fields))

        custom_fields = [
            ("启用", self._make_checkbox("_custom_enabled", "勾选后启用自定义大模型接口")),
            ("API密钥", self._make_lineedit("_custom_key", True, "输入你的API密钥", "你的API密钥，从模型提供商处获取")),
            ("API地址", self._make_lineedit("_custom_base", False, "https://你的接口地址/v1", "完整的API接口地址，必须以/v1结尾")),
            ("模型名称", self._make_lineedit("_custom_model", False, "模型名称，如gpt-3.5-turbo", "你要使用的具体模型名称")),
        ]
        cloud_layout.addWidget(make_group("自定义接口 (OpenAI兼容)", custom_fields))

        self._sf_model = QComboBox()
        self._sf_model.setEditable(True)
        self._sf_model.addItems([
            "deepseek-ai/DeepSeek-V3.2", "deepseek-ai/DeepSeek-V3", "deepseek-ai/DeepSeek-R1",
            "Qwen/Qwen2.5-72B-Instruct", "Qwen/Qwen2.5-32B-Instruct",
            "Qwen/Qwen2.5-14B-Instruct", "Qwen/Qwen2.5-7B-Instruct",
            "THUDM/glm-4-9b-chat", "internlm/internlm2_5-20b-chat",
        ])
        self._sf_model.setToolTip("选择或手动输入硅基流动支持的模型名称")
        sf_fields = [
            ("启用", self._make_checkbox("_sf_enabled", "勾选后启用硅基流动API")),
            ("API密钥", self._make_lineedit("_sf_key", True, "输入硅基流动API密钥", "在硅基流动官网控制台获取API密钥")),
            ("模型", self._sf_model),
        ]
        sf_url_label = QLabel("https://api.siliconflow.cn/v1")
        sf_url_label.setStyleSheet("color: #888;")
        sf_fields.append(("API地址", sf_url_label))
        cloud_layout.addWidget(make_group("硅基流动 (SiliconFlow)", sf_fields))

        self._ds_model = QComboBox()
        self._ds_model.addItems(["deepseek-chat", "deepseek-reasoner"])
        self._ds_model.setToolTip("deepseek-chat：通用对话；deepseek-reasoner：推理模型")
        ds_fields = [
            ("启用", self._make_checkbox("_ds_enabled", "勾选后启用深度求索API")),
            ("API密钥", self._make_lineedit("_ds_key", True, "输入深度求索API密钥", "在深度求索官网平台获取API密钥")),
            ("模型", self._ds_model),
        ]
        ds_url_label = QLabel("https://api.deepseek.com")
        ds_url_label.setStyleSheet("color: #888;")
        ds_fields.append(("API地址", ds_url_label))
        cloud_layout.addWidget(make_group("深度求索 (DeepSeek)", ds_fields))

        layout.addWidget(cloud_group)

        local_group = QGroupBox("本地大模型 (llama-cpp-python)")
        local_layout = QVBoxLayout(local_group)
        self._local_enabled = QCheckBox("启用")
        local_layout.addWidget(self._local_enabled)
        path_row = QHBoxLayout()
        self._local_path = QLineEdit()
        self._local_path.setPlaceholderText("选择GGUF格式模型文件...")
        path_row.addWidget(self._local_path, 1)
        browse_btn = QPushButton("浏览...")
        browse_btn.clicked.connect(self.browse_model)
        path_row.addWidget(browse_btn)
        local_layout.addLayout(path_row)
        ctx_row = QHBoxLayout()
        ctx_row.addWidget(QLabel("上下文长度"))
        self._local_ctx = QSpinBox()
        self._local_ctx.setRange(1024, 32768)
        self._local_ctx.setValue(4096)
        self._local_ctx.setSingleStep(1024)
        ctx_row.addWidget(self._local_ctx, 1)
        local_layout.addLayout(ctx_row)
        gpu_row = QHBoxLayout()
        gpu_row.addWidget(QLabel("GPU层数"))
        self._local_gpu = QSpinBox()
        self._local_gpu.setRange(0, 100)
        self._local_gpu.setValue(0)
        gpu_row.addWidget(self._local_gpu, 1)
        local_layout.addLayout(gpu_row)
        thread_row = QHBoxLayout()
        thread_row.addWidget(QLabel("线程数"))
        self._local_threads = QSpinBox()
        self._local_threads.setRange(1, 32)
        self._local_threads.setValue(4)
        thread_row.addWidget(self._local_threads, 1)
        local_layout.addLayout(thread_row)
        layout.addWidget(local_group)

        param_group = QGroupBox("生成参数")
        param_layout = QVBoxLayout(param_group)
        temp_row = QHBoxLayout()
        temp_row.addWidget(QLabel("温度"))
        self._temperature = QDoubleSpinBox()
        self._temperature.setRange(0.1, 2.0)
        self._temperature.setSingleStep(0.1)
        self._temperature.setValue(0.8)
        temp_row.addWidget(self._temperature, 1)
        param_layout.addLayout(temp_row)
        token_row = QHBoxLayout()
        token_row.addWidget(QLabel("最大Token数"))
        self._max_tokens = QSpinBox()
        self._max_tokens.setRange(128, 8192)
        self._max_tokens.setValue(2048)
        self._max_tokens.setSingleStep(128)
        token_row.addWidget(self._max_tokens, 1)
        param_layout.addLayout(token_row)
        layout.addWidget(param_group)

        layout.addStretch()

        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)

        self.load_settings()

    def _make_checkbox(self, attr_name, tooltip=""):
        cb = QCheckBox()
        cb.setText("启用")
        if tooltip:
            cb.setToolTip(tooltip)
        setattr(self, attr_name, cb)
        return cb

    def _make_lineedit(self, attr_name, password=False, placeholder="", tooltip=""):
        le = QLineEdit()
        if password:
            le.setEchoMode(QLineEdit.Password)
        if placeholder:
            le.setPlaceholderText(placeholder)
        if tooltip:
            le.setToolTip(tooltip)
        setattr(self, attr_name, le)
        return le

    def _make_combo(self, attr_name, items, tooltip=""):
        cb = QComboBox()
        cb.addItems(items)
        if tooltip:
            cb.setToolTip(tooltip)
        setattr(self, attr_name, cb)
        return cb

    def browse_model(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择GGUF模型文件", "", "GGUF模型 (*.gguf);;所有文件 (*.*)"
        )
        if path:
            self._local_path.setText(path)

    def load_settings(self):
        ai_config = config_manager.get("ai", {})
        cloud = ai_config.get("cloud_models", {})
        local = ai_config.get("local_model", {})

        openai_cfg = cloud.get("openai", {})
        self._openai_enabled.setChecked(openai_cfg.get("enabled", False))
        self._openai_key.setText(openai_cfg.get("api_key", ""))
        self._openai_base.setText(openai_cfg.get("api_base", "https://api.openai.com/v1"))
        self._openai_model.setCurrentText(openai_cfg.get("model", "gpt-3.5-turbo"))

        wenxin_cfg = cloud.get("wenxin", {})
        self._wenxin_enabled.setChecked(wenxin_cfg.get("enabled", False))
        self._wenxin_key.setText(wenxin_cfg.get("api_key", ""))
        self._wenxin_secret.setText(wenxin_cfg.get("secret_key", ""))

        tongyi_cfg = cloud.get("tongyi", {})
        self._tongyi_enabled.setChecked(tongyi_cfg.get("enabled", False))
        self._tongyi_key.setText(tongyi_cfg.get("api_key", ""))

        custom_cfg = cloud.get("custom", {})
        self._custom_enabled.setChecked(custom_cfg.get("enabled", False))
        self._custom_key.setText(custom_cfg.get("api_key", ""))
        self._custom_base.setText(custom_cfg.get("api_base", ""))
        self._custom_model.setText(custom_cfg.get("model", ""))

        sf_cfg = cloud.get("siliconflow", {})
        self._sf_enabled.setChecked(sf_cfg.get("enabled", False))
        self._sf_key.setText(sf_cfg.get("api_key", ""))
        self._sf_model.setCurrentText(sf_cfg.get("model", "deepseek-ai/DeepSeek-V3"))

        ds_cfg = cloud.get("deepseek", {})
        self._ds_enabled.setChecked(ds_cfg.get("enabled", False))
        self._ds_key.setText(ds_cfg.get("api_key", ""))
        self._ds_model.setCurrentText(ds_cfg.get("model", "deepseek-chat"))

        self._local_enabled.setChecked(local.get("enabled", False))
        self._local_path.setText(local.get("model_path", ""))
        self._local_ctx.setValue(local.get("n_ctx", 4096))
        self._local_gpu.setValue(local.get("n_gpu_layers", 0))
        self._local_threads.setValue(local.get("n_threads", 4))

        self._temperature.setValue(ai_config.get("temperature", 0.8))
        self._max_tokens.setValue(ai_config.get("max_tokens", 2048))

    def save_settings(self):
        config_manager.set("ai.cloud_models.openai.enabled", self._openai_enabled.isChecked())
        config_manager.set("ai.cloud_models.openai.api_key", self._openai_key.text())
        config_manager.set("ai.cloud_models.openai.api_base", self._openai_base.text())
        config_manager.set("ai.cloud_models.openai.model", self._openai_model.currentText())

        config_manager.set("ai.cloud_models.wenxin.enabled", self._wenxin_enabled.isChecked())
        config_manager.set("ai.cloud_models.wenxin.api_key", self._wenxin_key.text())
        config_manager.set("ai.cloud_models.wenxin.secret_key", self._wenxin_secret.text())

        config_manager.set("ai.cloud_models.tongyi.enabled", self._tongyi_enabled.isChecked())
        config_manager.set("ai.cloud_models.tongyi.api_key", self._tongyi_key.text())

        config_manager.set("ai.cloud_models.custom.enabled", self._custom_enabled.isChecked())
        config_manager.set("ai.cloud_models.custom.api_key", self._custom_key.text())
        config_manager.set("ai.cloud_models.custom.api_base", self._custom_base.text())
        config_manager.set("ai.cloud_models.custom.model", self._custom_model.text())

        config_manager.set("ai.cloud_models.siliconflow.enabled", self._sf_enabled.isChecked())
        config_manager.set("ai.cloud_models.siliconflow.api_key", self._sf_key.text())
        config_manager.set("ai.cloud_models.siliconflow.model", self._sf_model.currentText())

        config_manager.set("ai.cloud_models.deepseek.enabled", self._ds_enabled.isChecked())
        config_manager.set("ai.cloud_models.deepseek.api_key", self._ds_key.text())
        config_manager.set("ai.cloud_models.deepseek.model", self._ds_model.currentText())

        config_manager.set("ai.local_model.enabled", self._local_enabled.isChecked())
        config_manager.set("ai.local_model.model_path", self._local_path.text())
        config_manager.set("ai.local_model.n_ctx", self._local_ctx.value())
        config_manager.set("ai.local_model.n_gpu_layers", self._local_gpu.value())
        config_manager.set("ai.local_model.n_threads", self._local_threads.value())

        config_manager.set("ai.temperature", self._temperature.value())
        config_manager.set("ai.max_tokens", self._max_tokens.value())

        ai_manager.initialize()


class EditorSettingsPage(QWidget):
    """编辑器设置页面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QFormLayout(self)

        self._font_family = QComboBox()
        self._font_family.setEditable(True)
        self._font_family.addItems(["Microsoft YaHei", "SimSun", "SimHei", "KaiTi", "FangSong", "Arial", "Consolas"])
        layout.addRow("字体：", self._font_family)

        self._font_size = QSpinBox()
        self._font_size.setRange(8, 48)
        layout.addRow("字号：", self._font_size)

        self._auto_save = QSpinBox()
        self._auto_save.setRange(10, 600)
        self._auto_save.setSuffix(" 秒")
        layout.addRow("自动保存间隔：", self._auto_save)

        self._tab_width = QSpinBox()
        self._tab_width.setRange(1, 8)
        layout.addRow("Tab宽度：", self._tab_width)

        self._wrap_mode = QCheckBox("启用自动换行")
        layout.addRow(self._wrap_mode)

        self._line_numbers = QCheckBox("显示行号")
        layout.addRow(self._line_numbers)

        self.load_settings()

    def load_settings(self):
        editor_config = config_manager.get("editor", {})
        self._font_family.setCurrentText(editor_config.get("font_family", "Microsoft YaHei"))
        self._font_size.setValue(editor_config.get("font_size", 14))
        self._auto_save.setValue(editor_config.get("auto_save_interval", 30))
        self._tab_width.setValue(editor_config.get("tab_width", 4))
        self._wrap_mode.setChecked(editor_config.get("wrap_mode", True))
        self._line_numbers.setChecked(editor_config.get("show_line_numbers", True))

    def save_settings(self):
        config_manager.set("editor.font_family", self._font_family.currentText())
        config_manager.set("editor.font_size", self._font_size.value())
        config_manager.set("editor.auto_save_interval", self._auto_save.value())
        config_manager.set("editor.tab_width", self._tab_width.value())
        config_manager.set("editor.wrap_mode", self._wrap_mode.isChecked())
        config_manager.set("editor.show_line_numbers", self._line_numbers.isChecked())


class WritingSettingsPage(QWidget):
    """写作设置页面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QFormLayout(self)

        self._daily_goal = QSpinBox()
        self._daily_goal.setRange(100, 100000)
        self._daily_goal.setSingleStep(500)
        self._daily_goal.setSuffix(" 字")
        layout.addRow("每日字数目标：", self._daily_goal)

        self._typing_sound = QCheckBox("启用打字音效")
        layout.addRow(self._typing_sound)

        self._sound_volume = QSlider(Qt.Horizontal)
        self._sound_volume.setRange(0, 100)
        layout.addRow("音效音量：", self._sound_volume)

        self._auto_backup = QCheckBox("启用自动备份")
        layout.addRow(self._auto_backup)

        self._backup_interval = QSpinBox()
        self._backup_interval.setRange(60, 3600)
        self._backup_interval.setSuffix(" 秒")
        layout.addRow("备份间隔：", self._backup_interval)

        self._backup_dir = QLineEdit()
        self._backup_dir.setReadOnly(True)
        backup_layout = QHBoxLayout()
        backup_layout.addWidget(self._backup_dir)
        browse_btn = QPushButton("浏览...")
        browse_btn.clicked.connect(self.browse_backup_dir)
        backup_layout.addWidget(browse_btn)
        layout.addRow("备份目录：", backup_layout)

        layout.addRow(QLabel(""))
        ai_group = QGroupBox("AI生成字数设置")
        ai_form = QFormLayout(ai_group)
        self._continue_words = QSpinBox()
        self._continue_words.setRange(50, 5000)
        self._continue_words.setSingleStep(50)
        self._continue_words.setSuffix(" 字")
        self._continue_words.setToolTip("AI一键续写时默认生成的文字数量")
        ai_form.addRow("续写默认字数：", self._continue_words)

        self._gen_chapters = QSpinBox()
        self._gen_chapters.setRange(2, 20)
        self._gen_chapters.setToolTip("AI自动生成小说时生成的章节数量")
        ai_form.addRow("生成章节数：", self._gen_chapters)

        self._gen_words = QSpinBox()
        self._gen_words.setRange(200, 5000)
        self._gen_words.setSingleStep(100)
        self._gen_words.setSuffix(" 字")
        self._gen_words.setToolTip("AI自动生成小说时每章约多少字")
        ai_form.addRow("每章字数：", self._gen_words)
        layout.addRow(ai_group)

        self.load_settings()

    def browse_backup_dir(self):
        path = QFileDialog.getExistingDirectory(self, "选择备份目录")
        if path:
            self._backup_dir.setText(path)

    def load_settings(self):
        writing_config = config_manager.get("writing", {})
        self._daily_goal.setValue(writing_config.get("daily_word_goal", 3000))
        self._typing_sound.setChecked(writing_config.get("typing_sound", True))
        self._sound_volume.setValue(writing_config.get("typing_sound_volume", 50))
        self._auto_backup.setChecked(writing_config.get("auto_backup", True))
        self._backup_interval.setValue(writing_config.get("backup_interval", 300))
        self._backup_dir.setText(writing_config.get("backup_dir", ""))
        self._continue_words.setValue(writing_config.get("continue_word_count", 500))
        self._gen_chapters.setValue(writing_config.get("generate_chapter_count", 6))
        self._gen_words.setValue(writing_config.get("generate_word_per_chapter", 1000))

    def save_settings(self):
        config_manager.set("writing.daily_word_goal", self._daily_goal.value())
        config_manager.set("writing.typing_sound", self._typing_sound.isChecked())
        config_manager.set("writing.typing_sound_volume", self._sound_volume.value())
        config_manager.set("writing.auto_backup", self._auto_backup.isChecked())
        config_manager.set("writing.backup_interval", self._backup_interval.value())
        config_manager.set("writing.backup_dir", self._backup_dir.text())
        config_manager.set("writing.continue_word_count", self._continue_words.value())
        config_manager.set("writing.generate_chapter_count", self._gen_chapters.value())
        config_manager.set("writing.generate_word_per_chapter", self._gen_words.value())


class SettingsDialog(QDialog):
    """设置对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.setMinimumSize(750, 600)
        self.resize(800, 700)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        self._tab_widget = QTabWidget()

        self._ai_page = AISettingsPage()
        self._editor_page = EditorSettingsPage()
        self._writing_page = WritingSettingsPage()

        self._tab_widget.addTab(self._ai_page, "AI 模型")
        self._tab_widget.addTab(self._editor_page, "编辑器")
        self._tab_widget.addTab(self._writing_page, "写作设置")

        layout.addWidget(self._tab_widget)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.save_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def save_and_accept(self):
        self._ai_page.save_settings()
        self._editor_page.save_settings()
        self._writing_page.save_settings()
        QMessageBox.information(self, "提示", "设置已保存，部分设置需要重启应用后生效。")
        self.accept()