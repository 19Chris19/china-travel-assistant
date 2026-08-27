import unittest

from china_travel_assistant.contracts import ExplorationTier, ItineraryLeg, RiskLevel, TravelRequest
from china_travel_assistant.omniroute import build_search_plan, compose_itineraries, plan_trip, policy_for, resolve_tier


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

        self.assertEqual({item.template for item in standard}, {"direct", "nearby_gateway"})
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


if __name__ == "__main__":
    unittest.main()
