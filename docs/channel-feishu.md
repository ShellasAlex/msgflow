# 飞书接入指南

## 创建飞书应用

1. 打开 [飞书开放平台](https://open.feishu.cn/app)，登录后点击「创建企业自建应用」
2. 填写应用名称（如 `msgflow`）和描述，点击创建
3. 进入应用，记录以下信息：
   - **App ID**：凭证与基础信息页面，格式 `cli_xxxxxxxxxxxxxxxx`
   - **App Secret**：同页面，点击显示后复制

## 配置应用权限

进入应用 → 权限管理 → 搜索并开通以下权限：

| 权限 | 说明 |
|------|------|
| `im:message:send_as_bot` | 以机器人身份发送消息 |
| `im:message.receive_v1` | 接收消息事件 |

## 配置事件订阅

1. 进入应用 → 事件与回调 → 事件订阅
2. 请求地址填写：

```
https://你的域名/feishu/event
```

3. 页面上方会显示 **Verification Token**，复制保存
4. 点击保存（飞书会发验证请求，Worker 自动响应 challenge）
5. 添加事件：点击「添加事件」→ 搜索 `im.message.receive_v1` → 勾选

## 发布应用

1. 进入应用 → 版本管理与发布
2. 创建版本 → 填写版本号和更新说明
3. 提交审核（企业内部应用通常自动通过）
4. 确认应用状态为「已启用」

## 配置 Worker Secrets

```bash
wrangler secret put FEISHU_APP_ID
# 输入：cli_xxxxxxxxxxxxxxxx

wrangler secret put FEISHU_APP_SECRET
# 输入：应用的 App Secret

wrangler secret put FEISHU_VERIFICATION_TOKEN
# 输入：事件订阅页面的 Verification Token
```

设置完后重新部署：

```bash
wrangler deploy
```

## 测试

在飞书中搜索你的机器人名称，发送一条 URL：

```
https://github.com/ohwiki/msgflow
```

预期：
1. 立即收到「收到，正在处理... ⏳」
2. 1-2 分钟后收到抓取的 Markdown 内容

## 故障排查

| 问题 | 原因 | 解决 |
|------|------|------|
| 事件订阅保存失败 | Worker 未部署或地址错误 | 确认 Worker 已部署且域名正确 |
| Bot 没有回复 | 应用未发布或权限未开通 | 检查应用状态和权限列表 |
| 收到「收到」但无后续 | GitHub Token 权限不够 | 检查 PAT 的 Actions 读写权限 |
| 重复收到消息 | 事件去重失败 | 检查 Worker 日志，确认版本最新 |

## 注意事项

- 飞书应用的 token 缓存有效期 2 小时，Worker 会自动管理
- 如果更换了 App Secret，需要重新 `wrangler secret put FEISHU_APP_SECRET` 并重新部署
- 飞书事件有 5 秒超时限制，Worker 会先回复「收到」再异步触发任务
