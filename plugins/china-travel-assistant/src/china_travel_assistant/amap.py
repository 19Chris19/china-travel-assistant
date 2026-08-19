from __future__ import annotations

import json
import math
import os
from datetime import datetime
from typing import Any, Callable
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo


class AmapError(RuntimeError):
    pass


class AmapClient:
    POI_URL = "https://restapi.amap.com/v5/place/text"
    ROUTE_URLS = {
        "walking": "https://restapi.amap.com/v3/direction/walking",
        "transit": "https://restapi.amap.com/v3/direction/transit/integrated",
        "driving": "https://restapi.amap.com/v3/direction/driving",
        "taxi": "https://restapi.amap.com/v3/direction/driving",
    }

    def __init__(
        self,
        *,
        api_key: str | None = None,
        opener: Callable[..., Any] = urlopen,
        timeout: float = 10,
    ) -> None:
        self._api_key = api_key or os.environ.get("AMAP_WEBSERVICE_KEY")
        self._opener = opener
        self._timeout = timeout

    def text_search(self, keywords: str, *, city: str) -> list[dict[str, Any]]:
        payload = self._request(
            self.POI_URL,
            {
                "keywords": keywords,
                "region": city,
                "city_limit": "true",
                "show_fields": "business",
            },
        )
        pois = payload.get("pois")
        if not isinstance(pois, list):
            raise AmapError("AMap response invalid: expected POI list")
        if any(not isinstance(item, dict) for item in pois):
            raise AmapError("AMap response invalid: expected POI objects")
        return [self._normalize_poi(item) for item in pois]

    def route(
        self,
        origin: tuple[float, float],
        destination: tuple[float, float],
        *,
        mode: str,
        city: str | None = None,
        destination_city: str | None = None,
    ) -> list[dict[str, Any]]:
        if mode not in self.ROUTE_URLS:
            raise ValueError(f"unsupported AMap route mode: {mode}")
        if mode == "transit" and not city:
            raise ValueError("city is required for transit routes")

        origin_text = self._coordinate(origin, field_name="origin")
        destination_text = self._coordinate(destination, field_name="destination")
        parameters: dict[str, str] = {
            "origin": origin_text,
            "destination": destination_text,
            "output": "JSON",
        }
        if mode == "transit":
            parameters.update({"city": str(city), "extensions": "all", "strategy": "0"})
            if destination_city:
                parameters["cityd"] = destination_city
        elif mode in {"driving", "taxi"}:
            parameters.update({"extensions": "all", "strategy": "10"})

        payload = self._request(self.ROUTE_URLS[mode], parameters)
        route = payload.get("route")
        if not isinstance(route, dict):
            raise AmapError("AMap response invalid: expected route object")
        queried_at = datetime.now(ZoneInfo("Asia/Shanghai")).isoformat()
        if mode == "transit":
            transits = route.get("transits")
            if not isinstance(transits, list) or any(not isinstance(item, dict) for item in transits):
                raise AmapError("AMap response invalid: expected transit list")
            return [
                {
                    "origin": origin_text,
                    "destination": destination_text,
                    "mode": mode,
                    "distance_meters": None,
                    "duration_minutes": self._minutes(item.get("duration")),
                    "cost_cny": self._number(item.get("cost")),
                    "transfers": self._transfers(item.get("segments")),
                    "buffer_minutes": 0,
                    "source": "amap-web-service-v3",
                    "queried_at": queried_at,
                }
                for item in transits
            ]

        paths = route.get("paths")
        if not isinstance(paths, list) or any(not isinstance(item, dict) for item in paths):
            raise AmapError("AMap response invalid: expected route path list")
        taxi_cost = self._number(route.get("taxi_cost")) if mode == "taxi" else None
        return [
            {
                "origin": origin_text,
                "destination": destination_text,
                "mode": mode,
                "distance_meters": self._integer(item.get("distance")),
                "duration_minutes": self._minutes(item.get("duration")),
                "cost_cny": taxi_cost,
                "transfers": 0,
                "buffer_minutes": 0,
                "source": "amap-web-service-v3",
                "queried_at": queried_at,
            }
            for item in paths
        ]

    def _request(self, url: str, parameters: dict[str, str]) -> dict[str, Any]:
        if not self._api_key:
            raise AmapError("AMAP_WEBSERVICE_KEY is not configured")
        query = urlencode({"key": self._api_key, **parameters})
        request = Request(f"{url}?{query}", headers={"User-Agent": "china-travel-assistant/0.1"})
        transport_error: str | None = None
        payload: Any = None
        try:
            with self._opener(request, timeout=self._timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            transport_error = type(exc).__name__
        if transport_error is not None:
            raise AmapError(f"AMap request failed: {transport_error}")
        if not isinstance(payload, dict):
            raise AmapError("AMap response invalid: expected object")
        if payload.get("status") != "1":
            info = str(payload.get("info") or "provider_error").replace(self._api_key, "[redacted]")
            raise AmapError(f"AMap provider error: {info}")
        return payload

    @staticmethod
    def _coordinate(value: tuple[float, float], *, field_name: str) -> str:
        if not isinstance(value, tuple) or len(value) != 2:
            raise ValueError(f"{field_name} must be a (longitude, latitude) tuple")
        try:
            longitude, latitude = (float(value[0]), float(value[1]))
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{field_name} must contain numeric coordinates") from exc
        if not math.isfinite(longitude) or not math.isfinite(latitude):
            raise ValueError(f"{field_name} must contain finite coordinates")
        if not -180 <= longitude <= 180 or not -90 <= latitude <= 90:
            raise ValueError(f"{field_name} coordinates are out of range")
        return f"{longitude:.6f},{latitude:.6f}"

    @staticmethod
    def _number(value: Any) -> float | None:
        if value is None or value == "" or isinstance(value, bool):
            return None
        try:
            number = float(value)
        except (TypeError, ValueError):
            return None
        return number if math.isfinite(number) and number >= 0 else None

    @classmethod
    def _integer(cls, value: Any) -> int | None:
        number = cls._number(value)
        return int(number) if number is not None and number.is_integer() else None

    @classmethod
    def _minutes(cls, seconds: Any) -> int | None:
        number = cls._number(seconds)
        return math.ceil(number / 60) if number is not None else None

    @staticmethod
    def _transfers(segments: Any) -> int | None:
        if not isinstance(segments, list):
            return None
        transit_segment_count = 0
        for segment in segments:
            if not isinstance(segment, dict):
                continue
            bus = segment.get("bus")
            if not isinstance(bus, dict):
                continue
            buslines = bus.get("buslines")
            if isinstance(buslines, list) and any(isinstance(line, dict) for line in buslines):
                transit_segment_count += 1
        return max(0, transit_segment_count - 1)

    @staticmethod
    def _normalize_poi(item: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(item, dict):
            raise ValueError("POI is not an object")
        longitude = latitude = None
        location = item.get("location")
        if isinstance(location, str) and "," in location:
            raw_longitude, raw_latitude = location.split(",", 1)
            try:
                longitude = float(raw_longitude)
                latitude = float(raw_latitude)
            except ValueError:
                longitude = latitude = None
        return {
            "id": item.get("id"),
            "name": item.get("name"),
            "address": item.get("address"),
            "longitude": longitude,
            "latitude": latitude,
            "coordinate_system": "GCJ-02",
            "source": "amap-web-service",
        }
