Your first UrbanCode project
============================

Urban question
--------------

Which 250 m cells in Punggol are greener, and which have a denser
walk graph — and can those two answers share one saved table?

This page assumes you can load the pocket. Clone the repository, install
``urbancode[standard]``, and keep the working directory at the repo
root so ``examples/data/real/punggol`` resolves. The chain is the same
as :doc:`quickstart`. Here you inspect records, save receipts, and try
one sensitivity change.

Result first
------------

.. figure:: /_static/recipes/core/city_roundtrip_punggol.png
   :alt: Punggol City streets and parks after load and round-trip save
   :width: 100%

   Streets and parks from ``examples/data/real/punggol``. This is
   the project container after ``uc.load``.

1. Recap: one combined table
----------------------------

::

   import urbancode as uc

   city = uc.load("examples/data/real/punggol", lazy=True)
   units = uc.units.grid(city, cell_size=250)
   ndvi = uc.fusion.aggregate(
       uc.imagery.ndvi(city.layers["sentinel2"]),
       units, stat="mean", indicator="ndvi",
   )
   reach = uc.fusion.aggregate(
       uc.network.accessibility(
           city["streets"], radius=150, metric="reachability"
       ),
       units, stat="mean", indicator="reachability",
   )
   result = uc.fusion.combine(units, ndvi, reach)

``city`` is the project container, ``units`` is the shared 250 m
frame, and ``ndvi`` / ``reach`` are already aggregated results.
``result`` concatenates 81 records from each indicator; it does not
calculate a correlation between them.

::

   rec = result.records[0]
   print(rec.city_id, rec.indicator, round(rec.value, 3), rec.coverage)

::

   punggol ndvi 0.146 1.0

Fields on every record: ``unit_id``, ``value``, ``coverage``,
``method``, ``parameters``, provenance. A green cell can still have
low reachability; they share ``unit_id``, they are not a cause.

2. Plot one indicator
---------------------

::

   result.plot(indicator="ndvi")

.. figure:: /_static/recipes/fusion/combine_punggol.png
   :alt: NDVI on the Punggol 250 m grid
   :width: 100%

   Combined ``IndicatorResult`` for ``ndvi``. Use
   ``indicator="reachability"`` for the network map. 32 of 81
   reachability cells are null (no street node).

3. Save and reload
------------------

::

   saved = result.save("punggol_indicators")
   again = uc.IndicatorResult.load(saved)
   print(sorted(path.name for path in saved.iterdir()))
   print(again.to_pandas().groupby("indicator")["value"].mean())

::

   ['provenance', 'records.csv', 'result.json', 'units.gpkg']
   indicator
   ndvi             0.208
   reachability    16.030
   Name: value, dtype: float64

``save`` writes ``records.csv``, optional parquet, ``units.gpkg``,
and ``provenance/receipts.jsonl``. Reload with
``IndicatorResult.load``, not a module-level ``load``. Means match
the in-memory table: NDVI 0.208, reachability 16.0.

4. Change one thing
-------------------

::

   hexes = uc.units.hexgrid(city, cell_size=250)
   print(len(units.frame), len(hexes.frame), hexes.kind)

::

   81 38 hexgrid

Hex IDs are not interchangeable with the square grid. That is MAUP:
means move when the unit changes. Try ``cell_size=100`` or
``radius=500`` the same way, one parameter at a time.

Limitations
-----------

* Two indicators on one grid are not a causal claim.
* The pocket is too small for city-wide ranking.
* Street-view and climate are later workflows.

Next: :doc:`choose_your_path`, then
:doc:`/workflows/punggol_urban_profile`.
