# 部署指南

飞书 + Telegram 接入 NullClaw，通过 Cloudflare Worker 中转触发 GitHub Actions。

## 架构

```
飞书/Telegram 发消息 → Cloudflare Worker → GitHub Actions (NullClaw + Skill) → Worker → 飞书/Telegram 回复
```

## 前置条件

- GitHub 账号
- Cloudflare 账号（免费）
- 能上 Telegram（发消息用）
- Node.js 环境（部署 Worker 用，本机 WSL 即可）

---

## 第一步：推代码到 GitHub

```bash
cd msgflow
git init
git add .
git commit -m "init: msgflow with feishu + telegram"
```

在 GitHub 上创建新仓库（建议命名 `msgflow`），然后：

```bash
git remote add origin https://github.com/你的用户名/msgflow.git
git branch -M main
git push -u origin main
```

---

## 第二步：配置 GitHub 仓库 Secrets

> **提示**：如果使用 Admin 管理页面配置 AI 参数，以下 Secrets 可以跳过（仅 `CALLBACK_SECRET` 必须设置）。Admin 页面配置优先，GitHub Secrets 作为 fallback。

进入仓库页面 → Settings → Secrets and variables → Actions → New repository secret

添加以下 Secrets：

| Name | Value |
|------|-------|
| `NULLCLAW_API_KEY` | `your-api-key` |
| `NULLCLAW_BASE_URL` | `https://token-plan-sgp.xiaomimimo.com/v1` |
| `CALLBACK_SECRET` | 自己编一个随机字符串，例如 `my-cb-secret-2026`（记住它，第五步要用） |

添加 Variable（同页面切换到 Variables 标签）：

| Name | Value |
|------|-------|
| `NULLCLAW_MODEL` | `mimo-v2.5-pro` |

---

## 第三步：创建 GitHub Personal Access Token

1. 打开 https://github.com/settings/tokens?type=beta
2. 点击 "Generate new token"
3. 填写：
   - Token name: `msgflow-worker`
   - Expiration: 90 days（或更长）
   - Repository access: Only select repositories → 选择 `msgflow`
   - Permissions:
     - Actions: **Read and write**
     - Contents: **Read and write**
4. 点击 Generate token
5. **立即复制 token**（只显示一次）

---

## 第四步：安装 Wrangler CLI

```bash
npm install -g wrangler
```

如果没有 npm：

```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs
npm install -g wrangler
```

---

## 第五步：部署 Cloudflare Worker

### 5.1 登录 Cloudflare

```bash
wrangler login
```

浏览器会打开授权页面，点击 Allow。

### 5.2 创建 KV Namespace

```bash
cd worker
wrangler kv namespace create MSGFLOW_CONFIG
```

命令会输出一个 `id`，把它填入 `wrangler.toml` 的 `[[kv_namespaces]]` 段：

```toml
[[kv_namespaces]]
binding = "MSGFLOW_CONFIG"
id = "输出的id"
```

### 5.3 修改配置

编辑 `worker/wrangler.toml`，把两个变量改成你的实际值：

```toml
[vars]
WORKER_URL = "https://bot.你的域名.com"
GITHUB_REPO = "你的GitHub用户名/msgflow"
```

### 5.4 配置 Secrets

进入你的 Worker 目录（即仓库中的 `worker/` 文件夹），然后逐个设置：

核心 Secrets（必须设置）：

```bash
wrangler secret put ADMIN_TOKEN       # 管理页面密码
wrangler secret put GITHUB_TOKEN      # 第三步生成的 GitHub PAT
wrangler secret put CALLBACK_SECRET   # 第二步填的随机字符串
```

渠道 Secrets（根据你接入的渠道设置）：

**Telegram** — 详见 [Telegram 接入指南](channel-telegram.md)

```bash
wrangler secret put TELEGRAM_BOT_TOKEN
```

**飞书** — 详见 [飞书接入指南](channel-feishu.md)

```bash
wrangler secret put FEISHU_APP_ID
wrangler secret put FEISHU_APP_SECRET
wrangler secret put FEISHU_VERIFICATION_TOKEN
```

**企业微信** — 详见 [企业微信接入指南](channel-wecom.md)

```bash
wrangler secret put WECOM_CORP_ID
wrangler secret put WECOM_CORP_SECRET
wrangler secret put WECOM_TOKEN
wrangler secret put WECOM_ENCODING_AES_KEY
```

### 5.5 部署

```bash
wrangler deploy
```

部署成功后会显示 Worker URL，类似：
```
https://feishu-nullclaw.你的子域名.workers.dev
```

---

## 第六步：绑定自定义域名（推荐）

> **注意**：`wrangler.toml` 中的 `custom_domain = true` 会在部署时自动绑定域名，但前提是该域名已在同一 Cloudflare 账号下托管 DNS。如果你用自己的域名，需要先完成以下步骤。

### 6.1 将域名 DNS 托管到 Cloudflare（仅首次）

1. 打开 https://dash.cloudflare.com → Add a site
2. 输入你的域名，选择 Free 计划
3. Cloudflare 会给你两个 nameserver 地址
4. 去你的域名注册商（如 Namesilo、GoDaddy）修改 NS 记录指向 Cloudflare
5. 等待生效（通常几分钟到 24 小时）

### 6.2 配置 wrangler.toml

```toml
routes = [
  { pattern = "bot.你的域名.com", custom_domain = true }
]

[vars]
WORKER_URL = "https://bot.你的域名.com"
```

部署时 Wrangler 会自动创建 DNS 记录并绑定域名，无需手动操作 Dashboard。

### 6.3 不用自定义域名

如果不想绑定域名，删掉 `routes` 配置即可。部署后 Worker 会分配一个默认地址：

```
https://你的worker名.你的子域名.workers.dev
```

把这个地址填到 `WORKER_URL` 变量里，其他配置中用到域名的地方也相应替换。

---

## 第七步：接入聊天渠道

选择你要用的渠道，按对应文档配置：

| 渠道 | 文档 | 难度 |
|------|------|------|
| Telegram | [Telegram 接入指南](channel-telegram.md) | ⭐ 最简单，推荐先用这个 |
| 飞书 | [飞书接入指南](channel-feishu.md) | ⭐⭐ 需要创建飞书应用 |
| 企业微信 | [企业微信接入指南](channel-wecom.md) | ⭐⭐⭐ 需要企业微信管理员权限 |

至少接入一个渠道后，就可以测试了。

---

## 第八步：测试

给你接入的 Bot 发一条 URL：

```
https://github.com/ohwiki/msgflow
```

预期：
1. 立即收到「收到，正在处理... ⏳」
2. 1-2 分钟后收到抓取的 Markdown 内容

**收到了？部署完成。** 🎉

---

## 支持的指令

| 指令 | 说明 | 示例 |
|------|------|------|
| 直接发 URL | 抓取为 Markdown | `https://mp.weixin.qq.com/s/xxx` |
| `改写 风格 URL` | 抓取并改写 | `改写 鲁迅 https://mp.weixin.qq.com/s/xxx` |
| `改写 风格 文件路径` | 改写已有文章 | `改写 马三立 articles/xxx.md` |
| `skill:名称 消息` | 执行任意 skill | `skill:markdown-proxy https://example.com` |

支持的风格：`鲁迅` / `马三立` / `徐志摩`

---

## Admin 管理页面

部署完成后，打开管理页面配置 AI 和集成参数：

```
https://你的域名/admin?token=你的ADMIN_TOKEN
```

可配置项：

| 配置 | 说明 |
|------|------|
| API Key | NullClaw/AI 模型的 API Key |
| Base URL | AI 模型 API 地址 |
| Model | 模型名称（如 `mimo-v2.5-pro`） |
| 墨问 Key | 墨问发布平台 API Key |
| Unsplash Key | 封面图 Access Key |
| Wiki Repo | 知识库仓库（如 `user/llmwiki`） |
| Wiki Token | 访问私有知识库的 GitHub PAT |
| 任务超时 | NullClaw 执行超时秒数（默认 600） |

配置保存后立即生效（下次消息触发时使用新值）。KV 传播延迟通常 < 60 秒。

> **优势**：配置完 Admin 页面后，GitHub 仓库的 Secrets/Variables 可以不设置（作为 fallback 保留向后兼容）。新用户只需设置最少的 Worker Secrets（ADMIN_TOKEN、GITHUB_TOKEN、CALLBACK_SECRET、聊天平台凭据），其余全部在 Admin 页面完成。

---

## 故障排查

### Bot 没有回复「收到」

- 检查 Worker 是否部署成功：浏览器访问 `https://你的域名` 应返回 "OK"
- Telegram：访问 `https://你的域名/setup` 确认 webhook 注册成功
- 飞书：确认事件订阅地址正确且验证通过

### 收到「收到」但没有后续结果

- 去 GitHub 仓库 → Actions 页面查看是否有 workflow 运行
- 如果没有触发：检查 `GITHUB_TOKEN` 权限和 `GITHUB_REPO` 值
- 如果触发了但失败：查看 Actions 日志

### 回调失败（有 Actions 日志但飞书/Telegram 没收到结果）

- 确认 GitHub Secret `CALLBACK_SECRET` 和 Worker Secret `CALLBACK_SECRET` 值一致
- 确认 `WORKER_URL` 配置正确

### Actions 中 NullClaw 执行失败

- 检查 `NULLCLAW_API_KEY` 和 `NULLCLAW_BASE_URL` 是否正确
- 查看 Actions 日志中的具体错误

---

## 费用

| 组件 | 费用 |
|------|------|
| Cloudflare Worker | 免费（每天 10 万次请求） |
| GitHub Actions | 免费（公开仓库无限制，私有仓库每月 2000 分钟） |
| 飞书机器人 | 免费 |
| Telegram Bot | 免费 |
| 小米 MiMo API | 按 token 计费 |

---

## CI 自动部署（推荐）

Worker 代码变更后自动部署，无需手动执行 `wrangler deploy`。

### 配置步骤

1. **创建 Cloudflare API Token**
   - 打开 https://dash.cloudflare.com/profile/api-tokens
   - Create Token → 使用 "Edit Cloudflare Workers" 模板
   - 权限范围选择你的账号和域名
   - 复制生成的 token

2. **添加 GitHub Secret**
   - 仓库 Settings → Secrets → Actions → New repository secret
   - Name: `CLOUDFLARE_API_TOKEN`
   - Value: 上一步的 token

3. **完成**
   - 之后每次 push 到 main 且修改了 `worker/` 下的文件，会自动触发部署
   - 也可以在 Actions 页面手动触发（workflow_dispatch）

### 工作流文件

`.github/workflows/deploy-worker.yml` 已包含在仓库中，无需额外创建。

---

## 企业微信接入

详见 [企业微信接入指南](channel-wecom.md)。
