uc.units.hexgrid
================

Urban question
--------------

What hex cells cover this study area?

Real case
---------

- Dataset: ``punggol``
- Domain: units
- Extra: ``urbancode[vector]``
- Offline: True

Copy this
---------

.. code-block:: python

   import urbancode as uc

   city = uc.load("examples/data/real/punggol", lazy=True)
   units = uc.units.hexgrid(city, cell_size=250)
   print(len(units.frame), units.kind)

``units`` is an :class:`~urbancode.units.AnalysisUnits` object containing clipped pointy-top hexagons. ``cell_size`` is centre-to-vertex distance in metres.

The figure below is the output for the committed fixture. Live-source
recipes can return different timestamps or inventories.

.. figure:: ../../../_static/recipes/units/units_punggol.png
   :alt: uc.units.hexgrid result for the registered dataset
   :width: 100%

   Output of ``uc.units.hexgrid`` on dataset ``punggol``.
   Unit: metre. Backend: shapely.

Inputs
------

City or StudyArea

Spatial support
---------------

Output support: AnalysisUnits. These are a comparison frame, not a replacement for streets or buildings.

Parameters
----------

``cell_size`` is the centre-to-vertex radius in metres, not the flat-to-flat width.

Method
------

Pointy-top hexes. cell_size is the centre-to-vertex radius.

Backend: ``shapely``. Output unit: ``metre``.

Output
------

AnalysisUnits with hex IDs. Not interchangeable with square grid IDs.

How to read
-----------

Hex IDs are not interchangeable with square grid IDs.

Parameters and sensitivity
--------------------------

Halving cell_size roughly quadruples hex count.

Failure modes
-------------

A geographic CRS without a metric CRS raises.

Limitations
-----------

- hex size is metres
- IDs are scheme-specific and not interchangeable with square grid IDs

Related pages
-------------

- Domain: :doc:`/domains/units`
- API: :doc:`/reference/api/units`
- Workflow: :doc:`/workflows/punggol_urban_profile`
- Dataset: :doc:`/reference/datasets`
- Catalog: :doc:`/reference/capabilities`
