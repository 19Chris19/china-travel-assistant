# 凭据申请与安全配置

最后核验：`2026-09-28`。额度、价格、试用期限以供应商控制台为准，本文不保证固定赠送额度。

## 桌面端

在 macOS 上，`scripts/setup-credentials.sh` 打开本机回环地址的固定配置页，由你亲自填写，保存到 Keychain。配置页需要 Node.js 22.18+ 与 npm，但核心 CLI 安装不需要它。每个供应商有独立 profile，运行时仅将对应 Key 注入对应子进程。Windows Credential Manager、Linux Secret Service 后端尚未实机验证。

```bash
./scripts/setup-credentials.sh amap
./scripts/setup-credentials.sh flyai
./scripts/setup-credentials.sh variflight
travel-assistant doctor
```

**不读取旧 `credentials.env`**，也不自动迁移其中的 Key。曾在聊天、代码或旧文件暴露的 Key，请先到官方控制台轮换，再在配置页重新填写；确认 `doctor` 状态后，自行清理旧明文文件。不要把 Key 粘贴到对话、命令行参数、MCP URL、截图、日志、Issue 或 Git。

| 能力 | 官方申请与配置入口 | 凭据或运行时 | 备注 |
| --- | --- | --- | --- |
| 高德 Web Service | [创建项目与 Key](https://lbs.amap.com/api/webservice/create-project-and-key)、[额度与计费](https://lbs.amap.com/pages/base_service_price) | `AMAP_WEBSERVICE_KEY`，配置页 `amap` | 国内 POI、附近搜索、接驳、门户发现；Key 类型必须是 Web 服务 |
| 高德 JS API | [JS API v2 前置准备](https://lbs.amap.com/api/javascript-api-v2/prerequisites) | `AMAP_JSAPI_KEY`、`AMAP_SECURITY_CODE` | 当前静态 HTML/SVG 不需要；将来做交互地图才配置 |
| FlyAI / 飞猪 | [开放平台](https://open.fly.ai/)、[快速开始](https://open.fly.ai/docs/quickstart) | `FLYAI_API_KEY`，配置页 `flyai` | CLI `@fly-ai/flyai-cli@1.0.16`；不是 Codex 直连 MCP；免费额度与有效期以账户为准 |
| 飞常准 | [开放平台](https://ai.variflight.com/) | `VARIFLIGHT_API_KEY`，配置页 `variflight` | MCP `@variflight-ai/variflight-mcp@1.0.3` 为可选航班运行增强；试用额度、有效期与收费以账户为准 |
| QWeather | [项目和凭据](https://dev.qweather.com/docs/configuration/project-and-key/)、[JWT 认证](https://dev.qweather.com/docs/configuration/authentication/)、[订阅说明](https://dev.qweather.com/docs/finance/subscription/) | 见下方 `settings.env` | 可选天气与户外风险；遵守署名、额度和许可 |
| 12306 MCP | [固定 Fork](https://github.com/19Chris19/mcp-server-12306) | 无查询 Key；需要 `uvx` | 实时余票、票价仍以官方结果为准 |
| Ego Browser | [上游项目](https://github.com/citrolabs/ego-lite) | 无本项目 API Key | 浏览器应用管理登录态，本项目不读取 Cookie |
| Visualize | [官方说明](https://learn.chatgpt.com/docs/visualizations) | 无本项目 API Key | 宿主协商；不可用时使用本地 HTML/SVG |

`VIGOLIVE_API_KEY` 仅为 v2 租房预留，v0.3 不加载也不提示配置。

## QWeather JWT

在 [QWeather 控制台](https://console.qweather.com/)创建项目、上传 Ed25519 公钥，并取得项目专用 HTTPS API Host。不要复制其他项目的 Host。私钥放在仓库外的绝对路径，权限必须为 `0600`，不能把私钥内容写到 `settings.env`。非敏感字段可写在 `~/.config/china-travel-assistant/settings.env`：

```dotenv
QWEATHER_API_HOST=https://your-project.qweatherapi.com
QWEATHER_KEY_ID=
QWEATHER_DEVELOPER_ID=
QWEATHER_PROJECT_ID=
QWEATHER_PRIVATE_KEY_PATH=/absolute/path/outside/repository/qweather-ed25519-private.pem
```

默认 `doctor` 只校验配置和权限，不请求服务；`doctor --live` 才会尝试最小在线连通性测试，可能消耗额度。天气结果须标注 QWeather 来源。

## 无界面运行

CI、容器与无界面场景可由启动环境**显式注入**供应商变量；桌面端不从普通 `.env` 文件回退。注入时按供应商限制进程范围：12306 无 Key，飞常准子进程只收到飞常准 Key，FlyAI 子进程只收到 FlyAI Key。不要把变量写进公开 CI 日志或仓库。

`doctor` 状态包括 `ready`、`missing`、`expired`、`forbidden`、`rate_limited`、`degraded`、`unknown`、`not_required`。默认 `ready` 只代表配置或运行时检查通过，不代表票价、余票或天气已实时核验。若 401、403、429 或余额不足，检查对应供应商控制台并采用明确降级路径；不要伪造结果或暴力重试。
