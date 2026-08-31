uc.imagery.slope
================

Urban question
--------------

How steep is the terrain?

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
   slope = uc.imagery.slope(city.layers["dem"])
   slope.plot()

``slope`` is a raster :class:`~urbancode.city.Layer` in degrees, derived from ``city.layers['dem']``. It follows the DEM grid and nodata mask.

The figure below is the output for the committed fixture. Live-source
recipes can return different timestamps or inventories.

.. figure:: ../../../_static/recipes/imagery/terrain_punggol.png
   :alt: uc.imagery.slope result for the registered dataset
   :width: 100%

   Output of ``uc.imagery.slope`` on dataset ``punggol``.
   Unit: degree. Backend: rasterio.

Inputs
------

dem

Spatial support
---------------

Native support: raster pixels (10 m Sentinel-2 or 30 m DEM). Recipe figure is the native raster. Grid means appear only in fusion workflows.

Parameters
----------

DEM Layer or GeoTIFF. Computed in a metric CRS. Output unit degrees. Nodata cells stay nodata.

Method
------

Slope in degrees from the Copernicus DEM GLO-30 grid.

Backend: ``rasterio``. Output unit: ``degree``.

Output
------

Raster Layer ``slope``. Resolution follows the DEM (30 m here).

How to read
-----------

This is terrain, not a building DSM.

Parameters and sensitivity
--------------------------

A building DSM is not a substitute; this is terrain.

Failure modes
-------------

Missing DEM band raises. Geographic pixels are reprojected first.

Limitations
-----------

- Copernicus DEM GLO-30 is a 30 m product resampled to the pocket grid
- buildings are not a DSM

Related pages
-------------

- Domain: :doc:`/domains/imagery`
- API: :doc:`/reference/api/imagery`
- Workflow: :doc:`/workflows/multi_city_comparison`
- Dataset: :doc:`/reference/datasets`
- Catalog: :doc:`/reference/capabilities`
