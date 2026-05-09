"""封面图获取：从文本提取关键词，搜索 Unsplash"""
import os
import json
import urllib.request
import urllib.parse

_KEYWORD_MAP = {
    "AI": "artificial intelligence", "Agent": "AI agent",
    "代码": "coding", "技术": "technology", "写作": "writing",
    "数据": "data", "分析": "analysis", "工具": "tools",
    "自动": "automation", "机器人": "robot", "模型": "model",
    "智能": "intelligence", "协作": "collaboration", "编程": "programming",
}


def get_cover_url(text: str) -> str | None:
    """从文章文本提取关键词，搜索 Unsplash 返回 16:9 封面图 URL"""
    api_key = os.environ.get("UNSPLASH_KEY", "")
    if not api_key:
        return None

    keywords = _extract_keywords(text[:500])
    return _search_unsplash(keywords, api_key)


def _extract_keywords(text: str) -> str:
    words = [v for k, v in _KEYWORD_MAP.items() if k in text]
    return "+".join(words[:3]) if words else "technology+digital"


def _search_unsplash(keywords: str, api_key: str) -> str | None:
    url = f"https://api.unsplash.com/search/photos?query={urllib.parse.quote(keywords)}&orientation=landscape&per_page=1"
    req = urllib.request.Request(url, headers={"Authorization": f"Client-ID {api_key}"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            results = data.get("results", [])
            if results:
                return results[0]["urls"]["regular"]
    except Exception:
        pass
    return None
