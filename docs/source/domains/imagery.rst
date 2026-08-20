Imagery
=======

Urban question
--------------

Where is vegetation, water, and built-up response in the Punggol
Sentinel-2 window, and what does the DEM look like?

``uc.imagery`` is continuous geographic raster. Discrete city
photos live in ``uc.images``. Do not put Sentinel-2 in images.

Result first
------------

.. figure:: /_static/recipes/imagery/indices_punggol.png
   :alt: NDVI, NDWI, and NDBI for the Punggol 2 km pocket
   :width: 100%

   NDVI, McFeeters NDWI, and NDBI from Sentinel-2 L2A item
   ``S2B_MSIL2A_20240728T031519`` (28 July 2024). One date, not a
   seasonal composite.

What you will learn
-------------------

* Read vs fetch, indices, terrain, and zonal stats.
* Band formulas and the committed band list (including B03).
* What Rasterio / rioxarray / STAC do.
* DEM slope units and hillshade assumptions.

Installation
------------

::

   pip install "urbancode[imagery]"

UrbanCode API
-------------

* :func:`urbancode.imagery.read`
* :func:`urbancode.imagery.fetch`
* :func:`urbancode.imagery.ndvi`
* :func:`urbancode.imagery.ndwi`
* :func:`urbancode.imagery.ndbi`
* :func:`urbancode.imagery.slope`
* :func:`urbancode.imagery.aspect`
* :func:`urbancode.imagery.hillshade`
* :func:`urbancode.imagery.zonal_stats`

``uc.imagery.utci`` is a compatibility alias of
:func:`urbancode.climate.utci`. The tutorial lives on
:doc:`climate`.

Backend stack
-------------

.. list-table::
   :header-rows: 1
   :widths: 22 24 20 16 18

   * - Package
     - Responsibility
     - Called by UrbanCode
     - Direct use?
     - Status
   * - Rasterio
     - I/O, window, mask, transform
     - read, indices, terrain, zonal
     - Yes
     - integrated
   * - rioxarray
     - CRS-aware Xarray
     - read
     - Yes
     - integrated
   * - Xarray
     - labelled arrays
     - raster Layer
     - Yes
     - integrated
   * - pystac-client
     - STAC search
     - ``imagery.fetch``
     - Yes
     - integrated
   * - planetary-computer
     - asset signing
     - ``imagery.fetch``
     - Rarely
     - integrated
   * - stackstac / odc-stac / Dask
     - multi-date stacks
     - no
     - Yes
     - planned
   * - exactextract / rasterstats
     - alternate zonal backends
     - no
     - Yes
     - planned

Spectral indices
----------------

The Punggol fixture includes B02, B03, B04, B08, and B11. NDWI is
computed; this fixture is not a B03-missing case.

* NDVI = (NIR − Red) / (NIR + Red) = (B08 − B04) / (B08 + B04)
* NDWI (McFeeters) = (Green − NIR) / (Green + NIR) = (B03 − B08) / (B03 + B08)
* NDBI = (SWIR − NIR) / (SWIR + NIR) = (B11 − B08) / (B11 + B08)

Inputs are the committed L2A window. Residual cloud and atmosphere
remain. Nodata stays nodata. There is no multi-date composite in
the offline recipe.

Terrain
-------

.. figure:: /_static/recipes/imagery/terrain_punggol.png
   :alt: DEM, slope, aspect, and hillshade for the Punggol pocket
   :width: 100%

   Copernicus DEM GLO-30 resampled to the pocket grid. Slope is
   degrees. Aspect is 0–360° clockwise from north; flat cells are
   nodata. Hillshade uses an assumed azimuth and altitude, not a
   local sun position.

This DEM is terrain, not a building DSM.

Zonal stats
-----------

.. figure:: /_static/recipes/imagery/zonal_stats_punggol.png
   :alt: Park polygons, NDVI, and park-mean choropleth
   :width: 100%

   Mean NDVI inside each OSM park polygon. The mean ignores
   within-park structure.

Reading the result
------------------

* High NDVI follows tree cover and parks on 28 July 2024.
* High NDWI can be water or dark shadow; check the RGB preview
  from :doc:`/reference/recipes/imagery/read_punggol`.
* High NDBI can be built-up or bare soil.

Limitations
-----------

* Single acquisition; Punggol is equatorial, so this is a calendar
  window, not a shared growing season with Helsinki or New York.
* Offline ``fetch`` uses the committed STAC item.
* stackstac time stacks are not implemented.

Related pages
-------------

* Recipes: :doc:`/reference/recipes/imagery/ndvi_punggol`,
  :doc:`/reference/recipes/imagery/slope_punggol`
* Workflow: :doc:`/workflows/punggol_urban_profile`
* API: :doc:`/reference/api/imagery`
* Upstream: `Rasterio <https://rasterio.readthedocs.io/>`__,
  `rioxarray <https://corteva.github.io/rioxarray/stable/>`__,
  `Xarray <https://docs.xarray.dev/>`__

Use UrbanCode when indices must land on the same units as network
or climate.
Use Rasterio / rioxarray directly for windowed I/O or a custom
index.
