from __future__ import annotations

from html import escape
from typing import Any, Mapping
from urllib.parse import urlsplit

from .contracts import PresentationMode


UNKNOWN = "未返回"


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
{''.join(rows)}
<text x="60" y="{height - 34}" class="meta">事实源 itinerary.json · 未返回字段不推断 · 交易前需单独确认</text>
</svg>
"""


def render_markdown(plan: Mapping[str, Any]) -> str:
    itineraries = _itineraries(plan)
    request = plan.get("request") if isinstance(plan.get("request"), Mapping) else {}
    lines = [
        f"# 天枢 TravelOS: {_text(request.get('origin'))} -> {_text(request.get('destination'))}",
        "",
        f"- 探索档位: `{_text(plan.get('resolved_tier'))}`",
        f"- 出发日期: `{_text(request.get('date_start'))}`",
        "- 事实源: `itinerary.json`",
    ]
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
