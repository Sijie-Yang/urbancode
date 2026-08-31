"""Live Overpass / Nominatim tests. Run with: pytest -m live"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.live


def test_download_network_small_place():
    pytest.importorskip("osmnx")
    import urbancode as uc

    graph = uc.download_network("graph", "walk", "Punggol, Singapore")
    assert graph.number_of_nodes() > 0
