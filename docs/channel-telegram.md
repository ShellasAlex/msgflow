# Telegram 接入指南

## 创建 Bot

1. 在 Telegram 搜索 `@BotFather`，发送 `/newbot`
2. 按提示输入 Bot 名称（显示名）和用户名（必须以 `bot` 结尾）
3. 创建成功后 BotFather 会给你一个 Token，格式：`123456789:AABBccdd-EEFFgghh`
4. **立即复制保存**

## 配置 Worker Secret

```bash
wrangler secret put TELEGRAM_BOT_TOKEN
```

输入上一步拿到的 Token。

## 注册 Webhook

部署 Worker 后，浏览器打开：

```
https://你的域名/setup?token=你的CALLBACK_SECRET
```

看到以下内容就成功了：

```json
{"ok":true,"result":true,"description":"Webhook was set"}
```

> ⚠️ **每次重新部署 Worker 后，必须重新访问 `/setup` 注册 webhook。**
>
> 原因：注册时会把 `CALLBACK_SECRET` 作为 `secret_token` 告诉 Telegram，之后 Telegram 每次发消息都会带上这个 token，Worker 会验证它。不重新注册，消息会被 403 拒绝。
>
> 简单记忆：**部署后访问一次 `/setup`，Telegram 就能正常工作。**

## 测试

在 Telegram 找到你的 Bot，发送一条 URL：

```
https://github.com/ohwiki/msgflow
```

预期：
1. 立即收到「收到，正在处理... ⏳」
2. 1-2 分钟后收到抓取的 Markdown 内容

## 故障排查

| 问题 | 原因 | 解决 |
|------|------|------|
| Bot 没有任何回复 | webhook 未注册 | 访问 `/setup?token=xxx` |
| 收到「收到」但无后续 | GitHub Token 权限不够 | 检查 PAT 的 Actions 读写权限 |
| 403 错误 | CALLBACK_SECRET 不匹配 | 确认 Worker Secret 和 GitHub Secret 值一致 |
