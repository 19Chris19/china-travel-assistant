---
name: plan-china-trip
description: Orchestrate the 远行计划局 China travel Agent Skills into a complete evidence-backed trip, comparing transport, access, hotels, cost, fatigue, and risks. Use when the user asks for an end-to-end itinerary or several transport modes together. Do not use for a single isolated flight, train, hotel, transfer, webpage fact, or rendering request; route those to the domain Skill.
---

# Plan China Trip

Use this as the orchestration Skill. Keep provider calls separate from planning logic and read [provider-routing.md](references/provider-routing.md) before selecting a source.

## Workflow

1. Normalize the request into `TravelRequest`. Resolve relative dates using the current China Standard Time date and show the final dates.
2. Extract hard constraints: origin, destination, dates, travelers, budget, luggage, student-fare eligibility, arrival/departure windows, fatigue tolerance, and required airline or transport mode.
3. Ask only for missing facts that can change the recommendation. If the user delegates a choice, state conservative defaults and continue.
4. Resolve `exploration_tier`. Default `auto` (智能选择) to 拓界 (`pro`); converge to 从容 (`standard`) for direct-only, explicitly stable-risk, or rigid arrival constraints. Never enable 远征 (`pro_max`) without an explicit user choice.
5. For any flight-capable request, first ask `$plan-china-transfers` to discover generic reachable gateways. Then query each viable gateway through `$search-china-flights` and collect door-to-door ground access. Do not hard-code a city, airport, or personal historical preference.
6. Build verified candidate legs through `$search-china-flights`, `$search-china-trains`, `$search-china-hotels`, and `$plan-china-transfers`.
7. Invoke `$explore-china-routes` with the normalized request and candidate legs. Always keep a stable conventional baseline, then add only combinations that pass hard constraints and transfer buffers.
8. Normalize every result into `TravelOffer`, `TransferLeg`, `GatewayCandidate`, `PlaceEvidence`, `WeatherRisk`, or `ItineraryCandidate`. Preserve `null` for data that a provider did not return.
8. Include all known costs: ticket price, taxes, baggage, transfer fares, local transit, and required overnight stays. Label estimates separately from live offers.
9. Deduplicate only with a stable service identity. Do not combine conflicting fare variants from the same provider.
10. Rank by the user's explicit priority. If none is given, compare cheapest, fastest, and balanced options; do not silently optimize only price.
11. For outdoor stops and exposed transfers, use QWeather only as an optional risk layer. It can change buffer and place ordering, never manufacture a route, price, opening status, or availability.
12. Include a safe provider-health record for sources used in this itinerary. Readiness is not evidence; report a relevant degraded provider and its non-sensitive configuration path separately.
13. Invoke `$present-china-trip` with the validated `itinerary.json`. Prefer Visualize when available and use deterministic local presentation fallbacks otherwise.
14. Stop before real-name entry, order submission, payment, cancellation, refund, or change. Request a separate explicit confirmation for any transactional action.

## Exploration Tiers

All tiers retain the same high baseline: student fares, accommodation, luggage, taxes, transfers, refund rules, fatigue, time windows, evidence, and booking links. The tier changes search breadth and tolerated complexity, not feature availability.

- `Standard`: prioritize stable and conventional routes while still checking the complete cost and nearby gateways.
- `Pro`: the default for ordinary requests. Add flight-train, train-flight, split-ticket, nearby-airport, and corridor-hub hypotheses with managed risk.
- `Pro Max`: explicit opt-in only. Expand dates, hubs, overnight paths, and challenge routes while keeping hard constraints and transaction boundaries.

## Evidence Rules

- Dynamic prices, inventory, schedules, operating hours, and fares require a source label and query timestamp.
- A browser result is page evidence, not an official API result. Do not merge it into a live API offer without saying so.
- If a provider fails, keep independent successful legs and mark the plan partial. Say which provider failed and what fallback was used.
- Never infer tax inclusion, baggage, refund rules, terminal, inventory, or seat availability.
- For a tight connection, calculate a visible buffer and explain what happens if the previous leg is delayed.
- Every unconventional option must state its benefit over the stable baseline, added burden, self-transfer exposure, delay fallback, risk level, and evidence status.
- Rank gateways only from explicit ticket and ground facts. A missing ground fare stays unknown and must not be used as a pseudo-precise total.

## Output

Return trip assumptions and normalized dates; the resolved tier; one stable baseline; one recommended end-to-end plan and at most two alternatives; leg-by-leg prices, duration, transfers, buffers, risk and source status; booking links; and unresolved fields.

Use `scripts/validate_plan.py` for machine-readable plans before claiming that totals or buffers are complete.
