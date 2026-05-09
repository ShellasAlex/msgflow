"""墨问发布封装"""
import os
import subprocess
from capabilities.logger import get_logger

log = get_logger("publisher")


def publish_to_mowen(file_path: str, tags: list[str] | None = None) -> bool:
    """调用 mowen-cli 发布文件，返回是否成功"""
    api_key = os.environ.get("MOWEN_API_KEY", "")
    if not api_key:
        log.warning("MOWEN_API_KEY not set")
        return False

    mowen = "/usr/local/bin/mowen-cli"
    if not os.path.isfile(mowen):
        log.warning("mowen-cli not found")
        return False

    cmd = [mowen, "create", file_path, "--auto-publish"]
    if tags:
        cmd.extend(["--tags", ",".join(tags)])

    try:
        env = {**os.environ, "MOWEN_API_KEY": api_key}
        result = subprocess.run(cmd, capture_output=True, timeout=60, env=env)
        if result.returncode == 0:
            log.info("published", extra={"file": file_path})
        else:
            log.error("publish failed", extra={"file": file_path, "stderr": result.stderr.decode()[:200]})
        return result.returncode == 0
    except (subprocess.TimeoutExpired, OSError) as e:
        log.error("publish error", extra={"error": str(e)})
        return False
