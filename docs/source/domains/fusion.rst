Fusion
======

Urban question
--------------

How do Punggol rasters, graphs, parks, and points land on the same
250 m units?

Result first
------------

.. figure:: /_static/recipes/fusion/aggregate_punggol.png
   :alt: Six aggregate statistics on the Punggol 250 m grid
   :width: 100%

   ``uc.fusion.aggregate`` summaries on the committed 250 m grid.
   Read each value with its coverage.

What you will learn
-------------------

* Vector → units, raster → units, and graph/points → units.
* The statistics the code actually implements.
* What ``combine`` checks and what it does not do.

Installation
------------

::

   pip install "urbancode[vector]"

This installs the vector overlay needed by fusion. Add the extra for
each source modality whose layers you aggregate.

Network and imagery layers still need their extras.

UrbanCode API
-------------

* :func:`urbancode.fusion.aggregate`
* :func:`urbancode.fusion.combine`

Fusion is not a DataFrame ``merge``. It is a spatial alignment
plus a typed indicator table.

::

   import urbancode as uc

   city = uc.load("examples/data/real/punggol", lazy=True)
   units = uc.units.grid(city, cell_size=250)
   ndvi = uc.imagery.ndvi(city.layers["sentinel2"])
   result = uc.fusion.aggregate(ndvi, units, stat="mean", indicator="ndvi")
   print(len(result.records), round(float(result.to_pandas()["value"].mean()), 3))
   result.plot(indicator="ndvi")

::

   81 0.208

``units`` is the target grid, ``ndvi`` is the native raster, and
``result`` is an ``IndicatorResult`` with 81 values plus coverage and
provenance. The plot reads geometry from ``units``; it does not alter
the raster.

Backend stack
-------------

.. list-table::
   :header-rows: 1
   :widths: 22 24 22 16 16

   * - Package
     - Responsibility
     - Called by UrbanCode
     - Direct use?
     - Status
   * - GeoPandas
     - spatial join, overlay
     - vector aggregate
     - Yes
     - integrated
   * - Shapely
     - predicates, distance
     - nearest_distance
     - Yes
     - integrated
   * - Rasterio / rioxarray
     - zonal sampling
     - raster aggregate
     - Yes
     - integrated
   * - pandas
     - table concat
     - combine
     - Yes
     - integrated
   * - NetworkX
     - node/edge coordinates
     - graph aggregate
     - Yes
     - integrated

Supported statistics
--------------------

Value stats: ``mean``, ``min``, ``max``, ``median``, ``p50``,
``sum``, ``count``, ``weighted_mean``.

Geometry stats: ``coverage``, ``area_fraction``, ``length_density``,
``presence``, ``nearest_distance``.

Unknown names raise. There is no hidden ``mode`` or kriging stat.

Coverage rules
--------------

* raster — valid-pixel fraction
* points / graph — 1 if any observation, else 0
* polygons — intersection area / cell area

Missing stays null, not zero, except where a geometry stat is
defined as 0 (presence / count / area_fraction / length_density
on an empty cell).

combine
-------

.. figure:: /_static/recipes/fusion/combine_punggol.png
   :alt: Combined NDVI IndicatorResult on the Punggol grid
   :width: 100%

   ``combine`` concatenates IndicatorResults that already share
   units. It checks ``city_id``, unit IDs, CRS, and scheme. It does
   not spatially re-aggregate. Duplicate columns follow the
   IndicatorResult ``on_duplicate`` policy.

Reading the result
------------------

* A high NDVI on low coverage is a thin sample.
* Park ``area_fraction`` near 1 means the cell is mostly park
  polygon, not that the park is high quality.
* Combined tables are long: one row per indicator.

Limitations
-----------

* Mixed geometry types in a GeoDataFrame can break overlay; filter
  to polygons first.
* ``combine`` will not fix mismatched grids.
* Cross-city comparison still needs the same unit constructor.

Related pages
-------------

* Recipes: :doc:`/reference/recipes/fusion/aggregate_punggol`,
  :doc:`/reference/recipes/fusion/combine_punggol`
* Workflows: :doc:`/workflows/punggol_urban_profile`,
  :doc:`/workflows/green_accessibility`
* Concepts: :doc:`/concepts/analysis_units`, :doc:`/concepts/indicators`
* API: :doc:`/reference/api/fusion`

Use UrbanCode when several modalities must share unit IDs.
Use GeoPandas directly when you are joining two frames that already
share a key.
