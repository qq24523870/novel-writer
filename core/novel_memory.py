"""小说记忆管理系统

核心功能：
1. 每章节结束后自动压缩记忆，提取关键信息
2. 追踪伏笔（伏笔）和钩子（钩子）的完整生命周期
3. 跨章节/跨卷的情节连贯性保障
4. 为AI生成提供精准的上下文记忆

压缩策略：
- 每章：立即压缩，生成章节记忆快照
- 每3章：全量记忆重组，清理冗余
- 每卷：卷级综合记忆，提炼弧线进展
- 伏笔/钩子：永久追踪，直到解决"""
import json
import threading
from datetime import datetime
from typing import Callable, Dict, List, Optional, Tuple
from models.database import db_manager
from utils.logger import logger
from utils.text_processor import text_processor


FORESHADOWING_CATEGORIES = {
    "foreshadowing": "伏笔 - 暗示未来情节的细节",
    "hook": "钩子 - 吸引读者追更的悬念",
    "mystery": "谜团 - 需要解开的疑问",
    "character_secret": "角色秘密 - 角色隐藏的真相",
    "item_clue": "物品线索 - 关键物品的线索",
    "prophecy": "预言/预兆 - 预示未来的征兆",
}

FORESHADOWING_STATUSES = {
    "active": "活跃中 - 待解决",
    "evolving": "发展中 - 正在逐步揭示",
    "resolved": "已解决 - 已完成闭环",
    "abandoned": "已废弃 - 决定不再使用",
}

COMPRESSION_INTERVAL_CHAPTERS = 3


class ForeshadowingEntry:
    """单个伏笔/钩子条目"""

    def __init__(self, data: dict):
        self.id = data["id"]
        self.project_id = data["project_id"]
        self.chapter_id = data.get("chapter_id")
        self.title = data["title"]
        self.content = data["content"]
        self.category = data.get("category", "foreshadowing")
        self.status = data.get("status", "active")
        self.planted_at_chapter = data.get("planted_at_chapter", 0)
        self.resolved_at_chapter = data.get("resolved_at_chapter", 0)
        self.resolution_note = data.get("resolution_note", "")
        self.tags = json.loads(data.get("tags", "[]"))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "chapter_id": self.chapter_id,
            "title": self.title,
            "content": self.content,
            "category": self.category,
            "status": self.status,
            "planted_at_chapter": self.planted_at_chapter,
            "resolved_at_chapter": self.resolved_at_chapter,
            "resolution_note": self.resolution_note,
            "tags": self.tags,
        }

    def is_active(self) -> bool:
        return self.status in ("active", "evolving")

    def summary(self) -> str:
        status_icon = {"active": "⏳", "evolving": "🔄", "resolved": "✅", "abandoned": "❌"}
        return f"{status_icon.get(self.status, '❓')}[{self.category}] {self.title}: {self.content[:80]}"


class ChapterMemory:
    """单章记忆压缩"""

    def __init__(self, data: dict):
        self.id = data.get("id", 0)
        self.project_id = data["project_id"]
        self.chapter_id = data["chapter_id"]
        self.volume_id = data["volume_id"]
        self.summary = data.get("summary", "")
        self.key_events = json.loads(data.get("key_events", "[]"))
        self.new_characters = json.loads(data.get("new_characters", "[]"))
        self.active_foreshadowing_ids = json.loads(data.get("active_foreshadowing_ids", "[]"))
        self.word_count = data.get("word_count", 0)

    def to_dict(self) -> dict:
        return {
            "project_id": self.project_id,
            "chapter_id": self.chapter_id,
            "volume_id": self.volume_id,
            "summary": self.summary,
            "key_events": json.dumps(self.key_events, ensure_ascii=False),
            "new_characters": json.dumps(self.new_characters, ensure_ascii=False),
            "active_foreshadowing_ids": json.dumps(self.active_foreshadowing_ids, ensure_ascii=False),
            "word_count": self.word_count,
        }


class NovelMemory:
    """小说记忆管理器 - 每个项目一个实例"""

    def __init__(self, project_id: int):
        self.project_id = project_id
        self._lock = threading.Lock()
        self._foreshadowings: Dict[int, ForeshadowingEntry] = {}
        self._chapter_memories: Dict[int, ChapterMemory] = {}
        self._volume_memories: Dict[int, dict] = {}
        self._plot_arcs: Dict[int, dict] = {}
        self._chapter_count = 0
        self._load_all()

    def _load_all(self):
        """从数据库加载所有记忆数据"""
        with self._lock:
            rows = db_manager.fetch_all(
                "SELECT * FROM foreshadowings WHERE project_id = ? ORDER BY id",
                (self.project_id,)
            )
            for row in rows:
                fe = ForeshadowingEntry(row)
                self._foreshadowings[fe.id] = fe

            cm_rows = db_manager.fetch_all(
                "SELECT * FROM chapter_memories WHERE project_id = ? ORDER BY chapter_id",
                (self.project_id,)
            )
            for row in cm_rows:
                cm = ChapterMemory(row)
                self._chapter_memories[cm.chapter_id] = cm

            vm_rows = db_manager.fetch_all(
                "SELECT * FROM volume_memories WHERE project_id = ? ORDER BY volume_id",
                (self.project_id,)
            )
            for row in vm_rows:
                self._volume_memories[row["volume_id"]] = row

            pa_rows = db_manager.fetch_all(
                "SELECT * FROM plot_arcs WHERE project_id = ? ORDER BY id",
                (self.project_id,)
            )
            for row in pa_rows:
                self._plot_arcs[row["id"]] = row

            self._chapter_count = len(self._chapter_memories)

    # ============ 伏笔/钩子管理 ============

    def add_foreshadowing(self, title: str, content: str,
                          chapter_id: Optional[int] = None,
                          category: str = "foreshadowing",
                          tags: Optional[List[str]] = None) -> int:
        """添加伏笔或钩子

        Args:
            title: 伏笔标题
            content: 详细描述
            chapter_id: 埋下的章节ID
            category: 类别
            tags: 标签列表

        Returns:
            伏笔ID
        """
        with self._lock:
            self._chapter_count += 1
            fid = db_manager.insert("foreshadowings", {
                "project_id": self.project_id,
                "chapter_id": chapter_id,
                "title": title,
                "content": content,
                "category": category,
                "status": "active",
                "planted_at_chapter": self._chapter_count,
                "tags": json.dumps(tags or [], ensure_ascii=False),
            })
            fe = ForeshadowingEntry({
                "id": fid, "project_id": self.project_id,
                "chapter_id": chapter_id, "title": title,
                "content": content, "category": category,
                "status": "active", "planted_at_chapter": self._chapter_count,
                "resolved_at_chapter": 0, "resolution_note": "",
                "tags": json.dumps(tags or [], ensure_ascii=False),
            })
            self._foreshadowings[fid] = fe
            logger.info(f"添加伏笔: [{category}] {title}")
            return fid

    def resolve_foreshadowing(self, foreshadowing_id: int,
                              resolution_note: str = ""):
        """解决伏笔/钩子

        Args:
            foreshadowing_id: 伏笔ID
            resolution_note: 解决说明
        """
        with self._lock:
            fe = self._foreshadowings.get(foreshadowing_id)
            if not fe:
                logger.warning(f"伏笔不存在: {foreshadowing_id}")
                return
            fe.status = "resolved"
            fe.resolved_at_chapter = self._chapter_count
            fe.resolution_note = resolution_note
            db_manager.update("foreshadowings", {
                "status": "resolved",
                "resolved_at_chapter": self._chapter_count,
                "resolution_note": resolution_note,
                "updated_at": datetime.now().isoformat(),
            }, "id = ?", (foreshadowing_id,))
            logger.info(f"伏笔已解决: [{fe.category}] {fe.title}")

    def update_foreshadowing_status(self, foreshadowing_id: int, status: str):
        """更新伏笔状态"""
        with self._lock:
            fe = self._foreshadowings.get(foreshadowing_id)
            if not fe:
                return
            fe.status = status
            db_manager.update("foreshadowings", {
                "status": status,
                "updated_at": datetime.now().isoformat(),
            }, "id = ?", (foreshadowing_id,))

    def get_active_foreshadowings(self) -> List[ForeshadowingEntry]:
        """获取所有活跃的伏笔/钩子"""
        return [fe for fe in self._foreshadowings.values() if fe.is_active()]

    def get_resolved_foreshadowings(self) -> List[ForeshadowingEntry]:
        """获取所有已解决的伏笔/钩子"""
        return [fe for fe in self._foreshadowings.values() if fe.status == "resolved"]

    def get_foreshadowing_context(self, max_count: int = 10) -> str:
        """生成伏笔上下文摘要（供AI使用）"""
        active = self.get_active_foreshadowings()
        if not active:
            return "当前没有活跃的伏笔或钩子。"

        lines = ["【未解决的伏笔和钩子】"]
        for i, fe in enumerate(active[:max_count], 1):
            lines.append(f"  {i}. {fe.summary()}")
        return "\n".join(lines)

    # ============ 章节记忆压缩 ============

    def compress_chapter(self, chapter_id: int, volume_id: int,
                         title: str, content: str):
        """压缩单章记忆

        每次保存章节时自动调用，提取：
        - 情节摘要
        - 关键事件
        - 新增角色
        - 新埋下的伏笔

        Args:
            chapter_id: 章节ID
            volume_id: 卷ID
            title: 章节标题
            content: 章节内容
        """
        with self._lock:
            is_new_chapter = chapter_id not in self._chapter_memories
            if is_new_chapter:
                self._chapter_count += 1

            word_count = text_processor.count_words(content)

            key_events = self._extract_key_events(content)
            new_chars = self._extract_new_characters(content)

            summary = content[:200].replace("\n", " ") if len(content) > 200 else content

            data = {
                "project_id": self.project_id,
                "chapter_id": chapter_id,
                "volume_id": volume_id,
                "summary": summary,
                "key_events": json.dumps(key_events, ensure_ascii=False),
                "new_characters": json.dumps(new_chars, ensure_ascii=False),
                "active_foreshadowing_ids": json.dumps(
                    [fe.id for fe in self.get_active_foreshadowings()],
                    ensure_ascii=False
                ),
                "word_count": word_count,
            }

            existing = db_manager.fetch_one(
                "SELECT id FROM chapter_memories WHERE chapter_id = ?",
                (chapter_id,)
            )
            if existing:
                db_manager.update("chapter_memories", data, "chapter_id = ?", (chapter_id,))
            else:
                db_manager.insert("chapter_memories", data)

            self._chapter_memories[chapter_id] = ChapterMemory({
                "id": existing["id"] if existing else 0, **data
            })
            logger.info(f"章节记忆压缩完成: {title} ({word_count}字)")

            if is_new_chapter and self._chapter_count % COMPRESSION_INTERVAL_CHAPTERS == 0:
                self._trigger_full_compression()

    def compress_volume(self, volume_id: int, title: str):
        """压缩卷级记忆"""
        with self._lock:
            chapters = db_manager.fetch_all(
                "SELECT * FROM chapter_memories WHERE volume_id = ? ORDER BY chapter_id",
                (volume_id,)
            )
            if not chapters:
                return

            all_events = []
            all_chars = set()
            active_fids = set()
            total_words = 0

            for ch in chapters:
                events = json.loads(ch.get("key_events", "[]"))
                all_events.extend(events)
                chars = json.loads(ch.get("new_characters", "[]"))
                all_chars.update(chars)
                fids = json.loads(ch.get("active_foreshadowing_ids", "[]"))
                active_fids.update(fids)
                total_words += ch.get("word_count", 0)

            resolved_ids = [fe.id for fe in self._foreshadowings.values()
                          if fe.status == "resolved"]

            summary = f"卷《{title}》记忆摘要：包含 {len(chapters)} 章，"
            summary += f"共 {total_words} 字。"
            if all_events:
                summary += f"关键事件: {' → '.join(all_events[:5])}"

            data = {
                "summary": summary,
                "arc_progression": json.dumps(all_events[:20], ensure_ascii=False),
                "character_arcs": json.dumps(list(all_chars), ensure_ascii=False),
                "resolved_foreshadowing_ids": json.dumps(resolved_ids, ensure_ascii=False),
                "active_foreshadowing_ids": json.dumps(list(active_fids), ensure_ascii=False),
                "word_count": total_words,
            }

            existing = db_manager.fetch_one(
                "SELECT id FROM volume_memories WHERE volume_id = ?",
                (volume_id,)
            )
            if existing:
                db_manager.update("volume_memories", data, "volume_id = ?", (volume_id,))
            else:
                data.update({"project_id": self.project_id, "volume_id": volume_id})
                db_manager.insert("volume_memories", data)

            self._volume_memories[volume_id] = data
            logger.info(f"卷记忆压缩完成: {title} ({len(chapters)}章, {total_words}字)")

    def _extract_key_events(self, content: str) -> List[str]:
        """从内容中提取关键事件"""
        sentences = text_processor.count_sentences(content)
        if sentences <= 3:
            return [content[:100].replace("\n", " ")]
        lines = [l.strip() for l in content.split("\n") if l.strip()]
        events = [l[:80] for l in lines[:5] if len(l) > 10]
        if not events:
            events = [content[:100].replace("\n", " ")]
        return events[:5]

    def _extract_new_characters(self, content: str) -> List[str]:
        """提取新出现的人物名"""
        known_chars = db_manager.fetch_all(
            "SELECT name FROM characters WHERE project_id = ?",
            (self.project_id,)
        )
        known_names = [c["name"] for c in known_chars]
        found = []
        for name in known_names:
            if name in content:
                found.append(name)
        return found[:3]

    def _trigger_full_compression(self):
        """全量记忆重组（每3章触发一次）"""
        logger.info(f"触发全量记忆重组 (第{self._chapter_count}章)")
        chapters = db_manager.fetch_all(
            "SELECT * FROM chapter_memories WHERE project_id = ? ORDER BY chapter_id",
            (self.project_id,)
        )
        if not chapters:
            return
        recent = chapters[-3:]
        summaries = []
        for ch in recent:
            vol = db_manager.fetch_one(
                "SELECT title FROM volumes WHERE id = ?", (ch["volume_id"],)
            )
            vol_title = vol["title"] if vol else "未知卷"
            summaries.append(f"[{vol_title} 第{ch['chapter_id']}章] {ch['summary'][:100]}")
        logger.info(f"全量记忆: {' | '.join(summaries)}")

    # ============ 上下文生成 ============

    def get_ai_context(self, current_chapter_id: Optional[int] = None,
                       max_summary_chapters: int = 5) -> str:
        """生成供AI使用的完整上下文

        Args:
            current_chapter_id: 当前章节ID（排除自身）
            max_summary_chapters: 最多返回几章的摘要

        Returns:
            格式化的上下文文本
        """
        parts = []

        active_fs = self.get_active_foreshadowings()
        if active_fs:
            parts.append("=== 待解决的伏笔/钩子 ===")
            for fe in active_fs[:8]:
                parts.append(f"  [{fe.category}] {fe.title}")
                parts.append(f"    埋下位置: 第{fe.planted_at_chapter}章")
                parts.append(f"    内容: {fe.content[:120]}")
            parts.append("")

        summaries = []
        for cm in sorted(self._chapter_memories.values(),
                        key=lambda x: x.chapter_id, reverse=True):
            if current_chapter_id and cm.chapter_id == current_chapter_id:
                continue
            summaries.append(cm)
            if len(summaries) >= max_summary_chapters:
                break
        summaries.reverse()

        if summaries:
            parts.append("=== 最近章节摘要 ===")
            for cm in summaries:
                vol = db_manager.fetch_one(
                    "SELECT title FROM volumes WHERE id = ?", (cm.volume_id,)
                )
                vol_title = vol["title"] if vol else ""
                parts.append(f"  第{cm.chapter_id}章: {cm.summary[:150]}")
                if cm.key_events:
                    for ev in cm.key_events[:2]:
                        parts.append(f"    - {ev}")
            parts.append("")

        for vm in self._volume_memories.values():
            if isinstance(vm, dict):
                parts.append(f"  卷摘要: {vm.get('summary', '')[:200]}")
        parts.append("")

        resolved = self.get_resolved_foreshadowings()
        if resolved:
            parts.append("=== 已解决的伏笔/钩子 ===")
            for fe in resolved[-5:]:
                parts.append(f"  ✅ {fe.title} - {fe.resolution_note[:80]}")
            parts.append("")

        return "\n".join(parts)

    # ============ 查询API ============

    def get_chapter_memory(self, chapter_id: int) -> Optional[ChapterMemory]:
        return self._chapter_memories.get(chapter_id)

    def get_statistics(self) -> dict:
        """获取记忆系统统计"""
        with self._lock:
            active = len(self.get_active_foreshadowings())
            resolved = len(self.get_resolved_foreshadowings())
            total_fs = len(self._foreshadowings)
            return {
                "chapter_count": len(self._chapter_memories),
                "volume_count": len(self._volume_memories),
                "total_foreshadowings": total_fs,
                "active_foreshadowings": active,
                "resolved_foreshadowings": resolved,
                "resolve_rate": f"{resolved / total_fs * 100:.1f}%" if total_fs > 0 else "0%",
            }


class NovelMemoryManager:
    """全局记忆管理器，管理所有项目的记忆"""

    _instance = None
    _instances: Dict[int, NovelMemory] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get_memory(self, project_id: int) -> NovelMemory:
        """获取指定项目的记忆管理器"""
        if project_id not in self._instances:
            self._instances[project_id] = NovelMemory(project_id)
        return self._instances[project_id]

    def clear_cache(self, project_id: Optional[int] = None):
        """清除缓存"""
        if project_id:
            self._instances.pop(project_id, None)
        else:
            self._instances.clear()


novel_memory_manager = NovelMemoryManager()
