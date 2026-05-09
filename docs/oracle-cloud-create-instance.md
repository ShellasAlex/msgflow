# Oracle Cloud 创建 ARM 实例教程

> 前置条件：已完成 Oracle Cloud Free Tier 注册并能登录 https://cloud.oracle.com
> 参考：[Oracle Cloud Free Tier 申请教程](./oracle-cloud-free-tier.md)

---

## 第一步：创建网络（VCN）

> ⚠️ **必须先做这一步**。如果跳过直接创建实例，"Assign public IPv4 address" 按钮会灰色不可点。原因是默认网络没有 Internet Gateway，无法分配公网 IP。

1. 登录 Oracle Cloud Console
2. 左上角菜单 → **Networking** → **Virtual Cloud Networks**
3. 确认左下角 Compartment 选的是你的 root compartment
4. 点击 **Start VCN Wizard**
5. 选择 **Create VCN with Internet Connectivity** → 点击 **Start VCN Wizard**
6. 填写配置：

| 配置项 | 推荐值 |
|--------|--------|
| VCN Name | `vcn-main` |
| VCN IPv4 CIDR Block | `10.0.0.0/16`（默认） |
| Public Subnet CIDR | `10.0.0.0/24`（默认） |
| Private Subnet CIDR | `10.0.1.0/24`（默认） |

7. 点击 **Create** → 等待所有资源创建完成（约 30 秒）

创建完成后你会看到以下资源：

| 资源 | 用途 |
|------|------|
| Public Subnet | 放需要公网访问的实例（有 Internet Gateway） |
| Private Subnet | 放内部服务（通过 NAT Gateway 出站，无公网 IP） |
| Internet Gateway | 让 Public Subnet 的实例可被外部访问 |
| NAT Gateway | 让 Private Subnet 的实例可以访问外网 |
| Route Tables | 路由规则（已自动配好） |
| Security Lists | 防火墙规则（默认开放 SSH 22 端口） |

---

## 第二步：创建 Compute 实例

1. 左上角菜单 → **Compute** → **Instances**
2. 点击 **Create Instance**

---

## 第三步：基本配置

| 配置项 | 操作 |
|--------|------|
| **Name** | 填一个有意义的名字，如 `arm-runner` |
| **Compartment** | 保持默认（root） |
| **Availability Domain** | 如果有多个 AD，选 AD-1（容量不足时换其他 AD） |

---

## 第四步：选择镜像和 Shape

### Image（操作系统）

点击 **Edit** → **Change Image**：

| 推荐镜像 | 说明 |
|----------|------|
| **Ubuntu 22.04 Minimal (aarch64)** | 轻量，适合跑服务 |
| **Ubuntu 24.04 (aarch64)** | 更新，软件包更全 |
| Oracle Linux 9 (aarch64) | Oracle 官方维护，兼容 RHEL |

> 注意选 **aarch64** 版本（ARM 架构）。

### Shape（机型）

点击 **Change Shape**：

1. Shape type 选 **Virtual machine**
2. Shape series 选 **Ampere**（ARM）
3. 选择 **VM.Standard.A1.Flex**
4. 配置资源：

| 资源 | 推荐值 | 说明 |
|------|--------|------|
| OCPU | **4** | 用满免费额度 |
| Memory | **24 GB** | 用满免费额度 |

> 💡 如果只需要一个实例，直接拉满 4C/24G。如果想拆成多个 VM，按需分配（如 2C/12G × 2）。

> ⚠️ **常见错误**：不要选错 Shape！
>
> | Shape | 架构 | 配置 | 免费额度 |
> |-------|------|------|----------|
> | **VM.Standard.A1.Flex** ✅ | ARM (aarch64) | 最高 4C/24G | Always Free |
> | VM.Standard.E2.1.Micro ❌ | x86_64 | 1/8 OCPU + 1 GB | Always Free 但太弱 |
>
> 如果你创建后 SSH 登录看到 `x86_64` 而不是 `aarch64`，说明选错了 Shape。需要终止实例重新创建。
>
> 验证方法：
> ```bash
> uname -m
> # 正确输出：aarch64
> # 错误输出：x86_64（说明选了 micro 实例）
> ```

---

## 第五步：网络配置（关键）

点击 Networking 部分的 **Edit**：

| 配置项 | 选择 |
|--------|------|
| **Virtual cloud network** | 选第一步创建的 `vcn-main` |
| **Subnet** | 选 **Public Subnet-vcn-main** |
| **Public IPv4 address** | 勾选 ✓ **Automatically assign public IPv4 address** |

> ⚠️ **常见问题**：如果 "Assign public IPv4 address" 是灰色不可点：
> - 检查 Subnet 是否选的 **Public** Subnet（名字里带 "Public"）
> - 如果选了 Private Subnet，切换到 Public Subnet 即可
> - 如果下拉里没有 Public Subnet，说明第一步没做或没用 "Internet Connectivity" 模板

---

## 第六步：SSH 密钥

选择 **Upload public key files** 或 **Paste public keys**：

```bash
# 本地查看你的公钥
cat ~/.ssh/id_rsa.pub
```

把内容粘贴进去。或者选 **Generate a key pair for me**，然后**立即下载私钥**（只显示一次）。

---

## 第七步：Boot Volume（可选）

默认 46.6 GB。如果需要更大：

1. 勾选 **Specify a custom boot volume size**
2. 填写大小（如 100 GB）
3. 免费额度内总共 200 GB，按需分配

---

## 第八步：点击 Create

等待实例状态变为 **RUNNING**（通常 1-2 分钟）。

### 如果报错 "Out of host capacity"

这是热门区域 ARM 容量不足，不是你的问题。解决方法：

1. **换 Availability Domain** — 如果你的 region 有多个 AD，换一个试试
2. **减少配置** — 先用 2C/12G 创建，后续再调整
3. **等待重试** — 几小时或几天后再试（Oracle 会补充容量）
4. **写脚本自动重试** — 用 OCI CLI 每隔几分钟尝试创建

```bash
# 自动重试脚本（可选）
while true; do
  oci compute instance launch --config-file ~/.oci/config \
    --availability-domain "AD-1" \
    --compartment-id "ocid1.compartment.oc1..xxx" \
    --shape "VM.Standard.A1.Flex" \
    --shape-config '{"ocpus":4,"memoryInGBs":24}' \
    --subnet-id "ocid1.subnet.oc1..xxx" \
    --image-id "ocid1.image.oc1..xxx" \
    --assign-public-ip true \
    && break
  echo "Capacity not available, retrying in 5 minutes..."
  sleep 300
done
```

---

## 第九步：连接实例

实例 RUNNING 后，在详情页找到 **Public IP Address**。

```bash
# Ubuntu 镜像默认用户名是 ubuntu
ssh -i ~/.ssh/id_rsa ubuntu@<你的公网IP>

# Oracle Linux 默认用户名是 opc
ssh -i ~/.ssh/id_rsa opc@<你的公网IP>
```

---

## 第十步：安全配置

### 开放端口（Security List）

默认只开了 22 (SSH)。如果需要 HTTP/HTTPS：

1. 菜单 → Networking → Virtual Cloud Networks → `vcn-main`
2. 左侧 **Security Lists** → **Default Security List for vcn-main**
3. **Add Ingress Rules**：

| Source CIDR | Protocol | Port | 说明 |
|-------------|----------|------|------|
| `0.0.0.0/0` | TCP | 80 | HTTP |
| `0.0.0.0/0` | TCP | 443 | HTTPS |
| `0.0.0.0/0` | TCP | 8080 | 自定义服务（按需） |

### VM 内部防火墙

Oracle 的镜像默认有 iptables 规则阻止入站流量（Security List 之外还有一层）：

**Ubuntu：**

```bash
sudo iptables -I INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT -p tcp --dport 443 -j ACCEPT
sudo apt install iptables-persistent -y
# 提示保存时选 Yes
```

**Oracle Linux：**

```bash
sudo firewall-cmd --permanent --add-port=80/tcp
sudo firewall-cmd --permanent --add-port=443/tcp
sudo firewall-cmd --reload
```

---

## 第十一步：防止 Idle 回收

Oracle 会回收连续 7 天 CPU 使用率 < 10% 的 Always Free 实例。

如果你的实例不是每天都有任务跑，加一个保活 cron：

```bash
# 安装 stress-ng
sudo apt install stress-ng -y  # Ubuntu
# 或
sudo dnf install stress-ng -y  # Oracle Linux

# 每 6 小时跑 2 分钟轻量 CPU 负载
echo "0 */6 * * * root /usr/bin/nice -n 19 /usr/bin/stress-ng --cpu 1 --timeout 120s >/dev/null 2>&1" | sudo tee /etc/cron.d/keepalive
sudo chmod 644 /etc/cron.d/keepalive
```

如果实例上有持续运行的服务（如 GitHub Actions Runner），正常使用就不会触发回收。

---

## 验证清单

创建完成后逐项确认：

- [ ] 实例状态为 RUNNING
- [ ] 有 Public IP 地址
- [ ] 能 SSH 连接
- [ ] `uname -m` 输出 `aarch64`（确认是 ARM）
- [ ] `free -h` 显示约 24 GB 内存
- [ ] `nproc` 输出 4

---

## 常见问题

**Q: 创建后 Public IP 显示为空？**
A: 检查是否勾选了 "Assign public IPv4 address"。如果忘了，可以事后绑定：实例详情 → Attached VNICs → 点击 VNIC → IPv4 Addresses → Edit → 选择 Ephemeral Public IP。

**Q: SSH 连接超时？**
A: 检查三层：① Security List 是否开了 22 端口 ② VM 内部防火墙是否放行 ③ 本地网络是否能访问该 IP

**Q: 想改配置（加减 CPU/内存）？**
A: 实例详情 → Edit → Edit Shape → 调整 OCPU 和 Memory → 需要重启实例生效。

**Q: 能不能跑 Docker？**
A: 可以。ARM 上 Docker 正常工作，大多数官方镜像都有 arm64 版本。

```bash
sudo apt install docker.io -y
sudo usermod -aG docker $USER
# 重新登录后生效
```
