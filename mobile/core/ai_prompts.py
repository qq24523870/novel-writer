"""AI提示词模板集合"""

CONTINUE_WRITING = """你是一位专业的小说作家。请根据以下小说内容和上下文信息，继续往下写。

{novel_context}

【当前章节待续写的内容】
{content}

要求：
1. 必须参考「前文概要」中的情节发展，保持故事连贯性，不能写了当前章节就忘记前面章节的内容
2. 必须考虑「活跃伏笔/钩子」中的未解之谜，在续写中适时推进或暗示
3. 保持原有的风格、视角和叙事节奏
4. 人物性格和关系要与前文保持一致
5. 如果有关键人物在场，请确保其行为符合人物设定

请续写{length}字左右，只输出续写的内容，不要加任何说明。"""

POLISH_TEXT = """你是一位专业的文字编辑。请对以下小说文本进行润色，{intensity}程度地优化语句通顺度和文采。

要求：
- 保持原意不变
- 优化表达方式
- 提升文学美感
- 保持原有风格

原文：
{content}

请直接输出润色后的文本，不要加任何说明。"""

EXPAND_TEXT = """你是一位擅长细节描写的小说作家。请将以下短句或段落扩展为详细的段落，增加细节描写、心理活动、环境氛围等。

原文：
{content}

要求：
- 扩展后约{length}字
- 保持原有风格和基调
- 增加生动的细节描写
- 不要偏离原意

请直接输出扩展后的内容。"""

SUMMARIZE_TEXT = """请将以下小说段落精简为核心内容，保留关键情节和信息，去除冗余描写。

原文：
{content}

要求：
- 精简后约为原文的1/3长度
- 保留核心情节和关键信息
- 保持语句通顺

请直接输出精简后的内容。"""

STYLE_REWRITE = """你是一位擅长多种风格的小说作家。请将以下内容改写为{style}风格。

原文：
{content}

要求：
- 保持核心情节不变
- 使用{style}风格的表达方式
- 调整相应的词汇和句式

请直接输出改写后的内容。"""

CHECK_SPELLING = """请检查以下小说文本中的错别字、语法错误和用词不当之处。

文本：
{content}

请按以下格式输出：
1. 错误位置：[原文中的错误词]
2. 建议修改：[正确的词]
3. 说明：[简要说明]

如果没有错误，请回复"未发现明显错误"。"""

GENERATE_CHARACTER = """你是一位小说角色设计师。请根据以下关键词，生成一个完整的小说人物卡片。

关键词：{keywords}

请生成包含以下内容的人物卡片：
- 姓名
- 性别
- 年龄
- 外貌特征
- 性格特点
- 背景故事
- 口头禅
- 人物关系（可虚构相关人物）

请以结构化的格式输出。"""

GENERATE_OUTLINE = """你是一位资深小说架构师。请根据以下主题和设定，生成一个完整的小说大纲。

小说主题：{theme}
核心设定：{setting}
结构类型：{structure_type}（三幕式/五幕式）

请生成：
1. 故事简介
2. 主要人物
3. 分幕/分卷大纲
4. 关键情节节点
5. 分章建议

请以清晰的结构化格式输出。"""

GENERATE_CHAPTER_TITLES = """请根据以下章节内容，生成3-5个吸引人的章节标题。

章节内容：
{content}

要求：
- 标题要吸引人
- 要能概括章节核心内容
- 保持风格一致
- 每个标题不超过20字

请直接输出标题列表。"""

GENERATE_WORLD = """你是一位世界构建师。请根据以下设定，生成一个完整的虚构世界观。

核心设定：{setting}

请生成包含以下内容的世界观：
1. 地理环境（主要区域、气候、地貌）
2. 历史沿革（重要历史事件、时代划分）
3. 种族/民族（主要种族及其特征）
4. 势力分布（主要组织、国家、势力）
5. 规则体系（社会规则、法律、特殊规则）

请以清晰的结构化格式输出。"""

GENERATE_DIALOGUE = """你是一位小说对话写手。请根据以下场景和人物设定，生成一段自然的人物对话。

场景：{scene}
人物A：{character_a}
人物B：{character_b}
对话主题：{topic}
对话长度：约{length}字

要求：
- 对话要符合人物性格
- 语言要自然流畅
- 要有情感起伏
- 推动情节发展

请直接输出对话内容。"""

AI_CONSULTANT_SYSTEM = """你是一位经验丰富的小说创作顾问和编辑。你可以：
1. 帮助作者梳理剧情走向
2. 解决卡文问题
3. 分析人物关系
4. 提供创作建议
5. 讨论情节发展

请以专业、耐心、富有洞察力的方式与作者交流，给出具体可行的建议。"""

SENSITIVE_WORD_CHECK = """请检测以下文本中是否包含敏感或不适当的内容。

文本：
{content}

请列出所有可能的敏感内容及其位置。如果没有，请回复"未检测到敏感内容"。"""

CHAPTER_MEMORY_COMPRESS = """你是一位资深小说编辑。请对以下章节内容进行专业压缩，提取关键信息。

要求：
1. 用3-5句话概括本章核心情节
2. 列出本章发生的2-4个关键事件（用短句描述）
3. 识别本章新出现的重要角色
4. 识别本章埋下的伏笔或钩子（暗示未来发展的细节、未解之谜等）
5. 注意保留角色的关键对话和重要心理描写

原文：
{content}

请按以下JSON格式输出（不要加任何额外说明）：
{
    "summary": "章节概要",
    "key_events": ["事件1", "事件2"],
    "new_characters": ["新角色1"],
    "foreshadowings": [
        {"title": "伏笔标题", "content": "伏笔描述"}
    ],
    "foreshadowing_count": 0
}"""

VOLUME_MEMORY_COMPRESS = """你是一位资深小说编辑。请对以下整卷内容进行高级压缩，提炼完整的叙事弧线。

要求：
1. 用5-8句话总结整卷的情节发展弧线
2. 列出所有主要角色的成长和变化
3. 识别卷中埋下的所有重要伏笔
4. 识别卷中已解决的伏笔
5. 评估叙事节奏，指出铺垫和高潮部分

各章摘要：
{chapter_summaries}

请按以下JSON格式输出（不要加任何额外说明）：
{
    "summary": "卷级剧情总结",
    "arc_progression": ["弧线节点1", "弧线节点2"],
    "character_arcs": [
        {"name": "角色名", "arc": "角色成长弧线"}
    ],
    "active_foreshadowings": ["活跃伏笔1"],
    "resolved_foreshadowings": ["已解决伏笔1"],
    "narrative_pacing": "节奏评估"
}"""

FORESHADOWING_EXTRACT = """你是一位专业的小说伏笔分析师。请仔细阅读以下章节内容，分析并提取出所有潜在的伏笔、钩子和暗示。

伏笔种类：
- 伏笔：作者埋下的、暗示未来情节发展的细节
- 钩子：用于吸引读者继续阅读的悬念或未解之谜
- 角色伏笔：关于角色身份、秘密或过去的暗示
- 物品伏笔：特定物品可能在未来发挥关键作用
- 对话伏笔：对话中隐藏的重要信息

原文：
{content}

请分析以上内容，列出所有伏笔和钩子。对每个条目说明：
1. 类型（伏笔/钩子/角色伏笔/物品伏笔/对话伏笔）
2. 具体内容（这个伏笔是什么）
3. 可能的发展方向（它可能在后续如何发挥作用）

请按JSON格式输出"""

SCAN_FULL_NOVEL = """你是一位专业的小说分析专家。请对以下小说全文进行深度分析，提取关键信息。

小说全文内容：
{full_content}

请按以下格式进行分析输出：

【一、主要人物分析】
列出所有重要人物，对每个人物说明：
- 姓名
- 角色定位（主角/配角/反派等）
- 性格特征
- 在故事中的作用

【二、世界观设定提取】
提取故事中的世界观要素：
- 地理环境（主要场景、地点）
- 历史背景（重要历史事件）
- 势力组织（国家、帮派、组织等）
- 特殊规则（魔法体系、科技设定等）

【三、伏笔与悬疑检测】
列出所有未解决的伏笔、悬念和谜团：
- 每个伏笔的内容
- 埋下的位置（第几章附近）
- 可能的发展方向

【四、各卷剧情概要】
对每一卷进行总结：
- 卷名
- 核心剧情
- 主要冲突
- 关键转折点

【五、全文综述】
用300-500字概括整个故事的完整脉络，包括：
- 故事主线
- 人物关系网络
- 核心冲突
- 当前进展

请确保分析详尽、准确，直接输出分析结果。"""

AUTO_GENERATE_NOVEL = """你是一位专业的小说创作大师。请根据以下信息，创作一篇完整的小说。

小说类型：{novel_type}
主角设定：{protagonist}
故事背景：{setting}
核心剧情：{plot}
分章大纲：{outline}

创作要求：
1. 请按照以下结构输出小说内容，每个章节用 ===第X章=== 分隔
2. 第一章要有吸引人的开场，能立刻抓住读者
3. 每章结尾要有钩子，让读者想继续看下去
4. 注意人物性格一致性，对话要符合角色设定
5. 控制每章字数在{gen_words}字左右
6. 请先输出一个总标题，用 # 开头
7. 请输出完整的连续内容，不要省略
8. 请生成{gen_chapters}章

输出格式：
# 小说标题
小说简介：（用一段话概括）

===第一章===
[第一章完整内容]

===第二章===
[第二章完整内容]

...（以此类推，生成{gen_chapters}章）"""

AUTO_GENERATE_FROM_OUTLINE = """你是一位专业的小说创作大师。请根据以下总大纲，创作一篇完整的小说。

【总大纲】
{master_outline}

创作要求：
1. 严格按照总大纲的情节脉络创作，不得偏离总大纲的核心设定和剧情走向
2. 请按照以下结构输出小说内容，每个章节用 ===第X章=== 分隔
3. 第一章要有吸引人的开场，能立刻抓住读者
4. 每章结尾要有钩子，让读者想继续看下去
5. 注意人物性格一致性，对话要符合角色设定
6. 控制每章字数在{gen_words}字左右
7. 请先输出一个总标题，用 # 开头
8. 请输出完整的连续内容，不要省略
9. 请生成{gen_chapters}章

输出格式：
# 小说标题
小说简介：（用一段话概括）

===第一章===
[第一章完整内容]

===第二章===
[第二章完整内容]

...（以此类推，生成{gen_chapters}章）"""


def make_chapter_prompt(context_type: str, context_data: dict,
                        chapter_number: int, chapter_title: str,
                        word_count: int, previous_summaries: list) -> str:
    """构建单章生成提示词

    Args:
        context_type: "detail" 或 "outline"
        context_data: 上下文数据字典
        chapter_number: 当前章节号
        chapter_title: 当前章节标题
        word_count: 目标字数
        previous_summaries: 已生成章节的摘要列表

    Returns:
        格式化的提示词
    """
    parts = []

    novel_name = context_data.get("novel_name", "")
    male_name = context_data.get("male_name", "")
    female_name = context_data.get("female_name", "")
    writing_style = context_data.get("writing_style", "")
    gender_text = context_data.get("gender", "")
    existing_project_context = context_data.get("existing_project_context", "")
    is_continuation = bool(existing_project_context)

    is_male_oriented = "男频" in gender_text

    if novel_name:
        parts.append(f"【小说名】{novel_name}")
        parts.append("")

    if is_continuation:
        parts.append("你是一位专业的小说创作大师。请根据以下已有小说的内容脉络，继续往下创作。")
        parts.append("")
        parts.append("========== 已有小说内容回顾（创作后续章节前请先完整阅读）==========")
        parts.append(existing_project_context)
        parts.append("========== 回顾结束 ==========")
        parts.append("")

    if context_type == "outline":
        parts.append(f"你是一位专业的小说创作大师。请根据以下总大纲，生成指定章节的内容。\n")
        parts.append(f"【总大纲】\n{context_data.get('master_outline', '')}\n")

        protagonist_names = []
        if is_male_oriented:
            if male_name:
                protagonist_names.append(f"男主角{male_name}")
        else:
            if female_name:
                protagonist_names.append(f"女主角{female_name}")
            if male_name:
                protagonist_names.append(f"重要角色{male_name}")

        if protagonist_names:
            parts.append(f"主要人物：{'、'.join(protagonist_names)}")
            parts.append("")
    else:
        if not is_continuation:
            parts.append(f"你是一位专业的小说创作大师。请根据以下小说设定，生成指定章节的内容。\n")
        parts.append(f"小说类型：{context_data.get('novel_type', '')}")

        protagonist = context_data.get('protagonist', '')

        if is_male_oriented:
            if male_name and male_name not in protagonist:
                protagonist = f"男主角{male_name}，{protagonist}" if protagonist else f"男主角{male_name}"
            if "第一主角" not in protagonist:
                protagonist = f"（第一主角为男主）{protagonist}"
        else:
            if female_name and female_name not in protagonist:
                protagonist = f"女主角{female_name}，{protagonist}" if protagonist else f"女主角{female_name}"
            if "第一主角" not in protagonist:
                protagonist = f"（第一主角为女主）{protagonist}"

        parts.append(f"主角设定：{protagonist}")
        parts.append(f"故事背景：{context_data.get('setting', '')}")
        parts.append(f"核心剧情：{context_data.get('plot', '')}")
        if context_data.get('outline'):
            parts.append(f"分章大纲：{context_data.get('outline', '')}")

        parts.append("")

    if is_male_oriented:
        parts.append("【叙事视角】本作品为男频向，第一主角为男主，故事以其成长、冒险、事业为主线展开，侧重热血、升级、争霸或奇遇等元素。")
    else:
        parts.append("【叙事视角】本作品为女频向，第一主角为女主，故事以其情感、成长、人际关系为主线展开，侧重细腻情感、宫斗宅斗、甜宠或逆袭等元素。")
    parts.append("")

    if previous_summaries:
        parts.append("==========【前情提要】以下为已生成章节的关键信息，请仔细阅读以保证剧情连贯==========")
        for i, s in enumerate(previous_summaries, 1):
            parts.append(f"【第{i}章】{s[:250]}")
        parts.append("===================================================================")
        parts.append("")

    parts.append(f"【需要生成的章节】")
    parts.append(f"第{chapter_number}章：{chapter_title}")
    parts.append("")
    parts.append("要求：")
    parts.append(f"1. 字数控制在{word_count}字左右，上下浮动不超过200字")
    parts.append("2. 与已有章节的情节和人物性格保持连贯，不得出现前后矛盾")
    parts.append("3. 注意继承已有章节的伏笔和未解决的问题，在后续章节中适时推进")
    if chapter_number <= 3:
        parts.append("4. 【非常重要】前3章（黄金三章）是吸引读者的关键！开头必须在第一段内就抓住读者，要用强烈的冲突、悬念、危机感或震撼画面开篇。前三章必须环环相扣，节奏紧凑，快速建立主角形象和世界观核心魅力，让读者一读就放不下。")
    else:
        parts.append("4. 本章作为后续章节，需保持与前文的连贯性；结尾要有悬念或钩子，让读者想继续看下去")
    parts.append("5. 章节内容要有实质进展，不要注水")
    parts.append("6. 直接输出章节正文内容，不要加章节标题")

    if writing_style:
        parts.append("")
        parts.append(f"【文笔风格要求】")
        parts.append(writing_style)

    parts.append("")
    parts.append("请直接输出章节正文：")

    return "\n".join(parts)



def get_prompt(template_name: str, **kwargs) -> str:
    """获取指定模板的提示词

    Args:
        template_name: 模板名称
        **kwargs: 模板参数

    Returns:
        格式化后的提示词
    """
    templates = {
        "continue": CONTINUE_WRITING,
        "polish": POLISH_TEXT,
        "expand": EXPAND_TEXT,
        "summarize": SUMMARIZE_TEXT,
        "style_rewrite": STYLE_REWRITE,
        "check_spelling": CHECK_SPELLING,
        "generate_character": GENERATE_CHARACTER,
        "generate_outline": GENERATE_OUTLINE,
        "generate_titles": GENERATE_CHAPTER_TITLES,
        "generate_world": GENERATE_WORLD,
        "generate_dialogue": GENERATE_DIALOGUE,
        "sensitive_check": SENSITIVE_WORD_CHECK,
        "chapter_memory": CHAPTER_MEMORY_COMPRESS,
        "volume_memory": VOLUME_MEMORY_COMPRESS,
        "foreshadowing_extract": FORESHADOWING_EXTRACT,
        "auto_generate": AUTO_GENERATE_NOVEL,
        "auto_generate_from_outline": AUTO_GENERATE_FROM_OUTLINE,
        "scan_full_novel": SCAN_FULL_NOVEL,
    }

    template = templates.get(template_name)
    if not template:
        return ""

    import re
    needed = re.findall(r'\{(\w+)\}', template)
    full_kwargs = {k: kwargs.get(k, "") for k in needed}
    return template.format(**full_kwargs)