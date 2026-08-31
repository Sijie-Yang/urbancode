uc.fusion.aggregate_many
========================

Urban question
--------------

How do many perception columns become one indicator table?

Real case
---------

- Dataset: ``streetview``
- Domain: fusion
- Extra: ``urbancode[vector]``
- Offline: True

Copy this
---------

.. code-block:: python

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

``photos`` is the point observation layer and ``units`` is the target grid. ``result`` is a long :class:`~urbancode.indicators.IndicatorResult` containing the requested summaries for each populated unit.

The figure below is the output for the committed fixture. Live-source
recipes can return different timestamps or inventories.

.. figure:: ../../../_static/recipes/fusion/aggregate_many_punggol.png
   :alt: uc.fusion.aggregate_many result for the registered dataset
   :width: 100%

   Output of ``uc.fusion.aggregate_many`` on dataset ``streetview``.
   Unit: mixed. Backend: geopandas.

Inputs
------

Layer plus column map plus AnalysisUnits

Spatial support
---------------

Output support: AnalysisUnits (grid/hex/polygons). Context layers (streets, buildings, water) should remain visible.

Parameters
----------

See the signature of ``uc.fusion.aggregate_many`` in the API reference. The recipe uses the committed fixture and does not hard-code result values.

Method
------

Aggregates several columns from one Layer, then combines them.

Backend: ``geopandas``. Output unit: ``mixed``.

Output
------

IndicatorResult. Unit: mixed.

How to read
-----------

Units with no photos stay null, not zero.

Parameters and sensitivity
--------------------------

Change one parameter at a time (radius, cell size, date) and compare coverage.

Failure modes
-------------

Missing extras raise ``MissingExtraError``. Invalid parameters raise ``ValueError``.

Limitations
-----------

- each column is aggregated separately, then combined
- units with no photos stay null, not zero

Related pages
-------------

- Domain: :doc:`/domains/fusion`
- API: :doc:`/reference/api/fusion`
- Workflow: :doc:`/workflows/research_cases/thermal_comfort_in_sight`
- Dataset: :doc:`/reference/datasets`
- Catalog: :doc:`/reference/capabilities`
