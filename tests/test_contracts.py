import unittest
from math import inf, nan

from china_travel_assistant.contracts import (
    ProviderHealth,
    TransferLeg,
    TravelOffer,
    TravelRequest,
)


class ContractTests(unittest.TestCase):
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
            },
        )

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
