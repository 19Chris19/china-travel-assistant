# Flight Provider Tools

## FlyAI

Required package: `@fly-ai/flyai-cli@1.0.16`.

Before searching, run `flyai search-flight --help` or read the installed command reference. Use its structured flight search for the primary result and preserve returned booking links. `FLYAI_API_KEY` is optional enhanced access; do not require it for trial access when the installed CLI supports an unauthenticated query.

## Variflight

External package: `@variflight-ai/variflight-mcp@1.0.3` with `VARIFLIGHT_API_KEY`.

Discover `tools/list` at runtime. Typical tools cover route schedules, flight-number status, transfers, price-by-city, punctuality/comfort, and airport weather. Use only the smallest tool set required by the request.

Variflight data is optional enrichment in this project. Authentication, quota, or balance failure must not erase valid FlyAI results.

## Error Labels

| Condition | Provider health |
| --- | --- |
| missing binary/key | `missing` |
| HTTP 401 or explicit expired token | `expired` |
| HTTP 403 | `forbidden` |
| HTTP 429 | `rate_limited` |
| timeout, malformed response, balance failure | `degraded` |
