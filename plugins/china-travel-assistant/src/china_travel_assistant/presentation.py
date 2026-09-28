from __future__ import annotations

from html import escape
from typing import Any, Mapping
from urllib.parse import urlsplit

from .contracts import PresentationMode


UNKNOWN = "未返回"
_CREDENTIALS_URL = (
    "https://github.com/19Chris19/china-travel-assistant/blob/main/"
    "plugins/china-travel-assistant/references/credentials.md"
)
_HEALTH_COPY = {
    "amap": ("高德", "配置 AMAP_WEBSERVICE_KEY 以启用门户、POI 与接驳事实。"),
    "flyai": ("FlyAI", "安装 FlyAI CLI 并配置 FLYAI_API_KEY 以增强机酒景检索。"),
    "variflight": ("飞常准", "配置 VARIFLIGHT_API_KEY 以增强航班运行核验。"),
    "12306": ("12306", "重启 Codex 并核验 china-12306 MCP，以获得余票与票价。"),
    "qweather": ("QWeather", "配置 QWeather JWT 以增强户外风险与接驳缓冲。"),
    "ego-browser": ("Ego Browser", "安装并启动 Ego Browser，以核验登录价或官方页面。"),
    "visualize": ("Visualize", "升级到支持 Visualizations 的官方宿主；本地 HTML/SVG 仍可用。"),
}
_HEALTH_OK = {"ready", "not_required"}


def _text(value: Any) -> str:
    return UNKNOWN if value is None or value == "" else str(value)


def _html(value: Any) -> str:
    return escape(_text(value), quote=True)


def _safe_url(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    parsed = urlsplit(value.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return None
    return value.strip()


def _money(value: Any) -> str:
    if value is None:
        return UNKNOWN
    return f"CNY {float(value):.2f}"


def _duration(value: Any) -> str:
    if value is None:
        return UNKNOWN
    minutes = int(value)
    hours, remainder = divmod(minutes, 60)
    return f"{hours}h {remainder}m" if hours else f"{remainder}m"


def _itineraries(plan: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    values = plan.get("itineraries")
    if not isinstance(values, list):
        raise ValueError("plan itineraries must be a JSON array")
    for index, value in enumerate(values):
        if not isinstance(value, Mapping):
            raise ValueError(f"plan itinerary {index} must be a JSON object")
        legs = value.get("legs")
        if not isinstance(legs, list):
            raise ValueError(f"plan itinerary {index} legs must be a JSON array")
        if any(not isinstance(leg, Mapping) for leg in legs):
            raise ValueError(f"plan itinerary {index} legs must contain JSON objects")
    return values


def _provider_names(plan: Mapping[str, Any], itineraries: list[Mapping[str, Any]]) -> set[str]:
    providers: set[str] = set()
    for itinerary in itineraries:
        for leg in itinerary["legs"]:
            provider = leg.get("provider")
            if isinstance(provider, str):
                providers.add(provider)
            sources = leg.get("sources")
            if isinstance(sources, list):
                providers.update(item for item in sources if isinstance(item, str))
    for candidate in plan.get("gateway_candidates", []):
        if not isinstance(candidate, Mapping):
            continue
        provider = candidate.get("ticket_provider")
        if isinstance(provider, str):
            providers.add(provider)
        for access in candidate.get("ground_access", []):
            if isinstance(access, Mapping) and isinstance(access.get("source"), str):
                providers.add(access["source"])
    for place in plan.get("place_evidence", []):
        if not isinstance(place, Mapping):
            continue
        if isinstance(place.get("source"), str):
            providers.add(place["source"])
        weather = place.get("weather_risk")
        if isinstance(weather, Mapping) and isinstance(weather.get("source"), str):
            providers.add(weather["source"])
    return providers


def _health_records(plan: Mapping[str, Any], itineraries: list[Mapping[str, Any]]) -> list[dict[str, str]]:
    raw_records = plan.get("provider_health", [])
    if isinstance(raw_records, Mapping):
        records = [dict(value, provider=provider) for provider, value in raw_records.items() if isinstance(value, Mapping)]
    elif isinstance(raw_records, list):
        records = [item for item in raw_records if isinstance(item, Mapping)]
    else:
        records = []
    relevant = _provider_names(plan, itineraries)
    normalized = []
    for record in records:
        provider = record.get("provider")
        status = record.get("status")
        if provider not in _HEALTH_COPY or provider not in relevant or not isinstance(status, str):
            continue
        normalized.append({"provider": provider, "status": status if status in {
            "ready", "missing", "expired", "forbidden", "rate_limited", "degraded", "unknown", "not_required"
        } else "unknown"})
    return normalized


def _health_summary(records: list[dict[str, str]]) -> tuple[str, str | None]:
    if not records:
        return "数据健康：待查询", "本次尚无可展示的供应商状态。"
    issues = [record for record in records if record["status"] not in _HEALTH_OK]
    if not issues:
        return "数据健康：OK", None
    provider = issues[0]["provider"]
    return "数据健康：部分降级", _HEALTH_COPY[provider][1]


def _html_health(plan: Mapping[str, Any], itineraries: list[Mapping[str, Any]]) -> str:
    records = _health_records(plan, itineraries)
    summary, recommendation = _health_summary(records)
    labels = "".join(
        f'<span class="health-item health-{_html(record["status"])}">{_html(_HEALTH_COPY[record["provider"]][0])}: {_html(record["status"])}</span>'
        for record in records
    )
    cta = ""
    if recommendation and records:
        cta = (
            f'<a class="health-cta" href="{_CREDENTIALS_URL}" rel="noopener noreferrer">'
            f'{_html(recommendation)} 配置说明</a>'
        )
    return f'<section class="health-ribbon" aria-label="数据健康"><strong>{_html(summary)}</strong>{labels}{cta}</section>'


def _context_facts(plan: Mapping[str, Any]) -> str:
    gateway_candidates = plan.get("gateway_candidates")
    places = plan.get("place_evidence")
    parts = []
    if isinstance(gateway_candidates, list) and gateway_candidates:
        candidate = gateway_candidates[0]
        if isinstance(candidate, Mapping):
            parts.append(
                f'<p><b>首选门户</b> {_html(candidate.get("name"))} · '
                f'{_html(_money(candidate.get("total_known_cost_cny")))} · '
                f'{_html(candidate.get("ranking_reason"))}</p>'
            )
    if isinstance(places, list) and places:
        place = places[0]
        if isinstance(place, Mapping):
            parts.append(
                f'<p><b>地点事实</b> {_html(place.get("name"))} · '
                f'开放状态 {_html(place.get("opening_status"))} · {_html(place.get("ranking_reason"))}</p>'
            )
    return f'<section class="context-facts">{"".join(parts)}</section>' if parts else ""


def _html_leg(leg: Mapping[str, Any]) -> str:
    booking_url = _safe_url(leg.get("booking_url"))
    link = ""
    if booking_url:
        safe_url = escape(booking_url, quote=True)
        link = (
            '<div class="booking"><a href="'
            f'{safe_url}" rel="noopener noreferrer">打开预订页</a>'
            f'<input aria-label="可复制预订链接" readonly value="{safe_url}"></div>'
        )
    return f"""
      <li class="leg">
        <div class="node" aria-hidden="true"></div>
        <div class="leg-main">
          <strong>{_html(leg.get("origin"))} → {_html(leg.get("destination"))}</strong>
          <span>{_html(leg.get("mode"))} · {_html(leg.get("service_number"))}</span>
          <span>{_html(leg.get("departure_at"))} → {_html(leg.get("arrival_at"))}</span>
          <span>费用 {_html(_money(leg.get("total_price_cny")))} · 缓冲 {_html(_duration(leg.get("buffer_minutes")))}</span>
          <span>来源 {_html(", ".join(leg.get("sources") or []) or leg.get("provider"))} · 证据 {_html(leg.get("evidence_status"))}</span>
          {link}
        </div>
      </li>"""


def render_html(plan: Mapping[str, Any]) -> str:
    itineraries = _itineraries(plan)
    health = _html_health(plan, itineraries)
    context_facts = _context_facts(plan)
    cards = []
    for index, item in enumerate(itineraries):
        labels = []
        if item.get("is_baseline"):
            labels.append('<span class="badge baseline">稳妥基准</span>')
        labels.append(f'<span class="badge risk-{_html(item.get("risk_level"))}">风险 {_html(item.get("risk_level"))}</span>')
        labels.append(f'<span class="badge">证据 {_html(item.get("evidence_status"))}</span>')
        unknowns = item.get("unknown_fields") or []
        facts = "".join(
            (
                f'<p><b>相对收益</b> {_html(item.get("benefit_summary"))}</p>',
                f'<p><b>额外折腾</b> {_html(item.get("burden_summary"))}</p>',
                f'<p><b>延误兜底</b> {_html(item.get("delay_fallback"))}</p>',
                f'<p><b>未知字段</b> {_html(", ".join(unknowns) if unknowns else "无")}</p>',
            )
        )
        legs = "".join(_html_leg(leg) for leg in item["legs"])
        open_state = " open" if index == 0 else ""
        cards.append(
            f"""
    <details class="route"{open_state}>
      <summary>
        <span class="route-title">{_html(item.get("title"))}</span>
        <span class="metrics">{_html(_money(item.get("total_price_cny")))} · {_html(_duration(item.get("total_duration_minutes")))}</span>
      </summary>
      <div class="badges">{''.join(labels)}</div>
      <ol class="timeline">{legs}</ol>
      <div class="route-notes">{facts}</div>
    </details>"""
        )
    request = plan.get("request") if isinstance(plan.get("request"), Mapping) else {}
    route_label = f"{_text(request.get('origin'))} → {_text(request.get('destination'))}"
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="color-scheme" content="light dark">
  <title>天枢 TravelOS · {_html(route_label)}</title>
  <style>
    :root {{ color-scheme: light dark; --bg:#f4f1e8; --panel:#fffdf6; --ink:#17213b; --muted:#64708a; --line:#d8d1bf; --red:#db3434; --teal:#007d82; --shadow:0 18px 45px #17213b18; }}
    @media (prefers-color-scheme:dark) {{ :root {{ --bg:#10141d; --panel:#171d28; --ink:#f5f0e5; --muted:#a8b2c8; --line:#30394a; --red:#ff5a55; --teal:#27d2c3; --shadow:0 18px 45px #0007; }} }}
    * {{ box-sizing:border-box; }} body {{ margin:0; background:radial-gradient(circle at 85% 0,#007d8225,transparent 34%),var(--bg); color:var(--ink); font-family:"Avenir Next","Noto Sans SC",sans-serif; }}
    main {{ width:min(980px,calc(100% - 28px)); margin:0 auto; padding:54px 0 70px; }}
    header {{ border-left:7px solid var(--red); padding:4px 0 4px 20px; margin-bottom:30px; }}
    h1 {{ font-size:clamp(2rem,7vw,4.5rem); line-height:.95; margin:0 0 14px; letter-spacing:-.05em; }}
    header p {{ color:var(--muted); margin:5px 0; }} .tier {{ color:var(--teal); font-weight:800; text-transform:uppercase; }}
    .health-ribbon {{ display:flex; flex-wrap:wrap; align-items:center; gap:7px 10px; padding:10px 14px; margin:0 0 16px; border:1px solid var(--line); background:color-mix(in srgb,var(--panel) 90%,var(--teal)); font-size:.82rem; }} .health-item {{ color:var(--muted); }} .health-ready {{ color:var(--teal); }} .health-missing,.health-expired,.health-forbidden,.health-rate_limited,.health-degraded {{ color:var(--red); }} .health-cta {{ margin-left:auto; font-weight:750; }}
    .context-facts {{ padding:0 14px; margin:0 0 15px; color:var(--muted); font-size:.86rem; }} .context-facts p {{ margin:6px 0; }}
    .route {{ background:var(--panel); border:1px solid var(--line); border-radius:20px; margin:14px 0; box-shadow:var(--shadow); overflow:hidden; }}
    summary {{ display:flex; gap:18px; justify-content:space-between; align-items:center; cursor:pointer; padding:22px; font-weight:750; }}
    summary::marker {{ color:var(--red); }} .route-title {{ font-size:1.15rem; }} .metrics {{ color:var(--teal); white-space:nowrap; }}
    .badges,.route-notes {{ padding:0 22px 18px; }} .badge {{ display:inline-block; border:1px solid var(--line); border-radius:99px; padding:5px 9px; margin:0 6px 6px 0; font-size:.78rem; color:var(--muted); }}
    .baseline {{ color:var(--teal); border-color:var(--teal); }} .risk-challenge {{ color:var(--red); border-color:var(--red); }}
    .timeline {{ list-style:none; padding:0 22px; margin:0; }} .leg {{ position:relative; display:grid; grid-template-columns:18px 1fr; gap:13px; padding-bottom:20px; }}
    .leg::before {{ content:""; position:absolute; left:7px; top:16px; bottom:-2px; width:2px; background:var(--line); }} .leg:last-child::before {{ display:none; }}
    .node {{ width:16px; height:16px; margin-top:3px; border:4px solid var(--panel); border-radius:50%; background:var(--red); box-shadow:0 0 0 2px var(--red); z-index:1; }}
    .leg-main {{ display:grid; gap:5px; }} .leg-main span,.route-notes {{ color:var(--muted); font-size:.9rem; }} .route-notes p {{ margin:7px 0; }}
    .booking {{ display:flex; flex-wrap:wrap; gap:8px; margin-top:6px; }} a {{ color:var(--teal); font-weight:750; }} input {{ min-width:0; flex:1 1 280px; border:1px solid var(--line); border-radius:8px; background:transparent; color:var(--muted); padding:7px; }}
    footer {{ margin-top:26px; color:var(--muted); font-size:.82rem; }}
    @media (max-width:620px) {{ main {{ padding-top:32px; }} summary {{ align-items:flex-start; flex-direction:column; gap:8px; }} .metrics {{ white-space:normal; }} }}
  </style>
</head>
<body><main>
  <header>
    <p>天枢 TravelOS · Agent Skill 行程板</p>
    <h1>{_html(route_label)}</h1>
    <p class="tier">{_html(plan.get("resolved_tier"))} · {_html(request.get("date_start"))}</p>
  </header>
  {health}
  {context_facts}
  {''.join(cards) if cards else '<p>没有通过约束校验的候选行程。</p>'}
  <footer>所有事实来自同一份 itinerary.json。未返回字段不会在展示层推断；下单与支付需要单独确认。</footer>
</main></body>
</html>
"""


def render_svg(plan: Mapping[str, Any]) -> str:
    itineraries = _itineraries(plan)
    row_height = 112
    height = max(360, 240 + row_height * len(itineraries))
    request = plan.get("request") if isinstance(plan.get("request"), Mapping) else {}
    route_label = f"{_text(request.get('origin'))} → {_text(request.get('destination'))}"
    health_records = _health_records(plan, itineraries)
    health_summary, health_cta = _health_summary(health_records)
    health_text = " · ".join(
        f"{_HEALTH_COPY[item['provider']][0]} {item['status']}" for item in health_records
    ) or health_cta or "本次尚无可展示的供应商状态。"
    rows = []
    for index, item in enumerate(itineraries):
        y = 190 + index * row_height
        baseline = " · 稳妥基准" if item.get("is_baseline") else ""
        node_color = "#007d82" if item.get("is_baseline") else "#db3434"
        rows.append(
            f'<g transform="translate(60 {y})">'
            f'<circle cx="10" cy="10" r="8" fill="{node_color}"/>'
            f'<text x="38" y="15" class="route">{_html(item.get("title"))}{_html(baseline)}</text>'
            f'<text x="38" y="43" class="meta">{_html(_money(item.get("total_price_cny")))} · {_html(_duration(item.get("total_duration_minutes")))} · 风险 {_html(item.get("risk_level"))} · 证据 {_html(item.get("evidence_status"))}</text>'
            f'<text x="38" y="70" class="meta">{_html(item.get("benefit_summary"))} · {_html(item.get("burden_summary"))}</text>'
            '</g>'
        )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="title desc" viewBox="0 0 1200 {height}">
<title id="title">天枢 TravelOS {_html(route_label)} 行程</title>
<desc id="desc">由 itinerary.json 确定性生成的路线摘要</desc>
<style>.bg{{fill:#f4f1e8}}.ink{{fill:#17213b}}.muted{{fill:#64708a}}.title{{font:700 58px sans-serif}}.label{{font:700 22px sans-serif;fill:#007d82}}.route{{font:700 22px sans-serif;fill:#17213b}}.meta{{font:17px sans-serif;fill:#64708a}}</style>
<rect class="bg" width="1200" height="{height}" rx="30"/>
<rect x="55" y="50" width="8" height="94" rx="4" fill="#db3434"/>
<text x="86" y="86" class="label">天枢 TravelOS · {_html(plan.get("resolved_tier"))}</text>
<text x="86" y="137" class="title">{_html(route_label)}</text>
<text x="86" y="166" class="meta">{_html(health_summary)} · {_html(health_text)}</text>
{''.join(rows)}
<text x="60" y="{height - 34}" class="meta">事实源 itinerary.json · 未返回字段不推断 · 交易前需单独确认</text>
</svg>
"""


def render_markdown(plan: Mapping[str, Any]) -> str:
    itineraries = _itineraries(plan)
    request = plan.get("request") if isinstance(plan.get("request"), Mapping) else {}
    health_records = _health_records(plan, itineraries)
    health_summary, health_cta = _health_summary(health_records)
    lines = [
        f"# 天枢 TravelOS: {_text(request.get('origin'))} -> {_text(request.get('destination'))}",
        "",
        f"- 探索档位: `{_text(plan.get('resolved_tier'))}`",
        f"- 出发日期: `{_text(request.get('date_start'))}`",
        "- 事实源: `itinerary.json`",
        f"- {health_summary}",
    ]
    for record in health_records:
        lines.append(f"  - {_HEALTH_COPY[record['provider']][0]}: `{record['status']}`")
    if health_cta and health_records:
        lines.append(f"  - 改善体验: [{health_cta}]({_CREDENTIALS_URL})")
    for item in itineraries:
        baseline = " [稳妥基准]" if item.get("is_baseline") else ""
        lines.extend(
            [
                "",
                f"## {_text(item.get('title'))}{baseline}",
                "",
                f"总价: {_money(item.get('total_price_cny'))}; 总耗时: {_duration(item.get('total_duration_minutes'))}; 风险: {_text(item.get('risk_level'))}; 证据: {_text(item.get('evidence_status'))}",
                "",
                f"相对收益: {_text(item.get('benefit_summary'))}",
                "",
                f"额外折腾: {_text(item.get('burden_summary'))}",
                "",
                f"延误兜底: {_text(item.get('delay_fallback'))}",
            ]
        )
        for leg in item["legs"]:
            service = _text(leg.get("service_number"))
            lines.append(
                f"- {_text(leg.get('origin'))} -> {_text(leg.get('destination'))} | {_text(leg.get('mode'))} {service} | {_text(leg.get('departure_at'))} -> {_text(leg.get('arrival_at'))} | {_money(leg.get('total_price_cny'))} | 缓冲 {_duration(leg.get('buffer_minutes'))}"
            )
            booking_url = _safe_url(leg.get("booking_url"))
            if booking_url:
                lines.append(f"  预订链接: {booking_url}")
        unknowns = item.get("unknown_fields") or []
        lines.append(f"- 未知字段: {', '.join(unknowns) if unknowns else '无'}")
    lines.extend(["", "未返回字段不推断；实名、下单、支付和退改必须单独确认。", ""])
    return "\n".join(lines)


def render_plan(plan: Mapping[str, Any], mode: PresentationMode) -> tuple[PresentationMode, str]:
    resolved = PresentationMode.HTML if mode is PresentationMode.AUTO else mode
    if resolved is PresentationMode.VISUALIZE:
        raise ValueError("visualize presentation must be invoked by a supported Agent host")
    renderers = {
        PresentationMode.HTML: render_html,
        PresentationMode.SVG: render_svg,
        PresentationMode.MARKDOWN: render_markdown,
    }
    renderer = renderers.get(resolved)
    if renderer is None:
        raise ValueError(f"unsupported local presentation mode: {resolved.value}")
    return resolved, renderer(plan)
