uc.fusion.combine
=================

Urban question
--------------

Can two indicator tables share the same units?

Real case
---------

- Dataset: ``punggol``
- Domain: fusion
- Extra: ``urbancode[vector]``
- Offline: True

Command
-------

.. code-block:: python

   uc.fusion.combine(...)

Inputs
------

IndicatorResult plus AnalysisUnits

Spatial support
---------------

Output support: AnalysisUnits (grid/hex/polygons). Context layers (streets, buildings, water) should remain visible.

Parameters
----------

Two or more IndicatorResults. They must share city_id, units, CRS, and scheme.

Method
------

Concatenates IndicatorResults that share city_id, units, CRS, and scheme.

Backend: ``pandas``. Output unit: ``mixed``.

Output
------

One long IndicatorResult. combine does not re-aggregate.

Figure
------

.. figure:: ../../../_static/recipes/fusion/combine_punggol.png
   :alt: uc.fusion.combine result for the registered dataset
   :width: 100%

   Output of ``uc.fusion.combine`` on dataset ``punggol``.
   Unit: mixed. Backend: pandas.

How to read
-----------

combine does not re-aggregate; mismatched units raise.

Parameters and sensitivity
--------------------------

Mismatched unit IDs raise; they are not silently outer-joined.

Failure modes
-------------

Different grids or CRS raise ContractError.

Limitations
-----------

- combine checks city_id, unit IDs, CRS, and scheme
- it does not spatially re-aggregate

Complete script
---------------

.. literalinclude:: ../../../../../examples/recipes/fusion/combine_punggol.py
   :language: python
   :caption: examples/recipes/fusion/combine_punggol.py

Related pages
-------------

- Domain: :doc:`/domains/fusion`
- API: :doc:`/reference/api/fusion`
- Workflow: :doc:`/workflows/punggol_urban_profile`
- Dataset: :doc:`/reference/datasets`
- Catalog: :doc:`/reference/capabilities`
