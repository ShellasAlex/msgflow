# 企业微信接入指南

## 创建自建应用

1. 登录 [企业微信管理后台](https://work.weixin.qq.com) → 应用管理 → 自建 → 创建应用
2. 填写应用名称、Logo、可见范围
3. 创建完成后记录以下信息：

| 信息 | 位置 |
|------|------|
| **Corp ID** | 我的企业 → 企业信息 → 企业 ID |
| **Corp Secret** | 自建应用详情页 → Secret（点击查看） |

## 配置 API 接收消息

1. 进入自建应用 → API 接收消息
2. 点击「设置」，系统会自动生成：
   - **Token** — 复制保存
   - **EncodingAESKey** — 复制保存
3. URL 填写：

```
https://你的域名/wecom/callback
```

4. 点击保存（企业微信会发 GET 验证请求，Worker 自动响应）

## 配置 Worker Secrets

```bash
wrangler secret put WECOM_CORP_ID
# 输入：企业 ID

wrangler secret put WECOM_CORP_SECRET
# 输入：自建应用的 Secret

wrangler secret put WECOM_TOKEN
# 输入：API 接收消息页面的 Token

wrangler secret put WECOM_ENCODING_AES_KEY
# 输入：API 接收消息页面的 EncodingAESKey
```

设置完后重新部署：

```bash
wrangler deploy
```

## 测试

在企业微信中找到你的自建应用，发送：

```
https://github.com/ohwiki/msgflow
```

预期：
1. 立即收到「收到，正在处理... ⏳」
2. 1-2 分钟后收到抓取的 Markdown 内容

## 故障排查

| 问题 | 原因 | 解决 |
|------|------|------|
| 回调 URL 保存失败 | Worker 未部署或 AES 解密失败 | 确认 Worker 已部署，检查 WECOM_ENCODING_AES_KEY 是否正确 |
| Bot 没有回复 | Corp Secret 错误导致 token 获取失败 | 重新设置 WECOM_CORP_SECRET |
| 消息解密失败 | EncodingAESKey 不匹配 | 重新设置 WECOM_ENCODING_AES_KEY 并重新部署 |

## 注意事项

- 企业微信的 access_token 缓存有效期 1.5 小时，Worker 会自动管理
- 企业微信消息使用 AES-256-CBC 加密，Worker 已内置 Web Crypto 解密
- 如果应用可见范围有限，只有范围内的用户能给 Bot 发消息
