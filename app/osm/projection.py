"""Local metric projection for small map areas (Moscow-scale)."""

from __future__ import annotations

import math

# WGS84 approximations at mid-latitudes (meters per degree)
M_PER_DEG_LAT = 110_540.0


def meters_per_deg_lon(lat_deg: float) -> float:
    return 111_320.0 * math.cos(math.radians(lat_deg))


def latlon_to_local(lat: float, lon: float, origin_lat: float, origin_lon: float) -> tuple[float, float]:
    """Convert WGS84 to local meters with origin at SW corner of selection."""
    x = (lon - origin_lon) * meters_per_deg_lon(origin_lat)
    y = (lat - origin_lat) * M_PER_DEG_LAT
    return x, y


def bbox_size_meters(south: float, west: float, north: float, east: float) -> tuple[float, float]:
    origin_lat, origin_lon = south, west
    w, _ = latlon_to_local(south, east, origin_lat, origin_lon)
    _, h = latlon_to_local(north, west, origin_lat, origin_lon)
    return abs(w), abs(h)
