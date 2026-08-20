Green accessibility
===================

Urban question
--------------

Are greener neighbourhoods also better connected to accessible
parks?

Result first
------------

.. figure:: /_static/workflows/green_accessibility.png
   :alt: Punggol NDVI, nearest park distance, and network reachability
   :width: 100%

   Punggol, Singapore — 2 km × 2 km pocket · 250 m units ·
   EPSG:32648. NDVI, nearest park polygon, and walk-graph
   reachability with streets/buildings/water underneath.
   Correlation on this pocket is not causation. Sentinel-2
   2024-07-28.

What you will learn
-------------------

* How to put vegetation, park geometry, and network reach on the
  same units.
* How to read a typology without ranking neighbourhoods as
  “good” or “bad”.

Dataset
-------

Punggol real pocket. Parks are OSM polygons. NDVI is the
2024-07-28 Sentinel-2 window. Reachability is the walk graph.

Installation
------------

::

   pip install "urbancode[standard]"

Step-by-step
------------

.. literalinclude:: ../../../examples/workflows/green_accessibility.py
   :language: python
   :caption: examples/workflows/green_accessibility.py

APIs used: :func:`urbancode.imagery.ndvi`,
:func:`urbancode.network.accessibility`,
:func:`urbancode.fusion.aggregate`,
:func:`urbancode.fusion.combine`.

Reading the result
------------------

* Some high-NDVI cells are close to a park polygon; some are
  private or residual vegetation.
* High reachability can sit on grey streets with low NDVI.
* Low coverage cells are not “no park”; they are poorly observed.

Do not read this as evidence that greenery causes access, or that
access causes greenery.

Limitations
-----------

* Park polygons are OSM tags, not an official parks layer.
* Reachability is node count, not population with access to a park
  gate.
* Nearest-distance ignores park size and entry points.

Related pages
-------------

* Domain: :doc:`/domains/network`, :doc:`/domains/imagery`,
  :doc:`/domains/fusion`
* Recipes: :doc:`/reference/recipes/network/accessibility_punggol`,
  :doc:`/reference/recipes/imagery/ndvi_punggol`
* Concept: :doc:`/concepts/indicators`

Use UrbanCode when the question needs three modalities on one
grid.
Use OSMnx or GeoPandas directly when you only need one distance
column.
