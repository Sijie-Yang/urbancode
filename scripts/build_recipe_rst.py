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

# These notes sit directly below the runnable block.  They deliberately name
# the variables a reader will see in the snippet; a generic "print the object"
# instruction made the old recipe pages look complete while leaving the code
# unexplained.
EXAMPLE_NOTES = {
    "core.load": (
        "``city`` is the lazily loaded :class:`~urbancode.city.City`. The call "
        "to ``city.plot`` renders three existing layers; it does not download or "
        "modify data."
    ),
    "core.fetch": (
        "``city`` is the downloaded :class:`~urbancode.city.City`. Because this "
        "is a live call, its layer inventory and OSM/STAC timestamps can differ "
        "from the committed figure below."
    ),
    "core.study_area": (
        "``city.study_area.bbox`` is the stored west/south/east/north envelope. "
        "``area`` is a new :class:`~urbancode.area.StudyArea` built from the same "
        "coordinates; no layers are copied into it."
    ),
    "network.fetch": (
        "``streets`` is the graph :class:`~urbancode.city.Layer` already stored "
        "in ``city``. ``streets.plot()`` draws the graph in native support; the "
        "code does not aggregate it to a grid."
    ),
    "network.centrality": (
        "``between`` is a graph :class:`~urbancode.city.Layer`. Its NetworkX "
        "nodes carry a new ``betweenness`` attribute; ``between.plot()`` colours "
        "the native nodes/edges by that value."
    ),
    "network.accessibility": (
        "``reach`` is a graph :class:`~urbancode.city.Layer`. Each node gets a "
        "``reachability`` count of other nodes within 150 m of network length; "
        "``reach.plot()`` stays on graph nodes rather than grid cells."
    ),
    "network.clustering": (
        "``cluster`` is a graph :class:`~urbancode.city.Layer` whose nodes carry "
        "the dimensionless ``clustering`` coefficient. The plot is node-level."
    ),
    "network.local_efficiency": (
        "``eff`` is a graph :class:`~urbancode.city.Layer` whose nodes carry "
        "``local_efficiency``. The value describes neighbour redundancy, not "
        "travel speed."
    ),
    "imagery.read": (
        "``raster`` is a raster :class:`~urbancode.city.Layer` opened from the "
        "GeoTIFF path. It retains the file CRS, transform, bands, and nodata; "
        "``raster.plot()`` only renders those stored values."
    ),
    "imagery.fetch": (
        "``city`` is the live imagery result. The STAC item, acquisition date, "
        "cloud filter, and asset URLs are recorded in layer metadata; the figure "
        "below uses the pinned offline item instead."
    ),
    "imagery.ndvi": (
        "``ndvi`` is a dimensionless raster :class:`~urbancode.city.Layer` on "
        "the Sentinel-2 pixel grid. ``ndvi.plot()`` shows pixels, not 250 m "
        "analysis units."
    ),
    "imagery.ndwi": (
        "``ndwi`` is a dimensionless raster :class:`~urbancode.city.Layer` on "
        "the Sentinel-2 pixel grid. Positive pixels are water candidates, not "
        "validated water polygons."
    ),
    "imagery.ndbi": (
        "``ndbi`` is a dimensionless raster :class:`~urbancode.city.Layer` on "
        "the Sentinel-2 pixel grid. High values can represent built-up surface "
        "or bare soil."
    ),
    "imagery.slope": (
        "``slope`` is a raster :class:`~urbancode.city.Layer` in degrees, derived "
        "from ``city.layers['dem']``. It follows the DEM grid and nodata mask."
    ),
    "imagery.aspect": (
        "``aspect`` is a raster :class:`~urbancode.city.Layer` in degrees "
        "clockwise from north. Flat DEM cells remain nodata."
    ),
    "imagery.hillshade": (
        "``shade`` is a 0--255 raster :class:`~urbancode.city.Layer`. It visualises "
        "relief under assumed illumination and is not a solar-access result."
    ),
    "imagery.zonal_stats": (
        "``units`` contains the 250 m polygons, ``ndvi`` contains native pixels, "
        "and ``stats`` is a vector :class:`~urbancode.city.Layer` with one row per "
        "zone and the requested raster summaries."
    ),
    "climate.utci": (
        "``utci`` is a scalar UTCI value in degrees Celsius. Here ``tdb`` is air "
        "temperature, ``rh`` is relative humidity in percent, and ``v`` is wind "
        "speed in m/s; radiant temperature defaults to air temperature."
    ),
    "streetview.filename": (
        "``table`` is a pandas DataFrame with one row per discovered image file. "
        "It contains filenames and paths only--no coordinates or perception "
        "scores are inferred."
    ),
    "streetview.color": (
        "``table`` is the input file catalog. ``color`` is a copy augmented with "
        "pixel-statistic columns such as ``Colorfulness``; these are image-level "
        "features, not comfort measurements."
    ),
    "images.from_table": (
        "``catalog`` is the three-city source table. ``photos`` is the eight-row "
        "Punggol point :class:`~urbancode.city.Layer`; ``n_images`` counts catalog "
        "rows and ``photos.plot()`` maps their coordinates."
    ),
    "streetview.as_layer": (
        "``catalog`` is filtered to Punggol before conversion. ``photos`` is an "
        "eight-row point :class:`~urbancode.city.Layer`; rows without usable "
        "coordinates are not invented."
    ),
    "perception.thermal_affordance": (
        "``photos`` is the geolocated input image layer. ``vata`` is a point "
        ":class:`~urbancode.city.Layer` with TCIS VATA/VPI model outputs attached "
        "to each successfully scored image."
    ),
    "fusion.aggregate": (
        "``units`` is the 250 m target grid, ``ndvi`` is the native raster, and "
        "``result`` is an :class:`~urbancode.indicators.IndicatorResult` with one "
        "NDVI value and coverage field per unit."
    ),
    "fusion.aggregate_many": (
        "``photos`` is the point observation layer and ``units`` is the target "
        "grid. ``result`` is a long :class:`~urbancode.indicators.IndicatorResult` "
        "containing the requested summaries for each populated unit."
    ),
    "fusion.combine": (
        "``ndvi`` and ``reach`` are already aggregated IndicatorResults on the "
        "same ``units``. ``result`` concatenates their records; ``combine`` does "
        "not resample either source."
    ),
    "units.grid": (
        "``units`` is an :class:`~urbancode.units.AnalysisUnits` object. "
        "``units.frame`` contains clipped 250 m polygons with stable ``unit_id`` "
        "values in the reported metric CRS."
    ),
    "units.hexgrid": (
        "``units`` is an :class:`~urbancode.units.AnalysisUnits` object containing "
        "clipped pointy-top hexagons. ``cell_size`` is centre-to-vertex distance "
        "in metres."
    ),
    "units.from_layer": (
        "``units`` is an :class:`~urbancode.units.AnalysisUnits` object built from "
        "park polygons. Its IDs fingerprint geometry; they are not copied row "
        "numbers."
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
    snippet = _command_snippet(item).lstrip("\n")
    example_note = EXAMPLE_NOTES.get(
        item["id"],
        f"The last assignment is the recipe result: {output_fields}",
    )
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

Copy this
---------

.. code-block:: python

{snippet}

{example_note}

The figure below is the output for the committed fixture. Live-source
recipes can return different timestamps or inventories.

.. figure:: {image}
   :alt: {item['function']} result for the registered dataset
   :width: 100%

   Output of ``{item['function']}`` on dataset ``{item.get('dataset')}``.
   Unit: {item.get('unit')}. Backend: {item.get('backend')}.

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
        "images": "Image-observation recipes",
        "perception": "Perception recipes",
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


def _command_snippet(item: dict) -> str:
    """Short public-API example. Figure builders stay out of the page."""
    snippets = {
        "core.load": """
   import urbancode as uc

   city = uc.load("examples/data/real/punggol", lazy=True)
   city.plot(layers=["streets", "buildings", "parks"])
""",
        "core.fetch": """
   import urbancode as uc

   # Live download. The docs figure uses the committed pocket instead.
   city = uc.fetch("Punggol, Singapore")
""",
        "core.study_area": """
   import urbancode as uc

   city = uc.load("examples/data/real/punggol", lazy=True)
   print(city.study_area.bbox)
   area = uc.StudyArea.from_bbox(
       *city.metadata["bbox"], city_id="punggol"
   )
""",
        "network.fetch": """
   import urbancode as uc

   city = uc.load("examples/data/real/punggol", lazy=True)
   streets = city.layer("streets")
   streets.plot()
""",
        "network.centrality": """
   import urbancode as uc

   city = uc.load("examples/data/real/punggol", lazy=True)
   between = uc.network.centrality(city["streets"], metric="betweenness")
   between.plot()
""",
        "network.accessibility": """
   import urbancode as uc

   city = uc.load("examples/data/real/punggol", lazy=True)
   reach = uc.network.accessibility(
       city["streets"], radius=150, metric="reachability"
   )
   reach.plot()
""",
        "network.clustering": """
   import urbancode as uc

   city = uc.load("examples/data/real/punggol", lazy=True)
   cluster = uc.network.clustering(city["streets"])
   cluster.plot()
""",
        "network.local_efficiency": """
   import urbancode as uc

   city = uc.load("examples/data/real/punggol", lazy=True)
   eff = uc.network.local_efficiency(city["streets"])
   eff.plot()
""",
        "imagery.read": """
   import urbancode as uc

   city = uc.load("examples/data/real/punggol", lazy=True)
   raster = uc.imagery.read(city.layers["sentinel2"].path)
   raster.plot()
""",
        "imagery.fetch": """
   import urbancode as uc

   # Live STAC search. The docs figure uses the committed GeoTIFF.
   city = uc.imagery.fetch(place="Punggol, Singapore")
""",
        "imagery.ndvi": """
   import urbancode as uc

   city = uc.load("examples/data/real/punggol", lazy=True)
   ndvi = uc.imagery.ndvi(city.layers["sentinel2"])
   ndvi.plot()
""",
        "imagery.ndwi": """
   import urbancode as uc

   city = uc.load("examples/data/real/punggol", lazy=True)
   ndwi = uc.imagery.ndwi(city.layers["sentinel2"])
   ndwi.plot()
""",
        "imagery.ndbi": """
   import urbancode as uc

   city = uc.load("examples/data/real/punggol", lazy=True)
   ndbi = uc.imagery.ndbi(city.layers["sentinel2"])
   ndbi.plot()
""",
        "imagery.slope": """
   import urbancode as uc

   city = uc.load("examples/data/real/punggol", lazy=True)
   slope = uc.imagery.slope(city.layers["dem"])
   slope.plot()
""",
        "imagery.aspect": """
   import urbancode as uc

   city = uc.load("examples/data/real/punggol", lazy=True)
   aspect = uc.imagery.aspect(city.layers["dem"])
   aspect.plot()
""",
        "imagery.hillshade": """
   import urbancode as uc

   city = uc.load("examples/data/real/punggol", lazy=True)
   shade = uc.imagery.hillshade(city.layers["dem"])
   shade.plot()
""",
        "imagery.zonal_stats": """
   import urbancode as uc

   city = uc.load("examples/data/real/punggol", lazy=True)
   units = uc.units.grid(city, cell_size=250)
   ndvi = uc.imagery.ndvi(city.layers["sentinel2"])
   stats = uc.imagery.zonal_stats(ndvi, units.frame)
""",
        "climate.utci": """
   import urbancode as uc

   utci = uc.climate.utci(tdb=31.2, rh=74, v=1.8)
   print(float(utci))
""",
        "streetview.filename": """
   import urbancode as uc

   table = uc.svi.filename("examples/data/real/streetview/punggol")
   print(table.head())
""",
        "streetview.color": """
   import urbancode as uc

   table = uc.svi.filename("examples/data/real/streetview/punggol")
   color = uc.svi.color(
       table, folder_path="examples/data/real/streetview/punggol"
   )
   print(color.head())
""",
        "images.from_table": """
   import pandas as pd
   import urbancode as uc

   catalog = pd.read_json("examples/data/real/streetview/catalog.json")
   photos = uc.images.from_table(
       catalog[catalog["city_id"] == "punggol"],
       view_type="streetview",
       image_root="examples/data/real/streetview",
   )
   print(photos.kind, photos.metadata["n_images"])
   photos.plot()
""",
        "streetview.as_layer": """
   import pandas as pd
   import urbancode as uc

   catalog = pd.read_json("examples/data/real/streetview/catalog.json")
   photos = uc.svi.as_layer(catalog[catalog["city_id"] == "punggol"])
   print(photos.kind, photos.metadata["n_images"])
   photos.plot()
""",
        "perception.thermal_affordance": """
   import pandas as pd
   import urbancode as uc

   catalog = pd.read_json("examples/data/real/streetview/catalog.json")
   photos = uc.images.from_table(
       catalog[catalog["city_id"] == "punggol"],
       view_type="streetview",
       image_root="examples/data/real/streetview",
   )
   vata = uc.perception.thermal_affordance(photos)
   vata.plot()
""",
        "fusion.aggregate": """
   import urbancode as uc

   city = uc.load("examples/data/real/punggol", lazy=True)
   units = uc.units.grid(city, cell_size=250)
   ndvi = uc.imagery.ndvi(city.layers["sentinel2"])
   result = uc.fusion.aggregate(ndvi, units, stat="mean", indicator="ndvi")
   result.plot(indicator="ndvi")
""",
        "fusion.aggregate_many": """
   import pandas as pd
   import urbancode as uc

   city = uc.load("examples/data/real/punggol", lazy=True)
   units = uc.units.grid(city, cell_size=250)
   catalog = pd.read_json("examples/data/real/streetview/catalog.json")
   photos = uc.images.from_table(
       catalog[catalog["city_id"] == "punggol"],
       view_type="streetview",
       image_root="examples/data/real/streetview",
   )
   result = uc.fusion.aggregate_many(photos, units, stat="count")
   print(len(result.records))
""",
        "fusion.combine": """
   import urbancode as uc

   city = uc.load("examples/data/real/punggol", lazy=True)
   units = uc.units.grid(city, cell_size=250)
   ndvi = uc.fusion.aggregate(
       uc.imagery.ndvi(city.layers["sentinel2"]),
       units,
       stat="mean",
       indicator="ndvi",
   )
   reach = uc.fusion.aggregate(
       uc.network.accessibility(
           city["streets"], radius=150, metric="reachability"
       ),
       units,
       stat="mean",
       indicator="reachability",
   )
   result = uc.fusion.combine(units, ndvi, reach)
   result.plot(indicator="ndvi")
""",
        "units.grid": """
   import urbancode as uc

   city = uc.load("examples/data/real/punggol", lazy=True)
   units = uc.units.grid(city, cell_size=250)
   print(len(units.frame), units.metric_crs)
""",
        "units.hexgrid": """
   import urbancode as uc

   city = uc.load("examples/data/real/punggol", lazy=True)
   units = uc.units.hexgrid(city, cell_size=250)
   print(len(units.frame), units.kind)
""",
        "units.from_layer": """
   import urbancode as uc

   city = uc.load("examples/data/real/punggol", lazy=True)
   units = uc.units.from_layer(
       city.layer("parks"), study_area=city.study_area
   )
   print(len(units.frame), units.kind)
""",
        "indicators.save": """
   import urbancode as uc

   city = uc.load("examples/data/real/punggol", lazy=True)
   units = uc.units.grid(city, cell_size=250)
   result = uc.fusion.aggregate(
       uc.imagery.ndvi(city.layers["sentinel2"]),
       units,
       stat="mean",
       indicator="ndvi",
   )
   result.save("punggol_indicators")
""",
        "indicators.load": """
   import urbancode as uc

   result = uc.IndicatorResult.load("punggol_indicators")
   print(result.to_pandas().head())
""",
        "indicators.plot": """
   import urbancode as uc

   city = uc.load("examples/data/real/punggol", lazy=True)
   units = uc.units.grid(city, cell_size=250)
   result = uc.fusion.aggregate(
       uc.imagery.ndvi(city.layers["sentinel2"]),
       units,
       stat="mean",
       indicator="ndvi",
   )
   result.plot(indicator="ndvi")
""",
        "indicators.to_layer": """
   import urbancode as uc

   city = uc.load("examples/data/real/punggol", lazy=True)
   units = uc.units.grid(city, cell_size=250)
   result = uc.fusion.aggregate(
       uc.imagery.ndvi(city.layers["sentinel2"]),
       units,
       stat="mean",
       indicator="ndvi",
   )
   layer = result.to_layer(indicator="ndvi")
   layer.plot()
""",
    }
    text = snippets.get(item["id"])
    if text is None:
        text = f"""
   import urbancode as uc

   city = uc.load("examples/data/real/punggol", lazy=True)
   # {item['function']}
"""
    return text.strip("\n")


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
