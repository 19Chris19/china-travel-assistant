# Provider Routing

Use structured sources before page verification.

| Capability | Primary | Optional enrichment | Page verification |
| --- | --- | --- | --- |
| Domestic flights | FlyAI CLI | Variflight status/schedule/price | Ego Browser only when login-aware page data is needed |
| China rail | 12306 MCP | FlyAI booking link | Normally unnecessary |
| Hotels | FlyAI CLI | None | Ego Browser for room-level or login price checks |
| POI and transfers | AMap | None | Not a replacement for map data |

If a primary source fails, report its health state and keep independent partial results. Do not turn an optional source into an unlabeled replacement. Never claim that FlyAI CLI is a directly registered Codex MCP; it is a CLI that calls FlyAI/Fliggy services.

Browser verification must follow `verify-travel-web`. It is a fallback and evidence surface, not a silent scraping default.
