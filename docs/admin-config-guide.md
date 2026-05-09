# 配置项获取指南

Admin 管理页面中每个配置项的获取方法。按需配置，不用的功能可以留空。

---

## 🤖 AI 配置（必填）

这三项决定了 msgflow 用哪个 AI 模型来执行任务。

### API Key

**是什么**：AI 模型提供商给你的密钥，相当于"通行证"。

**如何获取**：

| 提供商 | 获取地址 | 格式示例 |
|--------|---------|---------|
| 小米 MiMo | https://mimo.xiaomi.com → 控制台 → API Keys | `sk-xxxxxxxx` |
| OpenAI | https://platform.openai.com/api-keys → Create new | `sk-proj-xxxxxxxx` |
| DeepSeek | https://platform.deepseek.com/api_keys | `sk-xxxxxxxx` |
| 硅基流动 | https://cloud.siliconflow.cn/account/ak → 新建 | `sk-xxxxxxxx` |

注册后一般有免费额度可以试用。

### Base URL

**是什么**：AI 模型的 API 接口地址，告诉 msgflow 把请求发到哪里。

**常见值**：

| 提供商 | Base URL |
|--------|----------|
| 小米 MiMo | `https://token-plan-sgp.xiaomimimo.com/v1` |
| OpenAI | `https://api.openai.com/v1` |
| DeepSeek | `https://api.deepseek.com/v1` |
| 硅基流动 | `https://api.siliconflow.cn/v1` |

直接复制对应的地址粘贴即可。

### Model

**是什么**：要使用的模型名称。不同模型能力和价格不同。

**常见值**：

| 提供商 | 推荐模型 | 说明 |
|--------|---------|------|
| 小米 MiMo | `mimo-v2.5-pro` | 性价比高，中文好 |
| OpenAI | `gpt-4o` | 综合能力强 |
| DeepSeek | `deepseek-chat` | 便宜，中文好 |
| 硅基流动 | `Qwen/Qwen2.5-72B-Instruct` | 免费额度多 |

---

## 📦 集成配置（按需填写）

以下配置对应不同功能，不用的可以留空。

### 墨问 API Key

**是什么**：墨问写作平台的密钥，用于把改写后的文章自动发布到墨问。

**不用墨问？** 留空即可，改写结果会直接回传到聊天。

**如何获取**：
1. 注册 https://www.mowen.cn
2. 登录后进入「设置」→「开发者」→「API Key」
3. 点击「生成」，复制 key（格式：`mk-xxxxxxxx`）

### Unsplash Key

**是什么**：Unsplash 免费图片平台的密钥，用于自动给文章配封面图。

**不需要封面图？** 留空即可。

**如何获取**：
1. 注册 https://unsplash.com/join
2. 打开 https://unsplash.com/oauth/applications → New Application
3. 勾选同意条款，填写应用名（随便写，如 `msgflow`）
4. 创建后页面下方找到 **Access Key**，复制

### Wiki Repo

**是什么**：你的知识库 GitHub 仓库地址，格式为 `用户名/仓库名`。

**不用知识库功能？** 留空即可，`摄入` 和 `查询` 指令将不可用。

**如何设置**：
1. 在 GitHub 创建一个新仓库（如 `my-wiki`），可以是私有的
2. 填入格式：`你的用户名/my-wiki`（如 `zhangsan/my-wiki`）

### Wiki Token

**是什么**：GitHub Personal Access Token，让 msgflow 能读写你的私有知识库仓库。

**仓库是公开的？** 也需要 token（因为要写入内容）。

**如何获取**：
1. 打开 https://github.com/settings/tokens?type=beta
2. 点击 **Generate new token**
3. 填写：
   - Token name：`msgflow-wiki`
   - Expiration：选 90 天或更长
   - Repository access：**Only select repositories** → 选你的知识库仓库
   - Permissions → Repository permissions：
     - **Contents**：Read and write
4. 点击 Generate token
5. **立即复制**（只显示一次！格式：`ghp_xxxxxxxx`）

### 任务超时(秒)

**是什么**：AI 执行一个任务最多等多久。超时后任务会被终止。

**建议值**：
- 普通任务（抓取、改写）：`600`（10 分钟，默认值）
- 复杂任务（蒸馏、长文改写）：`1800`（30 分钟）

一般保持默认 `600` 即可，遇到超时再调大。

---

## 💡 最简配置

如果你只想用「发 URL 抓取为 Markdown」功能，只需填 3 项：

1. **API Key** — 任意一家 AI 提供商的 key
2. **Base URL** — 对应的 API 地址
3. **Model** — 对应的模型名

其他全部留空，就能用了。
