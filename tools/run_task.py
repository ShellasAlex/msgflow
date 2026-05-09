#!/usr/bin/env python3
"""msgflow 任务执行器 — CLI 入口"""
import sys
import argparse
from pathlib import Path

# 确保 tools/ 目录在 import path 中
sys.path.insert(0, str(Path(__file__).parent))


def main():
    parser = argparse.ArgumentParser(prog="msgflow-task", description="msgflow 任务执行器")
    sub = parser.add_subparsers(dest="action", required=True, help="执行的动作")

    # fetch
    p = sub.add_parser("fetch", help="抓取 URL 为 Markdown")
    p.add_argument("target", help="URL")

    # rewrite
    p = sub.add_parser("rewrite", help="改写文章")
    p.add_argument("target", help="URL 或文件路径")
    p.add_argument("--style", required=True, help="改写风格 (lu-xun/ma-sanli/xu-zhimo/...)")

    # ingest
    p = sub.add_parser("ingest", help="摄入到知识库")
    p.add_argument("target", help="URL")

    # query
    p = sub.add_parser("query", help="查询知识库")
    p.add_argument("target", help="问题")

    # distill
    p = sub.add_parser("distill", help="蒸馏人物为 writer skill")
    p.add_argument("target", help="人物名")

    # publish
    p = sub.add_parser("publish", help="发布到墨问")
    p.add_argument("target", help="文件路径")

    # pending
    sub.add_parser("pending", help="列出未发布文件")

    # lint
    sub.add_parser("lint", help="知识库健康检查")

    # skill
    p = sub.add_parser("skill", help="执行任意 skill")
    p.add_argument("target", help="消息内容")
    p.add_argument("--skill", required=True, help="skill 名称")

    args = parser.parse_args()

    # 延迟 import，避免无关模块的依赖报错
    from pipelines import fetch, rewrite, ingest, query, distill, publish, pending, lint
    from capabilities import ai_runner
    from capabilities.logger import get_logger
    log = get_logger("cli")

    handlers = {
        "fetch": lambda: fetch.execute(args.target),
        "rewrite": lambda: rewrite.execute(args.target, style=args.style),
        "ingest": lambda: ingest.execute(args.target),
        "query": lambda: query.execute(args.target),
        "distill": lambda: distill.execute(args.target),
        "publish": lambda: publish.execute(args.target),
        "pending": lambda: pending.execute(),
        "lint": lambda: lint.execute(),
        "skill": lambda: ai_runner.run_skill(args.skill, args.target),
    }

    log.info("task start", extra={"action": args.action})
    result = handlers[args.action]()

    # 输出结果
    output = result or "执行超时或无输出"
    Path("/tmp/result.txt").write_text(output, encoding="utf-8")
    status = "success" if result else "error"
    log.info("task done", extra={"action": args.action, "status": status, "length": len(output)})
    print(status)
    sys.exit(0 if result else 1)


if __name__ == "__main__":
    main()
