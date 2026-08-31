uc.imagery.ndbi
===============

Urban question
--------------

Where does the SWIR-NIR response look built-up?

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
   ndbi = uc.imagery.ndbi(city.layers["sentinel2"])
   ndbi.plot()

``ndbi`` is a dimensionless raster :class:`~urbancode.city.Layer` on the Sentinel-2 pixel grid. High values can represent built-up surface or bare soil.

The figure below is the output for the committed fixture. Live-source
recipes can return different timestamps or inventories.

.. figure:: ../../../_static/recipes/imagery/indices_punggol.png
   :alt: uc.imagery.ndbi result for the registered dataset
   :width: 100%

   Output of ``uc.imagery.ndbi`` on dataset ``punggol``.
   Unit: dimensionless. Backend: rasterio.

Inputs
------

sentinel2

Spatial support
---------------

Native support: raster pixels (10 m Sentinel-2 or 30 m DEM). Recipe figure is the native raster. Grid means appear only in fusion workflows.

Parameters
----------

Needs B11 (SWIR) and B08 (NIR).

Method
------

NDBI = (SWIR - NIR) / (SWIR + NIR) using B11 and B08.

Backend: ``rasterio``. Output unit: ``dimensionless``.

Output
------

Raster Layer. (B11 − B08) / (B11 + B08).

How to read
-----------

High values can be built-up or bare soil.

Parameters and sensitivity
--------------------------

Bare soil can raise NDBI.

Failure modes
-------------

Missing B11 raises.

Limitations
-----------

- needs B11 and B08
- bare soil can raise NDBI

Related pages
-------------

- Domain: :doc:`/domains/imagery`
- API: :doc:`/reference/api/imagery`
- Workflow: :doc:`/workflows/punggol_urban_profile`
- Dataset: :doc:`/reference/datasets`
- Catalog: :doc:`/reference/capabilities`
