"""帮助系统 - AI小说创作助手使用指南"""
from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QLabel, QPushButton, QTreeWidget, QTreeWidgetItem, QTextBrowser,
    QSplitter, QFrame, QScrollArea, QDialogButtonBox
)
from PySide6.QtGui import QFont, QPixmap

HELP_CONTENT = {
    "welcome": {
        "title": "欢迎使用 AI小说创作助手",
        "content": """<h2>AI小说创作助手 v1.0.0</h2>
<hr>
<p>欢迎！这是一款专业的AI辅助小说创作工具，帮助你完成从灵感到成品的全过程。</p>

<h3>核心功能一览</h3>
<ul>
<li><b>专业编辑器</b> - 支持行号、查找替换、字数统计</li>
<li><b>AI辅助创作</b> - 续写、润色、扩写、缩写、风格改写</li>
<li><b>项目管理</b> - 分卷分章、人物卡片、世界观设定、时间线</li>
<li><b>多种导出</b> - 支持TXT、Markdown、Word格式</li>
<li><b>多主题</b> - 浅色、深色、护眼模式自由切换</li>
<li><b>自动保存</b> - 再也不用担心丢失内容</li>
</ul>

<h3>界面布局</h3>
<p><b>左侧</b>：侧边栏（大纲/人物/世界观）<br>
<b>中间</b>：编辑器（写作区域）<br>
<b>右侧</b>：AI面板（剧情顾问/快捷操作）<br>
<b>顶部</b>：菜单栏 + 工具栏<br>
<b>底部</b>：状态栏（字数/行号/AI状态）</p>"""
    },
    "project": {
        "title": "项目管理",
        "content": """<h2>📁 项目管理</h2>
<hr>

<h3>新建项目</h3>
<p><b>操作</b>：菜单栏 → 文件 → 新建项目（快捷键：Ctrl+N）<br>
在弹出的对话框中填写小说名称、作者、类型、简介和字数目标。</p>

<h3>打开项目</h3>
<p><b>操作</b>：菜单栏 → 文件 → 打开项目（快捷键：Ctrl+O）<br>
从列表中选择已有项目打开。</p>

<h3>分卷管理</h3>
<p>在左侧「大纲」面板中：<br>
• <b>新建卷</b>：点击面板顶部的「+卷」按钮<br>
• <b>重命名</b>：双击卷名称<br>
• <b>删除</b>：右键 → 删除卷<br>
• 卷是用来组织章节的大型分组，比如「第一卷：初出茅庐」</p>

<h3>章节管理</h3>
<p>在左侧「大纲」面板中：<br>
• <b>新建章节</b>：先选中一个卷，再点「+章」<br>
• <b>打开章节</b>：单击章节名称即可在编辑器中打开<br>
• <b>重命名</b>：双击章节名称<br>
• <b>删除</b>：右键 → 删除章节<br>
• 章节标题会显示字数统计（如：第一章 (1234字)）</p>

<h3>保存</h3>
<p>• <b>手动保存</b>：Ctrl+S 或 菜单 → 文件 → 保存<br>
• <b>自动保存</b>：每30秒自动保存当前章节（可在设置中调整间隔）<br>
• 状态栏会显示「已保存」提示</p>"""
    },
    "editor": {
        "title": "编辑器使用",
        "content": """<h2>✍️ 编辑器使用指南</h2>
<hr>

<h3>基本操作</h3>
<p>• 在编辑器区域直接输入文字<br>
• 左侧显示行号，方便定位<br>
• 底部状态栏显示当前光标位置（行号:列号）<br>
• Ctrl+滚轮可快速调整字体大小</p>

<h3>查找和替换</h3>
<p><b>查找</b>：Ctrl+F — 在编辑器顶部出现查找栏<br>
<b>替换</b>：Ctrl+H — 查找替换同时显示<br>
• 支持区分大小写<br>
• 支持正则表达式搜索<br>
• 点击「全部替换」可一键替换所有匹配项</p>

<h3>字数统计</h3>
<p>编辑器每2秒自动更新字数统计，显示在状态栏右侧：<br>
• 总字数（包含中文+英文+数字）<br>
• 光标所在行和列</p>

<h3>右键菜单</h3>
<p>在编辑器内右键弹出菜单：<br>
• 剪切/复制/粘贴（标准操作）<br>
• <b>AI辅助菜单</b>（选中文本后出现）<br>
&nbsp;&nbsp;- 一键续写<br>
&nbsp;&nbsp;- 智能润色<br>
&nbsp;&nbsp;- 内容扩写/缩写<br>
&nbsp;&nbsp;- 风格改写<br>
&nbsp;&nbsp;- 错别字检查</p>

<h3>文本格式化</h3>
<p>工具栏提供快捷格式化按钮：<br>
• <b>B</b> - 粗体（Ctrl+B）<br>
• <b>I</b> - 斜体（Ctrl+I）<br>
• <b>U</b> - 下划线（Ctrl+U）</p>"""
    },
    "ai": {
        "title": "AI辅助创作",
        "content": """<h2>🤖 AI辅助创作</h2>
<hr>

<h3>配置AI模型</h3>
<p><b>操作</b>：菜单栏 → 工具 → 设置 → AI模型标签<br>
支持以下AI提供商：<br>
• <b>OpenAI</b> (GPT-3.5/GPT-4/GPT-4o) — 需要API密钥<br>
• <b>百度文心一言</b> — 需要API Key和Secret Key<br>
• <b>阿里通义千问</b> — 需要API密钥<br>
• <b>自定义接口</b> — 支持任意OpenAI兼容的API服务，自由配置地址和模型<br>
• <b>硅基流动 (SiliconFlow)</b> — preset接口，支持DeepSeek/Qwen等热门模型<br>
• <b>深度求索 (DeepSeek)</b> — preset接口，支持deepseek-chat/reasoner<br>
• <b>本地大模型</b> — 需要GGUF格式模型文件（llama-cpp-python）<br>
<font color='red'>注意：使用AI功能前必须先配置并启用至少一个模型。</font></p>

<h3>自定义接口使用说明</h3>
<p>如果你使用的是第三方API服务（如 OneAPI、LiteLLM 等），请在设置中选择「自定义接口」：<br>
1. 勾选「启用」<br>
2. 填写API密钥<br>
3. 填写完整的API地址（必须以 /v1 结尾）<br>
4. 填写模型名称</p>

<h3>硅基流动 (SiliconFlow)</h3>
<p>国内知名的模型服务平台，提供多种开源模型API：<br>
• 官网：<a href='https://siliconflow.cn'>https://siliconflow.cn</a><br>
• 注册后获取API密钥<br>
• 支持 DeepSeek-V3/R1、Qwen2.5系列、GLM-4 等模型</p>

<h3>深度求索 (DeepSeek)</h3>
<p>DeepSeek官方API：<br>
• 官网：<a href='https://deepseek.com'>https://deepseek.com</a><br>
• deepseek-chat：通用对话模型<br>
• deepseek-reasoner：推理模型（适合复杂逻辑）</p>

<h3>AI写作功能</h3>
<p>选中文本后，可通过以下方式调用AI：<br>
<b>方式一</b>：右键 → AI辅助 → 选择功能<br>
<b>方式二</b>：菜单栏 → AI → 选择功能<br>
<b>方式三</b>：右侧AI面板 → 快捷操作 → 点击按钮</p>

<p><b>可用功能</b>：<br>
1. <b>一键续写</b> — 根据当前内容继续写作（可选100/300/500/1000字）<br>
2. <b>智能润色</b> — 优化语句通顺度和文采（可选轻度/中度/重度）<br>
3. <b>内容扩写</b> — 增加细节描写、心理活动、环境氛围<br>
4. <b>内容缩写</b> — 精简为核心内容<br>
5. <b>风格改写</b> — 改为古风/现代/科幻/悬疑/言情/奇幻/武侠风格<br>
6. <b>错别字检查</b> — 检测文本中的错别字和语法错误</p>

<h3>AI生成功能</h3>
<p>菜单栏 → AI → 生成：<br>
• <b>生成人物设定</b> — 输入关键词生成完整人物卡片<br>
• <b>生成剧情大纲</b> — 输入主题和设定生成大纲<br>
• <b>生成章节标题</b> — 根据内容生成吸引人的标题<br>
• <b>生成世界观</b> — 构建完整的虚构世界观<br>
• <b>敏感词检测</b> — 检测文本中的敏感内容</p>

<h3>AI剧情顾问</h3>
<p>右侧面板 → 「剧情顾问」标签 → 输入问题交流<br>
可以讨论剧情走向、解决卡文问题、分析人物关系等。</p>"""
    },
    "characters": {
        "title": "人物与世界观",
        "content": """<h2>👥 人物卡片与世界观</h2>
<hr>

<h3>人物卡片</h3>
<p><b>打开</b>：左侧侧边栏 → 点击「人物」标签<br>
<b>新建人物</b>：点击「+人物」按钮，输入姓名<br>
<b>编辑详情</b>：双击列表中的人物，弹出编辑对话框<br>
<b>编辑内容</b>：姓名、性别、年龄、外貌、性格、背景、口头禅<br>
<b>删除</b>：右键 → 删除（确认后移入回收站）</p>

<p><b>使用建议</b>：为每个主要角色创建详细的人物卡片，<br>
包括外貌特征、性格特点、背景故事等。<br>
写作时可以随时参考，确保角色形象一致。</p>

<h3>世界观设定</h3>
<p><b>打开</b>：左侧侧边栏 → 点击「世界观」标签<br>
<b>新建设定</b>：点击「+设定」按钮<br>
<b>分类选择</b>：地理、历史、种族、势力、物品、规则、魔法、科技、文化、其他<br>
<b>编辑</b>：双击设定条目修改详细内容<br>
<b>删除</b>：右键 → 删除</p>

<p><b>使用建议</b>：构建完整的世界观有助于保持故事一致性。<br>
特别是奇幻、科幻类小说，详细的世界观设定是优秀作品的基础。</p>"""
    },
    "export": {
        "title": "导出与备份",
        "content": """<h2>💾 导出与备份</h2>
<hr>

<h3>导出小说</h3>
<p><b>操作</b>：菜单栏 → 文件 → 导出 → 选择格式<br>
支持三种格式：<br>
• <b>TXT</b> — 纯文本格式，兼容性最好<br>
• <b>Markdown</b> — 带标题标记，适合后续排版<br>
• <b>Word (DOCX)</b> — 带格式的文档，可直接打印</p>
<p>导出时会包含所有卷和章节，按顺序排列。</p>

<h3>备份管理</h3>
<p><b>操作</b>：菜单栏 → 工具 → 备份管理<br>
• <b>创建备份</b>：将当前数据库打包为ZIP文件<br>
• <b>查看备份</b>：列出所有备份文件及大小<br>
• <b>恢复备份</b>：从备份文件恢复数据<br>
• <b>自动备份</b>：可在设置中开启（默认每5分钟）</p>

<h3>回收站</h3>
<p><b>操作</b>：菜单栏 → 工具 → 回收站<br>
• 删除的项目/卷/章节/人物会移入回收站<br>
• 可以恢复或永久删除<br>
• 清空回收站释放空间</p>"""
    },
    "settings": {
        "title": "个性化设置",
        "content": """<h2>⚙️ 个性化设置</h2>
<hr>

<h3>打开设置</h3>
<p><b>操作</b>：菜单栏 → 工具 → 设置（快捷键：Ctrl+,）</p>

<h3>AI模型设置</h3>
<p>配置AI提供商：<br>
• 填写API密钥后记得勾选「启用」<br>
• 点击「确定」保存设置<br>
• AI面板会自动刷新可用模型列表</p>

<h3>编辑器设置</h3>
<p>• <b>字体</b> — 选择写作字体（推荐：微软雅黑、宋体）<br>
• <b>字号</b> — 14-16pt最适合作文<br>
• <b>自动保存间隔</b> — 默认30秒<br>
• <b>Tab宽度</b> — 默认4个空格<br>
• <b>自动换行</b> — 建议开启<br>
• <b>显示行号</b> — 建议开启</p>

<h3>写作设置</h3>
<p>• <b>每日字数目标</b> — 设定每日写作目标，激励自己<br>
• <b>打字音效</b> — 开启后有打字声音（需系统音频支持）<br>
• <b>自动备份</b> — 建议开启，防止数据丢失</p>

<h3>主题切换</h3>
<p><b>操作</b>：菜单栏 → 视图 → 主题 → 选择<br>
• <b>浅色模式</b> — 适合白天写作<br>
• <b>深色模式</b> — 适合夜间写作<br>
• <b>护眼模式</b> — 柔和的绿色调，保护视力</p>

<h3>专注模式</h3>
<p><b>快捷键</b>：Ctrl+Shift+F<br>
隐藏侧边栏、AI面板、菜单栏和状态栏，<br>
让写作区域占据整个窗口，减少干扰。</p>"""
    },
    "shortcuts": {
        "title": "快捷键大全",
        "content": """<h2>⌨️ 快捷键大全</h2>
<hr>

<table border='1' cellpadding='6' cellspacing='0' width='100%'>
<tr><th>操作</th><th>快捷键</th></tr>
<tr><td>新建项目</td><td><b>Ctrl+N</b></td></tr>
<tr><td>打开项目</td><td><b>Ctrl+O</b></td></tr>
<tr><td>保存</td><td><b>Ctrl+S</b></td></tr>
<tr><td>查找</td><td><b>Ctrl+F</b></td></tr>
<tr><td>替换</td><td><b>Ctrl+H</b></td></tr>
<tr><td>撤销</td><td><b>Ctrl+Z</b></td></tr>
<tr><td>重做</td><td><b>Ctrl+Y</b></td></tr>
<tr><td>粗体</td><td><b>Ctrl+B</b></td></tr>
<tr><td>斜体</td><td><b>Ctrl+I</b></td></tr>
<tr><td>下划线</td><td><b>Ctrl+U</b></td></tr>
<tr><td>AI续写</td><td><b>Ctrl+E</b></td></tr>
<tr><td>AI润色</td><td><b>Ctrl+R</b></td></tr>
<tr><td>切换侧边栏</td><td><b>Ctrl+\\</b></td></tr>
<tr><td>切换AI面板</td><td><b>Ctrl+Shift+A</b></td></tr>
<tr><td>专注模式</td><td><b>Ctrl+Shift+F</b></td></tr>
<tr><td>全屏</td><td><b>F11</b></td></tr>
<tr><td>设置</td><td><b>Ctrl+,</b></td></tr>
<tr><td>退出</td><td><b>Ctrl+Q</b></td></tr>
</table>"""
    }
}


class HelpDialog(QDialog):
    """帮助对话框 - 包含完整的使用指南"""

    def __init__(self, parent=None, section="welcome"):
        super().__init__(parent)
        self.setWindowTitle("AI小说创作助手 - 使用指南")
        self.setMinimumSize(800, 600)
        self.resize(900, 700)
        self.setup_ui(section)

    def setup_ui(self, initial_section):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Horizontal)

        nav_panel = QWidget()
        nav_layout = QVBoxLayout(nav_panel)
        nav_layout.setContentsMargins(8, 8, 8, 8)

        nav_title = QLabel("📖 使用指南")
        nav_title_font = QFont()
        nav_title_font.setPointSize(14)
        nav_title_font.setBold(True)
        nav_title.setFont(nav_title_font)
        nav_layout.addWidget(nav_title)

        nav_layout.addWidget(QLabel("<small>点击分类查看详细说明</small>"))

        self._nav_tree = QTreeWidget()
        self._nav_tree.setHeaderHidden(True)
        self._nav_tree.setIndentation(12)
        self._nav_tree.setMinimumWidth(180)
        self._nav_tree.itemClicked.connect(self.on_nav_clicked)

        section_keys = ["welcome", "project", "editor", "ai", "characters", "export", "settings", "shortcuts"]
        section_icons = ["🏠", "📁", "✍️", "🤖", "👥", "💾", "⚙️", "⌨️"]
        section_names = ["欢迎使用", "项目管理", "编辑器使用", "AI辅助创作", "人物与世界观", "导出与备份", "个性化设置", "快捷键大全"]

        self._section_map = {}
        for key, icon, name in zip(section_keys, section_icons, section_names):
            item = QTreeWidgetItem([f"{icon} {name}"])
            item.setData(0, Qt.UserRole, key)
            self._nav_tree.addTopLevelItem(item)
            self._section_map[key] = item

        nav_layout.addWidget(self._nav_tree)
        splitter.addWidget(nav_panel)

        self._content_browser = QTextBrowser()
        self._content_browser.setOpenExternalLinks(True)
        self._content_browser.setMinimumWidth(500)
        splitter.addWidget(self._content_browser)

        splitter.setSizes([200, 600])
        layout.addWidget(splitter)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        close_btn = QPushButton("关闭")
        close_btn.setFixedWidth(100)
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

        if initial_section in self._section_map:
            self._nav_tree.setCurrentItem(self._section_map[initial_section])
            self.show_help(initial_section)
        else:
            self.show_help("welcome")

    def on_nav_clicked(self, item, column):
        section = item.data(0, Qt.UserRole)
        if section:
            self.show_help(section)

    def show_help(self, section):
        if section in HELP_CONTENT:
            html = f"""<html><body style='font-family: "Microsoft YaHei", sans-serif; padding: 20px;'>
{HELP_CONTENT[section]["content"]}
</body></html>"""
            self._content_browser.setHtml(html)
            self._content_browser.verticalScrollBar().setValue(0)


class TutorialDialog(QDialog):
    """新手引导对话框 - 第一次使用时的快速引导"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("欢迎使用 AI小说创作助手")
        self.setMinimumSize(650, 500)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        title = QLabel("🎉 欢迎使用 AI小说创作助手！")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel("一款专业的AI辅助小说创作工具，帮你从灵感到成品。")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #666; font-size: 14px;")
        layout.addWidget(subtitle)

        layout.addSpacing(12)

        steps = [
            ("📁 第一步：创建或打开项目",
             "点击菜单栏「文件 → 新建项目」，填写小说信息。\n"
             "你也可以打开演示项目「第七层梦境」来浏览样例。"),
            ("📝 第二步：开始写作",
             "在左侧「大纲」面板选择章节，\n"
             "在中间编辑器区域开始写作。Ctrl+S 随时保存。"),
            ("🤖 第三步：使用AI辅助",
             "选中文本→右键→AI辅助，或使用右侧AI面板。\n"
             "首次使用需在「设置」中配置AI模型（如OpenAI）。"),
            ("👥 第四步：管理人物和世界观",
             "在左侧面板切换到「人物」或「世界观」标签，\n"
             "创建和管理你的故事元素。"),
            ("💾 第五步：导出和备份",
             "写作完成后，通过「文件→导出」保存作品。\n"
             "定期备份以防数据丢失。")
        ]

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        steps_widget = QWidget()
        steps_layout = QVBoxLayout(steps_widget)
        steps_layout.setSpacing(12)

        for title_text, desc in steps:
            step_frame = QFrame()
            step_frame.setStyleSheet(
                "QFrame { background-color: #F8F9FA; border: 1px solid #E0E0E0; border-radius: 8px; padding: 12px; }"
            )
            step_layout = QVBoxLayout(step_frame)
            step_layout.setSpacing(4)
            step_title = QLabel(title_text)
            step_title_font = QFont()
            step_title_font.setPointSize(12)
            step_title_font.setBold(True)
            step_title.setFont(step_title_font)
            step_layout.addWidget(step_title)
            step_desc = QLabel(desc)
            step_desc.setWordWrap(True)
            step_desc.setStyleSheet("color: #555; font-size: 13px; line-height: 1.6;")
            step_layout.addWidget(step_desc)
            steps_layout.addWidget(step_frame)

        scroll.setWidget(steps_widget)
        layout.addWidget(scroll, 1)

        layout.addSpacing(12)

        tip = QLabel("💡 提示：帮助菜单中有详细的使用指南，随时可以查看。")
        tip.setStyleSheet("color: #4A90D9; font-size: 13px; font-style: italic;")
        tip.setAlignment(Qt.AlignCenter)
        layout.addWidget(tip)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        open_sample_btn = QPushButton("📂 打开样例项目")
        open_sample_btn.setFixedWidth(160)
        open_sample_btn.clicked.connect(self.accept)
        btn_layout.addWidget(open_sample_btn)

        got_it_btn = QPushButton("我知道了，开始使用 →")
        got_it_btn.setFixedWidth(200)
        got_it_btn.setStyleSheet(
            "QPushButton { background-color: #4A90D9; color: white; font-weight: bold; "
            "border-radius: 6px; padding: 10px 24px; font-size: 14px; }"
            "QPushButton:hover { background-color: #357ABD; }"
        )
        got_it_btn.clicked.connect(self.accept)
        btn_layout.addWidget(got_it_btn)
        layout.addLayout(btn_layout)
