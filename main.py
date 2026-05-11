﻿﻿﻿#!/usr/bin/env python3
"""AI小说创作助手 - 主程序入口

基于 PySide6 的AI辅助小说创作桌面工具
支持本地大模型和云端AI API，提供专业的写作环境
"""

import sys
import os


def setup_environment():
    """设置运行环境"""
    if sys.platform == "win32":
        import ctypes
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("novelwriter.ai")
        except Exception:
            pass


def main():
    """主函数"""
    setup_environment()

    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QFont

    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("AI小说创作助手")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("NovelWriter")

    from utils.logger import logger
    from utils.config_manager import config_manager
    from models.database import db_manager
    from models.ai_provider import ai_manager
    from ui.theme_manager import theme_manager
    from ui.main_window import MainWindow

    logger.info("=" * 60)
    logger.info("AI小说创作助手 启动中...")
    logger.info("=" * 60)

    config_manager.get_all()
    logger.info("配置加载完成")

    global_font_size = config_manager.get("app.font_size", 10)
    font = QFont("Microsoft YaHei", global_font_size)
    app.setFont(font)

    db_manager.initialize()
    logger.info("数据库初始化完成")

    ai_manager.initialize()
    logger.info("AI模型初始化完成")

    theme_manager.initialize()
    logger.info("主题系统初始化完成")

    window = MainWindow()
    window.show()
    logger.info("主窗口显示完成")

    sys.exit(app.exec())


if __name__ == "__main__":
    main()