Analysis units
==============

Urban question
--------------

What regular cells, hexes, or existing polygons should carry every
indicator in this study?

Result first
------------

.. figure:: /_static/recipes/units/units_punggol.png
   :alt: Square grid, hexgrid, and park polygons for the Punggol pocket
   :width: 100%

   Three unit schemes on the same Punggol envelope. Cell size is
   metres in EPSG:32648. Edge cells are clipped.

What you will learn
-------------------

* ``grid``, ``hexgrid``, and ``from_layer``.
* Clipped vs full cells and the area denominator.
* Why H3 is not an UrbanCode API yet.

Installation
------------

::

   pip install "urbancode[vector]"

This installs the polygon and CRS stack used by all three unit
constructors. It does not install imagery or network backends.

UrbanCode API
-------------

* :func:`urbancode.units.grid`
* :func:`urbancode.units.hexgrid`
* :func:`urbancode.units.from_layer`

::

   import urbancode as uc

   city = uc.load("examples/data/real/punggol", lazy=True)
   grid = uc.units.grid(city, cell_size=250)
   hexes = uc.units.hexgrid(city, cell_size=250)
   parks = uc.units.from_layer(city.layer("parks"), study_area=city.study_area)
   print(len(grid.frame), len(hexes.frame), len(parks.frame))

::

   81 38 48

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
   * - Shapely
     - cell geometry
     - all three constructors
     - Rarely
     - integrated
   * - GeoPandas
     - spatial table
     - frame, clip
     - Yes
     - integrated
   * - pyproj
     - metric CRS
     - StudyArea
     - Rarely
     - integrated
   * - H3 / h3-py
     - global indexes
     - no
     - Yes
     - roadmap

Method
------

* ``cell_size`` is metres. Do not pass degrees.
* Clipped edge cells have a smaller geometry; ``area_fraction`` and
  raster ``coverage`` use that geometry as the denominator.
* Square-grid IDs are world-origin. Hex IDs are scheme-specific.
* ``from_layer`` fingerprints geometry; duplicate polygons raise.
* Ordering of input polygons does not change fingerprints.

Recipes
-------

* :doc:`/reference/recipes/units/grid_punggol`
* :doc:`/reference/recipes/units/hexgrid_punggol`
* :doc:`/reference/recipes/units/from_layer_punggol`

Related pages
-------------

* Concept: :doc:`/concepts/analysis_units`
* Domain: :doc:`fusion`
* Workflow: :doc:`/workflows/multi_city_comparison`
* API: :doc:`/reference/api/units`

Use UrbanCode when unit IDs must be stable across scripts.
Use H3 directly when you need a global discrete index UrbanCode
does not wrap.
