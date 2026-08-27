# TianShu TravelOS China Travel Agent Skill Plugin

An eight-Skill Codex Plugin for evidence-backed China travel planning. The parent `$plan-china-trip` Agent Skill routes flight, train, hotel, transfer, web-verification, OmniRoute exploration, and exact presentation Skills.

Auto defaults to Pro exploration, while Pro Max requires explicit opt-in. Every tier retains student fares, luggage, accommodation, taxes, transfers, refund rules, fatigue, and time-window checks.

```bash
travel-assistant plan --tier auto --presentation html < request-and-legs.json > itinerary.json
travel-assistant render-plan --format html --output itinerary.html < itinerary.json
```

Install and use the complete Skill Plugin from https://github.com/19Chris19/china-travel-assistant. Dynamic prices and availability require provider access; real-name entry, order submission, payment, and refund/change actions remain outside this runtime without separate confirmation.
