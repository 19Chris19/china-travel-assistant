# Project State

## Active Change

- Change-ID: `CTA-20260827-OMNIROUTE-V020`
- Branch: `codex/CTA-20260827-OMNIROUTE-V020`
- Goal: Release China Travel Assistant Skill v0.2.0 with deterministic exploration tiers and precise visual delivery.
- Baseline: `d82a1d6`, `77/77` unit tests, Plugin validation and GitHub CI passed.
- Status: implementation in progress

## Invariants

- Dynamic travel facts retain source and query time.
- Missing price, inventory, baggage, or refund data remains unknown.
- Image generation never renders authoritative itinerary text.
- Real-name entry, order submission, payment, cancellation, refund, and change require separate confirmation.
- Kimi WebBridge, Chrome Control, and Playwright are outside the runtime.

## Next

Implement the v0.2.0 contracts, deterministic route exploration, Skills, presentation fallbacks, documentation, and release automation described in the active change record.

