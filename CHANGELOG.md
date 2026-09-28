# Changelog

All notable changes to TianShu TravelOS are documented here. The project follows semantic versioning.

## [0.3.0] - 2026-09-28

### Added

- Generic gateway ranking contracts that compare explicit tax-inclusive flight and ground-access facts without city-specific rules.
- Place evidence, QWeather JWT configuration, and weather-aware outdoor or transfer risk facts.
- Safe `unknown` and `not_required` provider-health states with timestamps and capability scopes.
- A narrow data-health ribbon in exact HTML, SVG, and Markdown itinerary outputs.

### Changed

- All eight Agent Skills now guide automatic gateway scanning, place facts, optional outdoor risk, and evidence-safe degradation.
- `travel-assistant doctor` reports QWeather and Visualize capability state without issuing paid requests by default.

### Security

- QWeather private keys stay outside the repository and must have `0600` permissions.
- Renderers ignore untrusted remediation text and never display raw credentials, private-key paths, or request URLs.

## [0.2.0] - 2026-08-27

### Added

- Eight visible Agent Skills, including independently triggerable OmniRoute exploration and exact trip presentation.
- Standard, Pro, Pro Max, and Auto exploration with deterministic multimodal composition and a stable baseline.
- Risk, evidence, burden, benefit, delay-fallback, transfer-buffer, and unknown-field contracts.
- `travel-assistant plan` and self-contained HTML, SVG, and Markdown `render-plan` outputs.
- Visualize-first capability negotiation without putting ImageGen in the itinerary fact chain.
- Provider application, quota, validity, and failure documentation verified on 2026-08-27.

### Changed

- Auto now biases ordinary requests toward Pro exploration and converges to Standard for rigid or explicitly stable constraints.
- The README and Plugin metadata now foreground the product as an Agent Skill Plugin.

### Security

- Browser automation remains Ego Browser only.
- Missing provider values remain unknown, and real-name entry, submission, payment, cancellation, refund, or changes require separate confirmation.

## [0.1.0] - 2026-08-19

- Initial six-Skill China travel Plugin with provider routing, unified contracts, diagnostics, local credential isolation, and README visual assets.

[0.2.0]: https://github.com/19Chris19/china-travel-assistant/compare/v0.1.0...v0.2.0
[0.3.0]: https://github.com/19Chris19/china-travel-assistant/compare/v0.2.0...v0.3.0
[0.1.0]: https://github.com/19Chris19/china-travel-assistant/releases/tag/v0.1.0
