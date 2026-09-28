# CTA-20260928-MULTISOURCE-V030

## Objective

Release TianShu TravelOS Skill v0.3.0 with deterministic gateway ranking,
place evidence, weather-aware outdoor risk, and a safe provider-health ribbon.

## Scope

- Keep the existing eight user-facing Agent Skills and add private orchestration
  modules only.
- Add QWeather JWT configuration without embedding a private key or token in
  the repository.
- Render readiness separately from per-offer evidence in HTML, SVG, and
  Markdown outputs.
- Preserve the confirmation boundary for real-name data, booking, payment,
  changes, and refunds.

## Non-goals

- No city-specific airport rules, rental search, automatic purchasing, or
  second domestic map provider.
- No live paid probe unless the user explicitly runs `travel-assistant doctor --live`.

## Risks and Controls

| Risk | Control |
| --- | --- |
| A key leaks through a URL, output, or test fixture | Keep secrets out of contracts; run gitleaks and dedicated leak tests. |
| Unknown ground costs distort a gateway ranking | Rank known-cost candidates ahead of incomplete ones; retain unknown fields. |
| Weather is presented as certain | Timestamp every observation, preserve unknown values, and label risk separately from availability. |
| Optional provider failure blocks trip planning | Model provider health independently; maintain AMap, FlyAI, and 12306 degradation paths. |

## Acceptance Criteria

- Flight-capable requests receive generic gateway candidates with explainable,
  deterministic rankings and no airport name hard-coded in the orchestration.
- Place, weather, and provider-health facts round-trip through `itinerary.json`.
- `doctor` is offline by default and reports `unknown` and `not_required` in
  addition to existing states.
- Rendered outputs show only relevant health states and never sensitive values.
- Unit tests, plugin validation, Ruff, package build, and secret scanning pass.

## Commit Plan

1. `chore(governance): record v0.3.0 multisource change`
2. `feat(core): add multisource facts and health contracts`
3. `feat(routing): rank generic gateways and place evidence`
4. `feat(presentation): show safe itinerary health ribbon`
5. `docs(skill): document v0.3.0 provider orchestration`
6. `chore(release): prepare v0.3.0 artifacts`

## Rollout and Rollback

Ship through a GitHub pull request after CI. If a provider integration causes
errors, disable that optional provider path and retain the existing core
itinerary output; reverting the corresponding atomic commit restores v0.2.0
behavior without exposing credentials.
