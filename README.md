<p align="center">
  <img src="./assets/readme/china-travel-assistant.gif" width="100%" alt="中国出行助手：航班、铁路、酒店和城市接驳组成的一段动态联程路线">
</p>

<h1 align="center">远行计划局 · 中国出行 Agent Skill</h1>

<p align="center">
  面向 Agent 的中国境内出行规划 Skill Plugin：八个可独立调用的 Skills，用对话组合机票、12306 火车票、酒店、高德接驳、通用门户排序、地点事实与传统平台之外的多式联运路线。
</p>

<p align="center">
  <a href="https://github.com/19Chris19/china-travel-assistant/actions/workflows/ci.yml">CI</a> ·
  <a href="https://github.com/19Chris19/china-travel-assistant/releases/tag/v0.3.0">Release v0.3.0</a> ·
  <a href="./LICENSE">MIT License</a> ·
  <a href="https://github.com/19Chris19/china-travel-assistant/issues">Issues</a>
</p>

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="./assets/readme/china-travel-assistant-dark.jpeg">
    <source media="(prefers-color-scheme: light)" srcset="./assets/readme/china-travel-assistant-light.jpeg">
    <img src="./assets/readme/china-travel-assistant-dark.jpeg" width="100%" alt="中国出行助手旅程总览：飞机、高铁、酒店与城市路线组成完整联程">
  </picture>
</p>

<h2 id="quickstart">快速开始</h2>

<p align="center">
  <img src="./assets/readme/section-quickstart.svg" width="100%" alt="快速开始：从安装到第一次对话">
</p>

核心安装只要求 Python 3.10+、`pipx` 和 Codex。Node.js 22.18+、npm、`uvx` 与 [Ego Browser](https://github.com/citrolabs/ego-lite) 均为对应能力的可选依赖；缺少时 `doctor` 会说明降级。

```bash
git clone https://github.com/19Chris19/china-travel-assistant
cd china-travel-assistant
./scripts/install-local.sh
```

安装后完全退出并重启 Codex，使 Plugin 与 MCP 正式重载。按需安装增强能力并通过本机系统凭据页配置（macOS Keychain 已验证）：

```bash
./scripts/install-optional.sh --flyai
./scripts/setup-credentials.sh amap
./scripts/setup-credentials.sh flyai
./scripts/setup-credentials.sh variflight
travel-assistant doctor
```

第一句对话可以直接这样发：

```text
使用 $plan-china-trip，帮我比较沈阳到苏州周边机场的低价航班，
默认用智能选择（通常按拓界）主动探索飞铁联运，把机场接驳、学生票和含税总价一起算清楚。
```

默认 `doctor` 只检查本地配置、版本、私钥权限和运行时，不发送付费 API 请求；明确同意后才运行 `travel-assistant doctor --live`。它会安全返回 `ready`、`missing`、`expired`、`forbidden`、`rate_limited`、`degraded`、`unknown` 或 `not_required`，绝不回显凭据。

<h2 id="routing">能力路由</h2>

<p align="center">
  <img src="./assets/readme/section-routing.svg" width="100%" alt="能力路由：一个父 Skill 调度多个执行 Skill">
</p>

顶部 GIF 展示的是本项目的核心思路：Agent 先分别查询交通和住宿，再由路线推演器把航班、铁路、机场/车站接驳与酒店组合成可比较的行程，最后通过 Visualize 或精确本地文件交付。八个 Skills 可以由父 Skill 自动路由，也可以显式调用：

<p align="center">
  <img src="./assets/readme/skill-system-map.svg" width="100%" alt="八 Skill 系统：自然语言需求进入 plan-china-trip，再路由到供应商查询、路线推演和精确展示 Skill">
</p>

| Skill | 负责什么 | 主数据源 |
| --- | --- | --- |
| `$plan-china-trip` | 父 Skill：解析需求、调用其余 Skills、合并证据与推荐 | 全部已启用能力 |
| `$search-china-flights` | 国内航班、周边机场、票价和时间窗口 | FlyAI/飞猪 CLI；飞常准按需核验 |
| `$search-china-trains` | 12306 直达、换乘、余票、票价和链接 | 12306 MCP |
| `$plan-china-transfers` | POI 消歧、机场/车站接驳、公交地铁和步行 | 高德 Web Service 适配器 |
| `$search-china-hotels` | 酒店、房型、登录价、库存和取消条件 | FlyAI/飞猪；Ego Browser 页面核验 |
| `$verify-travel-web` | 页面证据、登录态交接和用户接管 | Ego Browser |
| `$explore-china-routes` | 路线推演器确定性组合、剪枝、风险和基准收益解释 | 已归一化的供应商行程腿 |
| `$present-china-trip` | Visualize 优先，HTML/SVG/Markdown 精确回退 | 同一份 `itinerary.json` |

租房搜索不在 v0.3 运行时中，相关能力计划在 v2 以原创适配器重新加入。

### 智能选择 / 从容 / 拓界 / 远征

三档共享同一套高基线能力：学生票、住宿、行李、税费、接驳、退改、疲劳、时间窗、证据和预订链接。档位只改变搜索广度、组合新颖度与可接受折腾程度，不会阉割基础功能。

| 档位 | 如何启用 | 探索风格 | 最高风险预算 |
| --- | --- | --- | --- |
| `从容` (`standard`) | 显式选择；或智能选择遇到只要直达、明确低风险、刚性到达约束 | 完整核验直达与附近门户，保留稳妥基准 | 稳妥 |
| `拓界` (`pro`) | 普通请求的智能选择默认 | 主动探索飞铁、铁飞、周边机场、沿途枢纽和分段票 | 可控 |
| `远征` (`pro_max`) | 只能由用户显式选择 | 扩展日期、枢纽、夜航与住宿组合，提供挑战路线 | 挑战 |

每个非传统方案必须解释相对基准收益、额外折腾、自助换乘、延误兜底、风险和证据。未知费用继续显示“未返回”，不会为了排序而猜一个数字。

### 数据源如何协作

<p align="center">
  <img src="./assets/readme/provider-workflow.svg" width="100%" alt="供应商工作流：解析需求、并发主查、按需增强核验、合成交付">
</p>

```text
自然语言需求
    -> plan-china-trip
    -> 高德发现通用门户 / FlyAI / 12306
    -> 飞常准按需增强
    -> QWeather 按需评估户外与接驳风险
    -> Ego Browser 仅核验登录价或页面证据
    -> explore-china-routes 组合与校验路线候选
    -> present-china-trip 选择 Visualize 或精确本地回退
    -> 输出比较结果、风险与真实平台链接
```

FlyAI 在本项目中是调用飞猪服务的 CLI，不是注册到 Codex 的直接 MCP。浏览器自动化只允许使用 Ego Browser；Kimi WebBridge、Chrome Control、Playwright 和旧租房 Skills 不属于 v0.3 调用链。

所有动态价格必须带来源和查询时间。缺失的票价、库存、行李或退改字段保持为“未返回”，不推断为已含税或有余票。

### 通用门户与地点事实

当用户所在城市没有机场，或附近存在多个可达机场/铁路门户时，Skill 不会将某个城市、机场或历史路线写死为规则。它会先用高德发现候选门户，再让航班、铁路与接驳 Skills 返回事实，按门到门已知总成本、耗时、换乘数、缓冲、时间窗、疲劳偏好和证据完整度确定性比较。

地面费用、营业状态或天气未返回时始终显示“未返回”，不会进入伪精确总价。高德提供国内 POI、周边与路径事实；FlyAI 提供机酒景产品；Ego Browser 只核验官方开放状态、库存或登录价。QWeather 是可选的户外风险层，会影响景点排序与接驳缓冲，但不替代票务、地图或开放事实。

### Visualize 优先，事实永远精确

在支持 [Visualizations](https://learn.chatgpt.com/docs/visualizations) 的 Codex/ChatGPT 宿主中，`$present-china-trip` 优先生成对话内交互行程板。该能力仍在逐步开放，是否出现取决于账号、平台、版本和工作区；官方当前说明 Codex CLI 与 IDE 扩展不渲染 Visualizations。

不可用时运行确定性本地回退：

```bash
travel-assistant plan --tier auto --presentation html < request-and-legs.json > itinerary.json
travel-assistant render-plan --format html --output itinerary.html < itinerary.json
travel-assistant render-plan --format svg --output itinerary.svg < itinerary.json
```

Visualize、HTML、SVG 和 Markdown 全部读取同一份 `itinerary.json`。ImageGen 不进入事实链，不能书写或重绘时间、价格、班次和链接；v0.3 只会考虑将它用于不承载事实的装饰背景和 MCP-backed App UI。

每张行程板顶部还有一条窄版数据健康条：只列出本次行程实际用到的供应商。`ready` 仅代表服务配置或探测正常，不代表某张票、余票、路线或天气已经核验；出现降级时，健康条会给出不含敏感值的配置建议，并链接到凭据说明。

<h2 id="security">配置安全</h2>

<p align="center">
  <img src="./assets/readme/section-security.svg" width="100%" alt="配置安全：真实 Key 由系统凭据存储，QWeather 私钥留在仓库外">
</p>

桌面端通过 `scripts/setup-credentials.sh` 打开本机配置页，分别写入系统凭据存储。运行时**不读取旧 `credentials.env`**；旧文件不会自动迁移，请轮换 Key 后重新填写，再自行清理旧文件。只有 CI、容器或无界面场景可显式注入环境变量。QWeather 非敏感参数可放 `settings.env`，私钥文件须在仓库外且权限 `0600`。不要把 Key 写进命令行参数、MCP URL、README、截图、Issue、HTML 或日志。完整步骤见 [`credentials.md`](plugins/china-travel-assistant/references/credentials.md)。

| 提供商 | 官方申请/配置入口 | 变量 | 用途 |
| --- | --- | --- | --- |
| 高德 Web Service | [创建项目与 Key](https://lbs.amap.com/api/webservice/create-project-and-key)；[计费与月配额](https://lbs.amap.com/pages/base_service_price) | `AMAP_WEBSERVICE_KEY` | POI、公交、驾车、步行等路线 |
| 高德 JS API | [JS API v2 前置准备](https://lbs.amap.com/api/javascript-api-v2/prerequisites) | `AMAP_JSAPI_KEY`、`AMAP_SECURITY_CODE` | 可选交互地图；不是路线服务必需项 |
| FlyAI / 飞猪 | [FlyAI Open Platform](https://open.fly.ai/) | `FLYAI_API_KEY` | 航班和酒店的增强访问；CLI 固定为 `@fly-ai/flyai-cli@1.0.16`，不是 Codex 直连 MCP |
| 飞常准 | [Variflight AI Open Platform](https://ai.variflight.com/) | `VARIFLIGHT_API_KEY` | 按需核验航班状态、准点率或价格；新用户试用与有效期以账户控制台为准 |
| QWeather | [项目与凭据](https://dev.qweather.com/docs/configuration/project-and-key/)；[JWT 认证](https://dev.qweather.com/docs/configuration/authentication/) | `QWEATHER_API_HOST`、`QWEATHER_KEY_ID`、`QWEATHER_DEVELOPER_ID`、`QWEATHER_PROJECT_ID`、`QWEATHER_PRIVATE_KEY_PATH` | 可选天气、预警、能见度与户外风险；私钥只放仓库外的 `0600` 文件 |
| Vigolive | 供应商账户 | `VIGOLIVE_API_KEY` | 仅 v2 租房预留，v0.3 不读取 |

12306 公共查询不要求 API Key；本项目使用固定提交的 [12306 MCP Fork](https://github.com/19Chris19/mcp-server-12306)。Ego Browser 的登录态由其独立应用管理，不写入本项目凭据文件。

<p align="center">
  <img src="./assets/readme/credential-boundary.svg" width="100%" alt="凭据边界：系统凭据按供应商最小注入；对话、MCP URL、日志和 Git 不含 Key">
</p>

### 给 Codex 的一键部署提示词

将下面整段交给 Codex。Codex Plugin、MCP 与 Visualize 是本版验证的首发体验；CLI、JSON 契约和 HTML/SVG 输出可移植，但其他 Agent 的直接安装尚未实机验证。

<details>
<summary>展开部署提示词</summary>

```text
请在当前机器部署以下仓库：
https://github.com/19Chris19/china-travel-assistant

1. 克隆仓库并阅读 README.md、SECURITY.md、THIRD_PARTY_NOTICES.md、provenance.yml 和 upstream-lock.yml。
2. 检查 Python 3.10+、pipx 和 Codex；Node.js 22.18+、npm、uvx、FlyAI、飞常准和 Ego Browser 为可选能力，缺少时不要阻塞核心安装。
3. 运行 ./scripts/install-local.sh。
4. 按需运行 ./scripts/install-optional.sh 和 ./scripts/setup-credentials.sh amap|flyai|variflight；只在本机配置页填写已轮换的 Key，桌面端写入 macOS Keychain，不创建明文 credentials.env。
5. 不要让我把 Key 粘贴到对话，不输出真实 Key，也不要把 Key 放进命令行、MCP URL、日志或文件提交；旧 credentials.env 不自动迁移，我会自行清理旧文件。
6. 如需户外风险，请引导我在本地创建 QWeather Ed25519 JWT 配置：QWEATHER_API_HOST、QWEATHER_KEY_ID、QWEATHER_DEVELOPER_ID、QWEATHER_PROJECT_ID 与仓库外、权限 0600 的 QWEATHER_PRIVATE_KEY_PATH；不要让私钥内容进入对话或仓库。
7. 运行 travel-assistant doctor；默认不要运行 doctor --live，除非我明确同意在线探测。
8. 检查八个 Agent Skills、china-12306 MCP、可选 variflight MCP、QWeather、Ego Browser Skill 和 Visualize 能力状态，并报告 ready、missing、expired、forbidden、rate_limited、degraded、unknown 或 not_required 类别。
9. 不启用 Kimi WebBridge、Chrome Control、Playwright 或 v2 租房 Skills；浏览器核验只使用 Ego Browser。
10. 提醒我完全退出并重启 Codex，使 Plugin、Skills 和 MCP 正式重载；Visualize 不可用时保留本地 HTML/SVG 回退，不要伪装成已调用。
11. 只完成安装、配置检查和预订链接准备；不执行实名、不执行下单、不执行支付、不执行退改。
```

</details>

<h2 id="sources">开源来源</h2>

<p align="center">
  <img src="./assets/readme/section-sources.svg" width="100%" alt="开源来源：区分真实 Fork、外部集成与架构参考">
</p>

本仓库原创编排代码与 Skills 采用 MIT。我们诚实区分三种关系：

- `forked_from`：在 `19Chris19` 账号下真实建立 Fork，并保留上游许可证和历史。
- `integrates_with`：运行时依赖外部 CLI、MCP、官方 API 或服务，没有把对方源码重新打包进本仓库。
- `inspired_by`：只借鉴架构或工作流，不复制源代码，也不把项目标记为 Fork。

<p align="center">
  <img src="./assets/readme/provenance-map.svg" width="100%" alt="来源关系矩阵：forked_from 保留历史与许可证，integrates_with 固定外部版本，inspired_by 不复制源码">
</p>

完整的源地址、许可证和修改说明：

- [第三方声明与所有源地址](THIRD_PARTY_NOTICES.md)
- [机器可读来源关系](provenance.yml)
- [Fork 提交与外部包版本锁定](upstream-lock.yml)
- [凭据申请和本地配置文档](plugins/china-travel-assistant/references/credentials.md)
- 本页的视觉整理参考了 [beautify-github-readme](https://github.com/oil-oil/beautify-github-readme)，仅作为 README 设计方法参考，没有复制其源码或标记为 Fork。

### 真实 Fork

- [19Chris19/mcp-server-12306](https://github.com/19Chris19/mcp-server-12306)，上游 [drfccv/mcp-server-12306](https://github.com/drfccv/mcp-server-12306)
- [19Chris19/amap-lbs-skill](https://github.com/19Chris19/amap-lbs-skill)，上游 [AMap-Web/amap-lbs-skill](https://github.com/AMap-Web/amap-lbs-skill)
- [19Chris19/flyai-skill](https://github.com/19Chris19/flyai-skill)，上游 [alibaba-flyai/flyai-skill](https://github.com/alibaba-flyai/flyai-skill)
- [19Chris19/universal-travel-planner-skill](https://github.com/19Chris19/universal-travel-planner-skill)，历史流程参考 [chaoliuzhu65-tech/universal-travel-planner-skill](https://github.com/chaoliuzhu65-tech/universal-travel-planner-skill)
- [19Chris19/x-cli](https://github.com/19Chris19/x-cli)，仅作 legacy 研究，不进入 v0.3 运行时；上游 [better-world-ai/x-cli](https://github.com/better-world-ai/x-cli)
- [19Chris19/ego-lite](https://github.com/19Chris19/ego-lite)，Ego Browser 外部运行时与 Skill；上游 [citrolabs/ego-lite](https://github.com/citrolabs/ego-lite)

### 外部依赖与架构参考

- [@fly-ai/flyai-cli](https://www.npmjs.com/package/@fly-ai/flyai-cli) `1.0.16`：主查航班和酒店的 CLI。
- [@variflight-ai/variflight-mcp](https://www.npmjs.com/package/@variflight-ai/variflight-mcp) `1.0.3`：可选飞常准 MCP；仓库许可证文件缺失时不复制其源码。
- 本机凭据配置页改编自本地安装的 MIT `oil-skill-creator/assets/credential-ui` 组件；公开上游地址尚未核实，来源关系以 [`provenance.yml`](provenance.yml) 的 `adapted_from` 记录为准，不冒称 Fork。
- [Yyh3/china-travel-planner-skills](https://github.com/Yyh3/china-travel-planner-skills)：最接近的中国出行多 Skill 架构参考。
- [MikkoParkkola/trvl](https://github.com/MikkoParkkola/trvl)：供应商健康状态和部分结果参考；PolyForm Noncommercial，不进入 MIT 核心。
- [618034128/Travel-Planning-Skill](https://github.com/618034128/Travel-Planning-Skill)：确认门、12306 和地图路由参考。
- [ZawYePhyo/travel-planner-skill](https://github.com/ZawYePhyo/travel-planner-skill)：规划 Skill 与执行 MCP 分离参考。
- [GruntworkAI/gruntwork-travel-skills](https://github.com/GruntworkAI/gruntwork-travel-skills)：提案优先、幂等和边界控制参考。
- [SquirrelSong5/travel-planner-skill](https://github.com/SquirrelSong5/travel-planner-skill)：国内 POI/路线经验参考；不采用其 Playwright 强依赖和 URL 携带 Key 的做法。

## 安全边界

- 只查询、比较、准备表单和生成真实平台链接；实名、下单、支付、退改必须经过单独明确确认。
- 本项目不代替承运方、铁路、酒店或地图服务的最终库存、价格、条款和安全判断。
- 所有曾在聊天、代码或历史配置中暴露的 Key 都应先轮换，再通过本机配置页写入系统凭据存储。
- `rent-ops` 为 CC-BY-NC-4.0，仅作 v2 研究；它和任何其他非商业材料都不进入 MIT 核心。

## 开发与验证

```bash
PYTHONPATH=plugins/china-travel-assistant/src \
  python3 -m unittest discover -s tests -v

python3 /Users/chrislee/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py \
  plugins/china-travel-assistant

ruff check --isolated --select E4,E7,E9,F \
  plugins/china-travel-assistant/src \
  plugins/china-travel-assistant/skills/plan-china-trip/scripts \
  tests

gitleaks detect --no-banner --redact --source .
```

## 视觉素材

顶部 GIF 由用户使用 GIFSKI 从视频导出，本仓库保留原始文件作为首页首图。两张静态 JPEG 是深色和浅色主题的旅程总览；8 个本地 SVG 负责章节节奏、八 Skill 路由、供应商工作流、凭据边界和开源来源。完整资产账本见 [`assets/readme/README.md`](assets/readme/README.md)。所有需要复制、搜索或经常更新的内容仍保留在 Markdown 中。
