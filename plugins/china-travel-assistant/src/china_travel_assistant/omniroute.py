from __future__ import annotations

from dataclasses import dataclass, replace
from math import inf
from typing import Iterable

from .contracts import (
    EvidenceStatus,
    ExplorationPolicy,
    ExplorationTier,
    GatewayCandidate,
    ItineraryCandidate,
    ItineraryLeg,
    PlaceEvidence,
    ProviderHealthRecord,
    RiskLevel,
    TravelRequest,
)


_RISK_ORDER = {
    RiskLevel.STABLE: 0,
    RiskLevel.MANAGED: 1,
    RiskLevel.CHALLENGE: 2,
}

_EVIDENCE_ORDER = {
    EvidenceStatus.VERIFIED: 0,
    EvidenceStatus.PARTIAL: 1,
    EvidenceStatus.HYPOTHESIS: 2,
}


@dataclass(frozen=True)
class SearchInstruction:
    instruction_id: str
    template: str
    capabilities: tuple[str, ...]
    purpose: str
    priority: int
    student_fare: bool
    date_offset_days: int = 0
    risk_level: RiskLevel = RiskLevel.STABLE

    def to_dict(self) -> dict[str, object]:
        return {
            "instruction_id": self.instruction_id,
            "template": self.template,
            "capabilities": list(self.capabilities),
            "purpose": self.purpose,
            "priority": self.priority,
            "student_fare": self.student_fare,
            "date_offset_days": self.date_offset_days,
            "risk_level": self.risk_level.value,
        }


def resolve_tier(request: TravelRequest) -> ExplorationTier:
    if request.exploration_tier is not ExplorationTier.AUTO:
        return request.exploration_tier
    if request.direct_only or request.risk_tolerance is RiskLevel.STABLE or request.arrival_deadline:
        return ExplorationTier.STANDARD
    return ExplorationTier.PRO


def policy_for(request: TravelRequest, tier: ExplorationTier | None = None) -> ExplorationPolicy:
    resolved = tier or resolve_tier(request)
    defaults = {
        ExplorationTier.STANDARD: (8, 0, 2, 120, 0, False, 0.1, RiskLevel.STABLE),
        ExplorationTier.PRO: (24, 2, 3, 350, 1, True, 0.45, RiskLevel.MANAGED),
        ExplorationTier.PRO_MAX: (60, 3, 4, 650, 2, True, 0.8, RiskLevel.CHALLENGE),
    }
    if resolved is ExplorationTier.AUTO:
        raise ValueError("policy tier must be resolved before use")
    hypotheses, self_transfers, modes, radius, flex, overnight, novelty, risk = defaults[resolved]
    if request.allow_overnight is not None:
        overnight = request.allow_overnight
    if request.risk_tolerance and _RISK_ORDER[request.risk_tolerance] < _RISK_ORDER[risk]:
        risk = request.risk_tolerance
    return ExplorationPolicy(
        tier=resolved,
        max_hypotheses=hypotheses,
        max_self_transfers=self_transfers,
        max_modes=modes,
        hub_radius_km=radius,
        date_flexibility_days=flex,
        allow_overnight=overnight,
        novelty_weight=novelty,
        risk_budget=risk,
    )


def build_search_plan(request: TravelRequest, policy: ExplorationPolicy) -> tuple[SearchInstruction, ...]:
    instructions = [
        SearchInstruction(
            instruction_id="baseline-direct",
            template="direct",
            capabilities=("flight", "train"),
            purpose="Establish the conventional direct baseline with complete costs and availability.",
            priority=0,
            student_fare=request.student_fare,
        ),
        SearchInstruction(
            instruction_id="baseline-gateway-scan",
            template="gateway_scan",
            capabilities=("poi", "flight", "train", "transfer"),
            purpose="Discover and compare reachable airports or rail gateways without hard-coding a city or relaxing constraints.",
            priority=1,
            student_fare=request.student_fare,
        ),
    ]
    if policy.tier in {ExplorationTier.PRO, ExplorationTier.PRO_MAX}:
        instructions.extend(
            (
                SearchInstruction(
                    instruction_id="creative-flight-train",
                    template="flight_train",
                    capabilities=("flight", "train", "transfer"),
                    purpose="Fly to a useful rail corridor hub, then continue by train.",
                    priority=2,
                    student_fare=request.student_fare,
                    risk_level=RiskLevel.MANAGED,
                ),
                SearchInstruction(
                    instruction_id="creative-train-flight",
                    template="train_flight",
                    capabilities=("train", "flight", "transfer"),
                    purpose="Reach a lower-fare surrounding airport by rail before flying.",
                    priority=2,
                    student_fare=request.student_fare,
                    risk_level=RiskLevel.MANAGED,
                ),
                SearchInstruction(
                    instruction_id="creative-split-rail",
                    template="split_rail",
                    capabilities=("train",),
                    purpose="Compare a split-ticket rail hub while preserving transfer buffers.",
                    priority=3,
                    student_fare=request.student_fare,
                    risk_level=RiskLevel.MANAGED,
                ),
            )
        )
    if policy.tier is ExplorationTier.PRO_MAX:
        instructions.extend(
            (
                SearchInstruction(
                    instruction_id="challenge-overnight",
                    template="overnight_multimodal",
                    capabilities=("flight", "train", "hotel", "transfer"),
                    purpose="Explore an overnight or early-morning connection with explicit sleep and fallback costs.",
                    priority=4,
                    student_fare=request.student_fare,
                    risk_level=RiskLevel.CHALLENGE,
                ),
                SearchInstruction(
                    instruction_id="challenge-corridor-hub",
                    template="corridor_hub",
                    capabilities=("poi", "flight", "train", "transfer"),
                    purpose="Search a wider cross-city corridor for combinations omitted by single-provider recommendations.",
                    priority=4,
                    student_fare=request.student_fare,
                    risk_level=RiskLevel.CHALLENGE,
                ),
            )
        )
        for offset in range(-policy.date_flexibility_days, policy.date_flexibility_days + 1):
            if offset:
                instructions.append(
                    SearchInstruction(
                        instruction_id=f"challenge-date-{offset:+d}",
                        template="date_shift",
                        capabilities=("flight", "train", "hotel", "transfer"),
                        purpose="Test a nearby departure date and include any required lodging cost.",
                        priority=5,
                        student_fare=request.student_fare,
                        date_offset_days=offset,
                        risk_level=RiskLevel.CHALLENGE,
                    )
                )
    return tuple(instructions)


def _gateway_score(candidate: GatewayCandidate) -> tuple[object, ...]:
    """Prefer complete facts; no missing value is converted into a guessed score."""

    total_cost = candidate.total_known_cost_cny
    total_duration = candidate.total_duration_minutes
    transfers = candidate.transfer_count
    return (
        total_cost is None,
        total_cost if total_cost is not None else inf,
        total_duration is None,
        total_duration if total_duration is not None else inf,
        transfers is None,
        transfers if transfers is not None else inf,
        _EVIDENCE_ORDER[candidate.evidence_status],
        candidate.name,
    )


def _gateway_reason(candidate: GatewayCandidate) -> str:
    total_cost = candidate.total_known_cost_cny
    duration = candidate.total_duration_minutes
    transfers = candidate.transfer_count
    facts = []
    if total_cost is None:
        facts.append("门到门总成本未返回，排在成本完整候选之后")
    else:
        facts.append(f"已知门到门成本 CNY {total_cost:.2f}")
    facts.append(f"总耗时 {duration} 分钟" if duration is not None else "总耗时未返回")
    facts.append(f"换乘 {transfers} 次" if transfers is not None else "换乘次数未返回")
    facts.append(f"证据 {candidate.evidence_status.value}")
    return "；".join(facts)


def rank_gateway_candidates(candidates: Iterable[GatewayCandidate]) -> tuple[GatewayCandidate, ...]:
    """Rank arbitrary transport gateways using only explicitly known values."""

    ordered = sorted(candidates, key=_gateway_score)
    return tuple(
        replace(candidate, rank=index, ranking_reason=_gateway_reason(candidate))
        for index, candidate in enumerate(ordered, 1)
    )


def _place_is_closed(place: PlaceEvidence) -> bool:
    status = (place.opening_status or "").casefold()
    return any(token in status for token in ("closed", "close", "关闭", "闭园", "暂停"))


def _place_score(place: PlaceEvidence) -> tuple[object, ...]:
    weather = place.weather_risk
    weather_risk = _RISK_ORDER[weather.risk_level] if weather else _RISK_ORDER[RiskLevel.MANAGED]
    durations = [item.total_duration_minutes for item in place.access_options]
    best_duration = min((item for item in durations if item is not None), default=inf)
    return (
        _place_is_closed(place),
        weather is None,
        weather_risk,
        best_duration == inf,
        best_duration,
        _EVIDENCE_ORDER[place.evidence_status],
        place.name,
    )


def _place_reason(place: PlaceEvidence) -> str:
    weather = place.weather_risk
    if _place_is_closed(place):
        return "官方开放状态显示不可用，保留为事实记录但不作为推荐。"
    if weather is None:
        weather_summary = "天气未返回"
    else:
        weather_summary = f"户外风险 {weather.risk_level.value}"
    duration = min(
        (item.total_duration_minutes for item in place.access_options if item.total_duration_minutes is not None),
        default=None,
    )
    access_summary = f"最快已知接驳 {duration} 分钟" if duration is not None else "接驳时长未返回"
    return f"{weather_summary}；{access_summary}；证据 {place.evidence_status.value}"


def rank_place_evidence(places: Iterable[PlaceEvidence]) -> tuple[PlaceEvidence, ...]:
    ordered = sorted(places, key=_place_score)
    return tuple(
        replace(place, rank=index, ranking_reason=_place_reason(place))
        for index, place in enumerate(ordered, 1)
    )


def _endpoint(value: str) -> str:
    return "".join(value.casefold().split())


def _minimum_connection_minutes(previous: ItineraryLeg, following: ItineraryLeg) -> int:
    if previous.mode.casefold() == "flight" or following.mode.casefold() == "flight":
        return 150 if previous.self_transfer or following.self_transfer else 120
    if previous.mode.casefold() == "train" and following.mode.casefold() == "train":
        return 45
    return 30


def _connection_is_valid(previous: ItineraryLeg, following: ItineraryLeg) -> bool:
    if _endpoint(previous.destination) != _endpoint(following.origin):
        return False
    if previous.arrival_at and following.departure_at:
        connection = int((following.departure_at - previous.arrival_at).total_seconds() // 60)
        required = max(
            _minimum_connection_minutes(previous, following),
            previous.buffer_minutes,
            following.buffer_minutes,
        )
        return connection >= required
    return True


def _path_risk(path: tuple[ItineraryLeg, ...]) -> RiskLevel:
    self_transfers = sum(leg.self_transfer for leg in path)
    has_overnight = any(
        previous.arrival_at
        and following.departure_at
        and following.departure_at.date() > previous.arrival_at.date()
        for previous, following in zip(path, path[1:])
    )
    if has_overnight or self_transfers > 1 or len(path) > 3:
        return RiskLevel.CHALLENGE
    if self_transfers or len(path) > 2:
        return RiskLevel.MANAGED
    return RiskLevel.STABLE


def _path_evidence(path: tuple[ItineraryLeg, ...]) -> EvidenceStatus:
    return max((leg.evidence_status for leg in path), key=_EVIDENCE_ORDER.__getitem__)


def _path_is_overnight(path: tuple[ItineraryLeg, ...]) -> bool:
    return any(
        previous.arrival_at
        and following.departure_at
        and following.departure_at.date() > previous.arrival_at.date()
        for previous, following in zip(path, path[1:])
    )


def _known_total(path: tuple[ItineraryLeg, ...]) -> float | None:
    prices = [leg.total_price_cny for leg in path]
    return sum(prices) if all(price is not None for price in prices) else None


def _known_duration(path: tuple[ItineraryLeg, ...]) -> int | None:
    if path[0].departure_at and path[-1].arrival_at:
        return int((path[-1].arrival_at - path[0].departure_at).total_seconds() // 60)
    durations = [leg.duration_minutes for leg in path]
    if all(duration is not None for duration in durations):
        return sum(durations) + sum(leg.buffer_minutes for leg in path)
    return None


def _novelty_reason(path: tuple[ItineraryLeg, ...]) -> str | None:
    modes = tuple(dict.fromkeys(leg.mode.casefold() for leg in path))
    if len(modes) > 1:
        return "Combines multiple transport modes outside a single-provider recommendation."
    if len(path) > 1:
        return "Uses a split itinerary through an intermediate hub."
    return None


def _candidate_from_path(index: int, path: tuple[ItineraryLeg, ...], tier: ExplorationTier) -> ItineraryCandidate:
    total = _known_total(path)
    duration = _known_duration(path)
    unknowns = []
    if total is None:
        unknowns.append("total_price_cny")
    if duration is None:
        unknowns.append("total_duration_minutes")
    risk = _path_risk(path)
    mode_label = "+".join(leg.mode for leg in path)
    return ItineraryCandidate(
        itinerary_id=f"route-{index:03d}",
        title=f"{mode_label}: {path[0].origin} -> {path[-1].destination}",
        tier=tier,
        legs=path,
        total_price_cny=total,
        total_duration_minutes=duration,
        transfer_count=max(0, len(path) - 1),
        risk_level=risk,
        evidence_status=_path_evidence(path),
        novelty_reason=_novelty_reason(path),
        burden_summary=(
            "Requires self-transfer or an unprotected split ticket."
            if any(leg.self_transfer for leg in path)
            else "Adds intermediate legs compared with a direct journey."
            if len(path) > 1
            else None
        ),
        delay_fallback=(
            "Recheck the next independently booked leg and the last same-day alternative after any delay."
            if any(leg.self_transfer for leg in path)
            else "Use the carrier or railway's protected rebooking process when applicable."
        ),
        unknown_fields=tuple(unknowns),
    )


def _candidate_score(candidate: ItineraryCandidate, novelty_weight: float) -> float:
    risk_penalty = _RISK_ORDER[candidate.risk_level] * 300
    evidence_penalty = _EVIDENCE_ORDER[candidate.evidence_status] * 500
    price = candidate.total_price_cny if candidate.total_price_cny is not None else inf
    duration = candidate.total_duration_minutes if candidate.total_duration_minutes is not None else inf
    novelty_bonus = 100 * novelty_weight if candidate.novelty_reason else 0
    if price == inf or duration == inf:
        return inf
    return price + duration * 0.35 + candidate.transfer_count * 100 + risk_penalty + evidence_penalty - novelty_bonus


def _with_comparison(candidate: ItineraryCandidate, baseline: ItineraryCandidate) -> ItineraryCandidate:
    benefit = candidate.benefit_summary
    if candidate.total_price_cny is not None and baseline.total_price_cny is not None:
        delta = candidate.total_price_cny - baseline.total_price_cny
        benefit = f"CNY {abs(delta):.2f} {'more' if delta > 0 else 'less'} than the stable baseline."
    return replace(candidate, benefit_summary=benefit)


def compose_itineraries(
    request: TravelRequest,
    legs: Iterable[ItineraryLeg],
    policy: ExplorationPolicy,
) -> tuple[ItineraryCandidate, ...]:
    values = tuple(legs)
    adjacency: dict[str, list[ItineraryLeg]] = {}
    for leg in values:
        adjacency.setdefault(_endpoint(leg.origin), []).append(leg)

    paths: list[tuple[ItineraryLeg, ...]] = []

    def walk(current: str, path: tuple[ItineraryLeg, ...], visited_locations: frozenset[str]) -> None:
        if len(paths) >= policy.max_hypotheses:
            return
        if path and _endpoint(path[-1].destination) == _endpoint(request.destination):
            paths.append(path)
            return
        if len(path) >= policy.max_modes:
            return
        for leg in adjacency.get(_endpoint(current), ()):
            next_location = _endpoint(leg.destination)
            if next_location in visited_locations:
                continue
            if path and not _connection_is_valid(path[-1], leg):
                continue
            walk(leg.destination, (*path, leg), visited_locations | {next_location})

    walk(request.origin, tuple(), frozenset({_endpoint(request.origin)}))

    candidates = []
    for index, path in enumerate(paths, 1):
        candidate = _candidate_from_path(index, path, policy.tier)
        if request.direct_only and candidate.transfer_count:
            continue
        if sum(leg.self_transfer for leg in path) > policy.max_self_transfers:
            continue
        if _RISK_ORDER[candidate.risk_level] > _RISK_ORDER[policy.risk_budget]:
            continue
        if _path_is_overnight(path) and not policy.allow_overnight:
            continue
        if request.arrival_deadline and path[-1].arrival_at and path[-1].arrival_at > request.arrival_deadline:
            continue
        candidates.append(candidate)

    if not candidates:
        return tuple()
    baseline = min(
        candidates,
        key=lambda item: (
            _RISK_ORDER[item.risk_level],
            item.transfer_count if item.transfer_count is not None else inf,
            _candidate_score(item, 0),
        ),
    )
    baseline = replace(baseline, is_baseline=True, novelty_reason=None)
    compared = [baseline]
    compared.extend(
        _with_comparison(item, baseline)
        for item in candidates
        if item.itinerary_id != baseline.itinerary_id
    )
    return tuple(
        sorted(
            compared,
            key=lambda item: (not item.is_baseline, _candidate_score(item, policy.novelty_weight)),
        )
    )


def plan_trip(
    request: TravelRequest,
    legs: Iterable[ItineraryLeg] = (),
    *,
    gateway_candidates: Iterable[GatewayCandidate] = (),
    place_evidence: Iterable[PlaceEvidence] = (),
    provider_health: Iterable[ProviderHealthRecord] = (),
) -> dict[str, object]:
    policy = policy_for(request)
    search_plan = build_search_plan(request, policy)
    itineraries = compose_itineraries(request, legs, policy)
    gateways = rank_gateway_candidates(gateway_candidates)
    places = rank_place_evidence(place_evidence)
    return {
        "request": request.to_dict(),
        "resolved_tier": policy.tier.value,
        "policy": policy.to_dict(),
        "search_plan": [instruction.to_dict() for instruction in search_plan],
        "itineraries": [candidate.to_dict() for candidate in itineraries],
        "gateway_candidates": [candidate.to_dict() for candidate in gateways],
        "place_evidence": [place.to_dict() for place in places],
        "provider_health": [record.to_dict() for record in provider_health],
    }
