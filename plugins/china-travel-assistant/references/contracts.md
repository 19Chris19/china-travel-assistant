# Public Contracts

TravelRequest contains origin, destination, date window, travelers, budget, luggage, time preference, and fatigue preference.

TravelOffer contains provider, mode, carrier/service, endpoints/times, explicit price components, duration, transfers, baggage, refund/change rules, booking link, query time, price type, and source list.

Offer and query timestamps are normalized to `Asia/Shanghai`. A timestamp without an explicit offset is interpreted as China Standard Time; timestamps with another offset are converted to China Standard Time.

TransferLeg contains endpoints, mode, distance, provider duration, explicit buffer, cost, transfer count, source, and query time. The AMap adapter supports walking, transit, driving, and taxi routes; missing provider fields remain null.

ProviderHealth is one of ready, missing, expired, forbidden, rate_limited, or degraded.

Unknown fields remain null. A total may be computed only when both explicit base price and explicit taxes are present. Page evidence remains separate from API/MCP evidence.
