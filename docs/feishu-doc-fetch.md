# 飞书文档抓取配置

让 msgflow 能高质量抓取飞书文档（docx、wiki 知识库页面），通过飞书开放 API 获取结构化数据，转为干净的 Markdown。

## 为什么需要单独配置

直接发飞书文档链接时，默认会走 Jina Reader 抓取网页。但飞书文档是 JS 渲染的，网页抓取效果差（图片丢失、内容截断）。

通过飞书 API 抓取，能拿到完整的结构化数据：标题层级、代码块、图片、列表等全部保留。

## 前提条件

- 一个飞书账号（手机号注册即可）
- 5 分钟时间

## 配置步骤

### 1. 创建飞书应用

打开 https://open.feishu.cn → 登录 → 创建企业自建应用

填写应用名称（如 `msgflow-reader`），创建后记录：
- **App ID**：格式 `cli_xxxxxxxxxxxxxxxx`
- **App Secret**：点击显示后复制

### 2. 添加文档读取权限

进入应用 → 权限管理 → 搜索并开通：

| 权限 | 用途 |
|------|------|
| `docx:document:readonly` | 读取文档内容 |
| `wiki:wiki:readonly` | 读取知识库页面 |

### 3. 发布应用

进入版本管理与发布 → 创建版本 → 提交（企业内部应用通常自动通过）

### 4. 配置到 msgflow

在 Admin 管理页面（`https://你的域名/admin?token=你的ADMIN_TOKEN`）暂时没有飞书文档的配置项。

需要在 GitHub Actions 的环境变量中添加：

仓库 Settings → Secrets → Actions → New repository secret：

| Name | Value |
|------|-------|
| `FEISHU_APP_ID` | 你的 App ID |
| `FEISHU_APP_SECRET` | 你的 App Secret |

> 如果你已经配置了飞书消息渠道，可以复用同一个应用，只需要加上文档读取权限即可。

## 获取知识库 Space ID

如果你想把内容发布到飞书知识库（而不是「我的空间」），需要知识库的 Space ID。

**获取方法：**

1. 打开飞书知识库页面，进入你要发布到的知识库
2. 看浏览器地址栏，URL 格式为：`https://xxx.feishu.cn/wiki/space/7xxxxxxxxxxxxxxx`
3. 最后那串数字就是 Space ID（如 `7380000000000000000`）

或者通过 API 获取：

```bash
# 先拿 token
TOKEN=$(curl -s https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal \
  -d '{"app_id":"你的APP_ID","app_secret":"你的APP_SECRET"}' | jq -r '.tenant_access_token')

# 列出你有权限的知识库
curl -s -H "Authorization: Bearer $TOKEN" \
  "https://open.feishu.cn/open-apis/wiki/v2/spaces" | jq '.data.items[] | {name, space_id}'
```

拿到 Space ID 后，在 Admin 管理页面的「飞书知识库 Space ID」字段填入即可。

## 能抓什么

| 文档类型 | 能否抓取 | 说明 |
|---------|---------|------|
| 互联网公开的文档 | ✅ | 任何设置了「互联网可见」的文档 |
| 你自己的文档 | ✅ | 应用代表你访问 |
| 别人分享给你的文档 | ✅ | 你有查看权限即可 |
| 别人的私有文档 | ❌ | 没有权限 |

## 支持的 URL 格式

```
https://xxx.feishu.cn/docx/xxxxxxxx    # 新版文档
https://xxx.feishu.cn/docs/xxxxxxxx    # 旧版文档
https://xxx.feishu.cn/wiki/xxxxxxxx    # 知识库页面
https://xxx.larksuite.com/docx/xxxxxxxx  # 国际版
```

## 使用方式

配置完成后，通过 `skill:markdown-proxy` 指令抓取飞书文档：

```
skill:markdown-proxy https://xxx.feishu.cn/wiki/xxxxxxxx
```

## 故障排查

| 问题 | 原因 | 解决 |
|------|------|------|
| 返回权限错误 | 应用没有文档读取权限 | 检查权限管理，确认已开通 `docx:document:readonly` |
| 知识库页面抓取失败 | 缺少 wiki 权限 | 添加 `wiki:wiki:readonly` 权限 |
| App Secret 无效 | 应用未发布 | 确认应用已发布上线 |
| 内容为空 | 文档是私有的且你无权访问 | 确认文档对你的账号可见 |
