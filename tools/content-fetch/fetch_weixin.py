#!/usr/bin/env python3
"""Fetch WeChat (公众号) article as Markdown. Uses Playwright + markdownify."""

import sys
import json
import asyncio
import re
from pathlib import Path


def slugify_filename(value: str, fallback: str = "wechat-article") -> str:
    cleaned = re.sub(r"[\\/:*?\"<>|]+", "-", value or "")
    cleaned = re.sub(r"\s+", " ", cleaned).strip().strip(".")
    return cleaned or fallback


async def fetch_weixin_article(url: str) -> dict:
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        return {"error": "playwright not installed. Run: pip install playwright; python -m playwright install chromium"}

    try:
        from bs4 import BeautifulSoup
    except ImportError:
        return {"error": "beautifulsoup4 not installed. Run: pip install beautifulsoup4 lxml"}

    try:
        from markdownify import markdownify as md
    except ImportError:
        return {"error": "markdownify not installed. Run: pip install markdownify"}

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_selector("#js_content", timeout=15000)
            html = await page.content()
        except Exception as e:
            await browser.close()
            return {"error": f"Failed to load page: {e}"}
        await browser.close()

    soup = BeautifulSoup(html, "lxml")

    title_el = soup.select_one("#activity-name")
    title = title_el.get_text(strip=True) if title_el else ""

    author_el = soup.select_one("#js_author_name") or soup.select_one(".rich_media_meta_text")
    author = author_el.get_text(strip=True) if author_el else ""

    time_el = soup.select_one("#publish_time")
    publish_time = time_el.get_text(strip=True) if time_el else ""

    content_el = soup.select_one("#js_content")
    if not content_el:
        return {"error": "Could not find article content (#js_content)"}

    # 清理无用标签
    for tag in content_el.find_all(["script", "style"]):
        tag.decompose()

    # 处理图片 data-src → src
    for img in content_el.find_all("img"):
        src = img.get("data-src") or img.get("src") or ""
        if src:
            img["src"] = src
        else:
            img.decompose()

    # 用 markdownify 转换
    content = md(
        str(content_el),
        heading_style="ATX",
        code_language="",
    )

    # 清理多余空行
    content = re.sub(r"\n{3,}", "\n\n", content).strip()

    return {"title": title, "author": author, "publish_time": publish_time, "content": content, "url": url}


def format_as_markdown(result: dict) -> str:
    if "error" in result:
        return f"Error: {result['error']}"

    parts = ["---"]
    if result.get("title"):
        parts.append(f'title: "{result["title"]}"')
    if result.get("author"):
        parts.append(f'author: "{result["author"]}"')
    if result.get("publish_time"):
        parts.append(f'date: "{result["publish_time"]}"')
    parts.append(f'url: "{result["url"]}"')
    parts.append("---")
    parts.append("")
    if result.get("title"):
        parts.append(f"# {result['title']}")
        parts.append("")
    parts.append(result.get("content", ""))
    return "\n".join(parts)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: fetch_weixin.py <url> [--json] [--output-dir DIR]", file=sys.stderr)
        sys.exit(1)

    url = sys.argv[1]
    use_json = "--json" in sys.argv
    output_dir = None
    if "--output-dir" in sys.argv:
        idx = sys.argv.index("--output-dir")
        if idx + 1 >= len(sys.argv):
            print("--output-dir requires a value", file=sys.stderr)
            sys.exit(1)
        output_dir = Path(sys.argv[idx + 1])

    result = asyncio.run(fetch_weixin_article(url))

    if "error" in result:
        print(result["error"], file=sys.stderr)
        sys.exit(1)

    if output_dir is not None:
        output_dir.mkdir(parents=True, exist_ok=True)
        filename = slugify_filename(result.get("title", "")) + ".md"
        output_path = output_dir / filename
        output_path.write_text(format_as_markdown(result), encoding="utf-8")
        print(str(output_path))
    elif use_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(format_as_markdown(result))
