#!/usr/bin/env python3
"""LOCATRIX-AI: GNSS-independent pedestrian dead-reckoning simulation."""
from __future__ import annotations
import argparse
import base64
import json
import math
import zlib
from dataclasses import dataclass, asdict
from typing import Any

EARTH_RADIUS_M = 6_371_000.0

def wrap_angle(degrees: float) -> float:
    return degrees % 360.0

def circular_blend(a_deg: float, b_deg: float, weight_a: float = 0.65) -> float:
    """Blend headings without the 359°/1° discontinuity."""
    if not 0 <= weight_a <= 1:
        raise ValueError("weight_a must be between 0 and 1")
    a, b = math.radians(a_deg), math.radians(b_deg)
    x = weight_a * math.cos(a) + (1 - weight_a) * math.cos(b)
    y = weight_a * math.sin(a) + (1 - weight_a) * math.sin(b)
    if abs(x) + abs(y) < 1e-12:
        return wrap_angle(a_deg)
    return wrap_angle(math.degrees(math.atan2(y, x)))

@dataclass
class Position:
    latitude: float
    longitude: float
    heading_deg: float
    steps: int
    distance_m: float
    uncertainty_m: float

class PositionEstimator:
    def __init__(self, latitude: float, longitude: float, heading_deg: float = 0.0,
                 initial_uncertainty_m: float = 1.0):
        if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
            raise ValueError("invalid starting coordinates")
        self.position = Position(latitude, longitude, wrap_angle(heading_deg), 0, 0.0,
                                 max(0.0, initial_uncertainty_m))

    def step(self, stride_m: float, compass_heading_deg: float,
             gyro_delta_deg: float = 0.0) -> Position:
        if stride_m <= 0 or stride_m > 3:
            raise ValueError("stride_m must be in (0, 3]")
        if not math.isfinite(compass_heading_deg) or not math.isfinite(gyro_delta_deg):
            raise ValueError("heading values must be finite")
        predicted = wrap_angle(self.position.heading_deg + gyro_delta_deg)
        heading = circular_blend(predicted, compass_heading_deg, 0.65)
        distance = stride_m
        bearing = math.radians(heading)
        lat1 = math.radians(self.position.latitude)
        lon1 = math.radians(self.position.longitude)
        angular = distance / EARTH_RADIUS_M
        lat2 = math.asin(math.sin(lat1) * math.cos(angular) +
                         math.cos(lat1) * math.sin(angular) * math.cos(bearing))
        lon2 = lon1 + math.atan2(math.sin(bearing) * math.sin(angular) * math.cos(lat1),
                                 math.cos(angular) - math.sin(lat1) * math.sin(lat2))
        self.position = Position(
            math.degrees(lat2), (math.degrees(lon2) + 540) % 360 - 180,
            heading, self.position.steps + 1, self.position.distance_m + distance,
            self.position.uncertainty_m + 0.04 + distance * 0.025
        )
        return self.position

    def snapshot(self) -> dict[str, Any]:
        return asdict(self.position)

def encode_packet(position: dict[str, Any]) -> dict[str, str]:
    raw = json.dumps(position, sort_keys=True, separators=(",", ":")).encode("utf-8")
    payload = base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")
    return {"payload": payload, "crc32": f"{zlib.crc32(raw) & 0xffffffff:08x}"}

def decode_packet(packet: dict[str, str]) -> dict[str, Any]:
    if "payload" not in packet or "crc32" not in packet:
        raise ValueError("packet must contain payload and crc32")
    encoded = packet["payload"]
    raw = base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4))
    expected = f"{zlib.crc32(raw) & 0xffffffff:08x}"
    if expected.lower() != packet["crc32"].lower():
        raise ValueError("packet checksum mismatch")
    value = json.loads(raw.decode("utf-8"))
    if not isinstance(value, dict):
        raise ValueError("packet payload must decode to an object")
    return value

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="LOCATRIX offline dead-reckoning demo")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("simulate")
    p.add_argument("--start-lat", type=float, required=True)
    p.add_argument("--start-lon", type=float, required=True)
    p.add_argument("--steps", type=int, default=10)
    p.add_argument("--heading", type=float, default=0.0, help="compass bearing, degrees clockwise from north")
    p.add_argument("--stride", type=float, default=0.72, help="estimated step length in metres")
    p.add_argument("--gyro-delta", type=float, default=0.0, help="gyro-predicted heading change per step")
    p = sub.add_parser("encode")
    p.add_argument("--lat", type=float, required=True); p.add_argument("--lon", type=float, required=True)
    p.add_argument("--steps", type=int, default=0)
    p.add_argument("--uncertainty", type=float, default=1.0)
    p = sub.add_parser("decode"); p.add_argument("packet_json", help="JSON object with payload and crc32")
    args = parser.parse_args(argv)
    if args.command == "simulate":
        if args.steps < 0 or args.steps > 100000:
            parser.error("--steps must be between 0 and 100000")
        estimator = PositionEstimator(args.start_lat, args.start_lon)
        for _ in range(args.steps):
            estimator.step(args.stride, args.heading, args.gyro_delta)
        result = estimator.snapshot()
        print(json.dumps(result, indent=2))
        print("relay_packet=" + json.dumps(encode_packet(result), separators=(",", ":")))
    elif args.command == "encode":
        if args.steps < 0 or args.uncertainty < 0:
            parser.error("--steps and --uncertainty must be non-negative")
        value = {"latitude": args.lat, "longitude": args.lon, "steps": args.steps,
                 "uncertainty_m": args.uncertainty}
        print(json.dumps(encode_packet(value), indent=2))
    else:
        print(json.dumps(decode_packet(json.loads(args.packet_json)), indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
