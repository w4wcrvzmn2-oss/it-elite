"""OSM map area integration tests."""

from __future__ import annotations

from app.osm.overpass import parse_osm_map_xml
from app.osm.projection import bbox_size_meters, latlon_to_local
from app.osm.to_dxf import generate_dxf_from_osm


def test_latlon_to_local_origin():
    x, y = latlon_to_local(55.756, 37.618, 55.755, 37.617)
    assert x > 0
    assert y > 0
    assert x < 200
    assert y < 200


def test_bbox_size_meters():
    w, h = bbox_size_meters(55.755, 37.617, 55.756, 37.618)
    assert 50 < w < 120
    assert 50 < h < 120


def test_generate_dxf_from_osm_minimal():
    osm = {
        "buildings": [
            {
                "geometry": [
                    {"lat": 55.755, "lon": 37.617},
                    {"lat": 55.755, "lon": 37.6175},
                    {"lat": 55.7553, "lon": 37.6175},
                    {"lat": 55.7553, "lon": 37.617},
                ]
            }
        ],
        "roads": [
            {
                "geometry": [
                    {"lat": 55.755, "lon": 37.617},
                    {"lat": 55.7555, "lon": 37.618},
                ]
            }
        ],
    }
    data = generate_dxf_from_osm(55.755, 37.617, 55.756, 37.618, osm)
    assert data[:22] == b"  0\nSECTION\n  2\nHEADER"
    assert len(data) > 500


def test_parse_osm_map_xml_keeps_buildings_and_roads():
    xml = b"""<?xml version="1.0"?>
    <osm>
      <node id="1" lat="55.75" lon="37.61"/>
      <node id="2" lat="55.751" lon="37.61"/>
      <node id="3" lat="55.751" lon="37.612"/>
      <way id="10">
        <nd ref="1"/><nd ref="2"/><nd ref="3"/><nd ref="1"/>
        <tag k="building" v="yes"/>
      </way>
      <way id="11">
        <nd ref="1"/><nd ref="2"/>
        <tag k="highway" v="residential"/>
      </way>
      <way id="12">
        <nd ref="2"/><nd ref="3"/>
        <tag k="highway" v="motorway"/>
      </way>
      <way id="13">
        <nd ref="1"/><nd ref="3"/>
      </way>
      <relation id="20">
        <member type="way" ref="13" role="outer"/>
        <tag k="type" v="multipolygon"/>
        <tag k="building" v="apartments"/>
      </relation>
    </osm>
    """
    parsed = parse_osm_map_xml(xml)
    assert len(parsed["buildings"]) == 2
    assert len(parsed["roads"]) == 1
    assert parsed["buildings"][0]["geometry"][0] == {"lat": 55.75, "lon": 37.61}
