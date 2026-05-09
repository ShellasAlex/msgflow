"""Pipeline: 知识库健康检查"""
from capabilities.ai_runner import run_skill


def execute(target: str = "full", **kwargs) -> str:
    prompt = (
        "请执行 Lint 操作。检查 wiki/ 目录的健康状况："
        "断链、孤立页面、index.md 与实际文件不一致、缺失的概念页。输出检查报告。"
    )
    result = run_skill("llmwiki-agent", prompt, timeout=300, workspace="llmwiki")
    return result or "错误：健康检查失败"
