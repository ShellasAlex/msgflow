"""Pipeline: 抓取 URL → 保存为 Markdown"""
from capabilities.content_fetcher import fetch
from capabilities.file_store import save_with_hash


def execute(target: str, **kwargs) -> str:
    content = fetch(target)
    if not content:
        return "错误：无法获取文章内容"

    save_with_hash(content, directory="articles")
    return content
