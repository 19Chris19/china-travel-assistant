# Changelog

All notable changes to TianShu TravelOS are documented here. The project follows semantic versioning.

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
[0.1.0]: https://github.com/19Chris19/china-travel-assistant/releases/tag/v0.1.0
