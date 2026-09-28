---
name: search-china-flights
description: Search and compare mainland-China flights, nearby airports, fares, taxes, schedules, baggage, and booking links. Use when the user asks about domestic airfare, low prices, airline or date comparisons, flight status, or multimodal flight-plus-train options.
---

# Search China Flights

Use FlyAI/飞猪 first for searchable domestic offers and booking links. Use Variflight only when status, punctuality, schedule, or a price cross-check is requested or materially improves confidence.

## Workflow

1. Normalize city and airport aliases to explicit airports. For every origin, discover viable reachable gateways through map/transfer facts, including cities without an airport. Do not promote a historical airport, city, or personal route into a universal rule.
2. Normalize the departure date and passenger/cabin constraints. Search no more than seven dates or airport combinations without explaining the call expansion.
3. Read [provider-tools.md](references/provider-tools.md) and inspect the installed CLI/MCP schema before invoking a provider. Never guess command flags.
4. Query FlyAI first through `travel-assistant flyai ...`, which injects the unified credentials file into the pinned FlyAI CLI. Keep provider identity, fare type, taxes, baggage, cancellation/change rules, booking link, and query time when returned.
5. If requested, enrich matching services with Variflight schedule/status/price information. Treat 401 as expired, 403 as forbidden, 429 as rate limited, and insufficient balance as a provider limitation.
6. Use `TravelOffer` normalization and conservative deduplication. Same-provider fare variants remain separate.
7. Compare total known cost, not just the advertised base fare. If taxes or baggage are missing, report the total as unknown rather than adding a remembered fee.
8. Return enough facts for generic `GatewayCandidate` ranking: provider-reported tax-inclusive fare when available, query time, airport identity, and any independent ground-access result. The routing engine, not the flight Skill, decides the winning gateway.

## Output

Include airline, flight number, airports, departure/arrival, duration, stops, known price components, price type, baggage/refund status, source, query timestamp, and booking link. State whether each number is a live offer or reference value.

Do not buy, enter real-name information, submit an order, or pay. Stop at the booking link unless the user gives a separate explicit confirmation. A page may be opened only through `verify-travel-web` after structured search and only for verification.
