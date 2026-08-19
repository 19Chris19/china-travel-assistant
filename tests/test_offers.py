import unittest

from china_travel_assistant.contracts import TravelOffer
from china_travel_assistant.offers import deduplicate_offers, rank_offers


def offer(**overrides):
    values = {
        "provider": "flyai",
        "mode": "flight",
        "carrier": "春秋航空",
        "service_number": "9C0001",
        "origin": "SHE",
        "destination": "PVG",
        "departure_at": "2026-08-20T10:00:00+08:00",
        "arrival_at": "2026-08-20T12:30:00+08:00",
        "duration_minutes": 150,
        "total_price_cny": 550,
        "price_type": "live_offer",
        "queried_at": "2026-08-19T10:00:00+08:00",
    }
    values.update(overrides)
    return TravelOffer.from_mapping(values)


class OfferTests(unittest.TestCase):
    def test_deduplicate_merges_same_service_and_keeps_sources(self):
        first = offer(provider="flyai", booking_url="https://example.com/book")
        second = offer(provider="variflight", baggage="7kg")

        result = deduplicate_offers([first, second])

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].booking_url, "https://example.com/book")
        self.assertEqual(result[0].baggage, "7kg")
        self.assertEqual(set(result[0].sources), {"flyai", "variflight"})

    def test_rank_price_places_unknown_prices_last(self):
        known = offer(service_number="9C0002", total_price_cny=500)
        unknown = offer(service_number="9C0003", total_price_cny=None)

        result = rank_offers([unknown, known], by="price")

        self.assertEqual(result[0].service_number, "9C0002")
        self.assertEqual(result[-1].service_number, "9C0003")

    def test_rank_balanced_accounts_for_duration_and_transfers(self):
        direct = offer(service_number="9C0004", total_price_cny=600, transfers=0)
        tiring = offer(
            service_number="9C0005",
            total_price_cny=550,
            duration_minutes=360,
            transfers=2,
        )

        result = rank_offers([tiring, direct], by="balanced")

        self.assertEqual(result[0].service_number, "9C0004")

    def test_deduplicate_never_merges_different_carriers(self):
        spring = offer(carrier="春秋航空", service_number=None, baggage="7kg")
        juneyao = offer(carrier="吉祥航空", service_number=None, baggage="20kg")

        result = deduplicate_offers([spring, juneyao])

        self.assertEqual(len(result), 2)
        self.assertEqual({item.carrier for item in result}, {"春秋航空", "吉祥航空"})

    def test_balanced_ranking_puts_unknown_duration_or_transfers_after_known_values(self):
        unknown = offer(service_number="9C0006", duration_minutes=None, transfers=None)
        known = offer(service_number="9C0007", duration_minutes=150, transfers=0)

        result = rank_offers([unknown, known], by="balanced")

        self.assertEqual(result[0].service_number, "9C0007")

    def test_deduplicate_does_not_merge_records_without_a_stable_identity(self):
        first = offer(carrier=None, service_number=None, origin=None, destination=None, departure_at=None)
        second = offer(carrier=None, service_number=None, origin=None, destination=None, departure_at=None)

        self.assertEqual(len(deduplicate_offers([first, second])), 2)

    def test_deduplicate_is_input_order_independent_for_conflicting_values(self):
        flyai = offer(provider="flyai", total_price_cny=600, sources=("flyai",))
        variflight = offer(provider="variflight", total_price_cny=500, sources=("variflight",))

        forward = deduplicate_offers([flyai, variflight])[0]
        reverse = deduplicate_offers([variflight, flyai])[0]

        self.assertEqual(forward.to_dict(), reverse.to_dict())
        self.assertEqual(forward.provider, "flyai")
        self.assertEqual(forward.total_price_cny, 600)

    def test_deduplicate_keeps_same_provider_fare_variants_separate(self):
        high = offer(provider="flyai", total_price_cny=600)
        low = offer(provider="flyai", total_price_cny=500)

        forward = deduplicate_offers([high, low])
        reverse = deduplicate_offers([low, high])

        self.assertEqual(sorted(item.total_price_cny for item in forward), [500, 600])
        self.assertEqual(
            [item.to_dict() for item in sorted(forward, key=lambda item: item.total_price_cny)],
            [item.to_dict() for item in sorted(reverse, key=lambda item: item.total_price_cny)],
        )

    def test_train_deduplication_keeps_12306_as_primary(self):
        common = {
            "mode": "train",
            "carrier": "中国铁路",
            "service_number": "G1234",
            "origin": "苏州",
            "destination": "上海",
            "departure_at": "2026-08-20T10:00:00+08:00",
            "arrival_at": "2026-08-20T10:30:00+08:00",
        }
        rail = TravelOffer.from_mapping({**common, "provider": "12306", "total_price_cny": 39.5})
        flyai = TravelOffer.from_mapping({**common, "provider": "flyai", "booking_url": "https://example.com"})

        result = deduplicate_offers([flyai, rail])[0]

        self.assertEqual(result.provider, "12306")
        self.assertEqual(result.total_price_cny, 39.5)
        self.assertEqual(result.booking_url, "https://example.com")

    def test_service_number_alone_is_not_a_stable_identity(self):
        incomplete = TravelOffer.from_mapping(
            {"provider": "flyai", "mode": "flight", "service_number": "9C0001"}
        )
        second = TravelOffer.from_mapping(
            {"provider": "variflight", "mode": "flight", "service_number": "9C0001"}
        )

        self.assertEqual(len(deduplicate_offers([incomplete, second])), 2)


if __name__ == "__main__":
    unittest.main()
