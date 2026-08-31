# Real documentation datasets

| Directory | Kind | Notes |
|---|---|---|
| `punggol/` | 2 km pocket | OSM + Sentinel-2 + DEM |
| `kallio/` | 2 km pocket | OSM + Sentinel-2 + DEM |
| `greenwich_village/` | 2 km pocket | OSM + Sentinel-2 + DEM |
| `climate/` | Open-Meteo archive | Observed T/RH/wind; MRT modelled |
| `streetview/` | Wikimedia Commons | Geotagged CC photos |

Rebuild:

```bash
python scripts/data/build_real_pockets.py --all
python scripts/data/build_climate_cases.py
python scripts/data/build_streetview_cases.py
```

Synthetic Helsinki/NYC fixtures live in `examples/data/contracts/`.
Do not use them as real-city conclusions.
