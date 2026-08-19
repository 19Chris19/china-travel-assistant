from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .contracts import ProviderHealth


class ProviderAction(str, Enum):
    SEARCH = "search"
    ENRICH = "enrich"
    VERIFY = "verify"


@dataclass(frozen=True)
class ProviderStep:
    provider: str
    action: ProviderAction
    required: bool
    reason: str


def build_provider_plan(
    capability: str,
    *,
    verify_status: bool = False,
    verify_web: bool = False,
    include_booking_link: bool = False,
) -> list[ProviderStep]:
    capability = capability.casefold()
    if capability == "flight":
        plan = [ProviderStep("flyai", ProviderAction.SEARCH, True, "primary searchable offers")]
        if verify_status:
            plan.append(ProviderStep("variflight", ProviderAction.ENRICH, False, "status and schedule verification"))
    elif capability == "train":
        plan = [ProviderStep("12306", ProviderAction.SEARCH, True, "official public rail query")]
        if include_booking_link:
            plan.append(ProviderStep("flyai", ProviderAction.ENRICH, False, "booking link enrichment"))
    elif capability == "hotel":
        plan = [ProviderStep("flyai", ProviderAction.SEARCH, True, "primary hotel search")]
    elif capability in {"transfer", "poi", "map"}:
        plan = [ProviderStep("amap", ProviderAction.SEARCH, True, "official map and routing data")]
    else:
        raise ValueError(f"unsupported capability: {capability}")
    if verify_web:
        plan.append(ProviderStep("ego-browser", ProviderAction.VERIFY, False, "login-aware page verification"))
    return plan


def classify_provider_error(status_code: int | None) -> ProviderHealth:
    if status_code == 401:
        return ProviderHealth.EXPIRED
    if status_code == 403:
        return ProviderHealth.FORBIDDEN
    if status_code == 429:
        return ProviderHealth.RATE_LIMITED
    return ProviderHealth.DEGRADED
