# Admin 管理页面 — 部署操作指南

## 版本一：人类手动操作

### 前提

- 已安装 `wrangler` CLI 并登录（`wrangler login`）
- Worker 代码已包含 admin 功能（handlers/admin.js、lib/config.js）

### 步骤

#### 1. 创建 KV 存储

```bash
cd worker/
wrangler kv namespace create MSGFLOW_CONFIG
```

输出中会有一行：
```
id = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

把这个 id 填入 `wrangler.toml`：

```toml
[[kv_namespaces]]
binding = "MSGFLOW_CONFIG"
id = "你得到的id"
```

#### 2. 设置管理密码

想一个密码（如 `my-admin-password-2026`），执行：

```bash
wrangler secret put ADMIN_TOKEN
```

提示输入时粘贴你的密码。**记住这个值**，后面访问管理页面要用。

#### 3. 部署

```bash
wrangler deploy
```

#### 4. 访问管理页面

浏览器打开：

```
https://你的域名/admin?token=你的密码
```

在页面上填写：
- API Key — AI 模型的 key
- Base URL — AI 模型 API 地址
- Model — 模型名称
- 墨问 Key — 墨问平台 key（如有）
- Unsplash Key — 封面图 key（如有）
- Wiki Repo — 知识库仓库（如 `user/llmwiki`）
- Wiki Token — 访问私有仓库的 GitHub PAT（如有）

点击「💾 保存」即可。

#### 5. 验证

给 Telegram/飞书 bot 发一条消息测试，确认流程正常。

---

## 版本二：给 AI 助手执行的操作指令

> 把以下内容发给 AI 助手（如 Kiro、Claude），它就能帮你完成部署。

---

**指令开始**

请帮我完成 msgflow Admin 管理页面的部署，步骤如下：

1. 进入 `worker/` 目录，执行 `wrangler kv namespace create MSGFLOW_CONFIG`，从输出中提取 `id` 值，填入 `wrangler.toml` 的 `[[kv_namespaces]]` 段替换 `REPLACE_WITH_KV_NAMESPACE_ID`。

2. 执行 `echo "我选的密码" | wrangler secret put ADMIN_TOKEN` 设置管理页面密码。密码我选：`________`（填你想要的值）。

3. 执行 `wrangler deploy` 部署 Worker。

4. 部署完成后，用 curl 验证：
   - `curl -s -o /dev/null -w "%{http_code}" "https://我的域名/admin?token=我的密码"` 应返回 `200`
   - `curl -s -o /dev/null -w "%{http_code}" "https://我的域名/admin"` 应返回 `403`

5. 通过 API 写入初始配置（替换实际值）：
   ```bash
   curl -X POST "https://我的域名/admin/config" \
     -H "Authorization: Bearer 我的密码" \
     -H "Content-Type: application/json" \
     -d '{
       "nullclaw_api_key": "sk-xxx",
       "nullclaw_base_url": "https://api.example.com/v1",
       "nullclaw_model": "mimo-v2.5-pro",
       "wiki_repo": "user/llmwiki",
       "llmwiki_token": "ghp_xxx",
       "mowen_api_key": "mk-xxx",
       "unsplash_key": "uk-xxx"
     }'
   ```

**指令结束**

---

### 使用示例

对 AI 说：

> 帮我部署 msgflow admin 页面。worker 目录在 `/home/me/msgflow/worker`，域名是 `bot.example.com`，ADMIN_TOKEN 用 `my-secret-123`。部署完后帮我把 API Key 配置为 `sk-abcdef`，模型用 `gpt-4o`，base url 是 `https://api.openai.com/v1`。

AI 就会自动执行上面所有步骤。
