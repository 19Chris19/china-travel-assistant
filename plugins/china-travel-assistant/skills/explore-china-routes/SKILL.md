---
name: explore-china-routes
description: Explore and validate imaginative China domestic multimodal routes with the deterministic OmniRoute engine. Use when an Agent needs alternatives beyond conventional travel-app recommendations, including flight-train, train-flight, nearby airports, corridor hubs, split tickets, overnight routes, or explicit Standard, Pro, and Pro Max exploration.
---

# Explore China Routes

Turn normalized provider results into end-to-end route hypotheses. Use the deterministic engine instead of relying on the model to invent combinations from memory.

## Inputs

- A normalized `TravelRequest` with `exploration_tier=auto|standard|pro|pro_max`.
- Verified or explicitly partial `ItineraryLeg` records from the flight, train, hotel, and transfer Skills.
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
3. Standard checks direct routes and nearby gateways with complete end-to-end costs.
4. Pro additionally checks flight-train, train-flight, split rail, surrounding airports, and corridor hubs.
5. Pro Max additionally expands dates, hub radius, overnight paths, and challenge combinations within the user's hard constraints.
6. Reject disconnected legs, repeated-location loops, impossible time order, insufficient transfer buffers, excessive self-transfers, and risk above the resolved budget.
7. Keep unknown prices, baggage, refund rules, inventory, and evidence as unknown. Never impute them for scoring.
8. Rank only after validation and preserve the stable baseline even when a creative route scores better.

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
