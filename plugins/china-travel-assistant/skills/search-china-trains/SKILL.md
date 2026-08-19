---
name: search-china-trains
description: Search China Railway train schedules, seats, fares, direct routes, and transfers through the 12306 MCP. Use when the user asks for train tickets, high-speed rail, station connections, or a rail alternative; never submit a purchase or payment.
---

# Search China Trains

Use the 12306 MCP as the primary rail source. It is a query service in this Skill, not a purchase automation tool.

## Workflow

1. Normalize cities and stations without silently choosing between similarly named stations. Ask when the station choice changes the transfer plan.
2. Normalize dates to `YYYY-MM-DD` in China Standard Time.
3. Discover the installed 12306 MCP tools and schemas before calling them. Prefer direct route search, then a bounded transfer search when direct results are insufficient.
4. Preserve train number, departure/arrival station and time, duration, seat classes, prices, availability, query time, and source.
5. If a FlyAI booking link is requested, invoke it through `travel-assistant flyai ...` and use it only as optional link enrichment after the 12306 result. Keep 12306 as the schedule and fare source.
6. Compare direct, one-transfer, and station-change options with explicit transfer buffers. Do not present a connection as feasible without a buffer and station compatibility check.

Show direct and transfer options separately. Mark missing seat availability or fare fields as `未返回`. Include a platform link when available, but stop at a user-purchasable link.

Never enter identity information, submit an order, claim a ticket, pay, or modify/refund a ticket. Any transactional step requires a separate explicit confirmation.
