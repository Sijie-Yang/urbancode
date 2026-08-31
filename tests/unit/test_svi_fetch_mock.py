from __future__ import annotations

import importlib
from pathlib import Path

import pytest

import urbancode as uc
from urbancode.errors import MissingExtraError

_fetch_mod = importlib.import_module("urbancode.streetview.download")


def _write_jpeg(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"\xff\xd8\xff\xd9")
    return path


def test_svi_fetch_requires_location() -> None:
    with pytest.raises(ValueError, match="place, bbox, or lat/lon"):
        uc.svi.fetch(source="kartaview")


def test_svi_fetch_mapillary_needs_key() -> None:
    with pytest.raises(ValueError, match="api_key"):
        uc.svi.fetch(lat=1.4, lon=103.9, source="mapillary")


def test_svi_fetch_google_off_by_default() -> None:
    with pytest.raises(ValueError, match="allow_unofficial"):
        uc.svi.fetch(lat=1.4, lon=103.9, source="google")


def test_svi_fetch_unknown_source() -> None:
    with pytest.raises(ValueError, match="unknown SVI source"):
        uc.svi.fetch(lat=1.4, lon=103.9, source="lookaround")


def test_svi_fetch_kartaview_mocked(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_download(out_dir, **kwargs):
        _write_jpeg(Path(out_dir) / "pano.jpg")

    monkeypatch.setattr(_fetch_mod, "_zensvi_download", fake_download)
    city = uc.svi.fetch(
        "Punggol, Singapore",
        source="kartaview",
        lat=1.405,
        lon=103.910,
        out=tmp_path,
    )
    assert "streetview" in city
    assert "svi_index" in city
    layer = city.layer("streetview")
    assert layer.kind == "images"
    assert Path(layer.path).is_file()
    assert layer.metadata["processing"]["op"] == "svi_fetch"
    assert layer.metadata["processing"]["backend"] == "zensvi"
    assert len(city["svi_index"]) == 1
    assert city["svi_index"]["source"].iloc[0] == "kartaview"


def test_svi_fetch_google_mocked(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_google(out_dir, **kwargs):
        _write_jpeg(Path(out_dir) / "gsv.jpg")

    monkeypatch.setattr(_fetch_mod, "_streetlevel_google", fake_google)
    city = uc.svi.fetch(
        lat=1.4,
        lon=103.9,
        source="google",
        allow_unofficial=True,
        out=tmp_path,
    )
    assert city.layer("streetview").metadata["processing"]["backend"] == "streetlevel"
    assert city.metadata["source"] == "google"


def test_svi_fetch_missing_download_extra(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    def boom(*_args, **_kwargs):
        raise MissingExtraError('zensvi is required. Install with: pip install "urbancode[download]"')

    monkeypatch.setattr(_fetch_mod, "_zensvi_download", boom)
    with pytest.raises(MissingExtraError, match="urbancode\\[download\\]"):
        uc.svi.fetch(lat=1.4, lon=103.9, source="kartaview", out=tmp_path)
