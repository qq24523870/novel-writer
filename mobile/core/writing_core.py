import threading
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
from models.database import db_manager
from utils.logger import logger
from utils.text_processor import text_processor
from core.novel_memory import novel_memory_manager


class ProjectManager:
    """项目管理器，处理小说项目的CRUD操作"""

    def __init__(self):
        self._current_project_id: Optional[int] = None
        self._listeners: List[Callable] = []

    def add_listener(self, callback: Callable):
        """添加项目变更监听器"""
        self._listeners.append(callback)

    def _notify_listeners(self, event: str, data: Any = None):
        """通知所有监听器"""
        for callback in self._listeners:
            try:
                callback(event, data)
            except Exception as e:
                logger.error(f"监听器回调失败: {e}")

    def create_project(self, name: str, author: str = "", genre: str = "",
                       description: str = "", word_goal: int = 0) -> int:
        """创建新项目

        Args:
            name: 小说名称
            author: 作者
            genre: 类型
            description: 简介
            word_goal: 字数目标

        Returns:
            项目ID
        """
        project_id = db_manager.insert("projects", {
            "name": name,
            "author": author,
            "genre": genre,
            "description": description,
            "word_goal": word_goal
        })

        default_volume_id = db_manager.insert("volumes", {
            "project_id": project_id,
            "title": "第一卷",
            "sort_order": 0,
            "description": "默认卷"
        })

        db_manager.insert("chapters", {
            "volume_id": default_volume_id,
            "title": "第一章",
            "content": "",
            "sort_order": 0,
            "word_count": 0
        })

        self._notify_listeners("project_created", {"id": project_id, "name": name})
        logger.info(f"创建项目: {name} (ID: {project_id})")
        return project_id

    def open_project(self, project_id: int):
        """打开项目

        Args:
            project_id: 项目ID
        """
        self._current_project_id = project_id
        self._notify_listeners("project_opened", {"id": project_id})
        logger.info(f"打开项目 ID: {project_id}")

    def close_project(self):
        """关闭当前项目"""
        if self._current_project_id:
            self._notify_listeners("project_closed", {"id": self._current_project_id})
            self._current_project_id = None

    def get_current_project_id(self) -> Optional[int]:
        """获取当前项目ID"""
        return self._current_project_id

    def get_project(self, project_id: int) -> Optional[Dict]:
        """获取项目信息"""
        return db_manager.fetch_one(
            "SELECT * FROM projects WHERE id = ? AND is_deleted = 0",
            (project_id,)
        )

    def get_all_projects(self) -> List[Dict]:
        """获取所有项目"""
        return db_manager.fetch_all(
            "SELECT * FROM projects WHERE is_deleted = 0 ORDER BY updated_at DESC"
        )

    def update_project(self, project_id: int, data: Dict):
        """更新项目信息"""
        data["updated_at"] = datetime.now().isoformat()
        db_manager.update("projects", data, "id = ?", (project_id,))
        self._notify_listeners("project_updated", {"id": project_id})

    def delete_project(self, project_id: int):
        """删除项目（移入回收站）"""
        db_manager.move_to_recycle_bin("projects", project_id)
        self._notify_listeners("project_deleted", {"id": project_id})

    def get_project_word_count(self, project_id: int) -> int:
        """获取项目总字数"""
        result = db_manager.fetch_one(
            """SELECT COALESCE(SUM(word_count), 0) as total
               FROM chapters WHERE volume_id IN
               (SELECT id FROM volumes WHERE project_id = ? AND is_deleted = 0)
               AND is_deleted = 0""",
            (project_id,)
        )
        return result["total"] if result else 0


class VolumeManager:
    """卷管理器"""

    def get_volumes(self, project_id: int) -> List[Dict]:
        """获取项目的所有卷"""
        return db_manager.fetch_all(
            "SELECT * FROM volumes WHERE project_id = ? AND is_deleted = 0 ORDER BY sort_order",
            (project_id,)
        )

    def create_volume(self, project_id: int, title: str, description: str = "") -> int:
        """创建新卷"""
        max_order = db_manager.fetch_one(
            "SELECT COALESCE(MAX(sort_order), -1) as max_order FROM volumes WHERE project_id = ?",
            (project_id,)
        )
        sort_order = (max_order["max_order"] if max_order else -1) + 1
        return db_manager.insert("volumes", {
            "project_id": project_id,
            "title": title,
            "sort_order": sort_order,
            "description": description
        })

    def update_volume(self, volume_id: int, data: Dict):
        """更新卷信息"""
        data["updated_at"] = datetime.now().isoformat()
        db_manager.update("volumes", data, "id = ?", (volume_id,))

    def delete_volume(self, volume_id: int):
        """删除卷"""
        db_manager.move_to_recycle_bin("volumes", volume_id)

    def reorder_volumes(self, volume_ids: List[int]):
        """重新排序卷"""
        for index, vid in enumerate(volume_ids):
            db_manager.update("volumes", {"sort_order": index}, "id = ?", (vid,))


class ChapterManager:
    """章节管理器"""

    def get_chapters(self, volume_id: int) -> List[Dict]:
        """获取卷的所有章节"""
        return db_manager.fetch_all(
            "SELECT * FROM chapters WHERE volume_id = ? AND is_deleted = 0 ORDER BY sort_order",
            (volume_id,)
        )

    def get_all_chapters_for_project(self, project_id: int) -> List[Dict]:
        """获取项目所有卷的全部章节（按卷序、章序排列）"""
        volumes = volume_manager.get_volumes(project_id)
        all_chapters = []
        for vol in volumes:
            chapters = self.get_chapters(vol["id"])
            for ch in chapters:
                ch["_volume_title"] = vol["title"]
                all_chapters.append(ch)
        return all_chapters

    def get_chapter(self, chapter_id: int) -> Optional[Dict]:
        """获取单个章节"""
        return db_manager.fetch_one(
            "SELECT * FROM chapters WHERE id = ? AND is_deleted = 0",
            (chapter_id,)
        )

    def create_chapter(self, volume_id: int, title: str = "") -> int:
        """创建新章节"""
        max_order = db_manager.fetch_one(
            "SELECT COALESCE(MAX(sort_order), -1) as max_order FROM chapters WHERE volume_id = ?",
            (volume_id,)
        )
        sort_order = (max_order["max_order"] if max_order else -1) + 1
        if not title:
            title = f"第{sort_order + 1}章"
        return db_manager.insert("chapters", {
            "volume_id": volume_id,
            "title": title,
            "content": "",
            "sort_order": sort_order,
            "word_count": 0
        })

    def save_chapter(self, chapter_id: int, content: str, title: str = ""):
        """保存章节内容"""
        word_count = text_processor.count_words(content)
        data = {
            "content": content,
            "word_count": word_count,
            "updated_at": datetime.now().isoformat()
        }
        if title:
            data["title"] = title
        db_manager.update("chapters", data, "id = ?", (chapter_id,))

        chapter = db_manager.fetch_one(
            "SELECT * FROM chapters WHERE id = ?", (chapter_id,)
        )
        if chapter:
            volume = db_manager.fetch_one(
                "SELECT project_id FROM volumes WHERE id = ?",
                (chapter["volume_id"],)
            )
            if volume:
                project_id = volume["project_id"]
                memory = novel_memory_manager.get_memory(project_id)
                memory.compress_chapter(
                    chapter_id=chapter_id,
                    volume_id=chapter["volume_id"],
                    title=title or chapter["title"],
                    content=content
                )
                self._check_volume_complete(chapter["volume_id"], project_id)

    def update_chapter(self, chapter_id: int, data: Dict):
        """更新章节信息"""
        data["updated_at"] = datetime.now().isoformat()
        db_manager.update("chapters", data, "id = ?", (chapter_id,))

    def delete_chapter(self, chapter_id: int):
        """删除章节"""
        db_manager.move_to_recycle_bin("chapters", chapter_id)

    def reorder_chapters(self, chapter_ids: List[int]):
        """重新排序章节"""
        for index, cid in enumerate(chapter_ids):
            db_manager.update("chapters", {"sort_order": index}, "id = ?", (cid,))

    def _check_volume_complete(self, volume_id: int, project_id: int):
        """检查卷是否已完成，完成则触发卷级压缩"""
        chapters = self.get_chapters(volume_id)
        completed = all(
            ch.get("status") == "published" or
            (ch.get("content") and text_processor.count_words(ch.get("content", "")) > 100)
            for ch in chapters
        )
        if completed and chapters:
            volume = db_manager.fetch_one(
                "SELECT title FROM volumes WHERE id = ?", (volume_id,)
            )
            if volume:
                memory = novel_memory_manager.get_memory(project_id)
                memory.compress_volume(volume_id, volume["title"])

    def merge_chapters(self, chapter_ids: List[int], new_title: str = "") -> int:
        """合并多个章节

        Args:
            chapter_ids: 要合并的章节ID列表
            new_title: 新章节标题

        Returns:
            新章节ID
        """
        chapters = []
        for cid in chapter_ids:
            chapter = self.get_chapter(cid)
            if chapter:
                chapters.append(chapter)

        if not chapters:
            return 0

        merged_content = "\n\n".join([c["content"] for c in chapters])
        first_chapter = chapters[0]

        if not new_title:
            new_title = first_chapter["title"]

        volume_id = first_chapter["volume_id"]
        new_id = self.create_chapter(volume_id, new_title)
        self.save_chapter(new_id, merged_content)

        for c in chapters:
            self.delete_chapter(c["id"])

        return new_id


class CharacterManager:
    """人物卡片管理器"""

    def get_characters(self, project_id: int) -> List[Dict]:
        """获取项目的所有人物卡片"""
        return db_manager.fetch_all(
            "SELECT * FROM characters WHERE project_id = ? AND is_deleted = 0 ORDER BY created_at",
            (project_id,)
        )

    def get_character(self, character_id: int) -> Optional[Dict]:
        """获取单个人物卡片"""
        return db_manager.fetch_one(
            "SELECT * FROM characters WHERE id = ? AND is_deleted = 0",
            (character_id,)
        )

    def create_character(self, project_id: int, name: str, **kwargs) -> int:
        """创建人物卡片"""
        data = {
            "project_id": project_id,
            "name": name,
            "gender": kwargs.get("gender", ""),
            "age": kwargs.get("age", ""),
            "appearance": kwargs.get("appearance", ""),
            "personality": kwargs.get("personality", ""),
            "background": kwargs.get("background", ""),
            "catchphrase": kwargs.get("catchphrase", ""),
            "relationships": kwargs.get("relationships", "[]"),
            "notes": kwargs.get("notes", "")
        }
        return db_manager.insert("characters", data)

    def update_character(self, character_id: int, data: Dict):
        """更新人物卡片"""
        data["updated_at"] = datetime.now().isoformat()
        db_manager.update("characters", data, "id = ?", (character_id,))

    def delete_character(self, character_id: int):
        """删除人物卡片"""
        db_manager.move_to_recycle_bin("characters", character_id)


class WorldSettingManager:
    """世界观设定管理器"""

    CATEGORIES = ["地理", "历史", "种族", "势力", "物品", "规则", "魔法", "科技", "文化", "其他"]

    def get_settings(self, project_id: int, category: str = "") -> List[Dict]:
        """获取世界观设定"""
        if category:
            return db_manager.fetch_all(
                "SELECT * FROM world_settings WHERE project_id = ? AND category = ? AND is_deleted = 0 ORDER BY updated_at DESC",
                (project_id, category)
            )
        return db_manager.fetch_all(
            "SELECT * FROM world_settings WHERE project_id = ? AND is_deleted = 0 ORDER BY category, updated_at DESC",
            (project_id,)
        )

    def create_setting(self, project_id: int, category: str, title: str, content: str = "", tags: str = "[]") -> int:
        """创建世界观设定"""
        return db_manager.insert("world_settings", {
            "project_id": project_id,
            "category": category,
            "title": title,
            "content": content,
            "tags": tags
        })

    def update_setting(self, setting_id: int, data: Dict):
        """更新世界观设定"""
        data["updated_at"] = datetime.now().isoformat()
        db_manager.update("world_settings", data, "id = ?", (setting_id,))

    def get_setting(self, setting_id: int) -> Optional[Dict]:
        """获取单条世界观设定"""
        return db_manager.fetch_one(
            "SELECT * FROM world_settings WHERE id = ? AND is_deleted = 0",
            (setting_id,)
        )

    def delete_setting(self, setting_id: int):
        """删除世界观设定"""
        db_manager.move_to_recycle_bin("world_settings", setting_id)


class TimelineManager:
    """时间线管理器"""

    def get_events(self, project_id: int) -> List[Dict]:
        """获取时间线事件"""
        return db_manager.fetch_all(
            "SELECT * FROM timeline_events WHERE project_id = ? ORDER BY sort_order, event_date",
            (project_id,)
        )

    def create_event(self, project_id: int, title: str, description: str = "",
                     event_date: str = "", chapter_id: int = None) -> int:
        """创建时间线事件"""
        max_order = db_manager.fetch_one(
            "SELECT COALESCE(MAX(sort_order), -1) as max_order FROM timeline_events WHERE project_id = ?",
            (project_id,)
        )
        sort_order = (max_order["max_order"] if max_order else -1) + 1
        return db_manager.insert("timeline_events", {
            "project_id": project_id,
            "title": title,
            "description": description,
            "event_date": event_date,
            "sort_order": sort_order,
            "chapter_id": chapter_id
        })

    def update_event(self, event_id: int, data: Dict):
        """更新时间线事件"""
        db_manager.update("timeline_events", data, "id = ?", (event_id,))

    def delete_event(self, event_id: int):
        """删除时间线事件"""
        db_manager.delete("timeline_events", "id = ?", (event_id,))


class WritingStatsManager:
    """写作统计管理器"""

    def record_writing(self, project_id: int, word_count: int, writing_time: int = 0):
        """记录写作数据

        Args:
            project_id: 项目ID
            word_count: 本次写作字数
            writing_time: 写作时长（秒）
        """
        today = datetime.now().strftime("%Y-%m-%d")
        existing = db_manager.fetch_one(
            "SELECT * FROM writing_stats WHERE project_id = ? AND date = ?",
            (project_id, today)
        )
        if existing:
            db_manager.update("writing_stats", {
                "word_count": existing["word_count"] + word_count,
                "writing_time": existing["writing_time"] + writing_time
            }, "id = ?", (existing["id"],))
        else:
            db_manager.insert("writing_stats", {
                "project_id": project_id,
                "date": today,
                "word_count": word_count,
                "writing_time": writing_time
            })

    def get_stats(self, project_id: int, days: int = 7) -> List[Dict]:
        """获取最近N天的写作统计"""
        return db_manager.fetch_all(
            """SELECT * FROM writing_stats
               WHERE project_id = ?
               ORDER BY date DESC LIMIT ?""",
            (project_id, days)
        )

    def get_total_stats(self, project_id: int) -> Dict:
        """获取总统计"""
        result = db_manager.fetch_one(
            """SELECT COALESCE(SUM(word_count), 0) as total_words,
                      COALESCE(SUM(writing_time), 0) as total_time
               FROM writing_stats WHERE project_id = ?""",
            (project_id,)
        )
        return {"total_words": result["total_words"], "total_time": result["total_time"]}


class RecycleBinManager:
    """回收站管理器"""

    def get_items(self) -> List[Dict]:
        """获取回收站所有项目"""
        return db_manager.fetch_all(
            "SELECT * FROM recycle_bin ORDER BY deleted_at DESC"
        )

    def restore_item(self, recycle_id: int):
        """恢复项目"""
        db_manager.restore_from_recycle_bin(recycle_id)

    def permanently_delete(self, recycle_id: int):
        """永久删除"""
        item = db_manager.fetch_one("SELECT * FROM recycle_bin WHERE id = ?", (recycle_id,))
        if item:
            db_manager.delete(item["original_table"], "id = ?", (item["original_id"],))
            db_manager.delete("recycle_bin", "id = ?", (recycle_id,))

    def empty_bin(self):
        """清空回收站"""
        items = self.get_items()
        for item in items:
            self.permanently_delete(item["id"])


project_manager = ProjectManager()
volume_manager = VolumeManager()
chapter_manager = ChapterManager()
character_manager = CharacterManager()
world_setting_manager = WorldSettingManager()
timeline_manager = TimelineManager()
writing_stats_manager = WritingStatsManager()
recycle_bin_manager = RecycleBinManager()