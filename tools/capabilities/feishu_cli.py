"""飞书 CLI 封装 — 通过 lark-cli 操作飞书（文档、知识库、消息等）"""
import subprocess
import json
import os
from capabilities.logger import get_logger

log = get_logger("feishu_cli")


def _run(args: list[str], input_text: str = None, timeout: int = 30) -> dict:
    """执行 lark-cli 命令，返回 {ok, data, error}"""
    cmd = ["lark-cli"] + args + ["--output", "json"]
    log.info("exec", extra={"cmd": " ".join(cmd[:6])})
    try:
        result = subprocess.run(cmd, input=input_text, capture_output=True, text=True, timeout=timeout)
        if result.returncode != 0:
            log.error("cli failed", extra={"code": result.returncode, "stderr": result.stderr[:200]})
            return {"ok": False, "data": None, "error": result.stderr[:200]}
        data = json.loads(result.stdout) if result.stdout.strip() else {}
        log.info("cli ok", extra={"args": args[:3]})
        return {"ok": True, "data": data, "error": None}
    except subprocess.TimeoutExpired:
        log.error("cli timeout", extra={"timeout": timeout})
        return {"ok": False, "data": None, "error": "超时"}
    except json.JSONDecodeError:
        # 有些命令输出不是 JSON
        return {"ok": True, "data": result.stdout.strip(), "error": None}
    except FileNotFoundError:
        log.error("lark-cli not installed")
        return {"ok": False, "data": None, "error": "lark-cli 未安装，请执行 npm install -g @larksuite/cli"}


# === 文档操作 ===

def doc_create(title: str, markdown: str, folder_token: str = None) -> str | None:
    """创建飞书文档，返回文档 URL"""
    args = ["docs", "+create", "--title", title, "--markdown", markdown]
    if folder_token:
        args.extend(["--folder-token", folder_token])
    r = _run(args, timeout=15)
    if r["ok"] and isinstance(r["data"], dict):
        url = r["data"].get("url") or r["data"].get("document_url")
        log.info("doc created", extra={"url": url})
        return url
    # fallback: 输出可能直接是 URL
    if r["ok"] and isinstance(r["data"], str) and "feishu" in r["data"]:
        return r["data"]
    log.error("doc_create failed", extra={"error": r["error"]})
    return None


def doc_read(url_or_token: str) -> str | None:
    """读取飞书文档为 Markdown"""
    args = ["docs", "+read", url_or_token]
    r = _run(args, timeout=15)
    if r["ok"]:
        if isinstance(r["data"], dict):
            return r["data"].get("markdown") or r["data"].get("content")
        return r["data"] if r["data"] else None
    log.error("doc_read failed", extra={"error": r["error"]})
    return None


# === 知识库操作 ===

def wiki_create(title: str, markdown: str, space_id: str, parent_node: str = None) -> str | None:
    """在知识库创建页面，返回 URL"""
    args = ["wiki", "+create", "--space-id", space_id, "--title", title, "--markdown", markdown]
    if parent_node:
        args.extend(["--parent-node-token", parent_node])
    r = _run(args, timeout=15)
    if r["ok"]:
        if isinstance(r["data"], dict):
            return r["data"].get("url") or r["data"].get("node_url")
        if isinstance(r["data"], str) and "feishu" in r["data"]:
            return r["data"]
    log.error("wiki_create failed", extra={"error": r["error"]})
    return None


def wiki_list_spaces() -> list[dict]:
    """列出有权限的知识库"""
    r = _run(["wiki", "+list-spaces"])
    if r["ok"] and isinstance(r["data"], dict):
        return r["data"].get("items") or r["data"].get("spaces") or []
    if r["ok"] and isinstance(r["data"], list):
        return r["data"]
    return []


# === 消息操作 ===

def send_message(chat_id: str, text: str) -> bool:
    """发送文本消息到群聊"""
    args = ["im", "+messages-send", "--chat-id", chat_id, "--text", text]
    r = _run(args, timeout=10)
    if r["ok"]:
        log.info("message sent", extra={"chat_id": chat_id[:10]})
    return r["ok"]


# === 通用发布入口 ===

def publish(title: str, markdown: str, wiki_space: str = None, parent_node: str = None) -> str:
    """发布 Markdown 到飞书（知识库或我的空间），返回结果描述"""
    wiki_space = wiki_space or os.environ.get("FEISHU_WIKI_SPACE")
    log.info("publish start", extra={"title": title, "wiki_space": wiki_space or "my_space"})

    if wiki_space:
        url = wiki_create(title, markdown, wiki_space, parent_node)
    else:
        url = doc_create(title, markdown)

    if url:
        log.info("publish success", extra={"url": url})
        return f"✅ 已发布到飞书\n{url}"
    else:
        log.error("publish failed")
        return "❌ 发布到飞书失败，请检查 lark-cli 配置和权限"
