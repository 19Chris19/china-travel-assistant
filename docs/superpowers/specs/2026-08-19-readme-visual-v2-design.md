# README 视觉叙事第二版设计

## 目标

在不改变顶部 GIF 和安装优先路径的前提下，把 README 从单一动图加长文本升级为有明确视觉节奏的开源产品首页。每张新增图片必须解释一个真实概念，不能只是装饰。

## 视觉系统

- 主题：综合交通调度终端，强调路线、调度、证据和边界。
- 画布：固定深色基底 `#0B0F17`，兼容 GitHub 明暗页面；卡片使用 `#111827`。
- 文本：主文本 `#F8FAFC`，次级文本 `#94A3B8`。
- 语义色：干线红 `#F43F5E`、接驳蓝 `#38BDF8`、安全琥珀 `#FBBF24`、可用绿 `#34D399`。
- 字体：中文使用系统无衬线，代码和状态使用系统等宽字体。
- 图形：正交路线、圆形站点、4-6px 小圆角、1-2px 结构线，不使用光球、伪图表、远程字体或脚本。

## 资产清单

1. 顶部保留 `china-travel-assistant.gif`。
2. `journey-overview` 使用现有深浅两张 JPEG，通过 `<picture>` 适配主题。
3. `skill-system-map.svg` 展示自然语言、父 Skill、五个执行 Skill 和数据源之间的关系。
4. `provider-workflow.svg` 展示解析、并发查询、按需核验、合成交付四阶段。
5. `credential-boundary.svg` 展示本地 `0600` 凭据文件与对话、URL、Issue、Git 的隔离边界。
6. `provenance-map.svg` 区分 `forked_from`、`integrates_with`、`inspired_by`。
7. `section-quickstart.svg`、`section-routing.svg`、`section-security.svg`、`section-sources.svg` 建立章节节奏。

## README 顺序

```text
顶部 GIF
项目名、价值和真实状态链接
旅程总览 picture
快速开始标题 + 安装命令 + 第一条对话
能力路由标题 + Skill 系统图 + 能力表
供应商工作流图 + 调用规则
配置安全标题 + Key 表 + 凭据边界图 + 部署提示词
开源来源标题 + 来源关系图 + 详细链接
安全边界、开发验证和视觉素材说明
```

## 可读性和边界

- 信息图统一使用 `viewBox="0 0 1200 600"`，关键文字不小于 24 SVG 单位，辅助文字不小于 20。
- 章节标题使用 `viewBox="0 0 1200 96"`，只保留序号、英文代号、中文标题和路线标尺。
- 所有 SVG 必须包含 `<title>` 和 `<desc>`，不得包含脚本、`foreignObject`、远程资源或嵌入 Key。
- URL、命令、环境变量、版本和完整项目清单仍留在 Markdown；图中只显示关系骨架。
- 桌面按 900px 宽、手机按 360px 宽渲染检查；手机端如果辅助文字过小，关系仍必须通过颜色、线条和分组成立。
- 两张 JPEG 不修改、不重编码；顶部 GIF 保留原始编码。

## 验收标准

- README 至少引用顶部 GIF、主题 `<picture>` 和 8 个 SVG，共不少于 11 个本地视觉引用。
- 8 个 SVG 均可解析、具备稳定 viewBox、无禁用特性且文件大小合理。
- 页面不虚构使用量、供应商状态、票价或性能数据。
- 现有 Key、来源、安全边界、安装命令和一键部署提示词保持可搜索、可复制。
- 全量测试、Ruff、Plugin 校验、Gitleaks、README 审计和 SVG 渲染检查通过。
