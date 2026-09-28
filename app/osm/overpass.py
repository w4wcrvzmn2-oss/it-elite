"""Fetch OpenStreetMap features for a bounding box."""

from __future__ import annotations

import logging
import re
import time
import xml.etree.ElementTree as ET
from typing import Any

import httpx

logger = logging.getLogger(__name__)

# Small areas fit the official map API. Overpass is only a fallback: public
# instances often answer 504, and each attempt used to block the request.
OSM_MAP_URL = "https://api.openstreetmap.org/api/0.6/map"
OVERPASS_ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
]

# Footways and paths turn a courtyard into a web of buffers. Keep carriageways.
_HIGHWAY_RE = re.compile(
    r"^(tertiary|secondary|primary|residential|service|unclassified|living_street)$"
)

# Preview and analyze hit the same bbox seconds apart. Reuse a successful reply
# so a busy Overpass server does not fail the calculation that just previewed.
_CACHE_TTL_S = 600.0
_cache: dict[tuple[float, float, float, float], tuple[float, dict[str, Any]]] = {}

HEADERS = {
    "User-Agent": "GreenPlanner/0.1 (urban planting demo; contact: local)",
    "Accept": "application/json",
}


def parse_osm_map_xml(content: bytes) -> dict[str, Any]:
    """Turn an OSM map extract into building and road ways with lat/lon geometry."""
    root = ET.fromstring(content)
    nodes: dict[str, tuple[float, float]] = {}
    for node in root.findall("node"):
        node_id = node.get("id")
        if node_id is None:
            continue
        nodes[node_id] = (float(node.get("lat") or 0), float(node.get("lon") or 0))

    buildings: list[dict[str, Any]] = []
    roads: list[dict[str, Any]] = []
    ways: dict[str, dict[str, Any]] = {}
    for way in root.findall("way"):
        way_id = way.get("id") or ""
        tags = {tag.get("k"): tag.get("v") for tag in way.findall("tag")}
        geometry = []
        for nd in way.findall("nd"):
            coords = nodes.get(nd.get("ref") or "")
            if coords is None:
                continue
            geometry.append({"lat": coords[0], "lon": coords[1]})
        if len(geometry) < 2:
            continue
        element = {"tags": tags, "geometry": geometry}
        ways[way_id] = element
        if tags.get("building"):
            buildings.append(element)
        highway = tags.get("highway") or ""
        if _HIGHWAY_RE.match(highway):
            roads.append(element)

    # Many Moscow buildings are multipolygon relations, not tagged ways.
    for rel in root.findall("relation"):
        tags = {tag.get("k"): tag.get("v") for tag in rel.findall("tag")}
        if not tags.get("building"):
            continue
        for member in rel.findall("member"):
            if member.get("type") != "way" or member.get("role") not in ("outer", ""):
                continue
            way = ways.get(member.get("ref") or "")
            if way is None or way.get("tags", {}).get("building"):
                continue
            buildings.append({"tags": tags, "geometry": way["geometry"]})

    return {"buildings": buildings, "roads": roads, "raw_count": len(buildings) + len(roads)}


def _fetch_osm_map(south: float, west: float, north: float, east: float) -> dict[str, Any]:
    url = f"{OSM_MAP_URL}?bbox={west},{south},{east},{north}"
    headers = {
        "User-Agent": HEADERS["User-Agent"],
        "Accept": "application/xml,text/xml,*/*",
    }
    logger.info("OSM map request bbox=%s,%s,%s,%s", south, west, north, east)
    with httpx.Client(timeout=20.0, headers=headers) as client:
        resp = client.get(url)
    if resp.status_code != 200:
        raise RuntimeError(f"OSM map HTTP {resp.status_code}")
    return parse_osm_map_xml(resp.content)


def _query(south: float, west: float, north: float, east: float) -> str:
    return f"""
    [out:json][timeout:25];
    (
      way["building"]({south},{west},{north},{east});
      way["highway"~"^(tertiary|secondary|primary|residential|service|unclassified|living_street)$"]({south},{west},{north},{east});
    );
    out geom;
    """


def _cache_key(south: float, west: float, north: float, east: float) -> tuple[float, float, float, float]:
    return (round(south, 5), round(west, 5), round(north, 5), round(east, 5))


def fetch_osm_features(south: float, west: float, north: float, east: float) -> dict[str, Any]:
    """Query buildings and roads inside bbox. Tries several Overpass servers."""
    key = _cache_key(south, west, north, east)
    cached = _cache.get(key)
    if cached and time.time() - cached[0] < _CACHE_TTL_S:
        logger.info("Overpass cache hit bbox=%s", key)
        return cached[1]

    errors: list[str] = []
    try:
        result = _fetch_osm_map(south, west, north, east)
        _cache[key] = (time.time(), result)
        return result
    except Exception as e:
        errors.append(str(e))
        logger.warning("OSM map failed: %s", e)

    query = _query(south, west, north, east)
    for url in OVERPASS_ENDPOINTS:
        try:
            logger.info("Overpass request %s bbox=%s,%s,%s,%s", url, south, west, north, east)
            with httpx.Client(timeout=12.0, headers=HEADERS) as client:
                resp = client.post(url, data={"data": query})
            if resp.status_code == 200:
                data = resp.json()
                elements = data.get("elements", [])
                buildings = [e for e in elements if e.get("tags", {}).get("building")]
                roads = [e for e in elements if e.get("tags", {}).get("highway")]
                result = {"buildings": buildings, "roads": roads, "raw_count": len(elements)}
                _cache[key] = (time.time(), result)
                return result
            errors.append(f"{url}: HTTP {resp.status_code}")
        except Exception as e:
            errors.append(f"{url}: {e}")
            logger.warning("Overpass failed %s: %s", url, e)

    raise RuntimeError("; ".join(errors) or "нет ответа от серверов")
