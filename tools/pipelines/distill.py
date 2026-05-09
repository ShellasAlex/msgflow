"""Pipeline: AI 蒸馏人物 → 生成 writer skill"""
import glob
import re
from pathlib import Path
from capabilities.ai_runner import run_skill

# 特殊人物名映射（优先覆盖，处理连读/别名）
_NAME_MAP = {
    "苏东坡": "su-dongpo", "苏轼": "su-shi",
    "马三立": "ma-sanli", "徐志摩": "xu-zhimo",
    "老舍": "lao-she",
}


def execute(target: str, **kwargs) -> str:
    name = target.strip().strip("<>")
    slug = _get_slug(name)
    target_dir = Path(f"skills/writers/{slug}-writer")

    # 调用女娲蒸馏
    prompt = (
        f"请蒸馏：{name}。按女娲流程执行，"
        f"生成的 SKILL.md 保存到 skills/writers/{slug}-writer/ 目录下。"
        f"注意：生成的是一个 writer skill，用于改写文章，name 字段必须是 {slug}-writer。"
    )
    result = run_skill("nuwa-skill", prompt, timeout=600)

    # 兜底：NullClaw 可能忽略路径指令，找到文件移到正确位置
    if not (target_dir / "SKILL.md").exists():
        found = _find_generated_skill(name, slug)
        if found:
            target_dir.mkdir(parents=True, exist_ok=True)
            (target_dir / "SKILL.md").write_text(
                Path(found).read_text(encoding="utf-8"), encoding="utf-8"
            )

    return result or "错误：蒸馏失败"


def _get_slug(name: str) -> str:
    """中文名转拼音 slug，优先用映射表"""
    if name in _NAME_MAP:
        return _NAME_MAP[name]
    try:
        from pypinyin import lazy_pinyin
        return "-".join(lazy_pinyin(name))
    except ImportError:
        # fallback: 保留 ASCII，中文用连字符连接
        return re.sub(r"[^a-z0-9-]", "", name.lower().replace(" ", "-")) or "unknown"


def _find_generated_skill(name: str, slug: str) -> str | None:
    """搜索 NullClaw 可能输出的位置"""
    patterns = [
        f"./**/*{name}*/SKILL.md",
        f"./**/*{slug}*/SKILL.md",
        f"./llmwiki/.agents/skills/*/SKILL.md",
    ]
    for pattern in patterns:
        matches = glob.glob(pattern, recursive=True)
        for m in matches:
            if f"skills/writers/{slug}-writer" not in m and ".git" not in m:
                return m
    return None
