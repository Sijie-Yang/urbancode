uc.fusion.aggregate
===================

Urban question
--------------

What does each analysis unit receive from this layer?

Real case
---------

- Dataset: ``punggol``
- Domain: fusion
- Extra: ``urbancode[vector]``
- Offline: True

Copy this
---------

.. code-block:: python

   import urbancode as uc

   city = uc.load("examples/data/real/punggol", lazy=True)
   units = uc.units.grid(city, cell_size=250)
   ndvi = uc.imagery.ndvi(city.layers["sentinel2"])
   result = uc.fusion.aggregate(ndvi, units, stat="mean", indicator="ndvi")
   result.plot(indicator="ndvi")

``units`` is the 250 m target grid, ``ndvi`` is the native raster, and ``result`` is an :class:`~urbancode.indicators.IndicatorResult` with one NDVI value and coverage field per unit.

The figure below is the output for the committed fixture. Live-source
recipes can return different timestamps or inventories.

.. figure:: ../../../_static/recipes/fusion/aggregate_punggol.png
   :alt: uc.fusion.aggregate result for the registered dataset
   :width: 100%

   Output of ``uc.fusion.aggregate`` on dataset ``punggol``.
   Unit: stat-dependent. Backend: geopandas.

Inputs
------

Layer plus AnalysisUnits

Spatial support
---------------

Output support: AnalysisUnits (grid/hex/polygons). Context layers (streets, buildings, water) should remain visible.

Parameters
----------

``stat``: mean, min, max, median, p50, sum, count, weighted_mean, coverage, area_fraction, length_density, presence, nearest_distance.

``indicator``: output name. ``column``: vector/graph value column.

Method
------

Summarize a Layer onto AnalysisUnits. Missing stays null.

Backend: ``geopandas``. Output unit: ``stat-dependent``.

Output
------

IndicatorResult with value, coverage, unit, quality_flags, provenance.

How to read
-----------

Read value together with coverage: a high value on low coverage is thin.

Parameters and sensitivity
--------------------------

Changing units (100 m vs 250 m) moves means (MAUP).

Failure modes
-------------

Unknown stat raises. Mixed geometry types can break overlay.

Limitations
-----------

- coverage is the fraction of the unit that intersected the source
- missing stays null, not zero

Related pages
-------------

- Domain: :doc:`/domains/fusion`
- API: :doc:`/reference/api/fusion`
- Workflow: :doc:`/workflows/punggol_urban_profile`
- Dataset: :doc:`/reference/datasets`
- Catalog: :doc:`/reference/capabilities`
