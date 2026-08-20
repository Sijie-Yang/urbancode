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

Command
-------

.. code-block:: python

   uc.units.hexgrid(...)

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

Figure
------

.. figure:: ../../../_static/recipes/units/units_punggol.png
   :alt: uc.units.hexgrid result for the registered dataset
   :width: 100%

   Output of ``uc.units.hexgrid`` on dataset ``punggol``.
   Unit: metre. Backend: shapely.

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

Complete script
---------------

.. literalinclude:: ../../../../../examples/recipes/units/hexgrid_punggol.py
   :language: python
   :caption: examples/recipes/units/hexgrid_punggol.py

Related pages
-------------

- Domain: :doc:`/domains/units`
- API: :doc:`/reference/api/units`
- Workflow: :doc:`/workflows/punggol_urban_profile`
- Dataset: :doc:`/reference/datasets`
- Catalog: :doc:`/reference/capabilities`
