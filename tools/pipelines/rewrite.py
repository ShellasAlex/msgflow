"""Pipeline: 抓取 → AI 改写 → 封面图 → 保存 → 发布（按配置的默认渠道）"""
import os
from pathlib import Path
from capabilities.content_fetcher import fetch
from capabilities.ai_runner import run_skill
from capabilities.cover import get_cover_url
from capabilities.publisher import publish_to_mowen
from capabilities.file_store import save
from capabilities.logger import get_logger

log = get_logger("rewrite")


def execute(target: str, style: str = "", **kwargs) -> str:
    log.info("rewrite start", extra={"target": target, "style": style})

    # 1. 获取原文
    if target.startswith("http"):
        article = fetch(target)
    else:
        p = Path(target)
        article = p.read_text(encoding="utf-8") if p.exists() else None

    if not article:
        log.error("fetch failed", extra={"target": target})
        return "错误：无法获取文章内容"

    log.info("article fetched", extra={"length": len(article)})

    # 2. AI 改写
    prompt = f"请用你的风格改写以下文章。只输出改写后的完整文章正文。原文如下：\n\n{article}"
    rewritten = run_skill(f"{style}-writer", prompt, timeout=300)
    if not rewritten:
        log.error("rewrite failed", extra={"style": style})
        return "错误：改写失败"

    log.info("rewrite done", extra={"length": len(rewritten)})

    # 3. 封面图
    cover = get_cover_url(rewritten)
    content = f"![cover]({cover})\n\n{rewritten}" if cover else rewritten

    # 4. 保存
    path = save(content, directory="rewritten", prefix=style)
    log.info("saved", extra={"path": path})

    # 5. 发布（按 publish_target 配置）
    publish_target = os.environ.get("PUBLISH_TARGET", "mowen")
    log.info("publishing", extra={"target": publish_target})

    if publish_target == "feishu":
        from pipelines.publish_feishu import execute as pub_feishu
        pub_result = pub_feishu(path)
    elif publish_target == "mowen":
        published = publish_to_mowen(path, tags=[style, "改写"])
        pub_result = "✅ 已发布到墨问" if published else ""
    elif publish_target == "none":
        pub_result = ""
    else:
        published = publish_to_mowen(path, tags=[style, "改写"])
        pub_result = "✅ 已发布到墨问" if published else ""

    result = content
    if pub_result:
        result += f"\n\n---\n{pub_result}"

    log.info("rewrite pipeline complete", extra={"publish": publish_target})
    return result
