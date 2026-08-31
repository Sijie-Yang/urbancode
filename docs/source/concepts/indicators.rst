Indicators
==========

Urban question
--------------

How can a satellite index and a street-network count share one
export format?

Result first
------------

.. figure:: /_static/recipes/core/indicator_result_punggol.png
   :alt: IndicatorResult table and map for Punggol NDVI
   :width: 100%

   An ``IndicatorResult`` is a long table plus the unit geometries.
   The map is ``plot(indicator=...)``.

What you will learn
-------------------

* The fields on ``IndicatorRecord`` / ``IndicatorResult``.
* Why NDVI and reachability can be combined.
* How to export pandas, GeoPandas, or a City Layer.

The contract
------------

Each record has:

* ``city_id``, ``unit_id``
* ``indicator`` name
* ``value`` and ``units``
* ``coverage`` in ``[0, 1]`` or null
* ``method``, ``parameters``
* source layers and provenance
* optional quality flags

After the Punggol script aggregates NDVI and reachability, the table
has one row per ``(city_id, unit_id, indicator)``. Duplicate keys
raise unless you pass ``on_duplicate``.
``plot(indicator="ndvi")`` is required when two indicators are present.

Two modalities, one table
-------------------------

* ``uc.imagery.ndvi`` returns a raster Layer. Values are
  dimensionless reflectance ratios on one date.
* ``uc.network.accessibility`` returns a graph Layer. Values are
  node counts inside a length cutoff.
* ``uc.fusion.aggregate`` writes both onto the same
  ``AnalysisUnits``. ``uc.fusion.combine`` concatenates the tables
  after checking ``city_id``, unit IDs, CRS, and scheme.

The shared object is the unit ID, not the original pixel or node.

Try it::

   import urbancode as uc

   city = uc.load("examples/data/real/punggol", lazy=True)
   units = uc.units.grid(city, cell_size=250)
   result = uc.fusion.aggregate(
       uc.imagery.ndvi(city.layers["sentinel2"]),
       units, stat="mean", indicator="ndvi",
   )
   rec = result.records[0]
   print(rec.indicator, round(rec.value, 3), rec.coverage)

::

   ndvi 0.146 1.0

Export
------

:class:`urbancode.indicators.IndicatorResult` supports
``to_pandas``, ``to_geopandas``, ``to_xarray``, ``to_layer``,
``plot``, ``save``, and ``load``. ``save`` writes CSV, optional
parquet, ``units.gpkg``, and receipts.

Related pages
-------------

* Concept: :doc:`provenance_quality`
* Domain: :doc:`/domains/fusion`
* API: :doc:`/reference/api/indicators`
* Recipe: :doc:`/reference/recipes/fusion/combine_punggol`

Use UrbanCode when the deliverable is a typed indicator table.
Use pandas directly when you already have that table and only need
a join.
