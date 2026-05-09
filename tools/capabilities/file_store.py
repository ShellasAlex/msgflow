"""文件存储：保存内容到文件，自动创建目录和生成文件名"""
import hashlib
from datetime import datetime
from pathlib import Path


def save(content: str, directory: str, prefix: str = "", suffix: str = ".md") -> str:
    """保存内容到文件，返回文件路径"""
    Path(directory).mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    name = f"{prefix}-{timestamp}" if prefix else timestamp
    path = Path(directory) / f"{name}{suffix}"
    path.write_text(content, encoding="utf-8")
    return str(path)


def save_with_hash(content: str, directory: str, prefix: str = "fetched") -> str:
    """用内容 hash 命名（适合去重场景），返回文件路径"""
    Path(directory).mkdir(parents=True, exist_ok=True)
    h = hashlib.md5(content.encode()).hexdigest()[:8]
    path = Path(directory) / f"{prefix}-{h}.md"
    path.write_text(content, encoding="utf-8")
    return str(path)
