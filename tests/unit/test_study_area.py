from __future__ import annotations

import pytest

from urbancode.area import StudyArea, utm_crs_from_lonlat
from urbancode.city import City


def test_utm_punggol() -> None:
    assert utm_crs_from_lonlat(103.91, 1.405) == "EPSG:32648"


def test_from_bbox() -> None:
    area = StudyArea.from_bbox(103.905, 1.4, 103.915, 1.41, place="Punggol")
    assert area.place == "Punggol"
    assert area.bbox == (103.905, 1.4, 103.915, 1.41)
    assert area.geographic_crs == "EPSG:4326"
    assert area.metric_crs == "EPSG:32648"


def test_from_geometry_tuple() -> None:
    area = StudyArea.from_geometry((103.9, 1.4, 103.92, 1.42))
    assert area.bbox[0] == pytest.approx(103.9)


def test_invalid_bbox() -> None:
    with pytest.raises(ValueError, match="west"):
        StudyArea.from_bbox(104.0, 1.4, 103.0, 1.5)


def test_city_accepts_study_area() -> None:
    area = StudyArea.from_bbox(103.905, 1.4, 103.915, 1.41, place="Punggol")
    city = City(area)
    assert city.place == "Punggol"
    assert city.study_area is area
    other = City(study_area=area)
    assert other.place == "Punggol"


def test_city_id_slug() -> None:
    area = StudyArea.from_bbox(103.905, 1.4, 103.915, 1.41, place="Punggol, Singapore")
    assert area.city_id == "punggol-singapore"
    assert area.projected_crs == area.metric_crs


def test_no_stub_unit_constructors() -> None:
    import urbancode.units as units

    assert not hasattr(units, "h3")
    assert not hasattr(units, "administrative")
    assert not hasattr(units, "street_segments")
    assert callable(units.hexgrid)


def test_from_geometry_rejects_projected_without_crs() -> None:
    with pytest.raises(ValueError, match="projected"):
        StudyArea.from_geometry((380000.0, 150000.0, 381000.0, 151000.0))


def test_from_bbox_rejects_projected_numbers_as_lonlat() -> None:
    with pytest.raises(ValueError, match="projected"):
        StudyArea.from_bbox(380000.0, 150000.0, 381000.0, 151000.0)
