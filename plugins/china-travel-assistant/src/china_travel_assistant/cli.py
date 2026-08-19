from __future__ import annotations

import argparse
import json
import sys

from .amap import AmapClient
from .contracts import TravelOffer, TravelRequest
from .doctor import Doctor
from .offers import deduplicate_offers, rank_offers
from .providers import build_provider_plan


def _read_json(value: str | None) -> object:
    if value:
        return json.loads(value)
    return json.load(sys.stdin)


def _coordinate(value: str) -> tuple[float, float]:
    parts = value.split(",")
    if len(parts) != 2:
        raise argparse.ArgumentTypeError("coordinate must be longitude,latitude")
    try:
        return float(parts[0]), float(parts[1])
    except ValueError as exc:
        raise argparse.ArgumentTypeError("coordinate must contain numbers") from exc


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="travel-assistant")
    subparsers = parser.add_subparsers(dest="command", required=True)

    doctor = subparsers.add_parser("doctor", help="report provider configuration without exposing secrets")
    doctor.add_argument("--live", action="store_true", help="run explicitly configured live probes")

    request = subparsers.add_parser("normalize-request", help="normalize a TravelRequest JSON object")
    request.add_argument("json", nargs="?")

    offers = subparsers.add_parser("rank-offers", help="deduplicate and rank TravelOffer JSON objects")
    offers.add_argument("json", nargs="?")
    offers.add_argument("--by", choices=("price", "duration", "balanced"), default="balanced")

    route = subparsers.add_parser("provider-plan", help="show the deterministic provider route")
    route.add_argument("capability", choices=("flight", "train", "hotel", "transfer", "poi", "map"))
    route.add_argument("--verify-status", action="store_true")
    route.add_argument("--verify-web", action="store_true")
    route.add_argument("--include-booking-link", action="store_true")

    amap = subparsers.add_parser("amap-search", help="search AMap POIs with the configured Web Service key")
    amap.add_argument("keywords")
    amap.add_argument("--city", required=True)

    amap_route = subparsers.add_parser("amap-route", help="plan an AMap walking, transit, driving, or taxi route")
    amap_route.add_argument("mode", choices=("walking", "transit", "driving", "taxi"))
    amap_route.add_argument("--origin", type=_coordinate, required=True)
    amap_route.add_argument("--destination", type=_coordinate, required=True)
    amap_route.add_argument("--city")
    amap_route.add_argument("--destination-city")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "doctor":
            Doctor(live=args.live).run()
        elif args.command == "normalize-request":
            payload = _read_json(args.json)
            if not isinstance(payload, dict):
                raise ValueError("normalize-request expects a JSON object")
            print(json.dumps(TravelRequest.from_mapping(payload).to_dict(), ensure_ascii=False))
        elif args.command == "rank-offers":
            payload = _read_json(args.json)
            if not isinstance(payload, list):
                raise ValueError("rank-offers expects a JSON array")
            offers = []
            for index, item in enumerate(payload):
                if not isinstance(item, dict):
                    raise ValueError(f"offer {index} must be a JSON object")
                offers.append(TravelOffer.from_mapping(item))
            ranked = rank_offers(deduplicate_offers(offers), by=args.by)
            print(json.dumps([item.to_dict() for item in ranked], ensure_ascii=False))
        elif args.command == "provider-plan":
            plan = build_provider_plan(
                args.capability,
                verify_status=args.verify_status,
                verify_web=args.verify_web,
                include_booking_link=args.include_booking_link,
            )
            print(json.dumps([item.__dict__ for item in plan], ensure_ascii=False, default=str))
        elif args.command == "amap-search":
            print(json.dumps(AmapClient().text_search(args.keywords, city=args.city), ensure_ascii=False))
        elif args.command == "amap-route":
            result = AmapClient().route(
                args.origin,
                args.destination,
                mode=args.mode,
                city=args.city,
                destination_city=args.destination_city,
            )
            print(json.dumps(result, ensure_ascii=False))
    except (TypeError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
