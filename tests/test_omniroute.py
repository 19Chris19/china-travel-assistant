import unittest

from china_travel_assistant.contracts import (
    ExplorationTier,
    GatewayCandidate,
    ItineraryLeg,
    PlaceEvidence,
    RiskLevel,
    TravelRequest,
)
from china_travel_assistant.omniroute import (
    build_search_plan,
    compose_itineraries,
    plan_trip,
    policy_for,
    rank_gateway_candidates,
    rank_place_evidence,
    resolve_tier,
)


def request(**overrides):
    payload = {
        "origin": "沈阳",
        "destination": "苏州",
        "date_start": "2026-08-30",
        "student_fare": True,
    }
    payload.update(overrides)
    return TravelRequest.from_mapping(payload)


def leg(leg_id, mode, origin, destination, **overrides):
    payload = {
        "leg_id": leg_id,
        "mode": mode,
        "origin": origin,
        "destination": destination,
        "provider": "fixture",
        "evidence_status": "verified",
    }
    payload.update(overrides)
    return ItineraryLeg.from_mapping(payload)


class OmniRouteTests(unittest.TestCase):
    def test_auto_biases_pro_but_hard_constraints_resolve_standard(self):
        self.assertEqual(resolve_tier(request()), ExplorationTier.PRO)
        self.assertEqual(resolve_tier(request(direct_only=True)), ExplorationTier.STANDARD)
        self.assertEqual(
            resolve_tier(request(arrival_deadline="2026-08-31T08:00:00+08:00")),
            ExplorationTier.STANDARD,
        )

    def test_all_tiers_keep_student_fare_in_search_instructions(self):
        for tier in ("standard", "pro", "pro_max"):
            item = request(tier=tier)
            instructions = build_search_plan(item, policy_for(item))
            self.assertTrue(all(instruction.student_fare for instruction in instructions), tier)

    def test_pro_and_pro_max_expand_search_breadth_without_changing_core_capabilities(self):
        standard = build_search_plan(request(tier="standard"), policy_for(request(tier="standard")))
        pro = build_search_plan(request(tier="pro"), policy_for(request(tier="pro")))
        pro_max = build_search_plan(request(tier="pro_max"), policy_for(request(tier="pro_max")))

        self.assertEqual({item.template for item in standard}, {"direct", "gateway_scan"})
        self.assertIn("flight_train", {item.template for item in pro})
        self.assertIn("overnight_multimodal", {item.template for item in pro_max})
        self.assertGreater(len(pro_max), len(pro))

    def test_compose_keeps_stable_baseline_and_adds_verified_multimodal_option(self):
        legs = [
            leg(
                "direct",
                "train",
                "沈阳",
                "苏州",
                departure_at="2026-08-30T12:00:00+08:00",
                arrival_at="2026-08-30T22:00:00+08:00",
                total_price_cny=730,
            ),
            leg(
                "flight",
                "flight",
                "沈阳",
                "合肥",
                departure_at="2026-08-30T08:00:00+08:00",
                arrival_at="2026-08-30T10:30:00+08:00",
                total_price_cny=520,
            ),
            leg(
                "rail",
                "train",
                "合肥",
                "苏州",
                departure_at="2026-08-30T13:30:00+08:00",
                arrival_at="2026-08-30T15:30:00+08:00",
                total_price_cny=150,
                self_transfer=True,
            ),
        ]

        itineraries = compose_itineraries(request(tier="pro"), legs, policy_for(request(tier="pro")))

        self.assertEqual(len(itineraries), 2)
        self.assertTrue(itineraries[0].is_baseline)
        self.assertEqual(itineraries[0].risk_level, RiskLevel.STABLE)
        self.assertEqual(itineraries[1].total_price_cny, 670)
        self.assertIsNotNone(itineraries[1].novelty_reason)
        self.assertIn("less", itineraries[1].benefit_summary)

    def test_tight_self_transfer_is_rejected(self):
        legs = [
            leg(
                "flight",
                "flight",
                "沈阳",
                "合肥",
                departure_at="2026-08-30T08:00:00+08:00",
                arrival_at="2026-08-30T10:30:00+08:00",
                total_price_cny=520,
            ),
            leg(
                "rail",
                "train",
                "合肥",
                "苏州",
                departure_at="2026-08-30T11:00:00+08:00",
                arrival_at="2026-08-30T13:00:00+08:00",
                total_price_cny=150,
                self_transfer=True,
            ),
        ]

        self.assertEqual(
            compose_itineraries(request(tier="pro"), legs, policy_for(request(tier="pro"))),
            tuple(),
        )

    def test_unknown_leg_price_keeps_total_unknown(self):
        result = plan_trip(
            request(tier="standard"),
            [leg("direct", "train", "沈阳", "苏州", duration_minutes=600)],
        )

        itinerary = result["itineraries"][0]
        self.assertIsNone(itinerary["total_price_cny"])
        self.assertIn("total_price_cny", itinerary["unknown_fields"])

    def test_pro_max_respects_explicit_stable_risk_cap(self):
        item = request(tier="pro_max", risk_tolerance="stable")
        self.assertEqual(policy_for(item).risk_budget, RiskLevel.STABLE)

    def test_generic_gateways_rank_complete_door_to_door_costs_before_unknown_costs(self):
        candidates = [
            GatewayCandidate.from_mapping(
                {
                    "gateway_id": "unknown-ground",
                    "name": "候选门户乙",
                    "gateway_type": "airport",
                    "origin": "无机场城市",
                    "destination": "目的地",
                    "flight_total_cny": 300,
                    "ground_access": [{"endpoint": "候选门户乙", "mode": "bus", "duration_minutes": 60}],
                }
            ),
            GatewayCandidate.from_mapping(
                {
                    "gateway_id": "complete-ground",
                    "name": "候选门户甲",
                    "gateway_type": "airport",
                    "origin": "无机场城市",
                    "destination": "目的地",
                    "flight_total_cny": 350,
                    "ground_access": [{"endpoint": "候选门户甲", "mode": "rail", "cost_cny": 30, "duration_minutes": 45, "transfers": 0}],
                }
            ),
        ]

        ranked = rank_gateway_candidates(candidates)

        self.assertEqual(ranked[0].gateway_id, "complete-ground")
        self.assertEqual(ranked[0].rank, 1)
        self.assertIn("已知门到门成本", ranked[0].ranking_reason)
        self.assertIn("未返回", ranked[1].ranking_reason)

    def test_place_ranking_keeps_closed_or_weather_risky_places_as_explicit_lower_priority(self):
        places = [
            PlaceEvidence.from_mapping(
                {
                    "place_id": "weather-risk",
                    "name": "户外景点",
                    "weather_risk": {"location": "户外景点", "risk_level": "challenge"},
                }
            ),
            PlaceEvidence.from_mapping(
                {
                    "place_id": "open-stable",
                    "name": "室内景点",
                    "opening_status": "开放",
                    "weather_risk": {"location": "室内景点", "risk_level": "stable"},
                }
            ),
            PlaceEvidence.from_mapping(
                {
                    "place_id": "closed",
                    "name": "闭园景点",
                    "opening_status": "关闭",
                }
            ),
        ]

        ranked = rank_place_evidence(places)

        self.assertEqual([item.place_id for item in ranked], ["open-stable", "weather-risk", "closed"])
        self.assertIn("不可用", ranked[-1].ranking_reason)

    def test_plan_includes_gateway_place_and_health_facts_without_affecting_route_composition(self):
        result = plan_trip(
            request(tier="standard"),
            [leg("direct", "train", "沈阳", "苏州", total_price_cny=730)],
            gateway_candidates=[
                GatewayCandidate.from_mapping(
                    {
                        "gateway_id": "gateway",
                        "name": "门户",
                        "gateway_type": "airport",
                        "origin": "沈阳",
                        "destination": "苏州",
                        "flight_total_cny": 500,
                        "ground_access": [{"endpoint": "门户", "mode": "metro", "cost_cny": 8}],
                    }
                )
            ],
        )

        self.assertEqual(result["gateway_candidates"][0]["total_known_cost_cny"], 508)
        self.assertEqual(result["place_evidence"], [])
        self.assertEqual(result["provider_health"], [])


if __name__ == "__main__":
    unittest.main()
