# -*- coding: utf-8 -*-
"""AI小说创作助手 - 主程序入口

基于 PySide6 的AI辅助小说创作桌面工具
支持本地大模型和云端AI API，提供专业的写作环境
"""
import sys
import os

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow
from utils.config_manager import config_manager
from utils.logger import logger
from models.database import db_manager
from models.ai_provider import ai_manager
from ui.theme_manager import theme_manager


def main():
    try:
        db_manager.initialize()
        ai_manager.initialize()
    except Exception as e:
        logger.error(f"初始化失败: {e}")

    app = QApplication(sys.argv)
    app.setApplicationName("AI小说创作助手")
    app.setOrganizationName("QingYi")

    theme_manager.apply_theme(app)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
