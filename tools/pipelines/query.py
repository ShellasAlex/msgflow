"""Pipeline: 基于 wiki 回答问题"""
from capabilities.ai_runner import run_skill


def execute(target: str, **kwargs) -> str:
    prompt = (
        f"请执行 Query 操作。问题：{target}。"
        f"先读 wiki/index.md 找相关页面，然后综合回答。"
        f"如果回答有价值，file back 回 wiki。"
    )
    result = run_skill("llmwiki-agent", prompt, timeout=300, workspace="llmwiki")
    return result or "错误：查询失败"
