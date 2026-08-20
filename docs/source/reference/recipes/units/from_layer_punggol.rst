uc.units.from_layer
===================

Urban question
--------------

Can existing polygons become analysis units?

Real case
---------

- Dataset: ``punggol``
- Domain: units
- Extra: ``urbancode[vector]``
- Offline: True

Command
-------

.. code-block:: python

   uc.units.from_layer(...)

Inputs
------

polygon Layer

Spatial support
---------------

Output support: AnalysisUnits. These are a comparison frame, not a replacement for streets or buildings.

Parameters
----------

``layer`` must be polygons. Optional ``id_column`` is not invented.

Method
------

Existing polygons become units. IDs are geometry fingerprints.

Backend: ``geopandas``. Output unit: ``polygon``.

Output
------

AnalysisUnits. IDs are geometry fingerprints unless a column is given.

Figure
------

.. figure:: ../../../_static/recipes/units/units_punggol.png
   :alt: uc.units.from_layer result for the registered dataset
   :width: 100%

   Output of ``uc.units.from_layer`` on dataset ``punggol``.
   Unit: polygon. Backend: geopandas.

How to read
-----------

Duplicate geometries raise; they are not row-number suffixed.

Parameters and sensitivity
--------------------------

Simplifying polygons changes IDs because they are fingerprints.

Failure modes
-------------

Duplicate geometries raise. Points and lines raise.

Limitations
-----------

- unit IDs are geometry fingerprints
- duplicate geometries raise

Complete script
---------------

.. literalinclude:: ../../../../../examples/recipes/units/from_layer_punggol.py
   :language: python
   :caption: examples/recipes/units/from_layer_punggol.py

Related pages
-------------

- Domain: :doc:`/domains/units`
- API: :doc:`/reference/api/units`
- Workflow: :doc:`/workflows/punggol_urban_profile`
- Dataset: :doc:`/reference/datasets`
- Catalog: :doc:`/reference/capabilities`
