# 凭据申请与本地配置

本项目只在本机读取凭据。真实值统一放在 `~/.config/china-travel-assistant/credentials.env`，文件权限必须是 `0600`；环境变量会覆盖同名文件值。不要把 Key 放进命令行参数、远程 MCP URL、README、截图、Issue、HTML、日志或提交记录。

## 申请入口

| 变量 | 提供商 | 官方申请/配置入口 | 必需 | 用途 |
| --- | --- | --- | --- | --- |
| `AMAP_WEBSERVICE_KEY` | 高德地图 Web Service | [创建项目与 Key](https://lbs.amap.com/api/webservice/create-project-and-key) | 是 | POI 搜索、公交/驾车/步行路线 |
| `AMAP_JSAPI_KEY` | 高德地图 JS API | [JS API v2 前置准备](https://lbs.amap.com/api/javascript-api-v2/prerequisites) | 否 | 可选交互地图展示 |
| `AMAP_SECURITY_CODE` | 高德地图 JS API | 在高德控制台的 JS API 应用详情中查看安全密钥 | 否 | 仅在 JS API 前端调用需要；Web Service 路线适配器不读取 |
| `FLYAI_API_KEY` | FlyAI / 飞猪 | [FlyAI Open Platform](https://open.fly.ai/) | 否 | FlyAI CLI 的增强访问；CLI 固定为 `@fly-ai/flyai-cli@1.0.16` |
| `VARIFLIGHT_API_KEY` | 飞常准 | [Variflight AI Open Platform](https://ai.variflight.com/) | 否 | 航班状态、准点率或价格增强核验；受账户额度和权限控制 |
| `VIGOLIVE_API_KEY` | Vigolive | 尚未纳入 v1 | 否 | v2 租房适配器预留，当前运行时不读取 |

12306 公共查询不要求 API Key。本项目使用固定提交的 [12306 MCP Fork](https://github.com/19Chris19/mcp-server-12306)。Ego Browser 的登录态由其独立应用管理，不写入本文件；浏览器自动化只走 Ego Browser。

## 安装与填写

1. 在仓库根目录运行初始化脚本：

   ```bash
   ./scripts/setup-credentials.sh
   ```

2. 用本机编辑器打开 `~/.config/china-travel-assistant/credentials.env`，只填写申请到的值。模板只包含变量名，不需要添加引号：

   ```dotenv
   AMAP_WEBSERVICE_KEY=
   AMAP_JSAPI_KEY=
   AMAP_SECURITY_CODE=
   FLYAI_API_KEY=
   VARIFLIGHT_API_KEY=
   VIGOLIVE_API_KEY=
   ```

3. 确认权限，不要把文件复制到仓库：

   ```bash
   chmod 600 "$HOME/.config/china-travel-assistant/credentials.env"
   ls -l "$HOME/.config/china-travel-assistant/credentials.env"
   ```

4. 运行默认离线检查：

   ```bash
   travel-assistant doctor
   ```

   该命令只显示是否已配置、版本和错误类别，不显示 Key 内容，也默认不发送付费请求。

5. 只有在明确允许在线探测时运行：

   ```bash
   travel-assistant doctor --live
   ```

   在线探测使用最小请求，仍不会在输出中打印凭据。

## 变量优先级

同名环境变量优先于凭据文件值。这适合一次性测试，但不要把真实值写进 Shell 历史或命令行：

```text
进程环境变量 > ~/.config/china-travel-assistant/credentials.env > 未配置
```

12306 和 Ego Browser 不需要把登录信息写入本项目配置。FlyAI 是 CLI，不要把它描述成 Codex 直接连接的 MCP；Variflight 是可选增强源，额度不足时必须降级并保留缺失字段。

## 错误分类

| 状态 | 含义 | 处理 |
| --- | --- | --- |
| `ready` | 配置存在且本地运行时可用 | 正常调用 |
| `missing` | 没有配置变量、CLI 或 MCP | 按上表申请或安装 |
| `expired` | 凭据已过期或返回 401 | 在官方控制台重新申请并替换本地值 |
| `forbidden` | 账号、套餐或接口无权使用，常见于 403 | 检查产品权限和服务条款，不重复暴力重试 |
| `rate_limited` | 请求过快或超过额度，常见于 429 | 等待、降低频率或检查额度 |
| `degraded` | 服务返回余额不足、部分结果或非完整字段 | 保留来源和缺失字段，切换已声明的增强/降级路径 |

任何曾在聊天、代码、日志或历史配置中暴露的 Key 都应先在提供商控制台轮换，再写入新的 `0600` 文件。提交前运行 `gitleaks detect --no-banner --redact --source .`。
