# Worker 与 GitHub Actions 交互流程

## 概览

```mermaid
%%{init: {'theme': 'base', 'themeVariables': {'primaryColor': '#f3e8ff', 'primaryBorderColor': '#9b72cf', 'primaryTextColor': '#2d1b4e', 'secondaryColor': '#e8e0f0', 'secondaryBorderColor': '#7e5eb0', 'tertiaryColor': '#faf5ff', 'tertiaryBorderColor': '#b39ddb', 'lineColor': '#7e5eb0', 'fontSize': '14px'}}}%%
flowchart LR
    subgraph S1["📱 消息入口"]
        A1["飞书"] --> A2["Telegram"] --> A3["企业微信"]
    end
    subgraph S2["⚡ Worker"]
        B1["解析指令"] --> B2["触发 workflow"]
    end
    subgraph S3["🔧 GitHub Actions"]
        C1["NullClaw 执行"] --> C2["回调 Worker"]
    end
    S1 --> S2 --> S3
```

## 完整时序

```mermaid
%%{init: {'theme': 'base', 'themeVariables': {'primaryColor': '#f3e8ff', 'primaryBorderColor': '#9b72cf', 'primaryTextColor': '#2d1b4e', 'secondaryColor': '#e8e0f0', 'secondaryBorderColor': '#7e5eb0', 'tertiaryColor': '#faf5ff', 'tertiaryBorderColor': '#b39ddb', 'lineColor': '#7e5eb0', 'fontSize': '14px'}}}%%
sequenceDiagram
    participant U as 用户
    participant W as Worker
    participant G as GitHub API
    participant A as Actions Runner

    U->>W: 发送消息（如 "摄入 URL"）
    W->>U: "收到，正在处理... ⏳"
    W->>G: POST workflow_dispatch
    G-->>W: 204 Accepted
    G->>A: 启动 feishu-task.yml
    A->>A: NullClaw + Skill 执行任务
    A->>W: POST /callback {secret, chat_id, status, result}
    W->>W: 验证 secret，路由 channel
    W->>U: 返回执行结果
```

## 触发接口（Worker → GitHub）

```
POST https://api.github.com/repos/{GITHUB_REPO}/actions/workflows/feishu-task.yml/dispatches
Authorization: Bearer {GITHUB_TOKEN}

{
  "ref": "main",
  "inputs": {
    "action": "fetch|ingest|query|rewrite|distill|publish|pending|lint|skill",
    "target": "URL 或文本",
    "style": "lu-xun|ma-sanli|xu-zhimo",
    "skill": "skill 名称",
    "chat_id": "telegram:123456",
    "callback_url": "https://your-domain.com/callback"
  }
}
```

GitHub API 返回 204 表示触发成功（异步，不等待执行完成）。

## 回调接口（GitHub → Worker）

```
POST https://your-domain.com/callback
Content-Type: application/json

{
  "secret": "CALLBACK_SECRET（双方共享）",
  "chat_id": "telegram:123456",
  "status": "success|error",
  "result": "执行结果文本"
}
```

Worker 验证 secret 后，根据 `chat_id` 前缀分发到对应 channel。

## chat_id 路由规则

| Channel | 格式 | 示例 |
|---------|------|------|
| Telegram | `telegram:{chat_id}` | `telegram:123456789` |
| 飞书 | `feishu:{chat_id}` | `feishu:oc_abcdef` |
| 企业微信 | `wecom:{userId}\|{agentId}` | `wecom:zhangsan\|1000002` |

## 安全机制

```mermaid
%%{init: {'theme': 'base', 'themeVariables': {'primaryColor': '#f3e8ff', 'primaryBorderColor': '#9b72cf', 'primaryTextColor': '#2d1b4e', 'secondaryColor': '#e8e0f0', 'secondaryBorderColor': '#7e5eb0', 'tertiaryColor': '#faf5ff', 'tertiaryBorderColor': '#b39ddb', 'lineColor': '#7e5eb0', 'fontSize': '14px'}}}%%
flowchart LR
    subgraph S1["🔐 入站验证"]
        A1["飞书: verification_token"] --> A2["企业微信: AES + 签名"] --> A3["回调: CALLBACK_SECRET"]
    end
    subgraph S2["🔑 出站认证"]
        B1["GitHub: PAT Bearer"] --> B2["飞书: tenant_token"] --> B3["企业微信: access_token"]
    end
    S1 --- S2
```

## 设计理由

- **Worker 免费额度大**（10 万次/天），只做消息转发，执行时间 < 1 秒
- **GitHub Actions 免费分钟多**（公开仓库无限），适合跑 AI 推理这种耗时任务
- **解耦**：换 AI 提供商只改 Actions secrets，Worker 不用动
- **可观测**：每次任务在 Actions 有完整日志，比 Worker 的 `wrangler tail` 详细得多
