import os
import re
import sys
from typing import Dict, Optional
from PySide6.QtCore import Qt, QTimer, QSize, Signal, QObject
from PySide6.QtGui import QAction, QKeySequence, QIcon, QFont
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QToolBar, QStatusBar, QLabel, QMenuBar, QMenu, QMessageBox,
    QFileDialog, QInputDialog, QApplication, QPushButton, QFrame,
    QTabWidget, QToolButton, QProgressBar, QListWidget, QListWidgetItem,
    QTableWidget, QTableWidgetItem, QHeaderView, QTextEdit, QDialog
)
from ui.editor_widget import NovelEditor, EditorTabWidget, FindReplaceWidget
from ui.sidebar_panel import SidebarPanel
from ui.ai_panel import AIPanel
from ui.theme_manager import theme_manager
from ui.settings_dialog import SettingsDialog
from ui.help_dialog import HelpDialog, TutorialDialog
from core.novel_memory import novel_memory_manager
from core.writing_core import (
    project_manager, volume_manager, chapter_manager,
    character_manager, world_setting_manager, writing_stats_manager,
    recycle_bin_manager
)
from core.export_manager import export_manager
from core.backup_manager import backup_manager
from core.novel_scanner import NovelScanner, novel_scanner_manager
from models.database import db_manager
from models.ai_provider import ai_manager
from utils.config_manager import config_manager
from utils.logger import logger


class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()
        self._current_project_id: Optional[int] = None
        self._current_chapter_id: Optional[int] = None
        self._focus_mode = False
        self._word_count_timer = QTimer(self)
        self._auto_backup_timer = QTimer(self)
        self._daily_word_count = 0
        self._session_word_count = 0

        self.setup_window()
        self.setup_menu_bar()
        self.setup_toolbar()
        self.setup_central_widget()
        self.setup_status_bar()
        self.setup_timers()
        self.apply_theme()
        self.connect_signals()
        self.check_first_run()
        self.check_sample_data()

        logger.info("主窗口初始化完成")

    def setup_window(self):
        """设置窗口属性"""
        self.setWindowTitle("AI小说创作助手")
        self.setMinimumSize(
            config_manager.get("app.min_width", 1000),
            config_manager.get("app.min_height", 700)
        )
        self.resize(
            config_manager.get("app.window_width", 1400),
            config_manager.get("app.window_height", 900)
        )

    def setup_menu_bar(self):
        """设置菜单栏"""
        menubar = self.menuBar()

        file_menu = menubar.addMenu("文件(&F)")
        file_menu.addAction("新建项目", self.new_project, QKeySequence.New)
        file_menu.addAction("打开项目", self.open_project, QKeySequence.Open)
        file_menu.addSeparator()
        file_menu.addAction("保存", self.save_current, QKeySequence.Save)
        file_menu.addAction("另存为...", self.save_as)
        file_menu.addSeparator()
        export_menu = file_menu.addMenu("导出")
        export_menu.addAction("导出为TXT", lambda: self.export_novel("txt"))
        export_menu.addAction("导出为Markdown", lambda: self.export_novel("markdown"))
        export_menu.addAction("导出为Word", lambda: self.export_novel("docx"))
        file_menu.addSeparator()
        file_menu.addAction("退出", self.close, QKeySequence("Ctrl+Q"))

        edit_menu = menubar.addMenu("编辑(&E)")
        edit_menu.addAction("撤销", self.undo, QKeySequence.Undo)
        edit_menu.addAction("重做", self.redo, QKeySequence("Ctrl+Y"))
        edit_menu.addSeparator()
        edit_menu.addAction("查找", self.show_find, QKeySequence.Find)
        edit_menu.addAction("替换", self.show_replace, QKeySequence("Ctrl+H"))

        view_menu = menubar.addMenu("视图(&V)")
        self._toggle_sidebar_action = view_menu.addAction("侧边栏", self.toggle_sidebar, QKeySequence("Ctrl+\\"))
        self._toggle_sidebar_action.setCheckable(True)
        self._toggle_sidebar_action.setChecked(True)
        self._toggle_ai_action = view_menu.addAction("AI面板", self.toggle_ai_panel, QKeySequence("Ctrl+Shift+A"))
        self._toggle_ai_action.setCheckable(True)
        self._toggle_ai_action.setChecked(True)
        view_menu.addSeparator()
        view_menu.addAction("专注模式", self.toggle_focus_mode, QKeySequence("Ctrl+Shift+F"))
        view_menu.addAction("全屏", self.toggle_fullscreen, QKeySequence("F11"))
        view_menu.addSeparator()
        theme_menu = view_menu.addMenu("主题")
        for theme_name in theme_manager.get_theme_names():
            theme_menu.addAction(
                theme_manager.get_theme_colors(theme_name).get("name", theme_name),
                lambda checked, t=theme_name: self.switch_theme(t)
            )

        novel_menu = menubar.addMenu("小说(&N)")
        novel_menu.addAction("新建章节", self.new_chapter, QKeySequence("Ctrl+N"))
        novel_menu.addAction("新建卷", self.new_volume)
        novel_menu.addSeparator()
        novel_menu.addAction("项目信息", self.show_project_info)
        novel_menu.addSeparator()
        novel_menu.addAction("扫描全文分析", self.show_full_novel_scan_dialog)
        novel_menu.addSeparator()
        novel_menu.addAction("记忆统计", self.show_memory_stats)

        ai_menu = menubar.addMenu("AI(&A)")
        ai_menu.addAction("一键续写", lambda: self.request_ai_action("continue"), QKeySequence("Ctrl+E"))
        ai_menu.addAction("智能润色", lambda: self.request_ai_action("polish"), QKeySequence("Ctrl+R"))
        ai_menu.addSeparator()
        ai_menu.addAction("生成人物设定", self.generate_character)
        ai_menu.addAction("生成剧情大纲", self.generate_outline)
        ai_menu.addAction("生成章节标题", self.generate_titles)
        ai_menu.addAction("生成世界观", self.generate_world)
        ai_menu.addSeparator()
        ai_menu.addAction("敏感词检测", self.check_sensitive_words)
        ai_menu.addSeparator()
        ai_menu.addAction("AI自动生成小说", self.auto_generate_novel, QKeySequence("Ctrl+Shift+G"))

        tools_menu = menubar.addMenu("工具(&T)")
        tools_menu.addAction("写作统计", self.show_writing_stats)
        tools_menu.addAction("回收站", self.show_recycle_bin)
        tools_menu.addAction("备份管理", self.show_backup_manager)
        tools_menu.addSeparator()
        tools_menu.addAction("设置", self.show_settings, QKeySequence("Ctrl+,"))

        help_menu = menubar.addMenu("帮助(&H)")
        help_menu.addAction("使用指南", self.show_help, QKeySequence("F1"))
        help_menu.addAction("新手教程", self.show_tutorial)
        help_menu.addSeparator()

        dev_action = QAction("联系开发者", self)
        dev_action.setToolTip("开发者: 青易  QQ: 24523870")
        dev_action.hovered.connect(lambda: self.statusBar().showMessage(
            "开发者: 青易  QQ: 24523870  如有问题请随时联系", 5000))
        dev_action.triggered.connect(lambda: QMessageBox.information(
            self, "联系开发者",
            "AI小说创作助手 v1.0.0\n\n"
            "开发者: 青易\n"
            "QQ: 24523870\n\n"
            "如有任何问题、建议或合作意向，\n"
            "欢迎随时联系！"))
        help_menu.addAction(dev_action)
        help_menu.addSeparator()
        help_menu.addAction("关于", self.show_about)

    def setup_toolbar(self):
        """设置工具栏"""
        toolbar = QToolBar("主工具栏")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(20, 20))
        toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.addToolBar(toolbar)

        save_btn = QAction("保存", self)
        save_btn.triggered.connect(self.save_current)
        save_btn.setShortcut(QKeySequence.Save)
        save_btn.setToolTip("保存当前章节 (Ctrl+S)")
        toolbar.addAction(save_btn)

        toolbar.addSeparator()

        bold_btn = QAction("粗体", self)
        bold_btn.triggered.connect(self.toggle_bold)
        bold_btn.setShortcut(QKeySequence.Bold)
        bold_btn.setToolTip("设置/取消粗体 (Ctrl+B)")
        toolbar.addAction(bold_btn)

        italic_btn = QAction("斜体", self)
        italic_btn.triggered.connect(self.toggle_italic)
        italic_btn.setShortcut(QKeySequence.Italic)
        italic_btn.setToolTip("设置/取消斜体 (Ctrl+I)")
        toolbar.addAction(italic_btn)

        underline_btn = QAction("下划线", self)
        underline_btn.triggered.connect(self.toggle_underline)
        underline_btn.setShortcut(QKeySequence.Underline)
        underline_btn.setToolTip("设置/取消下划线 (Ctrl+U)")
        toolbar.addAction(underline_btn)

        toolbar.addSeparator()

        ai_continue_btn = QAction("AI续写", self)
        ai_continue_btn.triggered.connect(lambda: self.request_ai_action("continue"))
        ai_continue_btn.setToolTip("使用AI续写当前选中的文本 (Ctrl+E)")
        toolbar.addAction(ai_continue_btn)

        ai_polish_btn = QAction("AI润色", self)
        ai_polish_btn.triggered.connect(lambda: self.request_ai_action("polish"))
        ai_polish_btn.setToolTip("使用AI润色当前选中的文本 (Ctrl+R)")
        toolbar.addAction(ai_polish_btn)

        toolbar.addSeparator()

        focus_btn = QAction("专注模式", self)
        focus_btn.triggered.connect(self.toggle_focus_mode)
        focus_btn.setToolTip("切换专注模式，隐藏所有面板只保留编辑器 (Ctrl+Shift+F)")
        toolbar.addAction(focus_btn)

    def setup_central_widget(self):
        """设置中央部件"""
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self._splitter = QSplitter(Qt.Horizontal)

        self._sidebar = SidebarPanel()
        self._sidebar.setMinimumWidth(200)
        self._sidebar.setMaximumWidth(400)
        self._sidebar.setToolTip("左侧面板：管理大纲、人物卡片和世界观设定")
        self._sidebar.chapterSelected.connect(self.on_chapter_selected)
        self._splitter.addWidget(self._sidebar)

        self._editor_tab_widget = QTabWidget()
        self._editor_tab_widget.setTabsClosable(True)
        self._editor_tab_widget.tabCloseRequested.connect(self.close_editor_tab)
        self._editor_tab_widget.currentChanged.connect(self.on_tab_changed)
        self._editor_tab_widget.setToolTip("写作区域：在此编辑小说章节内容")
        self._splitter.addWidget(self._editor_tab_widget)

        self._ai_panel = AIPanel()
        self._ai_panel.setMinimumWidth(250)
        self._ai_panel.setMaximumWidth(450)
        self._ai_panel.setToolTip("右侧面板：AI剧情顾问和快捷操作")
        self._splitter.addWidget(self._ai_panel)

        self._splitter.setSizes([250, 700, 300])
        main_layout.addWidget(self._splitter)

    def setup_status_bar(self):
        """设置状态栏"""
        status_bar = self.statusBar()

        self._status_project = QLabel("未打开项目")
        self._status_project.setToolTip("当前打开的小说项目名称")
        status_bar.addWidget(self._status_project)

        status_bar.addPermanentWidget(QLabel(" | "))

        self._status_words = QLabel("总字数: 0")
        self._status_words.setToolTip("当前项目的总字数统计")
        status_bar.addPermanentWidget(self._status_words)

        status_bar.addPermanentWidget(QLabel(" | "))

        self._status_session = QLabel("本日: 0")
        self._status_session.setToolTip("今日已写字数")
        status_bar.addPermanentWidget(self._status_session)

        status_bar.addPermanentWidget(QLabel(" | "))

        self._status_cursor = QLabel("行: 1  列: 1")
        self._status_cursor.setToolTip("当前光标所在行和列")
        status_bar.addPermanentWidget(self._status_cursor)

        status_bar.addPermanentWidget(QLabel(" | "))

        self._status_ai = QLabel("AI: 未连接")
        self._status_ai.setToolTip("AI模型的连接状态")
        status_bar.addPermanentWidget(self._status_ai)

        status_bar.addPermanentWidget(QLabel(" | "))

        self._status_save = QLabel("已保存")
        self._status_save.setToolTip("当前章节的保存状态")
        status_bar.addPermanentWidget(self._status_save)

        status_bar.addPermanentWidget(QLabel(" | "))

        dev_label = QLabel("开发者: 青易  QQ:24523870")
        dev_label.setProperty("devMode", True)
        dev_label.setToolTip("如有问题请联系开发者")
        status_bar.addPermanentWidget(dev_label)

    def setup_timers(self):
        """设置定时器"""
        self._word_count_timer.setInterval(5000)
        self._word_count_timer.timeout.connect(self.update_word_count_display)
        self._word_count_timer.start()

        auto_backup_enabled = config_manager.get("writing.auto_backup", True)
        if auto_backup_enabled:
            interval_seconds = config_manager.get("writing.backup_interval", 300)
            self._auto_backup_timer.setInterval(interval_seconds * 1000)
            self._auto_backup_timer.timeout.connect(self.auto_backup)
            self._auto_backup_timer.start()

    def connect_signals(self):
        """连接信号"""
        project_manager.add_listener(self.on_project_event)
        self._ai_panel._action_panel.actionRequested.connect(self.request_ai_action)

    def on_project_event(self, event: str, data: dict):
        """项目事件处理"""
        if event == "project_opened":
            self._status_project.setText(f"项目: {data.get('name', '')}")
            self._ai_panel.refresh_models()
            providers = ai_manager.get_available_providers()
            if providers:
                self._status_ai.setText(f"AI: {providers[0]}")
            else:
                self._status_ai.setText("AI: 未配置")

    def get_current_editor(self) -> Optional[NovelEditor]:
        """获取当前编辑器"""
        current_widget = self._editor_tab_widget.currentWidget()
        if current_widget and hasattr(current_widget, 'editor'):
            return current_widget.editor()
        return None

    def on_chapter_selected(self, chapter_id: int, title: str, content: str):
        """章节选择事件"""
        self._current_chapter_id = chapter_id
        logger.info(f"on_chapter_selected: chapter_id={chapter_id}, title={title}, content长度={len(content)}")

        for i in range(self._editor_tab_widget.count()):
            tab = self._editor_tab_widget.widget(i)
            if hasattr(tab, 'editor') and tab.editor().get_chapter_id() == chapter_id:
                self._editor_tab_widget.setCurrentIndex(i)
                return

        tab = EditorTabWidget()
        tab.editor().load_chapter(chapter_id, content, title)
        self._editor_tab_widget.addTab(tab, title)
        self._editor_tab_widget.setCurrentWidget(tab)

        tab.editor().cursorPositionChanged_signal.connect(self.update_cursor_position)
        tab.editor().wordCountChanged.connect(self.on_word_count_changed)

    def on_tab_changed(self, index: int):
        """标签页切换事件"""
        editor = self.get_current_editor()
        if editor:
            self._current_chapter_id = editor.get_chapter_id()

    def close_editor_tab(self, index: int):
        """关闭编辑器标签页"""
        tab = self._editor_tab_widget.widget(index)
        if tab and hasattr(tab, 'editor') and tab.editor().is_modified():
            reply = QMessageBox.question(self, "保存", "当前章节已修改，是否保存？",
                                         QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
            if reply == QMessageBox.Cancel:
                return
            if reply == QMessageBox.Yes:
                tab.editor().save_current()
        self._editor_tab_widget.removeTab(index)

    def on_word_count_changed(self, total: int, chinese: int, paragraphs: int):
        """字数变更事件"""
        self._status_words.setText(f"总字数: {total:,}")

    def update_cursor_position(self, line: int, col: int):
        """更新光标位置显示"""
        self._status_cursor.setText(f"行: {line}  列: {col}")

    def update_word_count_display(self):
        """更新字数显示"""
        if self._current_project_id:
            total = project_manager.get_project_word_count(self._current_project_id)
            self._status_words.setText(f"总字数: {total:,}")

    def apply_theme(self):
        """应用主题"""
        stylesheet = theme_manager.get_stylesheet()
        self.setStyleSheet(stylesheet)

        for i in range(self._editor_tab_widget.count()):
            tab = self._editor_tab_widget.widget(i)
            if hasattr(tab, 'editor'):
                tab.editor().apply_theme_colors()
        self._sidebar.apply_theme_colors() if hasattr(self._sidebar, 'apply_theme_colors') else None

    def showEvent(self, event):
        super().showEvent(event)
        self.apply_theme()

    def switch_theme(self, theme_name: str):
        """切换主题"""
        theme_manager.switch_to(theme_name)
        self.apply_theme()

    def toggle_sidebar(self):
        """切换侧边栏显示"""
        visible = self._sidebar.isVisible()
        self._sidebar.setVisible(not visible)
        self._toggle_sidebar_action.setChecked(not visible)

    def toggle_ai_panel(self):
        """切换AI面板显示"""
        visible = self._ai_panel.isVisible()
        self._ai_panel.setVisible(not visible)
        self._toggle_ai_action.setChecked(not visible)

    def toggle_focus_mode(self):
        """切换专注模式"""
        self._focus_mode = not self._focus_mode
        if self._focus_mode:
            self._sidebar.hide()
            self._ai_panel.hide()
            self.menuBar().hide()
            self.statusBar().hide()
        else:
            self._sidebar.show()
            self._ai_panel.show()
            self.menuBar().show()
            self.statusBar().show()

    def toggle_fullscreen(self):
        """切换全屏"""
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def new_project(self):
        """新建项目"""
        from PySide6.QtWidgets import QDialog, QFormLayout, QLineEdit, QSpinBox, QComboBox, QTextEdit, QDialogButtonBox

        dialog = QDialog(self)
        dialog.setWindowTitle("新建小说项目")
        dialog.setMinimumWidth(450)

        layout = QFormLayout(dialog)

        name_edit = QLineEdit()
        name_edit.setPlaceholderText("输入小说名称...")
        layout.addRow("小说名称：", name_edit)

        author_edit = QLineEdit()
        layout.addRow("作者：", author_edit)

        genre_combo = QComboBox()
        genre_combo.addItems(["玄幻", "奇幻", "武侠", "仙侠", "都市", "言情", "历史", "科幻", "悬疑", "恐怖", "游戏", "其他"])
        genre_combo.setEditable(True)
        layout.addRow("类型：", genre_combo)

        desc_edit = QTextEdit()
        desc_edit.setMaximumHeight(100)
        desc_edit.setPlaceholderText("输入小说简介...")
        layout.addRow("简介：", desc_edit)

        goal_spin = QSpinBox()
        goal_spin.setRange(0, 10000000)
        goal_spin.setSingleStep(10000)
        goal_spin.setSuffix(" 字")
        goal_spin.setSpecialValueText("不设置")
        layout.addRow("字数目标：", goal_spin)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)

        if dialog.exec() and name_edit.text():
            project_id = project_manager.create_project(
                name=name_edit.text(),
                author=author_edit.text(),
                genre=genre_combo.currentText(),
                description=desc_edit.toPlainText(),
                word_goal=goal_spin.value()
            )
            self.open_project_by_id(project_id)

    def open_project(self):
        """打开项目"""
        projects = project_manager.get_all_projects()
        if not projects:
            QMessageBox.information(self, "提示", "没有可打开的项目")
            return

        items = [f"{p['name']} ({p.get('author', '佚名')})" for p in projects]
        item, ok = QInputDialog.getItem(self, "打开项目", "选择项目：", items, 0, False)
        if ok and item:
            index = items.index(item)
            self.open_project_by_id(projects[index]["id"])

    def open_project_by_id(self, project_id: int):
        """通过ID打开项目"""
        project = project_manager.get_project(project_id)
        if not project:
            QMessageBox.warning(self, "错误", "项目不存在")
            return

        self._current_project_id = project_id
        project_manager.open_project(project_id)
        self._sidebar.set_project(project_id)
        self._ai_panel.set_project(project_id)
        self.setWindowTitle(f"AI小说创作助手 - {project['name']}")
        self._status_project.setText(f"项目: {project['name']}")

        while self._editor_tab_widget.count() > 0:
            self._editor_tab_widget.removeTab(0)

        self._daily_word_count = 0
        self._session_word_count = 0

    def save_current(self):
        """保存当前章节"""
        editor = self.get_current_editor()
        if editor and editor.save_current():
            self._status_save.setText("已保存")
            QTimer.singleShot(3000, lambda: self._status_save.setText(""))

    def save_as(self):
        """另存为"""
        editor = self.get_current_editor()
        if not editor:
            return

        path, _ = QFileDialog.getSaveFileName(
            self, "另存为", "", "文本文件 (*.txt);;Markdown (*.md);;所有文件 (*.*)"
        )
        if path:
            try:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(editor.toPlainText())
                QMessageBox.information(self, "成功", "文件已保存")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存失败：{e}")

    def new_chapter(self):
        """新建章节"""
        if not self._current_project_id:
            QMessageBox.information(self, "提示", "请先打开一个项目")
            return

        volumes = volume_manager.get_volumes(self._current_project_id)
        if not volumes:
            QMessageBox.information(self, "提示", "请先创建卷")
            return

        title, ok = QInputDialog.getText(self, "新建章节", "章节名称：")
        if ok:
            chapter_id = chapter_manager.create_chapter(volumes[0]["id"], title or "")
            chapter = chapter_manager.get_chapter(chapter_id)
            if chapter:
                self._sidebar.refresh()
                self.on_chapter_selected(chapter_id, chapter["title"], chapter.get("content", ""))

    def new_volume(self):
        """新建卷"""
        if not self._current_project_id:
            QMessageBox.information(self, "提示", "请先打开一个项目")
            return

        title, ok = QInputDialog.getText(self, "新建卷", "卷名称：")
        if ok and title:
            volume_manager.create_volume(self._current_project_id, title)
            self._sidebar.refresh()

    def show_full_novel_scan_dialog(self):
        """显示全文扫描分析对话框"""
        if not self._current_project_id:
            QMessageBox.information(self, "提示", "请先打开一个项目")
            return

        from PySide6.QtWidgets import (
            QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton,
            QLabel, QProgressBar, QTabWidget, QWidget,
            QMessageBox
        )

        class _ScanBridge(QObject):
            local_result = Signal(object)
            ai_token = Signal(str)
            ai_complete = Signal()
            ai_error = Signal(str)
            scan_progress = Signal(str)

        bridge = _ScanBridge()

        dialog = QDialog(self)
        dialog.setWindowTitle("扫描全文分析")
        dialog.setMinimumSize(800, 600)
        dialog.resize(900, 700)

        layout = QVBoxLayout(dialog)

        progress_bar = QProgressBar()
        progress_bar.setRange(0, 0)
        progress_bar.hide()
        layout.addWidget(progress_bar)

        status_label = QLabel("点击「开始扫描」进行全面分析")
        layout.addWidget(status_label)

        tab_widget = QTabWidget()
        layout.addWidget(tab_widget)

        local_tab = QWidget()
        local_layout = QVBoxLayout(local_tab)
        local_result_edit = QTextEdit()
        local_result_edit.setReadOnly(True)
        local_result_edit.setPlaceholderText("扫描完成后将在此显示本地统计结果...")
        local_layout.addWidget(local_result_edit)
        tab_widget.addTab(local_tab, "本地统计")

        ai_tab = QWidget()
        ai_layout = QVBoxLayout(ai_tab)
        ai_result_edit = QTextEdit()
        ai_result_edit.setReadOnly(True)
        ai_result_edit.setPlaceholderText("AI深度分析结果将在此显示（需要已配置AI模型）...")
        ai_layout.addWidget(ai_result_edit)
        tab_widget.addTab(ai_tab, "AI深度分析")

        btn_layout = QHBoxLayout()

        scan_btn = QPushButton("🔍 开始扫描")
        scan_btn.setFixedWidth(160)

        bridge.local_result.connect(lambda result: (
            last_result_holder.__setitem__(0, result),
            apply_btn.setEnabled(True),
            self._on_scan_complete(result, local_result_edit, scan_btn, progress_bar, status_label)
        )[-1])
        bridge.scan_progress.connect(lambda msg: status_label.setText(msg))

        def start_scan():
            scan_btn.setEnabled(False)
            scan_btn.setText("扫描中...")
            progress_bar.show()
            status_label.setText("正在分析，请稍候...")

            novel_scanner_manager.scan_full_novel_async(
                self._current_project_id,
                on_complete=lambda result: bridge.local_result.emit(result),
                on_progress=lambda msg: bridge.scan_progress.emit(msg)
            )

        scan_btn.clicked.connect(start_scan)
        btn_layout.addWidget(scan_btn)

        ai_scan_btn = QPushButton("🤖 AI深度分析")
        ai_scan_btn.setFixedWidth(160)

        bridge.ai_token.connect(lambda token: self._on_ai_token(ai_result_edit, token))
        bridge.ai_complete.connect(lambda: self._on_ai_complete(ai_scan_btn, progress_bar, status_label))
        bridge.ai_complete.connect(lambda: ai_analysis_text.__setitem__(0, ai_result_edit.toPlainText()))
        bridge.ai_error.connect(lambda err: self._on_ai_error(ai_scan_btn, progress_bar, status_label, dialog, err))

        def start_ai_scan():
            ai_scan_btn.setEnabled(False)
            ai_scan_btn.setText("AI分析中...")
            progress_bar.show()
            tab_widget.setCurrentWidget(ai_tab)
            status_label.setText("AI正在深度分析小说全文...")
            ai_result_edit.clear()

            NovelScanner.ai_scan_full_novel(
                self._current_project_id,
                on_complete=lambda r: bridge.ai_complete.emit(),
                on_error=lambda e: bridge.ai_error.emit(e),
                on_token=lambda t: bridge.ai_token.emit(t)
            )

        ai_scan_btn.clicked.connect(start_ai_scan)
        btn_layout.addWidget(ai_scan_btn)

        apply_btn = QPushButton("📥 应用扫描结果")
        apply_btn.setFixedWidth(160)
        apply_btn.setEnabled(False)
        apply_btn.setToolTip("将扫描检测到的新人物、地点等信息自动添加到项目中")

        last_result_holder = [None]
        ai_analysis_text = [""]

        def do_apply():
            result = last_result_holder[0]
            ai_text = ai_analysis_text[0]

            extracted_chars = []
            extracted_locations = []

            if ai_text:
                char_pattern = re.compile(r'(?:主要人物|人物名称|角色名)[：:]\s*[\s\S]*?(?=\n\n|\n##|\n\*\*)', re.MULTILINE)
                char_blocks = char_pattern.findall(ai_text)
                for block in char_blocks:
                    names = re.findall(r'(?:[-•\d.]\s*|^|\n)([\u4e00-\u9fff]{2,4})(?:\s*[：:（(]|$)', block, re.MULTILINE)
                    extracted_chars.extend([n for n in names if len(n) >= 2 and n not in
                        {'什么','怎么','然后','因为','所以','如果','但是','可以','这个','那个','我们','他们','你们','自己','大家','这样','那样','为什么'}])

                loc_pattern = re.compile(r'(?:地点|场景|环境|地理|世界)[：:]\s*[\s\S]*?(?=\n\n|\n##|\n\*\*)', re.MULTILINE)
                loc_blocks = loc_pattern.findall(ai_text)
                for block in loc_blocks:
                    locs = re.findall(r'(?:[-•\d.]\s*|^|\n)([\u4e00-\u9fff]{2,6}(?:城|镇|村|山|河|湖|海|岛|谷|林|森|原|峰|崖|洞|殿|塔|寺|观|宫|堡|楼|阁|园|馆|院|[一二三](?:楼|阁|殿|塔|院)))', block, re.MULTILINE)
                    extracted_locations.extend(locs)

                extracted_chars = list(dict.fromkeys(extracted_chars))
                extracted_locations = list(dict.fromkeys(extracted_locations))

            if not result or result.get("error", ""):
                if not ai_text:
                    QMessageBox.warning(dialog, "提示", "请先执行「开始扫描」或「AI深度分析」")
                    return

            try:
                from core.writing_core import character_manager, world_setting_manager, volume_manager
                from core.novel_scanner import NovelScanner

                if result and "error" not in result:
                    stats = NovelScanner.apply_scan_results(self._current_project_id, result)
                else:
                    stats = {"characters_created": 0, "world_settings_created": 0,
                             "foreshadowings_added": 0, "outlines_updated": 0}

                if ai_text:
                    existing_chars = character_manager.get_characters(self._current_project_id)
                    existing_names = {c["name"] for c in existing_chars}
                    for name in extracted_chars[:20]:
                        if name not in existing_names and len(name) >= 2:
                            character_manager.create_character(self._current_project_id, name,
                                notes=f"由AI深度分析自动检测")
                            stats["characters_created"] += 1
                            existing_names.add(name)

                    existing_settings = world_setting_manager.get_settings(self._current_project_id)
                    existing_titles = {s["title"] for s in existing_settings}
                    for loc in extracted_locations[:10]:
                        if loc not in existing_titles:
                            world_setting_manager.create_setting(self._current_project_id, "地理", loc,
                                f"由AI深度分析自动检测")
                            stats["world_settings_created"] += 1
                            existing_titles.add(loc)

                lines = [f"应用完成！\n"]
                if stats["characters_created"] > 0:
                    lines.append(f"新建人物卡片: {stats['characters_created']} 个")
                if stats["world_settings_created"] > 0:
                    lines.append(f"新建世界观设定: {stats['world_settings_created']} 条")
                if stats.get("outlines_updated", 0) > 0:
                    lines.append(f"更新卷描述: {stats['outlines_updated']} 卷")
                if stats["characters_created"] == 0 and stats["world_settings_created"] == 0 and stats.get("outlines_updated", 0) == 0:
                    lines.append("未发现新的可应用项")
                lines.append("\n请切换到左侧「人物」「世界观」「大纲」面板查看。")

                self._sidebar.refresh()
                QMessageBox.information(dialog, "应用完成", "\n".join(lines))
            except Exception as e:
                QMessageBox.critical(dialog, "错误", f"应用失败：{e}")

        apply_btn.clicked.connect(do_apply)
        btn_layout.addWidget(apply_btn)

        btn_layout.addStretch()

        close_btn = QPushButton("关闭")
        close_btn.setFixedWidth(100)
        close_btn.clicked.connect(dialog.accept)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)
        dialog.exec()

    def _on_scan_complete(self, result: Dict, result_edit: QTextEdit,
                           scan_btn: QPushButton, progress_bar: QProgressBar,
                           status_label: QLabel):
        """扫描完成回调（在主线程执行）"""
        scan_btn.setEnabled(True)
        scan_btn.setText("🔍 开始扫描")
        progress_bar.hide()

        if "error" in result:
            status_label.setText(f"❌ 扫描失败：{result['error']}")
            return

        status_label.setText("✅ 扫描完成")

        parts = []
        parts.append(f"📖 《{result.get('novel_name', '')}》全文分析报告")
        parts.append(f"{'='*50}")
        parts.append(f"作者: {result.get('author', '未设置')}")
        parts.append(f"类型: {result.get('genre', '未设置')}")
        parts.append(f"全篇: {result.get('total_volumes', 0)}卷, {result.get('total_chapters', 0)}章, {result.get('total_words', 0):,}字")
        parts.append(f"人物: {result.get('character_count', 0)}个已知角色")

        fs = result.get('foreshadowing_summary', {})
        parts.append(f"伏笔: {fs.get('total', 0)}个 (活跃: {fs.get('active', 0)}, 已解决: {fs.get('resolved', 0)})")
        parts.append("")

        parts.append(f"{'='*50}")
        parts.append(f"📋 卷结构概览")
        parts.append(f"{'='*50}")
        for vs in result.get('volume_summaries', []):
            parts.append(f"\n『{vs['volume_title']}』")
            parts.append(f"  章节数: {vs['chapter_count']} | 总字数: {vs['total_words']:,}")
            parts.append(f"  章节: {' → '.join(vs['chapter_titles'][:6])}")
            if len(vs['chapter_titles']) > 6:
                parts.append(f"  ...等共{vs['chapter_count']}章")
            parts.append(f"  概要: {vs['summary'][:200]}")

        parts.append(f"\n{'='*50}")
        parts.append(f"👥 人物出场统计")
        parts.append(f"{'='*50}")
        for c in result.get('character_stats', []):
            parts.append(f"  {c['name']}: 出场{c['appearances']}次, {len(c['chapter_ids'])}章出现")

        potential = result.get('potential_new_characters', [])
        if potential:
            parts.append(f"\n💡 建议创建的新人物卡片:")
            for pnc in potential[:10]:
                parts.append(f"  {pnc}")

        parts.append(f"\n{'='*50}")
        parts.append(f"🔍 伏笔状态")
        parts.append(f"{'='*50}")
        parts.append(f"  总计: {fs.get('total', 0)}个 | 活跃: {fs.get('active', 0)}个 | 已解决: {fs.get('resolved', 0)}个")
        parts.append(f"  未解决率: {fs.get('unresolved_ratio', '0%')}")

        result_edit.setPlainText("\n".join(parts))

    def _on_ai_token(self, result_edit: QTextEdit, token: str):
        """AI分析token回调（在主线程执行）"""
        result_edit.insertPlainText(token)
        cursor = result_edit.textCursor()
        cursor.movePosition(cursor.End)
        result_edit.setTextCursor(cursor)

    def _on_ai_complete(self, ai_scan_btn: QPushButton,
                         progress_bar: QProgressBar, status_label: QLabel):
        """AI分析完成回调（在主线程执行）"""
        ai_scan_btn.setEnabled(True)
        ai_scan_btn.setText("🤖 AI深度分析")
        progress_bar.hide()
        status_label.setText("✅ AI深度分析完成")

    def _on_ai_error(self, ai_scan_btn: QPushButton,
                      progress_bar: QProgressBar, status_label: QLabel,
                      dialog: QDialog, error: str):
        """AI分析错误回调（在主线程执行）"""
        ai_scan_btn.setEnabled(True)
        ai_scan_btn.setText("🤖 AI深度分析")
        progress_bar.hide()
        status_label.setText("❌ AI分析失败")
        QMessageBox.critical(dialog, "错误", f"AI分析失败：{error}")

    def show_memory_stats(self):
        """显示记忆统计"""
        if not self._current_project_id:
            QMessageBox.information(self, "提示", "请先打开一个项目")
            return

        memory = novel_memory_manager.get_memory(self._current_project_id)
        stats = memory.get_statistics()

        from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QHeaderView

        dialog = QDialog(self)
        dialog.setWindowTitle("小说记忆统计")
        dialog.setMinimumSize(500, 400)
        layout = QVBoxLayout(dialog)

        info_text = (
            f"<h3>📖 小说记忆系统</h3>"
            f"<hr>"
            f"<p><b>已压缩章节数：</b>{stats['chapter_count']} 章</p>"
            f"<p><b>已压缩卷数：</b>{stats['volume_count']} 卷</p>"
            f"<p><b>伏笔/钩子总数：</b>{stats['total_foreshadowings']}</p>"
            f"<p><b>活跃中：</b>{stats['active_foreshadowings']}</p>"
            f"<p><b>已解决：</b>{stats['resolved_foreshadowings']}</p>"
            f"<p><b>解决率：</b>{stats['resolve_rate']}</p>"
            f"<hr>"
            f"<p><b>💡 说明</b></p>"
            f"<p>• 每保存一章，系统自动压缩该章记忆</p>"
            f"<p>• 每 {3} 章执行一次全量记忆重组</p>"
            f"<p>• 伏笔和钩子在左侧「伏笔」面板中管理</p>"
            f"<p>• AI写作时会自动参考未解决的伏笔，保持情节连贯</p>"
        )

        info_label = QLabel(info_text)
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        active_fs = memory.get_active_foreshadowings()
        if active_fs:
            layout.addWidget(QLabel("<b>活跃伏笔列表：</b>"))
            table = QTableWidget()
            table.setColumnCount(3)
            table.setHorizontalHeaderLabels(["类型", "标题", "埋下位置"])
            table.horizontalHeader().setStretchLastSection(True)
            for i, fe in enumerate(active_fs[:10]):
                table.insertRow(i)
                table.setItem(i, 0, QTableWidgetItem(fe.category))
                table.setItem(i, 1, QTableWidgetItem(fe.title[:30]))
                table.setItem(i, 2, QTableWidgetItem(f"第{fe.planted_at_chapter}章"))
            layout.addWidget(table)

        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        dialog.exec()

    def show_project_info(self):
        """显示项目信息"""
        if not self._current_project_id:
            QMessageBox.information(self, "提示", "请先打开一个项目")
            return

        project = project_manager.get_project(self._current_project_id)
        if not project:
            return

        from PySide6.QtWidgets import QDialog, QFormLayout, QLabel

        dialog = QDialog(self)
        dialog.setWindowTitle("项目信息")
        dialog.setMinimumWidth(400)

        layout = QFormLayout(dialog)
        layout.addRow("名称：", QLabel(project["name"]))
        layout.addRow("作者：", QLabel(project.get("author", "未设置")))
        layout.addRow("类型：", QLabel(project.get("genre", "未设置")))
        layout.addRow("简介：", QLabel(project.get("description", "无")))
        layout.addRow("字数目标：", QLabel(f"{project.get('word_goal', 0):,} 字"))

        total_words = project_manager.get_project_word_count(self._current_project_id)
        layout.addRow("当前字数：", QLabel(f"{total_words:,} 字"))

        dialog.exec()

    def request_ai_action(self, action_type: str):
        """请求AI操作"""
        logger.info(f"main_window.request_ai_action 被调用: action_type='{action_type}'")
        editor = self.get_current_editor()
        if not editor:
            logger.warning("get_current_editor() 返回 None")
            QMessageBox.information(self, "提示", "请先打开一个章节")
            return

        if action_type == "continue":
            logger.info("main_window: 转发 continue 到 editor.request_ai_action")
            editor.request_ai_action(action_type)
            return

        selected_text = editor.get_selected_text()
        logger.info(f"main_window: selected_text长度={len(selected_text)}")
        if not selected_text:
            QMessageBox.information(self, "提示", "请先选中要处理的文本")
            return

        editor.request_ai_action(action_type)

    def generate_character(self):
        """生成人物设定"""
        if not self._current_project_id:
            QMessageBox.information(self, "提示", "请先打开一个项目")
            return

        keywords, ok = QInputDialog.getText(self, "生成人物设定", "输入人物关键词（如：高冷女杀手，25岁，有一只黑猫）：")
        if ok and keywords:
            from core.ai_prompts import get_prompt
            prompt = get_prompt("generate_character", keywords=keywords)

            def on_complete(result: str):
                if result:
                    self._safe_ui_call(self._show_ai_result_dialog, result, "生成的人物设定", 500, 400)

            ai_manager.generate_async(prompt=prompt, on_complete=on_complete)

    def _show_ai_result_dialog(self, result: str, title: str, min_w: int = 500, min_h: int = 400):
        """在主线程安全地显示AI生成结果对话框"""
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.setMinimumSize(min_w, min_h)
        layout = QVBoxLayout(dialog)
        text_edit = QTextEdit()
        text_edit.setPlainText(result)
        text_edit.setReadOnly(True)
        layout.addWidget(text_edit)
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        dialog.exec()

    def generate_outline(self):
        """生成剧情大纲"""
        if not self._current_project_id:
            QMessageBox.information(self, "提示", "请先打开一个项目")
            return

        from PySide6.QtWidgets import QDialog, QFormLayout, QLineEdit, QTextEdit, QComboBox, QDialogButtonBox

        dialog = QDialog(self)
        dialog.setWindowTitle("生成剧情大纲")
        layout = QFormLayout(dialog)

        theme_edit = QLineEdit()
        layout.addRow("小说主题：", theme_edit)

        setting_edit = QTextEdit()
        setting_edit.setMaximumHeight(80)
        layout.addRow("核心设定：", setting_edit)

        structure_combo = QComboBox()
        structure_combo.addItems(["三幕式", "五幕式"])
        layout.addRow("结构类型：", structure_combo)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)

        if dialog.exec() and theme_edit.text():
            from core.ai_prompts import get_prompt
            prompt = get_prompt("generate_outline",
                               theme=theme_edit.text(),
                               setting=setting_edit.toPlainText(),
                               structure_type=structure_combo.currentText())

            def on_complete(result: str):
                if result:
                    self._safe_ui_call(self._show_ai_result_dialog, result, "生成的剧情大纲", 600, 500)

            ai_manager.generate_async(prompt=prompt, on_complete=on_complete)

    def generate_titles(self):
        """生成章节标题"""
        editor = self.get_current_editor()
        if not editor:
            QMessageBox.information(self, "提示", "请先打开一个章节")
            return

        content = editor.toPlainText()
        if not content:
            QMessageBox.information(self, "提示", "当前章节内容为空")
            return

        from core.ai_prompts import get_prompt
        prompt = get_prompt("generate_titles", content=content[:1000])

        def on_complete(result: str):
            if result:
                self._safe_ui_call(QMessageBox.information, self, "推荐标题", result)

        ai_manager.generate_async(prompt=prompt, on_complete=on_complete)

    def generate_world(self):
        """生成世界观"""
        if not self._current_project_id:
            QMessageBox.information(self, "提示", "请先打开一个项目")
            return

        setting, ok = QInputDialog.getText(self, "生成世界观", "输入核心设定：")
        if ok and setting:
            from core.ai_prompts import get_prompt
            prompt = get_prompt("generate_world", setting=setting)

            def on_complete(result: str):
                if result:
                    self._safe_ui_call(self._show_ai_result_dialog, result, "生成的世界观", 600, 500)

            ai_manager.generate_async(prompt=prompt, on_complete=on_complete)

    def _safe_ui_call(self, callback, *args, **kwargs):
        """确保UI操作在主线程执行（解决后台线程不能操作UI的问题）"""
        QTimer.singleShot(0, lambda: callback(*args, **kwargs))

    def check_sensitive_words(self):
        """敏感词检测"""
        editor = self.get_current_editor()
        if not editor:
            QMessageBox.information(self, "提示", "请先打开一个章节")
            return

        content = editor.toPlainText()
        if not content:
            QMessageBox.information(self, "提示", "当前章节内容为空")
            return

        from core.ai_prompts import get_prompt
        prompt = get_prompt("sensitive_check", content=content)

        def on_complete(result: str):
            if result:
                self._safe_ui_call(QMessageBox.information, self, "敏感词检测结果", result)

        ai_manager.generate_async(prompt=prompt, on_complete=on_complete)

    def auto_generate_novel(self):
        """AI自动生成小说"""
        from ui.auto_generate_dialog import AutoGenerateDialog
        dialog = AutoGenerateDialog(self)
        if dialog.exec():
            pass

    def export_novel(self, fmt: str):
        """导出小说"""
        if not self._current_project_id:
            QMessageBox.information(self, "提示", "请先打开一个项目")
            return

        project = project_manager.get_project(self._current_project_id)
        if not project:
            return

        ext_map = {"txt": "txt", "markdown": "md", "docx": "docx"}
        filter_map = {
            "txt": "文本文件 (*.txt)",
            "markdown": "Markdown (*.md)",
            "docx": "Word文档 (*.docx)"
        }

        default_name = f"{project['name']}.{ext_map[fmt]}"
        path, _ = QFileDialog.getSaveFileName(self, "导出小说", default_name, filter_map[fmt])
        if not path:
            return

        volumes = volume_manager.get_volumes(self._current_project_id)
        all_chapters = []
        for volume in volumes:
            chapters = chapter_manager.get_chapters(volume["id"])
            for chapter in chapters:
                chapter["volume_title"] = volume["title"]
                all_chapters.append(chapter)

        if not all_chapters:
            QMessageBox.information(self, "提示", "没有可导出的章节")
            return

        def on_complete(success: bool):
            if success:
                QMessageBox.information(self, "成功", f"小说已导出到：{path}")
            else:
                QMessageBox.critical(self, "错误", "导出失败，请检查日志")

        export_manager.export_async(fmt, all_chapters, path, on_complete=on_complete)

    def show_find(self):
        """显示查找面板"""
        editor = self.get_current_editor()
        if editor and editor.parent():
            tab = editor.parent()
            if hasattr(tab, 'show_find'):
                tab.show_find()

    def show_replace(self):
        """显示替换面板"""
        self.show_find()

    def toggle_bold(self):
        """切换粗体"""
        editor = self.get_current_editor()
        if editor:
            fmt = editor.currentCharFormat()
            fmt.setBold(not fmt.font().bold())
            editor.setCurrentCharFormat(fmt)

    def toggle_italic(self):
        """切换斜体"""
        editor = self.get_current_editor()
        if editor:
            fmt = editor.currentCharFormat()
            fmt.setFontItalic(not fmt.fontItalic())
            editor.setCurrentCharFormat(fmt)

    def toggle_underline(self):
        """切换下划线"""
        editor = self.get_current_editor()
        if editor:
            fmt = editor.currentCharFormat()
            fmt.setFontUnderline(not fmt.fontUnderline())
            editor.setCurrentCharFormat(fmt)

    def undo(self):
        """撤销"""
        editor = self.get_current_editor()
        if editor:
            editor.undo()

    def redo(self):
        """重做"""
        editor = self.get_current_editor()
        if editor:
            editor.redo()

    def show_writing_stats(self):
        """显示写作统计"""
        if not self._current_project_id:
            QMessageBox.information(self, "提示", "请先打开一个项目")
            return

        stats = writing_stats_manager.get_stats(self._current_project_id, 30)
        total = writing_stats_manager.get_total_stats(self._current_project_id)

        from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QHeaderView

        dialog = QDialog(self)
        dialog.setWindowTitle("写作统计")
        dialog.setMinimumSize(500, 400)

        layout = QVBoxLayout(dialog)

        info_layout = QHBoxLayout()
        info_layout.addWidget(QLabel(f"总字数：{total['total_words']:,}"))
        info_layout.addWidget(QLabel(f"总时长：{total['total_time'] // 60} 分钟"))
        layout.addLayout(info_layout)

        table = QTableWidget()
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(["日期", "字数", "时长(分钟)"])
        table.horizontalHeader().setStretchLastSection(True)

        for i, stat in enumerate(stats):
            table.insertRow(i)
            table.setItem(i, 0, QTableWidgetItem(stat["date"]))
            table.setItem(i, 1, QTableWidgetItem(str(stat["word_count"])))
            table.setItem(i, 2, QTableWidgetItem(str(stat["writing_time"] // 60)))

        layout.addWidget(table)
        dialog.exec()

    def show_recycle_bin(self):
        """显示回收站"""
        items = recycle_bin_manager.get_items()
        if not items:
            QMessageBox.information(self, "回收站", "回收站为空")
            return

        from PySide6.QtWidgets import QDialog, QVBoxLayout, QListWidget, QPushButton, QHBoxLayout

        dialog = QDialog(self)
        dialog.setWindowTitle("回收站")
        dialog.setMinimumSize(500, 400)

        layout = QVBoxLayout(dialog)

        list_widget = QListWidget()
        for item in items:
            display = f"[{item['original_table']}] ID:{item['original_id']} - {item['deleted_at'][:19]}"
            list_widget.addItem(display)
            list_widget.item(list_widget.count() - 1).setData(Qt.UserRole, item["id"])

        layout.addWidget(list_widget)

        btn_layout = QHBoxLayout()
        restore_btn = QPushButton("恢复")
        def restore():
            current = list_widget.currentItem()
            if current:
                recycle_bin_manager.restore_item(current.data(Qt.UserRole))
                list_widget.takeItem(list_widget.row(current))
        restore_btn.clicked.connect(restore)
        btn_layout.addWidget(restore_btn)

        delete_btn = QPushButton("永久删除")
        def delete():
            current = list_widget.currentItem()
            if current:
                recycle_bin_manager.permanently_delete(current.data(Qt.UserRole))
                list_widget.takeItem(list_widget.row(current))
        delete_btn.clicked.connect(delete)
        btn_layout.addWidget(delete_btn)

        empty_btn = QPushButton("清空回收站")
        empty_btn.clicked.connect(lambda: [recycle_bin_manager.empty_bin(), list_widget.clear()])
        btn_layout.addWidget(empty_btn)

        layout.addLayout(btn_layout)
        dialog.exec()

    def show_backup_manager(self):
        """显示备份管理"""
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QListWidget, QPushButton, QHBoxLayout, QLabel

        backups = backup_manager.list_backups()
        dialog = QDialog(self)
        dialog.setWindowTitle("备份管理")
        dialog.setMinimumSize(500, 400)

        layout = QVBoxLayout(dialog)

        if not backups:
            layout.addWidget(QLabel("暂无备份"))
        else:
            list_widget = QListWidget()
            for b in backups:
                size_str = f"{b['size'] / 1024:.1f} KB" if b['size'] < 1024 * 1024 else f"{b['size'] / 1024 / 1024:.1f} MB"
                list_widget.addItem(f"{b['name']} ({size_str}) - {b['created_at'][:19]}")
                list_widget.item(list_widget.count() - 1).setData(Qt.UserRole, b["path"])
            layout.addWidget(list_widget)

        btn_layout = QHBoxLayout()

        backup_btn = QPushButton("创建备份")
        def create_backup():
            db_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "data", "novel_writer.db"
            )
            backup_manager.create_backup(db_path, on_complete=lambda s, p: QMessageBox.information(dialog, "提示", "备份创建成功" if s else f"备份失败：{p}"))
        backup_btn.clicked.connect(create_backup)
        btn_layout.addWidget(backup_btn)

        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(dialog.accept)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)
        dialog.exec()

    def show_settings(self):
        """显示设置对话框"""
        dialog = SettingsDialog(self)
        if dialog.exec():
            self.apply_theme()
            self._ai_panel.refresh_models()

    def auto_backup(self):
        """自动备份"""
        if self._current_project_id:
            db_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "data", "novel_writer.db"
            )
            backup_manager.create_backup(db_path)

    def check_first_run(self):
        """检查是否首次运行，首次运行显示教程"""
        first_run = config_manager.get("app.first_run", True)
        if first_run:
            config_manager.set("app.first_run", False)
            QTimer.singleShot(500, self.show_tutorial)

    def check_sample_data(self):
        """检查是否有样例数据，如果没有提示创建"""
        projects = project_manager.get_all_projects()
        if not projects:
            reply = QMessageBox.question(
                self, "欢迎使用",
                "是否加载悬疑小说《第七层梦境》的演示数据？\n"
                "（包含6卷22章，约13000字的完整悬疑故事，\n"
                "以及人物卡片和世界观设定）\n\n"
                "选择「是」加载演示数据，"
                "选择「否」直接开始创作。",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.load_sample_data()

    def load_sample_data(self):
        """加载样例数据"""
        import subprocess
        script_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "scripts", "create_sample.py"
        )
        if os.path.exists(script_path):
            try:
                subprocess.run(
                    [sys.executable, script_path],
                    cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    capture_output=True, timeout=30
                )
                QMessageBox.information(
                    self, "加载完成",
                    "演示数据加载成功！\n\n"
                    "请点击「文件 → 打开项目」\n"
                    "选择「第七层梦境」即可浏览。\n\n"
                    "包含：\n"
                    "• 6卷22章悬疑故事（约13000字）\n"
                    "• 5个完整的人物卡片\n"
                    "• 5条世界观设定"
                )
            except Exception as e:
                logger.error(f"加载样例数据失败: {e}")

    def show_help(self):
        """显示帮助指南"""
        dialog = HelpDialog(self)
        dialog.exec()

    def show_tutorial(self):
        """显示新手教程"""
        dialog = TutorialDialog(self)
        dialog.exec()

    def show_about(self):
        """显示关于对话框"""
        QMessageBox.about(
            self,
            "关于 AI小说创作助手",
            """<h2>AI小说创作助手 v1.0.0</h2>
            <p>基于 PySide6 的AI辅助小说创作工具</p>
            <p>功能特点：</p>
            <ul>
                <li>专业文本编辑器</li>
                <li>AI辅助创作（续写、润色、扩写等）</li>
                <li>多模型支持（OpenAI、文心一言、通义千问、本地模型）</li>
                <li>项目管理（分卷分章、人物卡片、世界观设定）</li>
                <li>多种导出格式（TXT、Markdown、Word）</li>
                <li>多主题支持（浅色、深色、护眼模式）</li>
            </ul>
            """
        )

    def closeEvent(self, event):
        """关闭事件"""
        editor = self.get_current_editor()
        if editor and editor.is_modified():
            reply = QMessageBox.question(self, "保存", "当前章节未保存，是否保存？",
                                         QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
            if reply == QMessageBox.Cancel:
                event.ignore()
                return
            if reply == QMessageBox.Yes:
                editor.save_current()

        db_manager.close()
        event.accept()