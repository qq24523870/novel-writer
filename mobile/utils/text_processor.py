import re
from typing import List, Tuple


class TextProcessor:
    """文本处理工具类，提供各种文本处理功能"""

    @staticmethod
    def count_words(text: str) -> int:
        """统计中文字数和英文单词数

        Args:
            text: 要统计的文本

        Returns:
            总字数
        """
        if not text:
            return 0
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        english_words = len(re.findall(r'[a-zA-Z]+', text))
        numbers = len(re.findall(r'\d+', text))
        return chinese_chars + english_words + numbers

    @staticmethod
    def count_chinese_chars(text: str) -> int:
        """统计中文字符数"""
        if not text:
            return 0
        return len(re.findall(r'[\u4e00-\u9fff]', text))

    @staticmethod
    def count_paragraphs(text: str) -> int:
        """统计段落数"""
        if not text:
            return 0
        paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
        return len(paragraphs)

    @staticmethod
    def count_sentences(text: str) -> int:
        """统计句子数"""
        if not text:
            return 0
        sentences = re.split(r'[。！？.!?]', text)
        return len([s.strip() for s in sentences if s.strip()])

    @staticmethod
    def split_into_paragraphs(text: str) -> List[str]:
        """将文本分割成段落列表"""
        if not text:
            return []
        return [p.strip() for p in text.split('\n') if p.strip()]

    @staticmethod
    def check_spelling(text: str) -> List[Tuple[int, str, str]]:
        """基础错别字检查

        Returns:
            列表，每个元素为 (位置, 错误词, 建议词)
        """
        if not text:
            return []

        common_errors = {
            "的得": "的/得",
            "的地": "的/地",
            "在再": "在/再",
            "他她它": "他/她/它",
            "做作": "做/作",
            "那哪": "那/哪",
            "像向": "像/向",
            "坐座": "坐/座",
            "历厉": "历/厉",
            "决绝": "决/绝",
        }

        issues = []
        for i, char in enumerate(text):
            for error_pair, suggestion in common_errors.items():
                if char in error_pair:
                    context_start = max(0, i - 5)
                    context_end = min(len(text), i + 5)
                    context = text[context_start:context_end]
                    issues.append((i, char, suggestion, context))
                    break

        return issues

    @staticmethod
    def detect_sensitive_words(text: str, custom_words: List[str] = None) -> List[Tuple[int, str]]:
        """检测敏感词

        Args:
            text: 要检测的文本
            custom_words: 自定义敏感词列表

        Returns:
            列表，每个元素为 (位置, 敏感词)
        """
        sensitive_words = custom_words or []
        results = []
        for word in sensitive_words:
            for match in re.finditer(re.escape(word), text):
                results.append((match.start(), word))
        return results

    @staticmethod
    def format_word_count(count: int) -> str:
        """格式化字数显示

        Args:
            count: 字数

        Returns:
            格式化后的字符串，如 "1,234 字"
        """
        return f"{count:,} 字"

    @staticmethod
    def estimate_reading_time(text: str) -> int:
        """估算阅读时间（分钟）

        Args:
            text: 文本内容

        Returns:
            预计阅读分钟数
        """
        word_count = TextProcessor.count_words(text)
        reading_speed = 300
        minutes = max(1, word_count // reading_speed)
        return minutes

    @staticmethod
    def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
        """简单关键词提取（基于词频）

        Args:
            text: 文本内容
            max_keywords: 最大关键词数量

        Returns:
            关键词列表
        """
        words = re.findall(r'[\u4e00-\u9fff]{2,}', text)
        word_freq = {}
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in sorted_words[:max_keywords]]


text_processor = TextProcessor()