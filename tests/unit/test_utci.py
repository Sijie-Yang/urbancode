from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pytest

from urbancode.city import Layer
from urbancode.errors import MissingExtraError
from urbancode.imagery.climate import utci


def test_utci_array_with_stub(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_utci(**kwargs):
        air = np.asarray(kwargs["tdb"], dtype=float)
        return SimpleNamespace(utci=air + 0.5)

    monkeypatch.setattr(
        "urbancode.climate.thermal.require_extra",
        lambda module, extra: SimpleNamespace(utci=fake_utci),
    )
    out = utci(np.array([[30.0, 31.0]]), tr=30.0, v=0.5, rh=50.0)
    assert isinstance(out, np.ndarray)
    assert out.shape == (1, 2)
    assert out[0, 0] == pytest.approx(30.5)


def test_utci_scalar_with_stub(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_utci(**kwargs):
        return SimpleNamespace(utci=24.6)

    monkeypatch.setattr(
        "urbancode.climate.thermal.require_extra",
        lambda module, extra: SimpleNamespace(utci=fake_utci),
    )
    out = utci(25.0)
    assert float(np.asarray(out)) == pytest.approx(24.6)


def test_utci_layer_inherits_grid(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_utci(**kwargs):
        return SimpleNamespace(utci=np.asarray(kwargs["tdb"]) + 1.0)

    monkeypatch.setattr(
        "urbancode.climate.thermal.require_extra",
        lambda module, extra: SimpleNamespace(utci=fake_utci),
    )
    class _Affine:
        a, b, c, d, e, f = 10.0, 0.0, 0.0, 0.0, -10.0, 20.0

    dem = Layer(
        name="tdb",
        kind="raster",
        data=np.array([[20.0, 21.0], [22.0, 23.0]]),
        crs="EPSG:32648",
        metadata={"transform": _Affine()},
    )
    layer = utci(dem, v=0.5, rh=50)
    assert isinstance(layer, Layer)
    assert layer.metadata["processing"]["op"] == "utci"
    assert layer.metadata["unit"] == "degree_celsius"
    assert layer.metadata["transform"][0] == pytest.approx(10.0)
    assert np.allclose(layer.data, dem.data + 1.0)


def test_utci_missing_extra(monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(module, extra):
        raise MissingExtraError(
            f'{module} is required. Install with: pip install "urbancode[{extra}]"'
        )

    monkeypatch.setattr("urbancode.climate.thermal.require_extra", boom)
    with pytest.raises(MissingExtraError, match="urbancode\\[climate\\]"):
        utci(25.0)
