# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Changed
- Public street-view namespace is `uc.svi` / `urbancode[svi]`. `uc.streetview` and the `streetview` extra stay as aliases
- Documentation uses the Material theme (same family as momepy): library homepage, User guide / Examples / API nav, measure-grouped API tables
- Tutorials teach in small blocks: code, then print / inspect / plot. Figure-builder scripts stay out of Get Started, workflows, research cases, and recipes
- Every generated recipe now places a variable/return-value explanation and the matching figure directly after its runnable code block
- Public docstrings for units, fusion, network metrics, and UTCI now state inputs, return contracts, units, failure modes, and interpretation limits

### Fixed
- `uc.units.grid` and `uc.units.hexgrid` now clip edge geometry to the StudyArea envelope, matching the documented contract and preventing out-of-study area from entering coverage and area-fraction denominators
- The docs figure refresher accepts recipes that already wrote directly to their final `_static` path instead of raising `SameFileError`

### Added
- `uc.images.from_table` and `uc.streetview.as_layer` accept a catalog path (JSON/CSV/parquet)
- Heat Resilience in Sight research case from committed city-month summaries (Singapore n = 21,772, not the TCIS 92,233 survey set). No public SHR helper.

## [0.3.0] - 2026-08-20

### Fixed
- `uc.network.fetch` stays the callable after `import urbancode.network.fetch` (function/submodule name collision)
- `uc.network.accessibility` no longer resolves to the legacy `_radius` submodule (module/function name collision)
- Docs tests set `MPLBACKEND=Agg`; Sphinx `-W` builds stay offline (empty intersphinx mapping)
- Lazy City context layers materialize before map drawing
- `uc.fusion.aggregate` raises if an explicit `column=` is missing instead of silently using 1.0

### Added
- `uc.images.from_table(..., image_root=)` resolves catalog relative paths without storing machine roots in exports
- Dataset-scale `uc.perception.thermal_affordance` (`batch_size`, `chunk_size`, `resume`, `output`) on the same API
- Pinned TCIS IF chain: SegFormer Cityscapes revision, Faster R-CNN COCO_V1, Places365 weight/label SHA-256
- Singapore 92,233 SVI: Alienware JPEG store and 10/100/1000 smoke (RTX 3070 Ti); full TCIS receipts from ual-chark RTX 5090 (parquet stays off Git); Commons eight-photo set is a tiny fixture
- `uc.images.from_table` geolocated photo-observation Layer; `uc.streetview.as_layer` wraps it
- `uc.perception.thermal_affordance` returns a Layer (VATA, not UTCI); TCIS inference moved to a torch-lazy backend
- `uc.fusion.aggregate_many` for multi-column IndicatorResult batching
- Thermal Comfort in Sight research case (real Commons photos, provenance, offline/full modes)
- Phase 2 design page for City Landscape in Sight (no half-implemented APIs)
- Extras: `perception`, `research`, `spatial-stats` (the last has no public API yet)
- Cartography helpers and a Spatial support and maps concept page
- Pocket context layers: water (Sentinel-2 NDWI or OSM) and parent-city locator envelopes
- Reverse public-API catalog audit from `__all__`, including `IndicatorResult.to_layer`
- Documentation contract: homepage, Get Started, Concepts, five research workflows, seven Domains, ecosystem/datasets pages, and catalog-driven recipes
- Real 2 km pockets (Punggol, Kallio, Greenwich Village), recipe catalog under Reference, and per-command figures
- Domain core: `StudyArea`, `AnalysisUnits.grid` / `from_layer`, `IndicatorRecord` / `IndicatorResult`, `uc.fusion.aggregate` (raster + graph → same grid)
- `uc.climate.utci` (canonical); `uc.streetview` is the official street-view namespace (`uc.svi` is a deprecated identity shim); `uc.backends.available` / `info` / `require` / `status` / `explain`
- Contract: persisted `StudyArea`, world-origin `AnalysisUnits.grid` / `hexgrid`, long-table `IndicatorResult`, `ProvenanceRecord`, lazy `City.to_dir` copies, `uc.fusion.combine`
- Helsinki and New York pocket fixtures for offline three-city comparison
- `uc.load(..., layers=..., lazy=True)` — raster-only load does not require GeoPandas
- Extras: `vector`, `streetview`, `viz`, `standard` (aliases kept: `svi`, `download`, `gallery`)
- Unified Phase 0 ADRs (UrbanCode × StreetRAG); frozen as a future interface; no StreetRAG runtime
- Ecosystem adapters: `uc.adapters` lazy re-exports; `uc.streetview.fetch` (ZenSVI / unofficial Google opt-in); `uc.imagery.utci` (`urbancode[climate]`); package table in `docs/source/architecture/ecosystem.rst`
- Phase 0 existing-API closure: `uc.network.clustering` (Watts–Strogatz, experimental), `uc.network.local_efficiency` (Latora–Marchiori, experimental), and `uc.imagery.aspect` (clockwise-from-north Layer, flat/nodata)
- Analysis catalog and Phases 1–4 roadmap (not a final UrbanStudy architecture)
- Visual tutorials for `network`, `imagery`, and `svi` (committed PNGs under `docs/source/_static/tutorials/`)
- High-level aliases `uc.load`, `City.save`, `Layer.save`, `City.plot`, `Layer.plot`
- `uc.imagery.ndvi` / `ndwi` / `ndbi` / `slope` / `hillshade` / `zonal_stats` accept Layer or path and return Layer
- `uc.network.centrality` and `uc.network.accessibility` return a plottable Layer
- Sphinx user guide, explicit API pages, and a visualization gallery
- Committed Punggol City fixture (real OSM / Sentinel-2 / DEM extract) under `examples/data/punggol_pocket/`
- `docs` and `gallery` extras; Read the Docs installs only `[docs]`
- PEP 621 `pyproject.toml` with light core deps and extras
- Unified cache under `platformdirs` / `URBANCODE_CACHE_DIR`
- `uc` / `urbancode` CLI (`fetch`, `network fetch`, `imagery fetch`, `svi comfort`)

### Changed
- Package version is 0.3.0 from `urbancode/_version.py`
- `import urbancode` no longer imports torch, osmnx, or rasterio
- `uc.streetview.comfort()` is deprecated; it still returns a DataFrame and keeps `thermal_comfort` as a one-cycle alias of VATA
- Maps are geometry-aware: City/Layer/IndicatorResult.plot accept context, study boundary, scale bar, north arrow, and locator; grid fill is semi-transparent over streets and buildings
- Indicator maps pick color scales from name/unit (NDVI, fraction, metres, node count, UTCI); NDVI ±0.2–0.8 is no longer applied to every vector layer
- Heat Exposure uses observed Open-Meteo weather plus a documented spatial MRT proxy, then joins UTCI, NDVI, NDBI, and building fraction
- Street-view ML recipes are blocked/live (`offline: false`); placeholder result PNGs were removed
- Workflow sidebar lists only the five canonical cases; old URLs are HTML redirects, not hidden toctree entries
- Recipe pages carry parameters, outputs, sensitivity, and failure modes instead of “defaults are those of function X”
- `affine` is pinned to `>=2.4,<3` for rasterio/rioxarray compatibility
- GeoPandas install hint is `urbancode[vector]`, not `[network]`
- StreetRAG ADRs marked frozen; product focus is the unified domain API
- Offline gallery scripts use only `urbancode` and `pathlib`; GIS orchestration moved into the package

## [0.2.1] - 2025-04-17

### Added
- Added normalization of perception scores to 0-5 range when processing multiple images
- Improved comfort function to automatically scale perception metrics

## [0.2.0] - 2025-04-17

### Changed
- Reorganized perception module into SVI module for better structure
- Updated version number consistency across the package

### Fixed
- Removed redundant perception module
- Fixed package structure in PyPI distribution

## [0.1.1] - 2025-01-15

### Added
- Added Street View Image (SVI) feature extraction functionality
  - Semantic segmentation using Segformer
  - Color feature extraction including color histograms and statistics
  - Object detection using Faster R-CNN
  - Scene recognition using ResNet models
- Improved documentation and examples

## [0.1.0] - 2024-11-09

### Added
- Initial release for urban perception analysis
- Two-stage neural network for perception analysis
- Beta version of urbancode
- Potential errors in documentation and programming
