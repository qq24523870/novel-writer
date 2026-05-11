from typing import Dict, Optional
from PySide6.QtGui import QColor, QPalette
from utils.config_manager import config_manager


class ThemeManager:
    """主题管理器，管理应用的主题切换和颜色方案"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._initialized = False
            self._current_theme = "light"
            self._themes: Dict = {}

    def initialize(self):
        """初始化主题管理器"""
        themes_config = config_manager.get("theme.themes", {})
        self._themes = themes_config
        self._current_theme = config_manager.get("theme.current", "light")
        self._initialized = True

    def get_theme_names(self) -> list:
        """获取所有主题名称"""
        return list(self._themes.keys())

    def get_current_theme_name(self) -> str:
        """获取当前主题名称"""
        return self._current_theme

    def get_theme_colors(self, theme_name: str = "") -> Dict:
        """获取主题颜色配置

        Args:
            theme_name: 主题名称，为空则返回当前主题

        Returns:
            颜色配置字典
        """
        if not theme_name:
            theme_name = self._current_theme
        return self._themes.get(theme_name, self._themes.get("light", {}))

    def get_color(self, color_key: str, theme_name: str = "") -> str:
        """获取指定颜色值

        Args:
            color_key: 颜色键名
            theme_name: 主题名称

        Returns:
            颜色十六进制值
        """
        colors = self.get_theme_colors(theme_name)
        return colors.get(color_key, "#000000")

    def switch_to(self, theme_name: str):
        """切换到指定主题

        Args:
            theme_name: 主题名称
        """
        if theme_name in self._themes:
            self._current_theme = theme_name
            config_manager.set("theme.current", theme_name)

    def get_stylesheet(self, theme_name: str = "") -> str:
        """生成主题对应的QSS样式表

        Args:
            theme_name: 主题名称

        Returns:
            QSS样式表字符串
        """
        colors = self.get_theme_colors(theme_name)

        return f"""
        /* 全局样式 */
        QMainWindow, QDialog, QWidget {{
            background-color: {colors.get('bg_primary', '#FFFFFF')};
            color: {colors.get('text_primary', '#333333')};
            font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
        }}

        /* 输入框联动高亮 */
        QLineEdit:hover, QTextEdit:hover, QPlainTextEdit:hover {{
            border-color: {colors.get('accent', '#4A90D9')};
        }}

        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
            border-color: {colors.get('accent', '#4A90D9')};
        }}

        QMenuBar {{
            background-color: {colors.get('bg_secondary', '#F5F5F5')};
            color: {colors.get('text_primary', '#333333')};
            border-bottom: 1px solid {colors.get('border', '#DCDCDC')};
            padding: 3px;
            font-size: 13px;
        }}

        QMenuBar::item {{
            padding: 4px 10px;
            border-radius: 4px;
        }}

        QMenuBar::item:selected {{
            background-color: {colors.get('accent', '#4A90D9')};
            color: white;
            border-radius: 4px;
        }}

        QMenu {{
            background-color: {colors.get('bg_primary', '#FFFFFF')};
            color: {colors.get('text_primary', '#333333')};
            border: 1px solid {colors.get('border', '#DCDCDC')};
            border-radius: 6px;
            padding: 4px;
        }}

        QMenu::item {{
            padding: 6px 28px 6px 12px;
            border-radius: 4px;
        }}

        QMenu::item:selected {{
            background-color: {colors.get('accent', '#4A90D9')};
            color: white;
        }}

        QToolBar {{
            background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {colors.get('bg_secondary', '#F5F5F5')},
                stop:1 {colors.get('bg_primary', '#FFFFFF')});
            border-bottom: 1px solid {colors.get('border', '#DCDCDC')};
            spacing: 4px;
            padding: 4px 8px;
        }}

        QToolButton {{
            background-color: transparent;
            color: {colors.get('text_primary', '#333333')};
            border: 1px solid transparent;
            border-radius: 6px;
            padding: 6px 10px;
            min-width: 30px;
            min-height: 30px;
        }}

        QToolButton:hover {{
            background-color: {colors.get('bg_tertiary', '#E8E8E8')};
            border-color: {colors.get('border', '#DCDCDC')};
        }}

        QToolButton:pressed {{
            background-color: {colors.get('accent', '#4A90D9')};
            color: white;
        }}

        QToolButton:checked {{
            background-color: {colors.get('accent', '#4A90D9')};
            color: white;
        }}

        QPushButton {{
            background-color: {colors.get('accent', '#4A90D9')};
            color: white;
            border: none;
            border-radius: 6px;
            padding: 8px 20px;
            min-height: 32px;
            font-size: 13px;
            font-weight: 500;
        }}

        QPushButton:hover {{
            background-color: {colors.get('accent_hover', '#357ABD')};
        }}

        QPushButton:pressed {{
            background-color: {colors.get('accent_hover', '#357ABD')};
        }}

        QPushButton:disabled {{
            background-color: {colors.get('bg_tertiary', '#E8E8E8')};
            color: {colors.get('text_tertiary', '#999999')};
        }}

        QLineEdit, QTextEdit, QPlainTextEdit {{
            background-color: {colors.get('editor_bg', '#FFFFFF')};
            color: {colors.get('editor_text', '#333333')};
            border: 1px solid {colors.get('border', '#DCDCDC')};
            border-radius: 6px;
            padding: 6px 10px;
            selection-background-color: {colors.get('editor_selection', '#D0E4F5')};
        }}

        QComboBox {{
            background-color: {colors.get('bg_primary', '#FFFFFF')};
            color: {colors.get('text_primary', '#333333')};
            border: 1px solid {colors.get('border', '#DCDCDC')};
            border-radius: 6px;
            padding: 6px 10px;
            min-height: 32px;
        }}

        QComboBox:hover {{
            border-color: {colors.get('accent', '#4A90D9')};
        }}

        QComboBox::drop-down {{
            border: none;
            width: 28px;
            border-top-right-radius: 6px;
            border-bottom-right-radius: 6px;
        }}

        QComboBox QAbstractItemView {{
            background-color: {colors.get('bg_primary', '#FFFFFF')};
            color: {colors.get('text_primary', '#333333')};
            border: 1px solid {colors.get('border', '#DCDCDC')};
            border-radius: 6px;
            padding: 4px;
            selection-background-color: {colors.get('accent', '#4A90D9')};
            selection-color: white;
        }}

        QTreeWidget, QListWidget, QTableWidget {{
            background-color: {colors.get('sidebar_bg', colors.get('bg_primary', '#FFFFFF'))};
            color: {colors.get('sidebar_text', colors.get('text_primary', '#333333'))};
            border: 1px solid {colors.get('border', '#DCDCDC')};
            border-radius: 6px;
            outline: none;
            padding: 2px;
        }}

        QTreeWidget::item, QListWidget::item {{
            padding: 6px 10px;
            min-height: 28px;
            border-radius: 4px;
        }}

        QTreeWidget::item:selected, QListWidget::item:selected {{
            background-color: {colors.get('accent', '#4A90D9')};
            color: white;
        }}

        QTreeWidget::item:hover, QListWidget::item:hover {{
            background-color: {colors.get('bg_tertiary', '#E8E8E8')};
        }}

        QHeaderView::section {{
            background-color: {colors.get('panel_header', '#F0F2F5')};
            color: {colors.get('text_primary', '#333333')};
            border: 1px solid {colors.get('border', '#DCDCDC')};
            border-radius: 4px;
            padding: 6px 10px;
            font-weight: bold;
        }}

        QTabWidget::pane {{
            background-color: {colors.get('bg_primary', '#FFFFFF')};
            border: 1px solid {colors.get('border', '#DCDCDC')};
            border-top: none;
            border-radius: 0 0 6px 6px;
        }}

        QTabBar::tab {{
            background-color: {colors.get('bg_secondary', '#F5F5F5')};
            color: {colors.get('text_secondary', '#666666')};
            border: 1px solid {colors.get('border', '#DCDCDC')};
            border-bottom: none;
            padding: 8px 18px;
            margin-right: 2px;
            border-top-left-radius: 6px;
            border-top-right-radius: 6px;
            font-size: 13px;
        }}

        QTabBar::tab:selected {{
            background-color: {colors.get('bg_primary', '#FFFFFF')};
            color: {colors.get('accent', '#4A90D9')};
            border-bottom: 2px solid {colors.get('accent', '#4A90D9')};
            font-weight: bold;
        }}

        QTabBar::tab:hover {{
            background-color: {colors.get('bg_tertiary', '#E8E8E8')};
        }}

        QScrollBar:vertical {{
            background-color: transparent;
            width: 8px;
            border: none;
            margin: 2px;
        }}

        QScrollBar::handle:vertical {{
            background-color: {colors.get('scrollbar', '#C0C0C0')};
            border-radius: 4px;
            min-height: 30px;
        }}

        QScrollBar::handle:vertical:hover {{
            background-color: {colors.get('scrollbar_hover', '#A0A0A0')};
        }}

        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}

        QScrollBar:horizontal {{
            background-color: transparent;
            height: 8px;
            border: none;
            margin: 2px;
        }}

        QScrollBar::handle:horizontal {{
            background-color: {colors.get('scrollbar', '#C0C0C0')};
            border-radius: 4px;
            min-width: 30px;
        }}

        QScrollBar::handle:horizontal:hover {{
            background-color: {colors.get('scrollbar_hover', '#A0A0A0')};
        }}

        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            width: 0px;
        }}

        QSplitter::handle {{
            background-color: {colors.get('border', '#DCDCDC')};
            width: 2px;
        }}

        QSplitter::handle:hover {{
            background-color: {colors.get('accent', '#4A90D9')};
        }}

        QStatusBar {{
            background-color: {colors.get('bg_secondary', '#F5F5F5')};
            color: {colors.get('text_secondary', '#666666')};
            border-top: 1px solid {colors.get('border', '#DCDCDC')};
            font-size: 12px;
            padding: 2px 8px;
        }}

        QStatusBar::item {{
            border: none;
        }}

        QStatusBar QLabel {{
            padding: 0 6px;
        }}

        QStatusBar QLabel[devMode="true"] {{
            color: {colors.get('warning', '#FAAD14')};
            font-weight: bold;
        }}

        QLabel {{
            color: {colors.get('text_primary', '#333333')};
        }}

        QCheckBox {{
            color: {colors.get('text_primary', '#333333')};
            spacing: 8px;
        }}

        QCheckBox::indicator {{
            width: 18px;
            height: 18px;
            border: 2px solid {colors.get('border', '#DCDCDC')};
            border-radius: 4px;
        }}

        QCheckBox::indicator:checked {{
            background-color: {colors.get('accent', '#4A90D9')};
            border-color: {colors.get('accent', '#4A90D9')};
        }}

        QRadioButton {{
            color: {colors.get('text_primary', '#333333')};
            spacing: 8px;
        }}

        QGroupBox {{
            border: 1px solid {colors.get('border', '#DCDCDC')};
            border-radius: 8px;
            margin-top: 16px;
            padding-top: 18px;
            font-weight: bold;
        }}

        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 14px;
            padding: 0 8px;
            color: {colors.get('accent', '#4A90D9')};
        }}

        QProgressBar {{
            background-color: {colors.get('bg_tertiary', '#E8E8E8')};
            border: none;
            border-radius: 6px;
            height: 12px;
            text-align: center;
        }}

        QProgressBar::chunk {{
            background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {colors.get('accent', '#4A90D9')},
                stop:1 {colors.get('success', '#52C41A')});
            border-radius: 6px;
        }}

        QDialog {{
            background-color: {colors.get('bg_primary', '#FFFFFF')};
        }}

        QSpinBox, QDoubleSpinBox {{
            background-color: {colors.get('bg_primary', '#FFFFFF')};
            color: {colors.get('text_primary', '#333333')};
            border: 1px solid {colors.get('border', '#DCDCDC')};
            border-radius: 6px;
            padding: 6px;
            min-height: 32px;
        }}

        QSpinBox:hover, QDoubleSpinBox:hover {{
            border-color: {colors.get('accent', '#4A90D9')};
        }}
        """


theme_manager = ThemeManager()