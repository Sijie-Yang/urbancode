Analysis units
==============

Urban question
--------------

How do satellite pixels, street nodes, and park polygons become
comparable neighbourhood scores?

Result first
------------

.. figure:: /_static/recipes/units/units_punggol.png
   :alt: Square grid, hexgrid, and park polygons as analysis units in Punggol
   :width: 100%

   The same Punggol pocket as a 250 m square grid, a hex grid, and
   park polygons via ``from_layer``. IDs are scheme-specific.

What you will learn
-------------------

* Why multimodal work needs a shared spatial frame.
* The three public constructors: grid, hexgrid, from_layer.
* Stable IDs, clipping, and the area denominator.
* MAUP and cross-city consistency.

Why units exist
---------------

A Sentinel-2 pixel, an OSM node, and a park polygon do not share a
row key. ``AnalysisUnits`` is that key. Fusion then writes one
``IndicatorResult`` row per ``(city_id, unit_id, indicator)``.

**Analysis units provide a common comparison support. They do not
replace the native geometry of streets, buildings, imagery, or
observations.** See :doc:`spatial_support_and_maps`.

Public methods
--------------

* :func:`urbancode.units.grid` — world-origin squares. ``cell_size``
  is metres in the metric CRS. Edge cells are clipped to the study
  area. IDs look like ``grid:EPSG:32648:250:col:row``.
* :func:`urbancode.units.hexgrid` — Shapely pointy-top hexes. IDs are
  not interchangeable with square-grid IDs. H3 is not implemented.
* :func:`urbancode.units.from_layer` — existing polygons. Duplicate
  geometries raise. Default IDs are geometry fingerprints after
  reprojection, 1 mm rounding, and ring normalization.

The Punggol workflow uses a 250 m world-origin grid so overlapping
pockets can share cell IDs.

Cross-city rules
----------------

To compare Punggol, Kallio, and Greenwich Village:

* same physical extent (here 2 km × 2 km) or an explicit exception
* same constructor and ``cell_size``
* same missing-value rule (null, not zero)
* keep each city's acquisition date in the manifest

Raw values, within-city percentiles, and cross-city z-scores are
different statements. See :doc:`/workflows/multi_city_comparison`.

MAUP
----

Changing ``cell_size`` from 100 m to 500 m moves means and ranks.
That is expected. Report the unit with the indicator. Do not treat
one resolution as the neighbourhood.

Related pages
-------------

* Domain: :doc:`/domains/units`, :doc:`/domains/fusion`
* Recipes: :doc:`/reference/recipes/units/grid_punggol`
* Workflow: :doc:`/workflows/multi_city_comparison`
* Concept: :doc:`crs_alignment`

Use UrbanCode when several Layers must share IDs.
Use GeoPandas directly when you are dissolving one layer for a
one-off map.
