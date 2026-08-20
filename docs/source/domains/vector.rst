Vector
======

Urban question
--------------

Where are streets, buildings, parks, and POIs in the Punggol 2 km
pocket, and how do they become unit-level counts and area fractions?

Result first
------------

.. figure:: /_static/recipes/cli/fetch.png
   :alt: Punggol streets, buildings, and parks from the committed OSM extract
   :width: 100%

   OSM streets, buildings, and parks clipped to the Punggol pocket
   (ODbL). This is the City layout ``uc.load`` / ``uc.fetch`` write.

What you will learn
-------------------

* UrbanCode vector entry points: ``uc.load``, ``uc.fetch``, City, Layer.
* What GeoPandas, Shapely, and pyproj do underneath.
* How buildings, parks, and POIs aggregate onto units.
* Native footprints come first; the grid is later
  (:doc:`/concepts/spatial_support_and_maps`).
* When to drop to ``layer.data``.

Dataset
-------

.. list-table::
   :header-rows: 1
   :widths: 24 76

   * - Field
     - Value
   * - City
     - Punggol, Singapore
   * - Layers
     - ``streets``, ``buildings``, ``parks``, ``pois``
   * - Source
     - OpenStreetMap
   * - License
     - ODbL 1.0
   * - CRS
     - EPSG:4326 stored; metric work in EPSG:32648
   * - Fixture
     - ``examples/data/real/punggol/layers/*.gpkg``
   * - Kind
     - observed OSM tags, clipped to the pocket

Installation
------------

::

   pip install "urbancode[vector]"

``uc.network.fetch`` also needs ``urbancode[network]``.

UrbanCode API
-------------

* :func:`urbancode.city.load` / :func:`urbancode.fetch.fetch`
* :class:`urbancode.city.City` / :class:`urbancode.city.Layer`
* :func:`urbancode.fusion.aggregate` with ``count``, ``area_fraction``,
  ``presence``

UrbanCode does not publish ``overlay()`` or ``buffer()``. Those stay
on GeoPandas / Shapely via ``layer.data``.

Backend stack
-------------

.. list-table::
   :header-rows: 1
   :widths: 20 24 20 18 18

   * - Package
     - Responsibility
     - Called by UrbanCode
     - Direct use needed?
     - Status
   * - GeoPandas
     - GeoDataFrame, join, overlay, clip
     - load, aggregate
     - Yes, custom geometry
     - integrated
   * - Shapely
     - predicates, buffer, intersection
     - units, aggregate
     - Yes
     - integrated
   * - pyproj
     - CRS
     - StudyArea, units
     - Rarely
     - integrated
   * - pyogrio / GDAL
     - vector I/O
     - City I/O
     - Rarely
     - integrated
   * - pandas
     - attribute tables
     - combine
     - Yes
     - integrated
   * - DuckDB Spatial
     - large local SQL
     - no
     - Yes
     - roadmap
   * - H3 / h3-py
     - global discrete grid
     - no
     - Yes
     - roadmap

Step-by-step
------------

Load the pocket and plot source layers::

   import urbancode as uc
   city = uc.load("examples/data/real/punggol", layers=["buildings", "parks", "pois"])

.. figure:: /_static/recipes/units/units_punggol.png
   :alt: Grid, hexgrid, and park polygons as analysis units
   :width: 100%

   Parks as ``from_layer`` units, beside the regular grid. Clipping
   is to the 2 km study area, not the city boundary.

Aggregate examples (see the fusion recipe for the runnable script):

* building count → ``stat="count"``
* park area fraction → ``stat="area_fraction"``
* POI count → ``stat="count"``

Reading the result
------------------

* Park polygons follow OSM ``leisure`` / ``natural`` tags, not a
  parks department inventory.
* Building footprints are OSM completeness, not a cadastral stock.
* POIs are sparse and tag-biased.

Limitations
-----------

* OSM timestamp is the extract date.
* Mixed geometry types must be filtered before overlay (the
  multi-city workflow keeps polygons only).
* DuckDB, PostGIS, and H3 are not UrbanCode APIs.

Related pages
-------------

* Recipes: :doc:`/reference/recipes/core/city_roundtrip_punggol`,
  :doc:`/reference/recipes/fusion/aggregate_punggol`
* Workflow: :doc:`/workflows/punggol_urban_profile`
* API: :doc:`/reference/api/city`
* Upstream: `GeoPandas <https://geopandas.org/>`__,
  `Shapely <https://shapely.readthedocs.io/>`__

Use UrbanCode when the vector layers are one step in a reproducible
City workflow.
Use GeoPandas / Shapely when you need custom geometry operations.
Use DuckDB or PostGIS when the extract no longer fits in memory.
