import unittest

from china_travel_assistant.providers import (
    ProviderAction,
    build_provider_plan,
    classify_provider_error,
)


class ProviderTests(unittest.TestCase):
    def test_flight_plan_uses_flyai_then_optional_variflight(self):
        plan = build_provider_plan("flight", verify_status=True)

        self.assertEqual(
            [(item.provider, item.action) for item in plan],
            [
                ("flyai", ProviderAction.SEARCH),
                ("variflight", ProviderAction.ENRICH),
            ],
        )
        self.assertFalse(plan[1].required)

    def test_browser_is_only_added_for_explicit_web_verification(self):
        regular = build_provider_plan("hotel")
        verified = build_provider_plan("hotel", verify_web=True)

        self.assertNotIn("ego-browser", [item.provider for item in regular])
        self.assertEqual(verified[-1].provider, "ego-browser")
        self.assertEqual(verified[-1].action, ProviderAction.VERIFY)

    def test_train_plan_starts_with_12306(self):
        plan = build_provider_plan("train", include_booking_link=True)

        self.assertEqual(plan[0].provider, "12306")
        self.assertEqual(plan[1].provider, "flyai")
        self.assertFalse(plan[1].required)

    def test_hotel_and_transfer_route_to_the_expected_primary_providers(self):
        hotel = build_provider_plan("hotel")
        transfer = build_provider_plan("transfer")

        self.assertEqual([item.provider for item in hotel], ["flyai"])
        self.assertTrue(hotel[0].required)
        self.assertEqual([item.provider for item in transfer], ["amap"])
        self.assertTrue(transfer[0].required)

    def test_error_classification_is_stable(self):
        cases = {
            401: "expired",
            403: "forbidden",
            429: "rate_limited",
            500: "degraded",
        }
        for status, expected in cases.items():
            with self.subTest(status=status):
                self.assertEqual(classify_provider_error(status).value, expected)


if __name__ == "__main__":
    unittest.main()
