#!/usr/bin/env python3
"""Generate recipe RST pages from the capability catalog."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from catalog_lib import analysis_items, is_blocked, load_catalog, recipe_py, recipe_rst  # noqa: E402

DOMAIN_DOC = {
    "vector": "/domains/vector",
    "units": "/domains/units",
    "network": "/domains/network",
    "imagery": "/domains/imagery",
    "climate": "/domains/climate",
    "streetview": "/domains/streetview",
    "fusion": "/domains/fusion",
    "images": "/concepts/image_observations",
    "perception": "/reference/api/perception",
    "adapters": "/reference/api/adapters",
}
API_DOC = {
    "vector": "/reference/api/city",
    "units": "/reference/api/units",
    "network": "/reference/api/network",
    "imagery": "/reference/api/imagery",
    "climate": "/reference/api/climate",
    "streetview": "/reference/api/streetview",
    "fusion": "/reference/api/fusion",
    "images": "/reference/api/images",
    "perception": "/reference/api/perception",
    "adapters": "/reference/api/adapters",
}

COPY = {
    "core.load": (
        "Reads a City directory. lazy=True copies source files on save without opening rasters first.",
        "The map is the layer inventory, not a new download.",
    ),
    "core.fetch": (
        "Live fetch writes a City directory from OSM and STAC. This page uses the committed pocket.",
        "Treat the figure as the output contract of uc.fetch, not a live Overpass result.",
    ),
    "core.study_area": (
        "StudyArea.from_bbox stores lon/lat and derives a metric CRS from the centre.",
        "The envelope is the 2 km pocket, not the municipal boundary.",
    ),
    "network.fetch": (
        "The committed graph is an OSM walk extract clipped to the pocket.",
        "Line density follows the street layout. This is not traffic volume.",
    ),
    "network.centrality": (
        "Betweenness uses Brandes with an optional radius. Closeness is inverse farness.",
        "High betweenness near the pocket edge is often a boundary effect, not a CBD.",
    ),
    "network.accessibility": (
        "Reachability counts other graph nodes within a length cutoff.",
        "Read this as network reachability, never as jobs or population access.",
    ),
    "network.clustering": (
        "Watts–Strogatz local clustering on the undirected walk graph.",
        "Zeros are expected on degree-1 and degree-2 street nodes.",
    ),
    "network.local_efficiency": (
        "Latora–Marchiori local efficiency among neighbours of each node.",
        "High values mean neighbours stay connected if the node is removed.",
    ),
    "imagery.read": (
        "Opens a local GeoTIFF with rasterio/rioxarray and records CRS, bands, nodata.",
        "The preview is a rendering, not a reflectance product.",
    ),
    "imagery.fetch": (
        "Live fetch searches Planetary Computer. This page uses the committed item.",
        "Cloud cover and item ID are in the sidecar text, not inferred from the RGB.",
    ),
    "imagery.ndvi": (
        "NDVI = (NIR - red) / (NIR + red) using B08 and B04.",
        "High values are greener canopies on this date only.",
    ),
    "imagery.ndwi": (
        "NDWI = (green - NIR) / (green + NIR) using B03 and B08.",
        "High values can be water or dark shadow; check the RGB.",
    ),
    "imagery.ndbi": (
        "NDBI = (SWIR - NIR) / (SWIR + NIR) using B11 and B08.",
        "High values can be built-up or bare soil.",
    ),
    "imagery.slope": (
        "Slope in degrees from the Copernicus DEM GLO-30 grid.",
        "This is terrain, not a building DSM.",
    ),
    "imagery.aspect": (
        "Aspect in degrees clockwise from north. Flat cells are nodata.",
        "Use a cyclic reading: 0 and 360 are the same facing.",
    ),
    "imagery.hillshade": (
        "Assumed illumination, not a local solar-position model.",
        "Shading is for reading relief, not solar access.",
    ),
    "imagery.zonal_stats": (
        "Mean NDVI inside each OSM park polygon.",
        "A high park mean is greener foliage inside that polygon on this date.",
    ),
    "climate.utci": (
        "UTCI from observed T/RH/wind and modelled mean radiant temperature.",
        "Do not read this as a measured outdoor campaign.",
    ),
    "streetview.filename": (
        "Lists image files in a folder. No perception scores.",
        "The contact sheet is the catalog, not a spatial sample.",
    ),
    "streetview.color": (
        "OpenCV Colorfulness and related pixel statistics.",
        "High Colorfulness is a more saturated photo, not a comfort score.",
    ),
    "streetview.as_layer": (
        "Builds a point Layer from lon/lat columns.",
        "Only geotagged rows are observations. Illustrative points stay labelled.",
    ),
    "streetview.segmentation": (
        "Packaged segmentation model. Offline page may use committed output.",
        "Class shares are model output, not a field survey.",
    ),
    "streetview.object_detection": (
        "Packaged detector. Offline page may use committed boxes.",
        "Counts are detections, not a traffic census.",
    ),
    "streetview.scene_recognition": (
        "Places365 scene prior.",
        "Top classes are visual resemblance, not land-use zoning.",
    ),
    "streetview.comfort": (
        "TCIS model scores. Weights stay in the user cache.",
        "A high score is the model, not a measured thermal comfort.",
    ),
    "fusion.aggregate": (
        "Summarize a Layer onto AnalysisUnits. Missing stays null.",
        "Read value together with coverage: a high value on low coverage is thin.",
    ),
    "fusion.combine": (
        "Concatenates IndicatorResults that share city_id, units, CRS, and scheme.",
        "combine does not re-aggregate; mismatched units raise.",
    ),
    "fusion.aggregate_many": (
        "Aggregates several columns from one Layer, then combines them.",
        "Units with no photos stay null, not zero.",
    ),
    "images.from_table": (
        "Builds a geolocated photo Layer. image_id must be unique.",
        "Each point is one photo, not a street census.",
    ),
    "perception.thermal_affordance": (
        "TCIS VATA and VPI heads as a Layer. Weights stay in the user cache.",
        "thermal_affordance is visual affordance, not measured comfort and not UTCI.",
    ),
    "units.grid": (
        "Square metres grid with world-origin IDs.",
        "Edge cells are clipped to the study area.",
    ),
    "units.hexgrid": (
        "Pointy-top hexes. cell_size is the centre-to-vertex radius.",
        "Hex IDs are not interchangeable with square grid IDs.",
    ),
    "units.from_layer": (
        "Existing polygons become units. IDs are geometry fingerprints.",
        "Duplicate geometries raise; they are not row-number suffixed.",
    ),
}

TEACHING = {
    "network.accessibility": {
        "parameters": (
            "``radius`` (float, required): graph-length cutoff in the same "
            "units as ``weight`` (metres on OSM walk graphs).\n\n"
            "``metric`` (str, default ``reachability``): only "
            "``reachability`` is implemented.\n\n"
            "``weight`` (str, default ``length``): edge attribute used as "
            "distance. Missing lengths are filled from geometry when present."
        ),
        "output_fields": (
            "Graph Layer. Node attribute ``reachability`` is a count of other "
            "nodes reachable within ``radius``. Unit: count. CRS is the "
            "source graph CRS (usually EPSG:4326); metric work happens on "
            "edge lengths, not degrees."
        ),
        "sensitivity": (
            "150 m vs 500 m raises node counts and flattens local contrast. "
            "A 2 km pocket truncates paths that would continue outside the box."
        ),
        "failure": (
            "Unknown ``metric`` raises. Negative ``radius`` raises. "
            "Disconnected components simply cannot reach each other."
        ),
        "spatial_support": (
            "Native support: network nodes. Recipe figure: nodes/edges on "
            "the street graph. Fusion support: optional 250 m grid after "
            "``uc.fusion.aggregate``."
        ),
    },
    "network.centrality": {
        "parameters": (
            "``metric``: ``betweenness`` or ``closeness``.\n\n"
            "``radius``: optional distance cutoff in ``weight`` units.\n\n"
            "``weight``: default ``length``."
        ),
        "output_fields": "Graph Layer with node attribute ``betweenness`` or ``closeness`` (dimensionless).",
        "sensitivity": "Unbounded betweenness on a clipped pocket is dominated by the cut boundary.",
        "failure": "Unknown metric raises. Isolated nodes have closeness 0.",
    },
    "imagery.ndvi": {
        "parameters": (
            "``source``: Layer, GeoTIFF path, or named-band mapping.\n\n"
            "``nodata``: default NaN. Bands must be named B08/NIR and B04/Red."
        ),
        "output_fields": (
            "Raster Layer ``ndvi``. Formula (B08 − B04) / (B08 + B04). "
            "Unit dimensionless. Resolution follows the source (10 m here)."
        ),
        "sensitivity": "A different date or cloud mask changes the map more than the formula.",
        "failure": "Missing B04 or B08 raises KeyError. No silent band-position fallback.",
        "spatial_support": (
            "Native support: 10 m raster pixels. Recipe figure: native raster. "
            "Fusion support: 250 m mean NDVI only in fusion workflows."
        ),
    },
    "imagery.ndwi": {
        "parameters": "McFeeters NDWI needs B03 (green) and B08 (NIR).",
        "output_fields": "Raster Layer. (B03 − B08) / (B03 + B08).",
        "sensitivity": "Dark shadow can look like water.",
        "failure": "Missing B03 raises; this fixture includes B03.",
    },
    "imagery.ndbi": {
        "parameters": "Needs B11 (SWIR) and B08 (NIR).",
        "output_fields": "Raster Layer. (B11 − B08) / (B11 + B08).",
        "sensitivity": "Bare soil can raise NDBI.",
        "failure": "Missing B11 raises.",
    },
    "climate.utci": {
        "parameters": (
            "``air_temperature``, ``mean_radiant_temperature``, "
            "``wind_speed``, ``relative_humidity``. MRT defaults to air "
            "temperature if omitted and is then flagged as assumed."
        ),
        "output_fields": "Raster Layer ``utci`` in °C.",
        "sensitivity": "A spatial MRT proxy changes the map; a point weather field does not.",
        "failure": "Missing extra ``climate`` raises MissingExtraError.",
    },
    "fusion.aggregate": {
        "parameters": (
            "``stat``: mean, min, max, median, p50, sum, count, weighted_mean, "
            "coverage, area_fraction, length_density, presence, nearest_distance.\n\n"
            "``indicator``: output name. ``column``: vector/graph value column."
        ),
        "output_fields": "IndicatorResult with value, coverage, unit, quality_flags, provenance.",
        "sensitivity": "Changing units (100 m vs 250 m) moves means (MAUP).",
        "failure": "Unknown stat raises. Mixed geometry types can break overlay.",
    },
    "units.grid": {
        "parameters": "``cell_size`` in metres in the metric CRS. Edge cells are clipped.",
        "output_fields": "AnalysisUnits with IDs ``grid:<CRS>:<size>:<col>:<row>``.",
        "sensitivity": "World-origin IDs stay stable if the bbox shifts slightly.",
        "failure": "A geographic CRS without a metric CRS raises.",
    },
    "units.hexgrid": {
        "parameters": (
            "``cell_size`` is the centre-to-vertex radius in metres, not the "
            "flat-to-flat width."
        ),
        "output_fields": "AnalysisUnits with hex IDs. Not interchangeable with square grid IDs.",
        "sensitivity": "Halving cell_size roughly quadruples hex count.",
        "failure": "A geographic CRS without a metric CRS raises.",
    },
    "units.from_layer": {
        "parameters": "``layer`` must be polygons. Optional ``id_column`` is not invented.",
        "output_fields": "AnalysisUnits. IDs are geometry fingerprints unless a column is given.",
        "sensitivity": "Simplifying polygons changes IDs because they are fingerprints.",
        "failure": "Duplicate geometries raise. Points and lines raise.",
    },
    "network.fetch": {
        "parameters": (
            "``place`` or ``bbox``. ``layers`` defaults to streets only; "
            "``layers='all'`` is explicit. ``network_type`` follows OSMnx walk/drive."
        ),
        "output_fields": "City with graph and vector layers. CRS EPSG:4326 plus a metric CRS stamp.",
        "sensitivity": "A 100 m bbox change can drop or add whole streets at the cut.",
        "failure": "Live Overpass failures raise unless ``on_error`` is set on ``uc.fetch``.",
    },
    "network.clustering": {
        "parameters": (
            "``radius`` optional length cutoff. ``weight`` default ``length``. "
            "Computed on the undirected simple graph."
        ),
        "output_fields": "Graph Layer. Node attribute ``clustering`` (Watts–Strogatz, dimensionless).",
        "sensitivity": "Degree-1 and degree-2 nodes are often zero; that is expected.",
        "failure": "Empty graphs raise. Isolated nodes get 0.",
    },
    "network.local_efficiency": {
        "parameters": "``radius`` optional. Neighbour subgraphs use hop distance, not metres.",
        "output_fields": "Graph Layer. Node attribute ``local_efficiency`` (Latora–Marchiori).",
        "sensitivity": "A radius cutoff changes which neighbours are considered.",
        "failure": "Missing network extra raises. Isolated nodes get 0.",
    },
    "imagery.read": {
        "parameters": "``source`` is a GeoTIFF path or Layer. Nodata follows the file tags.",
        "output_fields": "Raster Layer with CRS, transform, band names, and nodata in metadata.",
        "sensitivity": "Opening a different overview level changes the preview, not the values.",
        "failure": "Missing file raises. Missing ``imagery`` extra raises MissingExtraError.",
    },
    "imagery.fetch": {
        "parameters": (
            "``bbox`` or place, ``collection`` (Sentinel-2 L2A or DEM), "
            "``datetime``, ``max_cloud``, ``max_pixels``."
        ),
        "output_fields": "Raster Layer windowed to the bbox. Item ID and license are stamped.",
        "sensitivity": "A different date or cloud threshold selects a different STAC item.",
        "failure": "No item in the window raises. Pixel-budget overflow raises.",
    },
    "imagery.slope": {
        "parameters": (
            "DEM Layer or GeoTIFF. Computed in a metric CRS. Output unit degrees. "
            "Nodata cells stay nodata."
        ),
        "output_fields": "Raster Layer ``slope``. Resolution follows the DEM (30 m here).",
        "sensitivity": "A building DSM is not a substitute; this is terrain.",
        "failure": "Missing DEM band raises. Geographic pixels are reprojected first.",
    },
    "imagery.aspect": {
        "parameters": "DEM Layer. Aspect is clockwise from north. Flat cells are nodata.",
        "output_fields": "Raster Layer ``aspect`` in degrees 0–360.",
        "sensitivity": "A tiny slope change near flat can swing aspect by 180°.",
        "failure": "Missing DEM raises. Use a cyclic colormap; 0 and 360 are the same facing.",
    },
    "imagery.hillshade": {
        "parameters": "``azimuth`` and ``altitude`` are assumed illumination angles, not solar position.",
        "output_fields": "Raster Layer hillshade 0–255.",
        "sensitivity": "Changing azimuth rotates the shading; it is not solar access.",
        "failure": "Missing DEM raises.",
    },
    "imagery.zonal_stats": {
        "parameters": (
            "``raster`` plus polygon ``zones``. Statistic default mean. "
            "Zones are reprojected onto the raster CRS."
        ),
        "output_fields": "Vector Layer with the statistic column and a coverage fraction.",
        "sensitivity": "Small parks relative to 10 m pixels have low coverage.",
        "failure": "Empty zones raise. CRS mismatch is reprojected, not silently ignored.",
    },
    "streetview.filename": {
        "parameters": "``folder`` of image files. No model, no scores.",
        "output_fields": "DataFrame with Filename and path. Not a spatial sample.",
        "sensitivity": "Hidden files are ignored; extension filter is image types.",
        "failure": "Missing folder raises.",
    },
    "streetview.color": {
        "parameters": "Catalog plus ``folder_path``. OpenCV Colorfulness and related pixel stats.",
        "output_fields": "DataFrame columns include Colorfulness. Unit is a pixel statistic.",
        "sensitivity": "JPEG compression and crop change Colorfulness more than the formula.",
        "failure": "Unreadable images are skipped or raise depending on OpenCV.",
        "spatial_support": (
            "Native support: image and geotagged observation point. "
            "Fusion support: grid mean only when coverage is sufficient."
        ),
    },
    "streetview.as_layer": {
        "parameters": "Table with lon/lat columns. Rows without coordinates are dropped.",
        "output_fields": "Point Layer. CRS EPSG:4326 unless given.",
        "sensitivity": "Illustrative (non-geotagged) points must stay labelled as such.",
        "failure": "All-missing coordinates raise or return an empty layer.",
    },
    "fusion.combine": {
        "parameters": (
            "Two or more IndicatorResults. They must share city_id, units, CRS, and scheme."
        ),
        "output_fields": "One long IndicatorResult. combine does not re-aggregate.",
        "sensitivity": "Mismatched unit IDs raise; they are not silently outer-joined.",
        "failure": "Different grids or CRS raise ContractError.",
    },
    "core.load": {
        "parameters": "``path`` to a City directory. ``layers`` optional. ``lazy=True`` avoids opening rasters.",
        "output_fields": "City with Layer inventory, CRS, and stamps.",
        "sensitivity": "lazy=True copies files on save without decoding rasters first.",
        "failure": "Missing manifest raises. Unknown layer names raise.",
    },
    "core.fetch": {
        "parameters": "``place`` or bbox plus modality presets. ``on_error`` can keep partial success.",
        "output_fields": "City directory. This recipe uses the committed pocket, not a live Overpass call.",
        "sensitivity": "Live OSM and STAC change daily; the figure is the fixture.",
        "failure": "Network errors raise unless ``on_error`` swallows them.",
    },
    "core.study_area": {
        "parameters": "``xmin, ymin, xmax, ymax`` in lon/lat. Optional ``place`` and ``city_id``.",
        "output_fields": "StudyArea with geographic CRS, metric CRS, and bbox.",
        "sensitivity": "Metric CRS is derived from the centre, not from a national grid name.",
        "failure": "Inverted bbox raises.",
    },
}


def render(item: dict) -> str:
    method, how = COPY.get(item["id"], ("See the script.", "See the figure."))
    teach = TEACHING.get(item["id"], {})
    recipe = item["recipe"]
    figure = item["figure"]
    script = f"examples/recipes/{recipe}.py"
    depth = 4 + recipe.count("/")
    include = "../" * depth + script
    image = "../" * (2 + recipe.count("/")) + f"_static/{figure}"
    limitations = "\n".join(f"- {line}" for line in item.get("limitations") or [])
    parameters = teach.get(
        "parameters",
        f"See the signature of ``{item['function']}`` in the API reference. "
        "The recipe uses the committed fixture and does not hard-code result values.",
    )
    output_fields = teach.get(
        "output_fields",
        f"{item.get('output')}. Unit: {item.get('unit')}.",
    )
    sensitivity = teach.get(
        "sensitivity",
        "Change one parameter at a time (radius, cell size, date) and compare coverage.",
    )
    failure = teach.get(
        "failure",
        "Missing extras raise ``MissingExtraError``. Invalid parameters raise ``ValueError``.",
    )
    support = teach.get("spatial_support") or _default_support(item)
    return f"""{item['function']}
{'=' * len(item['function'])}

Urban question
--------------

{item['urban_question']}

Real case
---------

- Dataset: ``{item.get('dataset')}``
- Domain: {item.get('domain')}
- Extra: ``urbancode[{item.get('extra')}]``
- Offline: {item.get('offline')}

Command
-------

.. code-block:: python

   {item['function']}(...)

Inputs
------

{item.get('input')}

Spatial support
---------------

{support}

Parameters
----------

{parameters}

Method
------

{method}

Backend: ``{item.get('backend')}``. Output unit: ``{item.get('unit')}``.

Output
------

{output_fields}

Figure
------

.. figure:: {image}
   :alt: {item['function']} result for the registered dataset
   :width: 100%

   Output of ``{item['function']}`` on dataset ``{item.get('dataset')}``.
   Unit: {item.get('unit')}. Backend: {item.get('backend')}.

How to read
-----------

{how}

Parameters and sensitivity
--------------------------

{sensitivity}

Failure modes
-------------

{failure}

Limitations
-----------

{limitations}

Complete script
---------------

.. literalinclude:: {include}
   :language: python
   :caption: {script}

Related pages
-------------

- Domain: :doc:`{DOMAIN_DOC.get(item.get('domain'), '/domains/index')}`
- API: :doc:`{API_DOC.get(item.get('domain'), '/reference/api/index')}`
- Workflow: :doc:`/{item.get('workflow')}`
- Dataset: :doc:`/reference/datasets`
- Catalog: :doc:`/reference/capabilities`
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    written = []
    seen_recipes: set[str] = set()
    for item in analysis_items(load_catalog()):
        if is_blocked(item) or not item.get("recipe"):
            continue
        recipe_id = item["recipe"]
        if recipe_id in seen_recipes:
            continue
        seen_recipes.add(recipe_id)
        rst = recipe_rst(item)
        py = recipe_py(item)
        if rst is None or py is None or not py.is_file():
            continue
        text = render(item)
        if args.check:
            current = rst.read_text(encoding="utf-8") if rst.is_file() else ""
            if current != text:
                print(f"stale {rst.relative_to(ROOT)}")
                return 1
            continue
        rst.parent.mkdir(parents=True, exist_ok=True)
        rst.write_text(text, encoding="utf-8")
        written.append(rst)
    if not args.check:
        _update_indexes(written)
        print(f"wrote {len(written)} recipe pages")
    else:
        print("recipe RST ok")
    return 0


def _update_indexes(written: list[Path]) -> None:
    by_domain: dict[str, list[str]] = {}
    for path in written:
        rel = path.relative_to(ROOT / "docs" / "source" / "reference" / "recipes")
        domain = rel.parts[0]
        by_domain.setdefault(domain, []).append(rel.stem)
    titles = {
        "core": "Core recipes",
        "units": "Analysis-unit recipes",
        "network": "Network recipes",
        "imagery": "Imagery recipes",
        "climate": "Climate recipes",
        "streetview": "Street-view recipes",
        "fusion": "Fusion recipes",
        "cli": "CLI recipes",
    }
    for domain, names in by_domain.items():
        index = ROOT / "docs" / "source" / "reference" / "recipes" / domain / "index.rst"
        lines = [
            titles.get(domain, domain),
            "=" * len(titles.get(domain, domain)),
            "",
            ".. toctree::",
            "   :maxdepth: 1",
            "",
        ]
        for name in sorted(set(names)):
            if name == "index":
                continue
            lines.append(f"   {name}")
        lines.append("")
        index.write_text("\n".join(lines), encoding="utf-8")


def _default_support(item: dict) -> str:
    domain = item.get("domain")
    mapping = {
        "network": (
            "Native support: street graph nodes/edges. Recipe figure shows "
            "the graph. Fusion to a 250 m grid is optional and only after "
            "``uc.fusion.aggregate``."
        ),
        "imagery": (
            "Native support: raster pixels (10 m Sentinel-2 or 30 m DEM). "
            "Recipe figure is the native raster. Grid means appear only in "
            "fusion workflows."
        ),
        "streetview": (
            "Native support: image and geotagged point. Grid means are used "
            "only when coverage is sufficient."
        ),
        "climate": (
            "Native support: climate raster or point field. Analysis-unit "
            "means are a fusion step."
        ),
        "fusion": (
            "Output support: AnalysisUnits (grid/hex/polygons). Context "
            "layers (streets, buildings, water) should remain visible."
        ),
        "units": (
            "Output support: AnalysisUnits. These are a comparison frame, "
            "not a replacement for streets or buildings."
        ),
        "vector": (
            "Native support: OSM footprints, parks, and points. Do not "
            "aggregate before the vector map is shown."
        ),
    }
    return mapping.get(
        domain,
        "See :doc:`/concepts/spatial_support_and_maps` for native vs aggregated geometry.",
    )


if __name__ == "__main__":
    sys.exit(main())
