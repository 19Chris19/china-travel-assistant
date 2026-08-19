# 中国出行助手

面向 Codex 的中国境内出行规划 Plugin。通过对话组合机票、12306 火车票、酒店、高德接驳和城区公共交通，并在确有需要时使用 Ego Browser 核验登录态页面。

## v1 能力

- 国内航班：FlyAI/飞猪 CLI 主查，飞常准 MCP 按需核验。
- 铁路：固定到本人真实 Fork 提交的 12306 MCP。
- 酒店：FlyAI 主查，Ego Browser 核验房型、登录价、库存和取消条件。
- 接驳：高德 POI 与路线数据，显式计算换乘和缓冲时间。
- 安全边界：只查询、比较和生成真实链接；提交订单、实名、支付和退改必须单独确认。
- 租房：不在 v1 运行时中，计划在 v2 以原创适配器重新加入。

FlyAI 在本项目中是调用飞猪服务的 CLI，不是注册到 Codex 的直接 MCP。浏览器自动化统一使用 [Ego Browser](https://github.com/citrolabs/ego-lite)。

## 安装

要求 Python 3.10+、`pipx`（或可运行 `python3 -m pipx`）、Node.js、uvx、Codex，以及已安装可运行的 Ego Browser。Ego Browser Skill 元数据最低版本为 `1.2.3`；Ego CLI 使用独立的应用版本号，不能与 Skill 版本混用。

~~~bash
git clone https://github.com/19Chris19/china-travel-assistant
cd china-travel-assistant
./scripts/install-local.sh
~~~

也可分别安装：

~~~bash
pipx install ./plugins/china-travel-assistant
npm install -g @fly-ai/flyai-cli@1.0.16
codex plugin marketplace add "$PWD"
codex plugin add china-travel-assistant@china-travel-assistant
~~~

在 macOS 上若系统 npm 前缀不可写，可改用用户级安装：

~~~bash
npm install -g --prefix "$HOME/.local" @fly-ai/flyai-cli@1.0.16
~~~

安装后完全退出并重启 Codex，使 Plugin 与 MCP 正式重载。

## 凭据

运行：

~~~bash
./scripts/setup-credentials.sh
~~~

然后只在 ~/.config/china-travel-assistant/credentials.env 中填写真实值。该文件权限为 0600，不会进入仓库。

| 变量 | 用途 | 必需 |
| --- | --- | --- |
| AMAP_WEBSERVICE_KEY | 高德 POI 和路线 | 是 |
| AMAP_JSAPI_KEY | 可选交互地图 | 否 |
| AMAP_SECURITY_CODE | 高德 JS API 安全码 | 否 |
| FLYAI_API_KEY | FlyAI 增强访问 | 否 |
| VARIFLIGHT_API_KEY | 飞常准核验 | 否 |
| VIGOLIVE_API_KEY | v2 租房预留 | 否 |

密钥申请与存储说明见 [credentials.md](plugins/china-travel-assistant/references/credentials.md)。

检查本地状态：

~~~bash
travel-assistant doctor
~~~

默认只检查配置和运行时，不发送付费请求。`travel-assistant doctor --live` 才执行最小在线探测。

高德适配器也提供无浏览器的路线查询入口；费用只使用高德明确返回的字段：

~~~bash
travel-assistant amap-route transit \
  --origin '121.8,31.15' --destination '120.73,31.27' \
  --city '上海' --destination-city '苏州'
~~~

## 使用

安装并重启后直接对话，或显式调用：

~~~text
使用 $plan-china-trip，帮我比较沈阳到苏州周边机场的低价航班，
把机场到苏州工业园区的公共交通接驳和总价一起算清楚。
~~~

六个可独立调用的 Skills：

- $plan-china-trip
- $search-china-flights
- $search-china-trains
- $plan-china-transfers
- $search-china-hotels
- $verify-travel-web

## 来源与许可

本仓库原创代码采用 MIT。上游 Fork、外部包、官网服务和仅参考项目分别记录在 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)、[provenance.yml](provenance.yml) 与 [upstream-lock.yml](upstream-lock.yml)。

只有 GitHub 上真实建立 Fork 的项目才标记为 forked_from。外部 npm 包标记为 integrates_with，未复制的架构参考标记为 inspired_by。

## 开发

~~~bash
PYTHONPATH=plugins/china-travel-assistant/src \
  python3 -m unittest discover -s tests -v

python3 /Users/chrislee/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py \
  plugins/china-travel-assistant
~~~

发布前必须运行测试、Plugin/Skill 校验和密钥扫描。任何曾在聊天、代码或历史配置中暴露的 Key 都应先轮换。
