# Project State

## Stable Release

- Version: `v0.3.0` — 远行计划局 · 中国出行 Agent Skill.
- Release merge: `23977838012796de8887dab218b5b8d35c2b1924`, PR [#2](https://github.com/19Chris19/china-travel-assistant/pull/2).
- Release: [GitHub v0.3.0](https://github.com/19Chris19/china-travel-assistant/releases/tag/v0.3.0), published 2026-09-28 with Plugin ZIP, wheel, and SHA256SUMS.
- Status: stable release published; repository `main` requires PR, Python 3.10/3.13, Plugin, credential UI, and secrets checks.

## Invariants

- Dynamic travel facts retain source and query time.
- Missing price, inventory, baggage, or refund data remains unknown.
- Image generation never renders authoritative itinerary text.
- Real-name entry, order submission, payment, cancellation, refund, and change require separate confirmation.
- Kimi WebBridge, Chrome Control, and Playwright are outside the runtime.

## Verified

- `123/123` Python tests and `27/27` credential UI tests passed locally; macOS Keychain save/read/replace/delete passed with fake credentials, then test entries were removed.
- All eight strict Skill checks, the official Plugin validator, Ruff, full-history Gitleaks, and deterministic dual-build hashes passed.
- GitHub CI passed Python 3.10/3.13, Plugin reproducibility, Node 22 credential UI, and secrets checks. Remote release artifacts were downloaded and SHA256 verified.
- Three independent holdout routing trials scored 48/48, 45/48, and 48/48; three ambiguous classifications are documented in `plugins/china-travel-assistant/evals/trigger-review-v0.3.0.md`.
- No real provider key, paid `doctor --live`, order submission, or payment was used in release validation.

## Next

- Users with exposed old keys must rotate them and configure the optional local system-credential page; old `credentials.env` is not migrated or read.
- v0.4 may add a product-owned MCP-backed App UI after platform feasibility and separate validation. Housing remains deferred to v2.
