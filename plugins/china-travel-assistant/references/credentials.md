# Credential Reference

Store real values in ~/.config/china-travel-assistant/credentials.env with mode 0600. Environment variables override matching file entries.

| Variable | Provider | Acquire | Required |
| --- | --- | --- | --- |
| AMAP_WEBSERVICE_KEY | AMap Web Service | https://lbs.amap.com/api/webservice/create-project-and-key | Yes for POI/routes |
| AMAP_JSAPI_KEY | AMap JS API | https://lbs.amap.com/api/javascript-api-v2/prerequisites | No |
| AMAP_SECURITY_CODE | AMap JS API | AMap console for the JS application | No |
| FLYAI_API_KEY | FlyAI | https://open.fly.ai/ | No; enhanced access |
| VARIFLIGHT_API_KEY | Variflight | https://mcp.variflight.com/ | No; optional verification |
| VIGOLIVE_API_KEY | Vigolive | Provider account | No; reserved for v2 |

Do not put keys in command-line arguments, MCP URLs, Markdown links, screenshots, generated HTML, or issue reports. The MCP launcher sources the local credentials file before starting the fixed package command.

Variflight quota and key expiry are provider-managed. Treat 401 as expired, 403 as forbidden, 429 as rate limited, and balance failure as degraded.
