from typing import Callable, Dict, List, Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon, QFont, QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QPushButton, QLabel, QTabWidget, QListWidget, QListWidgetItem,
    QMenu, QInputDialog, QMessageBox, QSplitter, QToolButton,
    QFrame, QAbstractItemView
)
from core.writing_core import (
    project_manager, volume_manager, chapter_manager,
    character_manager, world_setting_manager
)
from core.novel_memory import novel_memory_manager, FORESHADOWING_CATEGORIES
from utils.logger import logger


class OutlinePanel(QWidget):
    """大纲面板 - 显示卷和章节的树形结构"""

    chapterSelected = Signal(int, str, str)
    chapterDeleted = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._project_id: Optional[int] = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QFrame()
        header.setFixedHeight(40)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(8, 4, 8, 4)

        title_label = QLabel("大纲")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        add_volume_btn = QToolButton()
        add_volume_btn.setText("+卷")
        add_volume_btn.setToolTip("新建一个卷（相当于小说的一个大章节或分部）")
        add_volume_btn.clicked.connect(self.add_volume)
        header_layout.addWidget(add_volume_btn)

        add_chapter_btn = QToolButton()
        add_chapter_btn.setText("+章")
        add_chapter_btn.setToolTip("在选中的卷下新建一个章节")
        add_chapter_btn.clicked.connect(self.add_chapter)
        header_layout.addWidget(add_chapter_btn)

        layout.addWidget(header)

        self._tree = QTreeWidget()
        self._tree.setHeaderHidden(True)
        self._tree.setAnimated(True)
        self._tree.setIndentation(16)
        self._tree.setDragDropMode(QAbstractItemView.InternalMove)
        self._tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self._tree.customContextMenuRequested.connect(self.show_context_menu)
        self._tree.itemClicked.connect(self.on_item_clicked)
        self._tree.itemDoubleClicked.connect(self.on_item_double_clicked)
        layout.addWidget(self._tree)

    def set_project(self, project_id: int):
        """设置当前项目

        Args:
            project_id: 项目ID
        """
        self._project_id = project_id
        self.refresh()

    def refresh(self):
        """刷新大纲树"""
        self._tree.clear()

        if not self._project_id:
            return

        volumes = volume_manager.get_volumes(self._project_id)
        for volume in volumes:
            volume_item = QTreeWidgetItem([volume["title"]])
            volume_item.setData(0, Qt.UserRole, ("volume", volume["id"]))
            volume_item.setFlags(volume_item.flags() | Qt.ItemIsEditable)

            font = QFont()
            font.setBold(True)
            volume_item.setFont(0, font)

            chapters = chapter_manager.get_chapters(volume["id"])
            for chapter in chapters:
                chapter_item = QTreeWidgetItem([chapter["title"]])
                chapter_item.setData(0, Qt.UserRole, ("chapter", chapter["id"]))
                chapter_item.setFlags(chapter_item.flags() | Qt.ItemIsEditable)

                word_count = chapter.get("word_count", 0)
                if word_count > 0:
                    chapter_item.setText(0, f"{chapter['title']} ({word_count}字)")

                volume_item.addChild(chapter_item)

            self._tree.addTopLevelItem(volume_item)

        self._tree.expandAll()

    def on_item_clicked(self, item: QTreeWidgetItem, column: int):
        """点击项目"""
        data = item.data(0, Qt.UserRole)
        if data and data[0] == "chapter":
            chapter_id = data[1]
            chapter = chapter_manager.get_chapter(chapter_id)
            if chapter:
                self.chapterSelected.emit(chapter_id, chapter["title"], chapter.get("content", ""))

    def on_item_double_clicked(self, item: QTreeWidgetItem, column: int):
        """双击项目"""
        data = item.data(0, Qt.UserRole)
        if data and data[0] == "volume":
            self.rename_volume(data[1])
        elif data and data[0] == "chapter":
            self.rename_chapter(data[1])

    def show_context_menu(self, pos):
        """显示右键菜单"""
        item = self._tree.itemAt(pos)
        if not item:
            return

        data = item.data(0, Qt.UserRole)
        if not data:
            return

        menu = QMenu(self)

        if data[0] == "volume":
            menu.addAction("重命名卷", lambda: self.rename_volume(data[1]))
            menu.addAction("添加章节", lambda: self.add_chapter_to_volume(data[1]))
            menu.addSeparator()
            menu.addAction("删除卷", lambda: self.delete_volume(data[1]))

        elif data[0] == "chapter":
            menu.addAction("重命名章节", lambda: self.rename_chapter(data[1]))
            menu.addSeparator()
            menu.addAction("删除章节", lambda: self.delete_chapter(data[1]))

        menu.exec(self._tree.mapToGlobal(pos))

    def add_volume(self):
        """添加新卷"""
        if not self._project_id:
            return
        title, ok = QInputDialog.getText(self, "新建卷", "卷名称：", text=f"第{len(self._tree.topLevelItemCount()) + 1}卷")
        if ok and title:
            volume_manager.create_volume(self._project_id, title)
            self.refresh()

    def add_chapter(self):
        """添加新章节到当前选中的卷"""
        current = self._tree.currentItem()
        if current:
            data = current.data(0, Qt.UserRole)
            if data and data[0] == "volume":
                self.add_chapter_to_volume(data[1])
                return
            elif data and data[0] == "chapter":
                parent = current.parent()
                if parent:
                    parent_data = parent.data(0, Qt.UserRole)
                    if parent_data:
                        self.add_chapter_to_volume(parent_data[1])
                        return

        volumes = volume_manager.get_volumes(self._project_id)
        if volumes:
            self.add_chapter_to_volume(volumes[0]["id"])

    def add_chapter_to_volume(self, volume_id: int):
        """向指定卷添加章节"""
        title, ok = QInputDialog.getText(self, "新建章节", "章节名称：")
        if ok:
            if not title:
                chapters = chapter_manager.get_chapters(volume_id)
                title = f"第{len(chapters) + 1}章"
            chapter_manager.create_chapter(volume_id, title)
            self.refresh()

    def rename_volume(self, volume_id: int):
        """重命名卷"""
        volume = volume_manager.get_volumes(project_manager.get_current_project_id())
        vol = next((v for v in volume if v["id"] == volume_id), None)
        if vol:
            title, ok = QInputDialog.getText(self, "重命名卷", "新名称：", text=vol["title"])
            if ok and title:
                volume_manager.update_volume(volume_id, {"title": title})
                self.refresh()

    def rename_chapter(self, chapter_id: int):
        """重命名章节"""
        chapter = chapter_manager.get_chapter(chapter_id)
        if chapter:
            title, ok = QInputDialog.getText(self, "重命名章节", "新名称：", text=chapter["title"])
            if ok and title:
                chapter_manager.update_chapter(chapter_id, {"title": title})
                self.refresh()

    def delete_volume(self, volume_id: int):
        """删除卷"""
        reply = QMessageBox.question(self, "确认删除", "确定要删除此卷及其所有章节吗？",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            volume_manager.delete_volume(volume_id)
            self.refresh()

    def delete_chapter(self, chapter_id: int):
        """删除章节"""
        reply = QMessageBox.question(self, "确认删除", "确定要删除此章节吗？",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            chapter_manager.delete_chapter(chapter_id)
            self.chapterDeleted.emit(chapter_id)
            self.refresh()


class CharacterPanel(QWidget):
    """人物卡片面板"""

    characterSelected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._project_id: Optional[int] = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QFrame()
        header.setFixedHeight(40)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(8, 4, 8, 4)

        title_label = QLabel("人物")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        add_btn = QToolButton()
        add_btn.setText("+人物")
        add_btn.setToolTip("新建一个人物卡片，记录角色的详细信息")
        add_btn.clicked.connect(self.add_character)
        header_layout.addWidget(add_btn)

        layout.addWidget(header)

        self._list = QListWidget()
        self._list.setContextMenuPolicy(Qt.CustomContextMenu)
        self._list.customContextMenuRequested.connect(self.show_context_menu)
        self._list.itemClicked.connect(self.on_item_clicked)
        self._list.itemDoubleClicked.connect(self.on_item_double_clicked)
        layout.addWidget(self._list)

    def set_project(self, project_id: int):
        self._project_id = project_id
        self.refresh()

    def refresh(self):
        self._list.clear()
        if not self._project_id:
            return

        characters = character_manager.get_characters(self._project_id)
        for char in characters:
            item = QListWidgetItem(f"{char['name']} ({char.get('gender', '未知')})")
            item.setData(Qt.UserRole, char["id"])
            self._list.addItem(item)

    def add_character(self):
        if not self._project_id:
            return
        name, ok = QInputDialog.getText(self, "新建人物", "人物名称：")
        if ok and name:
            character_manager.create_character(self._project_id, name)
            self.refresh()

    def on_item_clicked(self, item: QListWidgetItem):
        char_id = item.data(Qt.UserRole)
        char = character_manager.get_character(char_id)
        if char:
            self.characterSelected.emit(char["name"])

    def on_item_double_clicked(self, item: QListWidgetItem):
        self.edit_character(item.data(Qt.UserRole))

    def show_context_menu(self, pos):
        item = self._list.itemAt(pos)
        if not item:
            return

        menu = QMenu(self)
        char_id = item.data(Qt.UserRole)
        menu.addAction("编辑", lambda: self.edit_character(char_id))
        menu.addAction("删除", lambda: self.delete_character(char_id))
        menu.exec(self._list.mapToGlobal(pos))

    def edit_character(self, char_id: int):
        char = character_manager.get_character(char_id)
        if not char:
            return

        from PySide6.QtWidgets import QDialog, QFormLayout, QLineEdit, QTextEdit, QDialogButtonBox

        dialog = QDialog(self)
        dialog.setWindowTitle(f"编辑人物 - {char['name']}")
        dialog.setMinimumWidth(500)
        dialog.setMinimumHeight(400)

        layout = QFormLayout(dialog)

        name_edit = QLineEdit(char["name"])
        layout.addRow("姓名：", name_edit)

        gender_edit = QLineEdit(char.get("gender", ""))
        layout.addRow("性别：", gender_edit)

        age_edit = QLineEdit(char.get("age", ""))
        layout.addRow("年龄：", age_edit)

        appearance_edit = QTextEdit(char.get("appearance", ""))
        appearance_edit.setMaximumHeight(80)
        layout.addRow("外貌：", appearance_edit)

        personality_edit = QTextEdit(char.get("personality", ""))
        personality_edit.setMaximumHeight(80)
        layout.addRow("性格：", personality_edit)

        background_edit = QTextEdit(char.get("background", ""))
        background_edit.setMaximumHeight(80)
        layout.addRow("背景：", background_edit)

        catchphrase_edit = QLineEdit(char.get("catchphrase", ""))
        layout.addRow("口头禅：", catchphrase_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)

        if dialog.exec():
            character_manager.update_character(char_id, {
                "name": name_edit.text(),
                "gender": gender_edit.text(),
                "age": age_edit.text(),
                "appearance": appearance_edit.toPlainText(),
                "personality": personality_edit.toPlainText(),
                "background": background_edit.toPlainText(),
                "catchphrase": catchphrase_edit.text()
            })
            self.refresh()

    def delete_character(self, char_id: int):
        reply = QMessageBox.question(self, "确认删除", "确定要删除此人物卡片吗？",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            character_manager.delete_character(char_id)
            self.refresh()


class WorldSettingPanel(QWidget):
    """世界观设定面板"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._project_id: Optional[int] = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QFrame()
        header.setFixedHeight(40)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(8, 4, 8, 4)

        title_label = QLabel("世界观")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        add_btn = QToolButton()
        add_btn.setText("+设定")
        add_btn.setToolTip("新建世界观设定（如地理、历史、种族、科技等）")
        add_btn.clicked.connect(self.add_setting)
        header_layout.addWidget(add_btn)

        layout.addWidget(header)

        self._tree = QTreeWidget()
        self._tree.setHeaderHidden(True)
        self._tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self._tree.customContextMenuRequested.connect(self.show_context_menu)
        self._tree.itemDoubleClicked.connect(self.on_item_double_clicked)
        layout.addWidget(self._tree)

    def set_project(self, project_id: int):
        self._project_id = project_id
        self.refresh()

    def refresh(self):
        self._tree.clear()
        if not self._project_id:
            return

        settings = world_setting_manager.get_settings(self._project_id)
        categories = {}
        for s in settings:
            cat = s.get("category", "其他")
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(s)

        for category, items in categories.items():
            cat_item = QTreeWidgetItem([f"{category} ({len(items)})"])
            cat_item.setData(0, Qt.UserRole, ("category", category))
            font = QFont()
            font.setBold(True)
            cat_item.setFont(0, font)

            for item in items:
                sub_item = QTreeWidgetItem([item["title"]])
                sub_item.setData(0, Qt.UserRole, ("setting", item["id"]))
                cat_item.addChild(sub_item)

            self._tree.addTopLevelItem(cat_item)

        self._tree.expandAll()

    def add_setting(self):
        if not self._project_id:
            return

        from PySide6.QtWidgets import QDialog, QFormLayout, QLineEdit, QTextEdit, QComboBox, QDialogButtonBox

        dialog = QDialog(self)
        dialog.setWindowTitle("新建世界观设定")
        dialog.setMinimumWidth(500)

        layout = QFormLayout(dialog)

        title_edit = QLineEdit()
        layout.addRow("标题：", title_edit)

        category_combo = QComboBox()
        category_combo.addItems(world_setting_manager.CATEGORIES)
        layout.addRow("分类：", category_combo)

        content_edit = QTextEdit()
        content_edit.setPlaceholderText("请输入设定内容...")
        layout.addRow("内容：", content_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)

        if dialog.exec() and title_edit.text():
            world_setting_manager.create_setting(
                self._project_id,
                category_combo.currentText(),
                title_edit.text(),
                content_edit.toPlainText()
            )
            self.refresh()

    def on_item_double_clicked(self, item, column):
        data = item.data(0, Qt.UserRole)
        if data and data[0] == "setting":
            self.edit_setting(data[1])

    def show_context_menu(self, pos):
        item = self._tree.itemAt(pos)
        if not item:
            return

        data = item.data(0, Qt.UserRole)
        if not data:
            return

        menu = QMenu(self)
        if data[0] == "setting":
            menu.addAction("编辑", lambda: self.edit_setting(data[1]))
            menu.addAction("删除", lambda: self.delete_setting(data[1]))
        menu.exec(self._tree.mapToGlobal(pos))

    def edit_setting(self, setting_id: int):
        s = world_setting_manager.get_setting(setting_id)
        if not s:
            return

        from PySide6.QtWidgets import QDialog, QFormLayout, QLineEdit, QTextEdit, QComboBox, QDialogButtonBox

        dialog = QDialog(self)
        dialog.setWindowTitle(f"编辑设定 - {s['title']}")
        dialog.setMinimumWidth(500)

        layout = QFormLayout(dialog)

        title_edit = QLineEdit(s["title"])
        layout.addRow("标题：", title_edit)

        category_combo = QComboBox()
        category_combo.addItems(world_setting_manager.CATEGORIES)
        category_combo.setCurrentText(s.get("category", "其他"))
        layout.addRow("分类：", category_combo)

        content_edit = QTextEdit(s.get("content", ""))
        layout.addRow("内容：", content_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)

        if dialog.exec():
            world_setting_manager.update_setting(setting_id, {
                "title": title_edit.text(),
                "category": category_combo.currentText(),
                "content": content_edit.toPlainText()
            })
            self.refresh()

    def delete_setting(self, setting_id: int):
        reply = QMessageBox.question(self, "确认删除", "确定要删除此设定吗？",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            world_setting_manager.delete_setting(setting_id)
            self.refresh()


class ForeshadowingPanel(QWidget):
    """伏笔和钩子追踪面板"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._project_id: Optional[int] = None
        self._memory = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QFrame()
        header.setFixedHeight(40)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(8, 4, 8, 4)

        title_label = QLabel("伏笔和钩子")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        add_btn = QToolButton()
        add_btn.setText("+伏笔")
        add_btn.setToolTip("手动添加一个伏笔或钩子")
        add_btn.clicked.connect(self.add_foreshadowing)
        header_layout.addWidget(add_btn)

        layout.addWidget(header)

        self._tab_widget = QTabWidget()

        self._active_list = QTreeWidget()
        self._active_list.setHeaderHidden(True)
        self._active_list.setIndentation(8)
        self._active_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self._active_list.customContextMenuRequested.connect(self.show_active_menu)
        self._active_list.itemDoubleClicked.connect(self.on_active_double_click)
        self._tab_widget.addTab(self._active_list, "活跃中")

        self._resolved_list = QListWidget()
        self._resolved_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self._resolved_list.customContextMenuRequested.connect(self.show_resolved_menu)
        self._tab_widget.addTab(self._resolved_list, "已解决")

        layout.addWidget(self._tab_widget)

        stats_bar = QFrame()
        stats_bar.setFixedHeight(28)
        stats_layout = QHBoxLayout(stats_bar)
        stats_layout.setContentsMargins(8, 2, 8, 2)
        self._stats_label = QLabel("活跃: 0 | 已解决: 0")
        self._stats_label.setStyleSheet("font-size: 11px; color: #888;")
        stats_layout.addWidget(self._stats_label)
        layout.addWidget(stats_bar)

    def set_project(self, project_id: int):
        self._project_id = project_id
        if project_id:
            self._memory = novel_memory_manager.get_memory(project_id)
        else:
            self._memory = None
        self.refresh()

    def refresh(self):
        self._active_list.clear()
        self._resolved_list.clear()

        if not self._memory:
            self._stats_label.setText("活跃: 0 | 已解决: 0")
            return

        active = self._memory.get_active_foreshadowings()
        resolved = self._memory.get_resolved_foreshadowings()

        cats = {}
        for fe in active:
            cat = fe.category
            if cat not in cats:
                cats[cat] = []
            cats[cat].append(fe)

        cat_names = {
            "foreshadowing": "伏笔", "hook": "钩子", "mystery": "谜团",
            "character_secret": "角色秘密", "item_clue": "物品线索", "prophecy": "预言"
        }

        for cat_key, items in cats.items():
            cat_item = QTreeWidgetItem([f"{cat_names.get(cat_key, cat_key)} ({len(items)})"])
            cat_font = QFont()
            cat_font.setBold(True)
            cat_item.setFont(0, cat_font)
            cat_item.setData(0, Qt.UserRole, ("category", cat_key))

            for fe in items:
                status_icon = "⏳" if fe.status == "active" else "🔄"
                title_text = f"{status_icon} {fe.title}"
                sub_item = QTreeWidgetItem([title_text])
                sub_item.setData(0, Qt.UserRole, ("foreshadowing", fe.id))
                sub_item.setToolTip(0, f"埋下位置: 第{fe.planted_at_chapter}章\n{fe.content[:200]}")
                cat_item.addChild(sub_item)

            self._active_list.addTopLevelItem(cat_item)

        self._active_list.expandAll()

        for fe in resolved:
            display = f"✅ {fe.title} (第{fe.resolved_at_chapter}章)"
            item = QListWidgetItem(display)
            item.setData(Qt.UserRole, fe.id)
            item.setToolTip(f"{fe.content[:150]}\n解决: {fe.resolution_note[:100]}")
            self._resolved_list.addItem(item)

        self._stats_label.setText(
            f"活跃: {len(active)} | 已解决: {len(resolved)}"
        )

    def add_foreshadowing(self):
        if not self._project_id or not self._memory:
            return
        from PySide6.QtWidgets import QDialog, QFormLayout, QLineEdit, QTextEdit, QComboBox, QDialogButtonBox
        dialog = QDialog(self)
        dialog.setWindowTitle("添加伏笔/钩子")
        dialog.setMinimumWidth(450)
        layout = QFormLayout(dialog)
        title_edit = QLineEdit()
        title_edit.setPlaceholderText("伏笔标题，如：神秘的黑衣人")
        layout.addRow("标题：", title_edit)
        category_combo = QComboBox()
        for key in FORESHADOWING_CATEGORIES.keys():
            display_name = FORESHADOWING_CATEGORIES[key].split(" - ")[0]
            category_combo.addItem(display_name, key)
        category_combo.setCurrentIndex(0)
        layout.addRow("类型：", category_combo)
        content_edit = QTextEdit()
        content_edit.setPlaceholderText("描述这个伏笔的具体内容...")
        layout.addRow("内容：", content_edit)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)
        if dialog.exec() and title_edit.text():
            self._memory.add_foreshadowing(
                title=title_edit.text(),
                content=content_edit.toPlainText() or title_edit.text(),
                category=category_combo.currentData()
            )
            self.refresh()

    def show_active_menu(self, pos):
        item = self._active_list.itemAt(pos)
        if not item:
            return
        data = item.data(0, Qt.UserRole)
        if not data or data[0] != "foreshadowing":
            return
        fe_id = data[1]
        menu = QMenu(self)
        menu.addAction("✅ 标记为已解决", lambda: self.resolve_foreshadowing(fe_id))
        menu.addAction("🔄 标记为发展中", lambda: self.set_status(fe_id, "evolving"))
        menu.addSeparator()
        menu.addAction("❌ 废弃此伏笔", lambda: self.set_status(fe_id, "abandoned"))
        menu.exec(self._active_list.mapToGlobal(pos))

    def show_resolved_menu(self, pos):
        item = self._resolved_list.itemAt(pos)
        if not item:
            return
        menu = QMenu(self)
        menu.addAction("恢复为活跃", lambda: self.set_status(item.data(Qt.UserRole), "active"))
        menu.exec(self._resolved_list.mapToGlobal(pos))

    def on_active_double_click(self, item, column):
        data = item.data(0, Qt.UserRole)
        if data and data[0] == "foreshadowing":
            self.resolve_foreshadowing(data[1])

    def resolve_foreshadowing(self, fe_id: int):
        if not self._memory:
            return
        note, ok = QInputDialog.getText(
            self, "解决伏笔", "说明如何解决的：",
            text="已在第X章中揭示"
        )
        if ok:
            self._memory.resolve_foreshadowing(fe_id, note or "已解决")
            self.refresh()

    def set_status(self, fe_id: int, status: str):
        if self._memory:
            self._memory.update_foreshadowing_status(fe_id, status)
            self.refresh()


class SidebarPanel(QWidget):
    """左侧侧边栏面板，包含大纲、人物、世界观、伏笔四个标签页"""

    chapterSelected = Signal(int, str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._tab_widget = QTabWidget()
        self._tab_widget.setTabPosition(QTabWidget.North)

        self._outline_panel = OutlinePanel()
        self._character_panel = CharacterPanel()
        self._world_panel = WorldSettingPanel()
        self._foreshadowing_panel = ForeshadowingPanel()

        self._tab_widget.addTab(self._outline_panel, "大纲")
        self._tab_widget.addTab(self._character_panel, "人物")
        self._tab_widget.addTab(self._world_panel, "世界观")
        self._tab_widget.addTab(self._foreshadowing_panel, "伏笔")

        self._outline_panel.chapterSelected.connect(self.chapterSelected.emit)

        layout.addWidget(self._tab_widget)

    def set_project(self, project_id: int):
        """设置当前项目"""
        self._outline_panel.set_project(project_id)
        self._character_panel.set_project(project_id)
        self._world_panel.set_project(project_id)
        self._foreshadowing_panel.set_project(project_id)

    def refresh(self):
        """刷新所有面板"""
        self._outline_panel.refresh()
        self._character_panel.refresh()
        self._world_panel.refresh()
        self._foreshadowing_panel.refresh()

    def outline_panel(self) -> OutlinePanel:
        return self._outline_panel

    def foreshadowing_panel(self) -> ForeshadowingPanel:
        return self._foreshadowing_panel