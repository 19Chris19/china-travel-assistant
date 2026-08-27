---
name: plan-china-trip
description: Orchestrate the China Travel Assistant Agent Skills for domestic flights, trains, hotels, maps, transfers, OmniRoute exploration, budgets, and evidence-backed presentation. Use when the user asks to plan or compare a China trip, discover unconventional multimodal combinations, connect airports or stations, optimize cost versus time or fatigue, or turn travel constraints into an executable itinerary.
---

# Plan China Trip

Use this as the orchestration Skill. Keep provider calls separate from planning logic and read [provider-routing.md](references/provider-routing.md) before selecting a source.

## Workflow

1. Normalize the request into `TravelRequest`. Resolve relative dates using the current China Standard Time date and show the final dates.
2. Extract hard constraints: origin, destination, dates, travelers, budget, luggage, student-fare eligibility, arrival/departure windows, fatigue tolerance, and required airline or transport mode.
3. Ask only for missing facts that can change the recommendation. If the user delegates a choice, state conservative defaults and continue.
4. Resolve `exploration_tier`. Default `auto` to Pro; converge to Standard for direct-only, explicitly stable-risk, or rigid arrival constraints. Never enable Pro Max without an explicit user choice.
5. Build verified candidate legs through `$search-china-flights`, `$search-china-trains`, `$search-china-hotels`, and `$plan-china-transfers`.
6. Invoke `$explore-china-routes` with the normalized request and candidate legs. Always keep a stable conventional baseline, then add only combinations that pass hard constraints and transfer buffers.
7. Normalize every result into `TravelOffer`, `TransferLeg`, or `ItineraryCandidate`. Preserve `null` for data that a provider did not return.
8. Include all known costs: ticket price, taxes, baggage, transfer fares, local transit, and required overnight stays. Label estimates separately from live offers.
9. Deduplicate only with a stable service identity. Do not combine conflicting fare variants from the same provider.
10. Rank by the user's explicit priority. If none is given, compare cheapest, fastest, and balanced options; do not silently optimize only price.
11. Invoke `$present-china-trip` with the validated `itinerary.json`. Prefer Visualize when available and use deterministic local presentation fallbacks otherwise.
12. Stop before real-name entry, order submission, payment, cancellation, refund, or change. Request a separate explicit confirmation for any transactional action.

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

## Output

Return trip assumptions and normalized dates; the resolved tier; one stable baseline; one recommended end-to-end plan and at most two alternatives; leg-by-leg prices, duration, transfers, buffers, risk and source status; booking links; and unresolved fields.

Use `scripts/validate_plan.py` for machine-readable plans before claiming that totals or buffers are complete.
