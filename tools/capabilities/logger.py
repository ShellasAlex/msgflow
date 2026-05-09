"""结构化 JSON 日志 — GitHub Actions 友好，与 Worker lib/log.js 格式一致"""
import logging
import json
import sys


class JsonFormatter(logging.Formatter):
    def format(self, record):
        entry = {
            "ts": round(record.created, 3),
            "level": record.levelname.lower(),
            "module": record.name.replace("msgflow.", ""),
            "msg": record.getMessage(),
        }
        extra = getattr(record, "extra", None)
        if extra:
            entry.update(extra)
        return json.dumps(entry, ensure_ascii=False)


_initialized = False


def get_logger(name: str) -> logging.Logger:
    """获取带 JSON 格式化的 logger，自动加 msgflow. 前缀"""
    global _initialized
    logger = logging.getLogger(f"msgflow.{name}")
    if not _initialized:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(JsonFormatter())
        root = logging.getLogger("msgflow")
        root.addHandler(handler)
        root.setLevel(logging.DEBUG)
        _initialized = True
    return logger
