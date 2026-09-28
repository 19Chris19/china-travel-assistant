# CTA-20260928-RELEASE-HARDEN: 远行计划局 v0.3.0

## Goal

Finish the unpublished v0.3.0 branch as a safe, reproducible Codex-first Agent Skill release. Rename the public product to 远行计划局 while preserving stable package, Plugin, Skill, and JSON identifiers.

## Baseline

- Start from `26d369a`, retaining the six existing v0.3.0 commits.
- `main` and `origin/main` remain at the published v0.2.0 merge `c258614` until PR checks pass.
- Prior local validation: 116 tests, Plugin validation, Ruff, wheel build, and a merge rehearsal.

## Scope

- Replace desktop plaintext key entry with a reusable local configuration page and system credential storage. Keep explicit environment variables for CI and headless deployments. Do not auto-import old key values.
- Make core installation independent from optional provider and browser runtimes.
- Improve eight Skill trigger descriptions and measure routing with fixed positive and negative cases.
- Present 智能选择 / 从容 / 拓界 / 远征 while accepting the existing machine tier values; present risk as 稳妥 / 可控 / 挑战.
- Build reproducible Plugin and wheel artifacts, verify hashes and package contents, and extend CI and release gates.
- Publish only after a reviewed PR and passing required checks.

## Invariants

- No real key, browser state, itinerary, or private conversation content enters Git, prompts, logs, or release assets.
- Unknown price, availability, baggage, opening status, and weather remain unknown.
- Booking, real-name entry, payment, changes, cancellation, and refunds require separate explicit confirmation.
- Ego Browser remains the sole browser automation path.

## Acceptance

- Core installation works without optional providers; unsupported Python is rejected before any install.
- Each provider receives only the credential it needs, from a system store on supported desktops or explicit environment injection in headless runs.
- Existing `standard`, `pro`, `pro_max`, and `auto` inputs and outputs remain stable; Chinese aliases are accepted at request and CLI input boundaries.
- All eight Skills pass strict weak-model structure checks and have tested positive/negative routing samples.
- Two clean release builds produce identical SHA-256 hashes; archive audit and secret scanning pass.
- Python 3.10/3.13, Node 22, Plugin validation, Skill validation, Ruff, package and secret gates pass in CI.
- GitHub PR is merged, local main fast-forwards, v0.3.0 tag points at the verified merge commit, and Release assets and description are checked.

## Commit Groups

1. Governance and baseline.
2. Credential page, profile binding, and safe runtime.
3. Core/optional installer and diagnostics.
4. Skill trigger boundaries and fixed evaluation cases.
5. Deterministic release packaging and CI.
6. Public brand, tier aliases, visual and documentation updates.
7. Release notes and final verification.

## Rollback

Revert individual behavior commits through a PR before tagging. For a published release, retain the v0.2.0 tag and artifacts and revert the v0.3.0 merge via a new PR. Credential references are outside Git and remain owned by the local user.
