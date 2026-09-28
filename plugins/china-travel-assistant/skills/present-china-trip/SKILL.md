---
name: present-china-trip
description: Present an already validated China itinerary from itinerary.json as a Visualize-first route board or exact local HTML, SVG, or Markdown. Use when a trip is already planned and the user requests a visual itinerary. Do not use for provider searches, missing-fact inference, route composition, or ImageGen-written itinerary data.
---

# Present China Trip

Treat `itinerary.json` as the single source of truth. This Skill changes presentation, never facts.

## Capability Negotiation

1. If the host exposes Visualize, invoke it first and build an in-conversation route board from the validated JSON.
2. If Visualize is unavailable, generate a self-contained local HTML route board and an exact SVG summary when requested.
3. If artifact files cannot be rendered, return structured Markdown with complete links, risks, sources, and unknown fields.
4. State the chosen presentation mode. Do not silently omit data because a richer renderer is unavailable.

Visualize may be unavailable in older Codex versions or unsupported clients. Recommend upgrading or opening the task in a supported Codex surface, but always provide a local fallback.

## Fact Integrity

- Copy times, prices, service numbers, airports, stations, buffers, risk levels, evidence states, and URLs directly from `itinerary.json`.
- Preserve `null` as `未返回` or `Unknown`; do not calculate a missing amount in the presentation layer.
- Compare rendered values against the JSON before delivery.
- Escape untrusted labels and links in HTML and SVG.
- Do not load remote scripts, fonts, or analytics in local artifacts.
- ImageGen must not write or redraw itinerary facts. A future decorative background may be generated separately, but deterministic HTML or SVG must place all critical text.
- Show a narrow data-health ribbon sourced from `ProviderHealthRecord`. Only show providers relevant to this itinerary; display readiness separately from ticket, route, weather, and opening evidence. Never render a key, token, private-key path, raw error body, or sensitive request URL.

## Visual Structure

Show the resolved tier, constraints, stable baseline, recommendation, alternatives, leg nodes, transfer buffers, known total, unknown costs, evidence status, burden, delay fallback, generic gateway or place facts when present, the data-health ribbon, and copyable booking links. Use color and icons only as redundant cues; every status also needs a text label.

Never submit bookings, personal identity, payment, refund, or change requests from the presentation layer.
