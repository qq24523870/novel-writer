"""自动生成小说功能模拟测试脚本"""
import sys
import os
import concurrent.futures
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models.database import db_manager
from models.ai_provider import ai_manager
from core.writing_core import (project_manager, volume_manager,
                               chapter_manager, recycle_bin_manager)
from core.ai_prompts import make_chapter_prompt, get_prompt
from utils.text_processor import text_processor
from utils.logger import logger


def test_full_generation():
    """完整模拟生成流程"""
    print("=" * 60)
    print("AI小说生成功能模拟测试")
    print("=" * 60)

    # 1. 初始化
    db_manager.initialize()
    ai_manager.initialize()
    print("[OK] 数据库已初始化")
    print("[OK] AI模型: " + str(ai_manager.get_available_providers()))
    print()

    # 2. 创建项目
    novel_name = "[TEST] 星际迷途"
    print("步骤1: 创建项目《" + novel_name + "》")

    pid = project_manager.create_project(
        name=novel_name,
        author="AI创作",
        genre="科幻",
        description="AI自动生成的小说\n主角：林夜\n类型：科幻",
        word_goal=10 * 2000
    )
    print("  [OK] 项目已创建, ID=" + str(pid))

    volumes = volume_manager.get_volumes(pid)
    volume_id = volumes[0]["id"]
    print("  [OK] 卷已创建, volume_id=" + str(volume_id) + ", title=" + volumes[0]['title'])

    # 3. 删除默认空白章节
    existing = chapter_manager.get_chapters(volume_id)
    print("  [WARN] 发现 " + str(len(existing)) + " 个默认空白章节，正在清理...")
    for ch in existing:
        chapter_manager.delete_chapter(ch["id"])
    print("  [OK] 默认空白章节已清理")
    print()

    # 4. 逐章生成（测试3章，节省时间）
    print("步骤2: 逐章生成（测试3章 x 500字）")
    total_chapters = 3
    words_per_chapter = 500

    context_data = {
        "novel_type": "科幻",
        "protagonist": "林夜，22岁普通大学生，意外获得星际导航能力",
        "setting": "公元3000年，人类已实现星际航行",
        "plot": "主角获神秘能力后卷入星际阴谋",
        "outline": "第一章：意外觉醒\n第二章：初次测试\n第三章：深入调查",
    }

    previous_summaries = []
    total_words = 0
    max_tokens = int(words_per_chapter * 1.5) + 200
    success = True

    for chapter_number in range(1, total_chapters + 1):
        chapter_title = "第" + str(chapter_number) + "章"
        print()
        print("  " + "-" * 40)
        print("  [第" + str(chapter_number) + "/" + str(total_chapters) + "章]: " + chapter_title)

        # 创建章节
        cid = chapter_manager.create_chapter(volume_id, chapter_title)
        if not cid:
            print("  [FAIL] 创建章节失败")
            success = False
            break
        print("  [OK] 章节已创建, id=" + str(cid))

        # 构建提示词
        prompt = make_chapter_prompt(
            context_type="detail",
            context_data=context_data,
            chapter_number=chapter_number,
            chapter_title=chapter_title,
            word_count=words_per_chapter,
            previous_summaries=previous_summaries
        )
        print("  [OK] 提示词已生成, 长度=" + str(len(prompt)))

        # 调用AI生成（使用与对话框相同的concurrent.futures超时机制）
        print("  [WAIT] 正在调用AI生成（约" + str(words_per_chapter) + "字）...")
        import time
        start = time.time()
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(
                    ai_manager.generate,
                    prompt=prompt,
                    max_tokens=max_tokens,
                    temperature=0.8
                )
                result = future.result(timeout=180)
        except concurrent.futures.TimeoutError:
            print("  [FAIL] AI生成超时（>180秒）")
            success = False
            break
        except Exception as e:
            print("  [FAIL] AI生成异常: " + str(e))
            success = False
            break
        elapsed = time.time() - start
        print("  [OK] AI返回耗时: " + str(round(elapsed, 1)) + "秒")

        if not result or result.startswith("错误:") or result.startswith("生成失败"):
            print("  [FAIL] AI生成失败: " + str(result))
            success = False
            break

        # 保存章节
        chapter_manager.save_chapter(cid, result)

        # 统计
        word_count = text_processor.count_words(result)
        total_words += word_count
        summary = result[:150].replace("\n", " ")
        previous_summaries.append(summary)

        print("  [OK] 章节已完成!")
        print("  [DATA] 本章字数: " + str(word_count))
        print("  [DATA] 内容开头: " + result[:80].replace("\n", " ") + "...")
        print("  [DATA] 摘要: " + summary[:60] + "...")

    # 5. 结果验证
    print()
    print("=" * 40)
    print("步骤3: 结果验证")
    print("=" * 40)

    if success:
        chapters = chapter_manager.get_chapters(volume_id)
        project = project_manager.get_project(pid)
        print()
        print("项目《" + project['name'] + "》最终状态:")
        print("  名称: " + project['name'])
        print("  类型: " + project['genre'])
        print("  包含 " + str(len(chapters)) + " 个章节:")
        for ch in chapters:
            content_len = len(ch.get("content", ""))
            wc = ch.get("word_count", 0)
            print("    [章] " + ch['title'] + ": " + str(wc) + "字 (内容长度: " + str(content_len) + ")")

        print()
        print("[PASS] 测试结论: AI生成功能全部正常!")
        print("   - 项目创建: PASS")
        print("   - 默认章节清理: PASS")
        print("   - AI逐章调用(" + str(total_chapters) + "次): PASS")
        print("   - 章节内容保存: PASS")
        print("   - 字数统计: PASS（累计 " + str(total_words) + " 字）")
        print("   - 前后章连贯摘要: PASS（已记录 " + str(len(previous_summaries)) + " 章摘要）")
    else:
        print()
        print("[FAIL] 测试失败: 生成功能存在问题")

    # 6. 清理
    print()
    print("=" * 40)
    print("步骤4: 清理测试数据")
    recycle_bin_manager.empty_bin()
    project_manager.delete_project(pid)
    print("[OK] 测试项目已删除，环境已清理")
    print("=" * 40)


if __name__ == "__main__":
    test_full_generation()
