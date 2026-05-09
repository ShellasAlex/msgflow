# run-task 重构：Bash → Python 模块化

## 需求背景

当前 `tools/run-task.sh` 是 180+ 行的 Bash 脚本，存在以下问题：

1. **重复代码**：抓取逻辑（weixin → jina → defuddle）在 fetch/rewrite/ingest 中重复 3 次
2. **不可测试**：无法对单个能力写单元测试
3. **错误处理脆弱**：`set +e` + 手动 `$?` 检查，容易遗漏
4. **扩展困难**：新增 pipeline 需要在巨大的 case 语句中插入代码
5. **字符串处理危险**：Bash 变量拼接容易出 bug（空格、特殊字符）

## 需求清单

| # | 需求 | 优先级 |
|---|------|--------|
| R1 | 通用能力（抓取、AI 调用、发布、存储）抽离为独立模块 | P0 |
| R2 | 业务流程（rewrite、ingest 等）作为编排层组合能力 | P0 |
| R3 | 新增 pipeline 只需新建一个文件，不改已有代码 | P0 |
| R4 | 每个 capability 可独立测试 | P1 |
| R5 | workflow 改动最小（只改一行调用命令） | P1 |
| R6 | 保持向后兼容（输出格式不变：/tmp/result.txt） | P0 |

---

## 设计方案

### 架构分层

```
┌─────────────────────────────────────────────┐
│  run_task.py（入口：参数解析 → 路由到 pipeline）│
└──────────────────────┬──────────────────────┘
                       │
┌──────────────────────▼──────────────────────┐
│  pipelines/（编排层：业务流程，组合 capabilities）│
│  fetch / rewrite / ingest / query /          │
│  distill / publish / pending                 │
└──────────────────────┬──────────────────────┘
                       │
┌──────────────────────▼──────────────────────┐
│  capabilities/（能力层：通用、无业务语义）       │
│  content_fetcher / ai_runner / publisher /    │
│  cover / file_store                          │
└─────────────────────────────────────────────┘
```

### 目录结构

```
tools/
├── run_task.py                 # 入口
├── pipelines/
│   ├── __init__.py
│   ├── fetch.py                # 抓取 URL → 保存 Markdown
│   ├── rewrite.py              # 抓取 → AI 改写 → 封面图 → 保存 → 发布
│   ├── ingest.py               # 抓取 → 存 raw → AI 生成 wiki 页面
│   ├── query.py                # AI 基于 wiki 回答问题
│   ├── distill.py              # AI 蒸馏人物 → 生成 writer skill
│   ├── publish.py              # 手动发布文件到墨问
│   ├── pending.py              # 列出未发布文件
│   └── lint.py                 # 知识库健康检查
├── capabilities/
│   ├── __init__.py
│   ├── content_fetcher.py      # 统一抓取链
│   ├── ai_runner.py            # NullClaw 调用封装
│   ├── publisher.py            # 墨问发布
│   ├── cover.py                # 封面图获取
│   └── file_store.py           # 文件存储（含目录创建、命名）
└── content-fetch/
    └── fetch_weixin.py         # Playwright 实现（已有）
```

### 各层职责

#### 入口：run_task.py

```python
import sys
import argparse
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(prog="msgflow-task", description="msgflow 任务执行器")
    sub = parser.add_subparsers(dest="action", required=True)

    p = sub.add_parser("fetch", help="抓取 URL 为 Markdown")
    p.add_argument("target", help="URL")

    p = sub.add_parser("rewrite", help="改写文章")
    p.add_argument("target", help="URL 或文件路径")
    p.add_argument("--style", required=True, help="改写风格 (lu-xun/ma-sanli/xu-zhimo/...)")

    p = sub.add_parser("ingest", help="摄入到知识库")
    p.add_argument("target", help="URL")

    p = sub.add_parser("query", help="查询知识库")
    p.add_argument("target", help="问题")

    p = sub.add_parser("distill", help="蒸馏人物为 writer skill")
    p.add_argument("target", help="人物名")

    p = sub.add_parser("publish", help="发布到墨问")
    p.add_argument("target", help="文件路径")

    p = sub.add_parser("pending", help="列出未发布文件")

    p = sub.add_parser("lint", help="知识库健康检查")

    p = sub.add_parser("skill", help="执行任意 skill")
    p.add_argument("target", help="消息内容")
    p.add_argument("--skill", required=True, help="skill 名称")

    args = parser.parse_args()

    from pipelines import fetch, rewrite, ingest, query, distill, publish, pending, lint
    from capabilities import ai_runner

    handlers = {
        "fetch": lambda a: fetch.execute(a.target),
        "rewrite": lambda a: rewrite.execute(a.target, style=a.style),
        "ingest": lambda a: ingest.execute(a.target),
        "query": lambda a: query.execute(a.target),
        "distill": lambda a: distill.execute(a.target),
        "publish": lambda a: publish.execute(a.target),
        "pending": lambda a: pending.execute(),
        "lint": lambda a: lint.execute(),
        "skill": lambda a: ai_runner.run_skill(a.skill, a.target),
    }

    result = handlers[args.action](args)

    # 输出结果
    output = result or "执行超时或无输出"
    Path("/tmp/result.txt").write_text(output)
    print("success" if result else "error")

if __name__ == "__main__":
    main()
```

#### 能力层：capabilities/

**content_fetcher.py** — 统一抓取链

```python
def fetch(url: str) -> str | None:
    """抓取 URL 内容，按优先级尝试多种方式"""
    content = _try_weixin(url) if "mp.weixin.qq.com" in url else None
    if not content:
        content = _try_jina(url)
    if not content:
        content = _try_defuddle(url)
    return content
```

**ai_runner.py** — NullClaw 调用封装

```python
def run_skill(skill_name: str, prompt: str, timeout: int = 300, workspace: str = None) -> str | None:
    """调用 NullClaw agent，返回输出文本"""

def run_prompt(prompt: str, timeout: int = 300) -> str | None:
    """无 skill 的纯 prompt 调用"""
```

**publisher.py** — 墨问发布

```python
def publish_to_mowen(file_path: str, tags: list[str] = None) -> bool:
    """调用 mowen-cli 发布文件，返回是否成功"""
```

**cover.py** — 封面图

```python
def get_cover_url(text: str) -> str | None:
    """从文本提取关键词，搜索 Unsplash 返回封面图 URL"""
```

**file_store.py** — 文件存储

```python
def save(content: str, directory: str, prefix: str = "", suffix: str = ".md") -> str:
    """保存内容到文件，返回文件路径。自动创建目录、生成文件名。"""
```

#### 编排层：pipelines/

每个 pipeline 是一个 `execute(target, **kwargs) -> str` 函数，组合 capabilities 完成业务流程。

**pipelines/rewrite.py 示例：**

```python
from capabilities.content_fetcher import fetch
from capabilities.ai_runner import run_skill
from capabilities.cover import get_cover_url
from capabilities.publisher import publish_to_mowen
from capabilities.file_store import save

def execute(target: str, style: str = "", **kwargs) -> str:
    # 1. 抓取
    if target.startswith("http"):
        article = fetch(target)
    else:
        article = Path(target).read_text() if Path(target).exists() else None
    if not article:
        return "错误：无法获取文章内容"

    # 2. AI 改写
    prompt = f"请用你的风格改写以下文章。只输出改写后的完整文章正文。\n\n{article}"
    rewritten = run_skill(f"{style}-writer", prompt, timeout=300)
    if not rewritten:
        return "错误：改写失败"

    # 3. 封面图
    cover = get_cover_url(rewritten)
    content = f"![cover]({cover})\n\n{rewritten}" if cover else rewritten

    # 4. 保存
    path = save(content, directory="rewritten", prefix=style)

    # 5. 发布
    published = publish_to_mowen(path, tags=[style, "改写"])

    # 6. 返回结果
    result = content
    if published:
        result += "\n\n---\n✅ 已发布到墨问"
    return result
```

### workflow 改动

`feishu-task.yml` 只改一行：

```yaml
# 旧
bash tools/run-task.sh "${{ github.event.inputs.action }}" "${{ github.event.inputs.target }}" "${{ github.event.inputs.style }}" "${{ github.event.inputs.skill }}" >/dev/null

# 新（根据 action 拼接子命令）
ACTION="${{ github.event.inputs.action }}"
TARGET="${{ github.event.inputs.target }}"
STYLE="${{ github.event.inputs.style }}"
SKILL="${{ github.event.inputs.skill }}"

case "$ACTION" in
  rewrite) python3 tools/run_task.py rewrite "$TARGET" --style "$STYLE" ;;
  skill)   python3 tools/run_task.py skill "$TARGET" --skill "$SKILL" ;;
  *)       python3 tools/run_task.py "$ACTION" "$TARGET" ;;
esac
```

用户本地调试：

```bash
python3 tools/run_task.py --help
python3 tools/run_task.py rewrite --help
python3 tools/run_task.py fetch "https://example.com"
python3 tools/run_task.py rewrite "https://example.com" --style lu-xun
python3 tools/run_task.py distill "李白"
```

### 测试策略

```
tests/
├── test_content_fetcher.py    # mock requests，测试 fallback 链
├── test_ai_runner.py          # mock subprocess，测试超时/错误处理
├── test_publisher.py          # mock mowen-cli，测试成功/失败
├── test_file_store.py         # 用 tmp 目录，测试文件创建
└── test_pipelines/
    └── test_rewrite.py        # mock 所有 capabilities，测试编排逻辑
```

能力层每个模块可独立测试（mock 外部依赖）。编排层测试 mock 能力层，只验证调用顺序和条件判断。

### 复用验证

| 新增需求 | 改动 |
|---------|------|
| 新增"翻译"pipeline | 新建 `pipelines/translate.py`，复用 `fetch` + `ai_runner` + `save` |
| 新增"总结"pipeline | 新建 `pipelines/summarize.py`，复用 `fetch` + `ai_runner` |
| 换抓取方式（加 Firecrawl） | 只改 `capabilities/content_fetcher.py` |
| 换发布平台 | 只改 `capabilities/publisher.py` |
| 换 AI 引擎（NullClaw → 其他） | 只改 `capabilities/ai_runner.py` |
| 加重试逻辑 | 在 capability 内部加，所有 pipeline 自动受益 |

---

## 任务拆分

| # | 任务 | 依赖 | 说明 |
|---|------|------|------|
| T1 | 创建 `capabilities/content_fetcher.py` | 无 | 从 run-task.sh 提取抓取逻辑，统一接口 |
| T2 | 创建 `capabilities/ai_runner.py` | 无 | 封装 NullClaw subprocess 调用 |
| T3 | 创建 `capabilities/publisher.py` | 无 | 封装 mowen-cli 调用 |
| T4 | 创建 `capabilities/cover.py` | 无 | 从 get-cover.py 提取 |
| T5 | 创建 `capabilities/file_store.py` | 无 | 文件保存 + 目录创建 + 命名 |
| T6 | 创建 `pipelines/fetch.py` | T1, T5 | 组合：抓取 → 保存 |
| T7 | 创建 `pipelines/rewrite.py` | T1-T5 | 组合：抓取 → 改写 → 封面 → 保存 → 发布 |
| T8 | 创建 `pipelines/ingest.py` | T1, T2, T5 | 组合：抓取 → 存 raw → AI wiki |
| T9 | 创建 `pipelines/query.py` | T2 | AI 查询 |
| T10 | 创建 `pipelines/distill.py` | T2, T5 | AI 蒸馏 + 文件移动兜底 |
| T11 | 创建 `pipelines/publish.py` + `pending.py` + `lint.py` | T2, T3 | 简单 pipeline |
| T12 | 创建 `run_task.py` 入口 | T6-T11 | 参数解析 + 路由 + 结果输出 |
| T13 | 修改 `feishu-task.yml` | T12 | 改调用命令 |
| T14 | 删除 `run-task.sh` | T13 | 确认新版本工作后删除 |
| T15 | 编写 capabilities 单元测试 | T1-T5 | 可选，建议至少覆盖 content_fetcher |

### 执行建议

- T1-T5 可并行（无依赖）
- T6-T11 可并行（只依赖 capabilities）
- T12-T14 串行
- 建议先保留 `run-task.sh` 作为 fallback，新旧并存验证后再删
