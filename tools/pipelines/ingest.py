"""Pipeline: 抓取 URL → 存入 raw → AI 生成 wiki 页面"""
from capabilities.content_fetcher import fetch
from capabilities.ai_runner import run_skill
from capabilities.file_store import save_with_hash


def execute(target: str, **kwargs) -> str:
    # 1. 抓取
    content = fetch(target)
    if not content:
        return "错误：无法抓取文章内容"

    # 2. 存入 raw
    raw_path = save_with_hash(content, directory="llmwiki/raw")

    # 3. AI 生成 wiki 页面
    prompt = (
        f"请执行 Ingest 操作。新素材文件：{raw_path}。"
        f"请读取素材，生成摘要页到 wiki/，更新 index.md 和 log.md。"
        f"只输出你创建/更新的文件列表和摘要内容。"
    )
    result = run_skill("llmwiki-agent", prompt, timeout=300, workspace="llmwiki")
    return result or "错误：wiki 生成失败"
