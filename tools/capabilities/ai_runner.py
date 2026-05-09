"""NullClaw AI 调用封装"""
import subprocess
from capabilities.logger import get_logger

log = get_logger("ai")


def run_skill(skill_name: str, prompt: str, timeout: int = 300, workspace: str | None = None) -> str | None:
    """调用 NullClaw agent with skill，返回输出文本"""
    log.info("run_skill", extra={"skill": skill_name, "timeout": timeout})
    cmd = ["nullclaw", "agent", "--skill", skill_name, "-m", prompt]
    if workspace:
        cmd.extend(["--workspace", workspace])
    return _run(cmd, timeout)


def run_prompt(prompt: str, timeout: int = 300) -> str | None:
    """无 skill 的纯 prompt 调用"""
    log.info("run_prompt", extra={"timeout": timeout})
    cmd = ["nullclaw", "agent", "-m", prompt]
    return _run(cmd, timeout)


def _run(cmd: list[str], timeout: int) -> str | None:
    """执行命令，返回 stdout 或 None"""
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout
        )
        output = result.stdout.strip()
        if output:
            log.info("ai complete", extra={"length": len(output)})
        else:
            log.warning("ai returned empty", extra={"stderr": result.stderr[:200]})
        return output if output else None
    except subprocess.TimeoutExpired:
        log.error("ai timeout", extra={"timeout": timeout})
        return None
    except OSError as e:
        log.error("ai exec failed", extra={"error": str(e)})
        return None
