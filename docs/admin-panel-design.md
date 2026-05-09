# Admin 管理页面 — 需求与设计

## 需求背景

当前 msgflow 的配置（API Key、模型、URL 等）需要用户在 GitHub Settings 和 `wrangler secret put` 中手动设置，门槛高，不适合非开发者用户。需要一个 Web 管理页面，让用户通过浏览器完成所有配置。

## 用户故事

1. 作为用户，我部署完 Worker 后，打开管理页面就能配置所有参数
2. 作为用户，我想换 AI 模型或 API Key 时，在页面上改完立即生效
3. 作为用户，我不需要进 GitHub Settings 做任何操作（首次部署除外）

## 需求清单

| # | 需求 | 优先级 |
|---|------|--------|
| R1 | 管理页面可查看和修改所有运行时配置 | P0 |
| R2 | 管理页面有鉴权，未授权不可访问 | P0 |
| R3 | 配置修改后立即生效（下次消息触发时使用新值） | P0 |
| R4 | 用户部署时只需设置最少的 wrangler secrets | P1 |
| R5 | 页面简洁，非开发者能看懂 | P1 |
| R6 | 敏感值不出现在 GitHub Actions 日志中 | P0 |

---

## 设计方案

### 架构

```
用户浏览器
  │
  │ GET  /admin?token=xxx   → 配置页面 HTML
  │ GET  /admin/config      → 读 KV 返回当前配置（脱敏）
  │ POST /admin/config      → 写 KV 更新配置
  ▼
Worker (KV: MSGFLOW_CONFIG)
  │
  ├─ 触发 workflow 时：非敏感配置通过 dispatch inputs 传入
  │
  ├─ POST /internal/config  → workflow 运行时回调拉取敏感配置
  │   （用 CALLBACK_SECRET 鉴权）
  ▼
GitHub Actions (feishu-task.yml)
  │
  ├─ inputs 读取：model, base_url, wiki_repo
  ├─ curl Worker 获取：api_key, mowen_key, unsplash_key, llmwiki_token
  └─ fallback：secrets.* （向后兼容）
```

### 配置存储分层

| 配置项 | 存储位置 | 传递给 workflow 的方式 | 原因 |
|--------|---------|----------------------|------|
| `NULLCLAW_BASE_URL` | KV | dispatch input | 非敏感，可出现在日志 |
| `NULLCLAW_MODEL` | KV | dispatch input | 非敏感 |
| `WIKI_REPO` | KV | dispatch input | 非敏感 |
| `NULLCLAW_API_KEY` | KV | workflow curl /internal/config | 敏感，不能出现在日志 |
| `MOWEN_API_KEY` | KV | workflow curl /internal/config | 敏感 |
| `UNSPLASH_KEY` | KV | workflow curl /internal/config | 敏感 |
| `LLMWIKI_TOKEN` | KV | workflow curl /internal/config | 敏感 |
| `CALLBACK_SECRET` | Worker Secret | 不变 | 基础设施凭据，部署时设置 |
| `ADMIN_TOKEN` | Worker Secret | 不变 | 管理页面鉴权 |
| `GITHUB_TOKEN` | Worker Secret | 不变 | 触发 workflow |
| 聊天平台凭据 | Worker Secret | 不变 | 消息收发基础能力 |

### 鉴权

- **管理页面**：URL 参数 `?token=ADMIN_TOKEN` 或 header `Authorization: Bearer ADMIN_TOKEN`
- **/internal/config**：body 中 `secret` 字段 = `CALLBACK_SECRET`（workflow 已有此值）
- `ADMIN_TOKEN` 通过 `wrangler secret put` 部署时设置

### KV 数据结构

Namespace: `MSGFLOW_CONFIG`，单个 key `config`：

```json
{
  "nullclaw_api_key": "sk-xxx",
  "nullclaw_base_url": "https://api.example.com/v1",
  "nullclaw_model": "mimo-v2.5-pro",
  "mowen_api_key": "mk-xxx",
  "unsplash_key": "uk-xxx",
  "wiki_repo": "ohwiki/llmwiki",
  "llmwiki_token": "ghp_xxx",
  "task_timeout": 600
}
```

`task_timeout` 默认 600 秒（10 分钟），用户可在管理页面调整（如蒸馏需要更长时间可设为 1800）。

### Worker 路由变化

| 路由 | 方法 | 用途 | 鉴权 |
|------|------|------|------|
| `/admin` | GET | 返回管理页面 HTML | ADMIN_TOKEN |
| `/admin/config` | GET | 读取配置（敏感值脱敏） | ADMIN_TOKEN |
| `/admin/config` | POST | 更新配置 | ADMIN_TOKEN |
| `/internal/config` | POST | workflow 拉取敏感配置 | CALLBACK_SECRET |

### triggerWorkflow 改动

```js
// 从 KV 读非敏感配置，塞入 inputs
inputs: {
  action, target, style, skill, chat_id, callback_url,
  config: JSON.stringify({ base_url, model, wiki_repo })
}
```

用 JSON 字符串打包为单个 input，避免 GitHub 10 个 inputs 上限问题。

### workflow 侧改动

```yaml
inputs:
  config:
    description: 'JSON config from Worker KV'
    required: false
    type: string

steps:
  - name: Load config
    run: |
      # 非敏感配置从 input 解析
      if [ -n "${{ inputs.config }}" ]; then
        export NULLCLAW_BASE_URL=$(echo '${{ inputs.config }}' | jq -r '.base_url // empty')
        export NULLCLAW_MODEL=$(echo '${{ inputs.config }}' | jq -r '.model // empty')
        export WIKI_REPO=$(echo '${{ inputs.config }}' | jq -r '.wiki_repo // empty')
      fi

      # 敏感配置从 Worker 拉取
      secrets=$(curl -s -X POST "${{ inputs.callback_url | replace('/callback', '/internal/config') }}" \
        -H "Content-Type: application/json" \
        -d '{"secret":"${{ secrets.CALLBACK_SECRET }}"}')

      export NULLCLAW_API_KEY=$(echo "$secrets" | jq -r '.nullclaw_api_key // empty')
      export MOWEN_API_KEY=$(echo "$secrets" | jq -r '.mowen_api_key // empty')
      export UNSPLASH_KEY=$(echo "$secrets" | jq -r '.unsplash_key // empty')
      export LLMWIKI_TOKEN=$(echo "$secrets" | jq -r '.llmwiki_token // empty')

      # Fallback 到 GitHub Secrets（向后兼容）
      : ${NULLCLAW_API_KEY:=${{ secrets.NULLCLAW_API_KEY }}}
      : ${NULLCLAW_BASE_URL:=${{ secrets.NULLCLAW_BASE_URL }}}
      : ${NULLCLAW_MODEL:=${{ vars.NULLCLAW_MODEL }}}
      : ${MOWEN_API_KEY:=${{ secrets.MOWEN_API_KEY }}}
      : ${UNSPLASH_KEY:=${{ secrets.UNSPLASH_KEY }}}
```

### 管理页面 UI

单页 HTML，内联在 Worker 中。无外部 JS/CSS 依赖。

```
┌─────────────────────────────────────┐
│  msgflow 配置管理                    │
├─────────────────────────────────────┤
│                                     │
│  🤖 AI 配置                         │
│  ┌───────────────────────────────┐  │
│  │ API Key    [sk-****]          │  │
│  │ Base URL   [https://...]      │  │
│  │ Model      [mimo-v2.5-pro]    │  │
│  └───────────────────────────────┘  │
│                                     │
│  📦 集成配置                         │
│  ┌───────────────────────────────┐  │
│  │ 墨问 Key   [mk-****]          │  │
│  │ Unsplash   [uk-****]          │  │
│  │ Wiki Repo  [ohwiki/llmwiki]   │  │
│  │ Wiki Token [ghp_****]         │  │
│  └───────────────────────────────┘  │
│                                     │
│           [ 💾 保存 ]               │
│                                     │
└─────────────────────────────────────┘
```

### 安全考虑

1. HTTPS only（Cloudflare 强制）
2. GET /admin/config 返回脱敏值（前 4 位 + `****`）
3. /internal/config 用 CALLBACK_SECRET 鉴权，只返回敏感值
4. 无外部 JS 依赖，防供应链攻击
5. ADMIN_TOKEN 和 CALLBACK_SECRET 不存 KV，只在 Worker Secrets
6. KV 传播延迟 < 60 秒，文档中说明

### 部署时用户操作（简化后）

```bash
# 1. 部署 Worker
wrangler deploy

# 2. 设置最少 Secrets（一次性）
wrangler secret put ADMIN_TOKEN        # 管理页面密码
wrangler secret put GITHUB_TOKEN       # GitHub PAT
wrangler secret put CALLBACK_SECRET    # 回调验证
wrangler secret put TELEGRAM_BOT_TOKEN # 如需 Telegram

# 3. 打开管理页面，配置其余所有参数
# https://你的域名/admin?token=你的ADMIN_TOKEN
```

---

## 任务拆分

| # | 任务 | 依赖 | 预估 |
|---|------|------|------|
| T1 | wrangler.toml 添加 KV namespace binding | 无 | 小 |
| T2 | 创建 lib/config.js — 读写 KV，脱敏逻辑 | T1 | 小 |
| T3 | 创建 handlers/admin.js — 页面路由 + config API + /internal/config | T2 | 中 |
| T4 | 创建 admin HTML 页面（内联字符串） | T3 | 中 |
| T5 | 修改 lib/github.js — 从 KV 读非敏感配置打包为 config input | T2 | 小 |
| T6 | 修改 feishu-task.yml — 解析 config input + curl 拉取敏感值 + fallback | T5 | 中 |
| T7 | 更新 index.js — 添加 /admin 和 /internal/config 路由 | T3 | 小 |
| T8 | 更新部署文档和 wrangler.toml.example | T7 | 小 |
