Your first UrbanCode project
============================

Urban question
--------------

Which 250 m cells in Punggol are greener, and which have a denser
walk graph — and can those two answers share one table?

Result first
------------

.. figure:: /_static/recipes/core/city_roundtrip_punggol.png
   :alt: Punggol City streets and parks after load and round-trip save
   :width: 100%

   Streets and parks from ``examples/data/real/punggol`` after
   ``uc.load`` and ``City.to_dir``. This is the project container.

What you will learn
-------------------

* Load the real Punggol fixture and attach a StudyArea.
* Build a 250 m grid (or switch to hexgrid later).
* Compute NDVI and network reachability.
* Aggregate both onto the same units and combine them.
* Save the indicator table and provenance receipts.

This page is the bridge from :doc:`quickstart` to
:doc:`/workflows/punggol_urban_profile`.

Dataset
-------

Same fixture as the quickstart: ``examples/data/real/punggol``.
Checksums and licenses are in :doc:`/reference/datasets`.

Installation
------------

::

   pip install "urbancode[standard]"

Step-by-step
------------

Load, grid, NDVI, reachability, aggregate, combine, plot, save:

.. literalinclude:: ../../../examples/workflows/punggol_end_to_end.py
   :language: python
   :start-after: def main
   :end-before: return {

.. figure:: /_static/recipes/fusion/combine_punggol.png
   :alt: NDVI on the Punggol 250 m grid
   :width: 100%

   Combined IndicatorResult plotted for ``ndvi``. Switch the
   ``indicator=`` argument to ``reachability`` for the network map.

.. figure:: /_static/recipes/network/accessibility_punggol.png
   :alt: Network reachability at 150 m and 500 m on the Punggol walk graph
   :width: 100%

   Reachability before aggregation. After ``fusion.aggregate`` the
   values become one number per 250 m cell.

Reading the result
------------------

* High-NDVI cells follow parks and tree cover on 28 July 2024.
* High-reachability cells follow the dense walk graph, often along
  internal streets rather than the water edge.
* Combined rows share ``city_id`` and ``unit_id``. A green cell can
  still have low reachability.

Sensitivity
-----------

Change one thing at a time:

* ``cell_size=100`` or ``500`` — MAUP: means move when the unit changes.
* ``uc.units.hexgrid(city, cell_size=250)`` — IDs are not interchangeable
  with the square grid.
* ``radius=500`` — more nodes per origin; still not population access.

Quality and provenance
----------------------

``IndicatorResult.save`` writes ``records.csv``, optional parquet,
``units.gpkg``, and ``provenance/receipts.jsonl``. Receipts include
the source Layer stamp and an ``aggregate`` step. Coverage below 0.1
is flagged ``low_coverage``. Missing stays null, not zero.

Limitations
-----------

* Two indicators on one grid are not a causal claim.
* The pocket is too small for city-wide ranking.
* Street-view and climate are out of scope here; see the later
  workflows.

Related pages
-------------

* Concepts: :doc:`/concepts/analysis_units`, :doc:`/concepts/indicators`
* Domain: :doc:`/domains/fusion`
* Recipes: :doc:`/reference/recipes/imagery/ndvi_punggol`,
  :doc:`/reference/recipes/network/accessibility_punggol`
* Workflow: :doc:`/workflows/punggol_urban_profile`
* Dataset: :doc:`/reference/datasets`

Use UrbanCode when the deliverable is a reusable indicator table.
Use the upstream package directly when you are still exploring a
single GeoDataFrame or graph.
