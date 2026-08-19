from __future__ import annotations

from dataclasses import replace
from math import inf
from typing import Iterable

from .contracts import TravelOffer


_PROVIDER_PRIORITY = {
    "flyai": 0,
    "12306": 1,
    "amap": 2,
    "variflight": 3,
    "ego-browser": 4,
}


def _identity(offer: TravelOffer) -> tuple[object, ...] | None:
    identity = (
        offer.mode.casefold(),
        (offer.carrier or "").casefold(),
        (offer.service_number or "").casefold(),
        (offer.origin or "").casefold(),
        (offer.destination or "").casefold(),
        offer.departure_at.isoformat() if offer.departure_at else None,
    )
    if not all((offer.carrier, offer.service_number, offer.origin, offer.destination, offer.departure_at)):
        return None
    return identity


def _merge(primary: TravelOffer, secondary: TravelOffer) -> TravelOffer:
    values = primary.__dict__.copy()
    for key, value in secondary.__dict__.items():
        if key in {"provider", "sources"}:
            continue
        if values.get(key) is None and value is not None:
            values[key] = value
    values["sources"] = tuple(sorted({*primary.sources, *secondary.sources}))
    return replace(primary, **values)


def _provider_priority(offer: TravelOffer) -> tuple[int, str]:
    priorities = _PROVIDER_PRIORITY.copy()
    if offer.mode.casefold() == "train":
        priorities["12306"], priorities["flyai"] = priorities["flyai"], priorities["12306"]
    return (priorities.get(offer.provider.casefold(), 99), offer.provider.casefold())


def _primary(first: TravelOffer, second: TravelOffer) -> tuple[TravelOffer, TravelOffer]:
    first_key = _provider_priority(first)
    second_key = _provider_priority(second)
    return (first, second) if first_key <= second_key else (second, first)


def deduplicate_offers(offers: Iterable[TravelOffer]) -> list[TravelOffer]:
    merged: dict[tuple[object, ...], TravelOffer] = {}
    unmergeable: list[TravelOffer] = []
    for offer in offers:
        key = _identity(offer)
        if key is None:
            unmergeable.append(offer)
        elif key in merged:
            if merged[key].provider.casefold() == offer.provider.casefold():
                unmergeable.append(offer)
                continue
            primary, secondary = _primary(merged[key], offer)
            merged[key] = _merge(primary, secondary)
        else:
            merged[key] = offer
    return [*merged.values(), *unmergeable]


def _balanced_score(offer: TravelOffer) -> float:
    price = offer.effective_total_cny
    if price is None or offer.duration_minutes is None or offer.transfers is None:
        return inf
    return price + offer.duration_minutes * 0.35 + offer.transfers * 100


def rank_offers(offers: Iterable[TravelOffer], *, by: str = "balanced") -> list[TravelOffer]:
    values = list(offers)
    if by == "price":
        return sorted(values, key=lambda item: item.effective_total_cny if item.effective_total_cny is not None else inf)
    if by == "duration":
        return sorted(values, key=lambda item: item.duration_minutes if item.duration_minutes is not None else inf)
    if by == "balanced":
        return sorted(values, key=_balanced_score)
    raise ValueError("by must be one of: price, duration, balanced")
