# Public Contracts

TravelRequest contains origin, destination, date window, travelers, budget, luggage, time preference, and fatigue preference.

TravelOffer contains provider, mode, carrier/service, endpoints/times, explicit price components, duration, transfers, baggage, refund/change rules, booking link, query time, price type, and source list.

Offer and query timestamps are normalized to `Asia/Shanghai`. A timestamp without an explicit offset is interpreted as China Standard Time; timestamps with another offset are converted to China Standard Time.

TransferLeg contains endpoints, mode, distance, provider duration, explicit buffer, cost, transfer count, source, and query time. The AMap adapter supports walking, transit, driving, and taxi routes; missing provider fields remain null.

GatewayCandidate joins an arbitrary airport or rail gateway, the explicit flight total,
and its ground-access legs. A gateway gets a total only when both the flight and every
required ground-access cost are explicit. Rankings place incomplete costs after complete
facts rather than inventing a total.

GroundAccessOption records a concrete access leg, including endpoint, mode, reported
fare, duration, transfers, explicit buffer, source, timestamp, and evidence status.

PlaceEvidence records a place, its reported opening status, access options, source, and
optional WeatherRisk. WeatherRisk can contain only provider-reported precipitation,
wind, visibility, alerts, sunrise/sunset, timestamps, risk level, and recommendation.
Unknown weather values remain null.

ProviderHealthRecord is separate from live evidence. Its state is one of ready,
missing, expired, forbidden, rate_limited, degraded, unknown, or not_required; it also
records safe capability names and a check timestamp. A ready provider never proves a
specific ticket, inventory item, route, or opening status.

Unknown fields remain null. A total may be computed only when both explicit base price and explicit taxes are present. Page evidence remains separate from API/MCP evidence.
