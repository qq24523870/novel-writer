import os
import shutil
import threading
import zipfile
from datetime import datetime
from typing import Callable, Optional
from utils.logger import logger
from utils.config_manager import config_manager


class BackupManager:
    """备份管理器，支持手动和自动备份"""

    @staticmethod
    def get_backup_dir() -> str:
        """获取备份目录"""
        backup_dir = config_manager.get("writing.backup_dir", "")
        if not backup_dir:
            backup_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "data", "backups"
            )
        os.makedirs(backup_dir, exist_ok=True)
        return backup_dir

    @staticmethod
    def create_backup(db_path: str, on_complete: Callable[[bool, str], None] = None):
        """创建备份

        Args:
            db_path: 数据库文件路径
            on_complete: 完成回调 (success, backup_path)
        """
        def _run():
            try:
                backup_dir = BackupManager.get_backup_dir()
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_name = f"novel_writer_backup_{timestamp}.zip"
                backup_path = os.path.join(backup_dir, backup_name)

                with zipfile.ZipFile(backup_path, "w", zipfile.ZIP_DEFLATED) as zf:
                    zf.write(db_path, os.path.basename(db_path))

                config_path = os.path.join(
                    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "config", "config.json"
                )
                if os.path.exists(config_path):
                    zf.write(config_path, "config.json")

                logger.info(f"备份创建成功: {backup_path}")
                if on_complete:
                    on_complete(True, backup_path)
            except Exception as e:
                logger.error(f"备份创建失败: {e}")
                if on_complete:
                    on_complete(False, str(e))

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()

    @staticmethod
    def restore_backup(backup_path: str, restore_dir: str,
                       on_complete: Callable[[bool, str], None] = None):
        """从备份恢复

        Args:
            backup_path: 备份文件路径
            restore_dir: 恢复目录
            on_complete: 完成回调
        """
        def _run():
            try:
                os.makedirs(restore_dir, exist_ok=True)
                with zipfile.ZipFile(backup_path, "r") as zf:
                    zf.extractall(restore_dir)
                logger.info(f"从备份恢复成功: {backup_path}")
                if on_complete:
                    on_complete(True, restore_dir)
            except Exception as e:
                logger.error(f"从备份恢复失败: {e}")
                if on_complete:
                    on_complete(False, str(e))

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()

    @staticmethod
    def list_backups() -> list:
        """列出所有备份文件"""
        backup_dir = BackupManager.get_backup_dir()
        if not os.path.exists(backup_dir):
            return []

        backups = []
        for f in os.listdir(backup_dir):
            if f.endswith(".zip") and f.startswith("novel_writer_backup"):
                file_path = os.path.join(backup_dir, f)
                size = os.path.getsize(file_path)
                mtime = os.path.getmtime(file_path)
                backups.append({
                    "name": f,
                    "path": file_path,
                    "size": size,
                    "created_at": datetime.fromtimestamp(mtime).isoformat()
                })

        backups.sort(key=lambda x: x["created_at"], reverse=True)
        return backups

    @staticmethod
    def delete_backup(backup_path: str) -> bool:
        """删除备份文件"""
        try:
            if os.path.exists(backup_path):
                os.remove(backup_path)
                logger.info(f"删除备份: {backup_path}")
                return True
        except Exception as e:
            logger.error(f"删除备份失败: {e}")
        return False


backup_manager = BackupManager()