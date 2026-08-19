import json
import os
import unittest
from unittest.mock import patch

from china_travel_assistant.amap import AmapClient, AmapError


class FakeResponse:
    def __init__(self, payload, status=200):
        self.payload = payload
        self.status = status

    def read(self):
        return json.dumps(self.payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False


class AmapTests(unittest.TestCase):
    def test_text_search_uses_environment_key_and_returns_normalized_pois(self):
        seen = {}

        def opener(request, *, timeout):
            seen["url"] = request.full_url
            return FakeResponse(
                {
                    "status": "1",
                    "pois": [
                        {
                            "id": "poi-1",
                            "name": "苏州大学独墅湖校区",
                            "address": "仁爱路199号",
                            "location": "120.737,31.271",
                        }
                    ],
                }
            )

        with patch.dict(os.environ, {"AMAP_WEBSERVICE_KEY": "private-key"}, clear=False):
            result = AmapClient(opener=opener).text_search("苏州大学", city="苏州")

        self.assertIn("key=private-key", seen["url"])
        self.assertEqual(result[0]["name"], "苏州大学独墅湖校区")
        self.assertEqual(result[0]["longitude"], 120.737)
        self.assertEqual(result[0]["latitude"], 31.271)

    def test_provider_error_never_contains_key(self):
        def opener(_request, *, timeout):
            return FakeResponse({"status": "0", "info": "INVALID_USER_KEY private-key"})

        with patch.dict(os.environ, {"AMAP_WEBSERVICE_KEY": "private-key"}, clear=False):
            with self.assertRaises(AmapError) as error:
                AmapClient(opener=opener).text_search("苏州大学", city="苏州")

        self.assertNotIn("private-key", str(error.exception))
        self.assertIn("[redacted]", str(error.exception))

    def test_transport_error_does_not_retain_key_in_exception_chain(self):
        def opener(request, *, timeout):
            raise RuntimeError(request.full_url)

        with patch.dict(os.environ, {"AMAP_WEBSERVICE_KEY": "private-key"}, clear=True):
            with self.assertRaises(AmapError) as error:
                AmapClient(opener=opener).text_search("苏州大学", city="苏州")

        self.assertNotIn("private-key", str(error.exception))
        self.assertIsNone(error.exception.__cause__)
        self.assertIsNone(error.exception.__context__)

    def test_malformed_provider_payload_is_a_sanitized_amap_error(self):
        for payload in (
            None,
            [],
            {"status": "1"},
            {"status": "1", "pois": {}},
            {"status": "1", "pois": ""},
            {"status": "1", "pois": 0},
            {"status": "1", "pois": False},
            {"status": "1", "pois": [None]},
        ):
            with self.subTest(payload=payload):
                def opener(_request, *, timeout):
                    return FakeResponse(payload)

                with patch.dict(os.environ, {"AMAP_WEBSERVICE_KEY": "private-key"}, clear=True):
                    with self.assertRaises(AmapError) as error:
                        AmapClient(opener=opener).text_search("苏州大学", city="苏州")

                self.assertNotIn("private-key", str(error.exception))
                self.assertIsNone(error.exception.__context__)

    def test_transit_route_normalizes_explicit_cost_duration_and_transfers(self):
        seen = {}

        def opener(request, *, timeout):
            seen["url"] = request.full_url
            return FakeResponse(
                {
                    "status": "1",
                    "route": {
                        "transits": [
                            {
                                "cost": "8",
                                "duration": "5401",
                                "segments": [
                                    {"bus": {"buslines": [{"name": "地铁2号线"}]}},
                                    {"bus": {"buslines": [{"name": "地铁11号线"}]}},
                                ],
                            }
                        ]
                    },
                }
            )

        result = AmapClient(api_key="private-key", opener=opener).route(
            (121.8, 31.15),
            (120.73, 31.27),
            mode="transit",
            city="上海",
            destination_city="苏州",
        )

        self.assertIn("/v3/direction/transit/integrated", seen["url"])
        self.assertIn("city=%E4%B8%8A%E6%B5%B7", seen["url"])
        self.assertEqual(result[0]["duration_minutes"], 91)
        self.assertEqual(result[0]["cost_cny"], 8.0)
        self.assertEqual(result[0]["transfers"], 1)
        self.assertIsNotNone(result[0]["queried_at"])

    def test_walking_route_preserves_unknown_cost(self):
        def opener(_request, *, timeout):
            return FakeResponse(
                {
                    "status": "1",
                    "route": {"paths": [{"distance": "1250", "duration": "901"}]},
                }
            )

        result = AmapClient(api_key="private-key", opener=opener).route(
            (120.7, 31.2), (120.71, 31.21), mode="walking"
        )

        self.assertEqual(result[0]["distance_meters"], 1250)
        self.assertEqual(result[0]["duration_minutes"], 16)
        self.assertEqual(result[0]["transfers"], 0)
        self.assertIsNone(result[0]["cost_cny"])

    def test_taxi_route_uses_only_provider_reported_taxi_cost(self):
        def opener(_request, *, timeout):
            return FakeResponse(
                {
                    "status": "1",
                    "route": {
                        "taxi_cost": "42.5",
                        "paths": [{"distance": "23000", "duration": "1800"}],
                    },
                }
            )

        result = AmapClient(api_key="private-key", opener=opener).route(
            (119.7, 32.4), (119.4, 32.2), mode="taxi"
        )

        self.assertEqual(result[0]["cost_cny"], 42.5)
        self.assertEqual(result[0]["mode"], "taxi")

    def test_transit_route_requires_origin_city(self):
        with self.assertRaises(ValueError):
            AmapClient(api_key="private-key").route(
                (121.8, 31.15), (120.73, 31.27), mode="transit"
            )

    def test_transit_alternative_lines_do_not_inflate_transfer_count(self):
        def opener(_request, *, timeout):
            return FakeResponse(
                {
                    "status": "1",
                    "route": {
                        "transits": [
                            {
                                "segments": [
                                    {
                                        "bus": {
                                            "buslines": [
                                                {"name": "快线"},
                                                {"name": "普通线"},
                                            ]
                                        }
                                    }
                                ]
                            }
                        ]
                    },
                }
            )

        result = AmapClient(api_key="private-key", opener=opener).route(
            (120.7, 31.2), (120.8, 31.3), mode="transit", city="苏州"
        )

        self.assertEqual(result[0]["transfers"], 0)


if __name__ == "__main__":
    unittest.main()
