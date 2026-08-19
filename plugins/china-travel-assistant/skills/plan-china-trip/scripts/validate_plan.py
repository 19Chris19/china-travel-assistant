#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from china_travel_assistant.contracts import TransferLeg, TravelOffer, TravelRequest


def validate(payload: object) -> dict[str, object]:
    if not isinstance(payload, dict):
        raise ValueError("plan must be a JSON object")
    request_value = payload.get("request")
    offers_value = payload.get("offers", [])
    transfers_value = payload.get("transfers", [])
    if not isinstance(request_value, dict):
        raise ValueError("request must be a JSON object")
    if not isinstance(offers_value, list) or not all(isinstance(item, dict) for item in offers_value):
        raise ValueError("offers must be an array of objects")
    if not isinstance(transfers_value, list) or not all(isinstance(item, dict) for item in transfers_value):
        raise ValueError("transfers must be an array of objects")

    request = TravelRequest.from_mapping(request_value)
    offers = [TravelOffer.from_mapping(item) for item in offers_value]
    transfers = [TransferLeg.from_mapping(item) for item in transfers_value]
    known_prices = [item.effective_total_cny for item in offers]
    known_prices.extend(item.cost_cny for item in transfers)
    known_total = sum(value for value in known_prices if value is not None)
    unknown_price_items = sum(value is None for value in known_prices)
    return {
        "status": "valid",
        "request": request.to_dict(),
        "known_total_cny": known_total,
        "unknown_price_items": unknown_price_items,
        "offer_count": len(offers),
        "transfer_count": len(transfers),
    }


def main(argv: list[str] | None = None) -> int:
    args = argv or sys.argv[1:]
    if len(args) != 1:
        print("usage: validate_plan.py PLAN.json", file=sys.stderr)
        return 2
    try:
        payload = json.loads(Path(args[0]).read_text(encoding="utf-8"))
        print(json.dumps(validate(payload), ensure_ascii=False, sort_keys=True))
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        print(f"invalid plan: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
