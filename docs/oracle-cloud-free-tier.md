# Oracle Cloud Free Tier 申请教程

## 你能得到什么（永久免费）

| 资源 | 额度 |
|------|------|
| ARM CPU | 4 OCPU (Ampere A1)，可拆成 1-4 个 VM |
| 内存 | 24 GB RAM（总量分配） |
| 块存储 | 200 GB |
| 对象存储 | 20 GB |
| 出站流量 | 10 TB/月 |
| 负载均衡 | 1 个 Flexible LB |
| x86 VM | 2 个 micro（1/8 OCPU + 1 GB），聊胜于无 |

另外还有 30 天 $300 试用额度，可以体验付费服务。试用结束后 Always Free 资源不受影响。

---

## 申请步骤

### 第一步：准备材料

- 一个有效邮箱（建议用 Gmail/Outlook，企业邮箱通过率更高）
- 一张信用卡或借记卡（Visa/Mastercard，**不扣费**，仅验证身份）
- 手机号（接收验证码）
- 真实姓名和地址（必须和信用卡账单地址一致）

> ⚠️ 不接受：虚拟卡、预付卡、单次使用卡。

### 第二步：注册

1. 打开 https://signup.cloud.oracle.com/
2. 填写：
   - **Country/Territory** — 选择你的真实所在地
   - **Name** — 和信用卡持卡人一致
   - **Email** — 填写后点验证，去邮箱点确认链接
3. 设置密码（Oracle 账号密码）
4. 填写 **Cloud Account Name** — 这是你的租户名，全局唯一，建议用简短英文（如 `mylab2026`）

### 第三步：选择 Home Region

**这一步非常重要，选了不能改。**

推荐选择：
- **日本 (Tokyo / Osaka)** — 离中国近，延迟低
- **韩国 (Seoul / Chuncheon)** — 同上
- **新加坡 (Singapore)** — 东南亚节点
- **美西 (US West - Phoenix / San Jose)** — ARM 容量相对充足

> 💡 热门区域（如 US East Ashburn）经常 ARM 容量不足，创建 VM 时会报 "Out of host capacity"。选冷门区域成功率更高。

### 第四步：验证身份

1. 填写地址（必须和信用卡账单地址一致）
2. 填写手机号，接收短信验证码
3. 输入信用卡信息
   - Oracle 会发起一笔临时授权（通常 $1 或 $0），3-5 天内自动释放
   - **不会实际扣款**

### 第五步：等待审核

- 大多数情况下即时通过
- 少数情况需要人工审核（几小时到几天）
- 如果被拒，可以用页面右上角 Chat 联系客服

审核通过后会收到邮件，可以登录 https://cloud.oracle.com

---

## 创建 ARM VM

### 1. 先创建网络（VCN）

> ⚠️ 必须先做这一步，否则创建实例时无法分配 Public IP（按钮灰色不可点）。

1. 菜单 → **Networking** → **Virtual Cloud Networks**
2. 点击 **Start VCN Wizard**
3. 选择 **Create VCN with Internet Connectivity** → Start VCN Wizard
4. 填写名字（如 `vcn-main`），其他保持默认
5. 点击 **Create** → 等待完成

Wizard 会自动创建：
- Public Subnet（关联 Internet Gateway，允许分配 Public IP）
- Private Subnet（关联 NAT Gateway，无 Public IP）
- 路由表和安全规则

### 2. 创建实例

菜单 → Compute → Instances → **Create Instance**

### 3. 配置实例

| 配置项 | 推荐值 |
|--------|--------|
| Name | `msgflow-runner` |
| Image | Oracle Linux 9 或 Ubuntu 22.04 Minimal |
| Shape | VM.Standard.A1.Flex |
| OCPU | 4（用满免费额度） |
| Memory | 24 GB（用满） |
| Boot Volume | 50 GB（免费 200 GB 内可调） |

### 4. 网络配置（关键）

- **Virtual cloud network** — 选上一步创建的 VCN（如 `vcn-main`）
- **Subnet** — 必须选 **Public Subnet**（名字里带 "Public" 的那个）
- **Assign a public IPv4 address** — 勾选 ✓

> ⚠️ 如果选了 Private Subnet，Public IP 开关会灰色不可点。必须选 Public Subnet。

### 5. SSH 密钥

- 上传你的公钥（`~/.ssh/id_rsa.pub`）
- 或让 Oracle 生成，下载私钥保存好

### 6. 点击 Create

如果报 "Out of host capacity"：
- 换一个 Availability Domain 重试
- 或等几小时/几天再试（热门区域常见）
- 或减少 OCPU/RAM 配置（如 2C/12G）先创建，后续再调整

---

## 创建后的安全配置

### 开放端口（Security List）

默认只开了 22 (SSH)。如果要跑 HTTP 服务：

1. Networking → Virtual Cloud Networks → 你的 VCN
2. Security Lists → Default Security List
3. Add Ingress Rules:
   - Source: `0.0.0.0/0`，Protocol: TCP，Port: `80,443`

### 防火墙（VM 内部）

Oracle Linux 默认有 iptables 规则，需要额外放行：

```bash
sudo iptables -I INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT -p tcp --dport 443 -j ACCEPT
sudo netfilter-persistent save
```

Ubuntu 则用：

```bash
sudo iptables -I INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT -p tcp --dport 443 -j ACCEPT
sudo apt install iptables-persistent -y
```

---

## 防止被回收

Oracle 会回收闲置的 Always Free 实例。规则：

> 连续 7 天 CPU 使用率 < 10% 的实例可能被标记为 idle 并回收。

解决方案 — 加一个简单的 cron 保活：

```bash
# 每 6 小时跑一次轻量计算，保持 CPU 活跃
echo "0 */6 * * * /usr/bin/nice -n 19 /usr/bin/stress-ng --cpu 1 --timeout 120s" | sudo tee /etc/cron.d/keepalive
```

或者如果你在上面跑 GitHub Actions Runner / NullClaw 任务，正常使用就不会触发回收。

---

## 提高通过率的技巧

1. **用真实信息** — 姓名、地址、手机号必须和信用卡一致
2. **用企业邮箱** — 比 Gmail 通过率高
3. **避免 VPN** — 注册时 IP 地址应该和你选的 Home Region 在同一国家
4. **一人一号** — Oracle 严格限制每人一个免费账号，重复注册会被封
5. **选冷门区域** — 避开 US East (Ashburn)，选 Phoenix、Tokyo、Seoul

---

## 常见问题

**Q: 会不会被扣费？**
A: 不会。Always Free 资源不计费。只有你手动升级为 Pay As You Go 并创建付费资源才会扣费。

**Q: 试用期结束后 VM 会被删吗？**
A: 不会，只要你的 VM 是 Always Free shape (A1.Flex ≤ 4 OCPU / 24 GB)。试用期结束只回收付费资源。

**Q: 被拒了怎么办？**
A: 用 Oracle 官网右上角 Chat 联系客服，说明情况。或换一个邮箱重新注册（注意不要用同一张卡）。

**Q: ARM 跑不了 x86 程序怎么办？**
A: 大多数工具（Node.js、Python、Go、Zig）都有 ARM 版本。NullClaw 如果提供 ARM 二进制就能直接跑。实在不行可以用 2 个 x86 micro VM（但只有 1G 内存，很受限）。
