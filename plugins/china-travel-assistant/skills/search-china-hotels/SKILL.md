---
name: search-china-hotels
description: Search and compare hotels in mainland China with FlyAI and verify room-level price, cancellation, and availability details through Ego Browser when needed. Use when the user asks for hotels, accommodation, lodging near a station or venue, or price and condition comparison.
---

# Search China Hotels

Use FlyAI for the initial hotel search and room candidates. Use Ego Browser only when a login-specific price, room inventory, cancellation matrix, or detail page needs verification.

## Workflow

1. Normalize city, neighborhood/POI, check-in/check-out dates, travelers, rooms, budget, and priorities.
2. Search FlyAI and preserve property ID/name, address, room type, occupancy, nightly and total price, tax status, cancellation rules, rating, distance, query time, and detail link.
3. Separate list-level lead-in prices from room-level verified prices. Never claim a lead-in price is bookable for the user's dates without room details.
4. Rank by the user's priority: price, distance, cancellation flexibility, transit access, or balanced value. Missing fields remain unknown.
5. If page verification is needed, invoke `verify-travel-web` with the exact property URL and keep the API result and page evidence as separate sources.

Return real detail/booking links and a pre-booking checklist. Do not enter identity information, submit a reservation, store payment details, or pay without explicit confirmation.
