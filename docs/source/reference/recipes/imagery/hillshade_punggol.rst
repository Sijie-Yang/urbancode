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

Copy this
---------

.. code-block:: python

   import urbancode as uc

   city = uc.load("examples/data/real/punggol", lazy=True)
   shade = uc.imagery.hillshade(city.layers["dem"])
   shade.plot()

``shade`` is a 0--255 raster :class:`~urbancode.city.Layer`. It visualises relief under assumed illumination and is not a solar-access result.

The figure below is the output for the committed fixture. Live-source
recipes can return different timestamps or inventories.

.. figure:: ../../../_static/recipes/imagery/terrain_punggol.png
   :alt: uc.imagery.hillshade result for the registered dataset
   :width: 100%

   Output of ``uc.imagery.hillshade`` on dataset ``punggol``.
   Unit: dimensionless. Backend: rasterio.

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

Related pages
-------------

- Domain: :doc:`/domains/imagery`
- API: :doc:`/reference/api/imagery`
- Workflow: :doc:`/workflows/multi_city_comparison`
- Dataset: :doc:`/reference/datasets`
- Catalog: :doc:`/reference/capabilities`
