"""Pipeline: 手动发布文件到墨问"""
from pathlib import Path
from capabilities.publisher import publish_to_mowen


def execute(target: str, **kwargs) -> str:
    if not Path(target).is_file():
        return f"错误：文件不存在 {target}"

    if publish_to_mowen(target, tags=["nullclaw"]):
        return f"✅ 已发布到墨问：{target}"
    return "❌ 发布失败，请检查 API Key 配置"
