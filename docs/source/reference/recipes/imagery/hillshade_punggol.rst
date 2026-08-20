uc.imagery.hillshade
====================

Urban question
--------------

How does the terrain look under a standard illumination?

Real case
---------

- Dataset: ``punggol``
- Domain: imagery
- Extra: ``urbancode[imagery]``
- Offline: True

Command
-------

.. code-block:: python

   uc.imagery.hillshade(...)

Inputs
------

dem

Spatial support
---------------

Native support: raster pixels (10 m Sentinel-2 or 30 m DEM). Recipe figure is the native raster. Grid means appear only in fusion workflows.

Parameters
----------

``azimuth`` and ``altitude`` are assumed illumination angles, not solar position.

Method
------

Assumed illumination, not a local solar-position model.

Backend: ``rasterio``. Output unit: ``dimensionless``.

Output
------

Raster Layer hillshade 0–255.

Figure
------

.. figure:: ../../../_static/recipes/imagery/terrain_punggol.png
   :alt: uc.imagery.hillshade result for the registered dataset
   :width: 100%

   Output of ``uc.imagery.hillshade`` on dataset ``punggol``.
   Unit: dimensionless. Backend: rasterio.

How to read
-----------

Shading is for reading relief, not solar access.

Parameters and sensitivity
--------------------------

Changing azimuth rotates the shading; it is not solar access.

Failure modes
-------------

Missing DEM raises.

Limitations
-----------

- illumination is assumed, not a local sun position
- shading is not a solar-access model

Complete script
---------------

.. literalinclude:: ../../../../../examples/recipes/imagery/hillshade_punggol.py
   :language: python
   :caption: examples/recipes/imagery/hillshade_punggol.py

Related pages
-------------

- Domain: :doc:`/domains/imagery`
- API: :doc:`/reference/api/imagery`
- Workflow: :doc:`/workflows/multi_city_comparison`
- Dataset: :doc:`/reference/datasets`
- Catalog: :doc:`/reference/capabilities`
