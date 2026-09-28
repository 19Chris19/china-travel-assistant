---
name: explore-china-routes
description: Explore and validate unconventional domestic multimodal routes with the deterministic route exploration engine, using normalized provider facts and a stable baseline. Use when flight, rail, and access facts already exist and the user wants more imaginative alternatives. Do not use to fetch raw fares, inspect webpages, find hotels, or render a final board; delegate those tasks to domain or presentation Skills.
---

# Explore China Routes

Turn normalized provider results into end-to-end route hypotheses. Use the deterministic engine instead of relying on the model to invent combinations from memory.

## Inputs

- A normalized `TravelRequest` with `exploration_tier=auto|standard|pro|pro_max`.
- Verified or explicitly partial `ItineraryLeg` records from the flight, train, hotel, and transfer Skills.
- Generic `GatewayCandidate`, `GroundAccessOption`, and optional `PlaceEvidence` or `WeatherRisk` facts.
- The user's hard constraints, risk tolerance, student-fare eligibility, time windows, luggage, and budget.

All tiers share the same high baseline capabilities: student fares, accommodation, luggage, taxes, transfers, refund rules, fatigue, time windows, evidence status, and booking links. Never remove one of these capabilities merely because Standard was selected.

## Tier Resolution

1. Keep an explicit Standard, Pro, or Pro Max choice.
2. Resolve Auto to Standard for direct-only, explicitly stable-risk, or rigid arrival requirements.
3. Resolve other Auto requests to Pro so the Agent proactively explores useful combinations.
4. Pro Max is challenge exploration and requires an explicit user choice. Never infer it from phrases such as "cheap" or "creative" alone.

## Deterministic Workflow

1. Generate a machine-readable query plan with `travel-assistant plan` before composing recommendations.
2. Establish at least one conventional, stable baseline when provider data permits.
3. Every tier scans generic reachable gateways. Standard only narrows alternative count and risk appetite; it does not skip student fares, ground costs, or gateway facts.
4. Pro additionally checks flight-train, train-flight, split rail, surrounding airports, and corridor hubs.
5. Pro Max additionally expands dates, hub radius, overnight paths, and challenge combinations within the user's hard constraints.
6. Reject disconnected legs, repeated-location loops, impossible time order, insufficient transfer buffers, excessive self-transfers, and risk above the resolved budget.
7. Keep unknown prices, baggage, refund rules, inventory, and evidence as unknown. Never impute them for scoring.
8. Rank only after validation and preserve the stable baseline even when a creative route scores better.
9. Rank complete door-to-door gateway totals before incomplete ones. A missing taxi, bus, or rail fare remains `null`, not an estimate hidden inside a score.

## Required Explanation

For every nontraditional route, provide:

- benefit relative to the stable baseline;
- additional burden and transfer count;
- protected versus self-transfer status;
- minimum connection buffer and delay fallback;
- Stable, Managed, or Challenge risk;
- Verified, Partial, or Hypothesis evidence status;
- unresolved fields that can change the recommendation.

Do not present a hypothesis as available inventory. Domain Skills remain responsible for live provider queries and `$verify-travel-web` remains the only browser automation Skill.
