StudyArea, City, and Layer
==========================

Urban question
--------------

What objects hold the study boundary, the multimodal layers, and the
raw GIS payload?

Result first
------------

.. figure:: /_static/recipes/core/study_area_punggol.png
   :alt: Punggol StudyArea envelope with the walk network
   :width: 100%

   Punggol 2 km pocket. The envelope is ``StudyArea.from_bbox``;
   the streets are a graph Layer inside a City.

What you will learn
-------------------

* ``StudyArea`` stores the boundary and the canonical metric CRS.
* ``City`` is the container for named Layers in one study area.
* ``Layer`` adapts vector, raster, graph, table, or image payloads.
* ``layer.data`` is not always a GeoDataFrame.

Object relations
----------------

::

   StudyArea  (bbox, geographic_crs, metric_crs, city_id)
        │
        ▼
      City    (manifest, layers, optional area/)
        │
        ├── Layer(kind="vector")  → GeoDataFrame
        ├── Layer(kind="raster")  → path / Xarray
        ├── Layer(kind="graph")   → NetworkX MultiDiGraph
        ├── Layer(kind="table")   → DataFrame
        └── Layer(kind="images")  → file list

StudyArea
---------

``StudyArea.from_bbox(west, south, east, north)`` expects lon/lat
unless you pass a projected ``crs=``. Numbers outside the geographic
range are never treated as lon/lat. The object keeps:

* ``city_id``, ``place``, ``bbox``
* ``geographic_crs`` (usually EPSG:4326)
* ``metric_crs`` (UTM derived from the centre, EPSG:32648 for Punggol)
* optional boundary geometry

Also available: ``from_geometry`` and ``from_place``.

City
----

A City directory has ``manifest.json``, ``layers/``, and optional
``area/``. ``uc.load(..., lazy=True)`` records paths without opening
every raster. ``city["streets"]`` is the graph payload.
``city.layer("streets")`` is the Layer with metadata.

Layer
-----

A Layer is one named payload. Required metadata includes ``name``,
``kind``, ``crs`` when known, ``source``, and a provenance stamp.
Do not assume every layer is a GeoDataFrame:

.. list-table::
   :header-rows: 1
   :widths: 20 40 40

   * - kind
     - ``.data`` / access
     - Typical backend
   * - vector
     - GeoDataFrame
     - GeoPandas
   * - raster
     - path or Xarray
     - Rasterio / rioxarray
   * - graph
     - ``city["streets"]`` MultiDiGraph
     - NetworkX / OSMnx
   * - table
     - DataFrame
     - pandas
   * - images
     - directory + catalog
     - Pillow / OpenCV

Escape hatch: use ``layer.data`` (or the graph) and call GeoPandas,
OSMnx, or Rasterio directly.

Related pages
-------------

* Quickstart: :doc:`/getting_started/quickstart`
* API: :doc:`/reference/api/city`
* Recipes: :doc:`/reference/recipes/core/study_area_punggol`,
  :doc:`/reference/recipes/core/city_roundtrip_punggol`
* Functions: :func:`urbancode.city.load`, :func:`urbancode.fetch.fetch`

Use UrbanCode when you need one container for several modalities.
Use GeoPandas directly when you already have a single GeoDataFrame
and no City contract.
