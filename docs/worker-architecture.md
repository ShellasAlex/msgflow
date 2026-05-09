# Worker 架构与多 Worker 扩展规划

> 最后更新：2026-05-08

## 当前结构

```
worker/
├── index.js              # 薄路由 + 回调处理
├── handlers/
│   ├── telegram.js       # Telegram 消息处理
│   ├── feishu.js         # 飞书消息处理（事件去重 + 缓存 token）
│   └── wecom.js          # 企业微信（签名验证 + AES 解密 + XML 解析）
├── lib/
│   ├── command.js        # 通用指令解析 + HELP_TEXT
│   ├── github.js         # triggerWorkflow（带返回值检查 + 错误处理）
│   ├── feishu-token.js   # 飞书 token 缓存（Cache API，2h TTL）
│   ├── crypto.js         # Web Crypto AES-256-CBC 解密 + SHA-1 签名
│   └── log.js            # 结构化日志（JSON 格式，wrangler tail 友好）
└── wrangler.toml.example
```

## 设计原则

1. **lib/ 是可平移的独立模块** — 每个文件零外部依赖，只依赖 Web 标准 API
2. **handlers/ 是业务入口** — 每个 channel 一个文件，import lib/ 组合逻辑
3. **index.js 只做路由** — 不含业务逻辑，顶层 try/catch 统一兜底

## 多 Worker 扩展方案

当出现第二个 Worker 时，将 `lib/` 提升为共享包：

```
msgflow/
├── packages/
│   └── worker-shared/          # 共享包（从 lib/ 平移）
│       ├── log.js
│       ├── crypto.js
│       ├── github.js
│       └── package.json
├── workers/
│   ├── bot/                    # 当前 msgflow worker
│   │   ├── index.js
│   │   ├── handlers/
│   │   └── wrangler.toml
│   ├── cron-worker/            # 示例：定时任务
│   └── webhook-proxy/          # 示例：webhook 转发
└── package.json                # workspaces: ["packages/*", "workers/*"]
```

### 迁移步骤（未来执行）

1. 根目录 `npm init -w packages/worker-shared`
2. 把 `worker/lib/` 移入 `packages/worker-shared/`
3. 各 worker 的 import 路径改为 `import { log } from "worker-shared/log.js"`
4. Wrangler 自动 bundle，无需额外配置

### 触发时机

- ❌ 现在不做（只有一个 Worker）
- ✅ 当创建第二个 Worker 且需要复制 lib/ 中任何文件时执行

## 日志规范

所有 Worker 统一使用 `lib/log.js` 输出结构化 JSON：

```js
import { log } from "./lib/log.js";

log.info("workflow triggered", { action: "fetch", channel: "telegram" });
log.error("GitHub API failed", { status: 422, body: "..." });
```

输出格式（`wrangler tail` 可直接查看）：

```json
{"ts":1715155200000,"level":"info","msg":"workflow triggered","action":"fetch","channel":"telegram"}
```

### 为什么不用完整日志框架

- Worker 是无状态短生命周期函数，无文件系统、无日志轮转需求
- `console.*` 直接对接 Cloudflare 的 tail/realtime logs
- 请求级别日志量极小，不需要 sink 插件体系
- 10 行 helper 覆盖所有需求
