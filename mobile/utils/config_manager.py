import json
import os
import sys
import shutil
from typing import Any, Dict, Optional
from utils.logger import logger


class ConfigManager:
    """全局配置管理器，负责读取、保存和更新配置"""

    _instance = None
    _config: Dict[str, Any] = {}
    _config_path: str = ""

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._config:
            self._load_config()

    def _load_config(self):
        """加载配置文件，如果不存在则从默认配置创建"""
        app_dir = self._get_app_dir()
        self._config_path = os.path.join(app_dir, "config.json")

        default_config_path = self._get_default_config_path()

        if not os.path.exists(self._config_path):
            os.makedirs(app_dir, exist_ok=True)
            if os.path.exists(default_config_path):
                shutil.copy(default_config_path, self._config_path)
                logger.info(f"从默认配置创建配置文件: {self._config_path}")
            else:
                self._config = {}
                return

        try:
            with open(self._config_path, "r", encoding="utf-8") as f:
                self._config = json.load(f)
            logger.info(f"配置文件加载成功: {self._config_path}")
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            self._config = {}

    def _get_app_dir(self) -> str:
        """获取应用程序数据目录"""
        if getattr(sys, "frozen", False):
            app_base = os.path.dirname(sys.executable)
        else:
            app_base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if os.path.basename(app_base) == "mobile":
                app_base = os.path.dirname(app_base)
        return os.path.join(app_base, "data")

    def _get_default_config_path(self) -> str:
        """获取默认配置文件路径（兼容开发和PyInstaller打包）"""
        meipass = getattr(sys, "_MEIPASS", "")
        if meipass:
            candidate = os.path.join(meipass, "config", "default_config.json")
            if os.path.exists(candidate):
                return candidate

        candidate = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "config", "default_config.json"
        )
        return candidate

    def save(self):
        """保存配置到文件"""
        try:
            os.makedirs(os.path.dirname(self._config_path), exist_ok=True)
            with open(self._config_path, "w", encoding="utf-8") as f:
                json.dump(self._config, f, ensure_ascii=False, indent=4)
            logger.info("配置保存成功")
        except Exception as e:
            logger.error(f"保存配置失败: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值，支持点号分隔的嵌套键

        Args:
            key: 配置键，如 "editor.font_size"
            default: 默认值
        """
        keys = key.split(".")
        value = self._config
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def set(self, key: str, value: Any):
        """设置配置值，支持点号分隔的嵌套键"""
        keys = key.split(".")
        config = self._config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
        self.save()

    def get_all(self) -> Dict[str, Any]:
        """获取完整配置"""
        return self._config

    def reset_to_default(self):
        """重置为默认配置"""
        default_config_path = self._get_default_config_path()
        if os.path.exists(default_config_path):
            with open(default_config_path, "r", encoding="utf-8") as f:
                self._config = json.load(f)
            self.save()
            logger.info("配置已重置为默认值")


config_manager = ConfigManager()