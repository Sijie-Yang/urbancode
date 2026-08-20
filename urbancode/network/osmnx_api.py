"""OSMnx 2.x adapter. v0.3 does not support OSMnx 1.x."""

from __future__ import annotations

from typing import Any


def graph_from_bbox(ox: Any, west: float, south: float, east: float, north: float, network_type: str):
    """OSMnx 2: ``bbox=(left, bottom, right, top)`` = west, south, east, north."""
    return ox.graph_from_bbox(
        bbox=(west, south, east, north),
        network_type=network_type,
    )


def features_from_bbox(ox: Any, west: float, south: float, east: float, north: float, tags: dict):
    return ox.features_from_bbox(bbox=(west, south, east, north), tags=tags)
