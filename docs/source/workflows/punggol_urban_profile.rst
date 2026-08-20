Punggol urban profile
=====================

Urban question
--------------

What does the 2 km Punggol pocket look like as a **core** profile
of vector context, walk-network reachability, NDVI/NDBI, and terrain
on one 250 m grid?

Result first
------------

.. figure:: /_static/workflows/punggol_urban_profile.png
   :alt: Punggol core profile with vector context, reachability, NDVI, NDBI, and slope
   :width: 100%

   Punggol, Singapore — 2 km × 2 km · 250 m units · EPSG:32648.
   Context map first (water, parks, buildings, streets), then
   native rasters and a fused reachability surface. Core profile,
   not all-domain end-to-end. Script:
   ``examples/workflows/punggol_end_to_end.py``.

What you will learn
-------------------

* How to load every committed Punggol layer.
* How to run one metric per domain without pasting every recipe.
* How to export a combined indicator table and receipts.

Dataset
-------

``examples/data/real/punggol``. OSM (ODbL), Sentinel-2 L2A
2024-07-28, Copernicus DEM GLO-30. Details:
:doc:`/reference/datasets`.

Installation
------------

::

   pip install "urbancode[standard]"

Step-by-step
------------

Core chain (load → units → NDVI → reachability → combine):

.. literalinclude:: ../../../examples/workflows/punggol_end_to_end.py
   :language: python
   :start-after: def main
   :end-before: return {

Expand with recipes, do not duplicate them here:

* Vector context — :doc:`/reference/recipes/core/city_roundtrip_punggol`
* Network — :doc:`/reference/recipes/network/centrality_punggol`
* Imagery — :doc:`/reference/recipes/imagery/ndvi_punggol`
* Terrain — :doc:`/reference/recipes/imagery/slope_punggol`
* Units / fusion — :doc:`/reference/recipes/fusion/aggregate_punggol`
* Climate (separate) — :doc:`/workflows/heat_exposure`
* Street view (separate) — :doc:`/workflows/street_experience`

.. figure:: /_static/recipes/network/accessibility_punggol.png
   :alt: Punggol walk-graph reachability
   :width: 100%

   Reachability before aggregation.

.. figure:: /_static/recipes/imagery/indices_punggol.png
   :alt: Punggol NDVI, NDWI, and NDBI
   :width: 100%

   Spectral context for the same pocket.

Reading the result
------------------

* Greener cells follow parks and tree cover on 28 July 2024.
* Reachable cells follow the walk graph, not the water edge.
* Combined rows share unit IDs so the two maps can be compared
  without claiming causation.

Limitations
-----------

* This profile is a 2 km extract, not Punggol planning units.
* Climate and street-view are linked, not inlined, so this page
  stays short.
* One satellite date is not a year of vegetation.

Related pages
-------------

* Get started: :doc:`/getting_started/first_project`
* Domains: :doc:`/domains/fusion`, :doc:`/domains/network`,
  :doc:`/domains/imagery`
* Dataset: :doc:`/reference/datasets`

Use UrbanCode when you want this profile to be rerun on Kallio or
Greenwich Village with the same unit rule.
Use a single backend when you only need one map.
