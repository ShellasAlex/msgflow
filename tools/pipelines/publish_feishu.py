"""Pipeline: 发布内容到飞书文档或知识库（CLI 优先，API 兜底）"""
import os
import subprocess
import sys
from pathlib import Path
from capabilities.logger import get_logger

log = get_logger("publish_feishu")


def execute(target: str, **kwargs) -> str:
    """
    target: 文档标题（从最近的结果文件读取内容）
            或文件路径（直接读取该文件发布）
    """
    log.info("publish_feishu start", extra={"target": target})

    # 确定内容来源
    content = _resolve_content(target)
    if not content:
        log.error("no content to publish", extra={"target": target})
        return "错误：没有可发布的内容。请先执行抓取或改写，或指定文件路径"

    title = _extract_title(content, target)
    log.info("content resolved", extra={"title": title, "length": len(content)})

    # 优先尝试 CLI 方式
    result = _try_cli(title, content)
    if result:
        return result

    # CLI 不可用时 fallback 到 API 方式
    log.info("cli unavailable, fallback to api")
    return _try_api(title, content)


def _try_cli(title: str, content: str) -> str | None:
    """尝试通过 lark-cli 发布"""
    try:
        from capabilities.feishu_cli import publish
        result = publish(title, content)
        if "失败" not in result:
            return result
        return None
    except Exception as e:
        log.warning("cli fallback", extra={"error": str(e)})
        return None


def _try_api(title: str, content: str) -> str:
    """通过 API 方式发布（原有逻辑）"""
    if not os.environ.get("FEISHU_APP_ID") or not os.environ.get("FEISHU_APP_SECRET"):
        log.error("feishu credentials missing")
        return "错误：未配置飞书凭据（FEISHU_APP_ID / FEISHU_APP_SECRET），且 lark-cli 不可用"

    script = Path(__file__).parent.parent / "capabilities" / "write_feishu.py"
    cmd = [sys.executable, str(script), "--title", title]

    wiki_space = os.environ.get("FEISHU_WIKI_SPACE")
    if wiki_space:
        cmd.extend(["--wiki-space", wiki_space])
        log.info("api: publishing to wiki", extra={"space": wiki_space})
    else:
        log.info("api: publishing to my space")

    try:
        result = subprocess.run(cmd, input=content, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            log.error("api write failed", extra={"stderr": result.stderr[:200]})
            return f"错误：发布失败 - {result.stderr[:200]}"

        url = result.stdout.strip()
        log.info("api publish success", extra={"url": url})
        return f"✅ 已发布到飞书\n{url}"

    except subprocess.TimeoutExpired:
        log.error("api write timeout")
        return "错误：发布超时"
    except Exception as e:
        log.error("api write exception", extra={"error": str(e)})
        return f"错误：{str(e)}"


def _resolve_content(target: str) -> str | None:
    """从文件路径或最近结果中获取内容"""
    p = Path(target)
    if p.exists() and p.is_file():
        log.info("reading from file", extra={"path": str(p)})
        return p.read_text(encoding="utf-8")

    result_file = Path("/tmp/result.txt")
    if result_file.exists() and result_file.stat().st_size > 0:
        log.info("reading from /tmp/result.txt")
        return result_file.read_text(encoding="utf-8")

    rewritten = Path("rewritten")
    if rewritten.exists():
        files = sorted(rewritten.glob("*.md"), key=lambda f: f.stat().st_mtime, reverse=True)
        if files:
            log.info("reading latest rewritten file", extra={"path": str(files[0])})
            return files[0].read_text(encoding="utf-8")

    return None


def _extract_title(content: str, fallback: str) -> str:
    """从 Markdown 内容提取标题"""
    for line in content.split("\n")[:10]:
        if line.startswith("# "):
            return line[2:].strip()
    return fallback
