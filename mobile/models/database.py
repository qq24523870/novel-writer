import sqlite3
import os
import sys
import json
import threading
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from utils.logger import logger


class DatabaseManager:
    """数据库管理器，使用SQLite3存储所有数据"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._initialized = False
            self._db_path = ""
            self._conn = None
            self._local = threading.local()

    def _get_connection(self) -> sqlite3.Connection:
        """获取当前线程的数据库连接"""
        if not hasattr(self._local, 'conn') or self._local.conn is None:
            self._local.conn = sqlite3.connect(self._db_path, check_same_thread=False)
            self._local.conn.row_factory = sqlite3.Row
            self._local.conn.execute("PRAGMA journal_mode=WAL")
            self._local.conn.execute("PRAGMA foreign_keys=ON")
        return self._local.conn

    def initialize(self, db_path: str = ""):
        """初始化数据库

        Args:
            db_path: 数据库文件路径，为空则使用默认路径
        """
        if self._initialized:
            return

        if not db_path:
            if getattr(sys, "frozen", False):
                app_base = os.path.dirname(sys.executable)
            else:
                app_base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                if os.path.basename(app_base) == "mobile":
                    app_base = os.path.dirname(app_base)
            app_dir = os.path.join(app_base, "data")
            os.makedirs(app_dir, exist_ok=True)
            db_path = os.path.join(app_dir, "novel_writer.db")

        self._db_path = db_path
        self._create_tables()
        self._initialized = True
        logger.info(f"数据库初始化完成: {db_path}")

    def _create_tables(self):
        """创建所有数据库表"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.executescript("""
            -- 小说项目表
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                author TEXT DEFAULT '',
                genre TEXT DEFAULT '',
                description TEXT DEFAULT '',
                word_goal INTEGER DEFAULT 0,
                cover_path TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_deleted INTEGER DEFAULT 0,
                deleted_at TIMESTAMP
            );

            -- 卷表
            CREATE TABLE IF NOT EXISTS volumes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                sort_order INTEGER DEFAULT 0,
                description TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_deleted INTEGER DEFAULT 0,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
            );

            -- 章节表
            CREATE TABLE IF NOT EXISTS chapters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                volume_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                content TEXT DEFAULT '',
                word_count INTEGER DEFAULT 0,
                sort_order INTEGER DEFAULT 0,
                status TEXT DEFAULT 'draft',
                notes TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_deleted INTEGER DEFAULT 0,
                deleted_at TIMESTAMP,
                FOREIGN KEY (volume_id) REFERENCES volumes(id) ON DELETE CASCADE
            );

            -- 人物卡片表
            CREATE TABLE IF NOT EXISTS characters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                gender TEXT DEFAULT '',
                age TEXT DEFAULT '',
                appearance TEXT DEFAULT '',
                personality TEXT DEFAULT '',
                background TEXT DEFAULT '',
                catchphrase TEXT DEFAULT '',
                relationships TEXT DEFAULT '[]',
                avatar_path TEXT DEFAULT '',
                notes TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_deleted INTEGER DEFAULT 0,
                deleted_at TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
            );

            -- 世界观设定表
            CREATE TABLE IF NOT EXISTS world_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                category TEXT NOT NULL,
                title TEXT NOT NULL,
                content TEXT DEFAULT '',
                tags TEXT DEFAULT '[]',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_deleted INTEGER DEFAULT 0,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
            );

            -- 时间线事件表
            CREATE TABLE IF NOT EXISTS timeline_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                event_date TEXT DEFAULT '',
                sort_order INTEGER DEFAULT 0,
                chapter_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
                FOREIGN KEY (chapter_id) REFERENCES chapters(id) ON DELETE SET NULL
            );

            -- AI对话记录表
            CREATE TABLE IF NOT EXISTS ai_conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                model_used TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- 写作统计表
            CREATE TABLE IF NOT EXISTS writing_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                word_count INTEGER DEFAULT 0,
                writing_time INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
            );

            -- 回收站表
            CREATE TABLE IF NOT EXISTS recycle_bin (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_table TEXT NOT NULL,
                original_id INTEGER NOT NULL,
                data TEXT NOT NULL,
                deleted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- 敏感词表
            CREATE TABLE IF NOT EXISTS sensitive_words (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                word TEXT NOT NULL UNIQUE,
                category TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- 创建索引
            CREATE INDEX IF NOT EXISTS idx_volumes_project ON volumes(project_id);
            CREATE INDEX IF NOT EXISTS idx_chapters_volume ON chapters(volume_id);
            CREATE INDEX IF NOT EXISTS idx_characters_project ON characters(project_id);
            CREATE INDEX IF NOT EXISTS idx_world_settings_project ON world_settings(project_id);
            CREATE INDEX IF NOT EXISTS idx_timeline_project ON timeline_events(project_id);
            CREATE INDEX IF NOT EXISTS idx_writing_stats_project ON writing_stats(project_id);
            CREATE INDEX IF NOT EXISTS idx_writing_stats_date ON writing_stats(date);

            -- 伏笔和钩子表
            CREATE TABLE IF NOT EXISTS foreshadowings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                chapter_id INTEGER,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                category TEXT DEFAULT 'foreshadowing',
                status TEXT DEFAULT 'active',
                planted_at_chapter INTEGER DEFAULT 0,
                resolved_at_chapter INTEGER DEFAULT 0,
                resolution_note TEXT DEFAULT '',
                tags TEXT DEFAULT '[]',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
            );

            -- 章节记忆压缩表
            CREATE TABLE IF NOT EXISTS chapter_memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                chapter_id INTEGER NOT NULL,
                volume_id INTEGER NOT NULL,
                summary TEXT DEFAULT '',
                key_events TEXT DEFAULT '[]',
                new_characters TEXT DEFAULT '[]',
                active_foreshadowing_ids TEXT DEFAULT '[]',
                word_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
                FOREIGN KEY (chapter_id) REFERENCES chapters(id) ON DELETE CASCADE
            );

            -- 卷记忆压缩表
            CREATE TABLE IF NOT EXISTS volume_memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                volume_id INTEGER NOT NULL,
                summary TEXT DEFAULT '',
                arc_progression TEXT DEFAULT '',
                character_arcs TEXT DEFAULT '[]',
                resolved_foreshadowing_ids TEXT DEFAULT '[]',
                active_foreshadowing_ids TEXT DEFAULT '[]',
                word_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
                FOREIGN KEY (volume_id) REFERENCES volumes(id) ON DELETE CASCADE
            );

            -- 情节弧线表
            CREATE TABLE IF NOT EXISTS plot_arcs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                start_chapter_id INTEGER,
                end_chapter_id INTEGER,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_foreshadowings_project ON foreshadowings(project_id);
            CREATE INDEX IF NOT EXISTS idx_foreshadowings_status ON foreshadowings(status);
            CREATE INDEX IF NOT EXISTS idx_chapter_memories_project ON chapter_memories(project_id);
            CREATE INDEX IF NOT EXISTS idx_volume_memories_project ON volume_memories(project_id);
            CREATE INDEX IF NOT EXISTS idx_plot_arcs_project ON plot_arcs(project_id);
        """)

        conn.commit()

    def execute(self, query: str, params: Tuple = ()) -> sqlite3.Cursor:
        """执行SQL语句

        Args:
            query: SQL语句
            params: 参数

        Returns:
            sqlite3.Cursor
        """
        conn = self._get_connection()
        try:
            cursor = conn.execute(query, params)
            conn.commit()
            return cursor
        except Exception as e:
            logger.error(f"数据库执行错误: {query[:50]}... 错误: {e}")
            raise

    def fetch_one(self, query: str, params: Tuple = ()) -> Optional[Dict]:
        """查询单条记录

        Args:
            query: SQL语句
            params: 参数

        Returns:
            字典形式的记录，或None
        """
        cursor = self.execute(query, params)
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None

    def fetch_all(self, query: str, params: Tuple = ()) -> List[Dict]:
        """查询多条记录

        Args:
            query: SQL语句
            params: 参数

        Returns:
            字典列表
        """
        cursor = self.execute(query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def insert(self, table: str, data: Dict) -> int:
        """插入记录

        Args:
            table: 表名
            data: 数据字典

        Returns:
            新记录的ID
        """
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["?"] * len(data))
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        cursor = self.execute(query, tuple(data.values()))
        return cursor.lastrowid

    def update(self, table: str, data: Dict, where: str, params: Tuple = ()):
        """更新记录

        Args:
            table: 表名
            data: 要更新的数据字典
            where: WHERE条件
            params: WHERE参数
        """
        set_clause = ", ".join([f"{k} = ?" for k in data.keys()])
        query = f"UPDATE {table} SET {set_clause} WHERE {where}"
        all_params = tuple(data.values()) + params
        self.execute(query, all_params)

    def delete(self, table: str, where: str, params: Tuple = ()):
        """删除记录

        Args:
            table: 表名
            where: WHERE条件
            params: WHERE参数
        """
        query = f"DELETE FROM {table} WHERE {where}"
        self.execute(query, params)

    def move_to_recycle_bin(self, table: str, record_id: int):
        """将记录移入回收站

        Args:
            table: 原表名
            record_id: 记录ID
        """
        row = self.fetch_one(f"SELECT * FROM {table} WHERE id = ?", (record_id,))
        if row:
            data_json = json.dumps(row, ensure_ascii=False)
            self.insert("recycle_bin", {
                "original_table": table,
                "original_id": record_id,
                "data": data_json
            })
            self.update(table, {"is_deleted": 1, "deleted_at": datetime.now().isoformat()},
                       "id = ?", (record_id,))

    def restore_from_recycle_bin(self, recycle_id: int):
        """从回收站恢复记录

        Args:
            recycle_id: 回收站记录ID
        """
        recycle_item = self.fetch_one("SELECT * FROM recycle_bin WHERE id = ?", (recycle_id,))
        if recycle_item:
            data = json.loads(recycle_item["data"])
            data["is_deleted"] = 0
            data["deleted_at"] = None
            self.update(recycle_item["original_table"], data, "id = ?", (recycle_item["original_id"],))
            self.delete("recycle_bin", "id = ?", (recycle_id,))

    def close(self):
        """关闭数据库连接"""
        if hasattr(self._local, 'conn') and self._local.conn:
            self._local.conn.close()
            self._local.conn = None


db_manager = DatabaseManager()