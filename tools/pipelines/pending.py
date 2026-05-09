"""Pipeline: 列出未发布的文件"""
import json
from pathlib import Path


def execute(**kwargs) -> str:
    published = _get_published_files()
    pending = []

    for f in sorted(Path("rewritten").glob("*.md")):
        if str(f) not in published:
            pending.append(f"• {f}")

    if not pending:
        return "所有文件都已发布，没有待发布的内容。"

    return "未发布的文件：\n" + "\n".join(pending) + "\n\n发送「发布 <文件路径>」上传指定文件"


def _get_published_files() -> set[str]:
    meta = Path(".mowen/metadata.json")
    if not meta.exists():
        return set()
    try:
        data = json.loads(meta.read_text())
        items = data if isinstance(data, list) else data.get("files", [])
        return {item.get("path") or item.get("file_path", "") for item in items}
    except (json.JSONDecodeError, KeyError):
        return set()
