from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from dataclasses import replace

from .amap import AmapClient
from .credential_store import profile_status, reenter_with_profile, run_with_profile
from .contracts import (
    ExplorationTier,
    GatewayCandidate,
    ItineraryLeg,
    PlaceEvidence,
    PresentationMode,
    ProviderHealthRecord,
    TravelOffer,
    TravelRequest,
    TIER_ALIASES,
    parse_tier,
)
from .doctor import Doctor, ProviderProbeError, probe_amap, probe_variflight
from .offers import deduplicate_offers, rank_offers
from .omniroute import plan_trip
from .presentation import render_plan
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
    route.add_argument("capability", choices=("flight", "train", "hotel", "transfer", "poi", "map", "weather"))
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

    flyai = subparsers.add_parser("flyai", help="run the pinned FlyAI CLI with unified credentials")
    flyai.add_argument("args", nargs=argparse.REMAINDER)

    plan = subparsers.add_parser("plan", help="build a route exploration plan and compose supplied itinerary legs")
    plan.add_argument("json", nargs="?")
    plan.add_argument("--tier", choices=(*tuple(item.value for item in ExplorationTier), *TIER_ALIASES))
    plan.add_argument("--presentation", choices=tuple(item.value for item in PresentationMode), default="auto")

    render = subparsers.add_parser("render-plan", help="render itinerary JSON as exact local HTML, SVG, or Markdown")
    render.add_argument("json", nargs="?")
    render.add_argument(
        "--format",
        choices=("auto", "html", "svg", "markdown"),
        default="auto",
        dest="presentation_format",
    )
    render.add_argument("--output")
    probe = subparsers.add_parser("_probe-provider", help=argparse.SUPPRESS)
    probe.add_argument("provider", choices=("amap", "variflight"))
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
            if not os.environ.get("AMAP_WEBSERVICE_KEY"):
                return reenter_with_profile("amap", ["amap-search", args.keywords, "--city", args.city])
            client = AmapClient(api_key=os.environ["AMAP_WEBSERVICE_KEY"])
            print(json.dumps(client.text_search(args.keywords, city=args.city), ensure_ascii=False))
        elif args.command == "amap-route":
            if not os.environ.get("AMAP_WEBSERVICE_KEY"):
                command = ["amap-route", args.mode, "--origin", ",".join(map(str, args.origin)),
                           "--destination", ",".join(map(str, args.destination))]
                if args.city:
                    command.extend(("--city", args.city))
                if args.destination_city:
                    command.extend(("--destination-city", args.destination_city))
                return reenter_with_profile("amap", command)
            result = AmapClient(api_key=os.environ["AMAP_WEBSERVICE_KEY"]).route(
                args.origin,
                args.destination,
                mode=args.mode,
                city=args.city,
                destination_city=args.destination_city,
            )
            print(json.dumps(result, ensure_ascii=False))
        elif args.command == "flyai":
            if not args.args:
                raise ValueError("flyai requires a FlyAI subcommand")
            if not shutil.which("flyai"):
                raise RuntimeError("flyai binary is not available")
            environment = os.environ.copy()
            for key in (
                "AMAP_WEBSERVICE_KEY",
                "AMAP_JSAPI_KEY",
                "AMAP_SECURITY_CODE",
                "FLYAI_API_KEY",
                "VARIFLIGHT_API_KEY",
                "QWEATHER_API_HOST",
                "QWEATHER_KEY_ID",
                "QWEATHER_DEVELOPER_ID",
                "QWEATHER_PROJECT_ID",
                "QWEATHER_PRIVATE_KEY_PATH",
                "VIGOLIVE_API_KEY",
            ):
                environment.pop(key, None)
            flyai_key = os.environ.get("FLYAI_API_KEY")
            if flyai_key:
                environment["FLYAI_API_KEY"] = flyai_key
            elif profile_status("flyai") == "ready":
                return run_with_profile("flyai", ["flyai", *args.args])
            return subprocess.run(["flyai", *args.args], env=environment, check=False).returncode
        elif args.command == "_probe-provider":
            try:
                if args.provider == "amap":
                    probe_amap(os.environ.get("AMAP_WEBSERVICE_KEY"))
                else:
                    probe_variflight(os.environ.get("VARIFLIGHT_API_KEY"))
            except ProviderProbeError as exc:
                return {"expired": 3, "forbidden": 4, "rate_limited": 5}.get(exc.health.value, 2)
        elif args.command == "plan":
            payload = _read_json(args.json)
            if not isinstance(payload, dict):
                raise ValueError("plan expects a JSON object")
            request_payload = payload.get("request", payload)
            if not isinstance(request_payload, dict):
                raise ValueError("plan request must be a JSON object")
            request = TravelRequest.from_mapping(request_payload)
            if args.tier:
                request = replace(request, exploration_tier=parse_tier(args.tier))
            raw_legs = payload.get("legs", [])
            if not isinstance(raw_legs, list):
                raise ValueError("plan legs must be a JSON array")
            legs = []
            for index, item in enumerate(raw_legs):
                if not isinstance(item, dict):
                    raise ValueError(f"plan leg {index} must be a JSON object")
                legs.append(ItineraryLeg.from_mapping(item))
            def contract_list(key, factory):
                values = payload.get(key, [])
                if not isinstance(values, list):
                    raise ValueError(f"plan {key} must be a JSON array")
                result = []
                for index, item in enumerate(values):
                    if not isinstance(item, dict):
                        raise ValueError(f"plan {key} {index} must be a JSON object")
                    result.append(factory.from_mapping(item))
                return result

            result = plan_trip(
                request,
                legs,
                gateway_candidates=contract_list("gateway_candidates", GatewayCandidate),
                place_evidence=contract_list("place_evidence", PlaceEvidence),
                provider_health=contract_list("provider_health", ProviderHealthRecord),
            )
            result["presentation_requested"] = args.presentation
            print(json.dumps(result, ensure_ascii=False))
        elif args.command == "render-plan":
            payload = _read_json(args.json)
            if not isinstance(payload, dict):
                raise ValueError("render-plan expects a JSON object")
            mode, rendered = render_plan(payload, PresentationMode(args.presentation_format))
            if args.output:
                with open(args.output, "w", encoding="utf-8") as output:
                    output.write(rendered)
                print(json.dumps({"format": mode.value, "output": args.output}, ensure_ascii=False))
            else:
                print(rendered, end="")
    except (TypeError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
