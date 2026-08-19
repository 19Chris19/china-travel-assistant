from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from enum import Enum
from math import isfinite
from typing import Any, Mapping
from zoneinfo import ZoneInfo


CHINA_TIMEZONE = ZoneInfo("Asia/Shanghai")


class ProviderHealth(str, Enum):
    READY = "ready"
    MISSING = "missing"
    EXPIRED = "expired"
    FORBIDDEN = "forbidden"
    RATE_LIMITED = "rate_limited"
    DEGRADED = "degraded"


def _date(value: Any, *, field_name: str) -> date:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be YYYY-MM-DD")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be YYYY-MM-DD") from exc


def _datetime(value: Any, *, field_name: str) -> datetime | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=CHINA_TIMEZONE)
        return value.astimezone(CHINA_TIMEZONE)
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be ISO-8601")
    normalized = value.replace("Z", "+00:00")
    try:
        result = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be ISO-8601") from exc
    if result.tzinfo is None:
        return result.replace(tzinfo=CHINA_TIMEZONE)
    return result.astimezone(CHINA_TIMEZONE)


def _money(value: Any, *, field_name: str) -> float | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        raise ValueError(f"{field_name} must be a non-negative number")
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be a non-negative number") from exc
    if not isfinite(result) or result < 0:
        raise ValueError(f"{field_name} must be a non-negative number")
    return result


def _integer(value: Any, *, field_name: str, minimum: int = 0) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{field_name} must be an integer")
    if isinstance(value, int):
        result = value
    elif isinstance(value, float):
        if not isfinite(value) or not value.is_integer():
            raise ValueError(f"{field_name} must be an integer")
        result = int(value)
    elif isinstance(value, str):
        try:
            result = int(value.strip())
        except ValueError as exc:
            raise ValueError(f"{field_name} must be an integer") from exc
    else:
        raise ValueError(f"{field_name} must be an integer")
    if result < minimum:
        raise ValueError(f"{field_name} must be at least {minimum}")
    return result


def _optional_integer(value: Any, *, field_name: str, minimum: int = 0) -> int | None:
    if value is None or value == "":
        return None
    return _integer(value, field_name=field_name, minimum=minimum)


def _required_text(value: Any, *, field_name: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{field_name} is required")
    return text


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _sources(value: Any, provider: str) -> tuple[str, ...]:
    if value is None or value == "":
        return (provider,)
    if isinstance(value, str) or not isinstance(value, (list, tuple)):
        raise ValueError("sources must be a list of provider names")
    sources = tuple(_required_text(item, field_name="sources item") for item in value)
    return tuple(dict.fromkeys(sources or (provider,)))


@dataclass(frozen=True)
class TravelRequest:
    origin: str
    destination: str
    date_start: date
    date_end: date
    travelers: int = 1
    budget_cny: float | None = None
    luggage: str | None = None
    time_preference: str | None = None
    fatigue_preference: str | None = None

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "TravelRequest":
        start = _date(value.get("date_start"), field_name="date_start")
        end = _date(value.get("date_end", start), field_name="date_end")
        travelers = _integer(value.get("travelers", 1), field_name="travelers", minimum=1)
        if end < start:
            raise ValueError("date_end must not be before date_start")
        return cls(
            origin=_required_text(value.get("origin"), field_name="origin"),
            destination=_required_text(value.get("destination"), field_name="destination"),
            date_start=start,
            date_end=end,
            travelers=travelers,
            budget_cny=_money(value.get("budget_cny"), field_name="budget_cny"),
            luggage=_optional_text(value.get("luggage")),
            time_preference=_optional_text(value.get("time_preference")),
            fatigue_preference=_optional_text(value.get("fatigue_preference")),
        )

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["date_start"] = self.date_start.isoformat()
        payload["date_end"] = self.date_end.isoformat()
        return payload


@dataclass(frozen=True)
class TravelOffer:
    provider: str
    mode: str
    carrier: str | None = None
    service_number: str | None = None
    origin: str | None = None
    destination: str | None = None
    departure_at: datetime | None = None
    arrival_at: datetime | None = None
    base_price_cny: float | None = None
    taxes_cny: float | None = None
    total_price_cny: float | None = None
    duration_minutes: int | None = None
    transfers: int | None = None
    baggage: str | None = None
    refund_change: str | None = None
    booking_url: str | None = None
    queried_at: datetime | None = None
    price_type: str | None = None
    sources: tuple[str, ...] = field(default_factory=tuple)

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "TravelOffer":
        provider = _required_text(value.get("provider"), field_name="provider")
        duration = value.get("duration_minutes")
        transfers = value.get("transfers")
        return cls(
            provider=provider,
            mode=_required_text(value.get("mode"), field_name="mode"),
            carrier=_optional_text(value.get("carrier")),
            service_number=_optional_text(value.get("service_number")),
            origin=_optional_text(value.get("origin")),
            destination=_optional_text(value.get("destination")),
            departure_at=_datetime(value.get("departure_at"), field_name="departure_at"),
            arrival_at=_datetime(value.get("arrival_at"), field_name="arrival_at"),
            base_price_cny=_money(value.get("base_price_cny"), field_name="base_price_cny"),
            taxes_cny=_money(value.get("taxes_cny"), field_name="taxes_cny"),
            total_price_cny=_money(value.get("total_price_cny"), field_name="total_price_cny"),
            duration_minutes=_optional_integer(duration, field_name="duration_minutes"),
            transfers=_optional_integer(transfers, field_name="transfers"),
            baggage=_optional_text(value.get("baggage")),
            refund_change=_optional_text(value.get("refund_change")),
            booking_url=_optional_text(value.get("booking_url")),
            queried_at=_datetime(value.get("queried_at"), field_name="queried_at"),
            price_type=_optional_text(value.get("price_type")),
            sources=_sources(value.get("sources"), provider),
        )

    @property
    def effective_total_cny(self) -> float | None:
        if self.total_price_cny is not None:
            return self.total_price_cny
        if self.base_price_cny is not None and self.taxes_cny is not None:
            return self.base_price_cny + self.taxes_cny
        return None

    @property
    def total_basis(self) -> str | None:
        if self.total_price_cny is not None:
            return "provider_total"
        if self.base_price_cny is not None and self.taxes_cny is not None:
            return "computed_from_explicit_components"
        return None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        for key in ("departure_at", "arrival_at", "queried_at"):
            value = payload[key]
            payload[key] = value.isoformat() if value else None
        payload["sources"] = list(self.sources)
        payload["effective_total_cny"] = self.effective_total_cny
        payload["total_basis"] = self.total_basis
        return payload


@dataclass(frozen=True)
class TransferLeg:
    origin: str
    destination: str
    mode: str
    distance_meters: int | None = None
    duration_minutes: int | None = None
    cost_cny: float | None = None
    transfers: int | None = None
    buffer_minutes: int = 0
    source: str | None = None
    queried_at: datetime | None = None

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "TransferLeg":
        duration = value.get("duration_minutes")
        distance = value.get("distance_meters")
        transfers = value.get("transfers")
        buffer_minutes = _integer(value.get("buffer_minutes", 0), field_name="buffer_minutes")
        return cls(
            origin=_required_text(value.get("origin"), field_name="origin"),
            destination=_required_text(value.get("destination"), field_name="destination"),
            mode=_required_text(value.get("mode"), field_name="mode"),
            distance_meters=_optional_integer(distance, field_name="distance_meters"),
            duration_minutes=_optional_integer(duration, field_name="duration_minutes"),
            cost_cny=_money(value.get("cost_cny"), field_name="cost_cny"),
            transfers=_optional_integer(transfers, field_name="transfers"),
            buffer_minutes=buffer_minutes,
            source=_optional_text(value.get("source")),
            queried_at=_datetime(value.get("queried_at"), field_name="queried_at"),
        )

    @property
    def total_duration_minutes(self) -> int | None:
        if self.duration_minutes is None:
            return None
        return self.duration_minutes + self.buffer_minutes

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["queried_at"] = self.queried_at.isoformat() if self.queried_at else None
        payload["total_duration_minutes"] = self.total_duration_minutes
        return payload
