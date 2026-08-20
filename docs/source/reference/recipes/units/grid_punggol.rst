uc.units.grid
=============

Urban question
--------------

What regular cells cover this study area?

Real case
---------

- Dataset: ``punggol``
- Domain: units
- Extra: ``urbancode[vector]``
- Offline: True

Command
-------

.. code-block:: python

   uc.units.grid(...)

Inputs
------

City or StudyArea

Spatial support
---------------

Output support: AnalysisUnits. These are a comparison frame, not a replacement for streets or buildings.

Parameters
----------

``cell_size`` in metres in the metric CRS. Edge cells are clipped.

Method
------

Square metres grid with world-origin IDs.

Backend: ``geopandas``. Output unit: ``metre``.

Output
------

AnalysisUnits with IDs ``grid:<CRS>:<size>:<col>:<row>``.

Figure
------

.. figure:: ../../../_static/recipes/units/units_punggol.png
   :alt: uc.units.grid result for the registered dataset
   :width: 100%

   Output of ``uc.units.grid`` on dataset ``punggol``.
   Unit: metre. Backend: geopandas.

How to read
-----------

Edge cells are clipped to the study area.

Parameters and sensitivity
--------------------------

World-origin IDs stay stable if the bbox shifts slightly.

Failure modes
-------------

A geographic CRS without a metric CRS raises.

Limitations
-----------

- cell_size is metres in the metric CRS
- edge cells are clipped to the study area

Complete script
---------------

.. literalinclude:: ../../../../../examples/recipes/units/grid_punggol.py
   :language: python
   :caption: examples/recipes/units/grid_punggol.py

Related pages
-------------

- Domain: :doc:`/domains/units`
- API: :doc:`/reference/api/units`
- Workflow: :doc:`/workflows/punggol_urban_profile`
- Dataset: :doc:`/reference/datasets`
- Catalog: :doc:`/reference/capabilities`
