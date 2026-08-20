uc.imagery.ndwi
===============

Urban question
--------------

Where does the green-NIR response look like water?

Real case
---------

- Dataset: ``punggol``
- Domain: imagery
- Extra: ``urbancode[imagery]``
- Offline: True

Command
-------

.. code-block:: python

   uc.imagery.ndwi(...)

Inputs
------

sentinel2

Spatial support
---------------

Native support: raster pixels (10 m Sentinel-2 or 30 m DEM). Recipe figure is the native raster. Grid means appear only in fusion workflows.

Parameters
----------

McFeeters NDWI needs B03 (green) and B08 (NIR).

Method
------

NDWI = (green - NIR) / (green + NIR) using B03 and B08.

Backend: ``rasterio``. Output unit: ``dimensionless``.

Output
------

Raster Layer. (B03 − B08) / (B03 + B08).

Figure
------

.. figure:: ../../../_static/recipes/imagery/indices_punggol.png
   :alt: uc.imagery.ndwi result for the registered dataset
   :width: 100%

   Output of ``uc.imagery.ndwi`` on dataset ``punggol``.
   Unit: dimensionless. Backend: rasterio.

How to read
-----------

High values can be water or dark shadow; check the RGB.

Parameters and sensitivity
--------------------------

Dark shadow can look like water.

Failure modes
-------------

Missing B03 raises; this fixture includes B03.

Limitations
-----------

- needs B03 and B08
- water and dark shadow can look similar

Complete script
---------------

.. literalinclude:: ../../../../../examples/recipes/imagery/ndwi_punggol.py
   :language: python
   :caption: examples/recipes/imagery/ndwi_punggol.py

Related pages
-------------

- Domain: :doc:`/domains/imagery`
- API: :doc:`/reference/api/imagery`
- Workflow: :doc:`/workflows/punggol_urban_profile`
- Dataset: :doc:`/reference/datasets`
- Catalog: :doc:`/reference/capabilities`
