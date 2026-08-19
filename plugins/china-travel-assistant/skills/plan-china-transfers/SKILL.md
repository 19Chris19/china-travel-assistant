---
name: plan-china-transfers
description: Plan China airport, railway-station, metro, bus, taxi, walking, and last-mile transfers using AMap POI and route data. Use when the user asks how to connect transport legs, compare transfer cost and time, find stations or airports, or plan urban transit.
---

# Plan China Transfers

Use the official AMap Web Service or registered AMap MCP through the project adapter. The local adapter supports AMap POI, walking, transit, driving, and taxi endpoints. Do not guess coordinates, fares, distance, or travel time.

## Workflow

1. Resolve every named airport, station, venue, hotel, and destination with a city-limited POI search.
2. If multiple plausible POIs are returned, show names, districts, and addresses and ask the user to choose. Do not silently pick a similarly named place.
3. Use the same coordinate system for all adjacent legs. AMap locations are GCJ-02; never mix them with Baidu coordinates.
4. Query the requested modes, normally public transit first, then walking, taxi/driving, or airport bus when relevant.
5. Add a visible buffer for security, exit, luggage, station transfer, and boarding constraints. The buffer is not part of provider duration; represent it in `TransferLeg.buffer_minutes`.
6. Keep successful independent legs when one route fails. Mark the overall result partial and identify the failed leg.

For each leg return origin, destination, mode, distance, provider duration, buffer, total planning duration, fare, transfers, source, query time, and map link. Distinguish provider-reported fare from a user-entered estimate.

Do not use browser automation to replace a missing map API result. A browser is only a later verification surface.
