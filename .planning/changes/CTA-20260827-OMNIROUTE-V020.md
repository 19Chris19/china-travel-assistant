# CTA-20260827-OMNIROUTE-V020: TianShu TravelOS Skill v0.2.0

## Goal

Ship a stable Agent Skill release that generates and verifies conventional and non-obvious China travel combinations without relying on model improvisation, then presents exact itinerary facts through the best supported surface.

## Non-Goals

- MCP App UI, authoritative ImageGen text, rental search, payment, and booking submission.
- Replacing FlyAI, 12306, AMap, VariFlight, Ego Browser, or Visualize.

## Risks

- Route novelty could outrank safety or evidence.
- Provider outages or account quotas could be mistaken for product failures.
- Visual output could drift from itinerary JSON.
- Release metadata or documentation could expose credentials or stale quota claims.

## Acceptance

- Standard, Pro, Pro Max, and Auto behavior is deterministic and tested.
- Every result retains a stable baseline and labels benefit, burden, self-transfer, fallback, risk, and evidence.
- Eight Skills are discoverable and the parent Skill invokes exploration and presentation automatically.
- Visualize is preferred when available; local HTML, SVG, and Markdown preserve exact facts without remote scripts.
- Provider setup documentation distinguishes official fixed rules from account-specific terms and includes a verification date.
- Python 3.10/3.13 CI, Plugin validation, Ruff, package builds, Gitleaks, README checks, and local merge rehearsal pass.
- `v0.2.0` is released from verified `main` with wheel, Plugin ZIP, and SHA256 checksums.

## Commit Plan

1. Governance baseline.
2. OmniRoute contracts.
3. Deterministic route composition and CLI.
4. Exploration and presentation Skills.
5. Visualize-first deterministic renderers.
6. Skill-first README and provider documentation.
7. Release metadata, workflow, and artifacts.

## Verification

Record each commit's targeted tests and the final release gates in this file before merge.

## Rollback

Revert the merge commit or reinstall release `v0.1.0`. Provider credentials remain outside Git and require no repository rollback.

