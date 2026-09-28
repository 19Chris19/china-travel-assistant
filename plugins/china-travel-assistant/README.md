# 远行计划局 · 中国出行 Agent Skill Plugin

An eight-Skill Codex Plugin for evidence-backed China travel planning. The parent `$plan-china-trip` Agent Skill routes generic gateway discovery, flight, train, hotel, transfer, optional weather risk, web verification, route exploration, and exact presentation Skills.

Smart Select (`auto`) usually resolves to Frontier (`pro`), while Expedition (`pro_max`) requires explicit opt-in. Every tier retains student fares, luggage, accommodation, taxes, transfers, refund rules, fatigue, and time-window checks.

```bash
travel-assistant plan --tier auto --presentation html < request-and-legs.json > itinerary.json
travel-assistant render-plan --format html --output itinerary.html < itinerary.json
```

Install and use the complete Skill Plugin from https://github.com/19Chris19/china-travel-assistant. Dynamic prices and availability require provider access; real-name entry, order submission, payment, and refund/change actions remain outside this runtime without separate confirmation.
