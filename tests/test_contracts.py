import unittest
from datetime import datetime, timezone
from math import inf, nan

from china_travel_assistant.contracts import (
    EvidenceStatus,
    ExplorationPolicy,
    ExplorationTier,
    GatewayCandidate,
    GroundAccessOption,
    ItineraryCandidate,
    ItineraryLeg,
    PlaceEvidence,
    PresentationCapabilities,
    PresentationMode,
    ProviderHealth,
    ProviderHealthRecord,
    RiskLevel,
    TransferLeg,
    TravelOffer,
    TravelRequest,
    WeatherRisk,
)


class ContractTests(unittest.TestCase):
    def test_request_defaults_to_auto_and_preserves_shared_capabilities(self):
        request = TravelRequest.from_mapping(
            {
                "origin": "沈阳",
                "destination": "苏州",
                "date_start": "2026-08-31",
                "student_fare": True,
                "allow_overnight": False,
            }
        )

        self.assertEqual(request.exploration_tier, ExplorationTier.AUTO)
        self.assertTrue(request.student_fare)
        self.assertFalse(request.allow_overnight)
        self.assertEqual(request.to_dict()["exploration_tier"], "auto")

    def test_request_accepts_explicit_pro_max_and_challenge_tolerance(self):
        request = TravelRequest.from_mapping(
            {
                "origin": "沈阳",
                "destination": "苏州",
                "date_start": "2026-08-31",
                "tier": "pro_max",
                "risk_tolerance": "challenge",
                "arrival_deadline": "2026-09-01T08:00:00+08:00",
            }
        )

        self.assertEqual(request.exploration_tier, ExplorationTier.PRO_MAX)
        self.assertEqual(request.risk_tolerance, RiskLevel.CHALLENGE)
        self.assertEqual(request.arrival_deadline.hour, 8)

    def test_request_rejects_unknown_tier_and_non_boolean_flags(self):
        base = {"origin": "沈阳", "destination": "苏州", "date_start": "2026-08-31"}

        with self.assertRaisesRegex(ValueError, "exploration_tier"):
            TravelRequest.from_mapping({**base, "tier": "extreme"})
        with self.assertRaisesRegex(ValueError, "student_fare"):
            TravelRequest.from_mapping({**base, "student_fare": "sometimes"})

    def test_itinerary_contract_preserves_unknowns_and_evidence(self):
        leg = ItineraryLeg.from_mapping(
            {
                "leg_id": "flight-1",
                "mode": "flight",
                "origin": "沈阳桃仙",
                "destination": "合肥新桥",
                "provider": "flyai",
                "service_number": "9C0001",
                "evidence_status": "verified",
            }
        )
        candidate = ItineraryCandidate(
            itinerary_id="creative-1",
            title="合肥飞铁组合",
            tier=ExplorationTier.PRO,
            legs=(leg,),
            risk_level=RiskLevel.MANAGED,
            evidence_status=EvidenceStatus.PARTIAL,
            unknown_fields=("total_price_cny",),
        )

        payload = candidate.to_dict()
        self.assertIsNone(payload["total_price_cny"])
        self.assertEqual(payload["legs"][0]["evidence_status"], "verified")
        self.assertEqual(payload["unknown_fields"], ["total_price_cny"])

    def test_presentation_capability_prefers_visualize_then_exact_fallbacks(self):
        self.assertEqual(PresentationCapabilities(visualize=True).choose(), PresentationMode.VISUALIZE)
        self.assertEqual(PresentationCapabilities(visualize=False).choose(), PresentationMode.HTML)
        with self.assertRaisesRegex(ValueError, "unavailable"):
            PresentationCapabilities(visualize=False).choose(PresentationMode.VISUALIZE)

    def test_exploration_policy_serializes_public_enum_values(self):
        policy = ExplorationPolicy(
            tier=ExplorationTier.PRO,
            max_hypotheses=24,
            max_self_transfers=2,
            max_modes=3,
            hub_radius_km=350,
            date_flexibility_days=1,
            allow_overnight=True,
            novelty_weight=0.5,
            risk_budget=RiskLevel.MANAGED,
        )

        self.assertEqual(policy.to_dict()["tier"], "pro")
        self.assertEqual(policy.to_dict()["risk_budget"], "managed")

    def test_request_normalizes_dates_and_defaults(self):
        request = TravelRequest.from_mapping(
            {
                "origin": " 沈阳 ",
                "destination": "苏州",
                "date_start": "2026-08-20",
            }
        )

        self.assertEqual(request.origin, "沈阳")
        self.assertEqual(request.date_start.isoformat(), "2026-08-20")
        self.assertEqual(request.date_end.isoformat(), "2026-08-20")
        self.assertEqual(request.travelers, 1)
        self.assertIsNone(request.budget_cny)

    def test_request_keeps_all_user_preferences(self):
        request = TravelRequest.from_mapping(
            {
                "origin": "沈阳",
                "destination": "澳门",
                "date_start": "2026-08-20",
                "date_end": "2026-08-22",
                "travelers": 2,
                "budget_cny": 3000,
                "luggage": "one checked bag",
                "time_preference": "arrive before 18:00",
                "fatigue_preference": "avoid overnight transfers",
            }
        )

        self.assertEqual(request.date_end.isoformat(), "2026-08-22")
        self.assertEqual(request.travelers, 2)
        self.assertEqual(request.budget_cny, 3000)
        self.assertEqual(request.luggage, "one checked bag")
        self.assertEqual(request.time_preference, "arrive before 18:00")
        self.assertEqual(request.fatigue_preference, "avoid overnight transfers")

    def test_offer_preserves_unknown_fields_as_none(self):
        offer = TravelOffer.from_mapping(
            {
                "provider": "flyai",
                "mode": "flight",
                "origin": "SHE",
                "destination": "PVG",
                "departure_at": "2026-08-20T10:00:00+08:00",
            }
        )

        payload = offer.to_dict()
        self.assertIsNone(payload["base_price_cny"])
        self.assertIsNone(payload["taxes_cny"])
        self.assertIsNone(payload["total_price_cny"])
        self.assertIsNone(payload["baggage"])
        self.assertIsNone(payload["refund_change"])
        self.assertIsNone(offer.effective_total_cny)

    def test_offer_only_computes_total_from_explicit_components(self):
        offer = TravelOffer.from_mapping(
            {
                "provider": "flyai",
                "mode": "flight",
                "origin": "SHE",
                "destination": "PVG",
                "base_price_cny": 350,
                "taxes_cny": 200,
            }
        )

        self.assertEqual(offer.effective_total_cny, 550)
        self.assertEqual(offer.total_basis, "computed_from_explicit_components")

    def test_offer_times_normalize_to_china_standard_time(self):
        naive = TravelOffer.from_mapping(
            {
                "provider": "flyai",
                "mode": "flight",
                "departure_at": "2026-08-20T10:00:00",
            }
        )
        utc = TravelOffer.from_mapping(
            {
                "provider": "variflight",
                "mode": "flight",
                "departure_at": "2026-08-20T02:00:00Z",
            }
        )

        self.assertEqual(naive.departure_at.isoformat(), "2026-08-20T10:00:00+08:00")
        self.assertEqual(utc.departure_at.isoformat(), "2026-08-20T10:00:00+08:00")

        datetime_value = TravelOffer.from_mapping(
            {
                "provider": "12306",
                "mode": "train",
                "departure_at": datetime(2026, 8, 20, 2, 0, tzinfo=timezone.utc),
            }
        )
        self.assertEqual(datetime_value.departure_at.isoformat(), "2026-08-20T10:00:00+08:00")

    def test_transfer_buffer_is_explicit_and_included_in_total_duration(self):
        leg = TransferLeg.from_mapping(
            {
                "origin": "浦东机场",
                "destination": "上海虹桥站",
                "mode": "metro",
                "duration_minutes": 95,
                "buffer_minutes": 30,
                "source": "amap",
            }
        )

        self.assertEqual(leg.total_duration_minutes, 125)

        self.assertEqual(leg.distance_meters, None)
        self.assertEqual(leg.cost_cny, None)
        self.assertEqual(leg.transfers, None)

    def test_transfer_keeps_reported_distance_cost_and_transfers(self):
        leg = TransferLeg.from_mapping(
            {
                "origin": "机场",
                "destination": "车站",
                "mode": "taxi",
                "distance_meters": 42000,
                "duration_minutes": 50,
                "cost_cny": 86,
                "transfers": 0,
                "buffer_minutes": 20,
                "source": "amap",
            }
        )

        self.assertEqual(leg.distance_meters, 42000)
        self.assertEqual(leg.cost_cny, 86)
        self.assertEqual(leg.transfers, 0)

    def test_provider_health_has_only_public_states(self):
        self.assertEqual(
            {state.value for state in ProviderHealth},
            {
                "ready",
                "missing",
                "expired",
                "forbidden",
                "rate_limited",
                "degraded",
                "unknown",
                "not_required",
            },
        )

    def test_gateway_preserves_unknown_ground_cost_and_only_totals_explicit_values(self):
        complete = GatewayCandidate.from_mapping(
            {
                "gateway_id": "airport-a",
                "name": "通用门户 A",
                "gateway_type": "airport",
                "origin": "出发地",
                "destination": "目的地",
                "flight_total_cny": 520,
                "flight_duration_minutes": 150,
                "ground_access": [
                    {"endpoint": "通用门户 A", "mode": "rail", "cost_cny": 35, "duration_minutes": 42, "transfers": 0},
                    {"endpoint": "目的地", "mode": "metro", "cost_cny": 6, "duration_minutes": 34, "transfers": 1},
                ],
            }
        )
        incomplete = GatewayCandidate.from_mapping(
            {
                "gateway_id": "airport-b",
                "name": "通用门户 B",
                "gateway_type": "airport",
                "origin": "出发地",
                "destination": "目的地",
                "flight_total_cny": 480,
                "ground_access": [{"endpoint": "通用门户 B", "mode": "bus", "duration_minutes": 60}],
            }
        )

        self.assertEqual(complete.total_known_cost_cny, 561)
        self.assertEqual(complete.total_duration_minutes, 226)
        self.assertEqual(complete.transfer_count, 1)
        self.assertIsNone(incomplete.known_ground_cost_cny)
        self.assertIsNone(incomplete.total_known_cost_cny)

    def test_place_weather_and_health_records_round_trip_without_secrets(self):
        weather = WeatherRisk.from_mapping(
            {
                "location": "景点",
                "precipitation_probability": 70,
                "visibility_km": 2,
                "risk_level": "managed",
                "recommendation": "预留接驳缓冲",
            }
        )
        place = PlaceEvidence.from_mapping(
            {
                "place_id": "poi-1",
                "name": "景点",
                "opening_status": "开放状态未返回",
                "weather_risk": weather.to_dict(),
                "access_options": [{"endpoint": "景点", "mode": "walking", "duration_minutes": 15}],
            }
        )
        health = ProviderHealthRecord.from_mapping(
            {
                "provider": "qweather",
                "status": "not_required",
                "required": "false",
                "capabilities": ["weather", "alerts"],
            }
        )

        self.assertEqual(place.to_dict()["weather_risk"]["risk_level"], "managed")
        self.assertEqual(health.to_dict()["status"], "not_required")
        self.assertFalse(health.required)

    def test_contracts_reject_non_finite_money_and_fractional_travelers(self):
        base = {"origin": "沈阳", "destination": "苏州", "date_start": "2026-08-20"}
        for bad_money in (nan, inf, -inf):
            with self.subTest(bad_money=bad_money):
                with self.assertRaises(ValueError):
                    TravelRequest.from_mapping({**base, "budget_cny": bad_money})
        with self.assertRaises(ValueError):
            TravelRequest.from_mapping({**base, "travelers": 1.5})

    def test_contracts_reject_negative_counts_and_string_sources(self):
        with self.assertRaises(ValueError):
            TravelOffer.from_mapping({"provider": "flyai", "mode": "flight", "duration_minutes": -1})
        with self.assertRaises(ValueError):
            TravelOffer.from_mapping({"provider": "flyai", "mode": "flight", "transfers": -1})
        with self.assertRaises(ValueError):
            TravelOffer.from_mapping({"provider": "flyai", "mode": "flight", "sources": "flyai"})
        with self.assertRaises(ValueError):
            TravelOffer.from_mapping({"provider": "flyai", "mode": "flight", "sources": {"flyai", "amap"}})
        with self.assertRaises(ValueError):
            TransferLeg.from_mapping(
                {"origin": "机场", "destination": "车站", "mode": "metro", "distance_meters": -1}
            )


if __name__ == "__main__":
    unittest.main()
