"""Pipeline: 抓取 → AI 改写 → 封面图 → 保存 → 发布"""
from pathlib import Path
from capabilities.content_fetcher import fetch
from capabilities.ai_runner import run_skill
from capabilities.cover import get_cover_url
from capabilities.publisher import publish_to_mowen
from capabilities.file_store import save


def execute(target: str, style: str = "", **kwargs) -> str:
    # 1. 获取原文
    if target.startswith("http"):
        article = fetch(target)
    else:
        p = Path(target)
        article = p.read_text(encoding="utf-8") if p.exists() else None

    if not article:
        return "错误：无法获取文章内容"

    # 2. AI 改写
    prompt = f"请用你的风格改写以下文章。只输出改写后的完整文章正文。原文如下：\n\n{article}"
    rewritten = run_skill(f"{style}-writer", prompt, timeout=300)
    if not rewritten:
        return "错误：改写失败"

    # 3. 封面图
    cover = get_cover_url(rewritten)
    content = f"![cover]({cover})\n\n{rewritten}" if cover else rewritten

    # 4. 保存
    path = save(content, directory="rewritten", prefix=style)

    # 5. 发布
    published = publish_to_mowen(path, tags=[style, "改写"])

    result = content
    if published:
        result += "\n\n---\n✅ 已发布到墨问"
    return result
