"""小说全文扫描系统

功能：
1. 扫描全文提取人物信息（已有人物出场统计 + 新人物检测）
2. 扫描全文提取世界观设定关键词
3. 扫描全文检测伏笔和钩子
4. 为每一卷生成内容总结和大纲
5. 生成全文综述
"""
import re
import json
import threading
from typing import Callable, Dict, List, Optional
from models.database import db_manager
from models.ai_provider import ai_manager
from utils.logger import logger
from utils.text_processor import text_processor


class NovelScanner:
    """小说全文扫描器"""

    @staticmethod
    def get_all_project_content(project_id: int) -> List[Dict]:
        """获取项目所有章节内容（按卷分组）

        Args:
            project_id: 项目ID

        Returns:
            按卷分组的章节列表
        """
        volumes = db_manager.fetch_all(
            "SELECT * FROM volumes WHERE project_id = ? AND is_deleted = 0 ORDER BY sort_order",
            (project_id,)
        )
        result = []
        for vol in volumes:
            chapters = db_manager.fetch_all(
                "SELECT * FROM chapters WHERE volume_id = ? AND is_deleted = 0 ORDER BY sort_order",
                (vol["id"],)
            )
            result.append({
                "volume": vol,
                "chapters": chapters
            })
        return result

    @staticmethod
    def scan_characters(project_id: int) -> Dict:
        """扫描全文统计人物出场情况

        Returns:
            {
                "known_characters": [{"name": ..., "appearances": ..., "chapter_ids": [...]}, ...],
                "potential_new_characters": ["name1", "name2", ...],
                "total_appearances": int
            }
        """
        known_chars = db_manager.fetch_all(
            "SELECT id, name, personality, gender FROM characters WHERE project_id = ? AND is_deleted = 0",
            (project_id,)
        )

        all_chapters = db_manager.fetch_all(
            """SELECT c.id, c.content, c.title, v.title as volume_title
               FROM chapters c
               JOIN volumes v ON c.volume_id = v.id
               WHERE v.project_id = ? AND c.is_deleted = 0 AND v.is_deleted = 0
               ORDER BY v.sort_order, c.sort_order""",
            (project_id,)
        )

        char_stats = {}
        for char in known_chars:
            char_stats[char["name"]] = {
                "name": char["name"],
                "personality": char.get("personality", ""),
                "gender": char.get("gender", ""),
                "appearances": 0,
                "chapter_ids": [],
                "chapter_titles": []
            }

        full_text_parts = []
        for ch in all_chapters:
            content = ch.get("content", "")
            full_text_parts.append(content)

            for char_name in char_stats:
                if char_name in content:
                    char_stats[char_name]["appearances"] += content.count(char_name)
                    if ch["id"] not in char_stats[char_name]["chapter_ids"]:
                        char_stats[char_name]["chapter_ids"].append(ch["id"])
                        char_stats[char_name]["chapter_titles"].append(ch["title"])

        full_text = "\n".join(full_text_parts)

        potential_new = NovelScanner._detect_potential_characters(full_text, known_chars)

        sorted_chars = sorted(char_stats.values(), key=lambda x: x["appearances"], reverse=True)

        return {
            "known_characters": sorted_chars,
            "potential_new_characters": potential_new[:20],
            "total_appearances": sum(c["appearances"] for c in sorted_chars)
        }

    @staticmethod
    def _detect_potential_characters(text: str, known_chars: List[Dict]) -> List[str]:
        """检测潜在的新人物（基于命名实体模式）

        规则：
        - 2-4个中文字符组成的词
        - 出现在引号对话前或"说"、"道"、"问"、"答"等词前面
        - 已有人物排除
        """
        known_names = {c["name"] for c in known_chars}

        dialogue_pattern = re.compile(
            r'([\u4e00-\u9fff]{2,4})(?:说|道|问|答|喊|叫|骂|笑|哭|叹'
            r'|怒道|笑道|说道|问道|答道|喊道|叫道|骂道|叹道|惊道|冷道|淡道'
            r'|冷笑|苦笑|怒喝|大喝|低喝|沉声|厉声|低声|轻声|淡淡道|冷冷道)')
        matches = dialogue_pattern.findall(text)

        name_freq = {}
        for name in matches:
            if name not in known_names:
                name_freq[name] = name_freq.get(name, 0) + 1

        sorted_names = sorted(name_freq.items(), key=lambda x: x[1], reverse=True)

        common_words = {
            "什么", "怎么", "然后", "因为", "所以", "虽然", "但是", "如果", "而且", "或者",
            "大概", "可能", "应该", "可以", "没有", "不是", "就是", "这个", "那个", "一个",
            "两个", "我们", "他们", "你们", "自己", "大家", "这样", "那样", "为什么",
            "忽然", "突然", "马上", "立刻", "已经", "还是", "终于", "当然", "果然", "居然",
            "竟然", "不过", "只是", "无论", "不管", "除了", "除非", "尽管", "哪怕", "毕竟",
            "原来", "以前", "以后", "刚才", "现在", "正在", "已经", "一直", "总是", "经常",
            "偶尔", "从未", "从来", "仍然", "依旧", "渐渐", "慢慢", "猛地", "倏地", "霍地",
            "顿时", "瞬间", "霎时", "转身", "起来", "回来", "过去", "过来", "怎么",
            "似乎", "仿佛", "好像", "如同", "犹如", "宛若", "恍若", "依旧", "依然",
        }

        result = []
        for name, freq in sorted_names:
            if freq >= 2 and name not in common_words and len(name) >= 2:
                name_str = name.strip()
                if name_str:
                    result.append(f"{name_str}（出现{freq}次）")

        return result

    @staticmethod
    def scan_world_settings(project_id: int) -> Dict:
        """扫描全文提取世界观相关信息

        Returns:
            {
                "category_keywords": {category: [keyword, ...], ...},
                "detected_locations": [{"name": ..., "mentions": ...}, ...],
                "detected_items": [{"name": ..., "mentions": ...}, ...]
            }
        """
        categories = ["地理", "历史", "种族", "势力", "物品", "规则", "魔法", "科技", "文化", "其他"]

        existing_settings = db_manager.fetch_all(
            "SELECT title, content, category FROM world_settings WHERE project_id = ? AND is_deleted = 0",
            (project_id,)
        )

        all_chapters = db_manager.fetch_all(
            """SELECT c.content
               FROM chapters c
               JOIN volumes v ON c.volume_id = v.id
               WHERE v.project_id = ? AND c.is_deleted = 0 AND v.is_deleted = 0""",
            (project_id,)
        )
        full_text = "\n".join([ch.get("content", "") for ch in all_chapters])

        category_keywords = {}
        for cat in categories:
            category_keywords[cat] = []

        for setting in existing_settings:
            cat = setting.get("category", "其他")
            if cat not in category_keywords:
                category_keywords[cat] = []
            category_keywords[cat].append({
                "title": setting["title"],
                "content_preview": setting.get("content", "")[:60],
                "mentions_in_text": full_text.count(setting["title"])
            })

        location_pattern = re.compile(r'(?:在|来到|前往|抵达|离开|进入|位于|坐落于|到达|返回)([\u4e00-\u9fff]{2,6}(?:城|镇|村|山|河|湖|海|岛|谷|林|森|原|峰|崖|洞|殿|塔|寺|观|宫|堡|楼|阁|园|馆|院))')
        location_matches = location_pattern.findall(full_text)
        location_freq = {}
        for loc in location_matches:
            location_freq[loc] = location_freq.get(loc, 0) + 1

        sorted_locations = sorted(location_freq.items(), key=lambda x: x[1], reverse=True)

        return {
            "category_keywords": category_keywords,
            "detected_locations": [{"name": k, "mentions": v} for k, v in sorted_locations[:15]],
        }

    @staticmethod
    def scan_foreshadowing(project_id: int) -> Dict:
        """扫描全文现有伏笔状态

        Returns:
            {
                "active": [...],
                "resolved": [...],
                "unresolved_ratio": str
            }
        """
        foreshadowings = db_manager.fetch_all(
            "SELECT * FROM foreshadowings WHERE project_id = ? ORDER BY status, planted_at_chapter",
            (project_id,)
        )

        active = []
        resolved = []
        for fs in foreshadowings:
            entry = {
                "id": fs["id"],
                "title": fs["title"],
                "content": fs["content"][:100],
                "category": fs["category"],
                "status": fs["status"],
                "planted_at_chapter": fs.get("planted_at_chapter", 0),
            }
            if fs["status"] in ("active", "evolving"):
                active.append(entry)
            elif fs["status"] == "resolved":
                entry["resolution_note"] = fs.get("resolution_note", "")[:60]
                resolved.append(entry)

        total = len(foreshadowings)
        active_count = len(active)
        resolved_count = len(resolved)

        return {
            "active": active,
            "resolved": resolved,
            "total": total,
            "active_count": active_count,
            "resolved_count": resolved_count,
            "unresolved_ratio": f"{active_count / total * 100:.1f}%" if total > 0 else "0%"
        }

    @staticmethod
    def generate_volume_summaries(project_id: int) -> List[Dict]:
        """为每一卷生成内容总结

        Returns:
            [{
                "volume_title": ...,
                "chapter_count": ...,
                "total_words": ...,
                "summary": ...,
                "key_events": [...],
                "characters": [...]
            }, ...]
        """
        from core.novel_memory import novel_memory_manager

        volumes = db_manager.fetch_all(
            "SELECT * FROM volumes WHERE project_id = ? AND is_deleted = 0 ORDER BY sort_order",
            (project_id,)
        )

        memory = novel_memory_manager.get_memory(project_id)
        summaries = []

        for vol in volumes:
            chapters = db_manager.fetch_all(
                "SELECT * FROM chapters WHERE volume_id = ? AND is_deleted = 0 ORDER BY sort_order",
                (vol["id"],)
            )

            total_words = sum(ch.get("word_count", 0) for ch in chapters)

            vol_memory = memory._volume_memories.get(vol["id"], {})
            if isinstance(vol_memory, dict) and vol_memory.get("summary"):
                summary = vol_memory["summary"]
            else:
                chapter_summaries = []
                for ch in chapters:
                    cm = memory.get_chapter_memory(ch["id"])
                    if cm:
                        chapter_summaries.append(cm.summary[:100])
                if chapter_summaries:
                    summary = f"本卷共{len(chapters)}章，{total_words}字。情节概要: " + " | ".join(chapter_summaries[:5])
                else:
                    summary = f"本卷共{len(chapters)}章，{total_words}字。"

            all_chars_in_vol = set()
            for ch in chapters:
                cm = memory.get_chapter_memory(ch["id"])
                if cm and cm.new_characters:
                    all_chars_in_vol.update(cm.new_characters)

            chapter_titles = [ch["title"] for ch in chapters]

            summaries.append({
                "volume_title": vol["title"],
                "chapter_count": len(chapters),
                "total_words": total_words,
                "summary": summary,
                "chapter_titles": chapter_titles,
                "characters": list(all_chars_in_vol)
            })

        return summaries

    @staticmethod
    def generate_full_novel_outline(project_id: int) -> Dict:
        """生成全文综述

        Returns:
            {
                "novel_name": ...,
                "author": ...,
                "genre": ...,
                "total_volumes": ...,
                "total_chapters": ...,
                "total_words": ...,
                "volume_summaries": [...],
                "character_count": ...,
                "foreshadowing_summary": ...,
                "overview": ...
            }
        """
        project = db_manager.fetch_one(
            "SELECT * FROM projects WHERE id = ? AND is_deleted = 0",
            (project_id,)
        )
        if not project:
            return {}

        volumes_data = NovelScanner.get_all_project_content(project_id)
        total_chapters = sum(len(v["chapters"]) for v in volumes_data)
        total_words = sum(
            ch.get("word_count", 0) or text_processor.count_words(ch.get("content", ""))
            for v in volumes_data for ch in v["chapters"]
        )

        char_result = NovelScanner.scan_characters(project_id)
        fs_result = NovelScanner.scan_foreshadowing(project_id)
        vol_summaries = NovelScanner.generate_volume_summaries(project_id)

        overview_parts = [f"《{project['name']}》"]
        overview_parts.append(f"作者: {project.get('author', '未设置')} | 类型: {project.get('genre', '未设置')}")
        overview_parts.append(f"共 {len(volumes_data)} 卷，{total_chapters} 章，{total_words} 字")
        overview_parts.append(f"登场人物: {len(char_result['known_characters'])} 个已知角色")
        overview_parts.append(f"伏笔/钩子: {fs_result['total']} 个（活跃: {fs_result['active_count']}, 已解决: {fs_result['resolved_count']}）")

        overview_parts.append("\n【卷结构概览】")
        for vs in vol_summaries:
            overview_parts.append(f"\n{vs['volume_title']}:")
            overview_parts.append(f"  {vs['chapter_count']}章, {vs['total_words']}字")
            overview_parts.append(f"  章节: {' → '.join(vs['chapter_titles'][:8])}")
            if len(vs['chapter_titles']) > 8:
                overview_parts.append(f"  ...等共{vs['chapter_count']}章")
            overview_parts.append(f"  概要: {vs['summary'][:150]}")

        overview_parts.append("\n【人物出场统计】")
        for c in char_result['known_characters'][:10]:
            overview_parts.append(f"  {c['name']}: 出场{c['appearances']}次，涉及{c['chapter_ids']}章")

        if char_result['potential_new_characters']:
            overview_parts.append(f"\n【潜在新人物建议】")
            for pnc in char_result['potential_new_characters'][:8]:
                overview_parts.append(f"  {pnc}")

        overview_parts.append(f"\n【伏笔状态】")
        if fs_result['active']:
            overview_parts.append(f"  活跃中:")
            for fs in fs_result['active'][:8]:
                overview_parts.append(f"    [{fs['category']}] {fs['title']}")
        if fs_result['resolved']:
            overview_parts.append(f"  已解决:")
            for fs in fs_result['resolved'][:5]:
                overview_parts.append(f"    {fs['title']}")

        return {
            "novel_name": project.get("name", ""),
            "author": project.get("author", ""),
            "genre": project.get("genre", ""),
            "description": project.get("description", ""),
            "total_volumes": len(volumes_data),
            "total_chapters": total_chapters,
            "total_words": total_words,
            "volume_summaries": vol_summaries,
            "character_count": len(char_result['known_characters']),
            "character_stats": char_result['known_characters'][:15],
            "potential_new_characters": char_result['potential_new_characters'][:10],
            "foreshadowing_summary": {
                "total": fs_result['total'],
                "active": fs_result['active_count'],
                "resolved": fs_result['resolved_count'],
                "unresolved_ratio": fs_result['unresolved_ratio']
            },
            "overview": "\n".join(overview_parts)
        }

    @staticmethod
    def get_full_novel_text(project_id: int, max_chars: int = 8000) -> str:
        """获取全文文本（供AI分析使用）

        Args:
            project_id: 项目ID
            max_chars: 最大字符数（AI有上下文限制）

        Returns:
            格式化全文文本
        """
        volumes_data = NovelScanner.get_all_project_content(project_id)
        parts = []
        total_chars = 0
        for vd in volumes_data:
            vol = vd["volume"]
            vol_text = f"\n{'='*20}\n【{vol['title']}】\n{'='*20}\n"
            parts.append(vol_text)
            total_chars += len(vol_text)
            for ch in vd["chapters"]:
                content = ch.get("content", "")
                ch_text = f"\n## {ch['title']}\n\n{content[:500]}\n"
                if total_chars + len(ch_text) > max_chars:
                    ch_text = f"\n## {ch['title']}\n\n{content[:200]}...(截断)\n"
                parts.append(ch_text)
                total_chars += len(ch_text)
                if total_chars > max_chars:
                    break
            if total_chars > max_chars:
                parts.append("\n...（内容过长，已截断）")
                break
        return "".join(parts)

    @staticmethod
    def ai_scan_full_novel(project_id: int,
                           on_complete: Callable[[str], None] = None,
                           on_error: Callable[[str], None] = None,
                           on_token: Callable[[str], None] = None):
        """使用AI进行全文深度分析

        Args:
            project_id: 项目ID
            on_complete: 完成回调
            on_error: 错误回调
            on_token: 流式token回调
        """
        from core.ai_prompts import get_prompt

        project = db_manager.fetch_one(
            "SELECT name FROM projects WHERE id = ?", (project_id,)
        )
        novel_text = NovelScanner.get_full_novel_text(project_id, max_chars=8000)
        novel_name = project["name"] if project else "未知"

        full_content = f"小说名称：{novel_name}\n\n{novel_text}"
        prompt = get_prompt("scan_full_novel", full_content=full_content)

        ai_manager.generate_async(
            prompt=prompt,
            on_complete=on_complete,
            on_error=on_error,
            on_token=on_token
        )

    @staticmethod
    def apply_scan_results(project_id: int, scan_result: Dict) -> Dict:
        """将扫描结果应用到数据库（创建人物卡片、世界观设定、更新卷描述等）

        Args:
            project_id: 项目ID
            scan_result: generate_full_novel_outline 的返回结果

        Returns:
            操作统计 {"characters_created": int, "world_settings_created": int, ...}
        """
        from core.writing_core import character_manager, world_setting_manager, volume_manager
        from core.novel_memory import novel_memory_manager

        stats = {"characters_created": 0, "world_settings_created": 0,
                 "foreshadowings_added": 0, "outlines_updated": 0}

        existing_chars = character_manager.get_characters(project_id)
        existing_names = {c["name"] for c in existing_chars}

        for pnc in scan_result.get("potential_new_characters", []):
            name = pnc.split("（")[0] if "（" in pnc else pnc
            if name not in existing_names and len(name) >= 2:
                character_manager.create_character(
                    project_id, name,
                    notes=f"由全文扫描自动检测（{pnc}）"
                )
                stats["characters_created"] += 1
                existing_names.add(name)

        world_result = scan_result.get("world_settings_result", {})
        detected_locations = world_result.get("detected_locations", [])
        existing_settings = world_setting_manager.get_settings(project_id)
        existing_titles = {s["title"] for s in existing_settings}
        for loc in detected_locations[:10]:
            title = loc["name"]
            if title not in existing_titles:
                content = f"在全文中共出现{loc['mentions']}次。由全文扫描自动检测。"
                world_setting_manager.create_setting(
                    project_id, "地理", title, content
                )
                stats["world_settings_created"] += 1
                existing_titles.add(title)

        memory = novel_memory_manager.get_memory(project_id)
        fs_result = scan_result.get("foreshadowing_summary", {})
        if fs_result:
            stats["foreshadowings_added"] = fs_result.get("total", 0)

        vol_summaries = scan_result.get("volume_summaries", [])
        for vs in vol_summaries:
            volume_id = None
            volumes = volume_manager.get_volumes(project_id)
            for v in volumes:
                if v["title"] == vs["volume_title"]:
                    volume_id = v["id"]
                    break
            if volume_id:
                desc = f"【自动生成卷摘要】{vs['summary'][:200]}"
                volume_manager.update_volume(volume_id, {"description": desc})
                stats["outlines_updated"] += 1

        logger.info(f"扫描结果已应用: {stats}")
        return stats


class NovelScannerManager:
    """全文扫描管理器，提供异步扫描功能"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def scan_full_novel_async(self, project_id: int,
                               on_complete: Callable[[Dict], None] = None,
                               on_progress: Callable[[str], None] = None):
        """异步扫描全文

        Args:
            project_id: 项目ID
            on_complete: 完成回调 (result)
            on_progress: 进度回调 (message)
        """
        def _run():
            try:
                if on_progress:
                    on_progress("正在收集章节数据...")

                volumes_data = NovelScanner.get_all_project_content(project_id)
                if on_progress:
                    on_progress(f"共 {len(volumes_data)} 卷，分析中...")

                if on_progress:
                    on_progress("正在扫描人物出场统计...")
                char_result = NovelScanner.scan_characters(project_id)

                if on_progress:
                    on_progress("正在扫描世界观设定...")
                world_result = NovelScanner.scan_world_settings(project_id)

                if on_progress:
                    on_progress("正在扫描伏笔状态...")
                fs_result = NovelScanner.scan_foreshadowing(project_id)

                if on_progress:
                    on_progress("正在生成卷摘要...")
                vol_summaries = NovelScanner.generate_volume_summaries(project_id)

                if on_progress:
                    on_progress("正在生成全文综述...")
                full_outline = NovelScanner.generate_full_novel_outline(project_id)

                full_outline["world_settings_result"] = world_result
                if on_complete:
                    on_complete(full_outline)

            except Exception as e:
                logger.error(f"全文扫描失败: {e}")
                if on_complete:
                    on_complete({"error": str(e)})

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()


novel_scanner_manager = NovelScannerManager()
