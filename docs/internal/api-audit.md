# UrbanCode public API audit (2026-08-16)

Source of truth: `urbancode/__init__.py`, submodule `__all__`, `urbancode/cli.py`, `pyproject.toml`, `docs/source/catalog/capabilities.yaml`.

Status values in the catalog: `stable | experimental | adapter-only | planned | compatibility | legacy`. Reverse coverage is tested from `__all__`, not from YAML self-checks.

## Canonical public analysis API

| public_name | canonical_import | domain | status | input | output | unit | backends | recipe | workflow | figure | offline | provenance |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| uc.load | urbancode.city.load | vector | stable | City dir | City | mixed | geopandas/pyogrio | core/city_roundtrip_punggol | punggol_urban_profile | recipes/core/city_roundtrip_punggol.png | yes | Layer stamps |
| uc.fetch | urbancode.fetch.fetch | vector | stable | place/bbox | City | mixed | osmnx, pystac-client | core/fetch_punggol | punggol_urban_profile | recipes/cli/fetch.png | offline stand-in | Layer stamps |
| StudyArea.from_bbox | urbancode.area.StudyArea.from_bbox | vector | stable | lon/lat bbox | StudyArea | CRS | pyproj | core/study_area_punggol | punggol_urban_profile | recipes/core/study_area_punggol.png | yes | area metadata |
| uc.units.grid | urbancode.units.grid | units | stable | City/StudyArea | AnalysisUnits | m | geopandas, shapely, pyproj | units/grid_punggol | punggol_urban_profile | recipes/units/units_punggol.png | yes | unit IDs |
| uc.units.hexgrid | urbancode.units.hexgrid | units | stable | City/StudyArea | AnalysisUnits | m | shapely, geopandas | units/hexgrid_punggol | punggol_urban_profile | recipes/units/units_punggol.png | yes | unit IDs |
| uc.units.from_layer | urbancode.units.from_layer | units | stable | polygon Layer | AnalysisUnits | polygon | geopandas | units/from_layer_punggol | punggol_urban_profile | recipes/units/units_punggol.png | yes | geom fingerprint |
| uc.network.fetch | urbancode.network.fetch | network | stable | bbox/place | City | graph | osmnx | network/fetch_punggol | punggol_urban_profile | recipes/network/fetch_punggol.png | yes | OSM extract date |
| uc.network.centrality | urbancode.network.metrics.centrality | network | stable | graph | graph Layer | 1 | networkx | network/centrality_punggol | punggol_urban_profile | recipes/network/centrality_punggol.png | yes | params |
| uc.network.accessibility | urbancode.network.metrics.accessibility | network | stable | graph | graph Layer | count | networkx | network/accessibility_punggol | green_accessibility | recipes/network/accessibility_punggol.png | yes | radius |
| uc.network.clustering | urbancode.network.metrics.clustering | network | experimental | graph | graph Layer | 1 | networkx | network/clustering_punggol | punggol_urban_profile | recipes/network/clustering_punggol.png | yes | experimental |
| uc.network.local_efficiency | urbancode.network.metrics.local_efficiency | network | experimental | graph | graph Layer | 1 | networkx | network/local_efficiency_punggol | punggol_urban_profile | recipes/network/local_efficiency_punggol.png | yes | experimental |
| uc.imagery.read | urbancode.imagery.read | imagery | stable | GeoTIFF | raster Layer | source | rasterio, rioxarray | imagery/read_punggol | punggol_urban_profile | recipes/imagery/read_punggol.png | yes | CRS/bands |
| uc.imagery.fetch | urbancode.imagery.fetch | imagery | stable | bbox/STAC | raster Layer | reflectance/m | pystac-client, planetary-computer | imagery/fetch_punggol | punggol_urban_profile | recipes/imagery/fetch_punggol.png | offline stand-in | item id |
| uc.imagery.ndvi | urbancode.imagery.ndvi | imagery | stable | S2 Layer | raster Layer | 1 | rasterio | imagery/ndvi_punggol | punggol_urban_profile | recipes/imagery/indices_punggol.png | yes | bands/date |
| uc.imagery.ndwi | urbancode.imagery.ndwi | imagery | stable | S2 Layer | raster Layer | 1 | rasterio | imagery/ndwi_punggol | punggol_urban_profile | recipes/imagery/indices_punggol.png | yes | McFeeters B03/B08 |
| uc.imagery.ndbi | urbancode.imagery.ndbi | imagery | stable | S2 Layer | raster Layer | 1 | rasterio | imagery/ndbi_punggol | punggol_urban_profile | recipes/imagery/indices_punggol.png | yes | B11/B08 |
| uc.imagery.slope | urbancode.imagery.slope | imagery | stable | DEM | raster Layer | degree | rasterio | imagery/slope_punggol | multi_city_comparison | recipes/imagery/terrain_punggol.png | yes | DEM res |
| uc.imagery.aspect | urbancode.imagery.aspect | imagery | stable | DEM | raster Layer | degree | rasterio | imagery/aspect_punggol | multi_city_comparison | recipes/imagery/terrain_punggol.png | yes | from north |
| uc.imagery.hillshade | urbancode.imagery.hillshade | imagery | stable | DEM | raster Layer | 1 | rasterio | imagery/hillshade_punggol | multi_city_comparison | recipes/imagery/terrain_punggol.png | yes | assumed sun |
| uc.imagery.zonal_stats | urbancode.imagery.zonal_stats | imagery | stable | raster+polygons | vector Layer | source | rasterio | imagery/zonal_stats_punggol | punggol_urban_profile | recipes/imagery/zonal_stats_punggol.png | yes | coverage |
| uc.climate.utci | urbancode.climate.utci | climate | experimental | T, MRT, RH, wind | raster Layer | °C | pythermalcomfort | climate/utci_real | heat_exposure | recipes/climate/utci_real.png | yes | modelled MRT |
| uc.svi.fetch | urbancode.streetview.fetch | streetview | experimental | study area | catalog | image | zensvi, streetlevel | blocked | street_experience | — | live-only | provider terms; extra=`download` |
| uc.svi.filename | urbancode.streetview.filename | streetview | stable | image dir | DataFrame | filename | pandas | streetview/filename_punggol | street_experience | recipes/streetview/filename_punggol.png | yes | catalog only |
| uc.svi.color | urbancode.streetview.color | streetview | experimental | catalog | DataFrame | colorfulness | opencv | streetview/color_punggol | street_experience | recipes/streetview/color_punggol.png | yes | pixel stat |
| uc.svi.segmentation | urbancode.streetview.segmentation | streetview | experimental | photo | class shares | fraction | torch | blocked | street_experience | — | live/heavy | no committed masks |
| uc.svi.object_detection | urbancode.streetview.object_detection | streetview | experimental | photo | boxes | count | torch | blocked | street_experience | — | live/heavy | no committed boxes |
| uc.svi.scene_recognition | urbancode.streetview.scene_recognition | streetview | experimental | photo | probs | probability | torch | blocked | street_experience | — | live/heavy | no committed scores |
| uc.svi.comfort | urbancode.streetview.comfort | streetview | experimental | photo | scores | score | torch / TCIS | blocked | street_experience | — | live/heavy | no committed scores |
| uc.IndicatorResult.to_layer | urbancode.indicators.IndicatorResult.to_layer | fusion | stable | IndicatorResult | vector Layer | indicator | geopandas | fusion/combine_punggol | punggol_urban_profile | recipes/fusion/combine_punggol.png | yes | copies unit |
| uc.svi.as_layer | urbancode.streetview.as_layer | streetview | stable | lon/lat table | point Layer | point | geopandas | streetview/as_layer_punggol | street_experience | recipes/streetview/as_layer_punggol.png | yes | geotag quality |
| uc.fusion.aggregate | urbancode.fusion.aggregate | fusion | stable | Layer+Units | IndicatorResult | stat | geopandas, rasterio | fusion/aggregate_punggol | punggol_urban_profile | recipes/fusion/aggregate_punggol.png | yes | receipts |
| uc.fusion.combine | urbancode.fusion.combine | fusion | stable | IndicatorResults | IndicatorResult | mixed | pandas | fusion/combine_punggol | punggol_urban_profile | recipes/fusion/combine_punggol.png | yes | join checks |

## Compatibility / legacy (do not teach as current)

| name | status | note |
|---|---|---|
| uc.streetview | compatibility | Alias of uc.svi through 0.4.0. Teach uc.svi only. |
| uc.imagery.utci | compatibility | Alias of uc.climate.utci. Climate domain only. |
| uc.imagery.aspect_degrees / slope_degrees | compatibility | Same as aspect/slope. |
| uc.network.download_network / save_network / load_saved_network | legacy | Prefer uc.network.fetch and City I/O. |
| uc.network.graph_to_gdf / graph_from_gdf | compatibility | Graph interchange, not a metric. |
| uc.network.*_radius / calculate_accessibility_metrics | legacy | Prefer centrality / accessibility / clustering / local_efficiency. |
| CLI `uc streetview` | compatibility | Hidden alias of `uc svi`. Remove after 0.4.0. |

## CLI (real commands only)

| command | maps to | recipe figure |
|---|---|---|
| uc --version | package version | recipes/cli/version.png |
| uc fetch | uc.fetch | recipes/cli/fetch.png |
| uc network fetch | uc.network.fetch | recipes/cli/network_fetch.png (if generated) |
| uc imagery fetch | uc.imagery.fetch | recipes/cli/imagery_fetch.png |
| uc svi comfort | uc.svi.comfort | recipes/cli/streetview_comfort.png (if generated) |

There is no `uc doctor`. Use `uc.backends.status()`.

## Adapter-only

| name | extra | interop |
|---|---|---|
| uc.adapters.osmnx | network | examples/recipes/adapters/osmnx.py |
| uc.adapters.zensvi | download | examples/recipes/adapters/zensvi.py |

## Planned (not public, not “UrbanCode supports”)

momepy named morphology functions, H3 units, PySAL, cityseer, Pandana, r5py, stackstac/odc-stac, Dask rasters, DuckDB Spatial, xclim, pvlib.

## Docs gap closed in this pass

- Duplicate workflows merged to five research pages; old titles are redirects, not sidebar entries.
- Missing `uc.load` / `uc.fetch` / `StudyArea.from_bbox` added to the catalog.
- Domain `units` page added.
- `reference/ecosystem.rst` and `reference/datasets.rst` added.
- Homepage / Get Started / Concepts rewritten around the contract, not module lists.
- Street-view ML is blocked/live; no fake offline figures.
- Color scales follow indicator unit; NDVI range is not applied to distance or counts.
- `uc.network.accessibility` is the metrics function; legacy radius helpers live in `urbancode.network._radius`.
