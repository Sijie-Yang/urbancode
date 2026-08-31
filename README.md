# UrbanCode

UrbanCode is a library for reproducible urban analysis across street
networks, earth observation, climate, and street-view imagery. It is
built on GeoPandas, OSMnx, Rasterio, and related tools.

Import the package as `uc`.

**Docs:** https://urbancode.readthedocs.io/

## What it offers

- Load a study area and keep vector, raster, and graph layers in one `City`
- Build shared analysis units (grid, hex, or from a layer)
- Measure vegetation, water, built-up surface, and terrain
- Measure street-network centrality, clustering, and walk reachability
- Compute UTCI from observed weather plus a documented MRT proxy
- Score street photos for visual thermal affordance (VATA)
- Fuse those quantities onto the same units with provenance receipts

## Install

```bash
pip install urbancode
pip install "urbancode[standard]"     # vector + network + imagery + climate + viz
pip install "urbancode[svi]"          # TCIS + color
```

Tutorials need the committed Punggol fixture, which is not in the
wheel:

```bash
git clone --depth 1 https://github.com/Sijie-Yang/UrbanCode.git
cd UrbanCode
pip install -e ".[standard]"
python -c "import urbancode as uc; print(uc.__version__); print(uc.backends.status())"
```

Python 3.10+. The core wheel is small. Torch is not in `[standard]`.
`uc.svi.fetch` needs `urbancode[download]`. Weights download into
`~/.cache/urbancode/`.

## Examples

```python
import urbancode as uc

city = uc.load("examples/data/real/punggol", lazy=True)
print(city.place, city.keys()[:3])
```

Output:

```text
Punggol, Singapore ['streets', 'buildings', 'parks']
```

`city` is a lazy `City`: its manifest and layer inventory are loaded,
while raster pixels stay unopened until an imagery function needs them.

```python
units = uc.units.grid(city, cell_size=250)
ndvi = uc.imagery.ndvi(city.layers["sentinel2"])
result = uc.fusion.aggregate(ndvi, units, stat="mean", indicator="ndvi")
print(round(float(result.to_pandas()["value"].mean()), 3))
result.plot(indicator="ndvi")
```

Output:

```text
0.208
```

`units` is the 250 m grid, `ndvi` is the native Sentinel-2 raster, and
`result` is an `IndicatorResult` with one value and coverage record per
cell. The final line draws that result. Walkthrough:
https://urbancode.readthedocs.io/en/latest/getting_started/quickstart.html
Do **not** pass `layers="all"` for a whole city.

## Tests

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=. pytest tests/unit
sphinx-build -W --keep-going -b html docs/source docs/build/html
```
