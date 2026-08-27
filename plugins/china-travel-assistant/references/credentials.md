# 凭据申请、额度与本地配置

最后核验：`2026-08-27`。配额、试用金、有效期和产品权限可能变化，官方控制台永远高于本文快照。

本项目只在本机读取凭据。真实值统一放在 `~/.config/china-travel-assistant/credentials.env`，文件权限必须是 `0600`；环境变量会覆盖同名文件值。不要把 Key 放进命令行参数、远程 MCP URL、README、截图、Issue、HTML、日志或提交记录。

## 总览

| 变量或运行时 | Key 类型 | v0.2 必需 | 官方入口 | 已核验额度与有效期 |
| --- | --- | --- | --- | --- |
| `AMAP_WEBSERVICE_KEY` | 高德 Web Service Key | 接驳/POI 必需 | [创建项目与 Key](https://lbs.amap.com/api/webservice/create-project-and-key) | 个人认证非商业用途有自认证日起一年的免费月配额；当前基础 LBS `150,000/月`、基础搜索 `5,000/月` |
| `AMAP_JSAPI_KEY` | 高德 JS API Key | 否 | [JS API v2 前置准备](https://lbs.amap.com/api/javascript-api-v2/prerequisites) | 跟随高德账户和应用类型；v0.2 精确 HTML/SVG 不依赖它 |
| `AMAP_SECURITY_CODE` | JS API 安全密钥 | 否 | 高德控制台 JS API 应用详情 | 与对应 JS API Key 配套，不是 Web Service Key |
| `FLYAI_API_KEY` | FlyAI Open Platform API Key | 航班/酒店增强可选 | [FlyAI Open Platform](https://open.fly.ai/) | 官网未公开固定赠送额度或统一有效期；以账户控制台为准 |
| `VARIFLIGHT_API_KEY` | 飞常准 Aviation MCP/API Key | 否 | [Variflight AI Open Platform](https://ai.variflight.com/) | 官网当前写明新用户 `¥50` 试用额度；有效期和可用接口以控制台为准 |
| `VIGOLIVE_API_KEY` | 未来租房供应商 Key | 否 | 尚未纳入 v0.2 | 仅 v2 预留，v0.2 运行时不读取 |
| 12306 MCP | 无查询 Key | 火车能力需要运行时 | [12306 MCP Fork](https://github.com/19Chris19/mcp-server-12306) | 公共查询不要求 API Key，余票仍以 12306 实时结果为准 |
| Ego Browser | 无本项目 API Key | 登录页核验时需要 | [ego-lite](https://github.com/citrolabs/ego-lite) | 登录态由独立应用管理；当前上游说明 macOS 可用，Windows/Linux 在路线图中 |
| Visualize | 无本项目 API Key | 否 | [Visualizations 官方说明](https://learn.chatgpt.com/docs/visualizations) | 逐步开放，取决于账号、平台、版本和工作区；Codex CLI/IDE 当前不渲染 |

## 高德 Web Service

1. 注册并完成适合用途的开发者认证。
2. 在控制台创建应用，添加 `Web服务` Key，写入 `AMAP_WEBSERVICE_KEY`。
3. 查看[基础服务计费页](https://lbs.amap.com/pages/base_service_price)和[服务升级页](https://lbs.amap.com/upgrade)。当前官方口径是：非商业目的个人认证开发者自注册认证日起享有一年的免费月配额，个人认证的基础 LBS 服务为 `150,000/月`、QPS `3`，基础搜索为 `5,000/月`、QPS `3`。
4. 月配额超限后按官方规则付费购买或等待新周期，不要通过重试绕过限额。商业、组织或高调用量用途应按高德协议选择企业认证或技术服务许可。

`AMAP_JSAPI_KEY` 和 `AMAP_SECURITY_CODE` 只在未来使用高德 JS 地图时需要。v0.2 的路线适配器只读 `AMAP_WEBSERVICE_KEY`，本地 HTML/SVG 行程板也不在 URL 中携带任何 Key。

常见状态：未填或运行时未读取为 `missing`；Key 类型错误或权限不足通常为 `forbidden`；超过配额通常为 `rate_limited` 或 `degraded`。控制台中的应用类型、服务开通和用量记录是排查依据。

## FlyAI / 飞猪 CLI

1. 从 [FlyAI Open Platform](https://open.fly.ai/) 登录控制台并按账户页面申请 API Key。
2. 将值写入 `FLYAI_API_KEY`；CLI 固定为 `@fly-ai/flyai-cli@1.0.16`。
3. FlyAI 在本项目中是调用飞猪能力的 CLI，不是 Codex 直接连接的 MCP。

FlyAI 官网在核验日没有公开承诺固定赠送额度、统一试用有效期或统一超额价格，因此本文不猜测。无 Key 时能否返回公共结果、特定能力是否收费以及账户余额，都以 CLI 实际响应和控制台为准。失败时保持航班/酒店结果为部分状态，不把它伪装成 `ready`。

## 飞常准

1. 从 [Variflight AI Open Platform](https://ai.variflight.com/) 注册并创建 Key，写入 `VARIFLIGHT_API_KEY`。
2. v0.2 固定外部依赖 `@variflight-ai/variflight-mcp@1.0.3`，只用于按需增强航班状态、准点率和价格证据，不是核心发布的单点依赖。
3. 官方首页当前写明新用户注册可获 `¥50` Aviation MCP 试用额度；没有在公开页承诺统一有效期。余额、截止日期、接口权限和超额计费必须查看当前账户控制台。

`401` 通常归类为 `expired` 或无效凭据，`403` 为 `forbidden`，余额不足为 `degraded`，`429` 为 `rate_limited`。这些状态必须触发可解释降级，不能用推测值补齐飞常准字段。

## 12306、Ego Browser 与 Visualize

- 12306 公共查询不需要 API Key。本项目使用固定提交的 Fork 以 stdio MCP 运行；“进程可启动”与“Codex 已正式加载”是两种状态，需在重启后分别验证。
- Ego Browser 不把 Cookie 或登录凭据写入本项目文件。只有 `$verify-travel-web` 可以调用它；验证码、登录交接、下单和支付都停下来让用户接管。上游开源仓库是 Skill/harness，浏览器应用是独立运行时。
- Visualize 不使用本项目 Key。`$present-china-trip` 在支持的宿主中优先调用它；不可用时输出无远程脚本的本地 HTML/SVG。不要为了出现 Visualize 而向用户索取账号密码或建议使用非官方中转登录。

## 安装与填写

1. 在仓库根目录初始化文件：

   ```bash
   ./scripts/setup-credentials.sh
   ```

2. 用本机编辑器填写已经轮换过的新值。不要把真实 Key 粘贴到 Agent 对话：

   ```dotenv
   AMAP_WEBSERVICE_KEY=
   AMAP_JSAPI_KEY=
   AMAP_SECURITY_CODE=
   FLYAI_API_KEY=
   VARIFLIGHT_API_KEY=
   VIGOLIVE_API_KEY=
   ```

3. 确认权限，不要把文件复制进仓库：

   ```bash
   chmod 600 "$HOME/.config/china-travel-assistant/credentials.env"
   ls -l "$HOME/.config/china-travel-assistant/credentials.env"
   ```

4. 运行默认离线检查：

   ```bash
   travel-assistant doctor
   ```

   默认只显示配置、版本和错误类别，不显示 Key，也不发送付费请求。

5. 只有在明确允许最小在线探测且确认账户可能产生调用费用时运行：

   ```bash
   travel-assistant doctor --live
   ```

## 读取优先级与错误分类

```text
进程环境变量 > ~/.config/china-travel-assistant/credentials.env > 未配置
```

| 状态 | 含义 | 处理 |
| --- | --- | --- |
| `ready` | 配置存在且已通过对应级别验证 | 正常调用；仍保留动态查询时间 |
| `missing` | 没有配置变量、CLI、MCP 或宿主能力 | 按上表申请、安装或使用回退 |
| `expired` | 凭据无效、过期或返回 401 | 在官方控制台轮换后只写入本地文件 |
| `forbidden` | 账号、套餐、应用类型或接口无权限，常见于 403 | 检查产品权限和服务条款，不暴力重试 |
| `rate_limited` | 请求过快或超过额度，常见于 429 | 等待、降低频率或在控制台检查配额 |
| `degraded` | 余额不足、部分结果、宿主不支持或证据不完整 | 保留成功来源与未知字段，使用声明的降级路径 |

任何曾在聊天、代码、日志或历史配置中暴露的 Key 都必须先在提供商控制台轮换，再写入新的 `0600` 文件。提交前运行 `gitleaks detect --no-banner --redact --source .`。
