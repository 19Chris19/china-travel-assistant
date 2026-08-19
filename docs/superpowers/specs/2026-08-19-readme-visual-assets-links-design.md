# GitHub 首页视觉与来源说明设计

## 目标

把 `china-travel-assistant` 的 GitHub 首页从“项目说明页”整理成一个以安装转化为首要目标的开源产品首页：访客先看到 GIF 交通联程演示，随后能复制安装命令、配置凭据、发送第一句对话，并能审计所有 Key 申请入口、外部服务和上游项目来源。

## 已确认的视觉决定

- 顶部第一视觉元素使用用户提供的 `MiniMax H3 video.gif`，不在它前面放静态图片。
- GIF 保留原始文件：`640x271`、约 `5.33s`、`10 FPS`、约 `501 KB`。
- 两张静态 JPEG 作为后续主题视觉资源和静态降级素材保存；不把图片内的文字当作可复制文案。
- 项目名、价值描述、徽章、命令和链接全部保留在 Markdown 中。
- 不引入新的远程图片、动态徽章服务或 AI 生成视频依赖。

## 首页信息层级

1. GIF 首图与项目名、中文价值描述、真实 CI/Release/License 徽章。
2. 三分钟安装和第一句 Codex 对话。
3. GIF 所表达的“航班 + 铁路 + 接驳 + 酒店”能力矩阵。
4. 数据源路由和交易边界。
5. Key 申请、控制台和本地配置说明。
6. 可直接交给 Codex 等 Agent 的一键部署提示词。
7. `forked_from`、`integrates_with`、`inspired_by` 三类来源和许可证。
8. 安全边界、开发验证和 v2 租房范围。

## 文档边界

- `README.md` 面向首次安装者，提供入口、链接和最短可用路径。
- `plugins/china-travel-assistant/references/credentials.md` 面向配置者，提供申请网址、用途、变量、权限和故障分类。
- `THIRD_PARTY_NOTICES.md`、`provenance.yml`、`upstream-lock.yml` 保持机器可审计的来源事实；README 只做易读索引。
- `.env.example` 只保留变量名和空值，任何真实 Key 都不进入仓库。

## 验收标准

- GitHub 首屏第一个视觉元素是本地 GIF，图片路径在大小写敏感环境下存在。
- README 不把 FlyAI CLI 描述成 Codex 直连 MCP，不把参考项目描述成 Fork。
- README 和凭据文档包含所有当前变量对应的申请或配置入口，并对 v2 预留项明确标记。
- README 包含可复制的一键部署提示词，并明确不读取、输出或提交真实凭据，不执行实名、下单、支付或退改。
- 图片和 GIF 不包含远程依赖；GIF 文件小于 `2 MB`，并保留静态资源说明。
- 现有测试、插件校验、Ruff 和 Gitleaks 通过；链接检查至少覆盖本地相对链接和 README 中的官方 URL 语法。
