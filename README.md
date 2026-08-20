# UrbanCode (v0.3.0)

UrbanCode is a unified Python workflow for reproducible, multimodal and
multi-city urban analysis. Import it as `uc`.

**Docs:** https://urbancode.readthedocs.io/

```bash
pip install urbancode
pip install "urbancode[standard]"     # vector + network + imagery + climate + viz
pip install "urbancode[streetview]"   # TCIS + color (install aliases: svi, download)
```

Python 3.10+. The core wheel is small. Torch is not in `[standard]`.
Weights download into `~/.cache/urbancode/`.

## Quick start (offline Punggol pocket)

```python
import urbancode as uc

city = uc.load("examples/data/real/punggol", layers=["streets", "sentinel2"], lazy=True)
city.study_area = uc.StudyArea.from_bbox(*city.metadata["bbox"], place=city.place, city_id="punggol")
units = uc.units.grid(city, cell_size=250)
ndvi = uc.imagery.ndvi(city.layers["sentinel2"].path)
reach = uc.network.accessibility(city["streets"], radius=150, metric="reachability")
result = uc.fusion.combine(
    units,
    uc.fusion.aggregate(ndvi, units, indicator="ndvi"),
    uc.fusion.aggregate(reach, units, indicator="reachability"),
)
result.save("out/punggol")
```

The full script is `examples/workflows/punggol_end_to_end.py`.

Do **not** pass `layers="all"` for a whole city.

## Tests

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=. pytest tests/unit
sphinx-build -W --keep-going -b html docs/source docs/build/html
```
