---
name: plan-china-trip
description: Plan China domestic travel by combining flights, trains, hotels, maps, transfers, budgets, and evidence-backed alternatives. Use when the user asks to plan or compare a China trip, connect airports or stations to a destination, optimize cost versus time or fatigue, or turn travel constraints into an executable itinerary.
---

# Plan China Trip

Use this as the orchestration Skill. Keep provider calls separate from planning logic and read [provider-routing.md](references/provider-routing.md) before selecting a source.

## Workflow

1. Normalize the request into `TravelRequest`. Resolve relative dates using the current China Standard Time date and show the final dates.
2. Extract hard constraints: origin, destination, dates, travelers, budget, luggage, arrival/departure windows, fatigue tolerance, and required airline or transport mode.
3. Ask only for missing facts that can change the recommendation. If the user delegates a choice, state conservative defaults and continue.
4. Build candidate legs through the domain Skills: flights, trains, hotels, and transfers. Search nearby airports/stations only when the requested scope allows it.
5. Normalize every result into `TravelOffer` or `TransferLeg`. Preserve `null` for data that a provider did not return.
6. Include all known costs: ticket price, taxes, baggage, transfer fares, local transit, and required overnight stays. Label estimates separately from live offers.
7. Deduplicate only with a stable service identity. Do not combine conflicting fare variants from the same provider.
8. Rank by the user's explicit priority. If none is given, compare cheapest, fastest, and balanced options; do not silently optimize only price.
9. Present a concise recommendation, alternatives, assumptions, source and query timestamps, total-cost basis, and real booking links.
10. Stop before real-name entry, order submission, payment, cancellation, refund, or change. Request a separate explicit confirmation for any transactional action.

## Evidence Rules

- Dynamic prices, inventory, schedules, operating hours, and fares require a source label and query timestamp.
- A browser result is page evidence, not an official API result. Do not merge it into a live API offer without saying so.
- If a provider fails, keep independent successful legs and mark the plan partial. Say which provider failed and what fallback was used.
- Never infer tax inclusion, baggage, refund rules, terminal, inventory, or seat availability.
- For a tight connection, calculate a visible buffer and explain what happens if the previous leg is delayed.

## Output

Return trip assumptions and normalized dates; one recommended end-to-end plan and at most two alternatives; leg-by-leg prices, duration, transfers, buffers, and source status; booking links; and unresolved fields.

Use `scripts/validate_plan.py` for machine-readable plans before claiming that totals or buffers are complete.
