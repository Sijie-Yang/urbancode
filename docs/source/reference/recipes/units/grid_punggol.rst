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

Copy this
---------

.. code-block:: python

   import urbancode as uc

   city = uc.load("examples/data/real/punggol", lazy=True)
   units = uc.units.grid(city, cell_size=250)
   print(len(units.frame), units.metric_crs)

``units`` is an :class:`~urbancode.units.AnalysisUnits` object. ``units.frame`` contains clipped 250 m polygons with stable ``unit_id`` values in the reported metric CRS.

The figure below is the output for the committed fixture. Live-source
recipes can return different timestamps or inventories.

.. figure:: ../../../_static/recipes/units/units_punggol.png
   :alt: uc.units.grid result for the registered dataset
   :width: 100%

   Output of ``uc.units.grid`` on dataset ``punggol``.
   Unit: metre. Backend: geopandas.

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

Related pages
-------------

- Domain: :doc:`/domains/units`
- API: :doc:`/reference/api/units`
- Workflow: :doc:`/workflows/punggol_urban_profile`
- Dataset: :doc:`/reference/datasets`
- Catalog: :doc:`/reference/capabilities`
